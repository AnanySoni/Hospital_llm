import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

print("HOSPITAL LLM PROJECT - Master Test Suite (Auto-Generated)")
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Target: {BASE_URL}\n\n")

def print_result(section, passed, msg=None):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {section}: {msg if msg else ''}")

# 1. Health Check
try:
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200 and r.json()["status"] == "healthy"
    print_result("Health Check", True)
except Exception as e:
    print_result("Health Check", False, str(e))

# 2. Doctor Recommendations
try:
    payload = {"symptoms": "chest pain"}
    r = requests.post(f"{BASE_URL}/recommend-doctors", json=payload)
    assert r.status_code == 200 and isinstance(r.json(), list)
    print_result("Doctor Recommendations", True)
except Exception as e:
    print_result("Doctor Recommendations", False, str(e))

# 3. Book Appointment (with phone validation)
try:
    today = datetime.now().date()
    payload = {
        "doctor_id": 1,
        "patient_name": "Test User",
        "phone_number": "+919876543210",
        "appointment_date": str(today + timedelta(days=1)),
        "appointment_time": "10:00",
        "notes": "Test booking",
        "symptoms": "headache"
    }
    r = requests.post(f"{BASE_URL}/book-appointment", json=payload)
    assert r.status_code == 200 and "id" in r.json()
    appointment_id = r.json()["id"]
    print_result("Book Appointment", True)
except Exception as e:
    print_result("Book Appointment", False, str(e))
    appointment_id = None

# 4. Reschedule Appointment
if appointment_id:
    try:
        payload = {
            "appointment_id": appointment_id,
            "new_date": str(today + timedelta(days=2)),
            "new_time": "11:00"
        }
        r = requests.put(f"{BASE_URL}/reschedule-appointment", json=payload)
        assert r.status_code == 200 and r.json().get("status", "").startswith("resched")
        print_result("Reschedule Appointment", True)
    except Exception as e:
        print_result("Reschedule Appointment", False, str(e))

# 5. Cancel Appointment
if appointment_id:
    try:
        r = requests.delete(f"{BASE_URL}/cancel-appointment/{appointment_id}")
        assert r.status_code == 200 and r.json().get("calendar_event_cancelled", True)
        print_result("Cancel Appointment", True)
    except Exception as e:
        print_result("Cancel Appointment", False, str(e))

# 6. Get Departments
try:
    r = requests.get(f"{BASE_URL}/departments")
    assert r.status_code == 200 and isinstance(r.json(), list)
    print_result("Get Departments", True)
except Exception as e:
    print_result("Get Departments", False, str(e))

# 7. Get Doctor Availability
try:
    r = requests.get(f"{BASE_URL}/doctor-availability/1")
    assert r.status_code == 200 and isinstance(r.json(), list)
    print_result("Get Doctor Availability", True)
except Exception as e:
    print_result("Get Doctor Availability", False, str(e))

# 8. Book Medical Test
try:
    payload = {
        "patient_name": "Test User",
        "test_ids": ["TST001"],
        "preferred_date": str(today + timedelta(days=3)),
        "preferred_time": "12:00",
        "contact_number": "+919876543210",
        "notes": "Routine test"
    }
    r = requests.post(f"{BASE_URL}/book-tests", json=payload)
    assert r.status_code == 200 and "booking_id" in r.json()
    test_booking_id = r.json()["booking_id"]
    print_result("Book Medical Test", True)
except Exception as e:
    print_result("Book Medical Test", False, str(e))
    test_booking_id = None

# 9. Cancel Test Booking
if test_booking_id:
    try:
        r = requests.delete(f"{BASE_URL}/tests/cancel/{test_booking_id}")
        assert r.status_code == 200
        print_result("Cancel Test Booking", True)
    except Exception as e:
        print_result("Cancel Test Booking", False, str(e))

# 10. Adaptive Diagnostic Session (v2)
try:
    session_id = f"test_{int(datetime.now().timestamp())}"
    payload = {"symptoms": "fever", "session_id": session_id}
    r = requests.post(f"{BASE_URL}/v2/start-adaptive-diagnostic", params=payload)
    assert r.status_code == 200 and "current_question" in r.json()
    print_result("Start Adaptive Diagnostic Session", True)
except Exception as e:
    print_result("Start Adaptive Diagnostic Session", False, str(e))

# 11. Phone Recognition
try:
    payload = {"phone_number": "+919876543210", "first_name": "Test"}
    r = requests.post(f"{BASE_URL}/phone-recognition", json=payload)
    assert r.status_code == 200 and "id" in r.json()
    print_result("Phone Recognition", True)
except Exception as e:
    print_result("Phone Recognition", False, str(e))

# 12. Smart Welcome
try:
    payload = {"phone_number": "+919876543210", "symptoms": "cough", "session_id": session_id}
    r = requests.post(f"{BASE_URL}/smart-welcome", json=payload)
    assert r.status_code == 200 and "welcome_message" in r.json()
    print_result("Smart Welcome", True)
except Exception as e:
    print_result("Smart Welcome", False, str(e))

# 13. Chat Basic
try:
    payload = {"message": "What should I do for a headache?"}
    r = requests.post(f"{BASE_URL}/chat", json=payload)
    assert r.status_code == 200
    print_result("Chat Basic", True)
except Exception as e:
    print_result("Chat Basic", False, str(e))

# 14. Chat Enhanced
try:
    payload = {"message": "I have chest pain", "session_id": session_id}
    r = requests.post(f"{BASE_URL}/chat-enhanced", json=payload)
    assert r.status_code == 200
    print_result("Chat Enhanced", True)
except Exception as e:
    print_result("Chat Enhanced", False, str(e))

# 15. Calendar Setup Page
try:
    r = requests.get(f"{BASE_URL}/calendar-setup")
    assert r.status_code == 200
    print_result("Calendar Setup Page", True)
except Exception as e:
    print_result("Calendar Setup Page", False, str(e))

# 16. Get Available Tests
try:
    r = requests.get(f"{BASE_URL}/available-tests")
    assert r.status_code == 200 and isinstance(r.json(), list)
    print_result("Get Available Tests", True)
except Exception as e:
    print_result("Get Available Tests", False, str(e))

# 17. Get Patient Appointments
try:
    r = requests.get(f"{BASE_URL}/appointments/patient/Test%20User")
    assert r.status_code == 200 and isinstance(r.json(), list)
    print_result("Get Patient Appointments", True)
except Exception as e:
    print_result("Get Patient Appointments", False, str(e))

# 18. Get Patient Test Bookings
try:
    r = requests.get(f"{BASE_URL}/tests/patient/Test%20User")
    assert r.status_code == 200 and isinstance(r.json(), list)
    print_result("Get Patient Test Bookings", True)
except Exception as e:
    print_result("Get Patient Test Bookings", False, str(e))

# 19. Session Management
try:
    payload = {"session_id": session_id, "first_name": "Test", "age": 30, "gender": "male"}
    r = requests.post(f"{BASE_URL}/session-user", json=payload)
    assert r.status_code == 200
    print_result("Session Management", True)
except Exception as e:
    print_result("Session Management", False, str(e))

# 20. Error Handling (invalid endpoint)
try:
    r = requests.get(f"{BASE_URL}/nonexistent-endpoint")
    assert r.status_code == 404
    print_result("Error Handling (404)", True)
except Exception as e:
    print_result("Error Handling (404)", False, str(e))

print("\nAll tests completed.") 