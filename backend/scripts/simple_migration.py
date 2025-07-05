"""
Simple migration to add session_users table
Uses the correct database name: hospital_db
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def run_migration():
    """Add session_users table to hospital_db"""
    
    try:
        print("🔄 Connecting to hospital_db...")
        with engine.connect() as connection:
            print("✅ Connected successfully!")
            
            # Step 1: Create session_users table
            print("🔧 Creating session_users table...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS session_users (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE NOT NULL,
                    patient_id INTEGER REFERENCES patients(id),
                    first_name VARCHAR(100),
                    age INTEGER,
                    gender VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.commit()
            print("✅ session_users table created")
            
            # Step 2: Create indexes
            print("🔧 Creating indexes...")
            
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_session_users_session_id ON session_users(session_id)"))
            connection.commit()
            
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_session_users_patient_id ON session_users(patient_id)"))
            connection.commit()
            
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_session_users_last_active ON session_users(last_active)"))
            connection.commit()
            print("✅ Indexes created")
            
            # Step 3: Check if conversation_sessions exists and add column if needed
            print("🔧 Checking conversation_sessions table...")
            result = connection.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'conversation_sessions'
            """))
            
            if result.scalar() > 0:
                print("✅ conversation_sessions table found")
                
                # Check if session_user_id column exists
                result = connection.execute(text("""
                    SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = 'conversation_sessions' 
                    AND column_name = 'session_user_id'
                """))
                
                if result.scalar() == 0:
                    print("🔧 Adding session_user_id column...")
                    connection.execute(text("""
                        ALTER TABLE conversation_sessions 
                        ADD COLUMN session_user_id INTEGER REFERENCES session_users(id)
                    """))
                    connection.commit()
                    print("✅ session_user_id column added")
                else:
                    print("✅ session_user_id column already exists")
            else:
                print("ℹ️ conversation_sessions table not found (will be created later)")
            
            print("🎉 Migration completed successfully!")
            
            # Verify the table was created
            result = connection.execute(text("SELECT COUNT(*) FROM session_users"))
            print(f"✅ Verification: session_users table has {result.scalar()} records")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database 'hospital_db' exists")
        print("3. You have the correct password")
        return False

if __name__ == "__main__":
    print("🏥 Hospital LLM - Add Session Tracking")
    print("=" * 40)
    
    success = run_migration()
    
    if success:
        print("\n🚀 Ready to start the backend!")
        print("Run: cd backend && python -m uvicorn main:app --reload")
    else:
        print("\n❌ Please fix the database connection and try again.") 