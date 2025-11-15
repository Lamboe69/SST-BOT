"""
OANDA API Client
Handles all communication with OANDA's REST API
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class OandaClient:
    def __init__(self, api_key: str, account_id: str, environment: str = "practice"):
        """
        Initialize OANDA client
        
        Args:
            api_key: OANDA API key
            account_id: OANDA account ID
            environment: 'practice' or 'live'
        """
        self.api_key = api_key
        self.account_id = account_id
        
        # Set base URL based on environment
        if environment == "practice":
            self.base_url = "https://api-fxpractice.oanda.com/v3"
            self.stream_url = "https://stream-fxpractice.oanda.com/v3"
        else:
            self.base_url = "https://api-fxtrade.oanda.com/v3"
            self.stream_url = "https://stream-fxtrade.oanda.com/v3"
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None):
        """Make async HTTP request to OANDA API"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise Exception(f"OANDA API Error {response.status}: {text}")
                
                return await response.json()
    
    async def get_account_info(self) -> Dict:
        """Get account information"""
        result = await self._request("GET", f"/accounts/{self.account_id}")
        return result['account']
    
    async def get_candles(self, instrument: str, granularity: str = "M3", count: int = 500) -> List[Dict]:
        """
        Get historical candles
        
        Args:
            instrument: e.g., "NAS100_USD", "USD_JPY"
            granularity: M1, M3, M5, M15, H1, H4, D
            count: number of candles (max 5000)
        
        Returns:
            List of candle dictionaries
        """
        params = {
            "granularity": granularity,
            "count": count
        }
        
        result = await self._request("GET", f"/instruments/{instrument}/candles", params=params)
        
        # Parse candles
        candles = []
        for candle in result['candles']:
            if candle['complete']:  # Only use completed candles
                candles.append({
                    'time': candle['time'],
                    'volume': candle['volume'],
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c'])
                })
        
        return candles
    
    async def get_current_price(self, instrument: str) -> float:
        """Get current bid/ask price for an instrument"""
        result = await self._request("GET", f"/accounts/{self.account_id}/pricing", 
                                     params={"instruments": instrument})
        
        if result['prices']:
            price = result['prices'][0]
            # Return mid price (average of bid and ask)
            return (float(price['bids'][0]['price']) + float(price['asks'][0]['price'])) / 2
        
        raise Exception(f"No price data for {instrument}")
    
    async def place_market_order(
        self,
        instrument: str,
        units: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """
        Place a market order
        
        Args:
            instrument: e.g., "USD_JPY"
            units: positive for BUY, negative for SELL
            stop_loss: stop loss price
            take_profit: take profit price
        
        Returns:
            Order result dictionary
        """
        order_data = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "timeInForce": "FOK",  # Fill or Kill
                "positionFill": "DEFAULT"
            }
        }
        
        # Add stop loss if provided
        if stop_loss is not None:
            order_data["order"]["stopLossOnFill"] = {
                "price": str(stop_loss)
            }
        
        # Add take profit if provided
        if take_profit is not None:
            order_data["order"]["takeProfitOnFill"] = {
                "price": str(take_profit)
            }
        
        result = await self._request("POST", f"/accounts/{self.account_id}/orders", data=order_data)
        return result
    
    async def modify_trade(self, trade_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict:
        """Modify stop loss or take profit of an open trade"""
        modifications = {}
        
        if stop_loss is not None:
            modifications["stopLoss"] = {"price": str(stop_loss)}
        
        if take_profit is not None:
            modifications["takeProfit"] = {"price": str(take_profit)}
        
        if not modifications:
            raise ValueError("Must provide at least one modification (stop_loss or take_profit)")
        
        result = await self._request("PUT", f"/accounts/{self.account_id}/trades/{trade_id}/orders", 
                                     data=modifications)
        return result
    
    async def close_trade(self, trade_id: str) -> Dict:
        """Close an open trade"""
        result = await self._request("PUT", f"/accounts/{self.account_id}/trades/{trade_id}/close")
        return result
    
    async def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        result = await self._request("GET", f"/accounts/{self.account_id}/openTrades")
        return result.get('trades', [])
    
    async def get_trade_details(self, trade_id: str) -> Dict:
        """Get details of a specific trade"""
        result = await self._request("GET", f"/accounts/{self.account_id}/trades/{trade_id}")
        return result['trade']
    
    def calculate_units(self, risk_amount: float, stop_loss_pips: float, instrument: str) -> int:
        """
        Calculate position size in units based on risk amount and stop loss
        
        Args:
            risk_amount: Amount to risk in account currency
            stop_loss_pips: Stop loss distance in pips
            instrument: Trading instrument
        
        Returns:
            Number of units to trade
        """
        # Pip values for different instrument types
        if "JPY" in instrument:
            pip_value = 0.01  # For JPY pairs, 1 pip = 0.01
        elif "_" in instrument:  # Forex pairs
            pip_value = 0.0001  # Standard pip value
        else:  # Indices
            pip_value = 1.0  # Indices typically use point values
        
        # Calculate units
        # Units = Risk Amount / (Stop Loss Pips × Pip Value)
        units = int(risk_amount / (stop_loss_pips * pip_value))
        
        return units
    
    async def get_pip_value(self, instrument: str) -> float:
        """Get pip value for an instrument"""
        if "JPY" in instrument:
            return 0.01
        elif "_" in instrument:
            return 0.0001
        else:
            return 1.0
    
    async def test_connection(self) -> bool:
        """Test connection to OANDA"""
        try:
            await self.get_account_info()
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False