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
        """Calculate previous day high and low for an instrument"""
        try:
            # Get 2 days of 5-minute data to ensure we have previous day
            candles = await self.oanda_client.get_candles(instrument, "M5", 576)  # 2 days
            
            if len(candles) < 288:  # Need at least 1 day
                print(f"⚠️ Insufficient data for {instrument}")
                return
            
            # Get yesterday's candles (288 candles = 24 hours of 5-min data)
            yesterday_candles = candles[-576:-288] if len(candles) >= 576 else candles[:-288]
            
            if not yesterday_candles:
                print(f"⚠️ No yesterday data for {instrument}")
                return
            
            # Calculate PDH and PDL using CLOSE PRICES ONLY (line chart)
            yesterday_closes = [c['close'] for c in yesterday_candles]
            pdh = max(yesterday_closes)
            pdl = min(yesterday_closes)
            
            # Check if levels are broken using CLOSE PRICES ONLY
            today_candles = candles[-288:]  # Today's data
            today_closes = [c['close'] for c in today_candles]
            current_high = max(today_closes)
            current_low = min(today_closes)
            
            pdh_broken = current_high > pdh
            pdl_broken = current_low < pdl
            
            # Save to database
            level_data = {
                'instrument': instrument,
                'date': datetime.now().date(),
                'high_price': pdh,
                'low_price': pdl,
                'is_high_broken': pdh_broken,
                'is_low_broken': pdl_broken
            }
            
            self.db.save_previous_day_levels(level_data)
            
            status_high = "BROKEN" if pdh_broken else "INTACT"
            status_low = "BROKEN" if pdl_broken else "INTACT"
            
            print(f"📈 {instrument}: PDH={pdh:.4f} ({status_high}), PDL={pdl:.4f} ({status_low})")
            
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