"""
Initialize Admin Panel
Creates default hospitals, roles, permissions, and super admin user
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Hospital, AdminUser, Role, Permission, UserRole
from services.auth_service import AuthService
import json

def create_default_permissions(db: Session):
    """Create default permissions"""
    permissions = [
        # User management
        {"code": "admin:create", "name": "Create Admin Users", "description": "Create new admin users", "resource_type": "admin", "action": "create"},
        {"code": "admin:read", "name": "Read Admin Users", "description": "View admin user details", "resource_type": "admin", "action": "read"},
        {"code": "admin:update", "name": "Update Admin Users", "description": "Modify admin user details", "resource_type": "admin", "action": "update"},
        {"code": "admin:delete", "name": "Delete Admin Users", "description": "Remove admin users", "resource_type": "admin", "action": "delete"},
        
        # Hospital management
        {"code": "hospital:create", "name": "Create Hospitals", "description": "Create new hospitals", "resource_type": "hospital", "action": "create"},
        {"code": "hospital:read", "name": "Read Hospitals", "description": "View hospital details", "resource_type": "hospital", "action": "read"},
        {"code": "hospital:update", "name": "Update Hospitals", "description": "Modify hospital details", "resource_type": "hospital", "action": "update"},
        {"code": "hospital:delete", "name": "Delete Hospitals", "description": "Remove hospitals", "resource_type": "hospital", "action": "delete"},
        
        # Doctor management
        {"code": "doctor:create", "name": "Create Doctors", "description": "Add new doctors", "resource_type": "doctor", "action": "create"},
        {"code": "doctor:read", "name": "Read Doctors", "description": "View doctor details", "resource_type": "doctor", "action": "read"},
        {"code": "doctor:update", "name": "Update Doctors", "description": "Modify doctor details", "resource_type": "doctor", "action": "update"},
        {"code": "doctor:delete", "name": "Delete Doctors", "description": "Remove doctors", "resource_type": "doctor", "action": "delete"},
        
        # Patient management
        {"code": "patient:create", "name": "Create Patients", "description": "Add new patients", "resource_type": "patient", "action": "create"},
        {"code": "patient:read", "name": "Read Patients", "description": "View patient details", "resource_type": "patient", "action": "read"},
        {"code": "patient:update", "name": "Update Patients", "description": "Modify patient details", "resource_type": "patient", "action": "update"},
        {"code": "patient:delete", "name": "Delete Patients", "description": "Remove patients", "resource_type": "patient", "action": "delete"},
        
        # Appointment management
        {"code": "appointment:create", "name": "Create Appointments", "description": "Book appointments", "resource_type": "appointment", "action": "create"},
        {"code": "appointment:read", "name": "Read Appointments", "description": "View appointment details", "resource_type": "appointment", "action": "read"},
        {"code": "appointment:update", "name": "Update Appointments", "description": "Modify appointments", "resource_type": "appointment", "action": "update"},
        {"code": "appointment:delete", "name": "Delete Appointments", "description": "Cancel appointments", "resource_type": "appointment", "action": "delete"},
        
        # Analytics
        {"code": "analytics:read", "name": "Read Analytics", "description": "View hospital analytics", "resource_type": "analytics", "action": "read"},
        {"code": "analytics:manage", "name": "Manage Analytics", "description": "Manage system analytics", "resource_type": "analytics", "action": "manage"},
        
        # System management
        {"code": "system:manage", "name": "System Management", "description": "Manage system settings", "resource_type": "system", "action": "manage"},
    ]
    
    for perm_data in permissions:
        existing = db.query(Permission).filter_by(code=perm_data["code"]).first()
        if not existing:
            permission = Permission(**perm_data)
            db.add(permission)
            print(f"Created permission: {perm_data['code']}")
    
    db.commit()
    print("Default permissions created successfully")

def create_default_roles(db: Session):
    """Create default roles with permissions"""
    roles_data = [
        {
            "name": "super_admin",
            "display_name": "Super Administrator",
            "description": "Full system access across all hospitals",
            "is_system_role": True,
            "permissions": [
                "admin:create", "admin:read", "admin:update", "admin:delete",
                "hospital:create", "hospital:read", "hospital:update", "hospital:delete",
                "doctor:create", "doctor:read", "doctor:update", "doctor:delete",
                "patient:create", "patient:read", "patient:update", "patient:delete",
                "appointment:create", "appointment:read", "appointment:update", "appointment:delete",
                "analytics:read", "analytics:manage", "system:manage"
            ]
        },
        {
            "name": "hospital_admin",
            "display_name": "Hospital Administrator",
            "description": "Full access to hospital operations",
            "is_system_role": True,
            "permissions": [
                "admin:create", "admin:read", "admin:update",
                "doctor:create", "doctor:read", "doctor:update", "doctor:delete",
                "patient:create", "patient:read", "patient:update", "patient:delete",
                "appointment:create", "appointment:read", "appointment:update", "appointment:delete",
                "analytics:read"
            ]
        },
        {
            "name": "department_head",
            "display_name": "Department Head",
            "description": "Manage department doctors and appointments",
            "is_system_role": True,
            "permissions": [
                "doctor:read", "doctor:update",
                "patient:read", "patient:update",
                "appointment:create", "appointment:read", "appointment:update",
                "analytics:read"
            ]
        },
        {
            "name": "receptionist",
            "display_name": "Receptionist",
            "description": "Handle patient registration and appointments",
            "is_system_role": True,
            "permissions": [
                "patient:create", "patient:read", "patient:update",
                "appointment:create", "appointment:read", "appointment:update",
                "analytics:read"
            ]
        }
    ]
    
    for role_data in roles_data:
        existing = db.query(Role).filter_by(name=role_data["name"]).first()
        if not existing:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system_role=role_data["is_system_role"],
                permissions=json.dumps(role_data["permissions"])
            )
            db.add(role)
            print(f"Created role: {role_data['name']}")
    
    db.commit()
    print("Default roles created successfully")

def create_default_hospitals(db: Session):
    """Create default hospitals"""
    hospitals_data = [
        {
            "hospital_id": "demo_hospital",
            "name": "Demo Hospital",
            "display_name": "Demo Hospital - Main Branch",
            "address": "123 Healthcare Street, Medical District",
            "phone": "+91-9876543210",
            "email": "admin@demohospital.com",
            "website": "https://demohospital.com",
            "subscription_plan": "premium",
            "max_doctors": 50,
            "max_patients": 5000,
            "google_workspace_domain": "demohospital.com"
        },
        {
            "hospital_id": "apollo_delhi",
            "name": "Apollo Hospitals",
            "display_name": "Apollo Hospitals - Delhi",
            "address": "456 Apollo Road, Delhi",
            "phone": "+91-9876543211",
            "email": "admin@apollodelhi.com",
            "website": "https://apollodelhi.com",
            "subscription_plan": "enterprise",
            "max_doctors": 100,
            "max_patients": 10000,
            "google_workspace_domain": "apollodelhi.com"
        }
    ]
    
    for hospital_data in hospitals_data:
        existing = db.query(Hospital).filter_by(hospital_id=hospital_data["hospital_id"]).first()
        if not existing:
            hospital = Hospital(**hospital_data)
            db.add(hospital)
            print(f"Created hospital: {hospital_data['name']}")
    
    db.commit()
    print("Default hospitals created successfully")

def create_super_admin(db: Session):
    """Create a super admin user"""
    # Get the demo hospital
    demo_hospital = db.query(Hospital).filter_by(hospital_id="demo_hospital").first()
    if not demo_hospital:
        print("Demo hospital not found. Please create hospitals first.")
        return
    
    # Get super admin role
    super_admin_role = db.query(Role).filter_by(name="super_admin").first()
    if not super_admin_role:
        print("Super admin role not found. Please create roles first.")
        return
    
    # Check if super admin already exists
    existing_admin = db.query(AdminUser).filter_by(username="superadmin").first()
    if existing_admin:
        print("Super admin user already exists")
        return
    
    # Create super admin user
    super_admin = AdminUser(
        hospital_id=demo_hospital.id,
        username="superadmin",
        email="superadmin@demohospital.com",
        password_hash=AuthService.hash_password("Admin@123"),
        first_name="Super",
        last_name="Administrator",
        phone="+91-9876543210",
        is_active=True,
        is_super_admin=True
    )
    db.add(super_admin)
    db.flush()  # Get the ID
    
    # Assign super admin role
    user_role = UserRole(
        admin_user_id=super_admin.id,
        role_id=super_admin_role.id,
        granted_by=super_admin.id
    )
    db.add(user_role)
    
    db.commit()
    print("Super admin user created successfully")
    print("Username: superadmin")
    print("Password: Admin@123")
    print("Email: superadmin@demohospital.com")

def main():
    """Main initialization function"""
    print("Initializing Admin Panel...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create permissions first
        print("\n1. Creating default permissions...")
        create_default_permissions(db)
        
        # Create roles
        print("\n2. Creating default roles...")
        create_default_roles(db)
        
        # Create hospitals
        print("\n3. Creating default hospitals...")
        create_default_hospitals(db)
        
        # Create super admin
        print("\n4. Creating super admin user...")
        create_super_admin(db)
        
        print("\n✅ Admin panel initialization completed successfully!")
        print("\n📋 Default Login Credentials:")
        print("   Username: superadmin")
        print("   Password: Admin@123")
        print("   Email: superadmin@demohospital.com")
        print("\n🔗 Access the admin panel at: http://localhost:8000/admin")
        
    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 