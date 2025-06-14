#!/usr/bin/env python3
"""
Check network connectivity and firewall status for the backend server.
"""

import socket
import subprocess
import sys

def check_port_open(host, port):
    """Check if a port is open and accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Could not determine local IP: {e}")
        return "127.0.0.1"

def check_firewall_rules():
    """Check Windows Firewall rules for Python"""
    try:
        # Check if Python is allowed through firewall
        result = subprocess.run([
            "netsh", "advfirewall", "firewall", "show", "rule", 
            "name=all", "dir=in", "protocol=tcp", "localport=8000"
        ], capture_output=True, text=True, shell=True)
        
        if "No rules match the specified criteria" in result.stdout:
            print("❌ No firewall rule found for port 8000")
            return False
        else:
            print("✅ Firewall rules found for port 8000:")
            print(result.stdout)
            return True
    except Exception as e:
        print(f"Could not check firewall rules: {e}")
        return False

def suggest_firewall_fix():
    """Suggest how to fix firewall issues"""
    print("\n🔧 To fix firewall issues, run these commands as Administrator:")
    print("1. Allow Python through Windows Firewall:")
    print('   netsh advfirewall firewall add rule name="Python Backend" dir=in action=allow protocol=TCP localport=8000')
    print("\n2. Or temporarily disable Windows Firewall (not recommended for production):")
    print('   netsh advfirewall set allprofiles state off')
    print("\n3. Or add a rule through Windows Defender Firewall GUI:")
    print("   - Open Windows Defender Firewall")
    print("   - Click 'Allow an app or feature through Windows Defender Firewall'")
    print("   - Add Python.exe and allow it through both Private and Public networks")

def main():
    print("=== Network Connectivity Check ===")
    
    local_ip = get_local_ip()
    print(f"Local IP address: {local_ip}")
    
    # Check if port 8000 is open on localhost
    print(f"\nChecking localhost:8000...")
    localhost_open = check_port_open("127.0.0.1", 8000)
    print(f"localhost:8000: {'✅ Open' if localhost_open else '❌ Closed'}")
    
    # Check if port 8000 is open on network IP
    print(f"\nChecking {local_ip}:8000...")
    network_open = check_port_open(local_ip, 8000)
    print(f"{local_ip}:8000: {'✅ Open' if network_open else '❌ Closed'}")
    
    # Check firewall rules
    print(f"\nChecking Windows Firewall rules...")
    firewall_ok = check_firewall_rules()
    
    # Summary and recommendations
    print(f"\n=== Summary ===")
    if localhost_open and network_open:
        print("✅ Backend is accessible on both localhost and network IP")
        print(f"🎯 Your Android device should be able to connect to: http://{local_ip}:8000")
    elif localhost_open and not network_open:
        print("⚠️  Backend is running on localhost but not accessible from network")
        print("This is likely a firewall issue.")
        suggest_firewall_fix()
    elif not localhost_open:
        print("❌ Backend is not running or not accessible on localhost")
        print("Start the backend first using: python start_backend_network.py")
    
    print(f"\n=== Next Steps ===")
    print("1. Make sure the backend is running with: python start_backend_network.py")
    print("2. If firewall issues persist, run the firewall commands as Administrator")
    print("3. Test connectivity with: python test_backend.py")

if __name__ == "__main__":
    main()
