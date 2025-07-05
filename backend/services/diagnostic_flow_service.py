"""
Diagnostic Flow Service for Phase 1 Month 2
Manages the adaptive questioning flow and integrates with existing diagnostic system
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import DiagnosticSession, QuestionAnswer as DBQuestionAnswer
from schemas.question_models import (
    DiagnosticQuestion,
    QuestionAnswer,
    DiagnosticSessionCreate,
    AdaptiveRouterResponse,
    ConfidenceGapAnalysis
)
from schemas.request_models import RouterResponse, PredictiveDiagnosis, ConsequenceMessage, RiskProgression, PersuasionMetrics
from utils.adaptive_question_generator import AdaptiveQuestionGenerator
from utils.llm_utils import generate_predictive_diagnosis, make_routing_decision
from services.triage_service import TriageService
from services.consequence_messaging_service import ConsequenceMessagingService
from utils.urgency_assessor import assess_medical_urgency

logger = logging.getLogger(__name__)

class DiagnosticFlowService:
    def __init__(self):
        self.question_generator = AdaptiveQuestionGenerator()
        self.triage_service = TriageService()
        self.consequence_service = ConsequenceMessagingService()
    
    def get_db_session(self):
        """Get database session with proper cleanup"""
        return next(get_db())
    
    async def start_adaptive_diagnostic(
        self,
        session_id: str,
        symptoms: str,
        patient_profile: Optional[Dict[str, Any]] = None
    ) -> AdaptiveRouterResponse:
        """Start a new adaptive diagnostic session"""
        
        try:
            # Create diagnostic session
            db_session = await self.create_diagnostic_session(
                session_id=session_id,
                symptoms=symptoms,
                patient_profile=patient_profile or {}
            )
            
            # Generate first question
            confidence_gaps = ConfidenceGapAnalysis(
                uncertainty_factors=["symptom_location", "symptom_timing", "symptom_quality"],
                priority_areas=["initial_assessment"],
                recommended_question_types=["single_choice"],
                confidence_threshold=0.7
            )
            
            first_question_response = await self.question_generator.generate_next_question(
                symptoms=symptoms,
                answer_history=[],
                confidence_gaps=confidence_gaps,
                patient_profile=patient_profile or {},
                session_context={}
            )
            
            return AdaptiveRouterResponse(
                session_id=session_id,
                current_question=first_question_response.question,
                questions_remaining=db_session.max_questions - 1,
                message="Let's start with some questions to better understand your symptoms.",
                next_step="continue_diagnostic",
                medical_reasoning=first_question_response.generation_reasoning
            )
            
        except Exception as e:
            logger.error(f"Error starting adaptive diagnostic: {e}")
            return AdaptiveRouterResponse(
                session_id=session_id,
                questions_remaining=0,
                message="Unable to start diagnostic session. Please try again.",
                next_step="provide_diagnosis"
            )
    
    async def process_answer_and_continue(
        self,
        session_id: str,
        question_id: int,
        answer: Dict[str, Any]
    ) -> AdaptiveRouterResponse:
        """Process user answer and determine next step"""
        
        try:
            # Get diagnostic session
            db_session = await self.get_diagnostic_session(session_id)
            if not db_session:
                raise ValueError(f"Diagnostic session {session_id} not found")
            
            # Record the answer
            await self.record_answer(
                session_id=session_id,
                question_id=question_id,
                answer=answer
            )
            
            # Get updated answer history
            answer_history = await self.get_answer_history(session_id)
            
            # Decide: continue questions or provide diagnosis?
            should_continue = await self.should_continue_questioning(
                db_session, answer_history
            )
            
            if should_continue:
                # Generate next question
                return await self.generate_next_question_response(
                    db_session, answer_history
                )
            else:
                # Provide final diagnosis
                return await self.generate_final_diagnosis(
                    db_session, answer_history
                )
                
        except Exception as e:
            logger.error(f"Error processing answer: {e}")
            return AdaptiveRouterResponse(
                session_id=session_id,
                questions_remaining=0,
                message="Error processing your answer. Let me provide what I can determine so far.",
                next_step="provide_diagnosis"
            )
    
    async def create_diagnostic_session(
        self,
        session_id: str,
        symptoms: str,
        patient_profile: Dict[str, Any]
    ) -> DiagnosticSession:
        """Create new diagnostic session in database"""
        
        db = self.get_db_session()
        try:
            # Check if session already exists
            existing = db.query(DiagnosticSession).filter(
                DiagnosticSession.session_id == session_id
            ).first()
            
            if existing:
                return existing
            
            # Limit to 5 questions per session to avoid lengthy interviews
            db_session = DiagnosticSession(
                id=f"diag_{session_id}",
                session_id=session_id,
                initial_symptoms=symptoms,
                patient_profile=json.dumps(patient_profile),
                status="active",
                max_questions=5
            )
            
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            
            logger.info(f"Created diagnostic session: {session_id}")
            return db_session
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating diagnostic session: {e}")
            raise
        finally:
            db.close()
    
    async def get_diagnostic_session(self, session_id: str) -> Optional[DiagnosticSession]:
        """Get diagnostic session from database"""
        
        db = self.get_db_session()
        try:
            return db.query(DiagnosticSession).filter(
                DiagnosticSession.session_id == session_id
            ).first()
        finally:
            db.close()
    
    async def record_answer(
        self,
        session_id: str,
        question_id: int,
        answer: Dict[str, Any]
    ) -> None:
        """Record user's answer to a question"""
        
        db = self.get_db_session()
        try:
            # Get diagnostic session
            db_session = db.query(DiagnosticSession).filter(
                DiagnosticSession.session_id == session_id
            ).first()
            
            if not db_session:
                raise ValueError(f"Diagnostic session {session_id} not found")
            
            # Create question answer record
            # Provide fallback values for required fields
            question_text = answer.get("question_text") or f"Question {question_id}"
            question_type = answer.get("question_type") or "text_response"
            
            qa = DBQuestionAnswer(
                diagnostic_session_id=db_session.id,
                question_id=question_id,
                question_text=question_text,
                question_type=question_type,
                answer_payload=json.dumps(answer.get("answer_value", "")),
                confidence_before=answer.get("confidence_before"),
                confidence_after=answer.get("confidence_after")
            )
            
            db.add(qa)
            
            # Update session
            db_session.questions_asked += 1
            db_session.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Recorded answer for session {session_id}, question {question_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording answer: {e}")
            raise
        finally:
            db.close()
    
    async def get_answer_history(self, session_id: str) -> List[QuestionAnswer]:
        """Get answer history for a session"""
        
        db = self.get_db_session()
        try:
            # Get diagnostic session
            db_session = db.query(DiagnosticSession).filter(
                DiagnosticSession.session_id == session_id
            ).first()
            
            if not db_session:
                return []
            
            # Get answers
            answers = db.query(DBQuestionAnswer).filter(
                DBQuestionAnswer.diagnostic_session_id == db_session.id
            ).order_by(DBQuestionAnswer.asked_at).all()
            
            # Convert to schema objects with extended fields
            history = []
            for ans in answers:
                qa = QuestionAnswer(
                    question_id=ans.question_id,
                    answer_value=ans.get_answer(),
                    timestamp=ans.asked_at,
                    question_text=ans.question_text,
                    question_type=ans.question_type
                )
                history.append(qa)
            
            return history
            
        finally:
            db.close()
    
    async def should_continue_questioning(
        self,
        session: DiagnosticSession,
        answer_history: List[QuestionAnswer]
    ) -> bool:
        """Determine if we should ask more questions"""
        
        # Check question limit
        if session.questions_asked >= session.max_questions:
            return False
        
        # Check if we have minimum questions for basic diagnosis
        if len(answer_history) < 2:
            return True
        
        # For now, ask up to 5 questions before diagnosing
        if len(answer_history) >= 5:
            return False
        
        return True
    
    async def generate_next_question_response(
        self,
        session: DiagnosticSession,
        answer_history: List[QuestionAnswer]
    ) -> AdaptiveRouterResponse:
        """Generate the next question in the sequence"""
        
        # Analyze confidence gaps
        confidence_gaps = ConfidenceGapAnalysis(
            uncertainty_factors=["symptom_details", "timing", "severity"],
            priority_areas=["symptom_clarification"],
            recommended_question_types=["single_choice", "scale"],
            confidence_threshold=0.7
        )
        
        # Generate next question
        question_response = await self.question_generator.generate_next_question(
            symptoms=session.initial_symptoms,
            answer_history=answer_history,
            confidence_gaps=confidence_gaps,
            patient_profile=session.get_patient_profile(),
            session_context=session.get_context()
        )
        
        return AdaptiveRouterResponse(
            session_id=session.session_id,
            current_question=question_response.question,
            questions_remaining=session.max_questions - len(answer_history) - 1,
            message="Thank you for that information. Let me ask one more question.",
            next_step="continue_diagnostic",
            medical_reasoning=question_response.generation_reasoning
        )
    
    async def check_emergency_escalation(
        self,
        symptoms: str,
        answer_history: List[QuestionAnswer],
        patient_profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if emergency escalation is needed"""
        
        try:
            # Extract patient information
            patient_age = patient_profile.get("age", 35)
            medical_history = patient_profile.get("medical_history", [])
            
            # Convert answer history to dictionary
            answers_dict = {}
            for qa in answer_history:
                # Handle cases where question_text might be None or a fallback value
                question_key = qa.question_text or f"Question {qa.question_id}"
                answers_dict[question_key] = qa.answer_value
            
            # Run triage assessment
            triage_result = await self.triage_service.assess_urgency_level(
                symptoms=symptoms,
                answers=answers_dict,
                patient_profile=patient_profile,
                confidence_score=0.7  # Default confidence for escalation check
            )
            
            # Emergency escalation conditions
            if (triage_result.level.value == "emergency" or 
                len(triage_result.red_flags) > 0 or
                triage_result.confidence_score > 0.9):
                
                logger.warning(f"Emergency escalation triggered: {triage_result.level.value}")
                return {
                    "triage_assessment": triage_result,
                    "escalation_triggered": True,
                    "escalation_reason": f"Triage level: {triage_result.level.value}, Red flags: {len(triage_result.red_flags)}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in emergency escalation check: {e}")
            # Conservative approach - no escalation on error to avoid false alarms
            return None

    async def generate_final_diagnosis(
        self,
        session: DiagnosticSession,
        answer_history: List[QuestionAnswer]
    ) -> AdaptiveRouterResponse:
        """Generate final diagnosis using existing diagnostic system with triage assessment"""
        
        try:
            # Build comprehensive symptom description from answers
            enhanced_symptoms = self.build_enhanced_symptoms(
                session.initial_symptoms, answer_history
            )
            logger.info(f"Enhanced symptoms: {enhanced_symptoms}")
            
            # Check for emergency escalation first
            patient_profile = session.get_patient_profile()
            logger.info(f"Patient profile: {patient_profile}")
            
            emergency_check = await self.check_emergency_escalation(
                session.initial_symptoms, answer_history, patient_profile
            )
            logger.info(f"Emergency check completed: {emergency_check is not None}")
            
            is_emergency = emergency_check and emergency_check.get("escalation_triggered")
            
            # ALWAYS generate predictive diagnosis for ALL triage levels
            diagnosis_obj = None
            routing_decision = None
            diagnosis = None
            
            try:
                answers_dict = {(qa.question_text or f"Question {qa.question_id}"): qa.answer_value for qa in answer_history}
                logger.info(f"Calling generate_predictive_diagnosis with symptoms: {enhanced_symptoms[:100]}...")
                diagnosis = await generate_predictive_diagnosis(enhanced_symptoms, answers_dict)
                # Convert to Pydantic model for downstream services
                diagnosis_obj = PredictiveDiagnosis(**diagnosis)
                logger.info(f"Diagnosis generated successfully: {diagnosis is not None}")
                
                # Get all doctors for routing (you might want to make this configurable)
                doctors = []  # TODO: Get doctors from database if needed for routing
                test_recommendations = []  # TODO: Get test recommendations if needed
                routing_decision = await make_routing_decision(diagnosis, test_recommendations, doctors)
                logger.info(f"Routing decision generated successfully: {routing_decision is not None}")
            except Exception as diag_error:
                logger.error(f"Error in diagnosis generation: {diag_error}")
                # Create fallback diagnosis that works for all triage levels
                diagnosis = {
                    "possible_conditions": ["Medical evaluation recommended based on symptoms"],
                    "confidence_level": "Medium",
                    "urgency_level": ("Emergency" if is_emergency else "Urgent"),
                    "recommended_action": ("Seek immediate medical attention" if is_emergency else "Schedule prompt consultation"),
                    "explanation": f"Based on your symptoms ({enhanced_symptoms[:100]}...), professional medical evaluation is recommended.",
                    "confidence_score": (0.8 if is_emergency else 0.6)
                }
                diagnosis_obj = PredictiveDiagnosis(**diagnosis)
                routing_decision = {"action_type": "emergency_referral" if is_emergency else "book_appointment"}
            
            # Perform triage assessment for all cases
            triage_result = await self.triage_service.assess_urgency_level(
                symptoms=enhanced_symptoms,
                answers={(qa.question_text or f"Question {qa.question_id}"): qa.answer_value for qa in answer_history},
                patient_profile=patient_profile,
                confidence_score=diagnosis.get("confidence_score", 0.7) if diagnosis else 0.7
            )
            
            # Generate consequence messaging for all non-triage-blocked scenarios
            consequence_message = None
            risk_progression = None
            persuasion_metrics = None
            
            # ALWAYS generate consequence messaging for ALL triage levels using the service
            logger.info(f"Generating consequence messaging for session {session.session_id} with triage level: {triage_result.level.value if triage_result else 'unknown'}")
            
            try:
                # Use the consequence messaging service with disease predictions
                consequence_message, risk_progression, persuasion_metrics = await self.consequence_service.generate_consequence_message(
                    diagnosis=diagnosis_obj,
                    confidence_score=None,
                    triage_assessment=triage_result,
                    patient_age=patient_profile.get("age"),
                    symptoms=enhanced_symptoms
                )
                logger.info(f"Created consequence messaging for session {session.session_id} with risk level: {consequence_message.risk_level}")
            
            except Exception as e:
                logger.error(f"Failed to use consequence messaging service, creating fallback: {e}")
                # Fallback consequence messaging creation
                if is_emergency or (triage_result and triage_result.level.value == "emergency"):
                    risk_level = "emergency"
                    primary_msg = f"⚠️ URGENT: Your symptoms may indicate a serious condition requiring immediate medical attention."
                    timeframe = "Within the next 1-2 hours"
                    urgency_score = 0.9
                    fear_appeal = "high"
                elif triage_result and triage_result.level.value == "urgent":
                    risk_level = "urgent"
                    primary_msg = f"🚨 Important: Your symptoms require prompt medical evaluation to prevent complications."
                    timeframe = "Within the next 24-48 hours"
                    urgency_score = 0.7
                    fear_appeal = "medium"
                else:
                    risk_level = "routine"
                    primary_msg = f"💡 Your symptoms should be evaluated by a healthcare professional."
                    timeframe = "Within the next 1-2 weeks"
                    urgency_score = 0.4
                    fear_appeal = "low"
                
                # Create comprehensive consequence messaging
                consequence_message = ConsequenceMessage(
                    risk_level=risk_level,
                    primary_consequence=primary_msg,
                    timeframe=timeframe,
                    escalation_risks=["Symptom progression", "Potential complications", "Delayed treatment impact"],
                    opportunity_cost="Early medical evaluation provides better outcomes",
                    social_proof="Healthcare professionals recommend addressing these symptoms promptly",
                    regret_prevention="Patients often feel relief after getting proper medical evaluation",
                    action_benefits="Medical evaluation can provide clarity and appropriate treatment"
                )
                risk_progression = RiskProgression(
                    immediate_risk="Continued symptoms without medical evaluation",
                    short_term_risk="Potential worsening without proper assessment",
                    long_term_risk="Untreated conditions may develop complications",
                    prevention_window=timeframe
                )
                persuasion_metrics = PersuasionMetrics(
                    urgency_score=urgency_score,
                    fear_appeal_strength=fear_appeal,
                    message_type="medical_guidance",
                    expected_conversion=0.6
                )
            
            # Convert to adaptive response - ensure consequence messaging is always included
            logger.info(f"Creating response with consequence_message: {consequence_message is not None}")
            logger.info(f"Creating response with risk_progression: {risk_progression is not None}")
            logger.info(f"Creating response with persuasion_metrics: {persuasion_metrics is not None}")
            
            response_data = {
                "session_id": session.session_id,
                "questions_remaining": 0,
                "diagnosis": diagnosis_obj.dict() if diagnosis_obj else None,
                "decision": routing_decision if isinstance(routing_decision, dict) else (routing_decision.__dict__ if routing_decision else None),
                "message": ("URGENT: Based on your symptoms, you should seek immediate medical attention." if is_emergency else "Based on your symptoms and answers, here's my assessment:"),
                "next_step": ("emergency_referral" if is_emergency else "provide_diagnosis"),
                "medical_reasoning": "Comprehensive analysis completed using adaptive questioning",
                "triage_assessment": triage_result.__dict__ if triage_result else None,
                "consequence_message": consequence_message.dict() if consequence_message else None,
                "risk_progression": risk_progression.dict() if risk_progression else None,
                "persuasion_metrics": persuasion_metrics.dict() if persuasion_metrics else None
            }
            
            logger.info(f"Response data consequence_message: {response_data.get('consequence_message')}")
            
            return AdaptiveRouterResponse(**response_data)
            
        except Exception as e:
            import traceback
            logger.error(f"Error generating final diagnosis: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return AdaptiveRouterResponse(
                session_id=session.session_id,
                questions_remaining=0,
                message="I've gathered enough information to provide recommendations.",
                next_step="provide_diagnosis"
            )
    
    def build_enhanced_symptoms(
        self,
        initial_symptoms: str,
        answer_history: List[QuestionAnswer]
    ) -> str:
        """Build enhanced symptom description from answers"""
        
        enhanced = [f"Initial symptoms: {initial_symptoms}"]
        
        for qa in answer_history:
            # Convert answer_value to string if it's not already
            answer_str = str(qa.answer_value) if qa.answer_value is not None else ""
            if answer_str.strip():
                question_text = qa.question_text or f"Question {qa.question_id}"
                enhanced.append(f"{question_text}: {answer_str}")
        
        return " | ".join(enhanced)
    
    async def complete_session(self, session_id: str) -> None:
        """Mark diagnostic session as completed"""
        
        db = self.get_db_session()
        try:
            session = db.query(DiagnosticSession).filter(
                DiagnosticSession.session_id == session_id
            ).first()
            
            if session:
                session.status = "completed"
                session.updated_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error completing session: {e}")
        finally:
            db.close() 