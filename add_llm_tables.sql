-- Add missing tables for LLM conversation tracking and patient history
-- Run this script in pgAdmin or psql to add the missing functionality

-- 1. Conversation Sessions - Track chat conversations with users
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    patient_id INTEGER REFERENCES patients(id),
    session_data TEXT,  -- JSON string of conversation history
    session_type VARCHAR(50) DEFAULT 'general',  -- general, diagnostic, booking
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. Symptom Logs - Track symptoms reported during conversations
CREATE TABLE IF NOT EXISTS symptom_logs (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    session_id INTEGER REFERENCES conversation_sessions(id),
    symptom_description TEXT NOT NULL,
    severity VARCHAR(20),  -- mild, moderate, severe
    duration VARCHAR(100),  -- how long patient has had symptom
    frequency VARCHAR(100),  -- how often it occurs
    triggers TEXT,  -- what makes it worse/better
    associated_symptoms TEXT,  -- other symptoms
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Diagnostic Sessions - Track LLM diagnostic conversations
CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    patient_id INTEGER REFERENCES patients(id),
    initial_symptoms TEXT NOT NULL,
    questions_asked TEXT,  -- JSON array of questions asked
    responses_received TEXT,  -- JSON array of responses
    predicted_conditions TEXT,  -- JSON array of potential diagnoses
    confidence_scores TEXT,  -- JSON array of confidence scores
    recommendations TEXT,  -- JSON object of recommendations
    final_recommendation VARCHAR(50),  -- appointment, test, emergency
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 4. Test Bookings - Track scheduled medical tests (separate from results)
CREATE TABLE IF NOT EXISTS test_bookings (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    user_id INTEGER REFERENCES users(id),
    test_name VARCHAR(200) NOT NULL,
    test_type VARCHAR(100) NOT NULL,  -- blood, imaging, cardiac, etc.
    scheduled_date DATE NOT NULL,
    scheduled_time VARCHAR(20) NOT NULL,
    cost VARCHAR(20),
    preparation_instructions TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled, completed, cancelled
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_user_id ON conversation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_patient_id ON conversation_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_last_active ON conversation_sessions(last_active);

CREATE INDEX IF NOT EXISTS idx_symptom_logs_patient_id ON symptom_logs(patient_id);
CREATE INDEX IF NOT EXISTS idx_symptom_logs_session_id ON symptom_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_symptom_logs_reported_at ON symptom_logs(reported_at);

CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_user_id ON diagnostic_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_patient_id ON diagnostic_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_created_at ON diagnostic_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_test_bookings_patient_id ON test_bookings(patient_id);
CREATE INDEX IF NOT EXISTS idx_test_bookings_scheduled_date ON test_bookings(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_test_bookings_status ON test_bookings(status);

-- Add some sample data
INSERT INTO conversation_sessions (user_id, session_data, session_type, started_at, last_active) VALUES
(1, '{"messages": [{"role": "user", "content": "I have a headache"}, {"role": "assistant", "content": "I understand you have a headache. Can you tell me more about it?"}]}', 'diagnostic', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

COMMENT ON TABLE conversation_sessions IS 'Stores chat conversation history for each user session';
COMMENT ON TABLE symptom_logs IS 'Tracks symptoms reported by patients during conversations';
COMMENT ON TABLE diagnostic_sessions IS 'Records LLM diagnostic conversation sessions and outcomes';
COMMENT ON TABLE test_bookings IS 'Manages scheduled medical test appointments';

-- Verify tables were created
SELECT 'conversation_sessions' as table_name, COUNT(*) as row_count FROM conversation_sessions
UNION ALL
SELECT 'symptom_logs', COUNT(*) FROM symptom_logs
UNION ALL
SELECT 'diagnostic_sessions', COUNT(*) FROM diagnostic_sessions
UNION ALL
SELECT 'test_bookings', COUNT(*) FROM test_bookings; 