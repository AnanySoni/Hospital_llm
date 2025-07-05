"""
Schemas package - Contains Pydantic models for request/response validation
"""

from .request_models import (
    SymptomsRequest,
    AppointmentRequest,
    RescheduleRequest,
    CalendarConnectionRequest,
    DoctorRecommendation,
    AppointmentResponse,
    RescheduleResponse,
    CancelResponse,
    ErrorResponse,
    # New diagnostic router schemas
    DiagnosticQuestion,
    DiagnosticSession,
    DiagnosticAnswer,
    PredictiveDiagnosis,
    TestRecommendation,
    RouterDecision,
    RouterResponse,
    TestBookingRequest,
    TestBookingResponse,
    # New session-based user tracking schemas
    SessionUserCreate,
    SessionUserResponse,
    PatientHistoryCreate,
    PatientHistoryResponse,
    EnhancedChatRequest,
    SessionHistoryResponse,
    # Phone-based recognition schemas
    PhoneRecognitionRequest,
    SmartWelcomeRequest,
    SymptomAnalysisRequest,
    PatientProfileResponse,
    SmartWelcomeResponse,
    PhoneBasedChatRequest
)

__all__ = [
    "SymptomsRequest",
    "AppointmentRequest", 
    "RescheduleRequest",
    "CalendarConnectionRequest",
    "DoctorRecommendation",
    "AppointmentResponse",
    "RescheduleResponse",
    "CancelResponse",
    "ErrorResponse",
    # New diagnostic router schemas
    "DiagnosticQuestion",
    "DiagnosticSession", 
    "DiagnosticAnswer",
    "PredictiveDiagnosis",
    "TestRecommendation",
    "RouterDecision",
    "RouterResponse",
    "TestBookingRequest",
    "TestBookingResponse",
    # New session-based user tracking schemas
    "SessionUserCreate",
    "SessionUserResponse",
    "PatientHistoryCreate",
    "PatientHistoryResponse",
    "EnhancedChatRequest",
    "SessionHistoryResponse",
    # Phone-based recognition schemas
    "PhoneRecognitionRequest",
    "SmartWelcomeRequest",
    "SymptomAnalysisRequest",
    "PatientProfileResponse",
    "SmartWelcomeResponse",
    "PhoneBasedChatRequest"
] 