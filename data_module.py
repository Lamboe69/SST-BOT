"""
Data Module
Handles real-time data fetching and previous day level calculations
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional
import pytz

class DataModule:
    def __init__(self, oanda_client, db):
        self.oanda_client = oanda_client
        self.db = db
        self.instruments = ["NAS100_USD", "EU50_EUR", "JP225_USD", "USD_CAD", "USD_JPY"]
        self.broker_timezone = pytz.timezone('America/New_York')  # OANDA uses NY time
        self.last_daily_reset = None
        
    async def initialize_daily_levels(self):
        """Initialize previous day levels for all instruments"""
        print("📊 Initializing previous day levels...")
        
        for instrument in self.instruments:
            await self._calculate_previous_day_levels(instrument)
        
        self.last_daily_reset = datetime.now().date()
        print("✅ Previous day levels initialized")
    
    async def check_daily_reset(self):
        """Check if we need to reset daily levels (midnight broker time)"""
        now = datetime.now(self.broker_timezone)
        current_date = now.date()
        
        # Reset at midnight broker time
        if self.last_daily_reset != current_date and now.time() >= time(0, 0):
            print(f"🔄 Daily reset triggered for {current_date}")
            await self.initialize_daily_levels()
            
            # Reset daily stats in database
            self.db.reset_daily_stats()
            
            return True
        
        return False
    
    async def _calculate_previous_day_levels(self, instrument: str):
        """Calculate and store historical daily levels for long-term reference"""
        try:
            # Get 3 months of daily data for historical levels
            daily_candles = await self.oanda_client.get_candles(instrument, "D", 90)  # 3 months
            
            if len(daily_candles) < 2:
                print(f"⚠️ Insufficient daily data for {instrument}")
                return
            
            # Process each day's levels and store unbroken ones
            for i, candle in enumerate(daily_candles[:-1]):  # Exclude today
                day_date = datetime.fromisoformat(candle['time'].replace('Z', '+00:00')).date()
                day_high = candle['close']  # Use closing price as high for line chart
                day_low = candle['close']   # Use closing price as low for line chart
                
                # Check if this level has been broken by any future day
                broken_high = False
                broken_low = False
                
                for future_candle in daily_candles[i+1:]:
                    future_close = future_candle['close']
                    if future_close > day_high:
                        broken_high = True
                    if future_close < day_low:
                        broken_low = True
                
                # Save historical level to database
                level_data = {
                    'instrument': instrument,
                    'date': day_date,
                    'high_price': day_high,
                    'low_price': day_low,
                    'is_high_broken': broken_high,
                    'is_low_broken': broken_low
                }
                
                self.db.save_historical_level(level_data)
            
            # Also calculate yesterday's levels for immediate use
            yesterday = daily_candles[-2]
            today = daily_candles[-1]
            
            pdh = yesterday['close']
            pdl = yesterday['close']
            pdh_broken = today['close'] > pdh
            pdl_broken = today['close'] < pdl
            
            # Save yesterday's level
            level_data = {
                'instrument': instrument,
                'date': datetime.now().date() - timedelta(days=1),
                'high_price': pdh,
                'low_price': pdl,
                'is_high_broken': pdh_broken,
                'is_low_broken': pdl_broken
            }
            
            self.db.save_previous_day_levels(level_data)
            
            print(f"📈 {instrument}: Stored 90 days of historical levels")
            
        except Exception as e:
            print(f"❌ Error calculating levels for {instrument}: {str(e)}")
    
    async def get_real_time_data(self, instrument: str, count: int = 500) -> List[Dict]:
        """Get real-time 5-minute data for LINE CHART ONLY analysis"""
        try:
            candles = await self.oanda_client.get_candles(instrument, "M5", count)
            
            # Return ONLY closing prices for line chart analysis
            processed_data = []
            for candle in candles:
                processed_data.append({
                    'time': candle['time'],
                    'close': candle['close'],  # ONLY closing price for line chart
                    'volume': candle['volume']
                })
            
            return processed_data
            
        except Exception as e:
            print(f"❌ Error fetching real-time data for {instrument}: {str(e)}")
            return []
    
    async def get_previous_day_levels(self, instrument: str) -> Optional[Dict]:
        """Get previous day levels for an instrument"""
        return self.db.get_previous_day_levels(instrument)
    
    async def get_historical_levels(self, instrument: str, days: int = 90) -> List[Dict]:
        """Get all unbroken historical levels for an instrument"""
        return self.db.get_historical_levels(instrument, days)
    
    async def update_level_status(self, instrument: str, high_broken: bool = None, low_broken: bool = None):
        """Update the broken status of previous day levels"""
        self.db.update_level_status(instrument, high_broken, low_broken)
    
    async def is_market_open(self) -> bool:
        """Check if forex/indices markets are open (24/5)"""
        now = datetime.now(self.broker_timezone)
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Markets closed on weekends
        if weekday == 5:  # Saturday
            return False
        elif weekday == 6:  # Sunday
            # Markets open Sunday 5 PM ET
            return now.time() >= time(17, 0)
        else:  # Monday-Friday
            # Check for Friday close (5 PM ET)
            if weekday == 4 and now.time() >= time(17, 0):
                return False
            return True
    
    async def get_market_session(self) -> str:
        """Get current market session"""
        now = datetime.now(self.broker_timezone)
        hour = now.hour
        
        if 2 <= hour < 8:
            return "ASIAN"
        elif 8 <= hour < 13:
            return "LONDON"
        elif 13 <= hour < 17:
            return "OVERLAP"
        elif 17 <= hour < 22:
            return "NEW_YORK"
        else:
            return "QUIET"
    
    async def validate_data_quality(self, candles: List[Dict]) -> bool:
        """Validate data quality for trading decisions"""
        if not candles or len(candles) < 10:
            return False
        
        # Check for gaps in data
        for i in range(1, len(candles)):
            prev_time = datetime.fromisoformat(candles[i-1]['time'].replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(candles[i]['time'].replace('Z', '+00:00'))
            
            # Should be 5 minutes apart
            time_diff = (curr_time - prev_time).total_seconds()
            if time_diff > 600:  # More than 10 minutes gap
                print(f"⚠️ Data gap detected: {time_diff}s between candles")
                return False
        
        return True