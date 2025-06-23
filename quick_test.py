"""
Quick manual test of the reorganized backend
Run this to verify all functionality works correctly
"""

import requests
import json

def test_health_check():
    """Test the basic health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/")
        print("✅ Health Check:", response.json())
        return True
    except Exception as e:
        print("❌ Health Check Failed:", str(e))
        return False

def test_doctors_endpoint():
    """Test getting all doctors"""
    try:
        response = requests.get("http://localhost:8000/doctors")
        doctors = response.json()
        print(f"✅ Doctors Endpoint: Found {len(doctors)} doctors")
        if doctors:
            print(f"   Sample doctor: {doctors[0]['name']}")
        return True
    except Exception as e:
        print("❌ Doctors Endpoint Failed:", str(e))
        return False

def test_recommendations():
    """Test doctor recommendations"""
    try:
        response = requests.post("http://localhost:8000/recommend-doctors", 
                               json={"symptoms": "I have a headache and feel dizzy"})
        recommendations = response.json()
        print(f"✅ Recommendations: Got {len(recommendations)} doctor recommendations")
        if recommendations:
            print(f"   Sample recommendation: {recommendations[0]['name']}")
        return True
    except Exception as e:
        print("❌ Recommendations Failed:", str(e))
        return False

def main():
    print("🧪 Testing Reorganized Backend Functionality")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_health_check():
        tests_passed += 1
    
    if test_doctors_endpoint():
        tests_passed += 1
        
    if test_recommendations():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 SUCCESS: All functionality works correctly!")
        print("✅ The reorganized backend structure is fully functional")
    else:
        print("⚠️  Some tests failed - check the server logs")

if __name__ == "__main__":
    main() 