#!/usr/bin/env python3
"""
Local Development Setup Script
This script sets up the entire local development environment for the Real-Time Chat App.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("Real-Time Chat Application - Local Development Setup")
    print("=" * 60)

def check_prerequisites():
    """Check if all prerequisites are installed."""
    print("\n🔍 Checking prerequisites...")
    
    # Check Python
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Python: {result.stdout.strip()}")
        else:
            print("❌ Python not available")
            return False
    except Exception:
        print("❌ Python not available")
        return False
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
        else:
            print("❌ Docker not available")
            return False
    except Exception:
        print("❌ Docker not available")
        return False
    
    # Check Docker Compose
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        else:
            # Try with 'docker compose' (newer versions)
            result = subprocess.run(['docker', 'compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Docker Compose: {result.stdout.strip()}")
            else:
                print("❌ Docker Compose not available")
                return False
    except Exception:
        print("❌ Docker Compose not available")
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Python dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install Python dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing Python dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template."""
    print("\n📝 Creating .env file...")
    
    env_example = Path("env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ .env file created from template")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ env.example file not found")
        return False

def start_databases():
    """Start the databases."""
    print("\n🚀 Starting databases...")
    
    try:
        # Import and run the database startup script
        from start_databases import main as start_db_main
        start_db_main()
        return True
    except Exception as e:
        print(f"❌ Failed to start databases: {e}")
        return False

def initialize_databases():
    """Initialize database schemas."""
    print("\n🗄️  Initializing database schemas...")
    
    try:
        result = subprocess.run([sys.executable, 'init_db.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database schemas initialized successfully")
            return True
        else:
            print(f"❌ Failed to initialize database schemas: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error initializing database schemas: {e}")
        return False

def test_server():
    """Test if the server can start."""
    print("\n🧪 Testing server startup...")
    
    try:
        # Start server in background for a few seconds
        process = subprocess.Popen([sys.executable, 'start_server.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Server started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start: {stderr.decode()}")
            return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def show_next_steps():
    """Show next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Start the backend server:")
    print("   python start_server.py")
    print("\n2. In a new terminal, start the frontend:")
    print("   cd ..")
    print("   npm install")
    print("   npm run dev")
    print("\n3. Open your browser and go to:")
    print("   http://localhost:5173")
    print("\n📚 Useful commands:")
    print("   - Stop databases: docker-compose down")
    print("   - View logs: docker-compose logs")
    print("   - Restart databases: python start_databases.py")
    print("   - Reinitialize databases: python init_db.py")
    print("\n🚀 Happy coding!")

def main():
    """Main setup function."""
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install:")
        print("- Python 3.8+")
        print("- Docker")
        print("- Docker Compose")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("\n❌ Failed to create .env file")
        sys.exit(1)
    
    # Start databases
    if not start_databases():
        print("\n❌ Failed to start databases")
        sys.exit(1)
    
    # Initialize databases
    if not initialize_databases():
        print("\n❌ Failed to initialize databases")
        sys.exit(1)
    
    # Test server
    if not test_server():
        print("\n❌ Server test failed")
        sys.exit(1)
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main() 