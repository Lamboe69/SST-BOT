"""
Additional API endpoints for new features
"""

from fastapi import HTTPException

def add_new_endpoints(app, news_filter, signal_generator, trade_manager):
    """Add new API endpoints to the FastAPI app"""
    
    @app.post("/settings/news-filter")
    async def toggle_news_filter(enabled: bool):
        """Toggle news filter on/off"""
        try:
            if news_filter:
                if enabled:
                    news_filter.enable_filter()
                else:
                    news_filter.disable_filter()
                
                return {"success": True, "message": f"News filter {'enabled' if enabled else 'disabled'}"}
            else:
                return {"success": False, "message": "News filter not initialized"}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to toggle news filter: {str(e)}")

    @app.get("/news/upcoming")
    async def get_upcoming_news():
        """Get upcoming high-impact news events"""
        try:
            if news_filter:
                upcoming = news_filter.get_upcoming_news(24)
                return {"success": True, "news": upcoming}
            else:
                return {"success": False, "message": "News filter not initialized"}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get news: {str(e)}")

    @app.post("/settings/bos-distance")
    async def set_bos_distance(threshold_pips: float):
        """Set BOS distance threshold in pips"""
        try:
            if signal_generator:
                signal_generator.set_bos_distance_threshold(threshold_pips)
                return {"success": True, "message": f"BOS distance set to {threshold_pips} pips"}
            else:
                return {"success": False, "message": "Signal generator not initialized"}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to set BOS distance: {str(e)}")

    @app.get("/signals/statistics")
    async def get_signal_statistics():
        """Get signal generation statistics"""
        try:
            if signal_generator:
                stats = await signal_generator.get_signal_statistics()
                return {"success": True, "statistics": stats}
            else:
                return {"success": False, "message": "Signal generator not initialized"}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get signal statistics: {str(e)}")

    @app.get("/trades/performance")
    async def get_trade_performance():
        """Get detailed trade performance summary"""
        try:
            if trade_manager:
                performance = await trade_manager.get_trade_performance_summary()
                return {"success": True, "performance": performance}
            else:
                return {"success": False, "message": "Trade manager not initialized"}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get trade performance: {str(e)}")

    @app.post("/trades/close-all-eod")
    async def close_all_eod():
        """Manually close all trades (End of Day)"""
        try:
            if trade_manager:
                await trade_manager.close_all_eod_trades()
                return {"success": True, "message": "All trades closed"}
            else:
                return {"success": False, "message": "Trade manager not initialized"}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to close trades: {str(e)}")