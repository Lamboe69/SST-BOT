#!/usr/bin/env python3
"""
Reset Trade Limits
Clears any trade limits that might be preventing execution
"""

import sqlite3
import os
from datetime import datetime

def reset_database_limits():
    """Reset all trade limits in the database"""
    
    db_path = "trading_bot.db"
    
    if not os.path.exists(db_path):
        print("Database not found - will be created on bot startup")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Reset daily trade count
        cursor.execute("DELETE FROM trades WHERE status = 'OPEN'")
        print(f"Cleared open trades: {cursor.rowcount}")
        
        # Update bot config for aggressive trading
        cursor.execute("""
            UPDATE bot_config 
            SET value = ? 
            WHERE key = 'daily_trade_limit'
        """, ('10',))
        
        cursor.execute("""
            UPDATE bot_config 
            SET value = ? 
            WHERE key = 'news_filter'
        """, ('False',))
        
        cursor.execute("""
            UPDATE bot_config 
            SET value = ? 
            WHERE key = 'risk_percentage'
        """, ('1.0',))
        
        # Insert config if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO bot_config (key, value) 
            VALUES ('daily_trade_limit', '10')
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO bot_config (key, value) 
            VALUES ('news_filter', 'False')
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO bot_config (key, value) 
            VALUES ('risk_percentage', '1.0')
        """)
        
        conn.commit()
        conn.close()
        
        print("Database limits reset successfully!")
        print("- Daily trade limit: 10")
        print("- News filter: Disabled")
        print("- Risk percentage: 1%")
        
    except Exception as e:
        print(f"Error resetting database: {str(e)}")

if __name__ == "__main__":
    print("Resetting trade limits...")
    reset_database_limits()
    print("Trade limits reset complete!")