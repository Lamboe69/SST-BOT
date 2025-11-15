"""
Setup Script for Smart Structure Trading Bot
Run this script to set up the bot for first-time use
"""

import os
import shutil
from pathlib import Path

def setup_bot():
    """Setup the trading bot environment"""
    print("🤖 Setting up Smart Structure Trading Bot...")
    
    # Create .env file from example if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file with your OANDA credentials")
        else:
            print("❌ .env.example file not found")
    else:
        print("✅ .env file already exists")
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    print("✅ Created logs directory")
    
    # Create data directory for database
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    print("✅ Created data directory")
    
    # Check if database exists
    db_path = 'trading_bot.db'
    if not os.path.exists(db_path):
        print("📊 Database will be created on first run")
    else:
        print("✅ Database already exists")
    
    print("\n🎯 Setup Complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your OANDA API credentials")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the bot: python main.py")
    print("\n📖 See README.md for detailed instructions")

if __name__ == "__main__":
    setup_bot()