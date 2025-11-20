"""
Smart Structure Trading Bot - Main API
FastAPI backend with OANDA integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import asyncio

# Import our custom modules
import importlib.util
from line_chart_config import LINE_CHART_CONFIG

def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

oanda_client_mod = load_module("oanda_client", "oanda-client.py")
risk_manager_mod = load_module("risk_manager", "risk-manager.py")
structure_detector_mod = load_module("structure_detector", "structure-detector.py")
order_executor_mod = load_module("order_executor", "order-executor.py")
database_mod = load_module("database_module", "database-module.py")

OandaClient = oanda_client_mod.OandaClient
RiskManager = risk_manager_mod.RiskManager
StructureDetector = structure_detector_mod.StructureDetector
OrderExecutor = order_executor_mod.OrderExecutor
Database = database_mod.Database

# Load additional modules
data_module_mod = load_module("data_module", "data_module.py")
news_filter_mod = load_module("news_filter", "news_filter.py")

signal_generator_mod = load_module("signal_generator", "signal_generator.py")
trade_manager_mod = load_module("trade_manager", "trade_manager.py")

DataModule = data_module_mod.DataModule
NewsFilter = news_filter_mod.NewsFilter

SignalGenerator = signal_generator_mod.SignalGenerator
TradeManager = trade_manager_mod.TradeManager

# Load API endpoints
api_endpoints_mod = load_module("api_endpoints", "api_endpoints.py")

app = FastAPI(title="SST Trading Bot API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global instances
db = Database()
oanda_client = None
risk_manager = None
structure_detector = None
order_executor = None
data_module = None
news_filter = None

signal_generator = None
trade_manager = None
bot_running = False

# Pydantic models for request/response
class BotConfig(BaseModel):
    api_key: str
    account_id: str
    environment: str = "practice"  # practice or live
    risk_percentage: float = 2.0
    balance_method: str = "current"  # initial or current
    news_filter: bool = False
    daily_trade_limit: int = 3
    instruments: List[str] = ["NAS100_USD", "EU50_EUR", "JP225_USD", "USD_CAD", "USD_JPY"]

class BotStatus(BaseModel):
    running: bool
    account_balance: float
    today_pnl: float
    open_trades: int
    trades_remaining: int
    instruments_monitoring: List[str]

class TradeModify(BaseModel):
    trade_id: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

# API Routes

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    db.initialize()
    print("✅ Database initialized")
    
    # Auto-configure bot if environment variables are present
    api_key = os.getenv('OANDA_API_KEY')
    account_id = os.getenv('OANDA_ACCOUNT_ID')
    
    if api_key and account_id:
        try:
            # Load existing settings from database or use defaults
            saved_config = db.get_bot_config()
            
            config = BotConfig(
                api_key=api_key,
                account_id=account_id,
                environment=os.getenv('OANDA_ENVIRONMENT', 'practice'),
                risk_percentage=saved_config.get('risk_percentage', float(os.getenv('RISK_PERCENTAGE', 2.0))),
                balance_method=saved_config.get('balance_method', os.getenv('BALANCE_METHOD', 'current')),
                news_filter=saved_config.get('news_filter', os.getenv('NEWS_FILTER', 'False').lower() == 'true'),
                daily_trade_limit=saved_config.get('daily_trade_limit', int(os.getenv('DAILY_TRADE_LIMIT', 3))),
                instruments=saved_config.get('instruments', os.getenv('INSTRUMENTS', 'NAS100_USD,EU50_EUR,JP225_USD,USD_CAD,USD_JPY').split(','))
            )
            await configure_bot_internal(config)
            print("🚀 Bot auto-configured with saved settings")
        except Exception as e:
            print(f"⚠️ Auto-configuration failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Smart Structure Trading Bot API", "status": "running"}

@app.get("/dashboard")
async def dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/dashboard/full")
async def full_dashboard():
    return FileResponse("complete_dashboard.html")

async def configure_bot_internal(config: BotConfig):
    """Internal bot configuration function"""
    global oanda_client, risk_manager, structure_detector, order_executor
    global data_module, news_filter, signal_generator, trade_manager
    
    # Initialize OANDA client
    oanda_client = OandaClient(
        api_key=config.api_key,
        account_id=config.account_id,
        environment=config.environment
    )
    
    # Test connection
    account_info = await oanda_client.get_account_info()
    
    # Initialize other modules
    risk_manager = RiskManager(
        risk_percentage=config.risk_percentage,
        balance_method=config.balance_method,
        initial_balance=float(account_info['balance'])
    )
    
    structure_detector = StructureDetector(
        oanda_client=oanda_client,
        instruments=config.instruments
    )
    
    # Initialize data module
    data_module = DataModule(oanda_client, db)
    
    # Initialize news filter
    news_filter = NewsFilter(enabled=config.news_filter)
    
    # Initialize signal generator
    signal_generator = SignalGenerator(
        structure_detector=structure_detector,
        data_module=data_module,
        news_filter=news_filter,
        db=db
    )
    
    order_executor = OrderExecutor(
        oanda_client=oanda_client,
        risk_manager=risk_manager,
        db=db
    )
    
    # Initialize trade manager
    trade_manager = TradeManager(
        oanda_client=oanda_client,
        db=db
    )
    
    # Initialize previous day levels
    await data_module.initialize_daily_levels()
    
    # Save config to database
    db.save_bot_config(config.dict())
    
    # Register additional API endpoints
    api_endpoints_mod.add_new_endpoints(app, news_filter, signal_generator, trade_manager)
    
    return {
        "success": True,
        "message": "Bot configured successfully",
        "account_balance": account_info['balance'],
        "account_currency": account_info['currency']
    }

@app.post("/bot/configure")
async def configure_bot(config: BotConfig):
    """Configure bot with OANDA credentials and settings"""
    try:
        return await configure_bot_internal(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration failed: {str(e)}")

@app.post("/bot/start")
async def start_bot(background_tasks: BackgroundTasks):
    """Start the trading bot"""
    global bot_running
    
    if oanda_client is None:
        raise HTTPException(status_code=400, detail="Bot not configured. Please configure first.")
    
    if bot_running:
        return {"success": False, "message": "Bot is already running"}
    
    bot_running = True
    background_tasks.add_task(run_trading_bot)
    
    # Start trade monitoring
    if trade_manager:
        background_tasks.add_task(trade_manager.start_monitoring)
    

    
    return {"success": True, "message": "Bot started successfully"}

@app.post("/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    global bot_running
    
    if not bot_running:
        return {"success": False, "message": "Bot is not running"}
    
    bot_running = False
    
    # Stop trade monitoring
    if trade_manager:
        trade_manager.stop_monitoring()
    

    
    return {"success": True, "message": "Bot stopped successfully"}

@app.get("/bot/status", response_model=BotStatus)
async def get_bot_status():
    """Get current bot status"""
    if oanda_client is None:
        raise HTTPException(status_code=400, detail="Bot not configured")
    
    try:
        account_info = await oanda_client.get_account_info()
        open_trades = db.get_open_trades()
        total_active_trades = db.get_total_active_trades_count()
        config = db.get_bot_config()
        
        return BotStatus(
            running=bot_running,
            account_balance=float(account_info['balance']),
            today_pnl=db.get_today_pnl(),
            open_trades=len(open_trades),
            trades_remaining=max(0, config.get('daily_trade_limit', 3) - total_active_trades),
            instruments_monitoring=config.get('instruments', [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/trades/open")
async def get_open_trades():
    """Get all open trades"""
    try:
        trades = db.get_open_trades()
        
        # Enrich with current prices
        for trade in trades:
            current_price = await oanda_client.get_current_price(trade['instrument'])
            trade['current_price'] = current_price
            
            # Calculate unrealized P&L
            if trade['direction'] == 'BUY':
                trade['unrealized_pnl'] = (current_price - trade['entry_price']) * trade['units']
            else:
                trade['unrealized_pnl'] = (trade['entry_price'] - current_price) * trade['units']
        
        return {"success": True, "trades": trades}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get open trades: {str(e)}")

@app.get("/trades/history")
async def get_trade_history(limit: int = 50):
    """Get trade history"""
    try:
        trades = db.get_closed_trades(limit=limit)
        return {"success": True, "trades": trades}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trade history: {str(e)}")

@app.post("/trades/{trade_id}/modify")
async def modify_trade(trade_id: int, modify: TradeModify):
    """Modify stop loss or take profit of an open trade"""
    try:
        result = await order_executor.modify_trade(
            trade_id=trade_id,
            stop_loss=modify.stop_loss,
            take_profit=modify.take_profit
        )
        
        return {"success": True, "message": "Trade modified successfully", "result": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify trade: {str(e)}")

@app.post("/trades/{trade_id}/close")
async def close_trade(trade_id: int):
    """Manually close a trade"""
    try:
        result = await order_executor.close_trade(trade_id, reason="MANUAL")
        return {"success": True, "message": "Trade closed successfully", "result": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close trade: {str(e)}")

@app.get("/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics"""
    try:
        metrics = db.get_performance_metrics()
        return {"success": True, "metrics": metrics}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/settings")
async def get_settings():
    """Get current bot settings"""
    try:
        settings = db.get_bot_config()
        return {"success": True, "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")

@app.post("/settings/update")
async def update_settings(settings: dict):
    """Update bot settings and sync across devices"""
    try:
        # Update each setting in database
        for key, value in settings.items():
            db.update_setting(key, value)
        
        # Update global instances if they exist
        if risk_manager and 'risk_percentage' in settings:
            risk_manager.risk_percentage = settings['risk_percentage']
        if risk_manager and 'balance_method' in settings:
            risk_manager.balance_method = settings['balance_method']
        if news_filter and 'news_filter' in settings:
            news_filter.enabled = settings['news_filter']
        if structure_detector and 'atr_multiplier' in settings:
            structure_detector.atr_multiplier = settings['atr_multiplier']
            
        return {"success": True, "message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@app.post("/settings/news-filter")
async def update_news_filter(data: dict):
    """Update news filter setting"""
    try:
        enabled = data.get('enabled', False)
        db.update_setting('news_filter', enabled)
        
        if news_filter:
            news_filter.enabled = enabled
            
        return {"success": True, "message": f"News filter {'enabled' if enabled else 'disabled'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update news filter: {str(e)}")

@app.post("/settings/atr-multiplier")
async def update_atr_multiplier(data: dict):
    """Update ATR multiplier setting"""
    try:
        multiplier = data.get('atr_multiplier', 2.0)
        db.update_setting('atr_multiplier', multiplier)
        
        if structure_detector:
            structure_detector.atr_multiplier = multiplier
            
        return {"success": True, "message": f"ATR multiplier updated to {multiplier}x"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update ATR multiplier: {str(e)}")

# Background task - Main trading loop
async def run_trading_bot():
    """Main trading bot loop - runs in background"""
    global bot_running
    
    print("🤖 Trading bot started")
    print(f"📊 Line Chart Mode: {LINE_CHART_CONFIG.is_line_chart_mode()}")
    print(f"⚡ Auto Execute Trades: {LINE_CHART_CONFIG.should_auto_execute()}")
    
    while bot_running:
        try:
            # Check if we've reached maximum concurrent trades
            total_active_trades = db.get_total_active_trades_count()
            config = db.get_bot_config()
            
            if total_active_trades >= config['daily_trade_limit']:
                print(f"⏸️ Maximum concurrent trades reached ({total_active_trades}/{config['daily_trade_limit']})")
                await asyncio.sleep(60)  # Check every minute
                continue
            
            # Check for daily reset
            if data_module:
                await data_module.check_daily_reset()
            
            # Check each instrument for setups
            for instrument in config['instruments']:
                if not bot_running:
                    break
                
                print(f"\n🔍 Analyzing {instrument}...")
                
                # Generate signals - FORCE EXECUTION MODE
                signals = []
                try:
                    if signal_generator:
                        signals = await signal_generator.generate_signals(instrument)
                    else:
                        # Fallback to direct structure detector
                        candles = await data_module.get_real_time_data(instrument, 500)
                        if candles:
                            signals = structure_detector.analyze(instrument, candles)
                    
                    print(f"📊 Found {len(signals)} signals for {instrument}")
                    
                except Exception as e:
                    print(f"❌ Error analyzing {instrument}: {str(e)}")
                    continue
                
                # Execute trades based on signals - FORCE EXECUTION
                for signal in signals:
                    if not bot_running:
                        break
                    
                    # Check concurrent trade limit again
                    total_active_trades = db.get_total_active_trades_count()
                    if total_active_trades >= config['daily_trade_limit']:
                        print(f"⏸️ Trade limit reached ({total_active_trades}/{config['daily_trade_limit']})")
                        break
                    
                    # FORCE TRADE EXECUTION
                    print(f"🎯 EXECUTING TRADE: {signal['setup_type']} {signal['direction']} on {signal['instrument']}")
                    result = await order_executor.execute_signal(signal)
                    
                    if result['success']:
                        print(f"✅ TRADE EXECUTED: {result['message']}")
                    else:
                        print(f"❌ TRADE FAILED: {result['reason']}")
                    
                    # Small delay between trades
                    await asyncio.sleep(5)
            
            # Trade monitoring is handled by trade_manager
            
            # Sleep for 5 minutes - wait for candle close before next analysis
            await asyncio.sleep(300)
        
        except Exception as e:
            print(f"❌ Error in trading loop: {str(e)}")
            await asyncio.sleep(60)
    
    print("🛑 Trading bot stopped")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)