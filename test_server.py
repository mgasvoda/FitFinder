import uvicorn
import socket
import os

print("Starting test server...")
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {os.sys.executable}")

# Get local IP address
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    print(f"Local IP address: {local_ip}")
    print(f"Network IP address: 192.168.1.171")
except Exception as e:
    print(f"Could not determine local IP: {e}")

# Start the server
print("Starting Uvicorn server...")
uvicorn.run(
    "backend.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="debug"
)
