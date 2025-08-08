"""
Adaptive Question Generator for Phase 1 Month 2
Generates context-aware diagnostic questions using LLM and medical decision trees
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.schemas.question_models import (
    DiagnosticQuestion, 
    QuestionAnswer, 
    ConfidenceGapAnalysis,
    QuestionGenerationRequest,
    QuestionGenerationResponse
)
from backend.utils.llm_utils import call_groq_api

logger = logging.getLogger(__name__)

class AdaptiveQuestionGenerator:
    def __init__(self):
        self.medical_decision_trees = self.load_decision_trees()
        self.question_templates = self.load_question_templates()
        self.question_counter = 1000  # Start from 1000 for question IDs
    
    def load_decision_trees(self) -> Dict[str, Any]:
        """Load medical decision trees with structured question sets"""
        return {
            "chest_pain": {
                "structured_questions": [
                    # Question 1: Location (single choice)
                    {
                        "question": "Where is the chest pain located?",
                        "type": "single_choice",
                        "options": ["Left side", "Right side", "Center of the chest", "Radiates to the back", "Radiates to the arm(s)", "Diffuse"],
                        "medical_significance": "Location helps differentiate cardiac vs non-cardiac causes"
                    },
                    # Question 2: Duration (single choice)
                    {
                        "question": "How long have you been experiencing the chest pain?",
                        "type": "text",
                        "medical_significance": "Duration indicates acute vs chronic conditions"
                    },
                    # Question 3: Quality (multiple choice)
                    {
                        "question": "How would you describe the chest pain you're experiencing?",
                        "type": "multiple_choice",
                        "options": ["Sharp", "Dull", "Aching", "Burning", "Squeezing", "Other (please specify)"],
                        "medical_significance": "Quality of pain indicates potential causes"
                    },
                    # Question 4: Intensity (scale)
                    {
                        "question": "How would you describe the intensity of your chest pain?",
                        "type": "scale",
                        "medical_significance": "Intensity helps determine urgency"
                    },
                    # Question 5: Medical history (open ended - last question)
                    {
                        "question": "Do you have any relevant medical history? (e.g., smoking, diabetes, heart disease, high blood pressure, previous heart issues)",
                        "type": "text",
                        "medical_significance": "Medical history crucial for cardiac risk assessment"
                    }
                ],
                "red_flags": ["crushing pain", "radiating to arm", "sweating", "nausea"],
                "possible_diseases": [
                    "Acute Myocardial Infarction (Heart Attack)",
                    "Angina Pectoris",
                    "Pulmonary Embolism", 
                    "Aortic Dissection",
                    "Gastroesophageal Reflux Disease (GERD)",
                    "Costochondritis",
                    "Pneumothorax"
                ]
            },
            "headache": {
                "structured_questions": [
                    # Question 1: Type (single choice)
                    {
                        "question": "What type of headache best describes your pain?",
                        "type": "single_choice",
                        "options": ["Throbbing/pulsating", "Tight band around head", "Sharp/stabbing", "Dull pressure", "Behind the eyes"],
                        "medical_significance": "Type helps differentiate between migraine, tension, cluster headaches"
                    },
                    # Question 2: Location (single choice)
                    {
                        "question": "Where is your headache located?",
                        "type": "single_choice", 
                        "options": ["One side of head", "Both sides", "Forehead", "Back of head", "Top of head", "Around eyes"],
                        "medical_significance": "Location patterns suggest different headache types"
                    },
                    # Question 3: Severity (scale)
                    {
                        "question": "How severe is your headache on a scale of 1-10?",
                        "type": "scale",
                        "medical_significance": "Severity helps determine urgency and treatment approach"
                    },
                    # Question 4: Associated symptoms (multiple choice)
                    {
                        "question": "Do you have any of these symptoms along with your headache?",
                        "type": "multiple_choice",
                        "options": ["Nausea/vomiting", "Sensitivity to light", "Sensitivity to sound", "Blurred vision", "Neck stiffness", "Fever", "None of these"],
                        "medical_significance": "Associated symptoms help identify serious causes and headache type"
                    },
                    # Question 5: Medical history (open ended - last question)
                    {
                        "question": "Do you have any relevant medical history for headaches? (e.g., previous migraines, high blood pressure, head injury, medication use, stress levels)",
                        "type": "text",
                        "medical_significance": "History crucial for headache diagnosis and ruling out secondary causes"
                    }
                ],
                "red_flags": ["sudden onset", "worst headache ever", "fever", "neck stiffness"],
                "possible_diseases": [
                    "Migraine with Aura",
                    "Tension-Type Headache",
                    "Cluster Headache",
                    "Meningitis", 
                    "Subarachnoid Hemorrhage",
                    "Brain Tumor",
                    "Hypertensive Crisis",
                    "Medication Overuse Headache"
                ]
            },
            "abdominal_pain": {
                "structured_questions": [
                    # Question 1: Location (single choice)
                    {
                        "question": "Where exactly is your abdominal pain located?",
                        "type": "single_choice",
                        "options": ["Upper right", "Upper left", "Upper center", "Lower right", "Lower left", "Lower center", "All over abdomen"],
                        "medical_significance": "Location helps identify specific organs involved"
                    },
                    # Question 2: Nature (single choice)
                    {
                        "question": "How would you describe the abdominal pain?",
                        "type": "single_choice",
                        "options": ["Sharp/stabbing", "Cramping", "Dull ache", "Burning", "Colicky (comes and goes)"],
                        "medical_significance": "Pain quality suggests different underlying conditions"
                    },
                    # Question 3: Severity (scale)
                    {
                        "question": "How severe is your abdominal pain on a scale of 1-10?",
                        "type": "scale", 
                        "medical_significance": "Severity indicates urgency and potential for serious conditions"
                    },
                    # Question 4: Associated symptoms (multiple choice)
                    {
                        "question": "Are you experiencing any of these symptoms with your abdominal pain?",
                        "type": "multiple_choice",
                        "options": ["Nausea/vomiting", "Diarrhea", "Constipation", "Fever", "Bloating", "Loss of appetite", "Blood in stool", "None of these"],
                        "medical_significance": "Associated symptoms help narrow down specific conditions"
                    },
                    # Question 5: Medical history (open ended - last question)
                    {
                        "question": "Do you have any relevant medical history? (e.g., previous surgeries, gallbladder issues, kidney stones, digestive problems, medications)",
                        "type": "text",
                        "medical_significance": "Medical history essential for abdominal pain diagnosis"
                    }
                ],
                "red_flags": ["severe pain", "rigid abdomen", "blood in vomit", "high fever"],
                "possible_diseases": [
                    "Appendicitis",
                    "Cholecystitis (Gallbladder Inflammation)", 
                    "Kidney Stones",
                    "Gastroenteritis",
                    "Peptic Ulcer Disease",
                    "Inflammatory Bowel Disease",
                    "Bowel Obstruction",
                    "Pancreatitis"
                ]
            },
            "fever": {
                "structured_questions": [
                    # Question 1: Temperature (single choice)
                    {
                        "question": "What is your current temperature (if you've measured it)?",
                        "type": "single_choice",
                        "options": ["Below 100°F (37.8°C)", "100-101°F (37.8-38.3°C)", "101-102°F (38.3-38.9°C)", "102-103°F (38.9-39.4°C)", "Above 103°F (39.4°C)", "Haven't measured"],
                        "medical_significance": "Temperature level indicates severity and urgency"
                    },
                    # Question 2: Duration (single choice)
                    {
                        "question": "How long have you had the fever?",
                        "type": "single_choice",
                        "options": ["Less than 24 hours", "1-2 days", "3-5 days", "More than a week"],
                        "medical_significance": "Duration helps differentiate viral vs bacterial infections"
                    },
                    # Question 3: Pattern (single choice)
                    {
                        "question": "How would you describe your fever pattern?",
                        "type": "single_choice",
                        "options": ["Constant high fever", "Comes and goes", "Gradually increasing", "High at night, lower during day"],
                        "medical_significance": "Fever patterns can suggest specific infections"
                    },
                    # Question 4: Associated symptoms (multiple choice)
                    {
                        "question": "What other symptoms are you experiencing with the fever?",
                        "type": "multiple_choice",
                        "options": ["Chills/shivering", "Sweating", "Headache", "Body aches", "Sore throat", "Cough", "Difficulty breathing", "Nausea", "Rash", "None of these"],
                        "medical_significance": "Associated symptoms help identify infection source"
                    },
                    # Question 5: Medical history (open ended - last question)
                    {
                        "question": "Do you have any relevant medical history? (e.g., recent travel, sick contacts, chronic conditions, immunocompromised status, recent surgeries)",
                        "type": "text",
                        "medical_significance": "Risk factors crucial for identifying serious infections"
                    }
                ],
                "red_flags": ["high fever", "difficulty breathing", "severe headache", "neck stiffness"],
                "possible_diseases": [
                    "Viral Upper Respiratory Infection",
                    "Bacterial Pneumonia",
                    "Urinary Tract Infection",
                    "Influenza",
                    "COVID-19",
                    "Meningitis",
                    "Sepsis",
                    "Malaria (if recent travel)"
                ]
            }
        }
    
    def load_question_templates(self) -> Dict[str, str]:
        """Load question generation templates"""
        return {
            "adaptive_prompt": """
You are an expert medical diagnostician. Generate the MOST VALUABLE next question to reduce diagnostic uncertainty.

PATIENT CONTEXT:
Primary symptoms: {symptoms}
Patient profile: {patient_profile}

DIAGNOSTIC HISTORY:
{answer_history}

CONFIDENCE ANALYSIS:
Current gaps: {confidence_gaps}
Uncertainty factors: {uncertainty_factors}

INSTRUCTIONS:
1. Choose the most medically relevant question type
2. Focus on closing the biggest diagnostic gap
3. Avoid repeating previous questions
4. Consider red flag symptoms
5. Make questions patient-friendly

Question types available:
- single_choice: One option from a list
- multiple_choice: Multiple options from a list  
- yes_no: Simple yes/no question
- scale: 1-10 rating scale
- text: Free text input

Respond ONLY with valid JSON:
{{
    "question_id": {question_id},
    "question": "Clear, patient-friendly question text",
    "question_type": "single_choice|multiple_choice|yes_no|scale|text",
    "options": ["option1", "option2", ...] or null,
    "required": true,
    "medical_rationale": "Why this question matters diagnostically",
    "confidence_targets": ["condition1", "condition2"],
    "priority_score": 1-10
}}
""",
            "follow_up_prompt": """
Based on the patient's previous answer: "{previous_answer}"
Generate a logical follow-up question that builds on this information.

{base_context}

Focus on clarifying or expanding the previous response.
""",
                         "structured_llm_prompt": """
You are an expert medical diagnostician. Generate a question that follows the exact structure specified while being medically relevant to the symptoms.

PATIENT CONTEXT:
Primary symptoms: {symptoms}
Patient profile: {patient_profile}

DIAGNOSTIC HISTORY:
{answer_history}

CONFIDENCE ANALYSIS:
Current gaps: {confidence_gaps}
Uncertainty factors: {uncertainty_factors}

STRUCTURED REQUIREMENTS:
Question Position: {question_position}/5
Required Type: {question_type}
Focus Area: {question_focus}

INSTRUCTIONS:
1. MUST use the specified question type: {question_type}
2. Focus on: {question_focus}
3. Ensure the question is medically relevant to "{symptoms}"
4. Avoid repeating previous questions
5. Consider red flag symptoms
6. Make questions patient-friendly

Question Type Guidelines:
- single_choice: Provide 4-6 clear options relevant to the symptoms
- multiple_choice: Provide 5-8 options, patient can select multiple
- text: Open-ended question for detailed responses
- scale: 1-10 rating scale for intensity/severity/frequency
- yes_no: Simple yes/no question

CRITICAL: For single_choice and multiple_choice, you MUST provide an "options" array with relevant medical choices.

Respond ONLY with valid JSON:
{{
    "question_id": {question_id},
    "question": "Clear, patient-friendly question text about {question_focus} related to {symptoms}",
    "question_type": "{question_type}",
    "options": ["option1", "option2", "option3", "option4"] or null,
    "required": true,
    "medical_rationale": "Why this {question_focus} question matters for diagnosing {symptoms}",
    "confidence_targets": ["condition1", "condition2"],
    "priority_score": {question_position}
}}
""",
        }
    
    async def generate_next_question(
        self,
        symptoms: str,
        answer_history: List[QuestionAnswer],
        confidence_gaps: ConfidenceGapAnalysis,
        patient_profile: Dict[str, Any],
        session_context: Dict[str, Any]
    ) -> QuestionGenerationResponse:
        """Generate the next most valuable diagnostic question using LLM but following structured format"""
        
        try:
            # Check if we have completed 5 questions
            answered_count = len(answer_history)
            if answered_count >= 5:
                return None
            
            # Determine question position and type based on our structure
            question_position = answered_count + 1  # 1-indexed
            
            # Generate structured LLM question based on position
            structured_question = await self.generate_structured_llm_question(
                symptoms=symptoms,
                answer_history=answer_history,
                confidence_gaps=confidence_gaps,
                patient_profile=patient_profile,
                session_context=session_context,
                question_position=question_position
            )
            
            if structured_question:
                return QuestionGenerationResponse(
                    question=structured_question,
                    generation_reasoning=f"LLM-generated structured question (position {question_position})",
                    confidence_impact_prediction=0.8
                )
            
            # Fallback to predefined questions if LLM fails
            priority_question = self.check_priority_questions(symptoms, answer_history)
            if priority_question:
                return QuestionGenerationResponse(
                    question=priority_question,
                    generation_reasoning="Fallback to predefined structured question",
                    confidence_impact_prediction=0.7
                )
            
        except Exception as e:
            logger.error(f"Error generating structured question: {e}")
            # Final fallback
            return self.get_fallback_question(symptoms)
    
    async def generate_structured_llm_question(
        self,
        symptoms: str,
        answer_history: List[QuestionAnswer],
        confidence_gaps: ConfidenceGapAnalysis,
        patient_profile: Dict[str, Any],
        session_context: Dict[str, Any],
        question_position: int
    ) -> Optional[DiagnosticQuestion]:
        """Generate LLM question that follows our structured format"""
        
        # Define the structured progression
        question_structure = {
            1: {"type": "single_choice", "focus": "primary characteristic or location"},
            2: {"type": "text", "focus": "timing, duration, or onset details"},
            3: {"type": "multiple_choice", "focus": "quality, characteristics, or associated symptoms"},
            4: {"type": "scale", "focus": "intensity, severity, or frequency"},
            5: {"type": "text", "focus": "medical history, risk factors, medications, lifestyle"}
        }
        
        current_structure = question_structure.get(question_position)
        if not current_structure:
            return None
        
        # Format answer history for context
        history_text = self.format_answer_history(answer_history)
        
        # Build structured prompt
        prompt = self.question_templates["structured_llm_prompt"].format(
            symptoms=symptoms,
            patient_profile=json.dumps(patient_profile, indent=2),
            answer_history=history_text,
            question_position=question_position,
            question_type=current_structure["type"],
            question_focus=current_structure["focus"],
            confidence_gaps=", ".join(confidence_gaps.priority_areas),
            uncertainty_factors=", ".join(confidence_gaps.uncertainty_factors),
            question_id=self.get_next_question_id()
        )
        
        # Call LLM
        response = await call_groq_api(
            prompt=prompt,
            system_message="You are an expert medical diagnostician. Generate questions that follow the exact structure specified while being medically relevant to the symptoms."
        )
        
        # Parse and validate response
        try:
            question_data = json.loads(response)
            
            # Enforce the structured type
            question_data["question_type"] = current_structure["type"]
            
            # Validate required fields for each type
            if current_structure["type"] in ["single_choice", "multiple_choice"]:
                if not question_data.get("options") or len(question_data["options"]) < 2:
                    logger.warning(f"LLM didn't provide proper options for {current_structure['type']}")
                    return None
            
            return DiagnosticQuestion(**question_data)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse structured LLM response: {e}")
            return None
    
    def check_priority_questions(
        self, 
        symptoms: str, 
        answer_history: List[QuestionAnswer]
    ) -> Optional[DiagnosticQuestion]:
        """Check for the next structured question in the sequence"""
        
        # Extract answered question IDs
        answered_count = len(answer_history)
        
        # If we've answered 5 questions, no more questions needed
        if answered_count >= 5:
            return None
        
        # Determine the symptom category
        symptom_category = self._identify_symptom_category(symptoms)
        if not symptom_category:
            return None
        
        # Get the structured questions for this category
        tree = self.medical_decision_trees.get(symptom_category)
        if not tree or "structured_questions" not in tree:
            return None
        
        structured_questions = tree["structured_questions"]
        
        # Return the next question in sequence (0-indexed)
        if answered_count < len(structured_questions):
            question_data = structured_questions[answered_count]
            question_id = self.question_counter + answered_count + 1
            
            return DiagnosticQuestion(
                question_id=question_id,
                question=question_data["question"],
                question_type=question_data["type"],
                options=question_data.get("options"),
                required=True,
                medical_rationale=question_data.get("medical_significance"),
                priority_score=9 - answered_count  # Descending priority
            )
        
        return None
    
    def _identify_symptom_category(self, symptoms: str) -> Optional[str]:
        """Identify the primary symptom category from user input"""
        symptoms_lower = symptoms.lower()
        
        # Map symptoms to categories
        category_keywords = {
            "chest_pain": ["chest pain", "chest hurt", "heart pain", "chest ache", "chest discomfort"],
            "headache": ["headache", "head pain", "migraine", "head hurt", "head ache"],
            "abdominal_pain": ["stomach pain", "belly pain", "abdominal pain", "stomach hurt", "stomach ache", "belly ache"],
            "fever": ["fever", "temperature", "hot", "feverish", "chills"]
        }
        
        # Find the best matching category
        for category, keywords in category_keywords.items():
            if any(keyword in symptoms_lower for keyword in keywords):
                return category
        
        # Default to chest_pain if no specific match (for safety)
        return "chest_pain"
    
    def get_possible_diseases_for_symptoms(self, symptoms: str) -> List[str]:
        """Get list of possible diseases for the symptom category"""
        symptom_category = self._identify_symptom_category(symptoms)
        if symptom_category and symptom_category in self.medical_decision_trees:
            return self.medical_decision_trees[symptom_category].get("possible_diseases", [])
        return []
    
    def format_answer_history(self, answer_history: List[QuestionAnswer]) -> str:
        """Format answer history for LLM prompt"""
        if not answer_history:
            return "No previous questions asked."
        
        formatted = []
        for qa in answer_history[-5:]:  # Last 5 questions only
            formatted.append(f"Q{qa.question_id}: {qa.answer_value}")
        
        return "\n".join(formatted)
    
    def get_next_question_id(self) -> int:
        """Generate unique question ID"""
        self.question_counter += 1
        return self.question_counter
    
    def get_fallback_question(self, symptoms: str) -> QuestionGenerationResponse:
        """Provide fallback question if LLM fails"""
        fallback_question = DiagnosticQuestion(
            question_id=self.get_next_question_id(),
            question="Can you describe when your symptoms started?",
            question_type="text",
            medical_rationale="Symptom onset timing is crucial for diagnosis",
            priority_score=7
        )
        
        return QuestionGenerationResponse(
            question=fallback_question,
            generation_reasoning="Fallback question due to LLM error",
            confidence_impact_prediction=0.5
        )
    
    def analyze_confidence_gaps(
        self, 
        current_confidence: Dict[str, Any],
        answer_history: List[QuestionAnswer]
    ) -> ConfidenceGapAnalysis:
        """Analyze what areas need more questioning"""
        
        uncertainty_factors = current_confidence.get("uncertainty_factors", [])
        confidence_score = current_confidence.get("score", 0.5)
        
        # Determine priority areas based on uncertainty
        priority_areas = []
        if "symptom_location" in uncertainty_factors:
            priority_areas.append("anatomical_location")
        if "symptom_timing" in uncertainty_factors:
            priority_areas.append("temporal_pattern")
        if "symptom_quality" in uncertainty_factors:
            priority_areas.append("symptom_characteristics")
        
        # Recommend question types based on gaps
        recommended_types = []
        if len(answer_history) < 2:
            recommended_types.append("single_choice")
        if confidence_score < 0.6:
            recommended_types.extend(["scale", "multiple_choice"])
        
        return ConfidenceGapAnalysis(
            uncertainty_factors=uncertainty_factors,
            priority_areas=priority_areas,
            recommended_question_types=recommended_types,
            confidence_threshold=0.7
        )
    
    def validate_question(self, question_data: Dict[str, Any]) -> DiagnosticQuestion:
        """Validate and enhance generated question"""
        
        # Ensure required fields
        if not question_data.get("question"):
            raise ValueError("Question text is required")
        
        if not question_data.get("question_type"):
            question_data["question_type"] = "text"
        
        # Validate question type and options
        q_type = question_data["question_type"]
        if q_type in ["single_choice", "multiple_choice", "scale"] and not question_data.get("options"):
            if q_type == "scale":
                question_data["options"] = [str(i) for i in range(1, 11)]
            else:
                raise ValueError(f"Question type {q_type} requires options")
        
        return DiagnosticQuestion(**question_data) 