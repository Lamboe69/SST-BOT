"""
Structure Detection Module
Detects CHOCH (Change of Character) and BOS (Break of Structure) patterns
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

class StructureDetector:
    def __init__(self, oanda_client, instruments: List[str]):
        """
        Initialize Structure Detector
        
        Args:
            oanda_client: OANDA client instance
            instruments: List of instruments to monitor
        """
        self.oanda_client = oanda_client
        self.instruments = instruments
        
        # Store previous day highs/lows for each instrument
        self.previous_day_levels = {}
        
        # Track last analysis time
        self.last_analysis = {}
    
    def analyze(self, instrument: str, candles: List[Dict]) -> List[Dict]:
        """
        Analyze candles for CHOCH and BOS setups
        
        Args:
            instrument: Trading instrument
            candles: List of candle data
        
        Returns:
            List of trading signals
        """
        signals = []
        
        # Update previous day levels
        self._update_previous_day_levels(instrument, candles)
        
        # Get current levels
        levels = self.previous_day_levels.get(instrument, {})
        if not levels:
            return signals
        
        pdh = levels.get('high')
        pdl = levels.get('low')
        pdh_broken = levels.get('high_broken', False)
        pdl_broken = levels.get('low_broken', False)
        
        # Detect swing highs and lows
        swing_highs, swing_lows = self._detect_swings(candles)
        
        # Check for CHOCH setups at PDH (not broken)
        if pdh and not pdh_broken:
            choch_signal = self._detect_choch_at_high(candles, pdh, swing_lows, instrument)
            if choch_signal:
                signals.append(choch_signal)
        
        # Check for CHOCH setups at PDL (not broken)
        if pdl and not pdl_broken:
            choch_signal = self._detect_choch_at_low(candles, pdl, swing_highs, instrument)
            if choch_signal:
                signals.append(choch_signal)
        
        # Check for BOS setups when PDH is broken
        if pdh and pdh_broken:
            bos_signal = self._detect_bos_after_high_break(candles, pdh, swing_highs, instrument)
            if bos_signal:
                signals.append(bos_signal)
            
            # Also check for CHOCH at flipped level (PDH now acts as support)
            choch_signal = self._detect_choch_at_flipped_high(candles, pdh, swing_highs, instrument)
            if choch_signal:
                signals.append(choch_signal)
        
        # Check for BOS setups when PDL is broken
        if pdl and pdl_broken:
            bos_signal = self._detect_bos_after_low_break(candles, pdl, swing_lows, instrument)
            if bos_signal:
                signals.append(bos_signal)
            
            # Also check for CHOCH at flipped level (PDL now acts as resistance)
            choch_signal = self._detect_choch_at_flipped_low(candles, pdl, swing_lows, instrument)
            if choch_signal:
                signals.append(choch_signal)
        
        return signals
    
    def _update_previous_day_levels(self, instrument: str, candles: List[Dict]):
        """Update or create previous day high/low levels"""
        if len(candles) < 480:  # Need at least 24 hours of 3-min candles
            return
        
        # Get yesterday's candles (last 480 candles = 24 hours)
        yesterday_candles = candles[-960:-480]  # 2 days ago to yesterday
        
        if not yesterday_candles:
            return
        
        # Calculate previous day high and low
        pdh = max([c['high'] for c in yesterday_candles])
        pdl = min([c['low'] for c in yesterday_candles])
        
        # Check if levels are broken
        recent_candles = candles[-100:]  # Last 100 candles (5 hours)
        current_high = max([c['high'] for c in recent_candles])
        current_low = min([c['low'] for c in recent_candles])
        
        pdh_broken = current_high > pdh
        pdl_broken = current_low < pdl
        
        # Store levels
        self.previous_day_levels[instrument] = {
            'high': pdh,
            'low': pdl,
            'high_broken': pdh_broken,
            'low_broken': pdl_broken,
            'updated_at': datetime.now()
        }
    
    def _detect_swings(self, candles: List[Dict], lookback: int = 5) -> tuple:
        """
        Detect swing highs and swing lows
        
        Args:
            candles: Price data
            lookback: Number of candles to look back for swing detection
        
        Returns:
            Tuple of (swing_highs, swing_lows)
        """
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(candles) - lookback):
            # Check for swing high
            is_swing_high = True
            for j in range(1, lookback + 1):
                if candles[i]['high'] <= candles[i - j]['high'] or candles[i]['high'] <= candles[i + j]['high']:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'price': candles[i]['high'],
                    'index': i,
                    'time': candles[i]['time']
                })
            
            # Check for swing low
            is_swing_low = True
            for j in range(1, lookback + 1):
                if candles[i]['low'] >= candles[i - j]['low'] or candles[i]['low'] >= candles[i + j]['low']:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'price': candles[i]['low'],
                    'index': i,
                    'time': candles[i]['time']
                })
        
        return swing_highs, swing_lows
    
    def _detect_choch_at_high(self, candles: List[Dict], pdh: float, swing_lows: List[Dict], instrument: str) -> Optional[Dict]:
        """Detect CHOCH (reversal) at previous day high"""
        if len(candles) < 20:
            return None
        
        recent_candles = candles[-20:]  # Last 20 candles
        current_price = recent_candles[-1]['close']
        
        # Check if price recently touched PDH (within last 20 candles)
        touched_pdh = any(c['high'] >= pdh * 0.999 for c in recent_candles)  # 0.1% tolerance
        
        if not touched_pdh:
            return None
        
        # Find the most recent swing low after touching PDH
        recent_swing_lows = [sl for sl in swing_lows if sl['index'] >= len(candles) - 20]
        
        if not recent_swing_lows:
            return None
        
        latest_swing_low = recent_swing_lows[-1]
        
        # Check if current price broke below the swing low (CHOCH confirmation)
        if current_price < latest_swing_low['price']:
            # Find the rejection high (highest point before the drop)
            rejection_high = max([c['high'] for c in recent_candles[:15]])
            
            # Calculate stop loss (above rejection high)
            stop_loss = rejection_high * 1.001  # Add small buffer
            
            return {
                'instrument': instrument,
                'setup_type': 'CHOCH',
                'direction': 'SELL',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'reference_level': pdh,
                'swing_break_level': latest_swing_low['price'],
                'timestamp': datetime.now()
            }
        
        return None
    
    def _detect_choch_at_low(self, candles: List[Dict], pdl: float, swing_highs: List[Dict], instrument: str) -> Optional[Dict]:
        """Detect CHOCH (reversal) at previous day low"""
        if len(candles) < 20:
            return None
        
        recent_candles = candles[-20:]
        current_price = recent_candles[-1]['close']
        
        # Check if price recently touched PDL
        touched_pdl = any(c['low'] <= pdl * 1.001 for c in recent_candles)
        
        if not touched_pdl:
            return None
        
        # Find the most recent swing high after touching PDL
        recent_swing_highs = [sh for sh in swing_highs if sh['index'] >= len(candles) - 20]
        
        if not recent_swing_highs:
            return None
        
        latest_swing_high = recent_swing_highs[-1]
        
        # Check if current price broke above the swing high (CHOCH confirmation)
        if current_price > latest_swing_high['price']:
            # Find the rejection low (lowest point before the rally)
            rejection_low = min([c['low'] for c in recent_candles[:15]])
            
            # Calculate stop loss (below rejection low)
            stop_loss = rejection_low * 0.999
            
            return {
                'instrument': instrument,
                'setup_type': 'CHOCH',
                'direction': 'BUY',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'reference_level': pdl,
                'swing_break_level': latest_swing_high['price'],
                'timestamp': datetime.now()
            }
        
        return None
    
    def _detect_bos_after_high_break(self, candles: List[Dict], pdh: float, swing_highs: List[Dict], instrument: str) -> Optional[Dict]:
        """Detect BOS (continuation) after PDH is broken"""
        if len(candles) < 30:
            return None
        
        recent_candles = candles[-30:]
        current_price = recent_candles[-1]['close']
        
        # Check if PDH was recently broken (price went above)
        broken_pdh = any(c['high'] > pdh for c in recent_candles[:20])
        
        if not broken_pdh:
            return None
        
        # Check if BOS is not too far from PDH (distance threshold)
        current_high = max([c['high'] for c in recent_candles])
        distance_from_pdh = current_high - pdh
        
        # If BOS is more than 1% away from PDH, don't take the trade
        if distance_from_pdh > (pdh * 0.01):
            return None
        
        # Find recent swing high after breaking PDH
        recent_swing_highs = [sh for sh in swing_highs if sh['index'] >= len(candles) - 30]
        
        if not recent_swing_highs:
            return None
        
        latest_swing_high = recent_swing_highs[-1]
        
        # Check if price broke above the swing high (BOS confirmation)
        if current_price > latest_swing_high['price']:
            # Stop loss below the broken PDH
            stop_loss = pdh * 0.999
            
            return {
                'instrument': instrument,
                'setup_type': 'BOS',
                'direction': 'BUY',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'reference_level': pdh,
                'swing_break_level': latest_swing_high['price'],
                'timestamp': datetime.now()
            }
        
        return None
    
    def _detect_bos_after_low_break(self, candles: List[Dict], pdl: float, swing_lows: List[Dict], instrument: str) -> Optional[Dict]:
        """Detect BOS (continuation) after PDL is broken"""
        if len(candles) < 30:
            return None
        
        recent_candles = candles[-30:]
        current_price = recent_candles[-1]['close']
        
        # Check if PDL was recently broken (price went below)
        broken_pdl = any(c['low'] < pdl for c in recent_candles[:20])
        
        if not broken_pdl:
            return None
        
        # Check if BOS is not too far from PDL
        current_low = min([c['low'] for c in recent_candles])
        distance_from_pdl = pdl - current_low
        
        if distance_from_pdl > (pdl * 0.01):
            return None
        
        # Find recent swing low after breaking PDL
        recent_swing_lows = [sl for sl in swing_lows if sl['index'] >= len(candles) - 30]
        
        if not recent_swing_lows:
            return None
        
        latest_swing_low = recent_swing_lows[-1]
        
        # Check if price broke below the swing low (BOS confirmation)
        if current_price < latest_swing_low['price']:
            # Stop loss above the broken PDL
            stop_loss = pdl * 1.001
            
            return {
                'instrument': instrument,
                'setup_type': 'BOS',
                'direction': 'SELL',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'reference_level': pdl,
                'swing_break_level': latest_swing_low['price'],
                'timestamp': datetime.now()
            }
        
        return None
    
    def _detect_choch_at_flipped_high(self, candles: List[Dict], pdh: float, swing_highs: List[Dict], instrument: str) -> Optional[Dict]:
        """Detect CHOCH at flipped PDH (now acting as support)"""
        # Similar logic to _detect_choch_at_low but using the flipped PDH
        return self._detect_choch_at_low(candles, pdh, swing_highs, instrument)
    
    def _detect_choch_at_flipped_low(self, candles: List[Dict], pdl: float, swing_lows: List[Dict], instrument: str) -> Optional[Dict]:
        """Detect CHOCH at flipped PDL (now acting as resistance)"""
        # Similar logic to _detect_choch_at_high but using the flipped PDL
        return self._detect_choch_at_high(candles, pdl, swing_lows, instrument)
    
    def get_previous_day_levels(self, instrument: str) -> Dict:
        """Get stored previous day levels for an instrument"""
        return self.previous_day_levels.get(instrument, {})