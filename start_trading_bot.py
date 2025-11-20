#!/usr/bin/env python3
"""
Start Trading Bot with Forced Execution
Ensures the bot starts with all trade execution enabled
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force trade execution settings
os.environ['TRADE_EXECUTION_ENABLED'] = 'True'
os.environ['AUTO_EXECUTE_TRADES'] = 'True'
os.environ['NEWS_FILTER'] = 'False'
os.environ['DAILY_TRADE_LIMIT'] = '10'

print("Starting Smart Structure Trading Bot with FORCED EXECUTION...")
print("Trade execution: ENABLED")
print("News filter: DISABLED") 
print("Daily trade limit: 10")
print("Risk per trade: 1%")

# Import and run the main bot
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
except Exception as e:
    print(f"Error starting bot: {str(e)}")
    sys.exit(1)