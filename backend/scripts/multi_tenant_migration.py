import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.core.models import (
    Base, Hospital, Doctor, User, TestResult, 
    Department, Appointment, AdminUser
)
from backend.services.auth_service import AuthService
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:kev1jiph@localhost:5432/hospital_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# --- MIGRATION SCRIPT FOR MULTI-TENANT SUPPORT ---
def create_hospitals_table():
    # Create the hospitals table if it doesn't exist
    Base.metadata.create_all(engine, tables=[Hospital.__table__])
    print("Ensured hospitals table exists.")

def add_hospital_id_columns():
    # This is a placeholder: in production, use Alembic for migrations
    # Here, we use raw SQL to add columns if they don't exist
    with engine.connect() as conn:
        for table in [
            'departments', 'subdivisions', 'users', 'doctors', 'patients', 'appointments',
            'medical_history', 'medications', 'allergies', 'test_results', 'vaccinations',
            'symptom_logs', 'diagnostic_sessions', 'question_answers', 'test_bookings',
            'session_users', 'conversation_sessions', 'patient_profiles', 'visit_history'
        ]:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS hospital_id INTEGER REFERENCES hospitals(id);") )
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_hospital_id_id ON {table} (hospital_id, id);") )
                print(f"Ensured hospital_id column and index on {table}.")
            except Exception as e:
                print(f"Error updating {table}: {e}")

def create_demo_hospitals():
    # Remove all admin users and hospitals except demo1 and demo2
    session = SessionLocal()
    # First, delete user_roles and admin users for non-demo hospitals
    demo_hospitals = session.query(Hospital.id).filter(Hospital.slug.in_(['demo1', 'demo2'])).all()
    demo_hospital_ids = [h.id for h in demo_hospitals]
    # Find admin user ids to delete
    admin_ids_to_delete = [admin.id for admin in session.query(AdminUser.id).filter(~AdminUser.hospital_id.in_(demo_hospital_ids)).all()]
    if admin_ids_to_delete:
        # Delete user_roles referencing these admin users (ORM for compatibility)
        try:
            UserRole = None
            # Dynamically import UserRole if not already imported
            from backend.core.models import UserRole
        except ImportError:
            pass
        if UserRole:
            session.query(UserRole).filter(UserRole.admin_user_id.in_(admin_ids_to_delete)).delete(synchronize_session=False)
            session.commit()
    # Now delete the admin users
    session.query(AdminUser).filter(~AdminUser.hospital_id.in_(demo_hospital_ids)).delete(synchronize_session=False)
    session.commit()
    # Now, delete the hospitals
    session.query(Hospital).filter(~Hospital.slug.in_(['demo1', 'demo2'])).delete(synchronize_session=False)
    session.commit()
    try:
        demo1 = session.query(Hospital).filter_by(slug='demo1').first()
        if not demo1:
            demo1 = Hospital(
                slug='demo1', 
                name='Demo Hospital 1',
                display_name='Demo Hospital 1',  # Add display_name
                status='active'
            )
            session.add(demo1)
        demo2 = session.query(Hospital).filter_by(slug='demo2').first()
        if not demo2:
            demo2 = Hospital(
                slug='demo2', 
                name='Demo Hospital 2',
                display_name='Demo Hospital 2',  # Add display_name
                status='active'
            )
            session.add(demo2)
        session.commit()
        print("Demo hospitals created or already exist.")
    finally:
        session.close()

def assign_doctors_to_demo_hospitals():
    """Assign doctors to hospitals while preserving department relationships"""
    session = SessionLocal()
    try:
        # Get demo hospitals
        hospitals = session.query(Hospital).filter(Hospital.slug.in_(['demo1', 'demo2'])).all()
        if len(hospitals) < 2:
            print("Demo hospitals not found. Skipping doctor assignment.")
            return
        demo1, demo2 = hospitals

        departments = session.query(Department).all()
        hospital_counts = {demo1.id: 0, demo2.id: 0}

        for dept in departments:
            dept_doctors = session.query(Doctor).filter_by(department_id=dept.id).all()
            if not dept_doctors:
                continue
            # Split evenly
            half = len(dept_doctors) // 2
            for i, doctor in enumerate(dept_doctors):
                if i < half:
                    doctor.hospital_id = demo1.id
                    hospital_counts[demo1.id] += 1
                else:
                    doctor.hospital_id = demo2.id
                    hospital_counts[demo2.id] += 1
            # Assign department to both hospitals (if needed)
            # dept.hospital_id = None  # If department is global, else assign as needed
            print(f"Split department {dept.name}: {half} to {demo1.slug}, {len(dept_doctors)-half} to {demo2.slug}")

        # Handle doctors without departments
        unassigned_doctors = session.query(Doctor).filter_by(department_id=None).all()
        for i, doctor in enumerate(unassigned_doctors):
            if i % 2 == 0:
                doctor.hospital_id = demo1.id
                hospital_counts[demo1.id] += 1
            else:
                doctor.hospital_id = demo2.id
                hospital_counts[demo2.id] += 1

        session.commit()
        print(f"\nFinal distribution:")
        print(f"Hospital {demo1.slug}: {hospital_counts[demo1.id]} doctors")
        print(f"Hospital {demo2.slug}: {hospital_counts[demo2.id]} doctors")
    except Exception as e:
        session.rollback()
        print(f"Error assigning doctors: {e}")
        raise
    finally:
        session.close()

def assign_tests_to_demo_hospitals():
    """Assign test results to hospitals"""
    session = SessionLocal()
    try:
        # Get demo hospitals
        hospitals = session.query(Hospital).filter(Hospital.slug.in_(['demo1', 'demo2'])).all()
        if len(hospitals) < 2:
            print("Demo hospitals not found. Skipping test assignment.")
            return
        demo1, demo2 = hospitals

        # Get all unique lab tests
        tests = session.query(TestResult).all()
        created = 0
        for test in tests:
            # Assign to both hospitals by duplicating
            # For demo1
            test1 = TestResult()
            for col in test.__table__.columns:
                if col.name != 'id':
                    setattr(test1, col.name, getattr(test, col.name))
            test1.hospital_id = demo1.id
            session.add(test1)
            # For demo2
            test2 = TestResult()
            for col in test.__table__.columns:
                if col.name != 'id':
                    setattr(test2, col.name, getattr(test, col.name))
            test2.hospital_id = demo2.id
            session.add(test2)
            created += 2
        session.commit()
        print(f"\nDuplicated {created//2} lab tests for each hospital (total {created} records)")
    except Exception as e:
        session.rollback()
        print(f"Error assigning tests: {e}")
        raise
    finally:
        session.close()

def update_users_with_hospital_id():
    session = SessionLocal()
    try:
        hospitals = session.query(Hospital).filter(Hospital.slug.in_(['demo1', 'demo2'])).all()
        if len(hospitals) < 2:
            print("Demo hospitals not found. Skipping user update.")
            return
        demo1, demo2 = hospitals
        users = session.query(User).all()
        for i, user in enumerate(users):
            user.hospital_id = demo1.id if i % 2 == 0 else demo2.id
        session.commit()
        print("Updated users with hospital_id.")
    finally:
        session.close()

def validate_pre_migration():
    """Validate data before migration"""
    session = SessionLocal()
    try:
        # Check for critical data
        doctor_count = session.query(Doctor).count()
        user_count = session.query(User).count()
        print(f"Found {doctor_count} doctors and {user_count} users")
        
        if doctor_count == 0:
            raise ValueError("No doctors found in database")
        if user_count == 0:
            raise ValueError("No users found in database")
            
        return True
    except Exception as e:
        print(f"Pre-migration validation failed: {e}")
        return False
    finally:
        session.close()

def verify_data_integrity():
    """Verify data integrity after migration"""
    session = SessionLocal()
    try:
        # Check hospitals were created
        hospitals = session.query(Hospital).all()
        if not hospitals:
            raise ValueError("No hospitals found after migration")
            
        # Check doctor distribution
        for hospital in hospitals:
            doctor_count = session.query(Doctor).filter_by(hospital_id=hospital.id).count()
            print(f"Hospital {hospital.slug}: {doctor_count} doctors")
            
        # Check for orphaned records
        for table, model in [
            ("doctors", Doctor),
            ("users", User),
            ("departments", Department),
            ("appointments", Appointment)
        ]:
            orphaned = session.query(model).filter_by(hospital_id=None).count()
            if orphaned > 0:
                print(f"WARNING: Found {orphaned} {table} without hospital_id")
                
        return True
    except Exception as e:
        print(f"Data integrity verification failed: {e}")
        return False
    finally:
        session.close()

def create_backup():
    """Create a backup of critical tables"""
    with engine.connect() as conn:
        # Get table names
        tables = ['doctors', 'users', 'departments', 'appointments', 'tests']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for table in tables:
            backup_table = f"{table}_backup_{timestamp}"
            try:
                conn.execute(text(f"CREATE TABLE {backup_table} AS SELECT * FROM {table};"))
                print(f"Created backup of {table} → {backup_table}")
            except Exception as e:
                print(f"Failed to backup {table}: {e}")

def create_admin_users():
    """Ensure exactly one admin for demo1 and demo2, and one superadmin."""
    session = SessionLocal()
    try:
        hospitals = session.query(Hospital).filter(Hospital.slug.in_(['demo1', 'demo2'])).all()
        print('Hospitals for admin creation:', [(h.id, h.slug, h.name) for h in hospitals])
        if len(hospitals) < 2:
            print("Demo hospitals not found. Skipping admin user creation.")
            return
        # Remove all user_roles for demo hospital admins, then delete the admins
        try:
            from backend.core.models import UserRole
        except ImportError:
            UserRole = None
        for hospital in hospitals:
            # Find all admin user ids for this hospital (non-superadmin)
            admin_ids = [a.id for a in session.query(AdminUser.id).filter_by(hospital_id=hospital.id, is_super_admin=False).all()]
            if UserRole and admin_ids:
                deleted_roles = session.query(UserRole).filter(UserRole.admin_user_id.in_(admin_ids)).delete(synchronize_session=False)
                print(f"Deleted {deleted_roles} user_roles for hospital {hospital.slug}")
            print(f"Deleting existing admins for hospital id={hospital.id}, slug={hospital.slug}")
            deleted = session.query(AdminUser).filter_by(hospital_id=hospital.id, is_super_admin=False).delete(synchronize_session=False)
            print(f"Deleted {deleted} admins for hospital {hospital.slug}")
            admin = AdminUser(
                hospital_id=hospital.id,
                username=f"admin_{hospital.slug}",
                email=f"admin@{hospital.slug}.com",
                first_name="Hospital",
                last_name="Admin",
                is_active=True,
                is_super_admin=False
            )
            password = "Admin@123"  # Default password
            admin.password_hash = AuthService.hash_password(password)
            session.add(admin)
            print(f"Added admin user for hospital id={hospital.id}, slug={hospital.slug}")
        # Ensure superadmin exists, but do not delete or recreate
        superadmin = session.query(AdminUser).filter_by(is_super_admin=True).first()
        if not superadmin:
            superadmin = AdminUser(
                username="superadmin",
                email="superadmin@demohospital.com",
                first_name="Super",
                last_name="Admin",
                is_active=True,
                is_super_admin=True,
                password_hash=AuthService.hash_password("Superadmin@123")
            )
            session.add(superadmin)
        session.commit()
        print("\nAdmin users ensured for all demo hospitals!")
        print("Default passwords:")
        print("- Hospital admins: Admin@123")
        print("- Superadmin: Superadmin@123")
        print("Please change passwords after first login")
        # Print all admin users for verification
        admins = session.query(AdminUser).all()
        print("Current admin users in DB:")
        for a in admins:
            print(f"username={a.username}, hospital_id={a.hospital_id}, is_super_admin={a.is_super_admin}")
        import sys; sys.stdout.flush()
    except Exception as e:
        session.rollback()
        print(f"Error creating admin users: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Running migration: create_admin_users()...")
    create_admin_users()