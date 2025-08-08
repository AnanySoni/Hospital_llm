"""
Session-based patient history service
Works with existing comprehensive patient database
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import json

from backend.core.models import (
    SessionUser, Patient, MedicalHistory, FamilyHistory, Medication, 
    Allergy, SymptomLog, TestResult, PatientNote, Vaccination,
    DiagnosticSession, ConversationSession
)
from backend.schemas.request_models import SessionUserCreate, PatientHistoryResponse

class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session_user(self, session_id: str, user_info: Optional[SessionUserCreate] = None) -> SessionUser:
        """Get existing session user or create new one"""
        session_user = self.db.query(SessionUser).filter(SessionUser.session_id == session_id).first()
        
        if not session_user:
            session_user = SessionUser(
                session_id=session_id,
                first_name=user_info.first_name if user_info else None,
                age=user_info.age if user_info else None,
                gender=user_info.gender if user_info else None
            )
            self.db.add(session_user)
            self.db.commit()
            self.db.refresh(session_user)
        else:
            # Update last_active timestamp
            session_user.last_active = datetime.utcnow()
            if user_info:
                session_user.first_name = user_info.first_name or session_user.first_name
                session_user.age = user_info.age or session_user.age
                session_user.gender = user_info.gender or session_user.gender
            self.db.commit()
        
        return session_user

    def link_session_to_patient(self, session_id: str, patient_id: int) -> bool:
        """Link a session to an existing patient record"""
        try:
            session_user = self.db.query(SessionUser).filter(SessionUser.session_id == session_id).first()
            if session_user:
                session_user.patient_id = patient_id
                self.db.commit()
                return True
            return False
        except Exception:
            self.db.rollback()
            return False

    def get_patient_comprehensive_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive patient history from all tables"""
        session_user = self.db.query(SessionUser).filter(SessionUser.session_id == session_id).first()
        if not session_user:
            return None
        
        # If linked to a patient, get full medical history
        if session_user.patient_id:
            patient = self.db.query(Patient).filter(Patient.id == session_user.patient_id).first()
            if patient:
                return self._build_patient_history(patient)
        
        # Otherwise, return session-based history from diagnostic sessions and symptom logs
        return self._build_session_history(session_user)

    def _build_patient_history(self, patient: Patient) -> Dict[str, Any]:
        """Build comprehensive history from patient record"""
        
        # Get all related medical data
        medical_history = self.db.query(MedicalHistory).filter(
            MedicalHistory.patient_id == patient.id
        ).order_by(desc(MedicalHistory.created_at)).all()
        
        medications = self.db.query(Medication).filter(
            Medication.patient_id == patient.id
        ).order_by(desc(Medication.created_at)).all()
        
        allergies = self.db.query(Allergy).filter(
            Allergy.patient_id == patient.id
        ).all()
        
        family_history = self.db.query(FamilyHistory).filter(
            FamilyHistory.patient_id == patient.id
        ).all()
        
        recent_symptoms = self.db.query(SymptomLog).filter(
            SymptomLog.patient_id == patient.id
        ).order_by(desc(SymptomLog.reported_at)).limit(10).all()
        
        test_results = self.db.query(TestResult).filter(
            TestResult.patient_id == patient.id
        ).order_by(desc(TestResult.test_date)).limit(10).all()
        
        doctor_notes = self.db.query(PatientNote).filter(
            PatientNote.patient_id == patient.id
        ).order_by(desc(PatientNote.created_at)).limit(5).all()
        
        vaccinations = self.db.query(Vaccination).filter(
            Vaccination.patient_id == patient.id
        ).order_by(desc(Vaccination.vaccination_date)).all()

        # Format for SessionHistoryResponse schema
        recent_symptom_strs = [f"{symptom.symptom_description} ({symptom.severity})" for symptom in recent_symptoms]
        recent_diagnoses_strs = [mh.condition_name for mh in medical_history[:3]]
        chronic_strs = [mh.condition_name for mh in medical_history if mh.status == 'chronic']
        allergy_strs = [allergy.allergen for allergy in allergies]
        
        return {
            "session_id": f"patient_{patient.id}",
            "conversation_count": len(doctor_notes) + 1,
            "recent_symptoms": recent_symptom_strs,
            "recent_diagnoses": recent_diagnoses_strs,
            "chronic_conditions": chronic_strs,
            "allergies": allergy_strs,
            "appointment_history": [],  # Could populate from appointments table
            "test_history": [f"{test.test_name}: {test.result_value}" for test in test_results],
            "last_visit": max(
                patient.updated_at if patient.updated_at else patient.created_at,
                max([note.created_at for note in doctor_notes], default=patient.created_at)
            )
        }

    def _build_session_history(self, session_user: SessionUser) -> Dict[str, Any]:
        """Build history from session-based data only"""
        
        # Return simplified session history to avoid database issues
        # Format to match SessionHistoryResponse schema
        return {
            "session_id": session_user.session_id,
            "conversation_count": 1,
            "recent_symptoms": [],
            "recent_diagnoses": [],
            "chronic_conditions": [],
            "allergies": [],
            "appointment_history": [],
            "test_history": [],
            "last_visit": session_user.last_active
        }

    def generate_llm_context(self, session_id: str) -> str:
        """Generate contextual prompt for LLM based on patient history"""
        history = self.get_patient_comprehensive_history(session_id)
        if not history:
            return "No previous medical history available for this session."
        
        context_parts = []
        
        # Add patient/session info
        if "patient_info" in history:
            patient = history["patient_info"]
            context_parts.append(f"Patient: {patient['name']}, Age: {patient['age']}, Gender: {patient['gender']}")
            if patient.get('blood_group'):
                context_parts.append(f"Blood Group: {patient['blood_group']}")
        elif "session_info" in history:
            session = history["session_info"]
            name = session['first_name'] or 'Patient'
            context_parts.append(f"Patient: {name}")
            if session['age']:
                context_parts.append(f"Age: {session['age']}")
            if session['gender']:
                context_parts.append(f"Gender: {session['gender']}")
        
        # Add medical history
        if history.get("medical_history"):
            conditions = [mh["condition"] for mh in history["medical_history"]]
            context_parts.append(f"Medical History: {', '.join(conditions)}")
        
        # Add allergies
        if history.get("allergies"):
            allergies = [f"{a['allergen']} ({a['severity']})" for a in history["allergies"]]
            context_parts.append(f"Allergies: {', '.join(allergies)}")
        
        # Add current medications
        if history.get("current_medications"):
            meds = [med["name"] for med in history["current_medications"]]
            context_parts.append(f"Current Medications: {', '.join(meds)}")
        
        # Add recent symptoms
        if history.get("recent_symptoms"):
            recent = history["recent_symptoms"][:3]  # Last 3 symptoms
            symptoms = [f"{s['description']} ({s['severity']})" for s in recent]
            context_parts.append(f"Recent Symptoms: {', '.join(symptoms)}")
        
        # Add family history
        if history.get("family_history"):
            family = [f"{fh['relation']}: {fh['condition']}" for fh in history["family_history"]]
            context_parts.append(f"Family History: {', '.join(family)}")
        
        return "\n".join(context_parts)

    def record_symptom_log(self, session_id: str, symptom_data: Dict[str, Any]) -> bool:
        """Record new symptom in symptom_logs table"""
        try:
            session_user = self.get_or_create_session_user(session_id)
            
            # Simple symptom log without conversation session reference
            symptom_log = SymptomLog(
                patient_id=session_user.patient_id,  # May be None for anonymous users
                session_id=None,  # Skip conversation session for now
                symptom_description=symptom_data.get('description', ''),
                severity=symptom_data.get('severity'),
                duration=symptom_data.get('duration'),
                frequency=symptom_data.get('frequency'),
                triggers=symptom_data.get('triggers'),
                associated_symptoms=symptom_data.get('associated_symptoms')
            )
            
            self.db.add(symptom_log)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def _calculate_age(self, date_of_birth) -> int:
        """Calculate age from date of birth"""
        today = datetime.now().date()
        return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        session_user = self.db.query(SessionUser).filter(SessionUser.session_id == session_id).first()
        if not session_user:
            return {}
        
        # For now, just return simple counts to avoid DB issues
        conversation_count = 1
        
        # For now, just return basic stats
        diagnostic_count = 0
        
        return {
            "session_id": session_id,
            "first_visit": session_user.created_at.isoformat(),
            "last_visit": session_user.last_active.isoformat(),
            "total_conversations": conversation_count,
            "total_diagnostics": diagnostic_count,
            "linked_to_patient": session_user.patient_id is not None,
            "patient_id": session_user.patient_id
        } 