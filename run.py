#!/usr/bin/env python3
"""
SmartMeet AI - Quick Start Script
Run this script to start the SmartMeet application with proper environment setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import streamlit
        import pandas
        import plotly
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  No .env file found. Please copy .env.example to .env and configure your settings.")
            print("   cp .env.example .env")
        else:
            print("⚠️  No environment configuration found.")
        return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment configuration loaded")
    except ImportError:
        print("⚠️  python-dotenv not installed. Install it with: pip install python-dotenv")
    
    return True

def main():
    """Main function to start the application"""
    print("🤖 SmartMeet AI - Starting Application...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("Main.py").exists():
        print("❌ Main.py not found. Please run this script from the SmartMeet directory.")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Start the Streamlit application
    print("\n🚀 Starting SmartMeet AI...")
    print("📱 The application will open in your browser at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the application")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "Main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 SmartMeet AI stopped. Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()