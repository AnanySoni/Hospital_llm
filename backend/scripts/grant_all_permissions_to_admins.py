"""
Grant all required permissions to all hospital admin users.
This script will ensure that every hospital admin user has the 'hospital_admin' role and that the role has all required permissions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.models import AdminUser, Role, UserRole
import json

def grant_permissions_to_hospital_admins(db: Session):
    # Get the hospital_admin role
    hospital_admin_role = db.query(Role).filter_by(name="hospital_admin").first()
    if not hospital_admin_role:
        print("Hospital admin role not found.")
        return

    # Ensure the hospital_admin role has all required permissions
    # NOTE: This list is the source of truth for what hospital admins can do.
    # It must stay in sync with any new require_permission("...") usages,
    # such as department:* and calendar:* permissions.
    required_permissions = [
        # Admin users
        "admin:create", "admin:read", "admin:update",

        # Doctors
        "doctor:create", "doctor:read", "doctor:update", "doctor:delete",

        # Patients
        "patient:create", "patient:read", "patient:update", "patient:delete",

        # Appointments
        "appointment:create", "appointment:read", "appointment:update", "appointment:delete",

        # Analytics and hospitals
        "analytics:read",
        "hospital:read",

        # Departments
        "department:create", "department:read", "department:update", "department:delete",

        # Calendar / scheduling
        "calendar:read", "calendar:manage",
    ]
    current_permissions = set(json.loads(hospital_admin_role.permissions or "[]"))
    updated_permissions = set(required_permissions) | current_permissions
    hospital_admin_role.permissions = json.dumps(list(updated_permissions))
    db.add(hospital_admin_role)
    db.commit()
    print(f"Updated hospital_admin role permissions: {updated_permissions}")

    # Assign hospital_admin role to all non-super-admin users (if not already assigned)
    admin_users = db.query(AdminUser).filter_by(is_super_admin=False).all()
    for admin in admin_users:
        has_role = db.query(UserRole).filter_by(admin_user_id=admin.id, role_id=hospital_admin_role.id).first()
        if not has_role:
            user_role = UserRole(
                admin_user_id=admin.id,
                role_id=hospital_admin_role.id,
                granted_by=admin.id
            )
            db.add(user_role)
            print(f"Granted hospital_admin role to user: {admin.username}")
    db.commit()
    print("All hospital admin users now have the correct permissions.")

def main():
    db = next(get_db())
    try:
        grant_permissions_to_hospital_admins(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
