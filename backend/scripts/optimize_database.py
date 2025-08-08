"""
Database optimization script
Run this to add indexes and constraints for better performance
"""

from backend.core.database import engine
from sqlalchemy import text

def apply_database_optimizations():
    """Apply database optimizations for better performance"""
    
    optimizations = [
        # Add indexes for better query performance
        "CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_name);",
        "CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);",
        "CREATE INDEX IF NOT EXISTS idx_doctors_department ON doctors(department_id);",
        "CREATE INDEX IF NOT EXISTS idx_doctors_name ON doctors(name);",
        
        # Add constraints for data integrity
        """ALTER TABLE appointments 
           ADD CONSTRAINT IF NOT EXISTS chk_appointment_status 
           CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled'));""",
        
        # Add soft delete columns
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;",
        "ALTER TABLE doctors ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;",
        
        # Add created_at and updated_at for audit trail
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE doctors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE doctors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
    ]
    
    with engine.connect() as conn:
        for optimization in optimizations:
            try:
                conn.execute(text(optimization))
                print(f"✅ Applied: {optimization[:50]}...")
            except Exception as e:
                print(f"⚠️ Skipped (might already exist): {optimization[:50]}... - {e}")
        
        conn.commit()
        print("🚀 Database optimizations completed!")

if __name__ == "__main__":
    apply_database_optimizations() 