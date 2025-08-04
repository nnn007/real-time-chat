#!/usr/bin/env python3
"""
Dependency Installation Script
This script installs Python dependencies with better error handling.
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install Python dependencies with error handling."""
    print("📦 Installing Python dependencies...")
    
    # Core dependencies that should work
    core_deps = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "sqlalchemy==2.0.23",
        "asyncpg==0.29.0",
        "psycopg2-binary==2.9.9",
        "pymongo==4.6.0",
        "redis==5.0.1",
        "alembic==1.12.1",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "email-validator==2.1.0",
        "httpx==0.25.2",
        "aiohttp==3.9.1",
        "slowapi==0.1.9",
        "structlog==23.2.0",
        "prometheus-fastapi-instrumentator==6.1.0",
        "openai==1.3.7",
        "python-magic==0.4.27",
        "websockets==12.0",
        "python-cors==1.7.0",
        "python-dotenv==1.0.0"
    ]
    
    # Optional dependencies that might fail
    optional_deps = [
        "Pillow==10.1.0",  # This was causing issues
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1",
        "black==23.11.0",
        "isort==5.12.0",
        "flake8==6.1.0"
    ]
    
    print("Installing core dependencies...")
    for dep in core_deps:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"✅ Installed: {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            print(f"⚠️  You may need to install this manually")
    
    print("\nInstalling optional dependencies...")
    for dep in optional_deps:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"✅ Installed: {dep}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Skipped optional dependency {dep}: {e}")
            print(f"   This is not critical for basic functionality")

if __name__ == "__main__":
    install_dependencies() 