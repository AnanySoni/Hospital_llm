"""
Urgency Assessor Utility for Phase 1 Month 3
Provides simplified urgency assessment functions for LLM-based medical triage
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.schemas.triage_models import TriageLevel, TriageAssessment, RiskFactor, RedFlag
from backend.utils.llm_utils import call_groq_api
from backend.utils.confidence_utils import calculate_confidence_level, calculate_age_risk_multiplier

logger = logging.getLogger(__name__)


async def assess_medical_urgency(
    symptoms: str,
    patient_age: int,
    medical_history: List[str],
    current_answers: Dict[str, Any],
    confidence_score: Optional[float] = None
) -> TriageAssessment:
    """
    LLM-powered urgency assessment with medical reasoning
    Simplified interface for quick urgency determination
    """
    
    system_message = """You are an emergency triage nurse AI with extensive medical training. 
    Assess the urgency level of medical situations based on symptoms, patient factors, and medical knowledge.
    Always err on the side of caution for patient safety. Your assessment can help route patients to appropriate care."""
    
    prompt = f"""
    MEDICAL TRIAGE ASSESSMENT REQUIRED:
    
    Patient Information:
    - Age: {patient_age} years old
    - Medical History: {medical_history if medical_history else "None reported"}
    
    Current Symptoms: {symptoms}
    
    Additional Patient Responses: {json.dumps(current_answers, indent=2) if current_answers else "None provided"}
    
    Initial Diagnostic Confidence: {confidence_score if confidence_score else "Not available"}
    
    Please provide a comprehensive triage assessment in this exact JSON format:
    {{
        "triage_level": "emergency|urgent|soon|routine",
        "confidence_score": 0.85,
        "time_urgency": "Seek care within X hours/days",
        "reasoning": "Detailed medical reasoning for urgency level based on symptoms and risk factors",
        "risk_factors": [
            {{
                "factor_type": "age|symptom_severity|medical_history|presentation",
                "severity": 0.8,
                "description": "Specific risk factor description"
            }}
        ],
        "recommendations": [
            "Specific care recommendations",
            "Follow-up instructions",
            "Warning signs to watch for"
        ],
        "emergency_indicators": [
            "List any emergency warning signs if present"
        ],
        "red_flags": [
            {{
                "symptom": "specific concerning symptom",
                "category": "cardiovascular|neurological|respiratory|trauma",
                "reasoning": "why this is concerning"
            }}
        ]
    }}
    
    TRIAGE LEVEL GUIDELINES:
    - EMERGENCY: Life-threatening symptoms requiring immediate care (call 911/go to ER)
      * Severe chest pain, difficulty breathing, severe bleeding
      * Loss of consciousness, severe head trauma, suspected stroke
      * Severe allergic reactions, poisoning
      
    - URGENT: Significant symptoms requiring prompt attention within 24-48 hours
      * Moderate to severe pain, persistent vomiting
      * High fever with concerning symptoms, moderate injury
      * Worsening chronic conditions
      
    - SOON: Concerning symptoms that should be evaluated within 1 week
      * Mild to moderate symptoms affecting daily activities
      * New or changing symptoms that may indicate health issues
      * Follow-up needed for ongoing conditions
      
    - ROUTINE: Minor symptoms suitable for routine care in 2+ weeks
      * Minor aches and pains, common cold symptoms
      * Routine check-ups, preventive care
      * Stable chronic conditions
    
    CRITICAL ASSESSMENT FACTORS:
    1. Symptom severity and progression
    2. Age-related risk factors (higher risk: infants, elderly)
    3. Medical history complications 
    4. Red flag symptoms requiring immediate attention
    5. Patient's ability to function normally
    6. Potential for rapid deterioration
    
    Remember: When in doubt, choose a higher urgency level for patient safety.
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        assessment_data = json.loads(response)
        
        # Validate and process the response
        triage_level = TriageLevel(assessment_data.get("triage_level", "soon"))
        confidence = min(max(assessment_data.get("confidence_score", 0.7), 0.0), 1.0)
        
        # Process risk factors
        risk_factors = []
        for rf_data in assessment_data.get("risk_factors", []):
            risk_factor = RiskFactor(
                factor_type=rf_data.get("factor_type", "assessment"),
                severity=min(max(rf_data.get("severity", 0.5), 0.0), 1.0),
                description=rf_data.get("description", "Assessment-identified risk factor"),
                weight=1.0
            )
            risk_factors.append(risk_factor)
        
        # Add age-based risk factor if significant
        age_risk_multiplier = calculate_age_risk_multiplier(patient_age, "general")
        if age_risk_multiplier > 1.0:
            age_risk = RiskFactor(
                factor_type="age",
                severity=min(age_risk_multiplier - 0.5, 1.0),  # Convert multiplier to severity
                description=f"Age {patient_age} increases medical risk",
                weight=1.0
            )
            risk_factors.append(age_risk)
        
        # Process red flags
        red_flags = []
        for rf_data in assessment_data.get("red_flags", []):
            red_flag = RedFlag(
                symptom=rf_data.get("symptom", "Concerning symptom"),
                category=rf_data.get("category", "general"),
                urgency_level=TriageLevel.URGENT,  # Default to urgent for red flags
                reasoning=rf_data.get("reasoning", "Concerning symptom requiring attention")
            )
            red_flags.append(red_flag)
        
        # Create comprehensive assessment
        assessment = TriageAssessment(
            level=triage_level,
            confidence_score=confidence,
            time_urgency=assessment_data.get("time_urgency", get_default_time_urgency(triage_level)),
            risk_factors=risk_factors,
            red_flags=red_flags,
            reasoning=assessment_data.get("reasoning", "LLM-based medical urgency assessment"),
            emergency_override=triage_level == TriageLevel.EMERGENCY,
            recommendations=assessment_data.get("recommendations", ["Consult with healthcare provider"])
        )
        
        logger.info(f"LLM urgency assessment completed: {triage_level.value} (confidence: {confidence:.2f})")
        return assessment
        
    except Exception as e:
        logger.error(f"Error in LLM urgency assessment: {e}")
        return create_conservative_fallback_assessment(symptoms, patient_age, confidence_score or 0.5)


async def quick_emergency_screening(symptoms: str, age: Optional[int] = None) -> Dict[str, Any]:
    """
    Fast emergency screening for immediate red flags
    Returns emergency status and basic recommendations
    """
    
    try:
        # Quick keyword-based emergency detection
        emergency_keywords = [
            "crushing chest pain", "difficulty breathing", "severe headache",
            "sudden confusion", "vomiting blood", "severe bleeding",
            "cannot speak", "blue lips", "unconscious", "choking",
            "severe allergic reaction", "overdose", "suicide"
        ]
        
        symptoms_lower = symptoms.lower()
        emergency_detected = False
        detected_keywords = []
        
        # Check for emergency keywords
        for keyword in emergency_keywords:
            if keyword in symptoms_lower:
                emergency_detected = True
                detected_keywords.append(keyword)
        
        # Age-specific emergency considerations
        age_emergency = False
        if age is not None:
            if age < 2 and any(word in symptoms_lower for word in ["fever", "breathing difficulty", "not responding"]):
                age_emergency = True
                detected_keywords.append("infant emergency indicators")
            elif age > 75 and "chest pain" in symptoms_lower:
                age_emergency = True
                detected_keywords.append("elderly chest pain")
        
        final_emergency = emergency_detected or age_emergency
        
        return {
            "emergency_detected": final_emergency,
            "confidence": 0.9 if emergency_detected else (0.7 if age_emergency else 0.3),
            "detected_keywords": detected_keywords,
            "recommendation": "CALL 911 IMMEDIATELY" if final_emergency else "Proceed with normal assessment",
            "urgency_level": "emergency" if final_emergency else "assessment_needed"
        }
        
    except Exception as e:
        logger.error(f"Error in emergency screening: {e}")
        return {
            "emergency_detected": True,  # Err on side of caution
            "confidence": 0.3,
            "detected_keywords": ["system_error"],
            "recommendation": "Seek immediate medical evaluation due to assessment error",
            "urgency_level": "emergency"
        }


def get_default_time_urgency(triage_level: TriageLevel) -> str:
    """Get default time urgency message for triage level"""
    
    time_urgencies = {
        TriageLevel.EMERGENCY: "Seek immediate emergency care (call 911 or go to ER now)",
        TriageLevel.URGENT: "Seek care within 24-48 hours (urgent care or ER)",
        TriageLevel.SOON: "Schedule appointment within 1 week with healthcare provider",
        TriageLevel.ROUTINE: "Schedule routine appointment within 2-4 weeks"
    }
    return time_urgencies.get(triage_level, "Consult with healthcare provider")


def create_conservative_fallback_assessment(
    symptoms: str, 
    age: int, 
    confidence_score: float
) -> TriageAssessment:
    """Create conservative fallback assessment when LLM fails"""
    
    # Conservative approach - default to URGENT if concerning symptoms
    concerning_words = ["severe", "sudden", "intense", "crushing", "difficulty", "unable", "blood"]
    is_concerning = any(word in symptoms.lower() for word in concerning_words)
    
    # Age-based risk adjustment
    if age < 5 or age > 75:
        level = TriageLevel.URGENT if is_concerning else TriageLevel.SOON
    else:
        level = TriageLevel.URGENT if is_concerning else TriageLevel.SOON
    
    # Create risk factors
    risk_factors = [
        RiskFactor(
            factor_type="system_fallback",
            severity=0.7 if is_concerning else 0.5,
            description="Conservative assessment due to system limitation - medical evaluation recommended",
            weight=1.0
        )
    ]
    
    # Add age risk if applicable
    if age < 5:
        risk_factors.append(RiskFactor(
            factor_type="age",
            severity=0.8,
            description="Young age increases medical risk",
            weight=1.0
        ))
    elif age > 75:
        risk_factors.append(RiskFactor(
            factor_type="age", 
            severity=0.7,
            description="Advanced age increases medical risk",
            weight=1.0
        ))
    
    return TriageAssessment(
        level=level,
        confidence_score=max(confidence_score * 0.6, 0.3),  # Lower confidence for fallback
        time_urgency=get_default_time_urgency(level),
        risk_factors=risk_factors,
        red_flags=[],
        reasoning="Conservative fallback assessment - recommend medical evaluation for proper diagnosis",
        emergency_override=False,
        recommendations=[
            "Consult with healthcare provider for proper evaluation",
            "Monitor symptoms and seek immediate care if they worsen",
            "Keep track of symptom changes for medical consultation"
        ]
    )


async def assess_symptom_urgency_simple(
    symptoms: str,
    age: Optional[int] = None
) -> Dict[str, Any]:
    """
    Simplified urgency assessment for basic symptom triage
    Returns basic urgency information without full assessment
    """
    
    try:
        # Quick emergency check first
        emergency_result = await quick_emergency_screening(symptoms, age)
        
        if emergency_result["emergency_detected"]:
            return {
                "urgency_level": "emergency",
                "time_urgency": "Seek immediate emergency care (call 911)",
                "confidence": emergency_result["confidence"],
                "reasoning": f"Emergency indicators detected: {', '.join(emergency_result['detected_keywords'])}",
                "recommendations": ["CALL 911 IMMEDIATELY", "Do not delay seeking emergency care"]
            }
        
        # Basic symptom categorization for non-emergency cases
        symptoms_lower = symptoms.lower()
        
        # High urgency indicators
        urgent_indicators = [
            "severe pain", "high fever", "persistent vomiting", "severe headache",
            "difficulty walking", "severe dizziness", "chest discomfort"
        ]
        
        # Moderate urgency indicators  
        moderate_indicators = [
            "moderate pain", "fever", "nausea", "headache", "fatigue",
            "mild difficulty breathing", "unusual symptoms"
        ]
        
        urgent_count = sum(1 for indicator in urgent_indicators if indicator in symptoms_lower)
        moderate_count = sum(1 for indicator in moderate_indicators if indicator in symptoms_lower)
        
        if urgent_count > 0:
            urgency_level = "urgent"
            time_urgency = "Seek care within 24-48 hours"
            confidence = 0.8
        elif moderate_count > 0:
            urgency_level = "soon"
            time_urgency = "Schedule appointment within 1 week"
            confidence = 0.7
        else:
            urgency_level = "routine"
            time_urgency = "Schedule routine appointment within 2-4 weeks"
            confidence = 0.6
        
        return {
            "urgency_level": urgency_level,
            "time_urgency": time_urgency,
            "confidence": confidence,
            "reasoning": f"Based on symptom analysis - {urgent_count} urgent indicators, {moderate_count} moderate indicators",
            "recommendations": [
                "Monitor symptoms for changes",
                "Seek care if symptoms worsen",
                "Keep track of symptom progression"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in simple urgency assessment: {e}")
        return {
            "urgency_level": "soon",
            "time_urgency": "Schedule appointment within 1 week due to assessment error",
            "confidence": 0.4,
            "reasoning": "Conservative assessment due to system error",
            "recommendations": ["Consult healthcare provider for proper evaluation"]
        } 