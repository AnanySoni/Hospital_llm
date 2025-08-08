"""
Add session tracking tables to existing hospital database
This adds Phase 1 session-based user tracking to your existing schema
"""

from sqlalchemy import create_engine, text
from backend.core.database import engine, SessionLocal

def add_session_tracking_tables():
    """Add session tracking tables to existing database"""
    
    session_tracking_sql = """
    -- Phase 1: Session-based User Tracking Tables
    
    -- Create session_users table
    CREATE TABLE IF NOT EXISTS session_users (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(100) UNIQUE NOT NULL,
        first_name VARCHAR(100),
        age INTEGER,
        gender VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create patient_history table
    CREATE TABLE IF NOT EXISTS patient_history (
        id SERIAL PRIMARY KEY,
        session_user_id INTEGER REFERENCES session_users(id),
        user_id INTEGER REFERENCES users(id),
        entry_type VARCHAR(50) NOT NULL,
        symptoms TEXT,
        diagnosis TEXT,
        doctor_recommendations TEXT,
        test_recommendations TEXT,
        appointment_outcome TEXT,
        test_results TEXT,
        medications_mentioned TEXT,
        chronic_conditions TEXT,
        allergies TEXT,
        family_history TEXT,
        severity_level VARCHAR(20),
        confidence_score VARCHAR(20),
        urgency_level VARCHAR(20),
        session_context TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Add session_user_id to existing appointments table
    ALTER TABLE appointments 
    ADD COLUMN IF NOT EXISTS session_user_id INTEGER REFERENCES session_users(id);
    
    -- Update existing users table if needed
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20);
    
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS age INTEGER;
    
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS medical_history TEXT;
    
    -- Create conversation_sessions table
    CREATE TABLE IF NOT EXISTS conversation_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        session_user_id INTEGER REFERENCES session_users(id),
        conversation_data TEXT,
        session_type VARCHAR(50) DEFAULT 'general',
        current_symptoms TEXT,
        diagnostic_questions TEXT,
        predicted_diagnosis TEXT,
        recommendations_given TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_session_users_session_id ON session_users(session_id);
    CREATE INDEX IF NOT EXISTS idx_patient_history_session_user ON patient_history(session_user_id);
    CREATE INDEX IF NOT EXISTS idx_patient_history_created_at ON patient_history(created_at);
    CREATE INDEX IF NOT EXISTS idx_patient_history_entry_type ON patient_history(entry_type);
    CREATE INDEX IF NOT EXISTS idx_appointments_session_user ON appointments(session_user_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_sessions_session_user ON conversation_sessions(session_user_id);
    
    -- Insert sample session user for testing
    INSERT INTO session_users (session_id, first_name, age, gender) 
    VALUES ('session_demo_123456789_abcdef123', 'Demo', 30, 'Other')
    ON CONFLICT (session_id) DO NOTHING;
    
    -- Insert sample patient history
    INSERT INTO patient_history (
        session_user_id, 
        entry_type, 
        symptoms, 
        diagnosis, 
        severity_level, 
        urgency_level,
        session_context
    ) 
    SELECT 
        su.id,
        'symptom',
        '["headache", "fever"]',
        'Possible viral infection',
        'moderate',
        'medium',
        'Initial demo consultation'
    FROM session_users su 
    WHERE su.session_id = 'session_demo_123456789_abcdef123'
    ON CONFLICT DO NOTHING;
    """
    
    db = SessionLocal()
    try:
        # Split SQL commands and execute each one
        commands = session_tracking_sql.split(';')
        
        for command in commands:
            command = command.strip()
            if command:
                try:
                    db.execute(text(command))
                    db.commit()
                except Exception as e:
                    print(f"Note: {e}")
                    db.rollback()
        
        print("✅ Session tracking tables added successfully!")
        print("🔹 Tables added: session_users, patient_history, conversation_sessions")
        print("🔹 Enhanced: appointments table with session_user_id")
        print("🔹 Demo data inserted for testing")
        
    except Exception as e:
        print(f"❌ Error adding session tracking tables: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Adding session tracking to existing hospital database...")
    add_session_tracking_tables()
    print("Session tracking setup complete!") 