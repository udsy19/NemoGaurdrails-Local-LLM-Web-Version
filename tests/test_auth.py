#!/usr/bin/env python3
"""
Test script for authentication system
"""

import os
import sys
import asyncio
import httpx

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_auth_endpoints():
    """Test authentication endpoints"""
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Authentication System")
        print("=" * 50)
        
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/api/auth/health")
            print(f"✅ Auth Health: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Auth Health Failed: {e}")
            return
        
        # Test bypass login
        try:
            login_data = {
                "email": "bypass@dev.com",
                "password": "bypass123",
                "use_bypass": True
            }
            
            response = await client.post(f"{base_url}/api/auth/login", json=login_data)
            print(f"✅ Bypass Login: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                print(f"   Message: {data.get('message')}")
                print(f"   Requires License: {data.get('requires_license')}")
                
                if data.get('session'):
                    print(f"   Session: {data['session'].keys()}")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Bypass Login Failed: {e}")
        
        # Test system info
        try:
            response = await client.get(f"{base_url}/api/auth/system-info")
            print(f"✅ System Info: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   System Info Keys: {data.keys()}")
            
        except Exception as e:
            print(f"❌ System Info Failed: {e}")
        
        print("=" * 50)
        print("🎯 Test Complete")

def test_backend_import():
    """Test that backend modules can be imported"""
    try:
        print("🧪 Testing Backend Module Imports")
        print("=" * 50)
        
        # Test config loading
        from app.services.config_service import ConfigService
        print("✅ ConfigService imported")
        
        # Test auth service
        from app.services.auth_service import AuthenticationManager
        print("✅ AuthenticationManager imported")
        
        # Test system info
        from app.utils.system_info import get_mac_address, get_ip_address
        print("✅ System info utilities imported")
        
        # Test actual system info collection
        mac = get_mac_address()
        ip = get_ip_address()
        
        print(f"   MAC Address: {mac}")
        print(f"   IP Address: {ip}")
        
        print("=" * 50)
        print("✅ All imports successful")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Authentication System Tests")
    print()
    
    # Test backend imports first
    test_backend_import()
    print()
    
    # Test endpoints (requires backend to be running)
    print("Note: Make sure the backend is running on localhost:8001")
    try:
        asyncio.run(test_auth_endpoints())
    except KeyboardInterrupt:
        print("\n⛔ Tests interrupted by user")
    except Exception as e:
        print(f"❌ Endpoint tests failed: {e}")
        print("💡 Make sure the backend server is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")