"""
Signal Generation Module
Validates CHOCH/BOS entry conditions and generates trading signals
"""

from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from line_chart_config import LINE_CHART_CONFIG

class SignalGenerator:
    def __init__(self, structure_detector, data_module, news_filter, db):
        self.structure_detector = structure_detector
        self.data_module = data_module
        self.news_filter = news_filter
        self.db = db
        self.bos_distance_threshold_pips = 50  # Configurable BOS distance threshold
    
    async def generate_signals(self, instrument: str) -> List[Dict]:
        """Generate trading signals for an instrument using LINE CHART strategy"""
        signals = []
        
        # ENFORCE LINE CHART MODE
        if not LINE_CHART_CONFIG.is_line_chart_mode():
            print(f"⚠️ [{instrument}] FORCING LINE CHART MODE ON")
            LINE_CHART_CONFIG.LINE_CHART_MODE = True
        
        print(f"📈 [{instrument}] Generating signals in LINE CHART MODE (closing prices only)")
        
        try:
            # Check if trading should be paused due to news
            if await self.news_filter.should_pause_trading():
                print(f"⏸️ [{instrument}] Trading paused due to news")
                return signals
            
            # Check total active trade limit (max 3 running at any time)
            total_active_trades = self.db.get_total_active_trades_count()
            config = self.db.get_bot_config()
            max_concurrent_trades = config.get('daily_trade_limit', 3)
            
            if total_active_trades >= max_concurrent_trades:
                print(f"⏸️ [{instrument}] Trade limit reached ({total_active_trades}/{max_concurrent_trades})")
                return signals
            
            # Get real-time data
            candles = await self.data_module.get_real_time_data(instrument, 500)
            
            if not candles:
                print(f"⚠️ [{instrument}] No candle data available")
                return signals
            
            if not await self.data_module.validate_data_quality(candles):
                print(f"⚠️ [{instrument}] Data quality check failed")
                return signals
            
            # Get previous day levels
            levels = await self.data_module.get_previous_day_levels(instrument)
            if not levels:
                print(f"⚠️ [{instrument}] No previous day levels available")
                return signals
            
            # Generate signals based on structure analysis - DIRECT CALL
            structure_signals = self.structure_detector.analyze(instrument, candles)
            
            print(f"🔍 [{instrument}] Structure detector found {len(structure_signals)} raw signals")
            
            # Validate each signal
            for signal in structure_signals:
                validated_signal = await self._validate_signal(signal, levels, candles)
                if validated_signal:
                    signals.append(validated_signal)
                    print(f"✅ [{instrument}] Signal validated: {signal['setup_type']} {signal['direction']}")
                else:
                    print(f"❌ [{instrument}] Signal rejected: {signal['setup_type']} {signal['direction']}")
            
        except Exception as e:
            print(f"❌ Error generating signals for {instrument}: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return signals
    
    async def _validate_signal(self, signal: Dict, levels: Dict, candles: List[Dict]) -> Optional[Dict]:
        """Validate a trading signal against all criteria - RELAXED FOR TESTING"""
        try:
            setup_type = signal['setup_type']
            direction = signal['direction']
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            
            # RELAXED VALIDATION - Accept most signals
            print(f"   Validating {setup_type} {direction} signal...")
            
            # Basic stop loss validation (very lenient)
            if direction == 'BUY' and stop_loss >= entry_price:
                print(f"   Invalid SL for BUY: SL={stop_loss} >= Entry={entry_price}")
                return None
            elif direction == 'SELL' and stop_loss <= entry_price:
                print(f"   Invalid SL for SELL: SL={stop_loss} <= Entry={entry_price}")
                return None
            
            # Skip BOS distance validation for now
            # Skip market conditions validation for now
            
            # Calculate take profit (1:4 RR)
            take_profit = self._calculate_take_profit(entry_price, stop_loss, direction)
            
            # Add validation timestamp
            signal['validated_at'] = datetime.now()
            signal['take_profit'] = take_profit
            signal['risk_reward_ratio'] = 4.0
            
            print(f"   Signal validated: Entry={entry_price:.4f}, SL={stop_loss:.4f}, TP={take_profit:.4f}")
            return signal
            
        except Exception as e:
            print(f"Error validating signal: {str(e)}")
            return None
    
    def _validate_stop_loss(self, entry_price: float, stop_loss: float, direction: str) -> bool:
        """Validate stop loss placement"""
        if direction == 'BUY':
            if stop_loss >= entry_price:
                return False
        else:  # SELL
            if stop_loss <= entry_price:
                return False
        
        # Check minimum stop loss distance (5 pips)
        sl_distance = abs(entry_price - stop_loss)
        min_distance = 0.0005  # 5 pips for most instruments
        
        if sl_distance < min_distance:
            return False
        
        return True
    
    def _validate_bos_distance(self, signal: Dict, levels: Dict) -> bool:
        """Validate BOS is not too far from broken level"""
        entry_price = signal['entry_price']
        reference_level = signal.get('reference_level')
        
        if not reference_level:
            return True
        
        # Calculate distance in pips
        distance = abs(entry_price - reference_level)
        
        # Convert to pips based on instrument
        instrument = signal['instrument']
        if 'JPY' in instrument:
            distance_pips = distance / 0.01
        elif '_' in instrument:  # Forex
            distance_pips = distance / 0.0001
        else:  # Indices
            distance_pips = distance / 1.0
        
        # Check if distance exceeds threshold
        if distance_pips > self.bos_distance_threshold_pips:
            print(f"⚠️ BOS too far from level: {distance_pips:.1f} pips > {self.bos_distance_threshold_pips} pips")
            return False
        
        return True
    
    async def _validate_market_conditions(self) -> bool:
        """Validate current market conditions"""
        # Check if market is open
        if not await self.data_module.is_market_open():
            return False
        
        # Additional market condition checks can be added here
        # - Volatility checks
        # - Spread checks
        # - Liquidity checks
        
        return True
    
    def _calculate_take_profit(self, entry_price: float, stop_loss: float, direction: str) -> float:
        """Calculate take profit at 1:4 risk-reward ratio"""
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * 4
        
        if direction == 'BUY':
            return entry_price + tp_distance
        else:  # SELL
            return entry_price - tp_distance
    
    def set_bos_distance_threshold(self, threshold_pips: float):
        """Set BOS distance threshold in pips"""
        self.bos_distance_threshold_pips = threshold_pips
        print(f"📏 BOS distance threshold set to {threshold_pips} pips")
    
    async def get_signal_statistics(self) -> Dict:
        """Get signal generation statistics"""
        try:
            # Get recent signals from database
            recent_trades = self.db.get_closed_trades(limit=100)
            
            total_signals = len(recent_trades)
            choch_signals = len([t for t in recent_trades if t['setup_type'] == 'CHOCH'])
            bos_signals = len([t for t in recent_trades if t['setup_type'] == 'BOS'])
            
            winning_signals = len([t for t in recent_trades if t['pnl'] > 0])
            win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
            
            return {
                'total_signals': total_signals,
                'choch_signals': choch_signals,
                'bos_signals': bos_signals,
                'win_rate': win_rate,
                'choch_win_rate': self._calculate_setup_win_rate(recent_trades, 'CHOCH'),
                'bos_win_rate': self._calculate_setup_win_rate(recent_trades, 'BOS')
            }
            
        except Exception as e:
            print(f"❌ Error getting signal statistics: {str(e)}")
            return {}
    
    def _calculate_setup_win_rate(self, trades: List[Dict], setup_type: str) -> float:
        """Calculate win rate for specific setup type"""
        setup_trades = [t for t in trades if t['setup_type'] == setup_type]
        if not setup_trades:
            return 0.0
        
        winning_trades = [t for t in setup_trades if t['pnl'] > 0]
        return (len(winning_trades) / len(setup_trades)) * 100