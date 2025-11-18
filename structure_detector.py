"""
Structure Detection Module
Detects CHOCH (Change of Character) and BOS (Break of Structure) patterns
✅ USES LINE GRAPH (CLOSE PRICES ONLY) - NOT CANDLESTICKS
Uses ATR-based dynamic distance calculation for BOS validation
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
        
        # Store ATR values for each instrument (for distance calculation)
        self.atr_values = {}
        
        # Store last signal time to prevent duplicate signals
        self.last_signal_time = {}

    def analyze(self, instrument: str, candles: List[Dict]) -> List[Dict]:
        """
        Analyze candles for CHOCH and BOS setups
        ✅ USES ONLY CLOSE PRICES (LINE GRAPH)
        
        Args:
            instrument: Trading instrument
            candles: List of candle data
        
        Returns:
            List of trading signals
        """
        signals = []
        
        if len(candles) < 100:
            print(f"⚠️ Not enough candles for {instrument}: {len(candles)}")
            return signals
        
        # Convert candles to line graph (close prices only)
        close_prices = [c['close'] for c in candles]
        
        # Calculate ATR for distance validation
        self._calculate_atr(instrument, candles)
        
        # Update previous day levels
        self._update_previous_day_levels(instrument, close_prices, candles)
        
        # Get current levels
        levels = self.previous_day_levels.get(instrument, {})
        if not levels or 'high' not in levels or 'low' not in levels:
            print(f"⚠️ No levels found for {instrument}")
            return signals
        
        pdh = levels.get('high')
        pdl = levels.get('low')
        pdh_broken = levels.get('high_broken', False)
        pdl_broken = levels.get('low_broken', False)
        
        print(f"\n📊 {instrument} Analysis:")
        print(f"   PDH: {pdh:.4f} (Broken: {pdh_broken})")
        print(f"   PDL: {pdl:.4f} (Broken: {pdl_broken})")
        print(f"   Current: {close_prices[-1]:.4f}")
        print(f"   ATR: {self.atr_values.get(instrument, 0):.4f}")
        
        # Detect swing highs and lows ON LINE GRAPH (using close prices)
        swing_highs, swing_lows = self._detect_swings_line_graph(close_prices, candles)
        
        print(f"   Swing Highs: {len(swing_highs)}, Swing Lows: {len(swing_lows)}")
        
        # Check for CHOCH setups at PDH (not broken)
        if pdh and not pdh_broken:
            choch_signal = self._detect_choch_at_high(close_prices, pdh, swing_lows, instrument, candles)
            if choch_signal:
                print(f"   ✅ CHOCH SELL signal detected at PDH!")
                signals.append(choch_signal)
        
        # Check for CHOCH setups at PDL (not broken)
        if pdl and not pdl_broken:
            choch_signal = self._detect_choch_at_low(close_prices, pdl, swing_highs, instrument, candles)
            if choch_signal:
                print(f"   ✅ CHOCH BUY signal detected at PDL!")
                signals.append(choch_signal)
        
        # Check for BOS setups when PDH is broken
        if pdh and pdh_broken:
            bos_signal = self._detect_bos_after_high_break(close_prices, pdh, swing_highs, instrument, candles)
            if bos_signal:
                print(f"   ✅ BOS BUY signal detected after PDH break!")
                signals.append(bos_signal)
            
            # Also check for CHOCH at flipped level (PDH now acts as support)
            choch_signal = self._detect_choch_at_flipped_high(close_prices, pdh, swing_highs, instrument, candles)
            if choch_signal:
                print(f"   ✅ CHOCH BUY signal at flipped PDH!")
                signals.append(choch_signal)
        
        # Check for BOS setups when PDL is broken
        if pdl and pdl_broken:
            bos_signal = self._detect_bos_after_low_break(close_prices, pdl, swing_lows, instrument, candles)
            if bos_signal:
                print(f"   ✅ BOS SELL signal detected after PDL break!")
                signals.append(bos_signal)
            
            # Also check for CHOCH at flipped level (PDL now acts as resistance)
            choch_signal = self._detect_choch_at_flipped_low(close_prices, pdl, swing_lows, instrument, candles)
            if choch_signal:
                print(f"   ✅ CHOCH SELL signal at flipped PDL!")
                signals.append(choch_signal)
        
        # Filter out duplicate signals (within 10 candles)
        signals = self._filter_duplicate_signals(instrument, signals)
        
        return signals

    def _filter_duplicate_signals(self, instrument: str, signals: List[Dict]) -> List[Dict]:
        """Prevent duplicate signals within short time period"""
        if not signals:
            return signals
        
        last_time = self.last_signal_time.get(instrument, 0)
        current_time = datetime.now().timestamp()
        
        # If last signal was less than 30 minutes ago, skip
        if current_time - last_time < 1800:  # 30 minutes
            print(f"   ⏸️ Skipping duplicate signal (last signal {(current_time - last_time)/60:.1f} min ago)")
            return []
        
        self.last_signal_time[instrument] = current_time
        return signals

    def _calculate_atr(self, instrument: str, candles: List[Dict], period: int = 14):
        """Calculate Average True Range (ATR) for dynamic distance measurement"""
        if len(candles) < period + 1:
            return
        
        true_ranges = []
        
        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        if len(true_ranges) >= period:
            atr = sum(true_ranges[-period:]) / period
            self.atr_values[instrument] = atr

    def _is_bos_too_far(self, instrument: str, reference_level: float, bos_level: float, direction: str) -> bool:
        """Determine if BOS formation is too far from the reference level using ATR"""
        atr = self.atr_values.get(instrument)
        
        if atr is None:
            distance = abs(bos_level - reference_level)
            max_distance = reference_level * 0.02  # 2% fallback
            return distance > max_distance
        
        distance = abs(bos_level - reference_level)
        
        # Increased multiplier to allow more trades - was 2.0, now 3.0
        atr_multiplier = 3.0
        max_allowed_distance = atr * atr_multiplier
        
        is_too_far = distance > max_allowed_distance
        
        if is_too_far:
            print(f"   ⚠️ BOS too far: Distance {distance:.4f} > Max {max_allowed_distance:.4f} ({atr_multiplier}x ATR)")
        else:
            print(f"   ✅ BOS distance OK: {distance:.4f} <= {max_allowed_distance:.4f}")
        
        return is_too_far

    def _calculate_distance_ratio(self, instrument: str, reference_level: float, bos_level: float) -> float:
        """Calculate how many ATRs away the BOS is from the reference level"""
        atr = self.atr_values.get(instrument)
        
        if atr is None or atr == 0:
            return 0
        
        distance = abs(bos_level - reference_level)
        ratio = distance / atr
        
        return ratio

    def _update_previous_day_levels(self, instrument: str, close_prices: List[float], candles: List[Dict]):
        """
        Update or create previous day high/low levels
        ✅ USES LINE GRAPH (close prices only for highs/lows)
        """
        if len(close_prices) < 480:
            return
        
        # Get yesterday's close prices (480 candles = 24 hours on 3min)
        yesterday_closes = close_prices[-960:-480] if len(close_prices) >= 960 else close_prices[-480:]
        
        if not yesterday_closes:
            return
        
        # Calculate previous day high and low FROM LINE GRAPH
        pdh = max(yesterday_closes)
        pdl = min(yesterday_closes)
        
        # Check if levels are broken (using recent close prices)
        recent_closes = close_prices[-100:]
        current_high = max(recent_closes)
        current_low = min(recent_closes)
        
        pdh_broken = current_high > pdh
        pdl_broken = current_low < pdl
        
        self.previous_day_levels[instrument] = {
            'high': pdh,
            'low': pdl,
            'high_broken': pdh_broken,
            'low_broken': pdl_broken,
            'updated_at': datetime.now()
        }

    def _detect_swings_line_graph(self, close_prices: List[float], candles: List[Dict], lookback: int = 3) -> tuple:
        """
        Detect swing highs and swing lows ON LINE GRAPH
        ✅ REDUCED LOOKBACK from 5 to 3 for more sensitivity
        
        Args:
            close_prices: List of close prices (line graph)
            candles: Original candle data (for timestamps)
            lookback: Number of candles to look back (reduced to 3)
        
        Returns:
            Tuple of (swing_highs, swing_lows)
        """
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(close_prices) - lookback):
            # Check for swing high on line graph
            is_swing_high = True
            for j in range(1, lookback + 1):
                if close_prices[i] <= close_prices[i - j] or close_prices[i] <= close_prices[i + j]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'price': close_prices[i],
                    'index': i,
                    'time': candles[i]['time'] if i < len(candles) else None
                })
            
            # Check for swing low on line graph
            is_swing_low = True
            for j in range(1, lookback + 1):
                if close_prices[i] >= close_prices[i - j] or close_prices[i] >= close_prices[i + j]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'price': close_prices[i],
                    'index': i,
                    'time': candles[i]['time'] if i < len(candles) else None
                })
        
        return swing_highs, swing_lows

    def _detect_choch_at_high(self, close_prices: List[float], pdh: float, swing_lows: List[Dict], instrument: str, candles: List[Dict]) -> Optional[Dict]:
        """
        Detect CHOCH (reversal) at previous day high
        ✅ USES LINE GRAPH - close prices only
        """
        if len(close_prices) < 20:
            return None
        
        recent_closes = close_prices[-20:]
        current_price = recent_closes[-1]
        
        # Check if price recently touched PDH (looser tolerance - 0.5%)
        touched_pdh = any(price >= pdh * 0.995 for price in recent_closes)
        
        if not touched_pdh:
            return None
        
        # Find the most recent swing low after touching PDH
        recent_swing_lows = [sl for sl in swing_lows if sl['index'] >= len(close_prices) - 20]
        
        if not recent_swing_lows:
            return None
        
        latest_swing_low = recent_swing_lows[-1]
        
        # Check if current price broke below the swing low (CHOCH confirmation)
        if current_price < latest_swing_low['price']:
            # Find the rejection high (highest close before the drop)
            rejection_high = max(recent_closes[:15])
            
            # Calculate stop loss (above rejection high with small buffer)
            stop_loss = rejection_high + (rejection_high * 0.002)  # 0.2% buffer
            
            print(f"   🎯 CHOCH SELL: Entry={current_price:.4f}, SL={stop_loss:.4f}, Swing={latest_swing_low['price']:.4f}")
            
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

    def _detect_choch_at_low(self, close_prices: List[float], pdl: float, swing_highs: List[Dict], instrument: str, candles: List[Dict]) -> Optional[Dict]:
        """
        Detect CHOCH (reversal) at previous day low
        ✅ USES LINE GRAPH - close prices only
        """
        if len(close_prices) < 20:
            return None
        
        recent_closes = close_prices[-20:]
        current_price = recent_closes[-1]
        
        # Check if price recently touched PDL (looser tolerance - 0.5%)
        touched_pdl = any(price <= pdl * 1.005 for price in recent_closes)
        
        if not touched_pdl:
            return None
        
        # Find the most recent swing high after touching PDL
        recent_swing_highs = [sh for sh in swing_highs if sh['index'] >= len(close_prices) - 20]
        
        if not recent_swing_highs:
            return None
        
        latest_swing_high = recent_swing_highs[-1]
        
        # Check if current price broke above the swing high (CHOCH confirmation)
        if current_price > latest_swing_high['price']:
            # Find the rejection low (lowest close before the rally)
            rejection_low = min(recent_closes[:15])
            
            # Calculate stop loss (below rejection low with small buffer)
            stop_loss = rejection_low - (rejection_low * 0.002)  # 0.2% buffer
            
            print(f"   🎯 CHOCH BUY: Entry={current_price:.4f}, SL={stop_loss:.4f}, Swing={latest_swing_high['price']:.4f}")
            
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

    def _detect_bos_after_high_break(self, close_prices: List[float], pdh: float, swing_highs: List[Dict], instrument: str, candles: List[Dict]) -> Optional[Dict]:
        """
        Detect BOS (continuation) after PDH is broken
        ✅ USES LINE GRAPH - close prices only
        """
        if len(close_prices) < 30:
            return None
        
        recent_closes = close_prices[-30:]
        current_price = recent_closes[-1]
        
        # Check if PDH was recently broken
        broken_pdh = any(price > pdh for price in recent_closes[:20])
        
        if not broken_pdh:
            return None
        
        # Find recent swing high after breaking PDH
        recent_swing_highs = [sh for sh in swing_highs if sh['index'] >= len(close_prices) - 30]
        
        if not recent_swing_highs:
            return None
        
        latest_swing_high = recent_swing_highs[-1]
        bos_level = latest_swing_high['price']
        
        # Check if BOS is too far using ATR-based logic
        if self._is_bos_too_far(instrument, pdh, bos_level, direction='UP'):
            return None
        
        # Check if price broke above the swing high (BOS confirmation)
        if current_price > latest_swing_high['price']:
            # Stop loss below the broken PDH
            stop_loss = pdh - (pdh * 0.002)  # 0.2% below
            
            distance_ratio = self._calculate_distance_ratio(instrument, pdh, bos_level)
            
            print(f"   🎯 BOS BUY: Entry={current_price:.4f}, SL={stop_loss:.4f}, Distance={distance_ratio:.2f}x ATR")
            
            return {
                'instrument': instrument,
                'setup_type': 'BOS',
                'direction': 'BUY',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'reference_level': pdh,
                'swing_break_level': latest_swing_high['price'],
                'distance_ratio': distance_ratio,
                'timestamp': datetime.now()
            }
        
        return None

    def _detect_bos_after_low_break(self, close_prices: List[float], pdl: float, swing_lows: List[Dict], instrument: str, candles: List[Dict]) -> Optional[Dict]:
        """
        Detect BOS (continuation) after PDL is broken
        ✅ USES LINE GRAPH - close prices only
        """
        if len(close_prices) < 30:
            return None
        
        recent_closes = close_prices[-30:]
        current_price = recent_closes[-1]
        
        # Check if PDL was recently broken
        broken_pdl = any(price < pdl for price in recent_closes[:20])
        
        if not broken_pdl:
            return None
        
        # Find recent swing low after breaking PDL
        recent_swing_lows = [sl for sl in swing_lows if sl['index'] >= len(close_prices) - 30]
        
        if not recent_swing_lows:
            return None
        
        latest_swing_low = recent_swing_lows[-1]
        bos_level = latest_swing_low['price']
        
        # Check if BOS is too far using ATR-based logic
        if self._is_bos_too_far(instrument, pdl, bos_level, direction='DOWN'):
            return None
        
        # Check if price broke below the swing low (BOS confirmation)
        if current_price < latest_swing_low['price']:
            # Stop loss above the broken PDL
            stop_loss = pdl + (pdl * 0.002)  # 0.2% above
            
            distance_ratio = self._calculate_distance_ratio(instrument, pdl, bos_level)
            
            print(f"   🎯 BOS SELL: Entry={current_price:.4f}, SL={stop_loss:.4f}, Distance={distance_ratio:.2f}x ATR")
            
            return {
                'instrument': instrument,
                'setup_type': 'BOS',
                'direction': 'SELL',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'reference_level': pdl,
                'swing_break_level': latest_swing_low['price'],
                'distance_ratio': distance_ratio,
                'timestamp': datetime.now()
            }
        
        return None

    def _detect_choch_at_flipped_high(self, close_prices: List[float], pdh: float, swing_highs: List[Dict], instrument: str, candles: List[Dict]) -> Optional[Dict]:
        """Detect CHOCH at flipped PDH (now acting as support)"""
        return self._detect_choch_at_low(close_prices, pdh, swing_highs, instrument, candles)

    def _detect_choch_at_flipped_low(self, close_prices: List[float], pdl: float, swing_lows: List[Dict], instrument: str, candles: List[Dict]) -> Optional[Dict]:
        """Detect CHOCH at flipped PDL (now acting as resistance)"""
        return self._detect_choch_at_high(close_prices, pdl, swing_lows, instrument, candles)

    def get_previous_day_levels(self, instrument: str) -> Dict:
        """Get stored previous day levels for an instrument"""
        return self.previous_day_levels.get(instrument, {})

    def get_atr(self, instrument: str) -> Optional[float]:
        """Get current ATR value for an instrument"""
        return self.atr_values.get(instrument)