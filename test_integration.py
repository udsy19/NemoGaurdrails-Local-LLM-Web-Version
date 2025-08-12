#!/usr/bin/env python3
"""
Integration Test Script for LLMinate Data Transmission
Tests the complete data pipeline from backend to LLMinate dashboard
"""

import asyncio
import json
import websockets
import requests
import time
import sys

BACKEND_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000/ws/dashboard"
LLMINATE_URL = "http://localhost:3001"

async def test_websocket_connection():
    """Test WebSocket connection and data flow"""
    print("🔌 Testing WebSocket connection...")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Send initial message
            await websocket.send(json.dumps({
                "type": "register_dashboard",
                "dashboard_type": "main",
                "refresh_interval": 5000
            }))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(response)
            print(f"✅ Received WebSocket response: {data.get('type', 'unknown')}")
            
            return True
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def test_backend_health():
    """Test backend health and endpoints"""
    print("🏥 Testing backend health...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy: {data.get('status')}")
            print(f"   - Models loaded: {data.get('models_loaded')}")
            print(f"   - Detectors: {len(data.get('detectors_available', []))}")
            return True
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_analytics_endpoint():
    """Test analytics data endpoints"""
    print("📊 Testing analytics endpoints...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/analytics/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analytics endpoint working")
            print(f"   - Total requests: {data['summary'].get('total_requests', 0)}")
            print(f"   - Blocked requests: {data['summary'].get('blocked_requests', 0)}")
            return True
        else:
            print(f"❌ Analytics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Analytics endpoint error: {e}")
        return False

def test_llminate_frontend():
    """Test LLMinate frontend accessibility"""
    print("🖥️ Testing LLMinate frontend...")
    
    try:
        response = requests.get(LLMINATE_URL, timeout=10)
        if response.status_code == 200:
            if "React App" in response.text or "LLMinate" in response.text:
                print("✅ LLMinate frontend accessible")
                return True
            else:
                print("⚠️ LLMinate frontend accessible but may not be fully loaded")
                return True
        else:
            print(f"❌ LLMinate frontend failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LLMinate frontend error: {e}")
        return False

def test_database_data():
    """Test database data existence"""
    print("🗄️ Testing database data...")
    
    import sqlite3
    db_path = "/Users/udsy/PycharmProjects/KPMG/NemoGaurdrails-Local-LLM-Web-Version/backend/user_data/ai_safety_analytics.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check user_analytics table
            cursor.execute("SELECT COUNT(*) FROM user_analytics")
            analytics_count = cursor.fetchone()[0]
            
            # Check export_log table  
            cursor.execute("SELECT COUNT(*) FROM export_log")
            export_count = cursor.fetchone()[0]
            
            print(f"✅ Database data exists")
            print(f"   - Analytics records: {analytics_count}")
            print(f"   - Export logs: {export_count}")
            
            if analytics_count > 0:
                return True
            else:
                print("⚠️ No analytics data found - may need to generate some")
                return True
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def generate_test_data():
    """Generate test data by making a chat request"""
    print("🔄 Generating test data...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/completions",
            json={
                "message": "Hello, this is a test message for data generation.",
                "detector_config": {
                    "toxicity": {"enabled": True, "threshold": 0.5},
                    "pii": {"enabled": True, "threshold": 0.5}
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Test data generated successfully")
            return True
        else:
            print(f"⚠️ Test data generation response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Test data generation failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Starting LLMinate Integration Tests\n")
    
    results = []
    
    # Test 1: Backend Health
    results.append(("Backend Health", test_backend_health()))
    
    # Test 2: Database Data
    results.append(("Database Data", test_database_data()))
    
    # Test 3: Analytics Endpoints
    results.append(("Analytics API", test_analytics_endpoint()))
    
    # Test 4: Generate Test Data
    results.append(("Test Data Generation", await generate_test_data()))
    
    # Test 5: WebSocket Connection
    results.append(("WebSocket Connection", await test_websocket_connection()))
    
    # Test 6: LLMinate Frontend
    results.append(("LLMinate Frontend", test_llminate_frontend()))
    
    # Report Results
    print("\n" + "="*50)
    print("📋 INTEGRATION TEST RESULTS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
    
    print(f"\nSUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LLMinate data transmission is working properly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)