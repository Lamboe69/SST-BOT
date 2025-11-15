"""
News Filter Module
Handles high-impact news filtering to pause trading
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class NewsFilter:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.news_events = []
        self.last_update = None
        
    async def should_pause_trading(self) -> bool:
        """Check if trading should be paused due to news"""
        if not self.enabled:
            return False
            
        await self._update_news_if_needed()
        
        now = datetime.now()
        
        # Check if we're within 30 minutes of any high-impact news
        for event in self.news_events:
            event_time = datetime.fromisoformat(event['time'])
            time_diff = abs((now - event_time).total_seconds() / 60)  # minutes
            
            if time_diff <= 30 and event['impact'] == 'high':
                return True
                
        return False
    
    async def _update_news_if_needed(self):
        """Update news events if data is stale"""
        now = datetime.now()
        
        # Update every hour
        if self.last_update is None or (now - self.last_update).seconds > 3600:
            await self._fetch_news_events()
            self.last_update = now
    
    async def _fetch_news_events(self):
        """Fetch news events from external API"""
        try:
            # Using a mock news API - replace with actual news service
            # ForexFactory, Investing.com, or similar
            
            # Mock high-impact news events for today
            today = datetime.now().date()
            
            self.news_events = [
                {
                    'time': f"{today}T08:30:00",
                    'title': 'US Non-Farm Payrolls',
                    'impact': 'high',
                    'currency': 'USD'
                },
                {
                    'time': f"{today}T14:00:00", 
                    'title': 'FOMC Meeting',
                    'impact': 'high',
                    'currency': 'USD'
                },
                {
                    'time': f"{today}T09:30:00",
                    'title': 'ECB Interest Rate Decision',
                    'impact': 'high',
                    'currency': 'EUR'
                }
            ]
            
            print(f"📰 Updated news events: {len(self.news_events)} events loaded")
            
        except Exception as e:
            print(f"❌ Error fetching news events: {str(e)}")
            self.news_events = []
    
    def get_upcoming_news(self, hours: int = 24) -> List[Dict]:
        """Get upcoming high-impact news events"""
        now = datetime.now()
        upcoming = []
        
        for event in self.news_events:
            event_time = datetime.fromisoformat(event['time'])
            if event_time > now and (event_time - now).total_seconds() / 3600 <= hours:
                upcoming.append(event)
        
        return upcoming
    
    def enable_filter(self):
        """Enable news filtering"""
        self.enabled = True
        print("📰 News filter enabled")
    
    def disable_filter(self):
        """Disable news filtering"""
        self.enabled = False
        print("📰 News filter disabled")