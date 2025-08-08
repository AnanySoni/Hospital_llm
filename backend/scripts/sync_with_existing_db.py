"""
Sync local models with existing database schema
This script will connect to your existing database and generate the correct models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, MetaData, inspect
from backend.core.database import engine

def inspect_existing_database():
    """Inspect the existing database and show all tables and columns"""
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("🔍 Existing database schema:")
    print("=" * 50)
    
    for table_name in sorted(tables):
        print(f"\n📋 Table: {table_name}")
        columns = inspector.get_columns(table_name)
        
        for column in columns:
            col_type = str(column['type'])
            nullable = "" if column['nullable'] else " NOT NULL"
            default = f" DEFAULT {column['default']}" if column['default'] else ""
            print(f"  - {column['name']}: {col_type}{nullable}{default}")
        
        # Show foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            print(f"  🔗 Foreign Keys:")
            for fk in foreign_keys:
                print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    print("\n" + "=" * 50)
    print(f"Total tables found: {len(tables)}")
    
    return tables

def check_patient_history_capabilities():
    """Check what patient history capabilities exist"""
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    patient_related_tables = [
        'patients', 'medical_history', 'family_history', 'medications',
        'symptom_logs', 'patient_notes', 'test_results', 'test_bookings'
    ]
    
    print("\n🏥 Patient History Capabilities:")
    print("=" * 40)
    
    for table in patient_related_tables:
        if table in tables:
            print(f"✅ {table}")
            columns = inspector.get_columns(table)
            key_columns = [col['name'] for col in columns if 'patient' in col['name'].lower() or col['name'] in ['id', 'created_at', 'updated_at']]
            print(f"   Key columns: {', '.join(key_columns)}")
        else:
            print(f"❌ {table} - missing")
    
    # Check if we have session tracking
    session_tables = ['session_users', 'conversation_sessions']
    print(f"\n🔄 Session Tracking:")
    for table in session_tables:
        if table in tables:
            print(f"✅ {table}")
        else:
            print(f"❌ {table} - missing (we can add this)")

if __name__ == "__main__":
    try:
        print("Connecting to your existing database...")
        tables = inspect_existing_database()
        check_patient_history_capabilities()
        
        print(f"\n💡 Next steps:")
        print(f"1. Update local models to match your existing schema")
        print(f"2. Add session tracking tables if needed")
        print(f"3. Connect the LLM to use your existing patient history")
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("Please check your database connection settings in backend/core/database.py") 