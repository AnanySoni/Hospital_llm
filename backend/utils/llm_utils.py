import os
import httpx
import json
import uuid
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from datetime import datetime
# Import confidence utilities (with fallback for testing)
try:
    from .confidence_utils import calculate_confidence_level
except ImportError:
    def calculate_confidence_level(score: float) -> str:
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"

# Load .env from project root explicitly so LLM keys and DB config are available
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama2-70b-4096")

# In-memory storage for diagnostic sessions (in production, use Redis or database)
diagnostic_sessions: Dict[str, dict] = {}

def is_conversational_input(user_input: str) -> bool:
    """Check if the input is a greeting or general conversation rather than symptoms."""
    user_input_lower = user_input.lower().strip()
    
    # Common greetings and conversational phrases
    conversational_phrases = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
        "how are you", "what's up", "how do you do", "greetings",
        "help", "can you help me", "i need help",
        "what can you do", "how does this work", "what is this",
        "thank you", "thanks", "bye", "goodbye", "see you",
        "ok", "okay", "yes", "no", "maybe", "sure"
    ]
    
    # Check if input is short and matches conversational patterns
    if len(user_input.strip()) <= 3:  # Very short inputs like "hi", "ok"
        return True
        
    # Check for exact matches or if input starts with conversational phrases
    for phrase in conversational_phrases:
        if user_input_lower == phrase or user_input_lower.startswith(phrase):
            return True
    
    # Check if input contains question words but no medical terms
    question_words = ["what", "how", "why", "when", "where", "who"]
    medical_terms = ["pain", "hurt", "ache", "sick", "fever", "cough", "symptom", "feel"]
    
    has_question_word = any(word in user_input_lower for word in question_words)
    has_medical_term = any(word in user_input_lower for word in medical_terms)
    
    if has_question_word and not has_medical_term:
        return True
    
    return False

def get_conversational_response() -> str:
    """Return a friendly response for conversational inputs."""
    return json.dumps([{
        "type": "conversation",
        "message": "Hello! 👋 I'm here to help you find the right doctor for your health concerns. To get started, please describe any symptoms or health issues you're experiencing. For example, you could say 'I have a headache and fever' or 'I'm experiencing chest pain'. What symptoms can I help you with today?",
        "suggestions": [
            "I have a headache and feel dizzy",
            "I'm experiencing chest pain",
            "I have a persistent cough and fever",
            "I have back pain that won't go away",
            "I'm having stomach issues"
        ]
    }])

async def get_doctor_recommendations(symptoms: str, doctors: list, hospital_id: int = None):
    # First check if this is a conversational input rather than symptoms
    if is_conversational_input(symptoms):
        return get_conversational_response()
    # Filter doctors by hospital_id if provided
    if hospital_id is not None:
        doctors = [doc for doc in doctors if doc.get('hospital_id') == hospital_id]
    if not GROQ_API_KEY:
        # If no API key, return mock data for testing
        # Ensure we have at least 3 doctors to recommend
        available_doctors = doctors[:3] if len(doctors) >= 3 else doctors + [doctors[0]] * (3 - len(doctors))
        
        # Map symptoms to relevant specialties
        symptom_specialties = {
            'chest': ['Cardiology', 'Internal Medicine'],
            'heart': ['Cardiology'],
            'pain': ['Internal Medicine', 'General Medicine'],
            'fever': ['Internal Medicine', 'General Medicine'],
            'headache': ['Neurology', 'General Medicine'],
            'cancer': ['Oncology', 'Internal Medicine'],
            'breathing': ['Pulmonology', 'Internal Medicine'],
            'stomach': ['Gastroenterology', 'Internal Medicine'],
            'joint': ['Orthopedics', 'Rheumatology'],
            'skin': ['Dermatology', 'General Medicine']
        }
        
        # Find relevant doctors based on symptoms
        relevant_specialties = set()
        symptoms_lower = symptoms.lower()
        for keyword, specialties in symptom_specialties.items():
            if keyword in symptoms_lower:
                relevant_specialties.update(specialties)
        
        if not relevant_specialties:
            relevant_specialties = {'General Medicine', 'Internal Medicine'}
        
        # Sort doctors by relevance to symptoms
        recommended_doctors = []
        for doc in doctors:
            dept = doc.get('department', '')
            tags = doc.get('tags', [])
            
            # Calculate relevance score
            score = 0
            if dept in relevant_specialties:
                score += 2
            for tag in tags:
                if any(specialty.lower() in tag.lower() for specialty in relevant_specialties):
                    score += 1
                if any(keyword in symptoms_lower and keyword in tag.lower() 
                      for keyword in symptom_specialties.keys()):
                    score += 2
            
            if score > 0:
                recommended_doctors.append((score, doc))
        
        # Sort by relevance score and take top 3
        recommended_doctors.sort(reverse=True)
        final_recommendations = []
        used_departments = set()
        
        # First, add highest scoring doctor from each relevant department
        for score, doc in recommended_doctors:
            if len(final_recommendations) < 3 and doc['department'] not in used_departments:
                final_recommendations.append({
                    "id": doc["id"],
                    "name": doc["name"],
                    "specialization": doc["department"],
                    "reason": f"Dr. {doc['name'].split()[-1]} specializes in {doc['department']} and has expertise in {', '.join(doc['tags']) if doc['tags'] else 'general medicine'}. They are highly recommended for your symptoms: {symptoms}.",
                    "experience": f"Extensive experience in {doc['department']} with focus on {', '.join(doc['tags'][:2]) if doc['tags'] else 'patient care'}",
                    "expertise": doc["tags"] if doc["tags"] else [doc["department"]]
                })
                used_departments.add(doc['department'])
        
        # If we still need more recommendations, add highest scoring remaining doctors
        for score, doc in recommended_doctors:
            if len(final_recommendations) < 3 and not any(r['id'] == doc['id'] for r in final_recommendations):
                final_recommendations.append({
                    "id": doc["id"],
                    "name": doc["name"],
                    "specialization": doc["department"],
                    "reason": f"Dr. {doc['name'].split()[-1]} specializes in {doc['department']} and has expertise in {', '.join(doc['tags']) if doc['tags'] else 'general medicine'}. They are well-qualified to help with your symptoms: {symptoms}.",
                    "experience": f"Experienced in {doc['department']} with focus on {', '.join(doc['tags'][:2]) if doc['tags'] else 'patient care'}",
                    "expertise": doc["tags"] if doc["tags"] else [doc["department"]]
                })
        
        # If we still don't have 3 recommendations, add general medicine doctors
        while len(final_recommendations) < 3 and len(doctors) > 0:
            for doc in doctors:
                if len(final_recommendations) >= 3:
                    break
                if not any(r['id'] == doc['id'] for r in final_recommendations):
                    final_recommendations.append({
                        "id": doc["id"],
                        "name": doc["name"],
                        "specialization": doc["department"],
                        "reason": f"Dr. {doc['name'].split()[-1]} can provide general medical evaluation for your symptoms: {symptoms}.",
                        "experience": f"Qualified medical professional in {doc['department']}",
                        "expertise": doc["tags"] if doc["tags"] else [doc["department"]]
                    })
            # If we still don't have enough doctors, duplicate some with different reasons
            if len(final_recommendations) < 3 and len(doctors) > 0:
                for doc in doctors:
                    if len(final_recommendations) >= 3:
                        break
                    if len([r for r in final_recommendations if r['id'] == doc['id']]) < 2:  # Allow up to 2 duplicates
                        final_recommendations.append({
                            "id": doc["id"],
                            "name": doc["name"],
                            "specialization": doc["department"],
                            "reason": f"Dr. {doc['name'].split()[-1]} is also available for consultation and can provide comprehensive care for your symptoms: {symptoms}.",
                            "experience": f"Alternative consultation option in {doc['department']}",
                            "expertise": doc["tags"] if doc["tags"] else [doc["department"]]
                        })
                break
        
        return json.dumps(final_recommendations)
    
    # Prepare doctor context for the prompt
    doctor_context = "\n".join([
        f"ID: {doc['id']}, Name: {doc['name']}, Department: {doc['department']}, Subdivision: {doc['subdivision']}, Tags: {', '.join(doc['tags'])}" 
        for doc in doctors
    ])
    
    print(f"Calling Groq API with key: {GROQ_API_KEY[:8]}..." if GROQ_API_KEY else "No Groq API key found, using fallback.")
    
    prompt = (
        f"You are a friendly and empathetic medical assistant helping patients find the right doctors. "
        f"A patient is experiencing: {symptoms}\n\n"
        f"Available doctors:\n{doctor_context}\n\n"
        f"Recommend exactly 3 most suitable doctors for these symptoms. "
        f"Write in a caring, professional tone that makes the patient feel understood and reassured. "
        f"For each doctor, explain their expertise and why they're specifically suitable for these symptoms in a warm, human way. "
        f"Respond ONLY with a JSON array in this exact format:\n"
        f'[{{\n'
        f'  "id": number,\n'
        f'  "name": "string",\n'
        f'  "specialization": "string",\n'
        f'  "reason": "detailed, caring explanation that addresses the specific symptoms",\n'
        f'  "experience": "string describing their experience in a reassuring way",\n'
        f'  "expertise": ["string", "string", ...]\n'
        f'}}, ...]\n'
        f"Make the reason field empathetic, detailed, and directly relevant to what the patient is experiencing. "
        f"Use phrases like 'I understand how concerning this must be' or 'Dr. X has extensive experience helping patients with exactly these symptoms.'"
    )
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a medical assistant that provides detailed doctor recommendations in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(GROQ_API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            try:
                recommendations = json.loads(content)
                if not isinstance(recommendations, list):
                    raise ValueError("Response is not a JSON array")
                
                # Ensure we have exactly 3 recommendations
                if len(recommendations) < 3:
                    print(f"API returned only {len(recommendations)} doctors, filling to 3...")
                    # Add more doctors from the database if needed
                    used_ids = {r.get('id') for r in recommendations}
                    for doc in doctors:
                        if len(recommendations) >= 3:
                            break
                        if doc['id'] not in used_ids:
                            recommendations.append({
                                "id": doc["id"],
                                "name": doc["name"],
                                "specialization": doc["department"],
                                "reason": f"Dr. {doc['name'].split()[-1]} can provide additional medical consultation for your symptoms: {symptoms}.",
                                "experience": f"Qualified medical professional in {doc['department']}",
                                "expertise": doc.get("tags", [doc["department"]])
                            })
                            used_ids.add(doc['id'])
                
                return json.dumps(recommendations[:3])  # Ensure exactly 3
            except (json.JSONDecodeError, ValueError) as e:
                print(f"LLM response parsing failed (using fallback): {str(e)[:100]}...")
                # Enhanced fallback to always return 3 doctors
                fallback_recommendations = []
                for i in range(min(3, len(doctors))):
                    fallback_recommendations.append({
                        "id": doctors[i]["id"],
                        "name": doctors[i]["name"],
                        "specialization": doctors[i]["department"],
                        "reason": f"Recommended for symptoms: {symptoms}",
                        "experience": "Many years of clinical experience",
                        "expertise": doctors[i].get("tags", [doctors[i]["department"]])
                    })
                
                # If we still need more doctors, duplicate with different reasons
                while len(fallback_recommendations) < 3 and len(doctors) > 0:
                    existing_count = len(fallback_recommendations)
                    doc = doctors[existing_count % len(doctors)]
                    fallback_recommendations.append({
                        "id": doc["id"],
                        "name": doc["name"],
                        "specialization": doc["department"],
                        "reason": f"Alternative consultation option for your symptoms: {symptoms}",
                        "experience": f"Additional specialist available in {doc['department']}",
                        "expertise": doc.get("tags", [doc["department"]])
                    })
                
                return json.dumps(fallback_recommendations[:3])
                
    except Exception as e:
        print(f"Groq API call failed: {e}")
        # Enhanced fallback to always return 3 doctors on API error
        fallback_recommendations = []
        for i in range(min(3, len(doctors))):
            fallback_recommendations.append({
                "id": doctors[i]["id"],
                "name": doctors[i]["name"],
                "specialization": doctors[i]["department"],
                "reason": "Recommended (fallback due to service error)",
                "experience": "Experienced medical professional",
                "expertise": doctors[i].get("tags", [doctors[i]["department"]])
            })
        
        # If we still need more doctors, duplicate with different reasons
        while len(fallback_recommendations) < 3 and len(doctors) > 0:
            existing_count = len(fallback_recommendations)
            doc = doctors[existing_count % len(doctors)]
            fallback_recommendations.append({
                "id": doc["id"],
                "name": doc["name"],
                "specialization": doc["department"],
                "reason": "Alternative recommendation (service backup)",
                "experience": f"Available specialist in {doc['department']}",
                "expertise": doc.get("tags", [doc["department"]])
            })
        
        return json.dumps(fallback_recommendations[:3]) 

def robust_json_parse(response_text: str):
    """Robust JSON parsing with multiple fallback strategies - handles both objects and arrays"""
    try:
        # First attempt: Direct JSON parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        try:
            # Second attempt: Extract JSON from markdown/text
            import re
            # Look for JSON blocks in markdown (both objects and arrays)
            json_pattern = r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            if matches:
                return json.loads(matches[0])
                
            # Look for standalone JSON objects
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
            
            # Look for standalone JSON arrays
            json_pattern = r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
                    
        except Exception:
            pass
            
        raise ValueError("No valid JSON found in response")

async def call_groq_api(prompt: str, system_message: str = None, max_retries: int = 3, retry_delay: float = 2.0) -> str:
    """Generic function to call Groq API with rate limiting protection"""
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not found")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1500
    }
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(GROQ_API_URL, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content.strip()
                
        except httpx.HTTPStatusError as e:
            last_exception = e
            if e.response.status_code == 429:  # Rate limit error
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # For rate limits, provide a graceful degradation instead of failing
                    print(f"Groq API call failed: {e}")
                    return "Rate limit exceeded. Using fallback response."
            elif e.response.status_code >= 500:  # Server errors
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"Server error {e.response.status_code}, waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
            raise e
            
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Network error, waiting {wait_time} seconds before retry")
                await asyncio.sleep(wait_time)
                continue
            raise e
    
    # If we get here, all retries failed
    raise last_exception or Exception("All retry attempts failed")


async def generate_diagnostic_questions(symptoms: str, session_id: str) -> List[dict]:
    """Generate 3-5 critical diagnostic questions based on symptoms"""
    
    system_message = """You are an expert medical assistant. Generate 3-5 critical diagnostic questions to better understand the patient's condition. 
    Focus on questions that will help determine urgency, severity, and appropriate next steps. 
    Return ONLY a JSON array of questions."""
    
    prompt = f"""
    Patient symptoms: {symptoms}
    
    Generate 3-5 critical diagnostic questions. Focus on:
    1. Severity and intensity of symptoms
    2. Duration and timing
    3. Location and radiation
    4. Triggers and aggravating factors
    5. Associated symptoms
    
    Return JSON format:
    [
        {{
            "question_id": 1,
            "question": "How severe is your pain on a scale of 1-10?",
            "question_type": "symptom_severity",
            "options": ["1-3 (Mild)", "4-6 (Moderate)", "7-10 (Severe)"],
            "required": true
        }}
    ]
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        parsed_response = robust_json_parse(response)
        
        # Handle both array and object responses
        if isinstance(parsed_response, list):
            questions = parsed_response
        elif isinstance(parsed_response, dict) and "questions" in parsed_response:
            questions = parsed_response["questions"]
        else:
            # If it's not a list or doesn't have questions, use fallback
            raise ValueError("Invalid response format")
        
        # Validate that we have a proper questions list
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("No valid questions found in response")
        
        # Store session
        diagnostic_sessions[session_id] = {
            "initial_symptoms": symptoms,
            "questions": questions,
            "answers": {},
            "current_question": 0
        }
        
        return questions
    except Exception as e:
        print(f"Error generating diagnostic questions: {e}")
        # Fallback questions
        return [
            {
                "question_id": 1,
                "question": "How severe are your symptoms on a scale of 1-10?",
                "question_type": "symptom_severity",
                "options": ["1-3 (Mild)", "4-6 (Moderate)", "7-10 (Severe)"],
                "required": True
            },
            {
                "question_id": 2,
                "question": "How long have you been experiencing these symptoms?",
                "question_type": "duration",
                "options": ["Less than 24 hours", "1-3 days", "1-2 weeks", "More than 2 weeks"],
                "required": True
            },
            {
                "question_id": 3,
                "question": "Are there any specific triggers that make your symptoms worse?",
                "question_type": "triggers",
                "required": True
            }
        ]


async def generate_predictive_diagnosis(symptoms: str, answers: dict) -> dict:
    """Generate predictive diagnosis based on symptoms and answers with confidence scoring"""
    
    system_message = """You are an expert medical AI assistant. Based on symptoms and patient answers, provide a predictive diagnosis with confidence assessment. 
    Be conservative and always recommend professional medical evaluation. Return ONLY JSON format."""
    
    # Combine symptoms and answers
    context = f"Symptoms: {symptoms}\n"
    for q_id, answer in answers.items():
        context += f"Answer {q_id}: {answer}\n"
    
    prompt = f"""
    {context}
    
    Provide a predictive diagnosis with confidence assessment in JSON format:
    {{
        "possible_conditions": ["condition1", "condition2"],
        "confidence_level": "High/Medium/Low",
        "urgency_level": "Emergency/Urgent/Routine",
        "recommended_action": "Immediate action needed",
        "explanation": "Detailed explanation of the diagnosis",
        "confidence_score": 0.75,
        "diagnostic_confidence": {{
            "score": 0.75,
            "level": "medium",
            "reasoning": "Good symptom match with some uncertainty factors",
            "uncertainty_factors": [
                "Limited physical examination data",
                "No laboratory test results available"
            ]
        }}
    }}
    
    Confidence scoring guidelines:
    - 0.9-1.0: Highly specific symptoms, clear diagnosis indicators
    - 0.7-0.89: Good symptom match, some uncertainty factors
    - 0.5-0.69: Moderate symptoms, multiple possibilities
    - 0.3-0.49: Vague symptoms, limited information
    - 0.0-0.29: Insufficient information for reliable assessment
    
    Important guidelines:
    - Always err on the side of caution
    - If symptoms suggest emergency, mark as Emergency
    - Be specific about possible conditions
    - Explain why each condition is possible
    - Include confidence assessment for transparency
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        diagnosis_data = json.loads(response)
        
        # Ensure confidence scoring is present
        if "confidence_score" not in diagnosis_data:
            base_score = 0.6 if len(answers) > 2 else 0.4
            diagnosis_data["confidence_score"] = base_score
            
        if "diagnostic_confidence" not in diagnosis_data:
            score = diagnosis_data.get("confidence_score", 0.6)
            diagnosis_data["diagnostic_confidence"] = {
                "score": score,
                "level": calculate_confidence_level(score),
                "reasoning": "Confidence assessment based on symptom analysis",
                "uncertainty_factors": ["Limited physical examination data"] if len(answers) < 3 else []
            }
        
        return diagnosis_data
        
    except Exception as e:
        print(f"Error generating diagnosis: {e}")
        base_score = 0.4
        return {
            "possible_conditions": ["Medical evaluation needed"],
            "confidence_level": "Low",
            "urgency_level": "Routine",
            "recommended_action": "Schedule a consultation with a healthcare provider",
            "explanation": "Based on your symptoms, a professional medical evaluation is recommended to determine the exact cause and appropriate treatment.",
            "confidence_score": base_score,
            "diagnostic_confidence": {
                "score": base_score,
                "level": "low",
                "reasoning": "Automated fallback assessment",
                "uncertainty_factors": ["System error occurred", "Limited diagnostic information"]
            }
        }


async def generate_test_recommendations(diagnosis: dict, symptoms: str, tests: list = None, hospital_id: int = None) -> list:
    """Generate test recommendations based on diagnosis"""
    
    system_message = """You are a medical AI assistant. Recommend appropriate medical tests based on the diagnosis and symptoms. 
    Return ONLY JSON array of test recommendations."""
    
    prompt = f"""
    Diagnosis: {json.dumps(diagnosis)}
    Symptoms: {symptoms}
    
    Recommend appropriate medical tests in JSON format:
    [
        {{
            "test_id": "blood_cbc",
            "test_name": "Complete Blood Count (CBC)",
            "test_category": "Blood Test",
            "description": "Measures red blood cells, white blood cells, and platelets",
            "urgency": "Within 24 hours/Within week/Routine",
            "cost_estimate": "$50-100",
            "preparation_required": "Fasting for 8-12 hours",
            "why_recommended": "To check for infection, anemia, or other blood disorders"
        }}
    ]
    
    Consider:
    - Blood tests for general health markers
    - Imaging tests if needed
    - Specialized tests based on symptoms
    - Cost and preparation requirements
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        test_recs = json.loads(response)
        # Filter test recommendations by hospital_id if provided
        if hospital_id is not None and tests is not None:
            allowed_test_ids = {t['test_id'] for t in tests if t.get('hospital_id') == hospital_id or t.get('hospital_id') is None}
            test_recs = [t for t in test_recs if t.get('test_id') in allowed_test_ids]
        return test_recs
    except Exception as e:
        print(f"Error generating test recommendations: {e}")
        fallback = {
            "test_id": "general_blood",
            "test_name": "General Blood Panel",
            "test_category": "Blood Test",
            "description": "Basic blood work to assess overall health",
            "urgency": "Within week",
            "cost_estimate": "$100-200",
            "preparation_required": "Fasting for 8-12 hours",
            "why_recommended": "To establish baseline health markers and identify any abnormalities"
        }
        if hospital_id is not None and tests is not None:
            allowed_test_ids = {t['test_id'] for t in tests if t.get('hospital_id') == hospital_id or t.get('hospital_id') is None}
            if fallback['test_id'] in allowed_test_ids:
                return [fallback]
            else:
                return []
        return [fallback]


async def make_routing_decision(diagnosis: dict, test_recommendations: List[dict], doctors: List[dict]) -> dict:
    """Make routing decision based on diagnosis and recommendations"""
    
    system_message = """You are a medical AI assistant. Based on the diagnosis and test recommendations, decide the best course of action. 
    Return ONLY JSON format with routing decision."""
    
    # Prepare doctor context
    doctor_context = "\n".join([
        f"ID: {doc['id']}, Name: {doc['name']}, Department: {doc['department']}, Tags: {', '.join(doc['tags'])}" 
        for doc in doctors
    ])
    
    prompt = f"""
    Diagnosis: {json.dumps(diagnosis)}
    Test Recommendations: {json.dumps(test_recommendations)}
    Available Doctors: {doctor_context}
    
    Make a routing decision in JSON format:
    {{
        "action_type": "book_appointment/book_tests/both/emergency",
        "reasoning": "Explanation of why this action is recommended",
        "recommended_tests": [list of test IDs to recommend],
        "recommended_doctors": [list of doctor IDs to recommend],
        "urgency_message": "Message about urgency and next steps"
    }}
    
    Decision guidelines:
    - Emergency: Send to ER or urgent care
    - Urgent: Book appointment + tests
    - Routine: Book tests first, then appointment if needed
    - Choose doctors based on diagnosis and symptoms
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        decision = robust_json_parse(response)
        
        # Filter recommended tests and doctors based on the decision
        if "recommended_tests" in decision:
            test_ids = decision["recommended_tests"]
            decision["recommended_tests"] = [
                test for test in test_recommendations 
                if test["test_id"] in test_ids
            ]
        
        if "recommended_doctors" in decision:
            doctor_ids = decision["recommended_doctors"]
            
            def safe_map_doctor(doc):
                """Safely map database doctor to DoctorRecommendation format"""
                # Handle different possible doctor structures
                doctor_id = doc.get("id", 0)
                doctor_name = doc.get("name", "Unknown Doctor")
                
                # Extract specialization from various possible fields
                specialization = (
                    doc.get("specialization") or 
                    doc.get("department") or 
                    (doc.get("department_name") if doc.get("department_name") else None) or
                    "General Medicine"
                )
                
                # Extract expertise/tags from various possible fields
                expertise = (
                    doc.get("expertise") or 
                    doc.get("tags") or 
                    doc.get("conditions") or 
                    [specialization]
                )
                
                # Ensure expertise is a list
                if isinstance(expertise, str):
                    expertise = [expertise]
                elif not isinstance(expertise, list):
                    expertise = [specialization]
                
                return {
                    "id": doctor_id,
                    "name": doctor_name,
                    "specialization": specialization,
                    "reason": f"Dr. {doctor_name.split()[-1] if ' ' in doctor_name else doctor_name} is recommended based on expertise in {specialization}",
                    "experience": f"Qualified medical professional specializing in {specialization}",
                    "expertise": expertise
                }
            
            decision["recommended_doctors"] = [
                safe_map_doctor(doc) for doc in doctors if doc.get("id") in doctor_ids
            ]
        
        return decision
    except Exception as e:
        print(f"Error making routing decision: {e}")
        
        # Create safe fallback doctors with proper structure
        safe_doctors = []
        for doc in doctors[:3]:
            safe_doctors.append({
                "id": doc.get("id", 0),
                "name": doc.get("name", "Available Doctor"),
                "specialization": doc.get("department") or doc.get("specialization") or "General Medicine",
                "reason": "Available for medical consultation and evaluation",
                "experience": "Qualified medical professional",
                "expertise": doc.get("tags", []) or doc.get("expertise", []) or ["General Medicine"]
            })
        
        return {
            "action_type": "book_appointment",
            "reasoning": "Based on your symptoms, a medical consultation is recommended",
            "recommended_tests": [],
            "recommended_doctors": safe_doctors,
            "urgency_message": "Please schedule an appointment with a healthcare provider for proper evaluation."
        }


async def process_diagnostic_answer(session_id: str, question_id: int, answer: str, doctors: List[dict]) -> dict:
    """Process a diagnostic answer and return next step"""
    
    if session_id not in diagnostic_sessions:
        raise ValueError("Invalid session ID")
    
    session = diagnostic_sessions[session_id]
    
    # Handle case where session exists but has no questions (e.g., due to LLM failure)
    if not session.get("questions") or len(session["questions"]) == 0:
        logger.warning(f"Session {session_id} has no questions, proceeding to diagnosis")
        
        try:
            # Use initial symptoms for diagnosis
            symptoms = session.get("initial_symptoms") or session.get("symptoms", "general symptoms")
            diagnosis = await generate_predictive_diagnosis(symptoms, {})
            test_recommendations = await generate_test_recommendations(diagnosis, symptoms)
            routing_decision = await make_routing_decision(diagnosis, test_recommendations, doctors)
            
            session["is_complete"] = True
            session["diagnosis"] = diagnosis
            session["decision"] = routing_decision
            
            return {
                "session_id": session_id,
                "current_question": None,
                "questions_remaining": 0,
                "diagnosis": diagnosis,
                "decision": routing_decision,
                "message": "Based on the information provided, here's my assessment:",
                "next_step": "review_diagnosis"
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback diagnosis: {e}")
            return {
                "session_id": session_id,
                "current_question": None,
                "questions_remaining": 0,
                "diagnosis": None,
                "decision": None,
                "message": "I'm having trouble processing your information right now. Please try again later.",
                "next_step": "provide_diagnosis"
            }
    
    # Initialize answers dict if not present
    if "answers" not in session:
        session["answers"] = {}
    
    session["answers"][question_id] = answer
    
    # Check if all questions are answered
    total_questions = len(session["questions"])
    answered_questions = len(session["answers"])
    
    if answered_questions < total_questions:
        # More questions to ask
        next_question = session["questions"][answered_questions]
        return {
            "session_id": session_id,
            "current_question": next_question,
            "questions_remaining": total_questions - answered_questions,
            "diagnosis": None,
            "decision": None,
            "message": f"Thank you for your answer. Here's the next question:",
            "next_step": "answer_question"
        }
    else:
        # All questions answered, generate diagnosis and routing with confidence
        symptoms = session.get("initial_symptoms") or session.get("symptoms", "general symptoms")
        
        try:
            diagnosis = await generate_predictive_diagnosis(symptoms, session["answers"])
            test_recommendations = await generate_test_recommendations(diagnosis, symptoms)
            routing_decision = await make_routing_decision(diagnosis, test_recommendations, doctors)
            
            # Calculate overall confidence from diagnosis
            overall_confidence = None
            if diagnosis and "diagnostic_confidence" in diagnosis:
                overall_confidence = diagnosis["diagnostic_confidence"]
            
            session["is_complete"] = True
            session["diagnosis"] = diagnosis
            session["decision"] = routing_decision
            
            return {
                "session_id": session_id,
                "current_question": None,
                "questions_remaining": 0,
                "diagnosis": diagnosis,
                "decision": routing_decision,
                "message": "Based on your symptoms and answers, here's our assessment:",
                "next_step": "review_diagnosis",
                "confidence": overall_confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating final diagnosis: {e}")
            return {
                "session_id": session_id,
                "current_question": None,
                "questions_remaining": 0,
                "diagnosis": None,
                "decision": None,
                "message": "Thank you for answering the questions. Let me provide what guidance I can.",
                "next_step": "provide_diagnosis"
            }


async def start_diagnostic_session(symptoms: str, doctors: List[dict]) -> dict:
    """Start a new diagnostic session"""
    
    session_id = str(uuid.uuid4())
    
    try:
        questions = await generate_diagnostic_questions(symptoms, session_id)
    except Exception as e:
        logger.error(f"Error generating diagnostic questions: {e}")
        questions = []
    
    # Store session data even if questions failed to generate
    diagnostic_sessions[session_id] = {
        "initial_symptoms": symptoms,
        "symptoms": symptoms,  # Keep both for compatibility
        "questions": questions or [],
        "answers": {},
        "current_question_index": 0,
        "doctors": doctors,
        "is_complete": False,
        "created_at": datetime.utcnow().isoformat()
    }
    
    if questions:
        first_question = questions[0]
        return {
            "session_id": session_id,
            "current_question": first_question,
            "questions_remaining": len(questions),
            "diagnosis": None,
            "decision": None,
            "message": "I understand your symptoms. To provide the best care, I need to ask you a few important questions:",
            "next_step": "answer_question"
        }
    else:
        # If question generation failed, go directly to diagnosis
        logger.warning(f"No questions generated for session {session_id}, proceeding to direct diagnosis")
        try:
            diagnosis = await generate_predictive_diagnosis(symptoms, {})
            test_recommendations = await generate_test_recommendations(diagnosis, symptoms)
            routing_decision = await make_routing_decision(diagnosis, test_recommendations, doctors)
            
            # Mark session as complete with direct diagnosis
            diagnostic_sessions[session_id]["is_complete"] = True
            diagnostic_sessions[session_id]["diagnosis"] = diagnosis
            diagnostic_sessions[session_id]["decision"] = routing_decision
            
            return {
                "session_id": session_id,
                "current_question": None,
                "questions_remaining": 0,
                "diagnosis": diagnosis,
                "decision": routing_decision,
                "message": "Based on your symptoms, here's my assessment:",
                "next_step": "review_diagnosis"
            }
        except Exception as e:
            logger.error(f"Error in fallback diagnosis: {e}")
            return {
                "session_id": session_id,
                "current_question": None,
                "questions_remaining": 0,
                "diagnosis": None,
                "decision": None,
                "message": "I understand your symptoms. Let me provide some general guidance.",
                "next_step": "provide_diagnosis"
            }

# Enhanced functions with patient history context
async def get_doctor_recommendations_with_history(
    symptoms: str, 
    doctors: list, 
    patient_context: str = None,
    session_id: str = None
):
    """Enhanced doctor recommendations that include patient history context"""
    # First check if this is a conversational input rather than symptoms
    if is_conversational_input(symptoms):
        return get_conversational_response()
    
    # Use original function if no context
    if not patient_context:
        return await get_doctor_recommendations(symptoms, doctors)
    
    if not GROQ_API_KEY:
        # Enhanced fallback with patient context consideration
        return await get_doctor_recommendations(symptoms, doctors)
    
    # Prepare doctor context for the prompt
    doctor_context = "\n".join([
        f"ID: {doc['id']}, Name: {doc['name']}, Department: {doc['department']}, Subdivision: {doc['subdivision']}, Tags: {', '.join(doc['tags'])}" 
        for doc in doctors
    ])
    
    print(f"Calling Groq API with patient history context for session: {session_id}")
    
    prompt = (
        f"You are a friendly and empathetic medical assistant helping patients find the right doctors. "
        f"PATIENT HISTORY CONTEXT:\n{patient_context}\n\n"
        f"CURRENT SYMPTOMS: {symptoms}\n\n"
        f"Available doctors:\n{doctor_context}\n\n"
        f"Based on both the patient's history and current symptoms, recommend exactly 3 most suitable doctors. "
        f"Consider any chronic conditions, previous diagnoses, and recent symptoms from their history. "
        f"Write in a caring, professional tone that acknowledges their medical history and current concerns. "
        f"For each doctor, explain their expertise and why they're specifically suitable considering both current symptoms and medical history. "
        f"Respond ONLY with a JSON array in this exact format:\n"
        f'[{{\n'
        f'  "id": number,\n'
        f'  "name": "string",\n'
        f'  "specialization": "string",\n'
        f'  "reason": "string explaining why this doctor is suitable considering both current symptoms and patient history",\n'
        f'  "experience": "string about doctor\'s experience",\n'
        f'  "expertise": ["array", "of", "expertise", "areas"]\n'
        f'}}]'
    )
    
    try:
        response = await call_groq_api(prompt)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response)
            if isinstance(parsed, list) and len(parsed) > 0:
                return response
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, extract JSON from the response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx]
            try:
                json.loads(json_str)  # Validate JSON
                return json_str
            except json.JSONDecodeError:
                pass
        
        # If all parsing fails, use fallback
        return await get_doctor_recommendations(symptoms, doctors)
        
    except Exception as e:
        print(f"Error in Groq API call: {e}")
        return await get_doctor_recommendations(symptoms, doctors)

async def start_diagnostic_session_with_history(
    symptoms: str, 
    doctors: List[dict], 
    patient_context: str = None,
    session_id: str = None
) -> dict:
    """Start a diagnostic session with patient history context"""
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Generate initial diagnostic questions with context
    questions = await generate_diagnostic_questions_with_history(symptoms, session_id, patient_context)
    
    # Store session data
    diagnostic_sessions[session_id] = {
        "symptoms": symptoms,
        "patient_context": patient_context,
        "questions": questions,
        "answers": {},
        "current_question_index": 0,
        "doctors": doctors
    }
    
    if questions:
        return {
            "session_id": session_id,
            "current_question": questions[0],
            "questions_remaining": len(questions),
            "message": "I'd like to ask you a few questions to better understand your condition and medical history.",
            "next_step": "answer_question"
        }
    else:
        # If no questions generated, proceed directly to diagnosis
        diagnosis = await generate_predictive_diagnosis_with_history(symptoms, {}, patient_context)
        return {
            "session_id": session_id,
            "diagnosis": diagnosis,
            "message": "Based on your symptoms and medical history, here's my assessment.",
            "next_step": "view_recommendations"
        }

async def generate_diagnostic_questions_with_history(
    symptoms: str, 
    session_id: str, 
    patient_context: str = None
) -> List[dict]:
    """Generate diagnostic questions considering patient history"""
    
    if not GROQ_API_KEY:
        # Fallback questions
        return [
            {
                "question_id": 1,
                "question": "How long have you been experiencing these symptoms?",
                "question_type": "duration",
                "options": ["Less than 24 hours", "1-3 days", "1 week", "More than a week"],
                "required": True
            },
            {
                "question_id": 2,
                "question": "On a scale of 1-10, how would you rate the severity of your symptoms?",
                "question_type": "severity",
                "options": ["1-3 (Mild)", "4-6 (Moderate)", "7-8 (Severe)", "9-10 (Extremely severe)"],
                "required": True
            }
        ]
    
    context_prompt = f"PATIENT HISTORY:\n{patient_context}\n\n" if patient_context else ""
    
    prompt = (
        f"You are a medical diagnostic assistant. {context_prompt}"
        f"A patient is presenting with: {symptoms}\n\n"
        f"Generate 3-5 targeted diagnostic questions that will help determine the best course of action. "
        f"Consider the patient's medical history when forming questions - avoid asking about things already known. "
        f"Focus on questions that would help differentiate between possible conditions and determine urgency. "
        f"Each question should be clear, specific, and help narrow down the diagnosis.\n\n"
        f"Respond with a JSON array in this exact format:\n"
        f'[{{\n'
        f'  "question_id": 1,\n'
        f'  "question": "Your question here?",\n'
        f'  "question_type": "duration|severity|location|frequency|triggers|associated",\n'
        f'  "options": ["option1", "option2", "option3", "option4"],\n'
        f'  "required": true\n'
        f'}}]'
    )
    
    try:
        response = await call_groq_api(prompt)
        
        # Try to parse as JSON
        try:
            questions = json.loads(response)
            if isinstance(questions, list) and len(questions) > 0:
                return questions
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, extract JSON from response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx]
            try:
                questions = json.loads(json_str)
                if isinstance(questions, list) and len(questions) > 0:
                    return questions
            except json.JSONDecodeError:
                pass
        
        # Fallback questions if parsing fails
        return [
            {
                "question_id": 1,
                "question": "How long have you been experiencing these symptoms?",
                "question_type": "duration",
                "options": ["Less than 24 hours", "1-3 days", "1 week", "More than a week"],
                "required": True
            },
            {
                "question_id": 2,
                "question": "On a scale of 1-10, how would you rate the severity?",
                "question_type": "severity", 
                "options": ["1-3 (Mild)", "4-6 (Moderate)", "7-8 (Severe)", "9-10 (Extremely severe)"],
                "required": True
            }
        ]
        
    except Exception as e:
        print(f"Error generating diagnostic questions: {e}")
        return [
            {
                "question_id": 1,
                "question": "How long have you been experiencing these symptoms?",
                "question_type": "duration",
                "options": ["Less than 24 hours", "1-3 days", "1 week", "More than a week"],
                "required": True
            }
        ]

async def generate_predictive_diagnosis_with_history(
    symptoms: str, 
    answers: dict, 
    patient_context: str = None
) -> dict:
    """Generate predictive diagnosis considering patient history"""
    
    if not GROQ_API_KEY:
        # Enhanced fallback with context consideration
        urgency = "medium"
        if any(word in symptoms.lower() for word in ["chest pain", "severe", "emergency", "urgent"]):
            urgency = "high"
        elif any(word in symptoms.lower() for word in ["mild", "slight", "minor"]):
            urgency = "low"
            
        return {
            "possible_conditions": ["General medical condition", "Symptoms requiring evaluation"],
            "confidence_level": "moderate",
            "urgency_level": urgency,
            "recommended_action": "medical consultation",
            "explanation": f"Based on your symptoms and medical history, a medical consultation is recommended for proper evaluation."
        }
    
    # Format answers for the prompt
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()]) if answers else "No additional answers provided."
    context_prompt = f"PATIENT MEDICAL HISTORY:\n{patient_context}\n\n" if patient_context else ""
    
    prompt = (
        f"You are an experienced medical diagnostic assistant. {context_prompt}"
        f"CURRENT SYMPTOMS: {symptoms}\n\n"
        f"DIAGNOSTIC ANSWERS:\n{answers_text}\n\n"
        f"Based on the patient's current symptoms, their medical history, and diagnostic answers, provide a preliminary assessment. "
        f"Consider any chronic conditions, previous diagnoses, and how they might relate to current symptoms. "
        f"Be thorough but acknowledge the limitations of remote diagnosis.\n\n"
        f"Respond with JSON in this exact format:\n"
        f'{{\n'
        f'  "possible_conditions": ["list of 2-4 possible conditions"],\n'
        f'  "confidence_level": "low|moderate|high",\n'
        f'  "urgency_level": "low|medium|high|urgent",\n'
        f'  "recommended_action": "appointment|test|emergency",\n'
        f'  "explanation": "detailed explanation considering patient history and current symptoms"\n'
        f'}}'
    )
    
    try:
        response = await call_groq_api(prompt)
        
        # Try to parse as JSON
        try:
            diagnosis = json.loads(response)
            if isinstance(diagnosis, dict) and "possible_conditions" in diagnosis:
                return diagnosis
        except json.JSONDecodeError:
            pass
        
        # Extract JSON from response if needed
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx]
            try:
                diagnosis = json.loads(json_str)
                if isinstance(diagnosis, dict) and "possible_conditions" in diagnosis:
                    return diagnosis
            except json.JSONDecodeError:
                pass
        
        # Fallback response
        return {
            "possible_conditions": ["Condition requiring medical evaluation"],
            "confidence_level": "moderate",
            "urgency_level": "medium",
            "recommended_action": "appointment",
            "explanation": f"Based on your symptoms and medical history, I recommend scheduling an appointment for proper evaluation."
        }
        
    except Exception as e:
        print(f"Error generating diagnosis: {e}")
        return {
            "possible_conditions": ["Medical condition requiring evaluation"],
            "confidence_level": "low",
            "urgency_level": "medium", 
            "recommended_action": "appointment",
            "explanation": f"I recommend consulting with a healthcare provider about your symptoms."
        }