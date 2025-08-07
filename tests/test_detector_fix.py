#!/usr/bin/env python3
"""
Test script to verify detector configuration fix
"""
import requests
import json

BACKEND_URL = "http://localhost:8000"

def test_detector_configuration():
    """Test different detector configurations"""
    
    # Test messages
    test_message = "Hello, how are you?"
    
    print("Testing detector configuration fix...")
    print("=" * 50)
    
    # Test 1: No detectors enabled (empty config)
    print("\n1. Testing with NO detectors enabled:")
    payload1 = {
        "message": test_message,
        "detector_config": {}  # Empty config = no detectors
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/chat/message", json=payload1, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Response received: {result.get('response', 'No response')[:50]}...")
            print(f"   ✅ Blocked: {result.get('blocked', False)}")
            print(f"   ✅ Detectors used: {result.get('detectors_used', [])}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 2: Only toxicity detector enabled
    print("\n2. Testing with ONLY toxicity detector enabled:")
    payload2 = {
        "message": test_message,
        "detector_config": {
            "toxicity": {"enabled": True}
        }
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/chat/message", json=payload2, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Response received: {result.get('response', 'No response')[:50]}...")
            print(f"   ✅ Blocked: {result.get('blocked', False)}")
            print(f"   ✅ Detectors used: {result.get('detectors_used', [])}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: Multiple detectors enabled
    print("\n3. Testing with MULTIPLE detectors enabled:")
    payload3 = {
        "message": test_message,
        "detector_config": {
            "toxicity": {"enabled": True},
            "pii": {"enabled": True}
        }
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/chat/message", json=payload3, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Response received: {result.get('response', 'No response')[:50]}...")
            print(f"   ✅ Blocked: {result.get('blocked', False)}")
            print(f"   ✅ Detectors used: {result.get('detectors_used', [])}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")

def check_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    if not check_backend_status():
        print("❌ Backend is not running on port 8000!")
        print("Please start the backend first with: python backend/app/main.py")
        exit(1)
    
    print("✅ Backend is running!")
    test_detector_configuration()
    print("\n" + "=" * 50)
    print("Test completed! If you see ✅ for all tests, the fix is working.")