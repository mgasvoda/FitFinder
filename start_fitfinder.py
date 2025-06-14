#!/usr/bin/env python3
"""
FitFinder Startup Script
Runs both FastAPI backend and Chainlit chat interface
"""

import subprocess
import sys
import time
import os
import signal
from threading import Thread

def run_fastapi():
    """Run the FastAPI backend"""
    print("🚀 Starting FastAPI Backend...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "backend.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])

def run_chainlit():
    """Run the Chainlit chat interface"""
    print("💬 Starting Chainlit Chat Interface...")
    # Wait a moment for FastAPI to start
    time.sleep(2)
    subprocess.run([
        sys.executable, "-m", "chainlit", 
        "run", "backend/chainlit_app.py", 
        "--host", "0.0.0.0", 
        "--port", "8001"
    ])

def main():
    print("🌟 Starting FitFinder Services...")
    print("=" * 50)
    
    try:
        # Start FastAPI in a separate thread
        fastapi_thread = Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        
        # Give FastAPI a moment to start
        time.sleep(3)
        
        print("\n📱 Access points:")
        print("   • FastAPI Backend: http://your-ip:8000")
        print("   • API Docs: http://your-ip:8000/api/docs") 
        print("   • Chainlit Chat: http://your-ip:8001")
        print("\n💡 Replace 'your-ip' with your actual local IP address")
        print("=" * 50)
        
        # Run Chainlit in the main thread
        run_chainlit()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down FitFinder services...")
        sys.exit(0)

if __name__ == "__main__":
    main() 