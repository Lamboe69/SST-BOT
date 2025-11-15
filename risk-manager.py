"""
Risk Management Module
Handles position sizing, risk calculations, and risk limits
"""

from typing import Dict, Optional
from datetime import datetime

class RiskManager:
    def __init__(
        self,
        risk_percentage: float = 2.0,
        balance_method: str = "current",
        initial_balance: float = 0.0,
        max_daily_loss_pct: Optional[float] = None
    ):
        """
        Initialize Risk Manager
        
        Args:
            risk_percentage: Percentage of balance to risk per trade (1-4%)
            balance_method: 'initial' or 'current' - which balance to base risk on
            initial_balance: Starting account balance
            max_daily_loss_pct: Maximum daily loss percentage (optional)
        """
        self.risk_percentage = risk_percentage
        self.balance_method = balance_method
        self.initial_balance = initial_balance
        self.max_daily_loss_pct = max_daily_loss_pct
        
        # Track daily stats
        self.daily_start_balance = initial_balance
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
    
    def calculate_position_size(
        self,
        current_balance: float,
        entry_price: float,
        stop_loss: float,
        instrument: str
    ) -> Dict:
        """
        Calculate position size based on risk parameters
        
        Args:
            current_balance: Current account balance
            entry_price: Planned entry price
            stop_loss: Stop loss price
            instrument: Trading instrument
        
        Returns:
            Dictionary with position sizing details
        """
        # Determine which balance to use
        balance = self.initial_balance if self.balance_method == "initial" else current_balance
        
        # Calculate risk amount in dollars
        risk_amount = balance * (self.risk_percentage / 100)
        
        # Calculate stop loss distance in price
        sl_distance_price = abs(entry_price - stop_loss)
        
        # Determine pip value based on instrument type
        if "JPY" in instrument:
            # For JPY pairs, pip is 0.01
            pip_value = 0.01
            sl_distance_pips = sl_distance_price / pip_value
        elif "_" in instrument:
            # For other forex pairs, pip is 0.0001
            pip_value = 0.0001
            sl_distance_pips = sl_distance_price / pip_value
        else:
            # For indices, use point values
            pip_value = 1.0
            sl_distance_pips = sl_distance_price / pip_value
        
        # Calculate position size (units)
        # Position Size = Risk Amount / Stop Loss Distance
        units = int(risk_amount / sl_distance_price)
        
        # Ensure minimum position size
        if units < 1:
            units = 1
        
        # Calculate actual risk with rounded units
        actual_risk = units * sl_distance_price
        
        # Calculate potential profit (1:4 RR)
        tp_distance_price = sl_distance_price * 4
        potential_profit = units * tp_distance_price
        
        return {
            "units": units,
            "risk_amount": actual_risk,
            "risk_percentage": (actual_risk / balance) * 100,
            "potential_profit": potential_profit,
            "reward_risk_ratio": 4.0,
            "stop_loss_distance_pips": sl_distance_pips,
            "balance_used": balance,
            "balance_method": self.balance_method
        }
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float, direction: str) -> float:
        """
        Calculate take profit price based on 1:4 risk-reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: 'BUY' or 'SELL'
        
        Returns:
            Take profit price
        """
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * 4  # 1:4 RR
        
        if direction == "BUY":
            take_profit = entry_price + tp_distance
        else:  # SELL
            take_profit = entry_price - tp_distance
        
        return take_profit
    
    def can_take_trade(self, current_balance: float, daily_pnl: float) -> Dict:
        """
        Check if a new trade can be taken based on risk limits
        
        Args:
            current_balance: Current account balance
            daily_pnl: Today's profit/loss
        
        Returns:
            Dictionary with permission and reason
        """
        # Reset daily stats if new day
        self._check_daily_reset()
        
        # Check maximum daily loss limit
        if self.max_daily_loss_pct is not None:
            max_daily_loss = self.daily_start_balance * (self.max_daily_loss_pct / 100)
            
            if daily_pnl < 0 and abs(daily_pnl) >= max_daily_loss:
                return {
                    "allowed": False,
                    "reason": f"Maximum daily loss limit reached ({abs(daily_pnl):.2f} / {max_daily_loss:.2f})"
                }
        
        # Check if account balance is too low
        min_balance = 50  # Minimum $50 to trade
        if current_balance < min_balance:
            return {
                "allowed": False,
                "reason": f"Account balance too low (${current_balance:.2f} < ${min_balance:.2f})"
            }
        
        return {
            "allowed": True,
            "reason": "All risk checks passed"
        }
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L tracking"""
        self._check_daily_reset()
        self.daily_pnl += pnl
    
    def _check_daily_reset(self):
        """Check if we need to reset daily stats (new day)"""
        today = datetime.now().date()
        
        if today > self.last_reset_date:
            # New day - reset stats
            self.last_reset_date = today
            self.daily_pnl = 0.0
            print(f"📅 Daily stats reset for {today}")
    
    def set_risk_percentage(self, risk_pct: float):
        """Update risk percentage (1-4%)"""
        if 0 < risk_pct <= 4:
            self.risk_percentage = risk_pct
        else:
            raise ValueError("Risk percentage must be between 0 and 4%")
    
    def set_balance_method(self, method: str):
        """Update balance calculation method"""
        if method in ["initial", "current"]:
            self.balance_method = method
        else:
            raise ValueError("Balance method must be 'initial' or 'current'")
    
    def get_risk_stats(self) -> Dict:
        """Get current risk statistics"""
        return {
            "risk_percentage": self.risk_percentage,
            "balance_method": self.balance_method,
            "initial_balance": self.initial_balance,
            "daily_pnl": self.daily_pnl,
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "last_reset_date": str(self.last_reset_date)
        }
    
    def calculate_lot_size_forex(
        self,
        risk_amount: float,
        stop_loss_pips: float,
        pip_value_per_lot: float = 10.0
    ) -> float:
        """
        Calculate lot size for forex trading
        
        Args:
            risk_amount: Amount willing to risk
            stop_loss_pips: Stop loss in pips
            pip_value_per_lot: Value of 1 pip for 1 standard lot (default $10)
        
        Returns:
            Lot size
        """
        # Lot Size = Risk Amount / (Stop Loss Pips × Pip Value per Lot)
        lot_size = risk_amount / (stop_loss_pips * pip_value_per_lot)
        
        # Round to 2 decimal places (mini lots)
        lot_size = round(lot_size, 2)
        
        # Ensure minimum lot size
        if lot_size < 0.01:
            lot_size = 0.01
        
        return lot_size
    
    def validate_stop_loss(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str,
        min_sl_distance_pips: float = 5.0
    ) -> Dict:
        """
        Validate stop loss placement
        
        Args:
            entry_price: Entry price
            stop_loss: Proposed stop loss
            direction: 'BUY' or 'SELL'
            min_sl_distance_pips: Minimum stop loss distance
        
        Returns:
            Validation result
        """
        sl_distance = abs(entry_price - stop_loss)
        
        # Check direction is correct
        if direction == "BUY" and stop_loss >= entry_price:
            return {
                "valid": False,
                "reason": "Stop loss must be below entry for BUY trades"
            }
        
        if direction == "SELL" and stop_loss <= entry_price:
            return {
                "valid": False,
                "reason": "Stop loss must be above entry for SELL trades"
            }
        
        # Check minimum distance
        if sl_distance < (min_sl_distance_pips * 0.0001):  # Convert pips to price
            return {
                "valid": False,
                "reason": f"Stop loss too close (min {min_sl_distance_pips} pips)"
            }
        
        return {
            "valid": True,
            "reason": "Stop loss valid",
            "distance_pips": sl_distance / 0.0001
        }