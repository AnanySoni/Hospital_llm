#!/usr/bin/env python3
"""
Final System Test Suite
Comprehensive test to verify all functionality is working correctly
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Test credentials
ADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "Admin@123"
}

def test_backend_health():
    """Test backend health endpoint"""
    print("🔍 Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Health: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Backend Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Health Check Error: {e}")
        return False

def test_frontend_accessibility():
    """Test frontend accessibility"""
    print("🔍 Testing Frontend Accessibility...")
    try:
        response = requests.get(FRONTEND_URL)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend accessibility error: {e}")
        return False

def test_admin_login():
    """Test admin login functionality"""
    print("🔍 Testing Admin Login...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/admin/login",
            json=ADMIN_CREDENTIALS,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print("✅ Admin Login Successful")
                return token
            else:
                print("❌ Admin Login Failed: No token received")
                return None
        else:
            print(f"❌ Admin Login Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Admin Login Error: {e}")
        return None

def test_admin_endpoints(token):
    """Test admin panel endpoints"""
    print("🔍 Testing Admin Endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/admin/me", "User Profile"),
        ("/admin/users", "Users Management"),
        ("/admin/hospitals", "Hospitals Management"),
        ("/admin/doctors", "Doctors Management"),
        ("/admin/analytics/hospital", "Hospital Analytics"),
        ("/admin/analytics/system", "System Analytics"),
    ]
    
    results = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            if response.status_code == 200:
                print(f"✅ {name}: Working")
                results.append(True)
            else:
                print(f"❌ {name}: Failed ({response.status_code})")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results.append(False)
    
    return all(results)

def test_patient_chat():
    """Test patient chat functionality"""
    print("🔍 Testing Patient Chat...")
    try:
        # Test basic chat endpoint
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": "I have a headache",
                "session_id": "test_session_123"
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("message"):
                print("✅ Patient Chat: Working")
                return True
            else:
                print("❌ Patient Chat: No response message")
                return False
        else:
            print(f"❌ Patient Chat: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Patient Chat Error: {e}")
        return False

def test_doctor_management(token):
    """Test doctor management functionality"""
    print("🔍 Testing Doctor Management...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test CSV template download
    try:
        response = requests.get(f"{BACKEND_URL}/admin/doctors/csv-template", headers=headers)
        if response.status_code == 200:
            print("✅ Doctor CSV Template: Working")
        else:
            print(f"❌ Doctor CSV Template: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Doctor CSV Template Error: {e}")
        return False
    
    # Test doctor listing
    try:
        response = requests.get(f"{BACKEND_URL}/admin/doctors", headers=headers)
        if response.status_code == 200:
            print("✅ Doctor Listing: Working")
            return True
        else:
            print(f"❌ Doctor Listing: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Doctor Listing Error: {e}")
        return False

def test_email_service(token):
    """Test email service functionality"""
    print("🔍 Testing Email Service...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test email invitation endpoint (this will fail gracefully if no doctors exist)
    try:
        response = requests.post(
            f"{BACKEND_URL}/admin/doctors/send-invitations",
            json={
                "doctor_ids": [],
                "message": "Test invitation",
                "send_welcome_email": True
            },
            headers=headers
        )
        # This should return 200 even with empty doctor_ids
        if response.status_code == 200:
            print("✅ Email Service: Endpoint Working")
            return True
        else:
            print(f"❌ Email Service: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Email Service Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive System Test\n")
    print("=" * 50)
    
    results = {}
    
    # Test backend health
    results["backend_health"] = test_backend_health()
    
    # Test frontend accessibility
    results["frontend_access"] = test_frontend_accessibility()
    
    # Test admin login
    token = test_admin_login()
    results["admin_login"] = token is not None
    
    if token:
        # Test admin endpoints
        results["admin_endpoints"] = test_admin_endpoints(token)
        
        # Test doctor management
        results["doctor_management"] = test_doctor_management(token)
        
        # Test email service
        results["email_service"] = test_email_service(token)
    else:
        results["admin_endpoints"] = False
        results["doctor_management"] = False
        results["email_service"] = False
    
    # Test patient chat
    results["patient_chat"] = test_patient_chat()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_status in results.items():
        status = "✅ PASS" if passed_status else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is fully functional.")
        print("\n🌐 Access URLs:")
        print(f"   • Patient Chat: {FRONTEND_URL}/")
        print(f"   • Admin Panel: {FRONTEND_URL}/admin")
        print(f"   • API Docs: {BACKEND_URL}/docs")
        print(f"   • Admin Login: username=superadmin, password=Admin@123")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 