"""
Consequence Messaging Service for Phase 1 Implementation
Generates persuasive messages to encourage appointment/test booking
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
from schemas.request_models import (
    ConsequenceMessage, RiskProgression, PersuasionMetrics,
    PredictiveDiagnosis, ConfidenceScore
)
from schemas.triage_models import TriageLevel, TriageAssessment
from utils.llm_utils import call_groq_api
from utils.advanced_prompt_builder import build_advanced_consequence_prompt


class ConsequenceMessagingService:
    """Service for generating consequence-based persuasive messaging"""
    
    def __init__(self):
        self.consequence_templates = self._load_consequence_templates()
        self.urgency_thresholds = {
            "emergency": 0.9,
            "urgent": 0.7,
            "routine": 0.0
        }
        # Import the question generator to get possible diseases
        try:
            from utils.adaptive_question_generator import AdaptiveQuestionGenerator
            self.question_generator = AdaptiveQuestionGenerator()
        except ImportError:
            self.question_generator = None
    
    async def generate_consequence_message(
        self,
        diagnosis: PredictiveDiagnosis,
        confidence_score: Optional[ConfidenceScore] = None,
        triage_assessment: Optional[TriageAssessment] = None,
        patient_age: Optional[int] = None,
        symptoms: str = ""
    ) -> tuple[ConsequenceMessage, RiskProgression, PersuasionMetrics]:
        """
        Generate comprehensive consequence messaging with specific disease predictions
        
        Returns:
            Tuple of (ConsequenceMessage, RiskProgression, PersuasionMetrics)
        """
        try:
            # Determine risk level and urgency
            risk_level = self._determine_risk_level(diagnosis, triage_assessment)
            urgency_score = self._calculate_urgency_score(diagnosis, confidence_score)
            
            # Get possible diseases for this symptom
            possible_diseases = self._get_possible_diseases(symptoms)
            
            # Generate consequence message via LLM with disease context
            consequence_data = await self._generate_llm_consequence(
                diagnosis, risk_level, urgency_score, patient_age, symptoms, possible_diseases
            )
            
            # Create structured response objects
            consequence_message = ConsequenceMessage(**consequence_data["consequence_message"])
            risk_progression = RiskProgression(**consequence_data["risk_progression"])
            persuasion_metrics = PersuasionMetrics(**consequence_data["persuasion_metrics"])
            
            return consequence_message, risk_progression, persuasion_metrics
            
        except Exception as e:
            # Fallback to template-based messaging
            return await self._generate_fallback_consequence(diagnosis, risk_level, urgency_score, possible_diseases)
    
    def _get_possible_diseases(self, symptoms: str) -> List[str]:
        """Get possible diseases for the given symptoms"""
        if self.question_generator:
            return self.question_generator.get_possible_diseases_for_symptoms(symptoms)
        
        # Fallback disease lists based on keywords
        symptoms_lower = symptoms.lower()
        if any(word in symptoms_lower for word in ["chest", "heart"]):
            return ["Heart Attack", "Angina", "Pulmonary Embolism", "Aortic Dissection"]
        elif any(word in symptoms_lower for word in ["head", "migraine"]):
            return ["Migraine", "Tension Headache", "Cluster Headache", "Brain Aneurysm"]
        elif any(word in symptoms_lower for word in ["stomach", "abdomen", "belly"]):
            return ["Appendicitis", "Gallbladder Disease", "Kidney Stones", "Peptic Ulcer"]
        elif any(word in symptoms_lower for word in ["fever", "temperature"]):
            return ["Pneumonia", "UTI", "Meningitis", "Sepsis"]
        else:
            return ["Various medical conditions"]
    
    async def _generate_llm_consequence(
        self,
        diagnosis: PredictiveDiagnosis,
        risk_level: str,
        urgency_score: float,
        patient_age: Optional[int],
        symptoms: str,
        possible_diseases: List[str]
    ) -> Dict[str, Any]:
        """Generate consequence message using LLM with specific disease context"""
        
        prompt = self._build_enhanced_consequence_prompt(
            diagnosis, risk_level, urgency_score, patient_age, symptoms, possible_diseases
        )
        
        try:
            response = await call_groq_api(prompt)
            
            if response and response.strip():
                consequence_data = json.loads(response.strip())
                return consequence_data
            else:
                raise ValueError("Empty LLM response")
                
        except (json.JSONDecodeError, ValueError, Exception) as e:
            print(f"Error generating LLM consequence: {e}")
            # Return template-based fallback with diseases
            return self._get_template_consequence_with_diseases(diagnosis, risk_level, urgency_score, possible_diseases)
    
    def _build_enhanced_consequence_prompt(
        self,
        diagnosis: PredictiveDiagnosis,
        risk_level: str,
        urgency_score: float,
        patient_age: Optional[int],
        symptoms: str,
        possible_diseases: List[str]
    ) -> str:
        """Build enhanced LLM prompt with specific disease context"""
        
        diseases_text = ", ".join(possible_diseases[:4])  # Limit to top 4 diseases
        
        prompt = f"""
You are a senior emergency physician. Based on the patient's symptoms "{symptoms}", generate persuasive consequence messaging.

MEDICAL CONTEXT:
- Possible conditions: {diseases_text}
- Risk level: {risk_level}
- Urgency score: {urgency_score:.2f}
- Patient age: {patient_age or 'unknown'}

INSTRUCTIONS:
Create realistic, evidence-based consequences that mention specific diseases. Be professional but persuasive.

For {risk_level} level cases:
- Emergency: Mention time-critical conditions like heart attack, stroke, etc.
- Urgent: Focus on conditions that worsen without treatment
- Routine: Emphasize prevention and early detection benefits

Respond ONLY with valid JSON:
{{
    "consequence_message": {{
        "primary_consequence": "Main message mentioning specific conditions (start with appropriate urgency emoji)",
        "risk_level": "{risk_level}",
        "timeframe": "Specific timeframe for action",
        "escalation_risks": ["Specific medical risks", "Disease progression risks"],
        "opportunity_cost": "What patient misses by delaying",
        "social_proof": "Medical professional recommendations",
        "regret_prevention": "Patient relief/outcome message",
        "action_benefits": "Benefits of timely medical evaluation"
    }},
    "risk_progression": {{
        "immediate_risk": "What could happen now",
        "short_term_risk": "Risks within days/weeks",
        "long_term_risk": "Chronic complications",
        "prevention_window": "Critical action timeframe"
    }},
    "persuasion_metrics": {{
        "urgency_score": {urgency_score:.1f},
        "fear_appeal_strength": "{"high" if urgency_score > 0.8 else "medium" if urgency_score > 0.6 else "low"}",
        "message_type": "medical_evidence",
        "expected_conversion": 0.75
    }}
}}
"""
        return prompt
    
    def _determine_risk_level(
        self,
        diagnosis: PredictiveDiagnosis,
        triage_assessment: Optional[TriageAssessment]
    ) -> str:
        """Determine overall risk level"""
        
        if triage_assessment:
            if triage_assessment.level == TriageLevel.EMERGENCY:
                return "emergency"
            elif triage_assessment.level == TriageLevel.URGENT:
                return "urgent"
            else:
                return "routine"
        
        # Fallback based on diagnosis urgency
        urgency = diagnosis.urgency_level.lower()
        if urgency == "emergency":
            return "emergency"
        elif urgency == "urgent":
            return "urgent"
        else:
            return "routine"
    
    def _calculate_urgency_score(
        self,
        diagnosis: PredictiveDiagnosis,
        confidence_score: Optional[ConfidenceScore]
    ) -> float:
        """Calculate numerical urgency score"""
        
        base_urgency = {
            "emergency": 0.95,
            "urgent": 0.75,
            "routine": 0.3
        }.get(diagnosis.urgency_level.lower(), 0.3)
        
        # Adjust based on confidence
        if confidence_score:
            confidence_multiplier = confidence_score.score
            return min(base_urgency * (0.7 + 0.3 * confidence_multiplier), 1.0)
        
        return base_urgency
    
    def _get_template_consequence(
        self,
        diagnosis: PredictiveDiagnosis,
        risk_level: str,
        urgency_score: float
    ) -> Dict[str, Any]:
        """Generate template-based consequence message as fallback"""
        
        templates = self.consequence_templates.get(risk_level, self.consequence_templates["routine"])
        
        return {
            "consequence_message": {
                "primary_consequence": templates["primary_consequence"].format(
                    conditions=', '.join(diagnosis.possible_conditions)
                ),
                "risk_level": risk_level,
                "timeframe": templates["timeframe"],
                "escalation_risks": templates["escalation_risks"],
                "opportunity_cost": templates["opportunity_cost"],
                "social_proof": templates["social_proof"],
                "regret_prevention": templates["regret_prevention"],
                "action_benefits": templates["action_benefits"]
            },
            "risk_progression": templates["risk_progression"],
            "persuasion_metrics": {
                "urgency_score": urgency_score,
                "fear_appeal_strength": "high" if urgency_score > 0.8 else "medium" if urgency_score > 0.6 else "low",
                "message_type": "statistical",
                "expected_conversion": 0.7
            }
        }
    
    def _get_template_consequence_with_diseases(
        self,
        diagnosis: PredictiveDiagnosis,
        risk_level: str,
        urgency_score: float,
        possible_diseases: List[str]
    ) -> Dict[str, Any]:
        """Generate template-based consequence message with specific diseases"""
        
        templates = self.consequence_templates.get(risk_level, self.consequence_templates["routine"])
        diseases_text = ", ".join(possible_diseases[:3])  # Limit to top 3 diseases
        
        # Customize primary consequence based on risk level and diseases
        if risk_level == "emergency":
            primary_msg = f"🚨 URGENT: Your symptoms may indicate serious conditions such as {diseases_text}. Immediate medical attention is critical."
        elif risk_level == "urgent":
            primary_msg = f"⚠️ Important: Your symptoms require prompt evaluation to rule out conditions like {diseases_text}."
        else:
            primary_msg = f"💡 Your symptoms should be evaluated to check for conditions such as {diseases_text}."
        
        return {
            "consequence_message": {
                "primary_consequence": primary_msg,
                "risk_level": risk_level,
                "timeframe": templates["timeframe"],
                "escalation_risks": [f"Progression of {diseases_text}", "Delayed diagnosis complications"],
                "opportunity_cost": templates["opportunity_cost"],
                "social_proof": templates["social_proof"],
                "regret_prevention": templates["regret_prevention"],
                "action_benefits": templates["action_benefits"]
            },
            "risk_progression": templates["risk_progression"],
            "persuasion_metrics": {
                "urgency_score": urgency_score,
                "fear_appeal_strength": "high" if urgency_score > 0.8 else "medium" if urgency_score > 0.6 else "low",
                "message_type": "statistical",
                "expected_conversion": 0.7
            }
        }
    
    async def _generate_fallback_consequence(
        self,
        diagnosis: PredictiveDiagnosis,
        risk_level: str,
        urgency_score: float,
        possible_diseases: List[str]
    ) -> tuple[ConsequenceMessage, RiskProgression, PersuasionMetrics]:
        """Generate fallback consequence messaging with diseases"""
        
        consequence_data = self._get_template_consequence_with_diseases(diagnosis, risk_level, urgency_score, possible_diseases)
        
        consequence_message = ConsequenceMessage(**consequence_data["consequence_message"])
        risk_progression = RiskProgression(**consequence_data["risk_progression"])
        persuasion_metrics = PersuasionMetrics(**consequence_data["persuasion_metrics"])
        
        return consequence_message, risk_progression, persuasion_metrics
    
    def _load_consequence_templates(self) -> Dict[str, Any]:
        """Load consequence message templates"""
        
        return {
            "emergency": {
                "primary_consequence": "⚠️ URGENT: {conditions} can be life-threatening and requires immediate medical attention",
                "timeframe": "Within the next 1-2 hours",
                "escalation_risks": [
                    "Rapid deterioration of condition",
                    "Permanent organ damage",
                    "Life-threatening complications"
                ],
                "opportunity_cost": "Emergency intervention is most effective when started immediately",
                "social_proof": "Emergency medicine specialists emphasize that every minute counts for these symptoms",
                "regret_prevention": "Patients often say 'I wish I hadn't waited' when dealing with these symptoms",
                "action_benefits": "Immediate care can prevent serious complications and save your life",
                "risk_progression": {
                    "immediate_risk": "Life-threatening complications within hours",
                    "short_term_risk": "Permanent damage or death",
                    "long_term_risk": "Not applicable - immediate action required",
                    "prevention_window": "Next 1-2 hours are critical"
                }
            },
            "urgent": {
                "primary_consequence": "🚨 Important: {conditions} can lead to serious complications if not treated promptly",
                "timeframe": "Within the next 24-48 hours",
                "escalation_risks": [
                    "Worsening of symptoms",
                    "Development of complications",
                    "Reduced treatment effectiveness"
                ],
                "opportunity_cost": "Early treatment has 85% higher success rates than delayed treatment",
                "social_proof": "Medical studies show patients who seek care within 48 hours have significantly better outcomes",
                "regret_prevention": "Most patients with similar symptoms wish they had acted sooner",
                "action_benefits": "Prompt treatment can prevent complications and speed recovery",
                "risk_progression": {
                    "immediate_risk": "Symptom progression likely within 24-48 hours",
                    "short_term_risk": "Complications and prolonged recovery within 1-2 weeks",
                    "long_term_risk": "Chronic issues and reduced quality of life",
                    "prevention_window": "Next 48 hours offer best treatment outcomes"
                }
            },
            "routine": {
                "primary_consequence": "💡 Good news: {conditions} are typically very treatable when addressed early",
                "timeframe": "Within the next 1-2 weeks",
                "escalation_risks": [
                    "Gradual worsening of symptoms",
                    "Impact on daily activities",
                    "Reduced quality of life"
                ],
                "opportunity_cost": "Early intervention prevents symptoms from becoming chronic",
                "social_proof": "Healthcare providers recommend addressing these symptoms before they interfere with daily life",
                "regret_prevention": "Patients often feel relief after addressing these concerns early",
                "action_benefits": "Early treatment typically leads to faster, more complete recovery",
                "risk_progression": {
                    "immediate_risk": "Continued mild discomfort",
                    "short_term_risk": "Gradual worsening affecting daily activities",
                    "long_term_risk": "Potential chronic condition requiring more intensive treatment",
                    "prevention_window": "Next 1-2 weeks ideal for early intervention"
                }
            }
        } 