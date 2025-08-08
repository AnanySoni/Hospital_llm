#!/usr/bin/env python3
"""
Simple System Test
Basic verification of core functionality
"""

import requests
import json

def test_basic_functionality():
    """Test basic system functionality"""
    print("🚀 Basic System Test")
    print("=" * 40)
    
    # Test 1: Backend Health
    print("1. Testing Backend Health...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("   ✅ Backend is healthy")
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend not accessible: {e}")
        return False
    
    # Test 2: Frontend Access
    print("2. Testing Frontend Access...")
    try:
        response = requests.get("http://localhost:3000")
        if response.status_code == 200:
            print("   ✅ Frontend is accessible")
        else:
            print(f"   ❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Frontend not accessible: {e}")
        return False
    
    # Test 3: Admin Login
    print("3. Testing Admin Login...")
    try:
        response = requests.post(
            "http://localhost:8000/admin/login",
            json={"username": "superadmin", "password": "Admin@123"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("access_token"):
                print("   ✅ Admin login successful")
                print(f"   📝 Token received: {data['access_token'][:20]}...")
            else:
                print("   ❌ No access token received")
                return False
        else:
            print(f"   ❌ Admin login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Admin login error: {e}")
        return False
    
    # Test 4: Patient Chat
    print("4. Testing Patient Chat...")
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"message": "Hello", "session_id": "test_123"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("message"):
                print("   ✅ Patient chat working")
                print(f"   💬 Response: {data['message'][:50]}...")
            else:
                print("   ❌ No chat response received")
                return False
        else:
            print(f"   ❌ Patient chat failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Patient chat error: {e}")
        return False
    
    # Test 5: API Documentation
    print("5. Testing API Documentation...")
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("   ✅ API documentation accessible")
        else:
            print(f"   ❌ API docs not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API docs error: {e}")
        return False
    
    print("\n🎉 All basic tests passed!")
    print("\n🌐 System URLs:")
    print("   • Patient Chat: http://localhost:3000/")
    print("   • Admin Panel: http://localhost:3000/admin")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Backend Health: http://localhost:8000/health")
    print("\n🔑 Admin Credentials:")
    print("   • Username: superadmin")
    print("   • Password: Admin@123")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    exit(0 if success else 1) 