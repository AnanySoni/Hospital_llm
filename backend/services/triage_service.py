"""
Triage Service for Phase 1 Month 3 - Risk Stratification & Triage
Handles urgency assessment, red flag detection, and emergency escalation
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from backend.schemas.triage_models import (
    TriageLevel, 
    TriageAssessment, 
    RiskFactor, 
    RedFlag,
    AGE_RISK_MULTIPLIERS,
    RED_FLAG_PATTERNS
)
from backend.utils.llm_utils import call_groq_api, robust_json_parse
from backend.utils.confidence_utils import calculate_confidence_level

logger = logging.getLogger(__name__)


class TriageService:
    def get_triage_records(self, patient_id=None, hospital_id=None, is_super_admin=False):
        """Get triage records for a hospital, or all if superadmin"""
        from backend.core.database import get_db
        from backend.core.models import TriageRecord
        db = next(get_db())
        try:
            query = db.query(TriageRecord)
            if not is_super_admin and hospital_id is not None:
                query = query.filter(TriageRecord.hospital_id == hospital_id)
            if patient_id:
                query = query.filter(TriageRecord.patient_id == patient_id)
            return query.all()
        finally:
            db.close()
    """Medical triage service for urgency assessment and emergency detection"""
    
    def __init__(self):
        self.red_flag_patterns = RED_FLAG_PATTERNS
        self.age_risk_multipliers = AGE_RISK_MULTIPLIERS
    
    async def assess_urgency_level(
        self,
        symptoms: str,
        answers: Dict[str, Any],
        patient_profile: Dict[str, Any],
        confidence_score: float
    ) -> TriageAssessment:
        """
        Comprehensive urgency assessment combining rule-based and LLM analysis
        """
        
        try:
            # Extract patient information
            patient_age = patient_profile.get("age", 35)  # Default middle age
            medical_history = patient_profile.get("medical_history", [])
            
            # Step 1: Check for immediate red flags
            red_flags = await self.detect_red_flags(symptoms, answers)
            
            # Step 2: Calculate age-based risk factors
            age_risk_factors = self.calculate_age_risk_factors(symptoms, patient_age)
            
            # Step 3: LLM-based urgency assessment
            llm_assessment = await self.llm_urgency_assessment(
                symptoms, patient_age, medical_history, answers, confidence_score
            )
            
            # Step 4: Combine assessments to determine final triage level
            final_assessment = await self.combine_triage_assessments(
                red_flags, age_risk_factors, llm_assessment, confidence_score
            )
            
            logger.info(f"Triage assessment completed: {final_assessment.level.value}")
            return final_assessment
            
        except Exception as e:
            logger.error(f"Error in urgency assessment: {e}")
            # Fallback to conservative assessment
            return self.create_fallback_assessment(symptoms, confidence_score)
    
    async def detect_red_flags(
        self, 
        symptoms: str, 
        answers: Dict[str, Any]
    ) -> List[RedFlag]:
        """Detect critical red flag symptoms requiring immediate attention"""
        
        detected_flags = []
        symptoms_lower = symptoms.lower()
        
        # Check each category of red flags
        for category, patterns in self.red_flag_patterns.items():
            for pattern in patterns:
                if self.symptom_matches_pattern(symptoms_lower, pattern):
                    red_flag = RedFlag(
                        symptom=pattern,
                        category=category,
                        urgency_level=TriageLevel.EMERGENCY if category in ["cardiovascular", "neurological"] else TriageLevel.URGENT,
                        reasoning=f"Pattern '{pattern}' detected in {category} category"
                    )
                    detected_flags.append(red_flag)
        
        # Check answers for additional red flags
        for question, answer in answers.items():
            if isinstance(answer, str):
                answer_lower = answer.lower()
                if any(danger_word in answer_lower for danger_word in 
                      ["severe", "crushing", "sudden", "unable to", "difficulty breathing"]):
                    
                    red_flag = RedFlag(
                        symptom=f"Severe symptom reported: {answer}",
                        category="patient_response",
                        urgency_level=TriageLevel.URGENT,
                        reasoning="Patient reported severe or concerning symptoms in questionnaire"
                    )
                    detected_flags.append(red_flag)
        
        return detected_flags
    
    def symptom_matches_pattern(self, symptoms: str, pattern: str) -> bool:
        """Check if symptoms match a red flag pattern"""
        
        # Simple keyword matching - could be enhanced with NLP
        pattern_words = pattern.lower().split()
        
        # Check if most pattern words are present
        matches = sum(1 for word in pattern_words if word in symptoms)
        return matches >= len(pattern_words) * 0.6  # 60% of words must match
    
    def calculate_age_risk_factors(self, symptoms: str, age: int) -> List[RiskFactor]:
        """Calculate age-based risk factors for different symptom categories"""
        
        age_risks = []
        
        # Determine symptom categories
        symptom_categories = self.categorize_symptoms(symptoms)
        
        for category in symptom_categories:
            if category in self.age_risk_multipliers:
                risk_multiplier = self.get_age_risk_multiplier(age, category)
                
                if risk_multiplier > 0.7:  # Significant risk
                    severity = min(risk_multiplier, 1.0)  # Cap at 1.0
                    
                    age_risk = RiskFactor(
                        factor_type="age",
                        severity=severity,
                        description=f"Age {age} increases risk for {category.replace('_', ' ')}",
                        weight=1.0
                    )
                    age_risks.append(age_risk)
        
        return age_risks
    
    def categorize_symptoms(self, symptoms: str) -> List[str]:
        """Categorize symptoms into medical categories for risk assessment"""
        
        symptoms_lower = symptoms.lower()
        categories = []
        
        # Cardiovascular indicators
        if any(word in symptoms_lower for word in ["chest", "heart", "pressure", "crushing"]):
            categories.append("chest_pain")
        
        # Neurological indicators  
        if any(word in symptoms_lower for word in ["headache", "head", "dizzy", "confusion"]):
            categories.append("headache")
        
        # Gastrointestinal indicators
        if any(word in symptoms_lower for word in ["stomach", "abdominal", "belly", "nausea"]):
            categories.append("abdominal_pain")
        
        # Respiratory indicators
        if any(word in symptoms_lower for word in ["breathing", "breath", "cough", "lung"]):
            categories.append("breathing_difficulty")
        
        return categories if categories else ["general"]
    
    def get_age_risk_multiplier(self, age: int, category: str) -> float:
        """Get age-based risk multiplier for a symptom category"""
        
        if category not in self.age_risk_multipliers:
            return 0.5  # Default moderate risk
        
        age_ranges = self.age_risk_multipliers[category]
        
        for (min_age, max_age), multiplier in age_ranges.items():
            if min_age <= age < max_age:
                return multiplier
        
        return 0.5  # Default if age not in ranges
    
    async def llm_urgency_assessment(
        self,
        symptoms: str,
        patient_age: int,
        medical_history: List[str],
        answers: Dict[str, Any],
        confidence_score: float
    ) -> Dict[str, Any]:
        """LLM-powered medical urgency assessment"""
        
        system_message = """You are an emergency triage nurse AI with extensive medical training. 
        Assess the urgency level of medical situations based on symptoms, patient factors, and medical knowledge.
        Always err on the side of caution for patient safety."""
        
        prompt = f"""
        MEDICAL TRIAGE ASSESSMENT REQUIRED:
        
        Patient Information:
        - Age: {patient_age} years old
        - Medical History: {medical_history if medical_history else "None reported"}
        
        Current Symptoms: {symptoms}
        
        Diagnostic Q&A Responses: {json.dumps(answers, indent=2)}
        
        Initial Confidence Score: {confidence_score}
        
        Please provide a comprehensive triage assessment in this exact JSON format:
        {{
            "triage_level": "emergency|urgent|soon|routine",
            "confidence_score": 0.85,
            "time_urgency": "Seek care within X hours/days",
            "reasoning": "Detailed medical reasoning for urgency level",
            "risk_factors": [
                {{
                    "factor_type": "medical_history|symptom_severity|age|presentation",
                    "severity": 0.8,
                    "description": "Specific risk factor description"
                }}
            ],
            "recommendations": [
                "Specific care recommendations",
                "Follow-up instructions"
            ],
            "emergency_indicators": [
                "List any emergency warning signs if present"
            ]
        }}
        
        TRIAGE LEVEL GUIDELINES:
        - EMERGENCY: Life-threatening symptoms, severe pain (8-10/10), critical vital signs
        - URGENT: Significant symptoms requiring prompt attention within 24-48 hours
        - SOON: Concerning symptoms that should be evaluated within 1 week
        - ROUTINE: Minor symptoms suitable for routine care in 2+ weeks
        
        Consider these factors:
        1. Symptom severity and progression
        2. Age-related risk factors
        3. Medical history complications
        4. Red flag symptoms
        5. Patient's ability to function normally
        """
        
        try:
            response = await call_groq_api(prompt, system_message)
            assessment_data = robust_json_parse(response)
            
            # Validate the response structure
            required_fields = ["triage_level", "confidence_score", "time_urgency", "reasoning"]
            for field in required_fields:
                if field not in assessment_data:
                    logger.warning(f"Missing field {field} in LLM triage response")
                    assessment_data[field] = self.get_fallback_value(field)
            
            return assessment_data
            
        except Exception as e:
            logger.error(f"Error in LLM urgency assessment: {e}")
            return self.create_fallback_llm_assessment(symptoms, confidence_score)
    
    async def combine_triage_assessments(
        self,
        red_flags: List[RedFlag],
        age_risk_factors: List[RiskFactor],
        llm_assessment: Dict[str, Any],
        confidence_score: float
    ) -> TriageAssessment:
        """Combine rule-based and LLM assessments into final triage decision"""
        
        # Start with LLM assessment
        triage_level_str = llm_assessment.get("triage_level", "routine")
        llm_triage_level = TriageLevel(triage_level_str)
        
        # Escalate if red flags detected
        if red_flags:
            highest_red_flag_level = max([flag.urgency_level for flag in red_flags], 
                                       key=lambda x: self.get_urgency_numeric_value(x))
            
            # Use highest urgency level between LLM and red flags
            if self.get_urgency_numeric_value(highest_red_flag_level) > self.get_urgency_numeric_value(llm_triage_level):
                final_level = highest_red_flag_level
                emergency_override = True
            else:
                final_level = llm_triage_level
                emergency_override = False
        else:
            final_level = llm_triage_level
            emergency_override = False
        
        # Adjust confidence based on agreement between assessments
        final_confidence = llm_assessment.get("confidence_score", confidence_score)
        if red_flags and final_level == TriageLevel.EMERGENCY:
            final_confidence = max(final_confidence, 0.9)  # High confidence for emergency with red flags
        
        # Combine all risk factors
        all_risk_factors = age_risk_factors + [
            RiskFactor(
                factor_type=rf.get("factor_type", "symptom"),
                severity=rf.get("severity", 0.5),
                description=rf.get("description", "LLM identified risk factor"),
                weight=1.0
            )
            for rf in llm_assessment.get("risk_factors", [])
        ]
        
        # Create final assessment
        return TriageAssessment(
            level=final_level,
            confidence_score=final_confidence,
            time_urgency=self.get_time_urgency_for_level(final_level),
            risk_factors=all_risk_factors,
            red_flags=red_flags,
            reasoning=llm_assessment.get("reasoning", "Combined rule-based and AI assessment"),
            emergency_override=emergency_override,
            recommendations=llm_assessment.get("recommendations", [])
        )
    
    def get_urgency_numeric_value(self, level: TriageLevel) -> int:
        """Convert triage level to numeric value for comparison"""
        level_values = {
            TriageLevel.ROUTINE: 1,
            TriageLevel.SOON: 2,
            TriageLevel.URGENT: 3,
            TriageLevel.EMERGENCY: 4
        }
        return level_values.get(level, 1)
    
    def get_time_urgency_for_level(self, level: TriageLevel) -> str:
        """Get human-readable time urgency for triage level"""
        time_urgencies = {
            TriageLevel.EMERGENCY: "Seek immediate emergency care (call 911 or go to ER)",
            TriageLevel.URGENT: "Seek care within 24-48 hours (urgent care or ER)",
            TriageLevel.SOON: "Schedule appointment within 1 week",
            TriageLevel.ROUTINE: "Schedule routine appointment within 2-4 weeks"
        }
        return time_urgencies.get(level, "Consult with healthcare provider")
    
    def create_fallback_assessment(self, symptoms: str, confidence_score: float) -> TriageAssessment:
        """Create conservative fallback assessment when other methods fail"""
        
        # Conservative approach - default to URGENT if any concerning symptoms
        concerning_words = ["severe", "sudden", "intense", "crushing", "difficulty", "unable"]
        is_concerning = any(word in symptoms.lower() for word in concerning_words)
        
        level = TriageLevel.URGENT if is_concerning else TriageLevel.SOON
        
        return TriageAssessment(
            level=level,
            confidence_score=max(confidence_score * 0.7, 0.3),  # Lower confidence for fallback
            time_urgency=self.get_time_urgency_for_level(level),
            risk_factors=[
                RiskFactor(
                    factor_type="system_fallback",
                    severity=0.6,
                    description="Conservative assessment due to system limitation",
                    weight=1.0
                )
            ],
            red_flags=[],
            reasoning="Conservative fallback assessment - recommend medical evaluation",
            emergency_override=False,
            recommendations=["Consult with healthcare provider for proper evaluation"]
        )
    
    def create_fallback_llm_assessment(self, symptoms: str, confidence_score: float) -> Dict[str, Any]:
        """Create fallback LLM assessment when API call fails"""
        
        return {
            "triage_level": "soon",
            "confidence_score": confidence_score * 0.8,
            "time_urgency": "Schedule appointment within 1 week",
            "reasoning": "Fallback assessment - LLM unavailable",
            "risk_factors": [],
            "recommendations": ["Consult healthcare provider"],
            "emergency_indicators": []
        }
    
    def get_fallback_value(self, field: str) -> Any:
        """Get fallback values for missing LLM response fields"""
        
        fallbacks = {
            "triage_level": "soon",
            "confidence_score": 0.6,
            "time_urgency": "Schedule appointment within 1 week",
            "reasoning": "Standard assessment based on available information"
        }
        return fallbacks.get(field, "Not available")
    
    async def quick_emergency_check(self, symptoms: str, age: Optional[int] = None) -> bool:
        """Quick emergency screening for immediate red flags"""
        
        try:
            # Check for immediate emergency indicators
            emergency_keywords = [
                "crushing chest pain", "difficulty breathing", "severe headache",
                "sudden confusion", "vomiting blood", "severe bleeding",
                "cannot speak", "blue lips", "unconscious"
            ]
            
            symptoms_lower = symptoms.lower()
            
            # Direct keyword matching for speed
            for keyword in emergency_keywords:
                if keyword in symptoms_lower:
                    logger.warning(f"Emergency keyword detected: {keyword}")
                    return True
            
            # Age-based emergency considerations
            if age is not None:
                if age < 2 and any(word in symptoms_lower for word in ["fever", "breathing", "crying"]):
                    return True  # Infants with fever/breathing issues
                if age > 75 and "chest pain" in symptoms_lower:
                    return True  # Elderly with chest pain
            
            return False
            
        except Exception as e:
            logger.error(f"Error in emergency check: {e}")
            return True  # Err on side of caution 