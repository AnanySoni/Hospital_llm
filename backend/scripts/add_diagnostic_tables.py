#!/usr/bin/env python3
"""
Add diagnostic session tracking tables for Phase 1 Month 2
- DiagnosticSession: tracks complete diagnostic flows
- QuestionAnswer: stores Q&A history with confidence impact
"""

import sys
import os
from datetime import datetime

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, backend_path)

from backend.core.database import get_db
from sqlalchemy import text

def upgrade_diagnostic_schema():
    """Add diagnostic session tracking tables"""
    
    for db in get_db():
        try:
            print("🔄 Adding diagnostic session tables...")
            
            # Drop existing tables if they exist (for clean install)
            db.execute(text("DROP TABLE IF EXISTS question_answers CASCADE;"))
            db.execute(text("DROP TABLE IF EXISTS diagnostic_sessions CASCADE;"))
            
            # Create diagnostic_sessions table first
            db.execute(text("""
                CREATE TABLE diagnostic_sessions (
                    id VARCHAR(255) PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    initial_symptoms TEXT NOT NULL,
                    current_context TEXT DEFAULT '{}',
                    status VARCHAR(50) DEFAULT 'active',
                    confidence_timeline TEXT DEFAULT '[]',
                    patient_profile TEXT DEFAULT '{}',
                    questions_asked INTEGER DEFAULT 0,
                    max_questions INTEGER DEFAULT 8,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """))
            
            # Create question_answers table with proper foreign key
            db.execute(text("""
                CREATE TABLE question_answers (
                    id SERIAL PRIMARY KEY,
                    diagnostic_session_id VARCHAR(255),
                    question_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type VARCHAR(20) NOT NULL,
                    question_options TEXT,
                    answer_payload TEXT NOT NULL,
                    confidence_before FLOAT,
                    confidence_after FLOAT,
                    confidence_impact FLOAT,
                    medical_reasoning TEXT,
                    asked_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (diagnostic_session_id) REFERENCES diagnostic_sessions(id) ON DELETE CASCADE
                );
            """))
            
            # Create indexes for performance
            db.execute(text("""
                CREATE INDEX idx_diagnostic_sessions_session_id 
                ON diagnostic_sessions(session_id);
            """))
            
            db.execute(text("""
                CREATE INDEX idx_question_answers_session_id 
                ON question_answers(diagnostic_session_id);
            """))
            
            db.execute(text("""
                CREATE INDEX idx_question_answers_question_id 
                ON question_answers(question_id);
            """))
            
            db.commit()
            print("✅ Diagnostic session tables created successfully")
            
            # Verify tables exist
            result = db.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name IN ('diagnostic_sessions', 'question_answers')
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Verified tables: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating diagnostic tables: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            break

def downgrade_diagnostic_schema():
    """Remove diagnostic session tables if needed"""
    
    for db in get_db():
        try:
            print("🔄 Removing diagnostic session tables...")
            
            db.execute(text("DROP TABLE IF EXISTS question_answers CASCADE;"))
            db.execute(text("DROP TABLE IF EXISTS diagnostic_sessions CASCADE;"))
            
            db.commit()
            print("✅ Diagnostic session tables removed successfully")
            
        except Exception as e:
            print(f"❌ Error removing diagnostic tables: {e}")
            db.rollback()
        finally:
            db.close()
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade_diagnostic_schema()
    else:
        upgrade_diagnostic_schema() 