#!/usr/bin/env python3
"""
Backend Server Startup Script
This script starts the FastAPI backend server with proper configuration.
"""

import os
import sys
import subprocess
import uvicorn
from pathlib import Path
import dotenv

dotenv.load_dotenv()

def print_banner():
    """Print startup banner."""
    print("=" * 60)
    print("Real-Time Chat Application - Backend Server")
    print("=" * 60)

def check_environment():
    """Check if environment is properly configured."""
    print("\n🔍 Checking environment...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please run setup.py first or copy env.example to .env")
        return False
    
    # Check required environment variables
    required_vars = [
        'SECRET_KEY',
        'POSTGRES_PASSWORD',
        'MONGODB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import motor
        import redis
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_server():
    """Start the FastAPI server."""
    print("\n🚀 Starting backend server...")
    
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    reload = os.getenv('RELOAD', 'true').lower() == 'true'
    log_level = os.getenv('LOG_LEVEL', 'info').lower()
    
    print(f"📍 Server will run on: http://{host}:{port}")
    print(f"🔄 Auto-reload: {'enabled' if reload else 'disabled'}")
    print(f"📝 Log level: {log_level}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print_banner()
    
    # Check environment
    if not check_environment():
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main() 