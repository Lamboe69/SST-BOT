# Quick Start Guide

## 1. Setup
```bash
# Run setup script
python setup_bot.py

# Copy environment file
copy .env.example .env
```

## 2. Configure
Edit `.env` file with your OANDA credentials:
```
OANDA_API_KEY=your_api_key_here
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice
```

## 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## 4. Test Connection
```bash
python test_connection.py
```

## 5. Run Bot
```bash
python main.py
```

## 6. Access Dashboard
Open browser: http://localhost:8000/dashboard

## API Endpoints
- `GET /` - API status
- `GET /dashboard` - Web dashboard
- `POST /bot/configure` - Configure bot
- `POST /bot/start` - Start bot
- `POST /bot/stop` - Stop bot
- `GET /bot/status` - Bot status
- `GET /trades/open` - Open trades
- `GET /trades/history` - Trade history