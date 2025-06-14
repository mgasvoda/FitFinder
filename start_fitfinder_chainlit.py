#!/usr/bin/env python3
"""
FitFinder Chainlit Startup Script
Simple script to start the FitFinder chat interface
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables and dependencies are set"""
    required_vars = ["ANTHROPIC_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file with the required variables. See env.example for reference.")
        return False
    
    return True

def main():
    """Main startup function"""
    logger.info("🌟 Starting FitFinder Chat Interface...")
    
    # Check if we're in the right directory
    if not Path("backend/chainlit_app.py").exists():
        logger.error("Could not find backend/chainlit_app.py. Make sure you're running this from the project root.")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Get configuration
    host = os.getenv("CHAINLIT_HOST", "0.0.0.0")
    port = os.getenv("CHAINLIT_PORT", "8001")
    
    logger.info(f"🚀 Starting Chainlit on http://{host}:{port}")
    logger.info("💡 Default login: admin / fitfinder2024!")
    logger.info("🔧 Use 'python -m backend.auth.user_manager' to manage users")
    
    try:
        # Start Chainlit
        cmd = [
            sys.executable, "-m", "chainlit", "run", 
            "backend/chainlit_app.py",
            "--host", host,
            "--port", port
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        logger.info("\n👋 FitFinder stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to start Chainlit: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 