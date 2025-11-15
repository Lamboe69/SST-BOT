#!/bin/bash

echo "Starting Smart Structure Trading Bot..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo
    echo "WARNING: .env file not found!"
    echo "Please run setup_bot.py first or copy .env.example to .env"
    echo "and configure your OANDA credentials."
    echo
    read -p "Press enter to continue..."
    exit 1
fi

# Run the bot
echo
echo "Starting bot..."
python main.py