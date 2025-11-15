"""
Database Module
Handles all database operations using SQLite
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, date
import json

class Database:
    def __init__(self, db_path: str = "trading_bot.db"):
        """
        Initialize Database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
    
    def initialize(self):
        """Create database tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Previous day levels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS previous_day_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument TEXT NOT NULL,
                date DATE NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                is_high_broken BOOLEAN DEFAULT 0,
                is_low_broken BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(instrument, date)
            )
        """)
        
        # Open trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS open_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                instrument TEXT NOT NULL,
                direction TEXT NOT NULL,
                setup_type TEXT NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                units REAL NOT NULL,
                risk_amount REAL NOT NULL,
                potential_profit REAL NOT NULL,
                unrealized_pnl REAL DEFAULT 0,
                entry_time TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'OPEN'
            )
        """)
        
        # Closed trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS closed_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                instrument TEXT NOT NULL,
                direction TEXT NOT NULL,
                setup_type TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                units REAL NOT NULL,
                risk_amount REAL NOT NULL,
                pnl REAL NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP NOT NULL,
                exit_reason TEXT NOT NULL
            )
        """)
        
        # Bot settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Initialize default settings if not exist
        cursor.execute("SELECT COUNT(*) FROM bot_settings")
        if cursor.fetchone()[0] == 0:
            default_settings = {
                'risk_percentage': 2,
                'balance_method': 'current',
                'news_filter': False,
                'daily_trade_limit': 3,
                'atr_multiplier': 2.0,
                'max_daily_loss': 5,
                'instruments': ['NAS100_USD', 'EU50_EUR', 'JP225_USD', 'USD_CAD', 'USD_JPY']
            }
            for key, value in default_settings.items():
                cursor.execute("""
                    INSERT INTO bot_settings (setting_name, setting_value)
                    VALUES (?, ?)
                """, (key, json.dumps(value)))
        
        # Daily stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                trades_taken INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                balance_start REAL DEFAULT 0,
                balance_end REAL DEFAULT 0
            )
        """)
        
        self.conn.commit()
        print("✅ Database tables initialized")
    
    def save_trade(self, trade_data: Dict):
        """Save a new open trade"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO open_trades (
                trade_id, instrument, direction, setup_type, entry_price,
                stop_loss, take_profit, units, risk_amount, potential_profit, entry_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data['trade_id'],
            trade_data['instrument'],
            trade_data['direction'],
            trade_data['setup_type'],
            trade_data['entry_price'],
            trade_data['stop_loss'],
            trade_data['take_profit'],
            trade_data['units'],
            trade_data['risk_amount'],
            trade_data['potential_profit'],
            trade_data['entry_time']
        ))
        
        self.conn.commit()
        
        # Update daily stats
        self._update_daily_stats(trades_taken=1)
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM open_trades WHERE status = 'OPEN'")
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_trade_by_id(self, trade_id: int) -> Optional[Dict]:
        """Get a specific trade by database ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM open_trades WHERE id = ?", (trade_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_trade_current_price(self, trade_id: str, current_price: float, unrealized_pnl: float):
        """Update current price and unrealized P&L for a trade"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE open_trades 
            SET current_price = ?, unrealized_pnl = ?
            WHERE trade_id = ?
        """, (current_price, unrealized_pnl, trade_id))
        
        self.conn.commit()
    
    def update_trade(self, trade_id: int, updates: Dict):
        """Update trade fields"""
        cursor = self.conn.cursor()
        
        # Build dynamic update query
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [trade_id]
        
        cursor.execute(f"""
            UPDATE open_trades 
            SET {set_clause}
            WHERE id = ?
        """, values)
        
        self.conn.commit()
    
    def close_trade(self, trade_id: str, exit_price: float, pnl: float, exit_reason: str, exit_time: datetime):
        """Close a trade and move it to closed_trades table"""
        cursor = self.conn.cursor()
        
        # Get trade from open_trades
        cursor.execute("SELECT * FROM open_trades WHERE trade_id = ?", (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            return
        
        trade = dict(trade)
        
        # Insert into closed_trades
        cursor.execute("""
            INSERT INTO closed_trades (
                trade_id, instrument, direction, setup_type, entry_price, exit_price,
                stop_loss, take_profit, units, risk_amount, pnl, entry_time, exit_time, exit_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade['trade_id'],
            trade['instrument'],
            trade['direction'],
            trade['setup_type'],
            trade['entry_price'],
            exit_price,
            trade['stop_loss'],
            trade['take_profit'],
            trade['units'],
            trade['risk_amount'],
            pnl,
            trade['entry_time'],
            exit_time,
            exit_reason
        ))
        
        # Delete from open_trades
        cursor.execute("DELETE FROM open_trades WHERE trade_id = ?", (trade_id,))
        
        self.conn.commit()
        
        # Update daily stats
        winning = 1 if pnl > 0 else 0
        losing = 1 if pnl < 0 else 0
        self._update_daily_stats(winning_trades=winning, losing_trades=losing, total_pnl=pnl)
    
    def get_closed_trades(self, limit: int = 50) -> List[Dict]:
        """Get closed trades history"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM closed_trades 
            ORDER BY exit_time DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_today_trades_count(self) -> int:
        """Get number of trades taken today"""
        cursor = self.conn.cursor()
        today = date.today()
        
        # Count from closed trades opened today
        cursor.execute("""
            SELECT COUNT(*) FROM closed_trades 
            WHERE DATE(entry_time) = ?
        """, (today,))
        closed_count = cursor.fetchone()[0]
        
        # Count from open trades opened today
        cursor.execute("""
            SELECT COUNT(*) FROM open_trades 
            WHERE DATE(entry_time) = ?
        """, (today,))
        open_count = cursor.fetchone()[0]
        
        return closed_count + open_count
    
    def get_total_active_trades_count(self) -> int:
        """Get total number of active trades (including from previous days)"""
        cursor = self.conn.cursor()
        
        # Count all open trades regardless of entry date
        cursor.execute("SELECT COUNT(*) FROM open_trades WHERE status = 'OPEN'")
        return cursor.fetchone()[0]
    
    def get_today_pnl(self) -> float:
        """Get today's total P&L"""
        cursor = self.conn.cursor()
        today = date.today()
        
        # Get realized P&L from closed trades
        cursor.execute("""
            SELECT COALESCE(SUM(pnl), 0) FROM closed_trades 
            WHERE DATE(exit_time) = ?
        """, (today,))
        realized_pnl = cursor.fetchone()[0]
        
        # Get unrealized P&L from open trades
        cursor.execute("""
            SELECT COALESCE(SUM(unrealized_pnl), 0) FROM open_trades 
            WHERE DATE(entry_time) = ?
        """, (today,))
        unrealized_pnl = cursor.fetchone()[0]
        
        return realized_pnl + unrealized_pnl
    
    def save_bot_config(self, config: Dict):
        """Save bot configuration"""
        cursor = self.conn.cursor()
        
        for key, value in config.items():
            cursor.execute("""
                INSERT OR REPLACE INTO bot_settings (setting_name, setting_value, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value)))
        
        self.conn.commit()
    
    def update_setting(self, setting_name: str, setting_value):
        """Update a single setting"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO bot_settings (setting_name, setting_value, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (setting_name, json.dumps(setting_value)))
        self.conn.commit()
    
    def get_setting(self, setting_name: str):
        """Get a single setting value"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT setting_value FROM bot_settings WHERE setting_name = ?", (setting_name,))
        row = cursor.fetchone()
        return json.loads(row['setting_value']) if row else None
    
    def get_bot_config(self) -> Dict:
        """Get bot configuration"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT setting_name, setting_value FROM bot_settings")
        
        rows = cursor.fetchall()
        config = {}
        
        for row in rows:
            config[row['setting_name']] = json.loads(row['setting_value'])
        
        return config
    
    def _update_daily_stats(self, trades_taken: int = 0, winning_trades: int = 0, 
                           losing_trades: int = 0, total_pnl: float = 0):
        """Update daily statistics"""
        cursor = self.conn.cursor()
        today = date.today()
        
        cursor.execute("""
            INSERT INTO daily_stats (date, trades_taken, winning_trades, losing_trades, total_pnl)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                trades_taken = trades_taken + ?,
                winning_trades = winning_trades + ?,
                losing_trades = losing_trades + ?,
                total_pnl = total_pnl + ?
        """, (today, trades_taken, winning_trades, losing_trades, total_pnl,
              trades_taken, winning_trades, losing_trades, total_pnl))
        
        self.conn.commit()
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        cursor = self.conn.cursor()
        
        # Total trades
        cursor.execute("SELECT COUNT(*) FROM closed_trades")
        total_trades = cursor.fetchone()[0]
        
        # Winning trades
        cursor.execute("SELECT COUNT(*) FROM closed_trades WHERE pnl > 0")
        winning_trades = cursor.fetchone()[0]
        
        # Total P&L
        cursor.execute("SELECT COALESCE(SUM(pnl), 0) FROM closed_trades")
        total_pnl = cursor.fetchone()[0]
        
        # Average R:R
        cursor.execute("""
            SELECT AVG(ABS(pnl / risk_amount)) FROM closed_trades WHERE pnl > 0
        """)
        avg_rr = cursor.fetchone()[0] or 0
        
        # Best trade
        cursor.execute("SELECT MAX(pnl) FROM closed_trades")
        best_trade = cursor.fetchone()[0] or 0
        
        # Worst trade
        cursor.execute("SELECT MIN(pnl) FROM closed_trades")
        worst_trade = cursor.fetchone()[0] or 0
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'average_rr': avg_rr,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }
    
    def save_previous_day_levels(self, level_data: Dict):
        """Save previous day levels"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO previous_day_levels (
                instrument, date, high_price, low_price, is_high_broken, is_low_broken
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            level_data['instrument'],
            level_data['date'],
            level_data['high_price'],
            level_data['low_price'],
            level_data['is_high_broken'],
            level_data['is_low_broken']
        ))
        
        self.conn.commit()
    
    def get_previous_day_levels(self, instrument: str) -> Optional[Dict]:
        """Get previous day levels for an instrument"""
        cursor = self.conn.cursor()
        today = date.today()
        
        cursor.execute("""
            SELECT * FROM previous_day_levels 
            WHERE instrument = ? AND date = ?
        """, (instrument, today))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_level_status(self, instrument: str, high_broken: bool = None, low_broken: bool = None):
        """Update broken status of levels"""
        cursor = self.conn.cursor()
        today = date.today()
        
        updates = []
        values = []
        
        if high_broken is not None:
            updates.append("is_high_broken = ?")
            values.append(high_broken)
        
        if low_broken is not None:
            updates.append("is_low_broken = ?")
            values.append(low_broken)
        
        if updates:
            values.extend([instrument, today])
            cursor.execute(f"""
                UPDATE previous_day_levels 
                SET {', '.join(updates)}
                WHERE instrument = ? AND date = ?
            """, values)
            
            self.conn.commit()
    
    def reset_daily_stats(self):
        """Reset daily statistics for new day"""
        cursor = self.conn.cursor()
        today = date.today()
        
        cursor.execute("""
            INSERT OR IGNORE INTO daily_stats (date, trades_taken, winning_trades, losing_trades, total_pnl)
            VALUES (?, 0, 0, 0, 0.0)
        """, (today,))
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()