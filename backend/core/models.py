from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ForeignKey, ARRAY, DateTime, func, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import json

Base = declarative_base()

# Existing schema models (matching user's database)
class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subdivisions = relationship('Subdivision', back_populates='department')
    doctors = relationship('Doctor', back_populates='department')

class Subdivision(Base):
    __tablename__ = 'subdivisions'
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id'))
    name = Column(String(100), nullable=False)
    department = relationship('Department', back_populates='subdivisions')
    doctors = relationship('Doctor', back_populates='subdivision')

class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)  # Will be set via migration
    name = Column(String(100), nullable=False)
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
    name = Column(String(100))
    contact_info = Column(String(100))
    phone_number = Column(String(20))
    age = Column(Integer)
    medical_history = Column(Text)
    appointments = relationship('Appointment', back_populates='user')
    # diagnostic_sessions = relationship('DiagnosticSession', back_populates='user')  # Removed for new adaptive model
    test_bookings = relationship('TestBooking', back_populates='user')

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)  # Will be set via migration
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
    # diagnostic_sessions = relationship('DiagnosticSession', back_populates='patient')  # Removed for new adaptive model

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)  # Will be set via migration
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

# Medical History Tables (matching existing schema)
class MedicalHistory(Base):
    __tablename__ = 'medical_history'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    condition_name = Column(String(100), nullable=False)
    diagnosis_date = Column(Date)
    status = Column(String(20), default='active')
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='medical_history')

class Medication(Base):
    __tablename__ = 'medications'
    id = Column(Integer, primary_key=True, index=True)
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

class Allergy(Base):
    __tablename__ = 'allergies'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    allergen = Column(String(100), nullable=False)
    reaction = Column(Text)
    severity = Column(String(20))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='allergies')

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

class Vaccination(Base):
    __tablename__ = 'vaccinations'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    vaccine_name = Column(String(100), nullable=False)
    vaccination_date = Column(Date, nullable=False)
    next_due_date = Column(Date)
    administered_by = Column(String(100))
    batch_number = Column(String(50))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='vaccinations')

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

class SymptomLog(Base):
    __tablename__ = 'symptom_logs'
    id = Column(Integer, primary_key=True, index=True)
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

class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"
    
    id = Column(String(255), primary_key=True)
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
            return json.loads(self.current_context) if self.current_context else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_context(self, context_dict):
        """Set JSON context"""
        self.current_context = json.dumps(context_dict)
    
    def get_confidence_timeline(self):
        """Parse JSON confidence timeline"""
        try:
            return json.loads(self.confidence_timeline) if self.confidence_timeline else []
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
            return json.loads(self.patient_profile) if self.patient_profile else {}
        except (json.JSONDecodeError, TypeError):
            return {}

class QuestionAnswer(Base):
    __tablename__ = "question_answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
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
            return json.loads(self.answer_payload) if self.answer_payload else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_answer(self, answer_dict):
        """Set JSON answer payload"""
        self.answer_payload = json.dumps(answer_dict)
    
    def get_options(self):
        """Parse JSON question options"""
        try:
            return json.loads(self.question_options) if self.question_options else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_options(self, options_list):
        """Set JSON question options"""
        self.question_options = json.dumps(options_list)

class TestBooking(Base):
    __tablename__ = 'test_bookings'
    id = Column(Integer, primary_key=True, index=True)
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

# NEW: Session tracking table to link browser sessions to patients
class SessionUser(Base):
    __tablename__ = 'session_users'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False)  # UUID from frontend
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)  # Link to existing patient
    first_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    last_active = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    patient = relationship('Patient', backref='session_users')
    conversation_sessions = relationship('ConversationSession', back_populates='session_user')

class ConversationSession(Base):
    __tablename__ = 'conversation_sessions'
    id = Column(Integer, primary_key=True, index=True)
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
    user = relationship('User', backref='conversation_sessions')
    session_user = relationship('SessionUser', back_populates='conversation_sessions')

# Enhanced Patient Profile for phone-based recognition
class PatientProfile(Base):
    __tablename__ = 'patient_profiles'
    id = Column(Integer, primary_key=True, index=True)
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

# ============================================================================
# MULTI-TENANT ADMIN SYSTEM MODELS
# ============================================================================

class Hospital(Base):
    """Hospital/Organization model for multi-tenancy"""
    __tablename__ = 'hospitals'
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(String(50), unique=True, nullable=False, index=True)  # Unique identifier like 'apollo_delhi'
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
    
    # Relationships
    admin_users = relationship('AdminUser', back_populates='hospital')
    doctors = relationship('Doctor', back_populates='hospital')
    patients = relationship('Patient', back_populates='hospital')
    appointments = relationship('Appointment', back_populates='hospital')

class AdminUser(Base):
    """Admin user accounts for hospital management"""
    __tablename__ = 'admin_users'
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
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
    hospital = relationship('Hospital', back_populates='admin_users')
    user_roles = relationship('UserRole', back_populates='admin_user', foreign_keys='UserRole.admin_user_id')
    granted_roles = relationship('UserRole', foreign_keys='UserRole.granted_by')

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
    
    # Relationships
    hospital = relationship('Hospital')
    admin_user = relationship('AdminUser')

# ============================================================================
# ENHANCE EXISTING MODELS WITH HOSPITAL_ID
# ============================================================================

# Add hospital_id to existing models (these will be added via migration)
# The relationships are defined here for reference 