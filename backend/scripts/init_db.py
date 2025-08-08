"""
Database initialization script
Creates tables and populates with sample data
"""

from sqlalchemy import create_engine, text
from backend.core.models import Base, Doctor, Department, Subdivision
from backend.core.database import SessionLocal, engine
import json

def apply_session_tracking_migration():
    """Apply session tracking tables migration"""
    db = SessionLocal()
    try:
        # Read the migration SQL
        with open('../add_session_tracking_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split into individual commands and execute
        commands = migration_sql.split(';')
        for command in commands:
            command = command.strip()
            if command:
                try:
                    db.execute(text(command))
                except Exception as e:
                    print(f"Note: {e}")  # Some commands may fail if already exists
        
        db.commit()
        print("✅ Session tracking migration applied successfully!")
        
    except FileNotFoundError:
        print("ℹ️ Session tracking migration file not found, skipping...")
    except Exception as e:
        print(f"❌ Error applying session tracking migration: {e}")
        db.rollback()
    finally:
        db.close()

def init_database():
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        
        # Apply session tracking tables migration
        apply_session_tracking_migration()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("ℹ️ Continuing with existing database...")
    
    # Add sample data
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Department).count() > 0:
            print("ℹ️ Database already initialized with data!")
            return
        
        # Create departments
        departments_data = [
            {"name": "Cardiology", "description": "Heart and cardiovascular diseases"},
            {"name": "Neurology", "description": "Brain and nervous system disorders"},
            {"name": "Orthopedics", "description": "Bone, joint, and musculoskeletal disorders"},
            {"name": "Dermatology", "description": "Skin, hair, and nail conditions"},
            {"name": "Pediatrics", "description": "Children's health and development"},
            {"name": "Psychiatry", "description": "Mental health and behavioral disorders"},
            {"name": "General Medicine", "description": "General healthcare and internal medicine"},
            {"name": "Surgery", "description": "Surgical procedures and operations"},
            {"name": "Gynecology", "description": "Women's reproductive health"},
            {"name": "Urology", "description": "Urinary system and male reproductive health"}
        ]
        
        departments = []
        for dept_data in departments_data:
            dept = Department(**dept_data)
            db.add(dept)
            departments.append(dept)
        
        db.flush()  # Get IDs without committing
        
        # Create subdivisions
        subdivisions_data = [
            {"name": "Interventional Cardiology", "department_id": departments[0].id},
            {"name": "Pediatric Cardiology", "department_id": departments[0].id},
            {"name": "Stroke Center", "department_id": departments[1].id},
            {"name": "Epilepsy Center", "department_id": departments[1].id},
            {"name": "Joint Replacement", "department_id": departments[2].id},
            {"name": "Sports Medicine", "department_id": departments[2].id},
            {"name": "Cosmetic Dermatology", "department_id": departments[3].id},
            {"name": "Dermatopathology", "department_id": departments[3].id},
            {"name": "Neonatology", "department_id": departments[4].id},
            {"name": "Child Psychology", "department_id": departments[5].id}
        ]
        
        subdivisions = []
        for subdiv_data in subdivisions_data:
            subdiv = Subdivision(**subdiv_data)
            db.add(subdiv)
            subdivisions.append(subdiv)
        
        db.flush()
        
        # Create doctors with comprehensive data
        doctors_data = [
            {"name": "Dr. Sarah Johnson", "department_id": departments[0].id, "subdivision_id": subdivisions[0].id, "tags": ["interventional", "angioplasty", "stents"]},
            {"name": "Dr. Michael Chen", "department_id": departments[0].id, "subdivision_id": subdivisions[1].id, "tags": ["pediatric", "congenital", "heart"]},
            {"name": "Dr. Emily Rodriguez", "department_id": departments[1].id, "subdivision_id": subdivisions[2].id, "tags": ["stroke", "emergency", "neurology"]},
            {"name": "Dr. David Kim", "department_id": departments[1].id, "subdivision_id": subdivisions[3].id, "tags": ["epilepsy", "seizures", "EEG"]},
            {"name": "Dr. Jennifer Wang", "department_id": departments[2].id, "subdivision_id": subdivisions[4].id, "tags": ["joint", "replacement", "surgery"]},
            # Add more doctors...
        ]
        
        for doctor_data in doctors_data:
            doctor = Doctor(**doctor_data)
            db.add(doctor)
        
        db.commit()
        print("✅ Sample data added successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 