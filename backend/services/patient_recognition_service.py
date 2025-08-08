"""
Patient Recognition Service
Handles phone-based patient identification, symptom categorization, and smart context management
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from backend.core.models import PatientProfile, SymptomHistory, VisitHistory, ConversationSession
from backend.utils.llm_utils import call_groq_api


class PatientRecognitionService:
    
    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """Normalize phone number for consistent storage and lookup (Indian +91 format)"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle common formats
        if len(digits) == 10:
            # Indian format without country code (10 digits)
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith('91'):
            # Indian format with country code - validate mobile part
            mobile_part = digits[2:]
            if mobile_part.startswith(('6', '7', '8', '9')):
                return f"+{digits}"
            else:
                # Invalid Indian mobile number - treat as international
                return f"+{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            # US format with country code (keep as is for international users)
            return f"+{digits}"
        elif len(digits) == 13 and digits.startswith('91'):
            # Indian format with extra digit - take last 12
            return f"+{digits[-12:]}"
        else:
            # Default to Indian format for other lengths
            if len(digits) >= 10:
                # Take last 10 digits and add +91
                return f"+91{digits[-10:]}"
            else:
                # Too short - assume international format
                return f"+{digits}"
    
    @staticmethod
    def find_or_create_patient_profile(
        db: Session, 
        phone_number: str, 
        first_name: str = None,
        family_member_type: str = "self"
    ) -> Tuple[PatientProfile, bool]:
        """
        Find existing patient or create new one
        Returns (PatientProfile, is_new_patient)
        """
        normalized_phone = PatientRecognitionService.normalize_phone_number(phone_number)
        
        # Try to find existing patient
        existing_patient = db.query(PatientProfile).filter(
            PatientProfile.phone_number == normalized_phone
        ).first()
        
        if existing_patient:
            # Update last visit date
            existing_patient.last_visit_date = datetime.now()
            existing_patient.total_visits += 1
            db.commit()
            db.refresh(existing_patient)
            return existing_patient, False
        
        # Create new patient profile
        if not first_name:
            first_name = "Patient"  # Default name
            
        new_patient = PatientProfile(
            phone_number=normalized_phone,
            first_name=first_name,
            family_member_type=family_member_type,
            last_visit_date=datetime.now(),
            total_visits=1,
            chronic_conditions="[]",  # Empty JSON array
            allergies="[]",  # Empty JSON array
            preferred_doctors="[]"  # Empty JSON array
        )
        
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        return new_patient, True
    
    @staticmethod
    async def categorize_symptoms(symptoms: str) -> str:
        """Categorize symptoms into main categories for tracking"""
        try:
            prompt = f"""
            Categorize the following symptoms into ONE primary category. 
            Choose from: chest_pain, headache, stomach_issues, respiratory, musculoskeletal, 
            skin_conditions, mental_health, cardiovascular, neurological, gynecological, 
            pediatric, emergency, general_checkup, other

            Symptoms: {symptoms}

            Respond with ONLY the category name, nothing else.
            """
            
            category = await call_groq_api(prompt)
            if category and category.strip():
                return category.strip().lower()
            else:
                return "other"
                
        except Exception:
            # Fallback categorization based on keywords
            symptoms_lower = symptoms.lower()
            if any(word in symptoms_lower for word in ['chest', 'heart', 'cardiac']):
                return "chest_pain"
            elif any(word in symptoms_lower for word in ['head', 'migraine']):
                return "headache"
            elif any(word in symptoms_lower for word in ['stomach', 'abdomen', 'nausea']):
                return "stomach_issues"
            elif any(word in symptoms_lower for word in ['cough', 'breathing', 'lung']):
                return "respiratory"
            else:
                return "other"
    
    @staticmethod
    async def check_symptom_relatedness(
        db: Session,
        patient_profile: PatientProfile,
        current_symptoms: str,
        current_category: str
    ) -> Dict[str, any]:
        """
        Check if current symptoms are related to previous visits
        Returns analysis with recommendations
        """
        try:
            # Get recent symptom history (last 6 months)
            cutoff_date = datetime.now() - timedelta(days=180)
            recent_history = db.query(SymptomHistory).filter(
                and_(
                    SymptomHistory.patient_profile_id == patient_profile.id,
                    SymptomHistory.visit_date >= cutoff_date
                )
            ).order_by(desc(SymptomHistory.visit_date)).limit(5).all()
            
            if not recent_history:
                return {
                    "is_related": False,
                    "relationship_type": "new_concern",
                    "message": f"Welcome back, {patient_profile.first_name}! I see you have a new concern today. What's bothering you?",
                    "reference_previous": False,
                    "relevant_history": None
                }
            
            # Check for same category in recent history
            same_category_recent = [h for h in recent_history if h.symptom_category == current_category]
            
            if same_category_recent:
                latest_same = same_category_recent[0]
                days_since = (datetime.now() - latest_same.visit_date).days
                
                if days_since <= 30:  # Recent issue
                    return {
                        "is_related": True,
                        "relationship_type": "follow_up",
                        "message": f"Welcome back, {patient_profile.first_name}! I see you're here about {current_category.replace('_', ' ')} again. Is this related to your visit {days_since} days ago?",
                        "reference_previous": True,
                        "relevant_history": {
                            "previous_symptoms": latest_same.symptoms_text,
                            "previous_diagnosis": latest_same.diagnosis_result,
                            "days_since": days_since,
                            "urgency_level": latest_same.urgency_level
                        }
                    }
                else:  # Same category but older
                    return {
                        "is_related": False,
                        "relationship_type": "similar_new",
                        "message": f"Welcome back, {patient_profile.first_name}! I see you have {current_category.replace('_', ' ')} concerns. Let's focus on your current symptoms.",
                        "reference_previous": False,
                        "relevant_history": {
                            "note": f"Patient has history of {current_category.replace('_', ' ')} from {days_since} days ago"
                        }
                    }
            
            # Different category - check for potential connections
            chronic_conditions = json.loads(patient_profile.chronic_conditions or "[]")
            if chronic_conditions:
                return {
                    "is_related": False,
                    "relationship_type": "new_with_history",
                    "message": f"Welcome back, {patient_profile.first_name}! I'll keep your medical history in mind as we discuss your {current_category.replace('_', ' ')} concerns.",
                    "reference_previous": False,
                    "relevant_history": {
                        "chronic_conditions": chronic_conditions,
                        "note": "Consider chronic conditions in diagnosis"
                    }
                }
            
            return {
                "is_related": False,
                "relationship_type": "new_concern",
                "message": f"Welcome back, {patient_profile.first_name}! I see you have a new concern today. What's bothering you?",
                "reference_previous": False,
                "relevant_history": None
            }
            
        except Exception as e:
            print(f"Error checking symptom relatedness: {e}")
            return {
                "is_related": False,
                "relationship_type": "new_concern", 
                "message": f"Welcome back, {patient_profile.first_name}! What's bothering you today?",
                "reference_previous": False,
                "relevant_history": None
            }
    
    @staticmethod
    def get_enhanced_llm_context(
        patient_profile: PatientProfile,
        relatedness_analysis: Dict[str, any]
    ) -> str:
        """
        Generate enhanced context for LLM based on patient history and current session
        """
        context_parts = []
        
        # Basic patient info
        context_parts.append(f"Patient: {patient_profile.first_name}")
        if patient_profile.age:
            context_parts.append(f"Age: {patient_profile.age}")
        if patient_profile.gender:
            context_parts.append(f"Gender: {patient_profile.gender}")
        
        # Visit history
        context_parts.append(f"Total visits: {patient_profile.total_visits}")
        if patient_profile.last_visit_date and patient_profile.total_visits > 1:
            last_visit = patient_profile.last_visit_date
            context_parts.append(f"Last visit: {last_visit.strftime('%Y-%m-%d')}")
        
        # Chronic conditions and allergies
        chronic_conditions = json.loads(patient_profile.chronic_conditions or "[]")
        if chronic_conditions:
            context_parts.append(f"Chronic conditions: {', '.join(chronic_conditions)}")
        
        allergies = json.loads(patient_profile.allergies or "[]")
        if allergies:
            context_parts.append(f"Known allergies: {', '.join(allergies)}")
        
        # Relevant history from analysis
        if relatedness_analysis.get("relevant_history"):
            history = relatedness_analysis["relevant_history"]
            if history.get("previous_symptoms"):
                context_parts.append(f"Recent related symptoms: {history['previous_symptoms']}")
            if history.get("previous_diagnosis"):
                context_parts.append(f"Previous diagnosis: {history['previous_diagnosis']}")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def save_symptom_history(
        db: Session,
        patient_profile: PatientProfile,
        symptoms: str,
        symptom_category: str,
        diagnosis_result: str = None,
        urgency_level: str = None,
        appointment_id: int = None,
        test_booking_id: str = None
    ):
        """Save symptom history for future reference"""
        try:
            symptom_history = SymptomHistory(
                patient_profile_id=patient_profile.id,
                symptom_category=symptom_category,
                symptoms_text=symptoms,
                diagnosis_result=diagnosis_result,
                urgency_level=urgency_level,
                related_appointment_id=appointment_id,
                related_test_booking_id=test_booking_id
            )
            
            db.add(symptom_history)
            
            # Update patient profile
            patient_profile.last_visit_symptoms = symptoms
            patient_profile.last_visit_date = datetime.now()
            
            db.commit()
            
        except Exception as e:
            print(f"Error saving symptom history: {e}")
            db.rollback()
    
    @staticmethod
    def save_visit_history(
        db: Session,
        patient_profile: PatientProfile,
        visit_type: str,
        primary_symptoms: str,
        outcome: str,
        doctors_consulted: List[str] = None,
        tests_taken: List[str] = None,
        session_data: Dict = None
    ):
        """Save complete visit history"""
        try:
            visit_history = VisitHistory(
                patient_profile_id=patient_profile.id,
                visit_type=visit_type,
                primary_symptoms=primary_symptoms,
                doctors_consulted=json.dumps(doctors_consulted or []),
                tests_taken=json.dumps(tests_taken or []),
                outcome=outcome,
                session_data=json.dumps(session_data or {})
            )
            
            db.add(visit_history)
            db.commit()
            
        except Exception as e:
            print(f"Error saving visit history: {e}")
            db.rollback()
    
    @staticmethod
    def handle_family_member_detection(
        db: Session,
        phone_number: str,
        patient_name: str,
        conversation_context: str
    ) -> Dict[str, any]:
        """
        Detect if this is a family member booking for someone else
        """
        try:
            # Look for family indicators in name or context
            family_indicators = [
                'my son', 'my daughter', 'my child', 'my mother', 'my father',
                'my husband', 'my wife', 'my sister', 'my brother'
            ]
            
            context_lower = conversation_context.lower()
            name_lower = patient_name.lower()
            
            family_type = "self"
            is_family_booking = False
            
            for indicator in family_indicators:
                if indicator in context_lower or indicator in name_lower:
                    is_family_booking = True
                    if 'son' in indicator or 'daughter' in indicator or 'child' in indicator:
                        family_type = "child"
                    elif 'mother' in indicator or 'father' in indicator:
                        family_type = "parent"
                    elif 'husband' in indicator or 'wife' in indicator:
                        family_type = "spouse"
                    elif 'sister' in indicator or 'brother' in indicator:
                        family_type = "sibling"
                    break
            
            return {
                "is_family_booking": is_family_booking,
                "family_member_type": family_type,
                "primary_contact_phone": phone_number if is_family_booking else None,
                "message": "Are you booking for yourself or a family member?" if is_family_booking else None
            }
            
        except Exception as e:
            print(f"Error detecting family member: {e}")
            return {
                "is_family_booking": False,
                "family_member_type": "self",
                "primary_contact_phone": None,
                "message": None
            } 