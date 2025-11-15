# Smart Structure Trading Bot (SST Bot)

Automated trading bot for CHOCH (Change of Character) and BOS (Break of Structure) setups on 3-minute timeframes.

## 📋 Features

- ✅ Automated CHOCH & BOS pattern detection
- ✅ 1:4 Risk-Reward ratio enforcement
- ✅ Multi-instrument monitoring (NAS100, EU50, JP225, USDCAD, USDJPY)
- ✅ Configurable risk management (1-4% per trade)
- ✅ Daily trade limits
- ✅ Real-time trade monitoring
- ✅ Beautiful web dashboard
- ✅ OANDA API integration
- ✅ SQLite database for trade history

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- OANDA account (practice or live)
- OANDA API key

### 2. Installation

```bash
# Clone or download the bot files
cd smart-structure-trading-bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your OANDA credentials:

```
OANDA_API_KEY=your_api_key_here
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice
```

### 4. Run the Bot

```bash
# Start the API server
python main.py
```

The API will be available at `http://localhost:8000`

### 5. Access the Dashboard

Open your browser and navigate to the dashboard (you'll need to serve the React frontend separately or integrate it).

For now, you can interact with the API directly:

**Configure the bot:**
```bash
curl -X POST http://localhost:8000/bot/configure \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_key",
    "account_id": "your_id",
    "environment": "practice",
    "risk_percentage": 2.0,
    "balance_method": "current",
    "daily_trade_limit": 3
  }'
```

**Start the bot:**
```bash
curl -X POST http://localhost:8000/bot/start
```

**Check status:**
```bash
curl http://localhost:8000/bot/status
```

## 📁 Project Structure

```
smart-structure-trading-bot/
├── main.py                 # Main FastAPI application
├── oanda_client.py         # OANDA API integration
├── risk_manager.py         # Risk management logic
├── structure_detector.py   # CHOCH/BOS pattern detection
├── order_executor.py       # Trade execution & monitoring
├── database.py             # SQLite database operations
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── README.md              # This file
└── trading_bot.db         # SQLite database (created automatically)
```

## 🔧 API Endpoints

### Configuration
- `POST /bot/configure` - Configure bot with OANDA credentials
- `POST /bot/start` - Start the trading bot
- `POST /bot/stop` - Stop the trading bot

### Status & Monitoring
- `GET /bot/status` - Get current bot status
- `GET /trades/open` - Get all open trades
- `GET /trades/history` - Get trade history
- `GET /performance/metrics` - Get performance statistics

### Trade Management
- `POST /trades/{trade_id}/modify` - Modify SL/TP of a trade
- `POST /trades/{trade_id}/close` - Manually close a trade

## 📊 How It Works

### 1. Previous Day Levels
Every day at midnight (broker time), the bot marks:
- **Previous Day High (PDH)** - Highest price from yesterday
- **Previous Day Low (PDL)** - Lowest price from yesterday

### 2. Pattern Detection

**CHOCH (Change of Character) - Reversal**
- Price touches PDH/PDL but doesn't break it
- Price forms a rejection pattern
- Price breaks the opposite swing (confirmation)
- Entry on swing break, SL above/below rejection

**BOS (Break of Structure) - Continuation**
- Price breaks through PDH/PDL
- Price forms a pullback
- Price breaks through pullback high/low (confirmation)
- Entry on pullback break, SL on broken level

### 3. Risk Management
- Fixed 1:4 Risk-Reward ratio
- Configurable risk per trade (1-4% of balance)
- Maximum 3 trades per day
- Position sizing based on stop loss distance

### 4. Trade Execution
- Automatic market order placement
- SL and TP set immediately
- Real-time monitoring for TP/SL hits
- Automatic trade closure at end of day

## 🎯 Trading Strategy

**Timeframe:** 3-minute charts  
**Markets:** Forex (USDCAD, USDJPY) & Indices (NAS100, EU50, JP225)  
**Risk-Reward:** 1:4 fixed  
**Win Rate Target:** 30-50% (profitable with 1:4 RR)  
**Max Trades:** 3 per day across all instruments  

## ⚙️ Configuration Options

```python
{
    "risk_percentage": 2.0,          # 1-4% of balance per trade
    "balance_method": "current",     # "current" or "initial"
    "daily_trade_limit": 3,          # Max trades per day
    "news_filter": False,            # Enable/disable news filtering
    "instruments": [                 # Instruments to monitor
        "NAS100_USD",
        "EU50_EUR", 
        "JP225_USD",
        "USD_CAD",
        "USD_JPY"
    ]
}
```

## 📈 Performance Tracking

The bot tracks:
- Win rate %
- Average Risk-Reward achieved
- Total P&L
- Best/Worst trades
- Daily statistics
- Trade history

Access via:
```bash
curl http://localhost:8000/performance/metrics
```

## 🔒 Safety Features

- Daily trade limit enforcement
- Maximum daily loss protection (optional)
- Stop loss on every trade
- Risk validation before trades
- Account balance checks
- Error handling & logging

## 🖥️ Deployment (VPS/Cloud)

### Deploy on Digital Ocean/AWS/Vultr

1. **Create VPS** (minimum 1GB RAM)

2. **SSH into server:**
```bash
ssh root@your_server_ip
```

3. **Install Python:**
```bash
apt update
apt install python3 python3-pip python3-venv
```

4. **Upload bot files:**
```bash
scp -r . root@your_server_ip:/root/trading-bot
```

5. **Setup & Run:**
```bash
cd /root/trading-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

6. **Run as background service (optional):**

Create `/etc/systemd/system/trading-bot.service`:
```ini
[Unit]
Description=Smart Structure Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/trading-bot
Environment="PATH=/root/trading-bot/venv/bin"
ExecStart=/root/trading-bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable & start:
```bash
systemctl enable trading-bot
systemctl start trading-bot
systemctl status trading-bot
```

## 🧪 Testing

### 1. Test on Demo Account
Always test on OANDA practice account first:
```bash
OANDA_ENVIRONMENT=practice
```

### 2. Monitor Logs
```bash
# View real-time logs
tail -f trading_bot.log

# Or if using systemd:
journalctl -u trading-bot -f
```

### 3. Backtesting
Backtest on historical data before live trading (implement backtesting module separately).

## ⚠️ Important Notes

1. **Start Small:** Begin with minimum risk (1%) and small capital
2. **Monitor Daily:** Check bot performance daily for first week
3. **Demo First:** Test on practice account for at least 2-4 weeks
4. **VPS Recommended:** For 24/5 operation without interruption
5. **Risk Management:** Never risk more than you can afford to lose
6. **Market Conditions:** Bot performs differently in trending vs ranging markets

## 🐛 Troubleshooting

**Bot won't start:**
- Check OANDA credentials in `.env`
- Verify internet connection
- Check API rate limits

**No trades executed:**
- Verify instruments are correct (e.g., `NAS100_USD` not `NAS100`)
- Check daily trade limit hasn't been reached
- Ensure bot is running during market hours

**Database errors:**
- Delete `trading_bot.db` and restart (will lose history)
- Check file permissions

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review OANDA API documentation: https://developer.oanda.com
3. Check bot logs for error messages

## 📜 License

This bot is for educational purposes. Use at your own risk. Trading involves substantial risk of loss.

## 🎓 Disclaimer

**IMPORTANT:** 
- Past performance does not guarantee future results
- Automated trading involves significant risks
- Only trade with money you can afford to lose
- Test thoroughly on demo before using real money
- Monitor bot performance regularly
- Understand the strategy before deploying

---

**Happy Trading! 📈💰**