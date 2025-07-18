"""
Request and Response models with validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, TYPE_CHECKING
from datetime import date, time, datetime
import re

if TYPE_CHECKING:
    pass

# Import TriageAssessment - must be available at runtime for Pydantic
from .triage_models import TriageAssessment


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
    phone_number: str = Field(..., min_length=10, max_length=20, description="Patient phone number")
    appointment_date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    appointment_time: str = Field(..., description="Appointment time in HH:MM format")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    symptoms: Optional[str] = Field(None, max_length=500, description="Symptoms that led to booking")
    
    @validator('patient_name')
    def validate_patient_name(cls, v):
        if not v.strip():
            raise ValueError("Patient name cannot be empty")
        if not re.match(r"^[a-zA-Z0-9\s\-'\.]+$", v.strip()):
            raise ValueError("Patient name contains invalid characters")
        return v.strip().title()
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v.strip():
            raise ValueError("Phone number cannot be empty")
        # Remove all non-digit characters for validation
        digits = re.sub(r'\D', '', v)
        
        # Indian phone numbers should be 10 digits (without country code) or 12 digits (with +91)
        if len(digits) == 10:
            # Valid Indian mobile number format
            if not digits.startswith(('6', '7', '8', '9')):
                raise ValueError("Indian mobile numbers should start with 6, 7, 8, or 9")
        elif len(digits) == 12 and digits.startswith('91'):
            # Valid with country code
            mobile_part = digits[2:]
            if not mobile_part.startswith(('6', '7', '8', '9')):
                raise ValueError("Indian mobile numbers should start with 6, 7, 8, or 9")
        elif len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        elif len(digits) > 15:
            raise ValueError("Phone number is too long")
            
        # Keep original format for display
        return v.strip()
    
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


class ConfidenceScore(BaseModel):
    score: float  # 0.0-1.0
    level: str   # "high", "medium", "low"
    reasoning: str
    uncertainty_factors: List[str] = []


class PredictiveDiagnosis(BaseModel):
    possible_conditions: List[str] = Field(..., description="List of possible medical conditions")
    confidence_level: str = Field(..., description="High/Medium/Low confidence in diagnosis")
    urgency_level: str = Field(..., description="Emergency/Urgent/Routine")
    recommended_action: str = Field(..., description="Immediate action recommended")
    explanation: str = Field(..., description="Explanation of the diagnosis")
    confidence_score: Optional[float] = Field(None, description="Numerical confidence score 0.0-1.0")
    diagnostic_confidence: Optional[ConfidenceScore] = Field(None, description="Detailed confidence analysis")


class TestRecommendation(BaseModel):
    test_id: str
    test_name: str
    test_category: str = Field(..., description="Blood test, Imaging, Physical exam, etc.")
    description: str
    urgency: str = Field(..., description="Immediate/Within 24 hours/Within week/Routine")
    cost_estimate: Optional[str] = None
    preparation_required: Optional[str] = None
    why_recommended: str


# Consequence messaging models (must be defined before RouterResponse)
class ConsequenceMessage(BaseModel):
    primary_consequence: str = Field(..., description="Main consequence warning")
    risk_level: str = Field(..., description="emergency/urgent/routine")
    timeframe: str = Field(..., description="Time window for action")
    escalation_risks: List[str] = Field(default_factory=list, description="What could happen if delayed")
    opportunity_cost: Optional[str] = Field(None, description="What could be lost by waiting")
    social_proof: Optional[str] = Field(None, description="Expert/statistical validation")
    regret_prevention: Optional[str] = Field(None, description="Patient story elements")
    action_benefits: str = Field(..., description="Benefits of taking action now")


class RiskProgression(BaseModel):
    immediate_risk: str = Field(..., description="Risk within hours/days")
    short_term_risk: str = Field(..., description="Risk within weeks")
    long_term_risk: str = Field(..., description="Risk within months/years")
    prevention_window: str = Field(..., description="Optimal treatment window")


class PersuasionMetrics(BaseModel):
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Urgency level 0.0-1.0")
    fear_appeal_strength: str = Field(..., description="low/medium/high")
    message_type: str = Field(..., description="statistical/story/authority/opportunity")
    expected_conversion: Optional[float] = Field(None, description="Predicted booking rate")


class RouterDecision(BaseModel):
    action_type: str = Field(..., description="'book_appointment', 'book_tests', 'both', 'emergency'")
    reasoning: str
    recommended_tests: List[TestRecommendation] = []
    recommended_doctors: List[DoctorRecommendation] = []
    urgency_message: str
    decision_confidence: Optional[ConfidenceScore] = Field(None, description="Confidence in routing decision")


class RouterResponse(BaseModel):
    session_id: str
    current_question: Optional[DiagnosticQuestion] = None
    questions_remaining: int
    diagnosis: Optional[PredictiveDiagnosis] = None
    decision: Optional[RouterDecision] = None
    message: str
    next_step: str
    confidence: Optional[ConfidenceScore] = None
    triage_assessment: Optional[TriageAssessment] = None
    urgency_override: Optional[bool] = None  # Emergency detection override
    # New consequence messaging fields (optional for backward compatibility)
    consequence_message: Optional[ConsequenceMessage] = None
    risk_progression: Optional[RiskProgression] = None
    persuasion_metrics: Optional[PersuasionMetrics] = None


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
        if not re.match(r"^[a-zA-Z0-9\s\-'\.]+$", v.strip()):
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


# Session User Schemas
class SessionUserCreate(BaseModel):
    session_id: str
    first_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


class SessionUserResponse(BaseModel):
    id: int
    session_id: str
    first_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


# Patient History Schemas
class PatientHistoryCreate(BaseModel):
    entry_type: str  # symptom, diagnosis, appointment, test, medication
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_recommendations: Optional[str] = None
    test_recommendations: Optional[str] = None
    appointment_outcome: Optional[str] = None
    test_results: Optional[str] = None
    medications_mentioned: Optional[str] = None
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None
    family_history: Optional[str] = None
    severity_level: Optional[str] = None
    confidence_score: Optional[str] = None
    urgency_level: Optional[str] = None
    session_context: Optional[str] = None


class PatientHistoryResponse(BaseModel):
    id: int
    entry_type: str
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_recommendations: Optional[str] = None
    test_recommendations: Optional[str] = None
    severity_level: Optional[str] = None
    urgency_level: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Enhanced Chat Request
class EnhancedChatRequest(BaseModel):
    message: str
    session_id: str
    user_info: Optional[dict] = None  # {first_name, age, gender}
    include_history: bool = True


# Session History Response
class SessionHistoryResponse(BaseModel):
    session_id: str
    conversation_count: int
    recent_symptoms: List[str]
    recent_diagnoses: List[str]
    chronic_conditions: List[str]
    allergies: List[str]
    appointment_history: List[dict]
    test_history: List[dict]
    last_visit: Optional[datetime] = None

    class Config:
        from_attributes = True


# Phone-based recognition models
class PhoneRecognitionRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20, description="Patient phone number")
    first_name: str = Field(None, min_length=1, max_length=100, description="First name (for new patients)")
    family_member_type: str = Field("self", description="Relationship: self, child, parent, spouse, sibling")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v.strip():
            raise ValueError("Phone number cannot be empty")
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', v.strip())
        
        # Indian phone numbers should be 10 digits (without country code) or 12 digits (with +91)
        if len(digits) == 10:
            # Valid Indian mobile number format
            if not digits.startswith(('6', '7', '8', '9')):
                raise ValueError("Indian mobile numbers should start with 6, 7, 8, or 9")
        elif len(digits) == 12 and digits.startswith('91'):
            # Valid with country code
            mobile_part = digits[2:]
            if not mobile_part.startswith(('6', '7', '8', '9')):
                raise ValueError("Indian mobile numbers should start with 6, 7, 8, or 9")
        elif len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        elif len(digits) > 15:
            raise ValueError("Phone number is too long")
            
        return v.strip()


class SmartWelcomeRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    symptoms: str = Field(..., min_length=2, max_length=1000, description="Current symptoms")
    session_id: str = Field(..., description="Current session ID")
    conversation_history: Optional[str] = Field(None, description="Current conversation context")


class SymptomAnalysisRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=15)
    symptoms: str = Field(..., min_length=2, max_length=1000)
    patient_name: str = Field(None, max_length=100)


class PatientProfileResponse(BaseModel):
    id: int
    phone_number: str
    first_name: str
    last_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    family_member_type: str
    total_visits: int
    last_visit_date: Optional[datetime]
    last_visit_symptoms: Optional[str]
    chronic_conditions: List[str]
    allergies: List[str]
    
    class Config:
        from_attributes = True


class SmartWelcomeResponse(BaseModel):
    patient_profile: PatientProfileResponse
    is_new_patient: bool
    welcome_message: str
    symptom_analysis: dict
    next_action: str  # "start_diagnostic", "collect_more_info", "ask_family_clarification"
    
    
class PhoneBasedChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., description="Session ID")
    phone_number: Optional[str] = Field(None, description="Phone number for patient recognition")
    patient_name: Optional[str] = Field(None, description="Patient name when first provided")
    include_history: bool = Field(False, description="Whether to include patient history in context")
    is_booking_flow: bool = Field(False, description="Whether this is part of a booking flow")


 