-- Add hospital_id columns for multi-tenancy
ALTER TABLE departments ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE medical_history ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE medications ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE allergies ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE vaccinations ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE symptom_logs ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE diagnostic_sessions ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE question_answers ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE test_bookings ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE session_users ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE visit_history ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE patient_notes ADD COLUMN IF NOT EXISTS hospital_id INTEGER;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS hospital_id INTEGER NOT NULL DEFAULT 1;

-- Add foreign key constraints (optional, but recommended)
ALTER TABLE departments ADD CONSTRAINT fk_departments_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE subdivisions ADD CONSTRAINT fk_subdivisions_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE users ADD CONSTRAINT fk_users_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE medical_history ADD CONSTRAINT fk_medical_history_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE medications ADD CONSTRAINT fk_medications_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE allergies ADD CONSTRAINT fk_allergies_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE test_results ADD CONSTRAINT fk_test_results_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE vaccinations ADD CONSTRAINT fk_vaccinations_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE symptom_logs ADD CONSTRAINT fk_symptom_logs_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE diagnostic_sessions ADD CONSTRAINT fk_diagnostic_sessions_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE question_answers ADD CONSTRAINT fk_question_answers_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE test_bookings ADD CONSTRAINT fk_test_bookings_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE session_users ADD CONSTRAINT fk_session_users_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE conversation_sessions ADD CONSTRAINT fk_conversation_sessions_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE patient_profiles ADD CONSTRAINT fk_patient_profiles_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE visit_history ADD CONSTRAINT fk_visit_history_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE patient_notes ADD CONSTRAINT fk_patient_notes_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id);

-- Add indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_departments_hospital_id ON departments(hospital_id);
CREATE INDEX IF NOT EXISTS idx_users_hospital_id ON users(hospital_id);
CREATE INDEX IF NOT EXISTS idx_medical_history_hospital_id ON medical_history(hospital_id);
CREATE INDEX IF NOT EXISTS idx_test_results_hospital_id ON test_results(hospital_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_hospital_id ON diagnostic_sessions(hospital_id);
CREATE INDEX IF NOT EXISTS idx_patient_profiles_hospital_id ON patient_profiles(hospital_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_hospital_id ON audit_logs(hospital_id); 