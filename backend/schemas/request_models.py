"""
Request and Response models with validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, time
import re


class SymptomsRequest(BaseModel):
    symptoms: str = Field(..., min_length=3, max_length=500, description="Patient symptoms description")
    
    @validator('symptoms')
    def validate_symptoms(cls, v):
        if not v.strip():
            raise ValueError("Symptoms cannot be empty")
        return v.strip()


class AppointmentRequest(BaseModel):
    doctor_id: int = Field(..., gt=0, description="Doctor ID")
    patient_name: str = Field(..., min_length=2, max_length=100, description="Patient full name")
    appointment_date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    appointment_time: str = Field(..., description="Appointment time in HH:MM format")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    symptoms: Optional[str] = Field(None, max_length=500, description="Symptoms that led to booking")
    
    @validator('patient_name')
    def validate_patient_name(cls, v):
        if not v.strip():
            raise ValueError("Patient name cannot be empty")
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v.strip()):
            raise ValueError("Patient name contains invalid characters")
        return v.strip().title()
    
    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        try:
            appointment_date = date.fromisoformat(v)
            if appointment_date < date.today():
                raise ValueError("Cannot book appointments in the past")
            return v
        except ValueError as e:
            if "past" in str(e):
                raise e
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    @validator('appointment_time')
    def validate_appointment_time(cls, v):
        # Handle both 12-hour (1:00 PM) and 24-hour (13:00) formats
        time_str = v.strip()
        
        # Check if it's 12-hour format (contains AM/PM)
        if re.search(r'\b(AM|PM)\b', time_str, re.IGNORECASE):
            # Parse 12-hour format
            try:
                from datetime import datetime
                parsed_time = datetime.strptime(time_str, "%I:%M %p")
                # Convert to 24-hour format
                hour = parsed_time.hour
                minute = parsed_time.minute
                time_24hr = f"{hour:02d}:{minute:02d}"
            except ValueError:
                raise ValueError("Invalid 12-hour time format. Use format like '1:00 PM'")
        else:
            # Assume 24-hour format
            if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", time_str):
                raise ValueError("Invalid time format. Use HH:MM (e.g., 14:30) or 12-hour format (e.g., 2:00 PM)")
            time_24hr = time_str
            hour = int(time_str.split(':')[0])
        
        # Validate business hours (9 AM to 6 PM)
        if hour < 9 or hour >= 18:
            raise ValueError("Appointments only available between 9:00 AM and 6:00 PM")
        
        return time_24hr
    
    @validator('notes')
    def validate_notes(cls, v):
        if v:
            return v.strip()
        return v


class RescheduleRequest(BaseModel):
    appointment_id: int = Field(..., gt=0, description="Appointment ID to reschedule")
    new_date: str = Field(..., description="New appointment date in YYYY-MM-DD format")
    new_time: str = Field(..., description="New appointment time in HH:MM format")
    
    @validator('new_date')
    def validate_new_date(cls, v):
        try:
            new_date = date.fromisoformat(v)
            if new_date < date.today():
                raise ValueError("Cannot reschedule to a past date")
            return v
        except ValueError as e:
            if "past" in str(e):
                raise e
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    @validator('new_time')
    def validate_new_time(cls, v):
        # Handle both 12-hour (1:00 PM) and 24-hour (13:00) formats
        time_str = v.strip()
        
        # Check if it's 12-hour format (contains AM/PM)
        if re.search(r'\b(AM|PM)\b', time_str, re.IGNORECASE):
            # Parse 12-hour format
            try:
                from datetime import datetime
                parsed_time = datetime.strptime(time_str, "%I:%M %p")
                # Convert to 24-hour format
                hour = parsed_time.hour
                minute = parsed_time.minute
                time_24hr = f"{hour:02d}:{minute:02d}"
            except ValueError:
                raise ValueError("Invalid 12-hour time format. Use format like '1:00 PM'")
        else:
            # Assume 24-hour format
            if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", time_str):
                raise ValueError("Invalid time format. Use HH:MM (e.g., 14:30) or 12-hour format (e.g., 2:00 PM)")
            time_24hr = time_str
            hour = int(time_str.split(':')[0])
        
        # Validate business hours
        if hour < 9 or hour >= 18:
            raise ValueError("Appointments only available between 9:00 AM and 6:00 PM")
        
        return time_24hr


class CalendarConnectionRequest(BaseModel):
    doctor_id: int = Field(..., gt=0, description="Doctor ID for calendar connection")


# Response models
class DoctorRecommendation(BaseModel):
    id: int
    name: str
    specialization: str
    reason: str
    experience: str
    expertise: List[str]


class AppointmentResponse(BaseModel):
    id: int
    message: str
    doctor_name: str
    appointment_date: str
    appointment_time: str
    calendar_event_created: bool
    note: str


class RescheduleResponse(BaseModel):
    message: str
    id: int
    doctor_name: str
    patient_name: str
    appointment_date: str
    appointment_time: str
    notes: Optional[str]
    status: str
    calendar_event_updated: bool


class CancelResponse(BaseModel):
    message: str
    calendar_event_cancelled: bool


class ErrorResponse(BaseModel):
    error: bool
    error_code: str
    message: str
    path: str
    details: Optional[List[str]] = None


# New models for Router LLM System
class DiagnosticQuestion(BaseModel):
    question_id: int
    question: str
    question_type: str = Field(..., description="Type: 'symptom_severity', 'duration', 'location', 'triggers', 'associated_symptoms'")
    options: Optional[List[str]] = Field(None, description="Multiple choice options if applicable")
    required: bool = True


class DiagnosticSession(BaseModel):
    session_id: str
    initial_symptoms: str
    questions_asked: List[DiagnosticQuestion] = []
    answers_received: dict = Field(default_factory=dict)
    current_question_index: int = 0
    is_complete: bool = False


class DiagnosticAnswer(BaseModel):
    session_id: str
    question_id: int
    answer: str


class PredictiveDiagnosis(BaseModel):
    possible_conditions: List[str] = Field(..., description="List of possible medical conditions")
    confidence_level: str = Field(..., description="High/Medium/Low confidence in diagnosis")
    urgency_level: str = Field(..., description="Emergency/Urgent/Routine")
    recommended_action: str = Field(..., description="Immediate action recommended")
    explanation: str = Field(..., description="Explanation of the diagnosis")


class TestRecommendation(BaseModel):
    test_id: str
    test_name: str
    test_category: str = Field(..., description="Blood test, Imaging, Physical exam, etc.")
    description: str
    urgency: str = Field(..., description="Immediate/Within 24 hours/Within week/Routine")
    cost_estimate: Optional[str] = None
    preparation_required: Optional[str] = None
    why_recommended: str


class RouterDecision(BaseModel):
    action_type: str = Field(..., description="'book_appointment', 'book_tests', 'both', 'emergency'")
    reasoning: str
    recommended_tests: List[TestRecommendation] = []
    recommended_doctors: List[DoctorRecommendation] = []
    urgency_message: str


class RouterResponse(BaseModel):
    session_id: str
    current_question: Optional[DiagnosticQuestion] = None
    questions_remaining: int
    diagnosis: Optional[PredictiveDiagnosis] = None
    decision: Optional[RouterDecision] = None
    message: str
    next_step: str


class TestBookingRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=100)
    test_ids: List[str] = Field(..., description="List of test IDs to book")
    preferred_date: str = Field(..., description="Preferred date in YYYY-MM-DD format")
    preferred_time: str = Field(..., description="Preferred time in HH:MM format")
    contact_number: str = Field(..., description="Patient contact number")
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('patient_name')
    def validate_patient_name(cls, v):
        if not v.strip():
            raise ValueError("Patient name cannot be empty")
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v.strip()):
            raise ValueError("Patient name contains invalid characters")
        return v.strip().title()
    
    @validator('contact_number')
    def validate_contact_number(cls, v):
        # Basic phone number validation
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[\d]{10,15}$', cleaned):
            raise ValueError("Invalid contact number format")
        return cleaned


class TestBookingResponse(BaseModel):
    booking_id: str
    message: str
    tests_booked: List[str]
    appointment_date: str
    appointment_time: str
    total_cost: Optional[str] = None
    preparation_instructions: List[str] = [] 