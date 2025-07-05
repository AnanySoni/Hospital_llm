"""
Test Booking Service
Handles test recommendations, booking, and management
"""

from sqlalchemy.orm import Session
from datetime import datetime, date
import uuid
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Mock test database (in production, this would be a proper database table)
AVAILABLE_TESTS = {
    "blood_cbc": {
        "id": "blood_cbc",
        "name": "Complete Blood Count (CBC)",
        "category": "Blood Test",
        "description": "Measures red blood cells, white blood cells, and platelets",
        "cost": 6000,
        "preparation": "Fasting for 8-12 hours",
        "duration": "15-30 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    },
    "blood_chemistry": {
        "id": "blood_chemistry",
        "name": "Comprehensive Metabolic Panel",
        "category": "Blood Test",
        "description": "Measures kidney function, liver function, blood sugar, and electrolytes",
        "cost": 9600,
        "preparation": "Fasting for 8-12 hours",
        "duration": "15-30 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    },
    "xray_chest": {
        "id": "xray_chest",
        "name": "Chest X-Ray",
        "category": "Imaging",
        "description": "X-ray of the chest to examine heart and lungs",
        "cost": 12000,
        "preparation": "No special preparation required",
        "duration": "10-15 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    },
    "ecg": {
        "id": "ecg",
        "name": "Electrocardiogram (ECG)",
        "category": "Cardiac Test",
        "description": "Records electrical activity of the heart",
        "cost": 16000,
        "preparation": "No special preparation required",
        "duration": "10-15 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    },
    "urinalysis": {
        "id": "urinalysis",
        "name": "Urinalysis",
        "category": "Urine Test",
        "description": "Analysis of urine for various health indicators",
        "cost": 3600,
        "preparation": "First morning urine preferred",
        "duration": "5-10 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    },
    "ultrasound_abdomen": {
        "id": "ultrasound_abdomen",
        "name": "Abdominal Ultrasound",
        "category": "Imaging",
        "description": "Ultrasound examination of abdominal organs",
        "cost": 24000,
        "preparation": "Fasting for 6-8 hours",
        "duration": "30-45 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00"]
    },
    "mri_brain": {
        "id": "mri_brain",
        "name": "Brain MRI",
        "category": "Imaging",
        "description": "Magnetic resonance imaging of the brain",
        "cost": 64000,
        "preparation": "No special preparation required",
        "duration": "45-60 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00"]
    },
    "stress_test": {
        "id": "stress_test",
        "name": "Cardiac Stress Test",
        "category": "Cardiac Test",
        "description": "Exercise test to evaluate heart function",
        "cost": 32000,
        "preparation": "Wear comfortable clothing and shoes",
        "duration": "45-60 minutes",
        "availability": ["09:00", "10:00", "11:00", "14:00", "15:00"]
    }
}

# Mock test bookings (in production, this would be a database table)
test_bookings = {}


class TestService:
    """Service for managing test bookings and recommendations"""
    
    @staticmethod
    async def get_available_tests() -> List[Dict]:
        """Get all available tests"""
        tests = []
        for test in AVAILABLE_TESTS.values():
            # Convert to frontend-compatible format
            tests.append({
                "test_id": test["id"],
                "test_name": test["name"],
                "test_category": test["category"],
                "description": test["description"],
                "urgency": "Within week",  # Default urgency
                "cost_estimate": f"₹{test['cost']}",
                "cost": test["cost"],
                "preparation_required": test["preparation"],
                "why_recommended": f"Standard {test['category'].lower()} for comprehensive health assessment"
            })
        return tests
    
    @staticmethod
    async def get_test_by_id(test_id: str) -> Optional[Dict]:
        """Get a specific test by ID"""
        test = AVAILABLE_TESTS.get(test_id)
        if test:
            return {
                "test_id": test["id"],
                "test_name": test["name"],
                "test_category": test["category"],
                "description": test["description"],
                "urgency": "Within week",
                "cost_estimate": f"₹{test['cost']}",
                "cost": test["cost"],
                "preparation_required": test["preparation"],
                "why_recommended": f"Standard {test['category'].lower()} for comprehensive health assessment"
            }
        return None
    
    @staticmethod
    async def get_tests_by_category(category: str) -> List[Dict]:
        """Get tests by category"""
        tests = []
        for test in AVAILABLE_TESTS.values():
            if test["category"].lower() == category.lower():
                tests.append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "test_category": test["category"],
                    "description": test["description"],
                    "urgency": "Within week",
                    "cost_estimate": f"₹{test['cost']}",
                    "cost": test["cost"],
                    "preparation_required": test["preparation"],
                    "why_recommended": f"Standard {test['category'].lower()} for comprehensive health assessment"
                })
        return tests
    
    @staticmethod
    async def check_test_availability(test_id: str, date: str, time: str) -> bool:
        """Check if a test is available at the specified date and time"""
        test = AVAILABLE_TESTS.get(test_id)
        if not test:
            return False
        
        # Check if time is in available slots
        if time not in test["availability"]:
            return False
        
        # For testing purposes, allow multiple bookings in the same slot
        # In production, this would be more strict
        booking_key = f"{test_id}_{date}_{time}"
        existing_bookings = sum(1 for key, booking in test_bookings.items() 
                               if key.startswith(f"{test_id}_{date}_{time}"))
        
        # Allow up to 3 concurrent bookings per slot for testing flexibility
        return existing_bookings < 3
    
    @staticmethod
    async def book_tests(
        patient_name: str,
        test_ids: List[str],
        preferred_date: str,
        preferred_time: str,
        contact_number: str,
        notes: Optional[str] = None
    ) -> Dict:
        """Book multiple tests for a patient"""
        
        # Validate all tests exist
        for test_id in test_ids:
            if test_id not in AVAILABLE_TESTS:
                raise ValueError(f"Test {test_id} not found")
        
        # Check availability for all tests
        for test_id in test_ids:
            if not await TestService.check_test_availability(test_id, preferred_date, preferred_time):
                raise ValueError(f"Test {test_id} not available at {preferred_date} {preferred_time}")
        
        # Create booking
        booking_id = str(uuid.uuid4())
        total_cost = sum(AVAILABLE_TESTS[test_id]["cost"] for test_id in test_ids)
        
        # Get test details
        tests_booked = []
        preparation_instructions = []
        
        for test_id in test_ids:
            test = AVAILABLE_TESTS[test_id]
            tests_booked.append(test["name"])
            if test["preparation"]:
                preparation_instructions.append(f"{test['name']}: {test['preparation']}")
            
            # Mark slot as booked with unique key
            booking_key = f"{test_id}_{preferred_date}_{preferred_time}_{booking_id}"
            test_bookings[booking_key] = {
                "booking_id": booking_id,
                "patient_name": patient_name,
                "test_id": test_id,
                "date": preferred_date,
                "time": preferred_time
            }
        
        booking = {
            "booking_id": booking_id,
            "message": f"Successfully booked {len(tests_booked)} test(s) for {patient_name}",
            "tests_booked": tests_booked,
            "appointment_date": preferred_date,
            "appointment_time": preferred_time,
            "total_cost": f"₹{total_cost:,}",
            "preparation_instructions": preparation_instructions
        }
        
        logger.info(f"Test booking created: {booking_id} for {patient_name}")
        return booking
    
    @staticmethod
    async def get_test_recommendations_by_symptoms(symptoms: str) -> List[Dict]:
        """Get test recommendations based on symptoms using LLM"""
        from utils.llm_utils import generate_test_recommendations
        
        try:
            # Use LLM to generate intelligent test recommendations
            diagnosis = {
                "possible_conditions": ["Based on symptoms analysis"],
                "confidence_level": "Medium",
                "urgency_level": "Routine",
                "recommended_action": "Medical tests recommended",
                "explanation": f"Analysis of symptoms: {symptoms}"
            }
            
            # Get LLM recommendations
            llm_recommendations = await generate_test_recommendations(diagnosis, symptoms)
            
            # Convert LLM recommendations to our format and match with available tests
            recommendations = []
            available_test_ids = set(AVAILABLE_TESTS.keys())
            
            for rec in llm_recommendations:
                test_id = rec.get("test_id", "").lower()
                
                # Try to match LLM recommendation with available tests
                matched_test = None
                if test_id in available_test_ids:
                    matched_test = AVAILABLE_TESTS[test_id]
                else:
                    # Try to find a match based on test name
                    test_name = rec.get("test_name", "").lower()
                    for tid, test in AVAILABLE_TESTS.items():
                        if any(word in test["name"].lower() for word in test_name.split()):
                            matched_test = test
                            break
                
                if matched_test:
                    recommendations.append({
                        "test_id": matched_test["id"],
                        "test_name": matched_test["name"],
                        "category": matched_test["category"],
                        "description": matched_test["description"],
                        "cost": matched_test["cost"],
                        "preparation": matched_test["preparation"],
                        "urgency": rec.get("urgency", "Within week")
                    })
            
            # If no matches found, fall back to symptom-based recommendations
            if not recommendations:
                recommendations = await TestService._get_fallback_recommendations(symptoms)
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            logger.error(f"Error getting LLM test recommendations: {e}")
            # Fallback to simple symptom-based recommendations
            return await TestService._get_fallback_recommendations(symptoms)
    
    @staticmethod
    async def _get_fallback_recommendations(symptoms: str) -> List[Dict]:
        """Fallback method for test recommendations based on simple keyword matching"""
        symptoms_lower = symptoms.lower()
        recommendations = []
        
        # Simple symptom-based recommendations
        if any(word in symptoms_lower for word in ["chest", "heart", "pain", "pressure"]):
            recommendations.extend([
                AVAILABLE_TESTS["ecg"],
                AVAILABLE_TESTS["xray_chest"],
                AVAILABLE_TESTS["blood_chemistry"]
            ])
        
        if any(word in symptoms_lower for word in ["headache", "dizzy", "confusion", "memory"]):
            recommendations.extend([
                AVAILABLE_TESTS["mri_brain"],
                AVAILABLE_TESTS["blood_chemistry"]
            ])
        
        if any(word in symptoms_lower for word in ["stomach", "abdomen", "nausea", "vomiting"]):
            recommendations.extend([
                AVAILABLE_TESTS["ultrasound_abdomen"],
                AVAILABLE_TESTS["blood_chemistry"],
                AVAILABLE_TESTS["urinalysis"]
            ])
        
        if any(word in symptoms_lower for word in ["fever", "infection", "sick"]):
            recommendations.extend([
                AVAILABLE_TESTS["blood_cbc"],
                AVAILABLE_TESTS["urinalysis"]
            ])
        
        # Always include basic blood work if no specific recommendations
        if not recommendations:
            recommendations.extend([
                AVAILABLE_TESTS["blood_cbc"],
                AVAILABLE_TESTS["blood_chemistry"]
            ])
        
        # Remove duplicates and convert to frontend format
        seen = set()
        unique_recommendations = []
        for test in recommendations:
            if test["id"] not in seen:
                seen.add(test["id"])
                unique_recommendations.append({
                    "test_id": test["id"],
                    "test_name": test["name"],
                    "category": test["category"],
                    "description": test["description"],
                    "cost": test["cost"],
                    "preparation": test["preparation"],
                    "urgency": "Within week"
                })
        
        return unique_recommendations[:5]
    
    @staticmethod
    async def cancel_test_booking(booking_id: str) -> Dict:
        """Cancel a test booking"""
        # Find and remove bookings
        cancelled_tests = []
        for booking_key, booking in list(test_bookings.items()):
            if booking["booking_id"] == booking_id:
                cancelled_tests.append(AVAILABLE_TESTS[booking["test_id"]]["name"])
                del test_bookings[booking_key]
        
        if not cancelled_tests:
            raise ValueError(f"Booking {booking_id} not found")
        
        logger.info(f"Test booking cancelled: {booking_id}")
        return {
            "booking_id": booking_id,
            "message": f"Successfully cancelled {len(cancelled_tests)} test(s)",
            "cancelled_tests": cancelled_tests
        }
    
    @staticmethod
    async def get_patient_test_bookings(patient_name: str) -> List[Dict]:
        """Get all test bookings for a patient"""
        patient_bookings = []
        seen_booking_ids = set()
        
        for booking_key, booking in test_bookings.items():
            if (booking["patient_name"].lower() == patient_name.lower() and 
                booking["booking_id"] not in seen_booking_ids):
                
                test_details = AVAILABLE_TESTS[booking["test_id"]]
                patient_bookings.append({
                    "booking_id": booking["booking_id"],
                    "test_name": test_details["name"],
                    "test_category": test_details["category"],
                    "appointment_date": booking["date"],
                    "appointment_time": booking["time"],
                    "cost": test_details["cost"],
                    "status": "confirmed"
                })
                seen_booking_ids.add(booking["booking_id"])
        
        return patient_bookings 