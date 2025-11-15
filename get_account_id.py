"""
Get OANDA Account ID
Run this script to retrieve your account ID from OANDA
"""

import asyncio
import aiohttp
from dotenv import load_dotenv
import os

async def get_account_id():
    load_dotenv()
    
    api_key = os.getenv('OANDA_API_KEY')
    environment = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    if environment == "practice":
        base_url = "https://api-fxpractice.oanda.com/v3"
    else:
        base_url = "https://api-fxtrade.oanda.com/v3"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/accounts", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    accounts = data.get('accounts', [])
                    
                    print("🔍 Found OANDA Accounts:")
                    for account in accounts:
                        account_id = account['id']
                        print(f"📋 Account ID: {account_id}")
                        
                        # Get account details
                        async with session.get(f"{base_url}/accounts/{account_id}", headers=headers) as acc_response:
                            if acc_response.status == 200:
                                acc_data = await acc_response.json()
                                acc_info = acc_data['account']
                                print(f"   💰 Balance: {acc_info['balance']} {acc_info['currency']}")
                                print(f"   📊 Type: {environment.upper()}")
                                print()
                    
                    if accounts:
                        account_id = accounts[0]['id']
                        print(f"✅ Use this Account ID in your .env file:")
                        print(f"OANDA_ACCOUNT_ID={account_id}")
                        
                        # Update .env file automatically
                        with open('.env', 'r') as f:
                            content = f.read()
                        
                        updated_content = content.replace('OANDA_ACCOUNT_ID=your_account_id_here', f'OANDA_ACCOUNT_ID={account_id}')
                        
                        with open('.env', 'w') as f:
                            f.write(updated_content)
                        
                        print("✅ .env file updated automatically!")
                    else:
                        print("❌ No accounts found")
                        
                else:
                    print(f"❌ Error: {response.status}")
                    text = await response.text()
                    print(text)
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(get_account_id())