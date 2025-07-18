from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from core.models import Doctor, Department
from schemas.triage_models import TriageLevel, TriageAssessment, TriageResponse
from utils.llm_utils import call_groq_api
import logging
import json

logger = logging.getLogger(__name__)

class SmartRoutingService:
    def __init__(self, db: Session):
        self.db = db
        self.urgency_specializations = self._load_urgency_specializations()
        self.availability_filters = self._load_availability_filters()

    def _load_urgency_specializations(self) -> Dict[str, List[str]]:
        """Load specialization requirements based on urgency level"""
        return {
            TriageLevel.EMERGENCY: [
                "Emergency Medicine", "Cardiology", "Neurology", 
                "Critical Care", "Trauma Surgery", "Internal Medicine"
            ],
            TriageLevel.URGENT: [
                "Internal Medicine", "Family Medicine", "Cardiology",
                "Pulmonology", "Gastroenterology", "Emergency Medicine",
                "Neurology", "Orthopedics"
            ],
            TriageLevel.SOON: [
                "Family Medicine", "Internal Medicine", "Dermatology",
                "Psychiatry", "Endocrinology", "Rheumatology",
                "Ophthalmology", "ENT"
            ],
            TriageLevel.ROUTINE: [
                "Family Medicine", "Dermatology", "Psychiatry",
                "Preventive Medicine", "Ophthalmology", "ENT",
                "Orthopedics", "Gynecology"
            ]
        }

    def _load_availability_filters(self) -> Dict[str, Dict]:
        """Load availability filtering criteria based on urgency"""
        return {
            TriageLevel.EMERGENCY: {
                "max_hours_ahead": 24,
                "require_emergency_available": True,
                "minimum_doctors": 3
            },
            TriageLevel.URGENT: {
                "max_hours_ahead": 72,
                "require_urgent_slots": True,
                "minimum_doctors": 3
            },
            TriageLevel.SOON: {
                "max_days_ahead": 14,
                "require_available_soon": True,
                "minimum_doctors": 2
            },
            TriageLevel.ROUTINE: {
                "max_days_ahead": 30,
                "require_available": False,
                "minimum_doctors": 1
            }
        }

    async def route_patient_to_doctors(
        self, 
        triage_assessment: TriageAssessment,
        symptoms: str,
        patient_age: Optional[int] = None,
        patient_preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """Route patient to appropriate doctors based on triage assessment"""
        try:
            logger.info(f"Routing patient with {triage_assessment.triage_level.value} urgency")
            
            # Step 1: Get all doctors
            all_doctors = self.db.query(Doctor).all()
            
            # Step 2: Filter by urgency-appropriate specializations
            urgency_filtered_doctors = self._filter_by_urgency_specialization(
                all_doctors, triage_assessment.triage_level
            )
            
            # Step 3: Get LLM-based symptom matching
            symptom_matched_doctors = await self._get_symptom_matched_doctors(
                urgency_filtered_doctors, symptoms, triage_assessment
            )
            
            # Step 4: Apply availability filtering
            available_doctors = await self._apply_availability_filtering(
                symptom_matched_doctors, triage_assessment.triage_level
            )
            
            # Step 5: Score and rank doctors
            scored_doctors = self._score_and_rank_doctors(
                available_doctors, triage_assessment, patient_age
            )
            
            # Step 6: Apply emergency escalation if needed
            if triage_assessment.escalation_required:
                scored_doctors = self._apply_emergency_escalation(scored_doctors)
            
            logger.info(f"Routed to {len(scored_doctors)} doctors for {triage_assessment.triage_level.value} case")
            return scored_doctors
            
        except Exception as e:
            logger.error(f"Error in smart routing: {e}")
            # Fallback to basic doctor list
            return self._get_fallback_doctors(all_doctors, triage_assessment.triage_level)

    def _filter_by_urgency_specialization(
        self, 
        doctors: List[Doctor], 
        urgency_level: TriageLevel
    ) -> List[Doctor]:
        """Filter doctors by urgency-appropriate specializations"""
        required_specializations = self.urgency_specializations.get(urgency_level, [])
        
        filtered_doctors = []
        for doctor in doctors:
            doctor_dept = doctor.department.name if doctor.department else ""
            doctor_subdiv = doctor.subdivision.name if doctor.subdivision else ""
            
            # Check if doctor's specialization matches urgency requirements
            for spec in required_specializations:
                if (spec.lower() in doctor_dept.lower() or 
                    spec.lower() in doctor_subdiv.lower() or
                    any(spec.lower() in tag.lower() for tag in (doctor.tags or []))):
                    filtered_doctors.append(doctor)
                    break
        
        # If no specific matches, include general/family medicine doctors
        if not filtered_doctors:
            for doctor in doctors:
                doctor_dept = doctor.department.name if doctor.department else ""
                if any(general in doctor_dept.lower() for general in ["general", "family", "internal"]):
                    filtered_doctors.append(doctor)
        
        return filtered_doctors

    async def _get_symptom_matched_doctors(
        self, 
        doctors: List[Doctor], 
        symptoms: str,
        triage_assessment: TriageAssessment
    ) -> List[Dict]:
        """Use LLM to match symptoms with doctor specializations"""
        try:
            # Convert doctors to format for LLM
            doctor_list = []
            for doctor in doctors:
                doctor_dict = {
                    "id": doctor.id,
                    "name": doctor.name,
                    "department": doctor.department.name if doctor.department else "",
                    "subdivision": doctor.subdivision.name if doctor.subdivision else "",
                    "tags": doctor.tags if doctor.tags else []
                }
                doctor_list.append(doctor_dict)
            
            # Create urgency-aware prompt
            urgency_context = f"""
            URGENCY LEVEL: {triage_assessment.triage_level.value.upper()}
            URGENCY SCORE: {triage_assessment.urgency_score}/100
            TIMEFRAME: {triage_assessment.timeframe}
            RED FLAGS: {', '.join([flag.symptom for flag in triage_assessment.red_flags_detected])}
            """
            
            prompt = f"""
            You are a medical routing AI. Match the patient's symptoms with the most appropriate doctors based on urgency level and specialization.
            
            {urgency_context}
            
            PATIENT SYMPTOMS: {symptoms}
            
            AVAILABLE DOCTORS: {json.dumps(doctor_list, indent=2)}
            
            Based on the urgency level and symptoms, recommend the TOP 3-5 most appropriate doctors.
            For {triage_assessment.triage_level.value} cases, prioritize:
            - Immediate availability for emergency cases
            - Appropriate specialization for symptoms
            - Experience with urgent conditions
            
            Respond with a JSON array of doctor recommendations with enhanced reasoning:
            [
                {{
                    "id": doctor_id,
                    "name": "Doctor Name",
                    "specialization": "Department/Specialty",
                    "reason": "Why this doctor is appropriate for these symptoms and urgency level",
                    "experience": "Relevant experience description",
                    "expertise": ["relevant", "specialties"],
                    "urgency_match": "How well this doctor matches the urgency level",
                    "symptom_relevance": "How relevant their specialty is to the symptoms"
                }}
            ]
            """
            
            response = await call_groq_api(prompt, max_tokens=1000)
            
            try:
                matched_doctors = json.loads(response)
                return matched_doctors
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response for doctor matching")
                return self._create_basic_doctor_list(doctors)
                
        except Exception as e:
            logger.error(f"Error in symptom matching: {e}")
            return self._create_basic_doctor_list(doctors)

    async def _apply_availability_filtering(
        self, 
        doctors: List[Dict],
        urgency_level: TriageLevel
    ) -> List[Dict]:
        """Apply availability-based filtering based on urgency"""
        availability_criteria = self.availability_filters.get(urgency_level, {})
        
        # For now, return all doctors but mark them with availability info
        # In a full implementation, this would check actual doctor schedules
        for doctor in doctors:
            if urgency_level == TriageLevel.EMERGENCY:
                doctor["availability_status"] = "Emergency slots available"
                doctor["next_available"] = "Within 2 hours"
            elif urgency_level == TriageLevel.URGENT:
                doctor["availability_status"] = "Urgent care slots available"
                doctor["next_available"] = "Within 24-48 hours"
            elif urgency_level == TriageLevel.SOON:
                doctor["availability_status"] = "Regular slots available"
                doctor["next_available"] = "Within 1 week"
            else:
                doctor["availability_status"] = "Routine scheduling"
                doctor["next_available"] = "Within 2-4 weeks"
        
        return doctors

    def _score_and_rank_doctors(
        self, 
        doctors: List[Dict],
        triage_assessment: TriageAssessment,
        patient_age: Optional[int] = None
    ) -> List[Dict]:
        """Score and rank doctors based on multiple factors"""
        for doctor in doctors:
            score = 0
            
            # Base score for appropriate specialty
            score += 50
            
            # Urgency level bonus
            urgency_bonuses = {
                TriageLevel.EMERGENCY: 40,
                TriageLevel.URGENT: 30,
                TriageLevel.SOON: 20,
                TriageLevel.ROUTINE: 10
            }
            score += urgency_bonuses.get(triage_assessment.triage_level, 10)
            
            # Red flag symptoms bonus for appropriate specialists
            if triage_assessment.red_flags_detected:
                for flag in triage_assessment.red_flags_detected:
                    if any(keyword in flag.symptom.lower() for keyword in 
                           ["cardiac", "heart", "chest"] if "cardiology" in doctor.get("specialization", "").lower()):
                        score += 25
                    elif any(keyword in flag.symptom.lower() for keyword in 
                             ["stroke", "neurological"] if "neurology" in doctor.get("specialization", "").lower()):
                        score += 25
            
            # Age-appropriate bonus
            if patient_age is not None:
                if patient_age <= 18 and "pediatric" in doctor.get("specialization", "").lower():
                    score += 20
                elif patient_age >= 65 and "geriatric" in doctor.get("specialization", "").lower():
                    score += 20
            
            # Risk factor bonuses
            for risk_factor in triage_assessment.risk_factors:
                if risk_factor.factor_type == "chronic_heart" and "cardiology" in doctor.get("specialization", "").lower():
                    score += 15
                elif risk_factor.factor_type == "chronic_diabetes" and "endocrin" in doctor.get("specialization", "").lower():
                    score += 15
            
            doctor["routing_score"] = score
            doctor["priority_level"] = self._get_priority_level(score)
        
        # Sort by score (highest first)
        doctors.sort(key=lambda x: x.get("routing_score", 0), reverse=True)
        
        return doctors

    def _apply_emergency_escalation(self, doctors: List[Dict]) -> List[Dict]:
        """Apply emergency escalation modifications to doctor list"""
        # Add emergency contact information to top doctors
        for i, doctor in enumerate(doctors[:3]):
            doctor["emergency_priority"] = True
            doctor["escalation_note"] = "IMMEDIATE ATTENTION REQUIRED - Emergency case"
            doctor["contact_priority"] = "Call immediately upon booking"
            
            if i == 0:  # Top doctor
                doctor["emergency_contact"] = "Primary emergency recommendation"
        
        return doctors

    def _get_priority_level(self, score: int) -> str:
        """Convert numerical score to priority level"""
        if score >= 90:
            return "CRITICAL"
        elif score >= 70:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        else:
            return "LOW"

    def _create_basic_doctor_list(self, doctors: List[Doctor]) -> List[Dict]:
        """Create basic doctor list as fallback"""
        return [
            {
                "id": doctor.id,
                "name": doctor.name,
                "specialization": doctor.department.name if doctor.department else "General Medicine",
                "reason": f"Available for medical consultation",
                "experience": "Medical professional",
                "expertise": doctor.tags if doctor.tags else ["General Medicine"],
                "routing_score": 50,
                "priority_level": "MEDIUM"
            }
            for doctor in doctors[:5]
        ]

    def _get_fallback_doctors(self, doctors: List[Doctor], urgency_level: TriageLevel) -> List[Dict]:
        """Get fallback doctors in case of routing failure"""
        fallback_doctors = self._create_basic_doctor_list(doctors)
        
        # Add urgency-appropriate messaging
        urgency_message = {
            TriageLevel.EMERGENCY: "EMERGENCY - Seek immediate medical attention",
            TriageLevel.URGENT: "URGENT - Schedule within 24-48 hours",
            TriageLevel.SOON: "Schedule appointment within 1 week",
            TriageLevel.ROUTINE: "Schedule routine appointment"
        }
        
        for doctor in fallback_doctors:
            doctor["urgency_message"] = urgency_message.get(urgency_level, "Medical consultation recommended")
        
        return fallback_doctors

    async def get_emergency_routing_options(self, symptoms: str) -> Dict:
        """Get emergency routing options for critical cases"""
        return {
            "immediate_actions": [
                "Call 911 for life-threatening emergencies",
                "Go to nearest emergency room",
                "Contact emergency services"
            ],
            "emergency_contacts": {
                "general": "911 - Emergency Services",
                "poison": "1-800-222-1222 - Poison Control",
                "mental_health": "988 - Suicide & Crisis Lifeline"
            },
            "nearest_hospitals": [
                "Contact your local emergency services for nearest hospital information"
            ],
            "urgent_care_options": [
                "Emergency Department - for life-threatening conditions",
                "Urgent Care Centers - for serious but non-life-threatening conditions"
            ]
        } 