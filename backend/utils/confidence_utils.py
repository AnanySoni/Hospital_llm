"""
Confidence Scoring Utilities for Medical AI Responses
Provides confidence assessment for diagnoses, routing decisions, and recommendations
"""

import json
import re
from typing import Dict, List, Tuple, Optional, Any
from .llm_utils import call_groq_api
from backend.schemas.triage_models import AGE_RISK_MULTIPLIERS


def calculate_confidence_level(score: float) -> str:
    """Convert numerical confidence score to descriptive level"""
    if score >= 0.8:
        return "high"
    elif score >= 0.6:
        return "medium"
    else:
        return "low"


def extract_confidence_from_response(response: str) -> Tuple[float, str]:
    """Extract confidence score and reasoning from LLM response"""
    # Look for confidence patterns in the response
    confidence_patterns = [
        r"confidence[:\s]*(\d+(?:\.\d+)?)[%\s]",
        r"certainty[:\s]*(\d+(?:\.\d+)?)[%\s]",
        r"probability[:\s]*(\d+(?:\.\d+)?)[%\s]",
        r"score[:\s]*(\d+(?:\.\d+)?)"
    ]
    
    score = 0.7  # Default moderate confidence
    reasoning = "Standard confidence assessment based on symptom analysis"
    
    for pattern in confidence_patterns:
        match = re.search(pattern, response.lower())
        if match:
            found_score = float(match.group(1))
            # Convert percentage to decimal if needed
            if found_score > 1.0:
                found_score = found_score / 100.0
            score = max(0.0, min(1.0, found_score))  # Clamp between 0 and 1
            break
    
    # Extract reasoning from response
    reasoning_patterns = [
        r"because[:\s]+(.*?)(?:\.|$)",
        r"based on[:\s]+(.*?)(?:\.|$)", 
        r"due to[:\s]+(.*?)(?:\.|$)",
        r"given[:\s]+(.*?)(?:\.|$)"
    ]
    
    for pattern in reasoning_patterns:
        match = re.search(pattern, response.lower())
        if match:
            reasoning = match.group(1).strip()
            break
    
    return score, reasoning


async def assess_diagnostic_confidence(
    symptoms: str,
    diagnosis_response: str,
    answered_questions: Dict[str, str]
) -> Dict:
    """Assess confidence in diagnostic analysis"""
    
    system_message = """You are a medical AI confidence assessor. Analyze the diagnostic confidence and provide a detailed assessment."""
    
    prompt = f"""
    Analyze the confidence level for this medical diagnosis:
    
    Original Symptoms: {symptoms}
    Diagnostic Response: {diagnosis_response}
    Questions Answered: {json.dumps(answered_questions)}
    
    Provide your analysis in this exact JSON format:
    {{
        "confidence_score": 0.85,
        "confidence_level": "high",
        "reasoning": "Clear symptom presentation with specific indicators supporting the diagnosis",
        "uncertainty_factors": [
            "Limited physical examination data",
            "No laboratory test results available"
        ],
        "certainty_indicators": [
            "Classic symptom triad present",
            "Symptom progression consistent with condition"
        ],
        "information_gaps": [
            "Duration of symptoms unclear",
            "Family history not assessed"
        ]
    }}
    
    Confidence scoring guidelines:
    - 0.9-1.0: Highly specific symptoms, clear diagnosis indicators
    - 0.7-0.89: Good symptom match, some uncertainty factors
    - 0.5-0.69: Moderate symptoms, multiple possibilities
    - 0.3-0.49: Vague symptoms, limited information
    - 0.0-0.29: Insufficient information for reliable assessment
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        # Try to parse JSON response
        confidence_data = json.loads(response)
        
        # Validate and normalize the response
        score = confidence_data.get("confidence_score", 0.7)
        score = max(0.0, min(1.0, float(score)))
        
        return {
            "score": score,
            "level": calculate_confidence_level(score),
            "reasoning": confidence_data.get("reasoning", "Confidence assessment based on symptom analysis"),
            "uncertainty_factors": confidence_data.get("uncertainty_factors", []),
            "certainty_indicators": confidence_data.get("certainty_indicators", []),
            "information_gaps": confidence_data.get("information_gaps", [])
        }
        
    except Exception as e:
        print(f"Error in confidence assessment: {e}")
        # Fallback confidence assessment
        base_score = 0.6 if len(answered_questions) > 2 else 0.4
        
        uncertainty_factors = []
        if len(answered_questions) < 3:
            uncertainty_factors.append("Limited diagnostic questions answered")
        if len(symptoms.split()) < 5:
            uncertainty_factors.append("Brief symptom description")
        
        return {
            "score": base_score,
            "level": calculate_confidence_level(base_score),
            "reasoning": "Automated confidence assessment based on available information",
            "uncertainty_factors": uncertainty_factors
        }


async def assess_routing_confidence(
    diagnosis: Dict,
    routing_decision: str,
    available_options: Dict
) -> Dict:
    """Assess confidence in routing/treatment decision"""
    
    system_message = """You are a medical AI routing confidence assessor. Evaluate the confidence in care coordination decisions."""
    
    prompt = f"""
    Assess confidence in this medical routing decision:
    
    Diagnosis: {json.dumps(diagnosis)}
    Routing Decision: {routing_decision}
    Available Options: {json.dumps(available_options)}
    
    Provide confidence analysis in this exact JSON format:
    {{
        "confidence_score": 0.78,
        "confidence_level": "medium",
        "reasoning": "Clear indication for specialist referral based on symptom severity",
        "uncertainty_factors": [
            "Multiple treatment pathways possible",
            "Urgency level assessment may vary"
        ],
        "decision_support": [
            "Symptom severity indicates specialist care",
            "Standard care pathway for this condition"
        ],
        "alternative_considerations": [
            "Could consider additional tests first",
            "Primary care consultation as alternative"
        ]
    }}
    
    Routing confidence guidelines:
    - 0.9-1.0: Clear medical indication, standard care pathway
    - 0.7-0.89: Good indication with minor alternatives
    - 0.5-0.69: Reasonable choice with multiple valid options
    - 0.3-0.49: Uncertain routing, multiple equally valid paths
    - 0.0-0.29: Insufficient information for routing decision
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        confidence_data = json.loads(response)
        
        score = confidence_data.get("confidence_score", 0.7)
        score = max(0.0, min(1.0, float(score)))
        
        return {
            "score": score,
            "level": calculate_confidence_level(score),
            "reasoning": confidence_data.get("reasoning", "Routing decision based on medical assessment"),
            "uncertainty_factors": confidence_data.get("uncertainty_factors", []),
            "decision_support": confidence_data.get("decision_support", []),
            "alternative_considerations": confidence_data.get("alternative_considerations", [])
        }
        
    except Exception as e:
        print(f"Error in routing confidence assessment: {e}")
        return {
            "score": 0.7,
            "level": "medium",
            "reasoning": "Standard routing decision based on available information",
            "uncertainty_factors": ["Automated assessment - manual review recommended"]
        }


async def assess_question_relevance(
    current_symptoms: str,
    question_text: str,
    previous_answers: Dict[str, str]
) -> Dict:
    """Assess how relevant and important a diagnostic question is"""
    
    system_message = """You are a medical questioning relevance assessor. Evaluate how important and relevant a diagnostic question is."""
    
    prompt = f"""
    Assess the relevance and importance of this diagnostic question:
    
    Current Symptoms: {current_symptoms}
    Question: {question_text}
    Previous Answers: {json.dumps(previous_answers)}
    
    Provide assessment in this JSON format:
    {{
        "relevance_score": 0.85,
        "importance_level": "high",
        "reasoning": "Essential for ruling out serious conditions",
        "diagnostic_value": [
            "Helps differentiate between conditions A and B",
            "Critical for urgency assessment"
        ],
        "skip_conditions": []
    }}
    
    Relevance scoring:
    - 0.9-1.0: Critical for diagnosis/safety
    - 0.7-0.89: Important for differential diagnosis
    - 0.5-0.69: Helpful but not essential
    - 0.3-0.49: Minor relevance
    - 0.0-0.29: Not relevant given current information
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        relevance_data = json.loads(response)
        
        score = relevance_data.get("relevance_score", 0.7)
        score = max(0.0, min(1.0, float(score)))
        
        return {
            "score": score,
            "level": calculate_confidence_level(score),
            "reasoning": relevance_data.get("reasoning", "Question relevance assessed"),
            "diagnostic_value": relevance_data.get("diagnostic_value", []),
            "skip_conditions": relevance_data.get("skip_conditions", [])
        }
        
    except Exception as e:
        print(f"Error in question relevance assessment: {e}")
        return {
            "score": 0.7,
            "level": "medium", 
            "reasoning": "Standard diagnostic question",
            "diagnostic_value": ["Standard medical assessment"]
        }


def aggregate_confidence_scores(individual_scores: List[Dict]) -> Dict:
    """Aggregate multiple confidence scores into overall assessment"""
    
    if not individual_scores:
        return {
            "score": 0.5,
            "level": "medium",
            "reasoning": "No confidence data available",
            "uncertainty_factors": ["Insufficient confidence data"]
        }
    
    # Calculate weighted average
    total_weight = 0
    weighted_sum = 0
    all_uncertainty_factors = []
    
    for score_data in individual_scores:
        weight = score_data.get("weight", 1.0)
        score = score_data.get("score", 0.5)
        
        weighted_sum += score * weight
        total_weight += weight
        
        if "uncertainty_factors" in score_data:
            all_uncertainty_factors.extend(score_data["uncertainty_factors"])
    
    final_score = weighted_sum / total_weight if total_weight > 0 else 0.5
    
    # Remove duplicate uncertainty factors
    unique_uncertainty_factors = list(set(all_uncertainty_factors))
    
    return {
        "score": final_score,
        "level": calculate_confidence_level(final_score),
        "reasoning": f"Aggregated confidence from {len(individual_scores)} assessments",
        "uncertainty_factors": unique_uncertainty_factors[:5],  # Limit to top 5
        "component_scores": len(individual_scores)
    }


def calculate_age_risk_multiplier(age: int, symptom_category: str) -> float:
    """
    Calculate age-based risk adjustment multiplier for triage decisions
    Returns multiplier (0.0-2.0) where 1.0 is baseline risk
    """
    
    if symptom_category not in AGE_RISK_MULTIPLIERS:
        # Default age-based risk adjustment for unknown categories
        if age < 5:
            return 1.3  # Higher risk for infants/toddlers
        elif age < 18:
            return 0.8  # Moderate risk for children
        elif 18 <= age < 65:
            return 1.0  # Baseline risk for adults
        else:
            return 1.2  # Higher risk for elderly
    
    age_ranges = AGE_RISK_MULTIPLIERS[symptom_category]
    
    for (min_age, max_age), multiplier in age_ranges.items():
        if min_age <= age < max_age:
            return multiplier
    
    # Fallback to elderly risk if age is outside all ranges
    return 1.1


def assess_demographic_risk_factors(patient_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Assess demographic risk factors for medical conditions
    Returns list of risk factor assessments
    """
    
    risk_factors = []
    age = patient_profile.get("age", 35)
    gender = patient_profile.get("gender", "unknown")
    medical_history = patient_profile.get("medical_history", [])
    
    # Age-based risk assessment
    if age < 1:
        risk_factors.append({
            "factor_type": "age",
            "severity": 0.9,
            "description": "Infant age increases medical risk",
            "weight": 1.2
        })
    elif age > 75:
        risk_factors.append({
            "factor_type": "age", 
            "severity": 0.8,
            "description": "Advanced age increases medical complications risk",
            "weight": 1.1
        })
    elif age > 65:
        risk_factors.append({
            "factor_type": "age",
            "severity": 0.6,
            "description": "Elderly age moderately increases medical risk", 
            "weight": 1.0
        })
    
    # Medical history risk factors
    high_risk_conditions = [
        "diabetes", "heart disease", "hypertension", "copd", "asthma",
        "kidney disease", "liver disease", "cancer", "immunocompromised"
    ]
    
    for condition in medical_history:
        condition_lower = condition.lower()
        if any(risk_condition in condition_lower for risk_condition in high_risk_conditions):
            risk_factors.append({
                "factor_type": "medical_history",
                "severity": 0.7,
                "description": f"History of {condition} increases complication risk",
                "weight": 1.0
            })
    
    return risk_factors


async def enhanced_confidence_with_triage(
    symptoms: str,
    diagnosis_response: str,
    answered_questions: Dict[str, str],
    patient_profile: Dict[str, Any],
    triage_assessment: Optional[Dict[str, Any]] = None
) -> Dict:
    """
    Enhanced confidence assessment that incorporates triage urgency level
    """
    
    # Get base confidence assessment
    base_confidence = await assess_diagnostic_confidence(
        symptoms, diagnosis_response, answered_questions
    )
    
    # Adjust confidence based on triage urgency
    if triage_assessment:
        triage_level = triage_assessment.get("level", "routine")
        
        # Adjust confidence based on urgency level
        urgency_confidence_adjustment = {
            "emergency": -0.1,  # Lower confidence for emergency situations (more uncertainty)
            "urgent": -0.05,    # Slight confidence reduction for urgent cases
            "soon": 0.0,        # No adjustment for moderate urgency
            "routine": 0.05     # Slight confidence boost for routine cases
        }
        
        adjustment = urgency_confidence_adjustment.get(triage_level, 0.0)
        adjusted_score = max(0.0, min(1.0, base_confidence["score"] + adjustment))
        
        # Update uncertainty factors with triage considerations
        uncertainty_factors = base_confidence.get("uncertainty_factors", [])
        
        if triage_level == "emergency":
            uncertainty_factors.append("Emergency situation may have multiple urgent considerations")
        elif len(triage_assessment.get("red_flags", [])) > 0:
            uncertainty_factors.append("Red flag symptoms detected requiring urgent attention")
        
        # Add demographic risk factors to uncertainty
        demographic_risks = assess_demographic_risk_factors(patient_profile)
        for risk in demographic_risks:
            if risk["severity"] > 0.7:
                uncertainty_factors.append(risk["description"])
        
        return {
            "score": adjusted_score,
            "level": calculate_confidence_level(adjusted_score),
            "reasoning": f"{base_confidence['reasoning']} (adjusted for {triage_level} urgency)",
            "uncertainty_factors": uncertainty_factors,
            "triage_adjusted": True,
            "triage_level": triage_level,
            "demographic_risks": demographic_risks
        }
    
    return base_confidence 