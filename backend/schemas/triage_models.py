"""
Triage Models for Phase 1 Month 3 - Risk Stratification & Triage
Defines urgency levels, risk factors, and triage assessment structures
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TriageLevel(str, Enum):
    """Medical triage urgency levels with timeframes"""
    EMERGENCY = "emergency"      # <1 hour - 911/ER immediate
    URGENT = "urgent"           # 24-48 hours - urgent care
    SOON = "soon"               # 1 week - specialist referral
    ROUTINE = "routine"         # 2+ weeks - primary care


class RiskFactor(BaseModel):
    """Individual risk factor contributing to triage decision"""
    factor_type: str = Field(..., description="Type: age, symptom, medical_history, lifestyle")
    severity: float = Field(..., ge=0.0, le=1.0, description="Risk severity 0.0-1.0")
    description: str = Field(..., description="Human-readable risk description")
    weight: float = Field(default=1.0, description="Weight in overall assessment")


class RedFlag(BaseModel):
    """Critical symptoms requiring immediate attention"""
    symptom: str = Field(..., description="Red flag symptom identified")
    category: str = Field(..., description="Medical category: cardiovascular, neurological, etc.")
    urgency_level: TriageLevel = Field(..., description="Minimum urgency level required")
    reasoning: str = Field(..., description="Why this is considered a red flag")


class TriageAssessment(BaseModel):
    """Complete triage assessment with urgency determination"""
    level: TriageLevel = Field(..., description="Determined triage level")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    time_urgency: str = Field(..., description="Human-readable timeframe for care")
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    red_flags: List[RedFlag] = Field(default_factory=list)
    reasoning: str = Field(..., description="Medical reasoning for triage decision")
    emergency_override: bool = Field(default=False, description="Emergency detection override")
    recommendations: List[str] = Field(default_factory=list, description="Care recommendations")


class UrgencyAssessmentRequest(BaseModel):
    """Request model for urgency assessment endpoint"""
    symptoms: str = Field(..., description="Patient symptoms description")
    patient_age: Optional[int] = Field(None, description="Patient age for risk stratification")
    medical_history: List[str] = Field(default_factory=list, description="Known medical conditions")
    current_medications: List[str] = Field(default_factory=list, description="Current medications")
    vital_signs: Optional[Dict[str, Any]] = Field(None, description="Available vital signs")
    answers: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic Q&A responses")


class EmergencyCheckRequest(BaseModel):
    """Quick emergency screening request"""
    symptoms: str = Field(..., description="Symptoms to check for emergency indicators")
    age: Optional[int] = Field(None, description="Patient age")
    
    
class TriageResponse(BaseModel):
    """Response model for triage assessment"""
    assessment: TriageAssessment
    next_steps: List[str] = Field(default_factory=list)
    emergency_contacts: Optional[Dict[str, str]] = Field(None, description="Emergency contact info")
    follow_up_timeframe: str = Field(..., description="When to follow up if symptoms persist")


# Age-based risk multipliers for different conditions
AGE_RISK_MULTIPLIERS = {
    "chest_pain": {
        (0, 30): 0.3,   # Low risk in young adults
        (30, 45): 0.5,  # Moderate risk 
        (45, 65): 0.8,  # Higher risk middle-aged
        (65, 100): 1.2  # Highest risk elderly
    },
    "headache": {
        (0, 18): 0.8,   # Higher risk in children
        (18, 50): 0.4,  # Lower risk young adults
        (50, 65): 0.7,  # Moderate risk middle-aged
        (65, 100): 0.9  # Higher risk elderly
    },
    "abdominal_pain": {
        (0, 18): 0.9,   # Higher risk in children
        (18, 40): 0.5,  # Lower risk young adults
        (40, 65): 0.7,  # Moderate risk
        (65, 100): 1.0  # Higher risk elderly
    },
    "breathing_difficulty": {
        (0, 5): 1.2,    # Very high risk infants
        (5, 18): 0.8,   # Moderate risk children
        (18, 65): 0.6,  # Lower risk adults
        (65, 100): 1.1  # High risk elderly
    }
}


# Red flag symptom patterns requiring immediate attention
RED_FLAG_PATTERNS = {
    "cardiovascular": [
        "crushing chest pain",
        "chest pain with shortness of breath",
        "chest pain radiating to arm",
        "severe chest pressure",
        "sudden severe chest pain"
    ],
    "neurological": [
        "sudden severe headache",
        "headache with vision changes",
        "sudden confusion",
        "weakness on one side",
        "difficulty speaking suddenly",
        "severe head injury"
    ],
    "respiratory": [
        "severe difficulty breathing",
        "cannot speak in full sentences",
        "blue lips or fingernails",
        "choking",
        "severe asthma attack"
    ],
    "gastrointestinal": [
        "vomiting blood",
        "severe abdominal pain",
        "signs of internal bleeding",
        "severe dehydration"
    ],
    "trauma": [
        "severe bleeding",
        "possible fracture",
        "head trauma",
        "severe burns",
        "suspected spinal injury"
    ]
} 