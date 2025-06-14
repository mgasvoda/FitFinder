#!/usr/bin/env python3
"""
Start the backend server accessible on the network IP for Android testing.
"""

import os
import sys
import socket
import subprocess

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Could not determine local IP: {e}")
        return "127.0.0.1"

def main():
    # Get the local IP
    local_ip = get_local_ip()
    print(f"Detected local IP: {local_ip}")
    
    # Set environment variables
    os.environ["HOST"] = "0.0.0.0"  # Listen on all interfaces
    os.environ["PORT"] = "8000"
    
    print(f"Starting backend server...")
    print(f"Will be accessible at:")
    print(f"  - Local: http://127.0.0.1:8000")
    print(f"  - Network: http://{local_ip}:8000")
    print(f"  - All interfaces: http://0.0.0.0:8000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Import and run the backend
        from backend.main import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="0.0.0.0",  # Listen on all interfaces
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
