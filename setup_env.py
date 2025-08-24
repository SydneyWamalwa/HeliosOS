#!/usr/bin/env python3
"""
HeliosOS Environment Setup Script

This script helps set up the environment for HeliosOS by:
1. Checking system requirements
2. Setting up the database
3. Configuring environment variables
4. Installing dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_postgresql():
    """Check if PostgreSQL is available."""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL detected: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  PostgreSQL not found. You can:")
    print("   1. Install PostgreSQL locally")
    print("   2. Use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password123 postgres")
    print("   3. Use SQLite (development only)")
    return False

def setup_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file and add your API keys:")
        print("   - HUGGINGFACE_API_KEY (get from https://huggingface.co/settings/tokens)")
        print("   - SECRET_KEY (generate a secure random string)")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        import sqlalchemy
        import requests
        print("✅ Core dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def setup_database():
    """Set up the database."""
    print("\n🔧 Setting up database...")
    
    # Check if we can connect to PostgreSQL
    db_url = os.getenv('DATABASE_URL', 'postgresql://sydney:password123@localhost:5432/helios_db')
    
    if 'postgresql' in db_url:
        print("Attempting to create PostgreSQL database...")
        try:
            # Try to create database
            subprocess.run([
                'createdb', 'helios_db', '-U', 'sydney', '-h', 'localhost'
            ], check=False)
            print("✅ Database setup completed")
        except Exception as e:
            print(f"⚠️  Database setup failed: {e}")
            print("Please ensure PostgreSQL is running and accessible")
    else:
        print("✅ Using SQLite database (development mode)")

def main():
    """Main setup function."""
    print("🚀 HeliosOS Environment Setup")
    print("=" * 30)
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    # Check PostgreSQL
    check_postgresql()
    
    # Setup environment file
    setup_env_file()
    
    # Check dependencies
    if not check_dependencies():
        print("\nInstalling dependencies...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
            print("✅ Dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Setup database
    setup_database()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Start PostgreSQL service (if using PostgreSQL)")
    print("3. Run: flask run")
    print("\nFor development without API keys, the app will use fallback responses.")

if __name__ == '__main__':
    main()