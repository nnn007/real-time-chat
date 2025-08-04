#!/usr/bin/env python3
"""
Database Stop Script
This script stops the database containers.
"""

import subprocess
import sys
from pathlib import Path

def print_banner():
    """Print stop banner."""
    print("=" * 60)
    print("Real-Time Chat Application - Database Stop")
    print("=" * 60)

def stop_databases():
    """Stop the databases using Docker Compose."""
    print("\n🛑 Stopping databases...")
    
    # Change to the backend directory
    backend_dir = Path(__file__).parent
    import os
    os.chdir(backend_dir)
    
    try:
        # Stop all services
        cmd = ['docker-compose', 'down']
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Databases stopped successfully")
            return True
        else:
            print(f"❌ Failed to stop databases: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error stopping databases: {e}")
        return False

def show_status():
    """Show the status of containers."""
    print("\n📊 Container Status:")
    try:
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Could not get container status")
    except Exception as e:
        print(f"Error getting container status: {e}")

def main():
    """Main stop function."""
    print_banner()
    
    # Stop databases
    if stop_databases():
        print("\n🎉 Databases stopped successfully!")
        show_status()
    else:
        print("\n❌ Failed to stop databases")
        sys.exit(1)

if __name__ == "__main__":
    main() 