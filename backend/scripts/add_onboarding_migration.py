"""
Migration script for Step 5: Database migrations and model updates
Adds onboarding-related columns and tables to support the onboarding flow.

This script is idempotent - safe to run multiple times.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from backend.core.database import engine, SessionLocal

def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.first() is not None

def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists"""
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = :table_name
    """), {"table_name": table_name})
    return result.first() is not None

def index_exists(conn, index_name: str) -> bool:
    """Check if an index exists"""
    result = conn.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE indexname = :index_name
    """), {"index_name": index_name})
    return result.first() is not None

def phase1_critical_fixes(db):
    """Phase 1: Add missing admin_users columns and create onboarding tables"""
    print("\n" + "="*60)
    print("Phase 1: Critical Fixes (admin_users columns + onboarding tables)")
    print("="*60)
    
    with db.connection() as conn:
        # Add missing columns to admin_users
        print("\n📝 Adding columns to admin_users table...")
        
        columns_to_add = [
            ("email_verified", "BOOLEAN DEFAULT FALSE", "Email verification status"),
            ("email_verified_at", "TIMESTAMP NULL", "Email verification timestamp"),
            ("auth_provider", "VARCHAR(50) DEFAULT 'email'", "Authentication provider"),
            ("google_user_id", "VARCHAR(255) UNIQUE NULL", "Google user ID"),
            ("company_name", "VARCHAR(200) NULL", "Company name (temporary)"),
            ("onboarding_session_id", "INTEGER NULL", "Onboarding session reference"),
            ("last_onboarding_step", "INTEGER NULL", "Last onboarding step"),
        ]
        
        for col_name, col_def, description in columns_to_add:
            if column_exists(conn, "admin_users", col_name):
                print(f"  ⏭️  {col_name} already exists, skipping")
            else:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE admin_users 
                        ADD COLUMN {col_name} {col_def}
                    """))
                    print(f"  ✅ Added {col_name} ({description})")
                except Exception as e:
                    print(f"  ❌ Error adding {col_name}: {e}")
        
        # Create onboarding_sessions table
        print("\n📝 Creating onboarding_sessions table...")
        if table_exists(conn, "onboarding_sessions"):
            print("  ⏭️  onboarding_sessions already exists, skipping")
        else:
            try:
                conn.execute(text("""
                    CREATE TABLE onboarding_sessions (
                        id SERIAL PRIMARY KEY,
                        admin_user_id INTEGER NOT NULL,
                        hospital_id INTEGER NULL,
                        current_step INTEGER DEFAULT 1,
                        completed_steps TEXT DEFAULT '[]',
                        partial_data TEXT DEFAULT '{}',
                        status VARCHAR(20) DEFAULT 'in_progress',
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP NULL,
                        abandoned_at TIMESTAMP NULL
                    )
                """))
                print("  ✅ Created onboarding_sessions table")
            except Exception as e:
                print(f"  ❌ Error creating onboarding_sessions: {e}")
        
        # Create email_verifications table
        print("\n📝 Creating email_verifications table...")
        if table_exists(conn, "email_verifications"):
            print("  ⏭️  email_verifications already exists, skipping")
        else:
            try:
                conn.execute(text("""
                    CREATE TABLE email_verifications (
                        id SERIAL PRIMARY KEY,
                        admin_user_id INTEGER NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        token VARCHAR(255) UNIQUE NOT NULL,
                        verification_type VARCHAR(50) DEFAULT 'email_verification',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        verified_at TIMESTAMP NULL
                    )
                """))
                print("  ✅ Created email_verifications table")
            except Exception as e:
                print(f"  ❌ Error creating email_verifications: {e}")
        
        # Create reserved_slugs table
        print("\n📝 Creating reserved_slugs table...")
        if table_exists(conn, "reserved_slugs"):
            print("  ⏭️  reserved_slugs already exists, skipping")
        else:
            try:
                conn.execute(text("""
                    CREATE TABLE reserved_slugs (
                        slug VARCHAR(50) PRIMARY KEY,
                        reason VARCHAR(100) NULL,
                        reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("  ✅ Created reserved_slugs table")
            except Exception as e:
                print(f"  ❌ Error creating reserved_slugs: {e}")
        
        db.commit()
        print("\n✅ Phase 1 completed!")

def phase2_hospital_updates(db):
    """Phase 2: Add onboarding fields to hospitals table"""
    print("\n" + "="*60)
    print("Phase 2: Hospital Model Updates")
    print("="*60)
    
    with db.connection() as conn:
        print("\n📝 Adding columns to hospitals table...")
        
        # Add onboarding_status
        if column_exists(conn, "hospitals", "onboarding_status"):
            print("  ⏭️  onboarding_status already exists, skipping")
        else:
            try:
                conn.execute(text("""
                    ALTER TABLE hospitals 
                    ADD COLUMN onboarding_status VARCHAR(20) DEFAULT 'completed'
                """))
                # Set existing hospitals to 'completed'
                conn.execute(text("""
                    UPDATE hospitals 
                    SET onboarding_status = 'completed' 
                    WHERE onboarding_status IS NULL
                """))
                print("  ✅ Added onboarding_status (existing hospitals set to 'completed')")
            except Exception as e:
                print(f"  ❌ Error adding onboarding_status: {e}")
        
        # Add onboarding_completed_at
        if column_exists(conn, "hospitals", "onboarding_completed_at"):
            print("  ⏭️  onboarding_completed_at already exists, skipping")
        else:
            try:
                conn.execute(text("""
                    ALTER TABLE hospitals 
                    ADD COLUMN onboarding_completed_at TIMESTAMP NULL
                """))
                print("  ✅ Added onboarding_completed_at")
            except Exception as e:
                print(f"  ❌ Error adding onboarding_completed_at: {e}")
        
        # Add created_by_admin_id
        if column_exists(conn, "hospitals", "created_by_admin_id"):
            print("  ⏭️  created_by_admin_id already exists, skipping")
        else:
            try:
                conn.execute(text("""
                    ALTER TABLE hospitals 
                    ADD COLUMN created_by_admin_id INTEGER NULL
                """))
                print("  ✅ Added created_by_admin_id (existing hospitals set to NULL)")
            except Exception as e:
                print(f"  ❌ Error adding created_by_admin_id: {e}")
        
        db.commit()
        print("\n✅ Phase 2 completed!")

def phase3_indexes_and_constraints(db):
    """Phase 3: Add indexes and foreign key constraints"""
    print("\n" + "="*60)
    print("Phase 3: Indexes and Foreign Key Constraints")
    print("="*60)
    
    with db.connection() as conn:
        # Add indexes
        print("\n📝 Creating indexes...")
        
        indexes = [
            ("idx_admin_users_email_verified", "admin_users", "email_verified"),
            ("idx_admin_users_google_user_id", "admin_users", "google_user_id"),
            ("idx_admin_users_onboarding_session_id", "admin_users", "onboarding_session_id"),
            ("idx_onboarding_sessions_admin_user_id", "onboarding_sessions", "admin_user_id"),
            ("idx_email_verifications_token", "email_verifications", "token"),
            ("idx_email_verifications_admin_user_id", "email_verifications", "admin_user_id"),
            ("idx_hospitals_created_by_admin_id", "hospitals", "created_by_admin_id"),
        ]
        
        for idx_name, table_name, column_name in indexes:
            if index_exists(conn, idx_name):
                print(f"  ⏭️  {idx_name} already exists, skipping")
            else:
                try:
                    conn.execute(text(f"""
                        CREATE INDEX {idx_name} 
                        ON {table_name}({column_name})
                    """))
                    print(f"  ✅ Created index {idx_name}")
                except Exception as e:
                    print(f"  ❌ Error creating {idx_name}: {e}")
        
        # Add foreign key constraints
        print("\n📝 Adding foreign key constraints...")
        
        # Check if FK constraints already exist by trying to add them
        fk_constraints = [
            {
                "name": "fk_admin_users_onboarding_session",
                "table": "admin_users",
                "column": "onboarding_session_id",
                "ref_table": "onboarding_sessions",
                "ref_column": "id",
                "on_delete": "SET NULL"
            },
            {
                "name": "fk_hospitals_created_by_admin",
                "table": "hospitals",
                "column": "created_by_admin_id",
                "ref_table": "admin_users",
                "ref_column": "id",
                "on_delete": "SET NULL"
            },
            {
                "name": "fk_onboarding_sessions_admin_user",
                "table": "onboarding_sessions",
                "column": "admin_user_id",
                "ref_table": "admin_users",
                "ref_column": "id",
                "on_delete": "CASCADE"
            },
            {
                "name": "fk_onboarding_sessions_hospital",
                "table": "onboarding_sessions",
                "column": "hospital_id",
                "ref_table": "hospitals",
                "ref_column": "id",
                "on_delete": "SET NULL"
            },
            {
                "name": "fk_email_verifications_admin_user",
                "table": "email_verifications",
                "column": "admin_user_id",
                "ref_table": "admin_users",
                "ref_column": "id",
                "on_delete": "CASCADE"
            },
        ]
        
        for fk in fk_constraints:
            # Check if constraint exists
            result = conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE constraint_name = :constraint_name
            """), {"constraint_name": fk["name"]})
            
            if result.first():
                print(f"  ⏭️  {fk['name']} already exists, skipping")
            else:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE {fk['table']} 
                        ADD CONSTRAINT {fk['name']} 
                        FOREIGN KEY ({fk['column']}) 
                        REFERENCES {fk['ref_table']}({fk['ref_column']}) 
                        ON DELETE {fk['on_delete']}
                    """))
                    print(f"  ✅ Added foreign key {fk['name']}")
                except Exception as e:
                    print(f"  ❌ Error adding {fk['name']}: {e}")
        
        db.commit()
        print("\n✅ Phase 3 completed!")

def phase4_verification(db):
    """Phase 4: Verify migration results"""
    print("\n" + "="*60)
    print("Phase 4: Verification")
    print("="*60)
    
    with db.connection() as conn:
        print("\n🔍 Verifying migration results...")
        
        # Check admin_users columns
        print("\n📋 Checking admin_users columns:")
        required_columns = [
            "email_verified", "email_verified_at", "auth_provider",
            "google_user_id", "company_name", "onboarding_session_id", "last_onboarding_step"
        ]
        all_present = True
        for col in required_columns:
            exists = column_exists(conn, "admin_users", col)
            status = "✅" if exists else "❌"
            print(f"  {status} {col}")
            if not exists:
                all_present = False
        
        # Check hospitals columns
        print("\n📋 Checking hospitals columns:")
        hospital_columns = ["onboarding_status", "onboarding_completed_at", "created_by_admin_id"]
        for col in hospital_columns:
            exists = column_exists(conn, "hospitals", col)
            status = "✅" if exists else "❌"
            print(f"  {status} {col}")
            if not exists:
                all_present = False
        
        # Check tables
        print("\n📋 Checking tables:")
        required_tables = ["onboarding_sessions", "email_verifications", "reserved_slugs"]
        for table in required_tables:
            exists = table_exists(conn, table)
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")
            if not exists:
                all_present = False
        
        # Check indexes
        print("\n📋 Checking indexes:")
        required_indexes = [
            "idx_admin_users_email_verified",
            "idx_onboarding_sessions_admin_user_id",
            "idx_email_verifications_token"
        ]
        for idx in required_indexes:
            exists = index_exists(conn, idx)
            status = "✅" if exists else "❌"
            print(f"  {status} {idx}")
        
        # Count existing hospitals
        result = conn.execute(text("SELECT COUNT(*) FROM hospitals"))
        hospital_count = result.scalar()
        print(f"\n📊 Existing hospitals: {hospital_count}")
        
        if all_present:
            print("\n✅ All required columns and tables are present!")
        else:
            print("\n⚠️  Some columns or tables are missing. Please review the errors above.")
        
        return all_present

def main():
    """Run the complete migration"""
    print("="*60)
    print("Onboarding Database Migration - Step 5")
    print("="*60)
    print("This script will:")
    print("  1. Add missing columns to admin_users")
    print("  2. Create onboarding-related tables")
    print("  3. Add columns to hospitals table")
    print("  4. Create indexes and foreign key constraints")
    print("  5. Verify all changes")
    print("\nThis script is idempotent - safe to run multiple times.")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Run all phases
        phase1_critical_fixes(db)
        phase2_hospital_updates(db)
        phase3_indexes_and_constraints(db)
        verification_passed = phase4_verification(db)
        
        print("\n" + "="*60)
        if verification_passed:
            print("✅ Migration completed successfully!")
            print("You can now use the onboarding flow.")
        else:
            print("⚠️  Migration completed with warnings.")
            print("Please review the errors above.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()



