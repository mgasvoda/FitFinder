#!/usr/bin/env python3
"""
Test script to verify the backend API is working correctly.
This helps debug Android deployment issues by testing the backend directly.
"""

import requests
import json
import sys

# Configuration
BACKEND_URLS = [
    # "http://localhost:8000",
    "http://192.168.1.171:8000"
]
API_KEY = "Rvn_ju-5hEOk9ThHTDM64ffG3eXWpyRuKiiTK9lAnpY"

def test_health_check(backend_url):
    """Test the health check endpoint"""
    print(f"Testing health check at {backend_url}...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        print(f"Health check response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_chat_endpoint(backend_url):
    """Test the chat endpoint"""
    print(f"\nTesting chat endpoint at {backend_url}...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    payload = {
        "prompt": "Hello, this is a test message from the test script."
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/chat", 
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Chat endpoint status: {response.status_code}")
        print(f"Chat endpoint headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Chat response: {data}")
            return True
        else:
            print(f"Chat endpoint error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Chat endpoint failed: {e}")
        return False

def test_cors(backend_url):
    """Test CORS headers"""
    print(f"\nTesting CORS at {backend_url}...")
    
    headers = {
        "Origin": "capacitor://localhost",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,X-API-Key"
    }
    
    try:
        response = requests.options(f"{backend_url}/api/chat", headers=headers, timeout=10)
        print(f"CORS preflight status: {response.status_code}")
        print(f"CORS headers: {dict(response.headers)}")
        return True
    except Exception as e:
        print(f"CORS test failed: {e}")
        return False

def main():
    print("=== Backend API Test ===")
    print(f"Using API key: {API_KEY[:8]}...")
    
    working_backend = None
    
    for backend_url in BACKEND_URLS:
        print(f"\n--- Testing backend at: {backend_url} ---")
        
        # Run tests
        health_ok = test_health_check(backend_url)
        if health_ok:
            working_backend = backend_url
            cors_ok = test_cors(backend_url)
            chat_ok = test_chat_endpoint(backend_url)
            
            print(f"\n=== Test Results for {backend_url} ===")
            print(f"Health check: {'✓' if health_ok else '✗'}")
            print(f"CORS test: {'✓' if cors_ok else '✗'}")
            print(f"Chat endpoint: {'✓' if chat_ok else '✗'}")
            
            if all([health_ok, cors_ok, chat_ok]):
                print(f"\n✅ All tests passed! Backend is working correctly at {backend_url}")
                break
        else:
            print(f"❌ Backend not accessible at {backend_url}")
    
    if working_backend:
        print(f"\n🎯 Recommended backend URL for mobile: {working_backend}")
        sys.exit(0)
    else:
        print("\n❌ No working backend found. Check the backend configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
