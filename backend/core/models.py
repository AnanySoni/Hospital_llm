from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ForeignKey, ARRAY, DateTime, func, Float, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import json

Base = declarative_base()

# Existing schema models (matching user's database)
class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    name = Column(String(100), nullable=False)
    subdivisions = relationship('Subdivision', back_populates='department')
    doctors = relationship('Doctor', back_populates='department')
    hospital = relationship('Hospital', back_populates='departments')
    __table_args__ = (
        Index('ix_departments_hospital_id_id', 'hospital_id', 'id'),
    )

class Subdivision(Base):
    __tablename__ = 'subdivisions'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    department_id = Column(Integer, ForeignKey('departments.id'))
    name = Column(String(100), nullable=False)
    department = relationship('Department', back_populates='subdivisions')
    doctors = relationship('Doctor', back_populates='subdivision')
    hospital = relationship('Hospital', back_populates='subdivisions')
    __table_args__ = (
        Index('ix_subdivisions_hospital_id_id', 'hospital_id', 'id'),
    )

class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Will be set via migration
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True, unique=True)
    department_id = Column(Integer, ForeignKey('departments.id'))
    subdivision_id = Column(Integer, ForeignKey('subdivisions.id'))
    profile = Column(Text)
    tags = Column(ARRAY(String))
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    token_expiry = Column(Date, nullable=True)
    phone_number = Column(String(20), nullable=True)
    department = relationship('Department', back_populates='doctors')
    subdivision = relationship('Subdivision', back_populates='doctors')
    hospital = relationship('Hospital', back_populates='doctors')
    availabilities = relationship('DoctorAvailability', back_populates='doctor')
    appointments = relationship('Appointment', back_populates='doctor')
    medications = relationship('Medication', back_populates='prescribing_doctor')
    patient_notes = relationship('PatientNote', back_populates='doctor')
    test_results = relationship('TestResult', back_populates='doctor')
    __table_args__ = (
        Index('ix_doctors_hospital_id_id', 'hospital_id', 'id'),
    )

class DoctorAvailability(Base):
    __tablename__ = 'doctor_availability'
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=False)
    is_booked = Column(Boolean, default=False)
    doctor = relationship('Doctor', back_populates='availabilities')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    name = Column(String(100))
    contact_info = Column(String(100))
    phone_number = Column(String(20))
    age = Column(Integer)
    medical_history = Column(Text)
    appointments = relationship('Appointment', back_populates='user')
    # diagnostic_sessions = relationship('DiagnosticSession', back_populates='user')  # Removed for new adaptive model
    test_bookings = relationship('TestBooking', back_populates='user')
    hospital = relationship('Hospital', back_populates='users')
    conversation_sessions = relationship('ConversationSession', back_populates='user')
    __table_args__ = (
        Index('ix_users_hospital_id_id', 'hospital_id', 'id'),
    )

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Will be set via migration
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    blood_group = Column(String(5))
    email = Column(String(100))
    phone = Column(String(20), nullable=False)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    address = Column(Text)
    insurance_provider = Column(String(100))
    insurance_number = Column(String(50))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    hospital = relationship('Hospital', back_populates='patients')
    medical_history = relationship('MedicalHistory', back_populates='patient')
    medications = relationship('Medication', back_populates='patient')
    allergies = relationship('Allergy', back_populates='patient')
    family_history = relationship('FamilyHistory', back_populates='patient')
    test_results = relationship('TestResult', back_populates='patient')
    vaccinations = relationship('Vaccination', back_populates='patient')
    patient_notes = relationship('PatientNote', back_populates='patient')
    symptoms = relationship('SymptomLog', back_populates='patient')
    test_bookings = relationship('TestBooking', back_populates='patient')
    session_users = relationship('SessionUser', back_populates='patient')
    # diagnostic_sessions = relationship('DiagnosticSession', back_populates='patient')  # Removed for new adaptive model
    __table_args__ = (
        Index('ix_patients_hospital_id_id', 'hospital_id', 'id'),
    )

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Will be set via migration
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=False)
    status = Column(String(20), default='booked')
    notes = Column(Text)
    patient_name = Column(String(100))
    phone_number = Column(String(20))
    user = relationship('User', back_populates='appointments')
    doctor = relationship('Doctor', back_populates='appointments')
    hospital = relationship('Hospital', back_populates='appointments')
    __table_args__ = (
        Index('ix_appointments_hospital_id_id', 'hospital_id', 'id'),
    )

# Medical History Tables (matching existing schema)
class MedicalHistory(Base):
    __tablename__ = 'medical_history'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_id = Column(Integer, ForeignKey('patients.id'))
    condition_name = Column(String(100), nullable=False)
    diagnosis_date = Column(Date)
    status = Column(String(20), default='active')
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='medical_history')
    hospital = relationship('Hospital', back_populates='medical_history')
    __table_args__ = (
        Index('ix_medical_history_hospital_id_id', 'hospital_id', 'id'),
    )

class Medication(Base):
    __tablename__ = 'medications'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_id = Column(Integer, ForeignKey('patients.id'))
    medication_name = Column(String(100), nullable=False)
    dosage = Column(String(50))
    frequency = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    prescribed_by = Column(Integer, ForeignKey('doctors.id'))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='medications')
    prescribing_doctor = relationship('Doctor', back_populates='medications')
    hospital = relationship('Hospital', back_populates='medications')
    __table_args__ = (
        Index('ix_medications_hospital_id_id', 'hospital_id', 'id'),
    )

class Allergy(Base):
    __tablename__ = 'allergies'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_id = Column(Integer, ForeignKey('patients.id'))
    allergen = Column(String(100), nullable=False)
    reaction = Column(Text)
    severity = Column(String(20))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='allergies')
    hospital = relationship('Hospital', back_populates='allergies')
    __table_args__ = (
        Index('ix_allergies_hospital_id_id', 'hospital_id', 'id'),
    )

class FamilyHistory(Base):
    __tablename__ = 'family_history'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    condition_name = Column(String(100), nullable=False)
    relation = Column(String(50), nullable=False)  # mother, father, sibling, etc.
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='family_history')

class TestResult(Base):
    __tablename__ = 'test_results'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_id = Column(Integer, ForeignKey('patients.id'))
    test_name = Column(String(100), nullable=False)
    test_date = Column(Date, nullable=False)
    result_value = Column(Text)
    reference_range = Column(Text)
    interpretation = Column(Text)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='test_results')
    doctor = relationship('Doctor', back_populates='test_results')
    hospital = relationship('Hospital', back_populates='test_results')
    __table_args__ = (
        Index('ix_test_results_hospital_id_id', 'hospital_id', 'id'),
    )

class Vaccination(Base):
    __tablename__ = 'vaccinations'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_id = Column(Integer, ForeignKey('patients.id'))
    vaccine_name = Column(String(100), nullable=False)
    vaccination_date = Column(Date, nullable=False)
    next_due_date = Column(Date)
    administered_by = Column(String(100))
    batch_number = Column(String(50))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='vaccinations')
    hospital = relationship('Hospital', back_populates='vaccinations')
    __table_args__ = (
        Index('ix_vaccinations_hospital_id_id', 'hospital_id', 'id'),
    )

class PatientNote(Base):
    __tablename__ = 'patient_notes'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    note_type = Column(String(50), nullable=False)  # consultation, diagnosis, treatment, etc.
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    patient = relationship('Patient', back_populates='patient_notes')
    doctor = relationship('Doctor', back_populates='patient_notes')
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)
    hospital = relationship('Hospital', back_populates='patient_notes')

class SymptomLog(Base):
    __tablename__ = 'symptom_logs'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_id = Column(Integer, ForeignKey('patients.id'))
    session_id = Column(Integer, ForeignKey('conversation_sessions.id'), nullable=True)
    symptom_description = Column(Text, nullable=False)
    severity = Column(String(20))  # mild, moderate, severe
    duration = Column(String(100))  # how long patient has had symptom
    frequency = Column(String(100))  # how often it occurs
    triggers = Column(Text)  # what makes it worse/better
    associated_symptoms = Column(Text)  # other symptoms
    reported_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='symptoms')
    hospital = relationship('Hospital', back_populates='symptoms')
    __table_args__ = (
        Index('ix_symptom_logs_hospital_id_id', 'hospital_id', 'id'),
    )

class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"
    
    id = Column(String(255), primary_key=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    session_id = Column(String(255), unique=True, nullable=False)
    initial_symptoms = Column(Text, nullable=False)
    current_context = Column(Text, default='{}')
    status = Column(String(50), default='active')
    confidence_timeline = Column(Text, default='[]')
    patient_profile = Column(Text, default='{}')
    questions_asked = Column(Integer, default=0)
    max_questions = Column(Integer, default=8)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to question answers
    question_answers = relationship("QuestionAnswer", back_populates="diagnostic_session", cascade="all, delete-orphan")
    
    def get_context(self):
        """Parse JSON context"""
        try:
            val = str(self.current_context) if self.current_context is not None else ""
            return json.loads(val) if val else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_context(self, context_dict):
        """Set JSON context"""
        self.current_context = json.dumps(context_dict)
    
    def get_confidence_timeline(self):
        """Parse JSON confidence timeline"""
        try:
            val = str(self.confidence_timeline) if self.confidence_timeline is not None else ""
            return json.loads(val) if val else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def add_confidence_score(self, confidence_score):
        """Add confidence score to timeline"""
        timeline = self.get_confidence_timeline()
        timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": confidence_score
        })
        self.confidence_timeline = json.dumps(timeline)
    
    def get_patient_profile(self):
        """Parse JSON patient profile"""
        try:
            val = str(self.patient_profile) if self.patient_profile is not None else ""
            return json.loads(val) if val else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    hospital = relationship('Hospital', back_populates='diagnostic_sessions')
    __table_args__ = (
        Index('ix_diagnostic_sessions_hospital_id_id', 'hospital_id', 'id'),
    )

class QuestionAnswer(Base):
    __tablename__ = "question_answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    diagnostic_session_id = Column(String(255), ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"))
    question_id = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    question_options = Column(Text)
    answer_payload = Column(Text, nullable=False)
    confidence_before = Column(Float)
    confidence_after = Column(Float)
    confidence_impact = Column(Float)
    medical_reasoning = Column(Text)
    asked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to diagnostic session
    diagnostic_session = relationship("DiagnosticSession", back_populates="question_answers")
    
    def get_answer(self):
        """Parse JSON answer payload"""
        try:
            val = str(self.answer_payload) if self.answer_payload is not None else ""
            return json.loads(val) if val else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_answer(self, answer_dict):
        """Set JSON answer payload"""
        self.answer_payload = json.dumps(answer_dict)
    
    def get_options(self):
        """Parse JSON question options"""
        try:
            val = str(self.question_options) if self.question_options is not None else ""
            return json.loads(val) if val else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_options(self, options_list):
        """Set JSON question options"""
        self.question_options = json.dumps(options_list)
    hospital = relationship('Hospital', back_populates='question_answers')
    __table_args__ = (
        Index('ix_question_answers_hospital_id_id', 'hospital_id', 'id'),
    )

class TestBooking(Base):
    __tablename__ = 'test_bookings'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_id = Column(Integer, ForeignKey('patients.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    test_name = Column(String(200), nullable=False)
    test_type = Column(String(100), nullable=False)  # blood, imaging, cardiac, etc.
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(String(20), nullable=False)
    cost = Column(String(20))
    preparation_instructions = Column(Text)
    status = Column(String(20), default='scheduled')  # scheduled, completed, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='test_bookings')
    user = relationship('User', back_populates='test_bookings')
    hospital = relationship('Hospital', back_populates='test_bookings')
    __table_args__ = (
        Index('ix_test_bookings_hospital_id_id', 'hospital_id', 'id'),
    )

# NEW: Session tracking table to link browser sessions to patients
class SessionUser(Base):
    __tablename__ = 'session_users'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    session_id = Column(String(100), unique=True, nullable=False)  # UUID from frontend
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)  # Link to existing patient
    first_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    last_active = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    patient = relationship('Patient', back_populates='session_users')
    conversation_sessions = relationship('ConversationSession', back_populates='session_user')
    hospital = relationship('Hospital', back_populates='session_users')
    __table_args__ = (
        Index('ix_session_users_hospital_id_id', 'hospital_id', 'id'),
    )

class ConversationSession(Base):
    __tablename__ = 'conversation_sessions'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    session_user_id = Column(Integer, ForeignKey('session_users.id'), nullable=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    session_type = Column(String(50), default='general')  # general, diagnostic, booking
    current_symptoms = Column(Text)  # Current session symptoms
    diagnostic_questions = Column(Text)  # JSON of Q&A from current session
    predicted_diagnosis = Column(Text)  # Current session diagnosis
    recommendations_given = Column(Text)  # Current session recommendations
    primary_symptom_category = Column(String(100))  # For symptom categorization
    is_related_to_previous = Column(Boolean, default=False)  # Track if related to previous visits
    phone_linked = Column(Boolean, default=False)  # Track if phone was provided
    started_at = Column(DateTime, server_default=func.current_timestamp())
    last_active = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    is_active = Column(Boolean, default=True)
    user = relationship('User', back_populates='conversation_sessions')
    session_user = relationship('SessionUser', back_populates='conversation_sessions')
    hospital = relationship('Hospital', back_populates='conversation_sessions')
    __table_args__ = (
        Index('ix_conversation_sessions_hospital_id_id', 'hospital_id', 'id'),
    )

# Enhanced Patient Profile for phone-based recognition
class PatientProfile(Base):
    __tablename__ = 'patient_profiles'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    phone_number = Column(String(20), unique=True, nullable=False, index=True)  # Primary identifier
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    emergency_contact = Column(String(100))
    chronic_conditions = Column(Text)  # JSON array of chronic conditions
    allergies = Column(Text)  # JSON array of allergies
    family_member_type = Column(String(50), default='self')  # self, child, parent, spouse
    primary_contact_phone = Column(String(20))  # For family members
    last_visit_date = Column(DateTime)
    last_visit_symptoms = Column(Text)
    preferred_doctors = Column(Text)  # JSON array of doctor IDs
    total_visits = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    symptom_history = relationship('SymptomHistory', back_populates='patient_profile')
    visit_history = relationship('VisitHistory', back_populates='patient_profile')
    hospital = relationship('Hospital', back_populates='patient_profiles')
    __table_args__ = (
        Index('ix_patient_profiles_hospital_id_id', 'hospital_id', 'id'),
    )

class SymptomHistory(Base):
    __tablename__ = 'symptom_history'
    id = Column(Integer, primary_key=True, index=True)
    patient_profile_id = Column(Integer, ForeignKey('patient_profiles.id'))
    symptom_category = Column(String(100), nullable=False)  # chest_pain, headache, etc.
    symptoms_text = Column(Text, nullable=False)
    diagnosis_result = Column(Text)  # JSON of diagnosis
    urgency_level = Column(String(20))
    visit_date = Column(DateTime, server_default=func.current_timestamp())
    is_resolved = Column(Boolean, default=False)
    follow_up_needed = Column(Boolean, default=False)
    related_appointment_id = Column(Integer, nullable=True)
    related_test_booking_id = Column(String(100), nullable=True)
    
    # Relationships
    patient_profile = relationship('PatientProfile', back_populates='symptom_history')

class VisitHistory(Base):
    __tablename__ = 'visit_history'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True, index=True)  # Multi-tenant support
    patient_profile_id = Column(Integer, ForeignKey('patient_profiles.id'))
    visit_type = Column(String(50), nullable=False)  # diagnostic, appointment, test
    primary_symptoms = Column(Text)
    doctors_consulted = Column(Text)  # JSON array
    tests_taken = Column(Text)  # JSON array
    outcome = Column(Text)
    visit_date = Column(DateTime, server_default=func.current_timestamp())
    session_data = Column(Text)  # Complete session context for reference
    
    # Relationships
    patient_profile = relationship('PatientProfile', back_populates='visit_history')
    hospital = relationship('Hospital', back_populates='visit_history')
    __table_args__ = (
        Index('ix_visit_history_hospital_id_id', 'hospital_id', 'id'),
    )

# ============================================================================
# MULTI-TENANT ADMIN SYSTEM MODELS
# ============================================================================

class Hospital(Base):
    """Hospital/Organization model for multi-tenancy"""
    __tablename__ = 'hospitals'
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)  # Unique slug for hospital (e.g., demo1)
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))
    subscription_plan = Column(String(50), default='basic')  # basic, premium, enterprise
    subscription_status = Column(String(20), default='active')  # active, suspended, cancelled
    subscription_expires = Column(DateTime)
    max_doctors = Column(Integer, default=10)
    max_patients = Column(Integer, default=1000)
    features_enabled = Column(Text, default='[]')  # JSON array of enabled features
    google_workspace_domain = Column(String(100))  # For Google Calendar integration
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    status = Column(String(20), default='active')  # active/inactive
    
    # Onboarding fields
    onboarding_status = Column(String(20), default='completed')  # not_started, in_progress, completed
    onboarding_completed_at = Column(DateTime, nullable=True)
    created_by_admin_id = Column(Integer, ForeignKey('admin_users.id'), nullable=True)  # Admin who created this hospital
    
    # Relationships
    admin_users = relationship('AdminUser', back_populates='hospital', foreign_keys='AdminUser.hospital_id')
    created_by_admin = relationship('AdminUser', foreign_keys=[created_by_admin_id], uselist=False)
    doctors = relationship('Doctor', back_populates='hospital')
    patients = relationship('Patient', back_populates='hospital')
    appointments = relationship('Appointment', back_populates='hospital')
    departments = relationship('Department', back_populates='hospital')
    subdivisions = relationship('Subdivision', back_populates='hospital')
    users = relationship('User', back_populates='hospital')
    medical_history = relationship('MedicalHistory', back_populates='hospital')
    medications = relationship('Medication', back_populates='hospital')
    allergies = relationship('Allergy', back_populates='hospital')
    test_results = relationship('TestResult', back_populates='hospital')
    vaccinations = relationship('Vaccination', back_populates='hospital')
    symptoms = relationship('SymptomLog', back_populates='hospital')
    diagnostic_sessions = relationship('DiagnosticSession', back_populates='hospital')
    question_answers = relationship('QuestionAnswer', back_populates='hospital')
    test_bookings = relationship('TestBooking', back_populates='hospital')
    session_users = relationship('SessionUser', back_populates='hospital')
    conversation_sessions = relationship('ConversationSession', back_populates='hospital')
    patient_profiles = relationship('PatientProfile', back_populates='hospital')
    visit_history = relationship('VisitHistory', back_populates='hospital')
    patient_notes = relationship('PatientNote', back_populates='hospital')
    audit_logs = relationship('AuditLog', back_populates='hospital')

class AdminUser(Base):
    """Admin user accounts for hospital management"""
    __tablename__ = 'admin_users'
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)  # Allow NULL for super admin users
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    # Onboarding / auth metadata
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    auth_provider = Column(String(50), default='email')  # email, google, both
    google_user_id = Column(String(255), unique=True, nullable=True)
    company_name = Column(String(200), nullable=True)  # Temporary until hospital is created
    onboarding_session_id = Column(Integer, nullable=True)  # Will link to OnboardingSession
    last_onboarding_step = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(Boolean, default=False)  # Can manage multiple hospitals
    last_login = Column(DateTime)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)  # For account lockout
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(100))  # For TOTP
    backup_codes = Column(Text)  # JSON array of backup codes
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    hospital = relationship('Hospital', back_populates='admin_users', foreign_keys=[hospital_id])
    user_roles = relationship('UserRole', back_populates='admin_user', foreign_keys='UserRole.admin_user_id')
    granted_roles = relationship('UserRole', foreign_keys='UserRole.granted_by')
    audit_logs = relationship('AuditLog', back_populates='admin_user')

class Role(Base):
    """Role definitions for role-based access control"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # hospital_admin, department_head, etc.
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    permissions = Column(Text, default='[]')  # JSON array of permission codes
    is_system_role = Column(Boolean, default=False)  # Cannot be modified
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationships
    user_roles = relationship('UserRole', back_populates='role')

class UserRole(Base):
    """Many-to-many relationship between AdminUser and Role"""
    __tablename__ = 'user_roles'
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey('admin_users.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    granted_by = Column(Integer, ForeignKey('admin_users.id'))  # Who granted this role
    granted_at = Column(DateTime, server_default=func.current_timestamp())
    expires_at = Column(DateTime)  # Optional role expiration
    
    # Relationships
    admin_user = relationship('AdminUser', back_populates='user_roles', foreign_keys=[admin_user_id])
    role = relationship('Role', back_populates='user_roles')
    granted_by_user = relationship('AdminUser', foreign_keys=[granted_by], overlaps="granted_roles")

class Permission(Base):
    """Permission definitions for fine-grained access control"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False)  # doctor:create, patient:read, etc.
    name = Column(String(100), nullable=False)
    description = Column(Text)
    resource_type = Column(String(50))  # doctor, patient, appointment, etc.
    action = Column(String(50))  # create, read, update, delete, manage
    created_at = Column(DateTime, server_default=func.current_timestamp())

class AuditLog(Base):
    """Audit trail for admin actions"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False)
    admin_user_id = Column(Integer, ForeignKey('admin_users.id'), nullable=False)
    action = Column(String(100), nullable=False)  # user.login, doctor.create, etc.
    resource_type = Column(String(50))  # user, doctor, patient, etc.
    resource_id = Column(String(50))  # ID of the affected resource
    details = Column(Text)  # JSON with action details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    hospital = relationship('Hospital', back_populates='audit_logs')
    admin_user = relationship('AdminUser', back_populates='audit_logs')


# ============================================================================
# ONBOARDING / EMAIL VERIFICATION MODELS
# ============================================================================


class OnboardingSession(Base):
    """
    Tracks progress of a hospital admin through the onboarding flow.
    """
    __tablename__ = 'onboarding_sessions'

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey('admin_users.id'), nullable=False)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)
    current_step = Column(Integer, default=1)
    completed_steps = Column(Text, default='[]')  # JSON array of completed step numbers
    partial_data = Column(Text, default='{}')  # JSON object with per-step form data
    status = Column(String(20), default='in_progress')  # in_progress, completed, abandoned
    started_at = Column(DateTime, server_default=func.current_timestamp())
    last_updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    completed_at = Column(DateTime, nullable=True)
    abandoned_at = Column(DateTime, nullable=True)
    step_started_at = Column(DateTime, nullable=True)  # Track when current step started
    step_timings = Column(Text, default='{}')  # JSON: {step_number: seconds_spent}


class EmailVerification(Base):
    """
    Stores one-time tokens for verifying admin user emails (and later password reset).
    """
    __tablename__ = 'email_verifications'

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey('admin_users.id'), nullable=False)
    email = Column(String(100), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    verification_type = Column(String(50), default='email_verification')  # email_verification, password_reset, etc.
    created_at = Column(DateTime, server_default=func.current_timestamp())
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    used = Column(Boolean, default=False, nullable=False, index=True)  # One-time use flag
    used_at = Column(DateTime, nullable=True)  # When token was used


class RateLimitLog(Base):
    """
    Tracks rate limit attempts for security and abuse prevention.
    """
    __tablename__ = 'rate_limit_logs'

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), nullable=False, index=True)  # IP address or user_id
    endpoint = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), index=True)
    
    __table_args__ = (
        Index('idx_identifier_endpoint_created', 'identifier', 'endpoint', 'created_at'),
    )


class OnboardingAnalytics(Base):
    """
    Tracks onboarding metrics and user behavior.
    """
    __tablename__ = 'onboarding_analytics'

    id = Column(Integer, primary_key=True, index=True)
    onboarding_session_id = Column(Integer, ForeignKey('onboarding_sessions.id'), nullable=True)
    admin_user_id = Column(Integer, ForeignKey('admin_users.id'), nullable=True)
    
    # Event tracking
    event_type = Column(String(50), nullable=False, index=True)  # registration_start, step_complete, drop_off, etc.
    event_data = Column(Text)  # JSON with event details
    
    # Timing
    step_number = Column(Integer, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)  # Time on step before event
    
    # Metadata
    signup_method = Column(String(20))  # google, email
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    created_at = Column(DateTime, server_default=func.current_timestamp(), index=True)
    
    # Relationships
    onboarding_session = relationship('OnboardingSession', backref='analytics_events')
    admin_user = relationship('AdminUser', backref='onboarding_analytics')


class TrialPeriod(Base):
    """
    Tracks trial periods for hospitals (deferred - table creation not implemented yet).
    This model is defined for future use when trial period functionality is needed.
    """
    __tablename__ = 'trial_periods'

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False, unique=True)
    started_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    usage_limits = Column(Text, default='{}')  # JSON object with usage limits
    status = Column(String(20), default='active')  # active, expired, converted
    converted_at = Column(DateTime, nullable=True)  # When trial converted to paid
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


# ============================================================================
# ENHANCE EXISTING MODELS WITH HOSPITAL_ID
# ============================================================================

# Add hospital_id to existing models (these will be added via migration)
# The relationships are defined here for reference 