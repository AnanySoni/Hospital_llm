"""
Debug script to test appointment booking functionality
"""

import requests
import json

def test_appointment_booking():
    """Test the appointment booking endpoint with debug information"""
    
    url = "http://localhost:8000/book-appointment"
    
    # Test data matching what's in the frontend
    test_data = {
        "doctor_id": 1,
        "patient_name": "avi",
        "appointment_date": "2025-01-09",  # Use future date
        "appointment_time": "1:00 PM",
        "notes": "Test appointment",
        "symptoms": "chest pain"
    }
    
    print("🧪 Testing appointment booking...")
    print(f"📋 Request URL: {url}")
    print(f"📋 Request Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=test_data)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Appointment booked:")
            print(json.dumps(result, indent=2))
        else:
            print("❌ ERROR! Response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Server not running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")

def test_doctors_endpoint():
    """Test if we can get doctors first"""
    
    url = "http://localhost:8000/doctors"
    
    print("🧪 Testing doctors endpoint...")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            doctors = response.json()
            print(f"✅ Found {len(doctors)} doctors")
            if doctors:
                print(f"📋 First doctor: ID={doctors[0]['id']}, Name={doctors[0]['name']}")
            return doctors
        else:
            print(f"❌ Error getting doctors: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

if __name__ == "__main__":
    print("🏥 Hospital Appointment Booking Debug")
    print("=" * 50)
    
    # First test if we can get doctors
    doctors = test_doctors_endpoint()
    print()
    
    # Then test appointment booking
    test_appointment_booking() 