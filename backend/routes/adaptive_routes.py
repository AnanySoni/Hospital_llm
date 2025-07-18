"""
Adaptive Diagnostic Routes for Phase 1 Month 2
New endpoints for advanced question generation (can coexist with existing endpoints)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from schemas.question_models import (
    DiagnosticSessionCreate,
    AdaptiveRouterResponse,
    QuestionAnswer
)
from schemas.triage_models import (
    UrgencyAssessmentRequest,
    EmergencyCheckRequest,
    TriageResponse
)
from services.diagnostic_flow_service import DiagnosticFlowService
from services.triage_service import TriageService
from utils.urgency_assessor import assess_medical_urgency, quick_emergency_screening

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v2", tags=["Adaptive Diagnostics"])

# Service instances
diagnostic_flow = DiagnosticFlowService()
triage_service = TriageService()

@router.post("/start-adaptive-diagnostic", response_model=AdaptiveRouterResponse)
async def start_adaptive_diagnostic(
    symptoms: str,
    session_id: str,
    patient_profile: Optional[Dict[str, Any]] = None
):
    """
    Start a new adaptive diagnostic session with intelligent questioning
    This is the v2 version that can run alongside existing /start-diagnostic
    """
    try:
        logger.info(f"Starting adaptive diagnostic for session {session_id}")
        
        response = await diagnostic_flow.start_adaptive_diagnostic(
            session_id=session_id,
            symptoms=symptoms,
            patient_profile=patient_profile
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in adaptive diagnostic start: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to start adaptive diagnostic: {str(e)}"
        )

@router.post("/answer-adaptive-question", response_model=AdaptiveRouterResponse)
async def answer_adaptive_question(
    session_id: str,
    question_id: int,
    answer_value: Any,
    question_text: Optional[str] = None,
    question_type: Optional[str] = None
):
    """
    Submit answer to an adaptive question and get next step
    This is the v2 version that can run alongside existing /answer-diagnostic
    """
    try:
        logger.info(f"Processing answer for session {session_id}, question {question_id}")
        
        # Prepare answer payload
        answer_data = {
            "question_text": question_text,
            "question_type": question_type,
            "answer_value": answer_value
        }
        
        response = await diagnostic_flow.process_answer_and_continue(
            session_id=session_id,
            question_id=question_id,
            answer=answer_data
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing adaptive answer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer: {str(e)}"
        )

@router.post("/complete-adaptive-session")
async def complete_adaptive_session(session_id: str):
    """Mark an adaptive diagnostic session as completed"""
    try:
        await diagnostic_flow.complete_session(session_id)
        return {"message": "Session completed successfully"}
        
    except Exception as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete session: {str(e)}"
        )

@router.get("/adaptive-session/{session_id}")
async def get_adaptive_session_info(session_id: str):
    """Get information about an adaptive diagnostic session"""
    try:
        session = await diagnostic_flow.get_diagnostic_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        answer_history = await diagnostic_flow.get_answer_history(session_id)
        
        return {
            "session_id": session.session_id,
            "status": session.status,
            "initial_symptoms": session.initial_symptoms,
            "questions_asked": session.questions_asked,
            "max_questions": session.max_questions,
            "answer_count": len(answer_history),
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session info: {str(e)}"
        )

# Feature flag endpoint (for A/B testing)
@router.get("/adaptive-diagnostic-enabled")
async def is_adaptive_diagnostic_enabled():
    """Check if adaptive diagnostic feature is enabled"""
    # This could check environment variables or database settings
    return {"enabled": True, "version": "1.0.0"}

# Triage and Urgency Assessment Endpoints (Phase 1 Month 3)

@router.post("/assess-urgency", response_model=TriageResponse)
async def assess_urgency_endpoint(request: UrgencyAssessmentRequest):
    """
    Comprehensive urgency assessment endpoint for medical triage
    Provides detailed triage analysis with risk factors and recommendations
    """
    try:
        logger.info(f"Urgency assessment requested for patient age {request.patient_age}")
        
        # Perform comprehensive triage assessment
        triage_assessment = await triage_service.assess_urgency_level(
            symptoms=request.symptoms,
            answers=request.answers,
            patient_profile={
                "age": request.patient_age,
                "medical_history": request.medical_history,
                "current_medications": request.current_medications,
                "vital_signs": request.vital_signs
            },
            confidence_score=0.7  # Default confidence for initial assessment
        )
        
        # Determine next steps based on triage level
        next_steps = []
        emergency_contacts = None
        
        if triage_assessment.level.value == "emergency":
            next_steps = [
                "Call 911 immediately",
                "Go to nearest emergency room",
                "Do not drive yourself - call ambulance or have someone drive you"
            ]
            emergency_contacts = {"emergency": "911", "poison_control": "1-800-222-1222"}
            
        elif triage_assessment.level.value == "urgent":
            next_steps = [
                "Contact your doctor immediately",
                "Go to urgent care center if doctor unavailable",
                "Monitor symptoms closely"
            ]
            
        elif triage_assessment.level.value == "soon":
            next_steps = [
                "Schedule appointment with healthcare provider within 1 week",
                "Monitor symptoms for any worsening",
                "Keep track of symptom changes"
            ]
            
        else:  # routine
            next_steps = [
                "Schedule routine appointment with primary care provider",
                "Continue normal activities unless symptoms worsen",
                "Consider preventive care discussion"
            ]
        
        return TriageResponse(
            assessment=triage_assessment,
            next_steps=next_steps,
            emergency_contacts=emergency_contacts,
            follow_up_timeframe="Contact healthcare provider if symptoms persist or worsen"
        )
        
    except Exception as e:
        logger.error(f"Error in urgency assessment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assess urgency: {str(e)}"
        )

@router.post("/emergency-check")
async def emergency_check_endpoint(request: EmergencyCheckRequest):
    """
    Quick emergency screening endpoint for immediate red flag detection
    Returns immediate emergency status and basic recommendations
    """
    try:
        logger.info(f"Emergency check requested for symptoms: {request.symptoms[:50]}...")
        
        # Perform quick emergency screening
        emergency_result = await quick_emergency_screening(
            symptoms=request.symptoms,
            age=request.age
        )
        
        return {
            "emergency_detected": emergency_result["emergency_detected"],
            "confidence": emergency_result["confidence"],
            "urgency_level": emergency_result["urgency_level"],
            "recommendation": emergency_result["recommendation"],
            "immediate_action": "CALL 911 NOW" if emergency_result["emergency_detected"] else "Proceed with normal assessment",
            "emergency_indicators": emergency_result.get("detected_keywords", [])
        }
        
    except Exception as e:
        logger.error(f"Error in emergency check: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform emergency check: {str(e)}"
        )

@router.post("/simplified-urgency-assessment")
async def simplified_urgency_assessment(
    symptoms: str,
    patient_age: Optional[int] = None,
    medical_history: Optional[str] = None
):
    """
    Simplified urgency assessment for basic symptom triage
    Lightweight endpoint for quick urgency determination
    """
    try:
        logger.info(f"Simplified urgency assessment for age {patient_age}")
        
        # Convert medical history string to list
        history_list = []
        if medical_history:
            history_list = [condition.strip() for condition in medical_history.split(',') if condition.strip()]
        
        # Perform simplified assessment
        assessment = await assess_medical_urgency(
            symptoms=symptoms,
            patient_age=patient_age or 35,
            medical_history=history_list,
            current_answers={},
            confidence_score=None
        )
        
        return {
            "urgency_level": assessment.level.value,
            "time_urgency": assessment.time_urgency,
            "confidence_score": assessment.confidence_score,
            "reasoning": assessment.reasoning,
            "recommendations": assessment.recommendations,
            "emergency_override": assessment.emergency_override,
            "red_flag_count": len(assessment.red_flags)
        }
        
    except Exception as e:
        logger.error(f"Error in simplified urgency assessment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assess urgency: {str(e)}"
        ) 