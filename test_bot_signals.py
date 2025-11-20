#!/usr/bin/env python3
"""
Test Bot Signal Generation
Quick test to verify the bot can generate and execute signals
"""

import asyncio
import os
from dotenv import load_dotenv
import importlib.util

# Load environment
load_dotenv()

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

async def test_bot():
    print("Testing Bot Signal Generation...")
    
    # Load modules
    oanda_client_mod = load_module("oanda_client", "oanda-client.py")
    database_mod = load_module("database_module", "database-module.py")
    data_module_mod = load_module("data_module", "data_module.py")
    structure_detector_mod = load_module("structure_detector", "structure-detector.py")
    signal_generator_mod = load_module("signal_generator", "signal_generator.py")
    news_filter_mod = load_module("news_filter", "news_filter.py")
    
    # Initialize components
    db = database_mod.Database()
    db.initialize()
    
    oanda_client = oanda_client_mod.OandaClient(
        api_key=os.getenv('OANDA_API_KEY'),
        account_id=os.getenv('OANDA_ACCOUNT_ID'),
        environment=os.getenv('OANDA_ENVIRONMENT', 'practice')
    )
    
    # Test connection
    try:
        account_info = await oanda_client.get_account_info()
        print(f"Connected to OANDA - Balance: ${account_info['balance']}")
    except Exception as e:
        print(f"OANDA connection failed: {str(e)}")
        return
    
    # Initialize modules
    data_module = data_module_mod.DataModule(oanda_client, db)
    structure_detector = structure_detector_mod.StructureDetector(oanda_client, ["NAS100_USD"])
    news_filter = news_filter_mod.NewsFilter(enabled=False)
    signal_generator = signal_generator_mod.SignalGenerator(structure_detector, data_module, news_filter, db)
    
    # Test signal generation for each instrument
    instruments = ["NAS100_USD", "EU50_EUR", "JP225_USD", "USD_CAD", "USD_JPY"]
    
    for instrument in instruments:
        print(f"\nTesting {instrument}...")
        
        try:
            # Initialize levels
            await data_module._calculate_previous_day_levels(instrument)
            
            # Generate signals
            signals = await signal_generator.generate_signals(instrument)
            
            print(f"{instrument}: Generated {len(signals)} signals")
            
            for signal in signals:
                print(f"   {signal['setup_type']} {signal['direction']} - Entry: {signal['entry_price']:.4f}")
                
        except Exception as e:
            print(f"Error testing {instrument}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\nBot signal test completed!")

if __name__ == "__main__":
    asyncio.run(test_bot())