from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ForeignKey, ARRAY, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

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
    conversation_sessions = relationship('ConversationSession', back_populates='user')

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_group = Column(String(10))
    email = Column(String(100))
    phone = Column(String(20), nullable=False)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    address = Column(Text)
    insurance_provider = Column(String(100))
    insurance_number = Column(String(100))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    medical_history = relationship('MedicalHistory', back_populates='patient')
    medications = relationship('Medication', back_populates='patient')
    allergies = relationship('Allergy', back_populates='patient')
    family_history = relationship('FamilyHistory', back_populates='patient')
    test_results = relationship('TestResult', back_populates='patient')
    vaccinations = relationship('Vaccination', back_populates='patient')
    patient_notes = relationship('PatientNote', back_populates='patient')
    symptoms = relationship('SymptomLog', back_populates='patient')
    test_bookings = relationship('TestBooking', back_populates='patient')

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=False)
    status = Column(String(20), default='booked')
    notes = Column(Text)
    patient_name = Column(String(100))
    user = relationship('User', back_populates='appointments')
    doctor = relationship('Doctor', back_populates='appointments')

# Medical History Tables
class MedicalHistory(Base):
    __tablename__ = 'medical_history'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    condition_name = Column(String(200), nullable=False)
    diagnosis_date = Column(Date)
    status = Column(String(20), default='active')
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='medical_history')

class Medication(Base):
    __tablename__ = 'medications'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
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
    allergen = Column(String(200), nullable=False)
    reaction = Column(Text)
    severity = Column(String(20))
    created_at = Column(DateTime, server_default=func.current_timestamp())
    patient = relationship('Patient', back_populates='allergies')

class FamilyHistory(Base):
    __tablename__ = 'family_history'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    condition_name = Column(String(200), nullable=False)
    relation = Column(String(50), nullable=False)  # mother, father, sibling, etc.
    notes = Column(Text)
    patient = relationship('Patient', back_populates='family_history')

class TestResult(Base):
    __tablename__ = 'test_results'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    test_name = Column(String(200), nullable=False)
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
    vaccine_name = Column(String(200), nullable=False)
    vaccination_date = Column(Date, nullable=False)
    next_due_date = Column(Date)
    administered_by = Column(String(200))
    batch_number = Column(String(100))
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

# NEW TABLES FOR LLM CONVERSATION TRACKING
class ConversationSession(Base):
    __tablename__ = 'conversation_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    session_data = Column(Text)  # JSON string of conversation history
    session_type = Column(String(50), default='general')  # general, diagnostic, booking
    started_at = Column(DateTime, server_default=func.current_timestamp())
    last_active = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    is_active = Column(Boolean, default=True)
    user = relationship('User', back_populates='conversation_sessions')

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
    __tablename__ = 'diagnostic_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    initial_symptoms = Column(Text, nullable=False)
    questions_asked = Column(Text)  # JSON array of questions asked
    responses_received = Column(Text)  # JSON array of responses
    predicted_conditions = Column(Text)  # JSON array of potential diagnoses
    confidence_scores = Column(Text)  # JSON array of confidence scores
    recommendations = Column(Text)  # JSON object of recommendations
    final_recommendation = Column(String(50))  # appointment, test, emergency
    created_at = Column(DateTime, server_default=func.current_timestamp())
    completed_at = Column(DateTime, nullable=True)

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