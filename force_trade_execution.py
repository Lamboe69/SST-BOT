#!/usr/bin/env python3
"""
Force Trade Execution Fix
Ensures the bot executes trades by bypassing all filters
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def fix_line_chart_config():
    """Force enable trade execution in line chart config"""
    
    config_content = '''"""
Line Chart Configuration Module
Ensures the bot operates in line chart mode using only closing prices
"""

class LineChartConfig:
    """Configuration class for line chart trading strategy"""
    
    # Line chart mode settings - FORCED ON
    LINE_CHART_MODE = True
    USE_CLOSING_PRICES_ONLY = True
    
    # Chart analysis settings
    SWING_DETECTION_METHOD = "CLOSING_PRICES"
    LEVEL_BREAK_METHOD = "CLOSING_PRICES"
    REJECTION_DETECTION_METHOD = "CLOSING_PRICES"
    
    # Trading execution settings - FORCED ON
    AUTO_EXECUTE_TRADES = True
    TRADE_EXECUTION_ENABLED = True
    
    @classmethod
    def get_config(cls) -> dict:
        """Get line chart configuration as dictionary"""
        return {
            'line_chart_mode': True,
            'use_closing_prices_only': True,
            'swing_detection_method': cls.SWING_DETECTION_METHOD,
            'level_break_method': cls.LEVEL_BREAK_METHOD,
            'rejection_detection_method': cls.REJECTION_DETECTION_METHOD,
            'auto_execute_trades': True,
            'trade_execution_enabled': True
        }
    
    @classmethod
    def is_line_chart_mode(cls) -> bool:
        """Check if line chart mode is enabled - ALWAYS TRUE"""
        return True
    
    @classmethod
    def should_auto_execute(cls) -> bool:
        """Check if trades should be executed automatically - ALWAYS TRUE"""
        return True

# Global configuration instance
LINE_CHART_CONFIG = LineChartConfig()
'''
    
    with open('line_chart_config.py', 'w') as f:
        f.write(config_content)
    
    print("Line chart config updated - trade execution FORCED ON")

def update_env_for_aggressive_trading():
    """Update .env for more aggressive trading"""
    
    env_content = f"""# OANDA API Configuration
OANDA_API_KEY={os.getenv('OANDA_API_KEY')}
OANDA_ACCOUNT_ID={os.getenv('OANDA_ACCOUNT_ID')}
OANDA_ENVIRONMENT=practice

# Trading Configuration - AGGRESSIVE SETTINGS
RISK_PERCENTAGE=1.0
BALANCE_METHOD=current
DAILY_TRADE_LIMIT=10
NEWS_FILTER=False

# Instruments to Trade (comma-separated)
INSTRUMENTS=NAS100_USD,EU50_EUR,JP225_USD,USD_CAD,USD_JPY

# Database
DB_PATH=trading_bot.db

# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Advanced Settings - RELAXED FOR MORE TRADES
BOS_DISTANCE_THRESHOLD_PIPS=100
MAX_DAILY_LOSS_PERCENT=10.0
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(".env updated with aggressive trading settings")

if __name__ == "__main__":
    print("Forcing trade execution settings...")
    fix_line_chart_config()
    update_env_for_aggressive_trading()
    print("Trade execution fixes applied!")
    print("Restart the bot to apply changes.")