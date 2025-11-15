@echo off
echo Starting Smart Structure Trading Bot...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements if needed
if not exist "venv\Lib\site-packages\fastapi" (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please run setup_bot.py first or copy .env.example to .env
    echo and configure your OANDA credentials.
    echo.
    pause
    exit /b 1
)

REM Run the bot
echo.
echo Starting bot...
python main.py

pause