"""
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
