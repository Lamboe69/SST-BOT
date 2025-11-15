"""
Trade Management Module
Handles trade monitoring, EOD closure, and trade lifecycle management
"""

import asyncio
from datetime import datetime, time
from typing import Dict, List
import pytz

class TradeManager:
    def __init__(self, oanda_client, db):
        self.oanda_client = oanda_client
        self.db = db
        self.broker_timezone = pytz.timezone('America/New_York')
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """Start trade monitoring loop"""
        self.monitoring_active = True
        print("👁️ Trade monitoring started")
        
        while self.monitoring_active:
            try:
                await self._monitor_trades()
                # EOD closure disabled - trades only close on TP/SL or manual
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Error in trade monitoring: {str(e)}")
                await asyncio.sleep(60)
    
    def stop_monitoring(self):
        """Stop trade monitoring"""
        self.monitoring_active = False
        print("⏹️ Trade monitoring stopped")
    
    async def _monitor_trades(self):
        """Monitor all open trades for TP/SL hits"""
        open_trades = self.db.get_open_trades()
        
        if not open_trades:
            return
        
        # Get current positions from OANDA
        try:
            oanda_trades = await self.oanda_client.get_open_trades()
            oanda_trade_ids = [t['id'] for t in oanda_trades]
            
            for trade in open_trades:
                trade_id = str(trade['trade_id'])
                
                # Check if trade is still open in OANDA
                if trade_id not in oanda_trade_ids:
                    await self._handle_closed_trade(trade)
                else:
                    # Update current price and unrealized P&L
                    await self._update_trade_status(trade)
                    
        except Exception as e:
            print(f"❌ Error monitoring trades: {str(e)}")
    
    async def _update_trade_status(self, trade: Dict):
        """Update trade with current price and unrealized P&L"""
        try:
            current_price = await self.oanda_client.get_current_price(trade['instrument'])
            
            # Calculate unrealized P&L
            if trade['direction'] == 'BUY':
                unrealized_pnl = (current_price - trade['entry_price']) * trade['units']
            else:
                unrealized_pnl = (trade['entry_price'] - current_price) * trade['units']
            
            # Update in database
            self.db.update_trade_current_price(
                trade['trade_id'], 
                current_price, 
                unrealized_pnl
            )
            
        except Exception as e:
            print(f"❌ Error updating trade status: {str(e)}")
    
    async def _handle_closed_trade(self, trade: Dict):
        """Handle a trade that was closed by broker (TP/SL hit)"""
        try:
            # Get exit price
            current_price = await self.oanda_client.get_current_price(trade['instrument'])
            
            # Calculate P&L
            if trade['direction'] == 'BUY':
                pnl = (current_price - trade['entry_price']) * trade['units']
            else:
                pnl = (trade['entry_price'] - current_price) * trade['units']
            
            # Determine exit reason
            exit_reason = self._determine_exit_reason(trade, current_price)
            
            # Close trade in database
            self.db.close_trade(
                trade_id=trade['trade_id'],
                exit_price=current_price,
                pnl=pnl,
                exit_reason=exit_reason,
                exit_time=datetime.now()
            )
            
            # Trade closed successfully
            pass
            
            # Log trade closure
            emoji = "🎯" if exit_reason == "TP" else "🛑" if exit_reason == "SL" else "⚠️"
            pnl_emoji = "💰" if pnl > 0 else "📉"
            
            print(f"{emoji} Trade closed: {trade['instrument']} {trade['direction']}")
            print(f"   {pnl_emoji} P&L: ${pnl:.2f} | Exit: {exit_reason}")
            
        except Exception as e:
            print(f"❌ Error handling closed trade: {str(e)}")
    
    def _determine_exit_reason(self, trade: Dict, exit_price: float) -> str:
        """Determine why the trade was closed"""
        tolerance = 0.0001  # Price tolerance for TP/SL detection
        
        # Check if TP was hit
        if trade['direction'] == 'BUY':
            if exit_price >= (trade['take_profit'] - tolerance):
                return 'TP'
            elif exit_price <= (trade['stop_loss'] + tolerance):
                return 'SL'
        else:  # SELL
            if exit_price <= (trade['take_profit'] + tolerance):
                return 'TP'
            elif exit_price >= (trade['stop_loss'] - tolerance):
                return 'SL'
        
        return 'BROKER'  # Closed by broker for other reasons
    
    async def modify_trade_levels(self, trade_id: int, stop_loss: float = None, take_profit: float = None) -> Dict:
        """Modify stop loss or take profit of an open trade"""
        try:
            # Get trade from database
            trade = self.db.get_trade_by_id(trade_id)
            
            if not trade or trade['status'] != 'OPEN':
                return {'success': False, 'reason': 'Trade not found or not open'}
            
            # Validate new levels
            if stop_loss is not None:
                if not self._validate_stop_loss(trade, stop_loss):
                    return {'success': False, 'reason': 'Invalid stop loss level'}
            
            if take_profit is not None:
                if not self._validate_take_profit(trade, take_profit):
                    return {'success': False, 'reason': 'Invalid take profit level'}
            
            # Modify in OANDA
            result = await self.oanda_client.modify_trade(
                trade_id=str(trade['trade_id']),
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Update database
            updates = {}
            if stop_loss is not None:
                updates['stop_loss'] = stop_loss
            if take_profit is not None:
                updates['take_profit'] = take_profit
            
            self.db.update_trade(trade_id, updates)
            
            print(f"✏️ Modified trade {trade_id}: SL={stop_loss}, TP={take_profit}")
            
            return {'success': True, 'message': 'Trade modified successfully'}
            
        except Exception as e:
            print(f"❌ Error modifying trade: {str(e)}")
            return {'success': False, 'reason': str(e)}
    
    def _validate_stop_loss(self, trade: Dict, new_sl: float) -> bool:
        """Validate new stop loss level"""
        current_price = trade.get('current_price', trade['entry_price'])
        
        if trade['direction'] == 'BUY':
            return new_sl < current_price
        else:
            return new_sl > current_price
    
    def _validate_take_profit(self, trade: Dict, new_tp: float) -> bool:
        """Validate new take profit level"""
        current_price = trade.get('current_price', trade['entry_price'])
        
        if trade['direction'] == 'BUY':
            return new_tp > current_price
        else:
            return new_tp < current_price
    
    async def get_trade_performance_summary(self) -> Dict:
        """Get performance summary of all trades"""
        try:
            closed_trades = self.db.get_closed_trades(limit=1000)
            open_trades = self.db.get_open_trades()
            
            total_trades = len(closed_trades)
            winning_trades = len([t for t in closed_trades if t['pnl'] > 0])
            losing_trades = total_trades - winning_trades
            
            total_pnl = sum([t['pnl'] for t in closed_trades])
            
            # Calculate unrealized P&L
            unrealized_pnl = sum([t.get('unrealized_pnl', 0) for t in open_trades])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Best and worst trades
            best_trade = max([t['pnl'] for t in closed_trades]) if closed_trades else 0
            worst_trade = min([t['pnl'] for t in closed_trades]) if closed_trades else 0
            
            return {
                'total_trades': total_trades,
                'open_trades': len(open_trades),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'unrealized_pnl': unrealized_pnl,
                'net_pnl': total_pnl + unrealized_pnl,
                'best_trade': best_trade,
                'worst_trade': worst_trade
            }
            
        except Exception as e:
            print(f"❌ Error getting performance summary: {str(e)}")
            return {}