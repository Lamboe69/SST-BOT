# OANDA API Configuration
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_account_id_here
OANDA_ENVIRONMENT=practice  # or 'live'

# Trading Configuration
RISK_PERCENTAGE=2.0
BALANCE_METHOD=current  # or 'initial'
DAILY_TRADE_LIMIT=3
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