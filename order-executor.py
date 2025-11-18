"""
Order Execution Module
Handles trade execution, monitoring, and management
"""

from typing import Dict, Optional, List
from datetime import datetime
import asyncio
from line_chart_config import LINE_CHART_CONFIG

class OrderExecutor:
    def __init__(self, oanda_client, risk_manager, db):
        """
        Initialize Order Executor
        
        Args:
            oanda_client: OANDA client instance
            risk_manager: Risk manager instance
            db: Database instance
        """
        self.oanda_client = oanda_client
        self.risk_manager = risk_manager
        self.db = db
    
    async def execute_signal(self, signal: Dict) -> Dict:
        """
        Execute a trading signal - FORCED EXECUTION MODE
        
        Args:
            signal: Signal dictionary from structure detector
        
        Returns:
            Execution result
        """
        # FORCE TRADE EXECUTION
        if not LINE_CHART_CONFIG.should_auto_execute():
            print(f"⚠️ FORCING TRADE EXECUTION ON - was disabled!")
            LINE_CHART_CONFIG.AUTO_EXECUTE_TRADES = True
            LINE_CHART_CONFIG.TRADE_EXECUTION_ENABLED = True
        
        print(f"🚀 EXECUTING TRADE: {signal.get('setup_type')} {signal.get('direction')} on {signal.get('instrument')}")
        
        try:
            instrument = signal['instrument']
            direction = signal['direction']
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            setup_type = signal['setup_type']
            
            # Get current account balance
            account_info = await self.oanda_client.get_account_info()
            current_balance = float(account_info['balance'])
            
            # Check if we can take this trade
            daily_pnl = self.db.get_today_pnl()
            risk_check = self.risk_manager.can_take_trade(current_balance, daily_pnl)
            
            if not risk_check['allowed']:
                print(f"⛔ Trade rejected: {risk_check['reason']}")
                return {
                    'success': False,
                    'reason': risk_check['reason']
                }
            
            # Calculate take profit (1:4 RR)
            take_profit = self.risk_manager.calculate_take_profit(
                entry_price=entry_price,
                stop_loss=stop_loss,
                direction=direction
            )
            
            # Calculate position size
            position_info = self.risk_manager.calculate_position_size(
                current_balance=current_balance,
                entry_price=entry_price,
                stop_loss=stop_loss,
                instrument=instrument
            )
            
            units = position_info['units']
            
            # Adjust units for direction (negative for SELL)
            if direction == "SELL":
                units = -units
            
            print(f"📊 Executing {direction} trade on {instrument}")
            print(f"   Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}")
            print(f"   Units: {units}, Risk: ${position_info['risk_amount']:.2f}")
            
            # Place the order
            order_result = await self.oanda_client.place_market_order(
                instrument=instrument,
                units=units,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Extract trade details from order result
            if 'orderFillTransaction' in order_result:
                fill = order_result['orderFillTransaction']
                trade_id = fill.get('id')
                actual_entry = float(fill.get('price', entry_price))
                
                # Save trade to database
                trade_data = {
                    'trade_id': trade_id,
                    'instrument': instrument,
                    'direction': direction,
                    'setup_type': setup_type,
                    'entry_price': actual_entry,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'units': abs(units),
                    'risk_amount': position_info['risk_amount'],
                    'potential_profit': position_info['potential_profit'],
                    'entry_time': datetime.now(),
                    'status': 'OPEN'
                }
                
                self.db.save_trade(trade_data)
                
                print(f"✅ Trade executed successfully! Trade ID: {trade_id}")
                
                return {
                    'success': True,
                    'trade_id': trade_id,
                    'entry_price': actual_entry,
                    'message': f'{direction} trade opened on {instrument}'
                }
            else:
                print(f"❌ Order failed: {order_result}")
                return {
                    'success': False,
                    'reason': 'Order not filled',
                    'details': order_result
                }
        
        except Exception as e:
            print(f"❌ Error executing signal: {str(e)}")
            return {
                'success': False,
                'reason': str(e)
            }
    
    async def monitor_open_trades(self):
        """Monitor all open trades for TP/SL hits or manual management"""
        try:
            # Get open trades from database
            open_trades = self.db.get_open_trades()
            
            if not open_trades:
                return
            
            # Get current positions from OANDA
            oanda_trades = await self.oanda_client.get_open_trades()
            oanda_trade_ids = [t['id'] for t in oanda_trades]
            
            # Check each trade
            for trade in open_trades:
                trade_id = str(trade['trade_id'])
                
                # If trade is not in OANDA (closed), update database
                if trade_id not in oanda_trade_ids:
                    await self._handle_closed_trade(trade)
                else:
                    # Trade still open - update current price
                    current_price = await self.oanda_client.get_current_price(trade['instrument'])
                    
                    # Calculate unrealized P&L
                    if trade['direction'] == 'BUY':
                        unrealized_pnl = (current_price - trade['entry_price']) * trade['units']
                    else:
                        unrealized_pnl = (trade['entry_price'] - current_price) * trade['units']
                    
                    # Update trade in database
                    self.db.update_trade_current_price(trade_id, current_price, unrealized_pnl)
        
        except Exception as e:
            print(f"❌ Error monitoring trades: {str(e)}")
    
    async def _handle_closed_trade(self, trade: Dict):
        """Handle a trade that was closed (TP/SL hit or manual)"""
        try:
            trade_id = str(trade['trade_id'])
            
            # Get trade details from OANDA to determine exit reason
            try:
                trade_details = await self.oanda_client.get_trade_details(trade_id)
                
                # This shouldn't happen if trade is closed, but check anyway
                if trade_details.get('state') == 'OPEN':
                    return
            except:
                # Trade not found in OANDA = it's closed
                pass
            
            # Get current price as exit price
            exit_price = await self.oanda_client.get_current_price(trade['instrument'])
            
            # Calculate P&L
            if trade['direction'] == 'BUY':
                pnl = (exit_price - trade['entry_price']) * trade['units']
            else:
                pnl = (trade['entry_price'] - exit_price) * trade['units']
            
            # Determine exit reason
            exit_reason = 'UNKNOWN'
            
            # Check if TP was hit
            if trade['direction'] == 'BUY' and exit_price >= trade['take_profit']:
                exit_reason = 'TP'
            elif trade['direction'] == 'SELL' and exit_price <= trade['take_profit']:
                exit_reason = 'TP'
            # Check if SL was hit
            elif trade['direction'] == 'BUY' and exit_price <= trade['stop_loss']:
                exit_reason = 'SL'
            elif trade['direction'] == 'SELL' and exit_price >= trade['stop_loss']:
                exit_reason = 'SL'
            
            # Close trade in database
            self.db.close_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                pnl=pnl,
                exit_reason=exit_reason,
                exit_time=datetime.now()
            )
            
            # Update risk manager with P&L
            self.risk_manager.update_daily_pnl(pnl)
            
            exit_emoji = "🎯" if exit_reason == "TP" else "🛑" if exit_reason == "SL" else "⚠️"
            pnl_emoji = "💰" if pnl > 0 else "📉"
            
            print(f"{exit_emoji} Trade closed: {trade['instrument']} {trade['direction']}")
            print(f"   {pnl_emoji} P&L: ${pnl:.2f} | Exit: {exit_reason}")
        
        except Exception as e:
            print(f"❌ Error handling closed trade: {str(e)}")
    
    async def modify_trade(self, trade_id: int, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict:
        """
        Modify stop loss or take profit of an open trade
        
        Args:
            trade_id: Database trade ID
            stop_loss: New stop loss price
            take_profit: New take profit price
        
        Returns:
            Modification result
        """
        try:
            # Get trade from database
            trade = self.db.get_trade_by_id(trade_id)
            
            if not trade:
                return {
                    'success': False,
                    'reason': 'Trade not found'
                }
            
            if trade['status'] != 'OPEN':
                return {
                    'success': False,
                    'reason': 'Trade is not open'
                }
            
            # Modify trade in OANDA
            oanda_trade_id = str(trade['trade_id'])
            result = await self.oanda_client.modify_trade(
                trade_id=oanda_trade_id,
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
            
            print(f"✏️ Trade {trade_id} modified: SL={stop_loss}, TP={take_profit}")
            
            return {
                'success': True,
                'message': 'Trade modified successfully'
            }
        
        except Exception as e:
            print(f"❌ Error modifying trade: {str(e)}")
            return {
                'success': False,
                'reason': str(e)
            }
    
    async def close_trade(self, trade_id: int, reason: str = "MANUAL") -> Dict:
        """
        Manually close a trade
        
        Args:
            trade_id: Database trade ID
            reason: Reason for closing
        
        Returns:
            Close result
        """
        try:
            # Get trade from database
            trade = self.db.get_trade_by_id(trade_id)
            
            if not trade:
                return {
                    'success': False,
                    'reason': 'Trade not found'
                }
            
            if trade['status'] != 'OPEN':
                return {
                    'success': False,
                    'reason': 'Trade is already closed'
                }
            
            # Close trade in OANDA
            oanda_trade_id = str(trade['trade_id'])
            result = await self.oanda_client.close_trade(oanda_trade_id)
            
            # Get exit price
            exit_price = await self.oanda_client.get_current_price(trade['instrument'])
            
            # Calculate P&L
            if trade['direction'] == 'BUY':
                pnl = (exit_price - trade['entry_price']) * trade['units']
            else:
                pnl = (trade['entry_price'] - exit_price) * trade['units']
            
            # Update database
            self.db.close_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                pnl=pnl,
                exit_reason=reason,
                exit_time=datetime.now()
            )
            
            # Update risk manager
            self.risk_manager.update_daily_pnl(pnl)
            
            print(f"🔒 Trade {trade_id} closed manually: P&L = ${pnl:.2f}")
            
            return {
                'success': True,
                'message': 'Trade closed successfully',
                'pnl': pnl
            }
        
        except Exception as e:
            print(f"❌ Error closing trade: {str(e)}")
            return {
                'success': False,
                'reason': str(e)
            }
    
    async def close_all_trades(self, reason: str = "EOD") -> Dict:
        """Close all open trades (e.g., at end of day)"""
        try:
            open_trades = self.db.get_open_trades()
            results = []
            
            for trade in open_trades:
                result = await self.close_trade(trade['id'], reason)
                results.append(result)
            
            successful = sum(1 for r in results if r['success'])
            
            return {
                'success': True,
                'message': f'Closed {successful}/{len(open_trades)} trades',
                'results': results
            }
        
        except Exception as e:
            return {
                'success': False,
                'reason': str(e)
            }