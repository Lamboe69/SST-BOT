"""
Line Chart Configuration Module
Ensures the bot operates in line chart mode using only closing prices
"""

class LineChartConfig:
    """Configuration class for line chart trading strategy"""
    
    # Line chart mode settings
    LINE_CHART_MODE = True
    USE_CLOSING_PRICES_ONLY = True
    
    # Chart analysis settings
    SWING_DETECTION_METHOD = "CLOSING_PRICES"  # Use closing prices for swing detection
    LEVEL_BREAK_METHOD = "CLOSING_PRICES"      # Use closing prices for level breaks
    REJECTION_DETECTION_METHOD = "CLOSING_PRICES"  # Use closing prices for rejections
    
    # Trading execution settings
    AUTO_EXECUTE_TRADES = True  # Ensure trades are executed automatically
    TRADE_EXECUTION_ENABLED = True
    
    @classmethod
    def get_config(cls) -> dict:
        """Get line chart configuration as dictionary"""
        return {
            'line_chart_mode': cls.LINE_CHART_MODE,
            'use_closing_prices_only': cls.USE_CLOSING_PRICES_ONLY,
            'swing_detection_method': cls.SWING_DETECTION_METHOD,
            'level_break_method': cls.LEVEL_BREAK_METHOD,
            'rejection_detection_method': cls.REJECTION_DETECTION_METHOD,
            'auto_execute_trades': cls.AUTO_EXECUTE_TRADES,
            'trade_execution_enabled': cls.TRADE_EXECUTION_ENABLED
        }
    
    @classmethod
    def is_line_chart_mode(cls) -> bool:
        """Check if line chart mode is enabled"""
        return cls.LINE_CHART_MODE
    
    @classmethod
    def should_auto_execute(cls) -> bool:
        """Check if trades should be executed automatically"""
        return cls.AUTO_EXECUTE_TRADES and cls.TRADE_EXECUTION_ENABLED

# Global configuration instance
LINE_CHART_CONFIG = LineChartConfig()