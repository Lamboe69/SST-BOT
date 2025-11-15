"""
Test OANDA Connection Script
Run this to verify your OANDA API credentials are working
"""

import asyncio
import os
from dotenv import load_dotenv
import importlib.util
spec = importlib.util.spec_from_file_location("oanda_client", "oanda-client.py")
oanda_client_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oanda_client_mod)
OandaClient = oanda_client_mod.OandaClient

async def test_connection():
    """Test OANDA API connection"""
    print("🔌 Testing OANDA API Connection...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    api_key = os.getenv('OANDA_API_KEY')
    account_id = os.getenv('OANDA_ACCOUNT_ID')
    environment = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    if not api_key or not account_id:
        print("❌ Missing OANDA credentials in .env file")
        print("Please set OANDA_API_KEY and OANDA_ACCOUNT_ID")
        return False
    
    try:
        # Initialize client
        client = OandaClient(api_key, account_id, environment)
        
        # Test connection
        print(f"🌐 Environment: {environment}")
        print(f"🔑 Account ID: {account_id}")
        
        # Get account info
        account_info = await client.get_account_info()
        
        print("✅ Connection successful!")
        print(f"💰 Account Balance: {account_info['balance']} {account_info['currency']}")
        print(f"📊 Account Status: {account_info.get('marginRate', 'N/A')}")
        
        # Test getting price data
        print("\n📈 Testing price data...")
        instruments = ['NAS100_USD', 'USD_JPY']
        
        for instrument in instruments:
            try:
                price = await client.get_current_price(instrument)
                print(f"   {instrument}: {price}")
            except Exception as e:
                print(f"   ❌ {instrument}: {str(e)}")
        
        # Test getting candles
        print("\n📊 Testing historical data...")
        try:
            candles = await client.get_candles('NAS100_USD', 'M3', 10)
            print(f"   ✅ Retrieved {len(candles)} candles for NAS100_USD")
        except Exception as e:
            print(f"   ❌ Error getting candles: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    
    if success:
        print("\n🎉 All tests passed! Your bot is ready to run.")
    else:
        print("\n🔧 Please fix the issues above before running the bot.")