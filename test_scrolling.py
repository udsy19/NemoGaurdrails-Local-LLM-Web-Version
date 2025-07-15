#!/usr/bin/env python3
"""
Test script to verify chat scrolling functionality
Sends multiple test messages to check auto-scroll behavior
"""

import requests
import time
import json

BACKEND_URL = "http://localhost:8000"

def test_chat_scrolling():
    """Send multiple messages to test scrolling"""
    
    test_messages = [
        "Hello, this is test message 1",
        "This is test message 2 to check scrolling",
        "Test message 3 - checking if scroll works properly",
        "Message 4 - adding more content to fill the chat",
        "Test message 5 - this should trigger scrolling",
        "Message 6 - keep testing the scroll functionality",
        "Test message 7 - checking auto-scroll behavior",
        "Message 8 - ensuring all messages are visible",
        "Test message 9 - final check for proper scrolling",
        "Message 10 - this should be at the bottom and visible"
    ]
    
    print("🧪 Testing Chat Scrolling Functionality")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not running. Please start it first:")
            print("   ./start_streamlit_app.sh  OR  ./start_react_app.sh")
            return False
        print("✅ Backend is running")
    except:
        print("❌ Cannot connect to backend. Please start it first:")
        print("   ./start_streamlit_app.sh  OR  ./start_react_app.sh")
        return False
    
    print(f"📤 Sending {len(test_messages)} test messages...")
    print("   (Check your Streamlit/React interface for scrolling behavior)")
    print("")
    
    for i, message in enumerate(test_messages, 1):
        payload = {
            "message": message,
            "session_id": "scroll_test",
            "detector_config": {
                "toxicity": {"enabled": True}
            }
        }
        
        try:
            print(f"   {i:2d}. Sending: {message}")
            response = requests.post(f"{BACKEND_URL}/api/chat/message", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('blocked'):
                    print(f"      ⚠️  Message was blocked: {data.get('blocking_reasons', [])}")
                else:
                    print(f"      ✅ Response received")
            else:
                print(f"      ❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Failed: {e}")
        
        # Wait a bit between messages to see scrolling effect
        time.sleep(1.5)
    
    print("")
    print("✅ Test completed!")
    print("")
    print("🔍 Manual Verification:")
    print("   1. Check your Streamlit interface (http://localhost:8501)")
    print("   2. OR check your React interface (http://localhost:3000)")
    print("   3. Verify that message 10 is visible at the bottom")
    print("   4. Try scrolling up, then send a new message")
    print("   5. Confirm it auto-scrolls to show the new message")
    print("")
    print("💡 If scrolling doesn't work:")
    print("   - Try refreshing the page")
    print("   - Check browser console for errors")
    print("   - Verify you're using the latest version")

if __name__ == "__main__":
    test_chat_scrolling()