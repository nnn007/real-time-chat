#!/usr/bin/env python3
"""
Real-Time Chat Application Setup Script
This script helps set up the backend environment and databases.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("Real-Time Chat Application - Backend Setup")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_dependencies():
    """Check if required system dependencies are installed."""
    print("\n🔍 Checking system dependencies...")
    
    # Check for Docker
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print("✅ Docker is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Docker not found. You'll need to install databases manually.")
    
    # Check for Python packages
    try:
        import fastapi
        print("✅ FastAPI is installed")
    except ImportError:
        print("❌ FastAPI not found. Run: pip install -r requirements.txt")

def setup_environment():
    """Set up environment configuration."""
    print("\n🔧 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from env.example")
            print("⚠️  Please review and update the .env file with your configuration")
        else:
            print("❌ env.example not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def setup_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "uploads",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_database_schemas():
    """Set up database schemas."""
    print("\n🗄️  Setting up database schemas...")
    
    # Check if database files exist
    schema_files = [
        "../database/postgresql_schema.sql",
        "../database/mongodb_schema.js",
        "../database/redis_config.conf"
    ]
    
    for schema_file in schema_files:
        if Path(schema_file).exists():
            print(f"✅ Found schema file: {schema_file}")
        else:
            print(f"⚠️  Schema file not found: {schema_file}")

def run_docker_setup():
    """Run Docker setup for databases."""
    print("\n🐳 Setting up databases with Docker...")
    
    try:
        # Check if docker-compose.yml exists
        if Path("docker-compose.yml").exists():
            print("✅ Found docker-compose.yml")
            
            # Start databases
            print("🚀 Starting databases...")
            subprocess.run(["docker-compose", "up", "-d", "postgres", "mongodb", "redis"], check=True)
            print("✅ Databases started successfully")
            
            # Wait for databases to be ready
            print("⏳ Waiting for databases to be ready...")
            import time
            time.sleep(10)
            
            return True
        else:
            print("❌ docker-compose.yml not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start databases: {e}")
        return False
    except FileNotFoundError:
        print("❌ Docker Compose not found")
        return False

def install_python_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_backend():
    """Test the backend server."""
    print("\n🧪 Testing backend server...")
    
    try:
        # Test with test server first
        print("🚀 Starting test server...")
        test_process = subprocess.Popen([
            sys.executable, "test_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        import time
        time.sleep(3)  # Wait for server to start
        
        # Test health endpoint
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Test server is running")
                test_process.terminate()
                return True
            else:
                print(f"❌ Test server returned status {response.status_code}")
                test_process.terminate()
                return False
        except requests.RequestException as e:
            print(f"❌ Failed to connect to test server: {e}")
            test_process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Failed to test backend: {e}")
        return False

def main():
    """Main setup function."""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    check_dependencies()
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        return
    
    # Setup directories
    setup_directories()
    
    # Setup database schemas
    setup_database_schemas()
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Dependency installation failed")
        return
    
    # Try Docker setup
    docker_success = run_docker_setup()
    
    # Test backend
    if test_backend():
        print("\n🎉 Backend setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Review and update the .env file with your configuration")
        if not docker_success:
            print("2. Install and configure PostgreSQL, MongoDB, and Redis manually")
        print("3. Run the main server: python -m uvicorn app.main:app --reload")
        print("4. Access the API documentation at: http://localhost:8000/docs")
    else:
        print("\n❌ Backend setup failed")
        print("Please check the error messages above and try again")

if __name__ == "__main__":
    main() 