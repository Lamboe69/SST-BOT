"""
Smart Structure Trading Bot - Main Entry Point
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the FastAPI app
import importlib.util
spec = importlib.util.spec_from_file_location("backend_main_api", "backend-main-api.py")
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)
app = backend.app
import uvicorn

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    print("🚀 Starting Smart Structure Trading Bot...")
    print(f"📡 API Server: http://{host}:{port}")
    print(f"📊 Dashboard: http://{host}:{port}/dashboard/full")
    print("⚠️  Make sure to configure your .env file with OANDA credentials")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=False
    )