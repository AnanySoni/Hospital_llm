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
    TestBookingResponse
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
    "TestBookingResponse"
] 