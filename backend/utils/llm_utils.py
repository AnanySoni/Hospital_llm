import os
import httpx
import json
import uuid
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

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

async def get_doctor_recommendations(symptoms: str, doctors: list):
    # First check if this is a conversational input rather than symptoms
    if is_conversational_input(symptoms):
        return get_conversational_response()
    
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

async def call_groq_api(prompt: str, system_message: str = None) -> str:
    """Generic function to call Groq API"""
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
    
    async with httpx.AsyncClient() as client:
        response = await client.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Clean the response to extract JSON
        content = content.strip()
        
        # Try to find JSON content between ```json and ``` or [ and ]
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif content.startswith("[") and content.endswith("]"):
            # Already looks like JSON array
            pass
        elif content.startswith("{") and content.endswith("}"):
            # Already looks like JSON object
            pass
        else:
            # Try to find JSON-like content
            import re
            json_match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
        
        return content


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
        questions = json.loads(response)
        
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
    """Generate predictive diagnosis based on symptoms and answers"""
    
    system_message = """You are an expert medical AI assistant. Based on symptoms and patient answers, provide a predictive diagnosis. 
    Be conservative and always recommend professional medical evaluation. Return ONLY JSON format."""
    
    # Combine symptoms and answers
    context = f"Symptoms: {symptoms}\n"
    for q_id, answer in answers.items():
        context += f"Answer {q_id}: {answer}\n"
    
    prompt = f"""
    {context}
    
    Provide a predictive diagnosis in JSON format:
    {{
        "possible_conditions": ["condition1", "condition2"],
        "confidence_level": "High/Medium/Low",
        "urgency_level": "Emergency/Urgent/Routine",
        "recommended_action": "Immediate action needed",
        "explanation": "Detailed explanation of the diagnosis"
    }}
    
    Important guidelines:
    - Always err on the side of caution
    - If symptoms suggest emergency, mark as Emergency
    - Be specific about possible conditions
    - Explain why each condition is possible
    """
    
    try:
        response = await call_groq_api(prompt, system_message)
        return json.loads(response)
    except Exception as e:
        print(f"Error generating diagnosis: {e}")
        return {
            "possible_conditions": ["Medical evaluation needed"],
            "confidence_level": "Low",
            "urgency_level": "Routine",
            "recommended_action": "Schedule a consultation with a healthcare provider",
            "explanation": "Based on your symptoms, a professional medical evaluation is recommended to determine the exact cause and appropriate treatment."
        }


async def generate_test_recommendations(diagnosis: dict, symptoms: str) -> List[dict]:
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
        return json.loads(response)
    except Exception as e:
        print(f"Error generating test recommendations: {e}")
        return [
            {
                "test_id": "general_blood",
                "test_name": "General Blood Panel",
                "test_category": "Blood Test",
                "description": "Basic blood work to assess overall health",
                "urgency": "Within week",
                "cost_estimate": "$100-200",
                "preparation_required": "Fasting for 8-12 hours",
                "why_recommended": "To establish baseline health markers and identify any abnormalities"
            }
        ]


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
        decision = json.loads(response)
        
        # Filter recommended tests and doctors based on the decision
        if "recommended_tests" in decision:
            test_ids = decision["recommended_tests"]
            decision["recommended_tests"] = [
                test for test in test_recommendations 
                if test["test_id"] in test_ids
            ]
        
        if "recommended_doctors" in decision:
            doctor_ids = decision["recommended_doctors"]
            decision["recommended_doctors"] = [
                {
                    "id": doc["id"],
                    "name": doc["name"],
                    "specialization": doc["department"],
                    "reason": f"Recommended for your condition based on expertise in {doc['department']}",
                    "experience": f"Experienced in {doc['department']}",
                    "expertise": doc.get("tags", [doc["department"]])
                }
                for doc in doctors if doc["id"] in doctor_ids
            ]
        
        return decision
    except Exception as e:
        print(f"Error making routing decision: {e}")
        return {
            "action_type": "book_appointment",
            "reasoning": "Based on your symptoms, a medical consultation is recommended",
            "recommended_tests": [],
            "recommended_doctors": doctors[:3],
            "urgency_message": "Please schedule an appointment with a healthcare provider for proper evaluation."
        }


async def process_diagnostic_answer(session_id: str, question_id: int, answer: str, doctors: List[dict]) -> dict:
    """Process a diagnostic answer and return next step"""
    
    if session_id not in diagnostic_sessions:
        raise ValueError("Invalid session ID")
    
    session = diagnostic_sessions[session_id]
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
        # All questions answered, generate diagnosis and routing
        diagnosis = await generate_predictive_diagnosis(session["initial_symptoms"], session["answers"])
        test_recommendations = await generate_test_recommendations(diagnosis, session["initial_symptoms"])
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
            "message": "Based on your symptoms and answers, here's our assessment:",
            "next_step": "review_diagnosis"
        }


async def start_diagnostic_session(symptoms: str, doctors: List[dict]) -> dict:
    """Start a new diagnostic session"""
    
    session_id = str(uuid.uuid4())
    questions = await generate_diagnostic_questions(symptoms, session_id)
    
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
        raise Exception("Failed to generate diagnostic questions") 