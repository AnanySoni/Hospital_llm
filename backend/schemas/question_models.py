from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class DiagnosticQuestion(BaseModel):
    """Enhanced diagnostic question with multiple types and metadata"""
    question_id: int
    question: str
    question_type: Literal["single_choice", "multiple_choice", "yes_no", "scale", "text"]
    options: Optional[List[str]] = None
    required: bool = True
    medical_rationale: Optional[str] = None
    confidence_targets: Optional[List[str]] = None
    priority_score: Optional[int] = Field(default=5, ge=1, le=10)

class QuestionAnswer(BaseModel):
    """User's answer to a diagnostic question"""
    question_id: int
    answer_value: Any  # Could be string, list, number
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Additional fields for compatibility with diagnosis generation
    question_text: Optional[str] = None
    question_type: Optional[str] = None

class DiagnosticSessionCreate(BaseModel):
    """Create new diagnostic session"""
    session_id: str
    initial_symptoms: str
    patient_profile: Optional[Dict[str, Any]] = None
    max_questions: int = Field(default=8, ge=1, le=15)

class DiagnosticSessionUpdate(BaseModel):
    """Update diagnostic session"""
    current_context: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "completed", "paused"]] = None
    patient_profile: Optional[Dict[str, Any]] = None

class DiagnosticSessionResponse(BaseModel):
    """Diagnostic session response"""
    id: str
    session_id: str
    initial_symptoms: str
    current_context: Dict[str, Any]
    status: str
    confidence_timeline: List[Dict[str, Any]]
    patient_profile: Dict[str, Any]
    questions_asked: int
    max_questions: int
    created_at: datetime
    updated_at: datetime

class AdaptiveRouterResponse(BaseModel):
    """Enhanced router response for adaptive questioning"""
    session_id: str
    current_question: Optional[DiagnosticQuestion] = None
    questions_remaining: int
    diagnosis: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    confidence: Optional[Dict[str, Any]] = None
    triage_assessment: Optional[Dict[str, Any]] = None
    message: str
    next_step: Literal["continue_diagnostic", "provide_diagnosis", "emergency_referral"]
    medical_reasoning: Optional[str] = None
    # New consequence messaging fields (Phase 1 implementation)
    consequence_message: Optional[Dict[str, Any]] = None
    risk_progression: Optional[Dict[str, Any]] = None
    persuasion_metrics: Optional[Dict[str, Any]] = None

class ConfidenceGapAnalysis(BaseModel):
    """Analysis of confidence gaps requiring additional questions"""
    uncertainty_factors: List[str]
    priority_areas: List[str]
    recommended_question_types: List[str]
    confidence_threshold: float = Field(ge=0.0, le=1.0)

class MedicalDecisionTree(BaseModel):
    """Medical decision tree node"""
    condition: str
    node_id: str
    questions: List[DiagnosticQuestion]
    decision_logic: Dict[str, Any]
    red_flags: List[str]
    confidence_requirements: Dict[str, float]

class QuestionGenerationRequest(BaseModel):
    """Request for generating next question"""
    session_id: str
    current_symptoms: str
    answer_history: List[QuestionAnswer]
    confidence_gaps: ConfidenceGapAnalysis
    patient_profile: Dict[str, Any]
    session_context: Dict[str, Any]

class QuestionGenerationResponse(BaseModel):
    """Response with generated question"""
    question: DiagnosticQuestion
    generation_reasoning: str
    confidence_impact_prediction: float
    alternative_questions: Optional[List[DiagnosticQuestion]] = None 