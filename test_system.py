#!/usr/bin/env python3
"""
Quick system test to verify the AI Safety System is working
"""

import requests
import time
import sys

def test_backend():
    """Test backend health"""
    try:
        print("🔍 Testing backend health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   - ML Backend: {data.get('ml_backend', False)}")
            print(f"   - Models Loaded: {data.get('models_loaded', False)}")
            print(f"   - Detectors: {len(data.get('detectors_available', []))}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_detectors():
    """Test detector API"""
    try:
        print("\n🔍 Testing detectors API...")
        response = requests.get("http://localhost:8000/api/detectors", timeout=5)
        if response.status_code == 200:
            detectors = response.json()
            print(f"✅ Found {len(detectors)} detectors")
            for detector in detectors:
                status = "✅" if detector.get('loaded') else "❌"
                print(f"   {status} {detector['name']}: {detector.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Detectors API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Detectors API failed: {e}")
        return False

def test_chat():
    """Test chat API"""
    try:
        print("\n🔍 Testing chat API...")
        payload = {
            "message": "Hello, this is a test message",
            "detector_config": {
                "toxicity": {"enabled": True}
            }
        }
        response = requests.post("http://localhost:8000/api/chat/message", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat API working")
            print(f"   - Message ID: {data.get('message_id', 'N/A')}")
            print(f"   - Blocked: {data.get('blocked', False)}")
            print(f"   - Response: {data.get('response', 'No response')[:50]}...")
            return True
        else:
            print(f"❌ Chat API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat API failed: {e}")
        return False

def test_system_info():
    """Test system info API"""
    try:
        print("\n🔍 Testing system info API...")
        response = requests.get("http://localhost:8000/api/system/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System info working")
            print(f"   - CPU Cores: {data.get('cpu', {}).get('cores', 'Unknown')}")
            print(f"   - Total Memory: {data.get('memory', {}).get('total', 'Unknown')} MB")
            print(f"   - Platform: {data.get('platform', 'Unknown')}")
            return True
        else:
            print(f"❌ System info API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ System info API failed: {e}")
        return False

def main():
    print("🚀 AI Safety System - Quick Test")
    print("=" * 50)
    
    # Wait a moment for backend to be ready
    print("⏳ Waiting 3 seconds for backend to be ready...")
    time.sleep(3)
    
    tests = [
        ("Backend Health", test_backend),
        ("Detectors API", test_detectors),
        ("Chat API", test_chat),
        ("System Info API", test_system_info)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
        print("\n🌐 Access your interfaces:")
        print("   - Streamlit: http://localhost:8501")
        print("   - React: http://localhost:3000")
        print("   - API Docs: http://localhost:8000/docs")
        return 0
    else:
        print("⚠️  Some tests failed. Check backend logs for details.")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure backend is running: ./start_backend.sh")
        print("   2. Check backend logs in logs/backend.log")
        print("   3. Verify all dependencies are installed")
        return 1

if __name__ == "__main__":
    sys.exit(main())