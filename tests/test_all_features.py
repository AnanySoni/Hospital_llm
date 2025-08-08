#!/usr/bin/env python3
"""
Comprehensive Feature Test Suite
Tests all implemented features including multi-tenant functionality
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health():
    """Test backend health"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print("✅ Health Check: PASS")
        return True
    except Exception as e:
        print(f"❌ Health Check: FAIL - {e}")
        return False

def test_multi_tenant_adaptive_diagnostic():
    """Test multi-tenant adaptive diagnostic"""
    try:
        url = f"{BASE_URL}/v2/h/demo1/start-adaptive-diagnostic"
        params = {
            "symptoms": "chest pain",
            "session_id": "test_session_123"
        }
        response = requests.post(url, params=params, json={})
        assert response.status_code == 200
        data = response.json()
        assert "current_question" in data
        assert "session_id" in data
        print("✅ Multi-Tenant Adaptive Diagnostic: PASS")
        return True
    except Exception as e:
        print(f"❌ Multi-Tenant Adaptive Diagnostic: FAIL - {e}")
        return False

def test_doctor_recommendations():
    """Test doctor recommendations"""
    try:
        url = f"{BASE_URL}/recommend-doctors"
        data = {"symptoms": "chest pain"}
        response = requests.post(url, json=data)
        assert response.status_code == 200
        doctors = response.json()
        assert isinstance(doctors, list)
        print("✅ Doctor Recommendations: PASS")
        return True
    except Exception as e:
        print(f"❌ Doctor Recommendations: FAIL - {e}")
        return False

def test_appointment_booking():
    """Test appointment booking"""
    try:
        url = f"{BASE_URL}/book-appointment"
        data = {
            "patient_name": "Test Patient",
            "doctor_id": 1,
            "appointment_date": "2025-08-15",
            "appointment_time": "10:00",
            "symptoms": "chest pain"
        }
        response = requests.post(url, json=data)
        assert response.status_code == 200
        print("✅ Appointment Booking: PASS")
        return True
    except Exception as e:
        print(f"❌ Appointment Booking: FAIL - {e}")
        return False

def test_phone_recognition():
    """Test phone recognition service"""
    try:
        url = f"{BASE_URL}/phone-recognition"
        data = {"phone_number": "+1234567890"}
        response = requests.post(url, json=data)
        assert response.status_code == 200
        print("✅ Phone Recognition: PASS")
        return True
    except Exception as e:
        print(f"❌ Phone Recognition: FAIL - {e}")
        return False

def test_smart_welcome():
    """Test smart welcome service"""
    try:
        url = f"{BASE_URL}/smart-welcome"
        data = {"phone_number": "+1234567890"}
        response = requests.post(url, json=data)
        assert response.status_code == 200
        print("✅ Smart Welcome: PASS")
        return True
    except Exception as e:
        print(f"❌ Smart Welcome: FAIL - {e}")
        return False

def test_enhanced_chat():
    """Test enhanced chat functionality"""
    try:
        url = f"{BASE_URL}/chat-enhanced"
        data = {
            "message": "I have chest pain",
            "session_id": "test_chat_session",
            "patient_profile": {"age": 35, "gender": "male"}
        }
        response = requests.post(url, json=data)
        assert response.status_code == 200
        print("✅ Enhanced Chat: PASS")
        return True
    except Exception as e:
        print(f"❌ Enhanced Chat: FAIL - {e}")
        return False

def test_urgency_assessment():
    """Test urgency assessment"""
    try:
        url = f"{BASE_URL}/v2/assess-urgency"
        data = {
            "symptoms": "chest pain",
            "patient_age": 35,
            "medical_history": "none"
        }
        response = requests.post(url, json=data)
        assert response.status_code == 200
        print("✅ Urgency Assessment: PASS")
        return True
    except Exception as e:
        print(f"❌ Urgency Assessment: FAIL - {e}")
        return False

def test_admin_endpoints():
    """Test admin endpoints"""
    try:
        # Test hospital lookup by slug
        url = f"{BASE_URL}/admin/hospitals/by-slug/demo1"
        response = requests.get(url)
        assert response.status_code == 200
        hospital_data = response.json()
        assert hospital_data["slug"] == "demo1"
        print("✅ Admin Endpoints: PASS")
        return True
    except Exception as e:
        print(f"❌ Admin Endpoints: FAIL - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 COMPREHENSIVE FEATURE TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_health,
        test_multi_tenant_adaptive_diagnostic,
        test_doctor_recommendations,
        test_appointment_booking,
        test_phone_recognition,
        test_smart_welcome,
        test_enhanced_chat,
        test_urgency_assessment,
        test_admin_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FEATURES WORKING PERFECTLY!")
    else:
        print("⚠️  Some features need attention")
    
    return passed == total

if __name__ == "__main__":
    main() 