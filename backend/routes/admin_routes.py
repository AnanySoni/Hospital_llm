"""
Admin Panel API Routes
FastAPI routes for admin panel functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import csv
import io
from datetime import datetime

from core.database import get_db
from core.models import AdminUser, Hospital, Role, UserRole, Permission, AuditLog, Doctor, Patient, Appointment, Department
from services.auth_service import AuthService, get_current_user, require_permission
from services.doctor_service import DoctorService
from schemas.admin_models import (
    LoginRequest, TokenResponse, RefreshTokenRequest,
    AdminUserCreate, AdminUserUpdate, AdminUserResponse,
    HospitalCreate, HospitalUpdate, HospitalResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionResponse, AuditLogResponse,
    HospitalAnalytics, SystemAnalytics,
    TwoFactorSetupResponse, TwoFactorEnableRequest, TwoFactorDisableRequest,
    PaginationParams, PaginatedResponse, SuccessResponse,
    DoctorCreateRequest, DoctorUpdateRequest, DoctorResponse,
    BulkUploadResponse, BulkUploadResult,
    EmailInvitationRequest, EmailInvitationResponse
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["Admin Panel"])

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    client_request: Request = None
):
    """Admin user login"""
    try:
        # Get client IP and user agent
        ip_address = client_request.client.host if client_request else "unknown"
        user_agent = client_request.headers.get("user-agent", "unknown") if client_request else "unknown"
        
        # Login user
        token_response = AuthService.login_user(db, request, ip_address, user_agent)
        
        logger.info(f"Admin login successful: {request.username}")
        return token_response
        
    except Exception as e:
        logger.error(f"Admin login failed: {str(e)}")
        raise

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    try:
        token_response = AuthService.refresh_token(db, request.refresh_token)
        return token_response
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise

@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin user logout"""
    try:
        # Log the logout action
        AuthService._log_action(db, current_user, "user.logout", "user", str(current_user.id), {})
        
        logger.info(f"Admin logout: {current_user.username}")
        return SuccessResponse(message="Logged out successfully")
        
    except Exception as e:
        logger.error(f"Admin logout failed: {str(e)}")
        raise

@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin_user(
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current admin user profile"""
    try:
        return AdminUserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            hospital_id=current_user.hospital_id,
            is_active=current_user.is_active,
            is_super_admin=current_user.is_super_admin,
            last_login=current_user.last_login,
            two_factor_enabled=getattr(current_user, 'two_factor_enabled', False),
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            roles=[]  # TODO: Implement role loading
        )
    except Exception as e:
        logger.error(f"Get current user failed: {str(e)}")
        raise

# ============================================================================
# 2FA ROUTES
# ============================================================================

@router.get("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup 2FA for current user"""
    try:
        setup_data = AuthService.setup_2fa(db, current_user)
        return TwoFactorSetupResponse(**setup_data)
    except Exception as e:
        logger.error(f"2FA setup failed: {str(e)}")
        raise

@router.post("/2fa/enable", response_model=SuccessResponse)
async def enable_2fa(
    request: TwoFactorEnableRequest,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable 2FA for current user"""
    try:
        AuthService.enable_2fa(db, current_user, request.secret, request.verification_code, request.backup_codes)
        return SuccessResponse(message="2FA enabled successfully")
    except Exception as e:
        logger.error(f"2FA enable failed: {str(e)}")
        raise

@router.post("/2fa/disable", response_model=SuccessResponse)
async def disable_2fa(
    request: TwoFactorDisableRequest,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA for current user"""
    try:
        AuthService.disable_2fa(db, current_user, request.verification_code)
        return SuccessResponse(message="2FA disabled successfully")
    except Exception as e:
        logger.error(f"2FA disable failed: {str(e)}")
        raise

# ============================================================================
# ADMIN USER MANAGEMENT ROUTES
# ============================================================================

@router.get("/users", response_model=PaginatedResponse)
async def get_admin_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: AdminUser = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db)
):
    """Get paginated list of admin users"""
    try:
        query = db.query(AdminUser)
        
        # Filter by hospital if not super admin
        if not current_user.is_super_admin:
            query = query.filter(AdminUser.hospital_id == current_user.hospital_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                (AdminUser.username.contains(search)) |
                (AdminUser.email.contains(search)) |
                (AdminUser.first_name.contains(search)) |
                (AdminUser.last_name.contains(search))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset((page - 1) * size).limit(size).all()
        
        # Convert to response models
        user_responses = []
        for user in users:
            # Get user roles and permissions
            roles = []
            permissions = []
            
            user_roles = db.query(UserRole).filter_by(admin_user_id=user.id).all()
            for user_role in user_roles:
                role = db.query(Role).filter_by(id=user_role.role_id).first()
                if role:
                    roles.append({
                        "id": role.id,
                        "name": role.name,
                        "display_name": role.display_name
                    })
                    # Add role permissions
                    if role.permissions:
                        import json
                        try:
                            role_permissions = json.loads(role.permissions)
                            permissions.extend(role_permissions)
                        except json.JSONDecodeError:
                            pass
            
            user_response = AdminUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                hospital_id=user.hospital_id,
                is_super_admin=user.is_super_admin,
                is_active=user.is_active,
                last_login=user.last_login,
                two_factor_enabled=user.two_factor_enabled,
                created_at=user.created_at,
                updated_at=user.updated_at,
                roles=roles,
                permissions=list(set(permissions))  # Remove duplicates
            )
            user_responses.append(user_response)
        
        return PaginatedResponse(
            items=user_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
            has_next=page * size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Get admin users failed: {str(e)}")
        raise

@router.post("/users", response_model=AdminUserResponse)
async def create_admin_user(
    user_data: AdminUserCreate,
    current_user: AdminUser = Depends(require_permission("admin:create")),
    db: Session = Depends(get_db)
):
    """Create a new admin user"""
    try:
        # Check if user can create users for this hospital
        if not current_user.is_super_admin and user_data.hospital_id != current_user.hospital_id:
            raise HTTPException(status_code=403, detail="Cannot create users for other hospitals")
        
        user = AuthService.create_admin_user(db, user_data, current_user)
        
        # Convert to response model
        user_response = AdminUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            hospital_id=user.hospital_id,
            is_super_admin=user.is_super_admin,
            is_active=user.is_active,
            last_login=user.last_login,
            two_factor_enabled=user.two_factor_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[],
            permissions=[]
        )
        
        logger.info(f"Admin user created: {user.username} by {current_user.username}")
        return user_response
        
    except Exception as e:
        logger.error(f"Create admin user failed: {str(e)}")
        raise

@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_admin_user(
    user_id: int,
    current_user: AdminUser = Depends(require_permission("admin:read")),
    db: Session = Depends(get_db)
):
    """Get a specific admin user"""
    try:
        user = db.query(AdminUser).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user can access this user
        if not current_user.is_super_admin and user.hospital_id != current_user.hospital_id:
            raise HTTPException(status_code=403, detail="Cannot access users from other hospitals")
        
        # Get user roles and permissions
        roles = []
        permissions = []
        
        user_roles = db.query(UserRole).filter_by(admin_user_id=user.id).all()
        for user_role in user_roles:
            role = db.query(Role).filter_by(id=user_role.role_id).first()
            if role:
                roles.append({
                    "id": role.id,
                    "name": role.name,
                    "display_name": role.display_name
                })
                if role.permissions:
                    import json
                    try:
                        role_permissions = json.loads(role.permissions)
                        permissions.extend(role_permissions)
                    except json.JSONDecodeError:
                        pass
        
        user_response = AdminUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            hospital_id=user.hospital_id,
            is_super_admin=user.is_super_admin,
            is_active=user.is_active,
            last_login=user.last_login,
            two_factor_enabled=user.two_factor_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=roles,
            permissions=list(set(permissions))
        )
        
        return user_response
        
    except Exception as e:
        logger.error(f"Get admin user failed: {str(e)}")
        raise

@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: int,
    user_data: AdminUserUpdate,
    current_user: AdminUser = Depends(require_permission("admin:update")),
    db: Session = Depends(get_db)
):
    """Update an admin user"""
    try:
        user = db.query(AdminUser).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user can update this user
        if not current_user.is_super_admin and user.hospital_id != current_user.hospital_id:
            raise HTTPException(status_code=403, detail="Cannot update users from other hospitals")
        
        updated_user = AuthService.update_admin_user(db, user_id, user_data, current_user)
        
        # Convert to response model
        user_response = AdminUserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            phone=updated_user.phone,
            hospital_id=updated_user.hospital_id,
            is_super_admin=updated_user.is_super_admin,
            is_active=updated_user.is_active,
            last_login=updated_user.last_login,
            two_factor_enabled=updated_user.two_factor_enabled,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            roles=[],
            permissions=[]
        )
        
        logger.info(f"Admin user updated: {updated_user.username} by {current_user.username}")
        return user_response
        
    except Exception as e:
        logger.error(f"Update admin user failed: {str(e)}")
        raise

# ============================================================================
# HOSPITAL MANAGEMENT ROUTES
# ============================================================================

@router.get("/hospitals", response_model=List[HospitalResponse])
async def get_hospitals(
    current_user: AdminUser = Depends(require_permission("hospital:read")),
    db: Session = Depends(get_db)
):
    """Get list of hospitals"""
    try:
        query = db.query(Hospital)
        
        # Filter by hospital if not super admin
        if not current_user.is_super_admin:
            query = query.filter(Hospital.id == current_user.hospital_id)
        
        hospitals = query.all()
        
        # Convert to response models
        hospital_responses = []
        for hospital in hospitals:
            # Get counts
            admin_users_count = db.query(AdminUser).filter_by(hospital_id=hospital.id).count()
            doctors_count = db.query(Doctor).filter_by(hospital_id=hospital.id).count()
            patients_count = db.query(Patient).filter_by(hospital_id=hospital.id).count()
            
            # Parse features_enabled
            features_enabled = []
            if hospital.features_enabled:
                import json
                try:
                    features_enabled = json.loads(hospital.features_enabled)
                except json.JSONDecodeError:
                    pass
            
            hospital_response = HospitalResponse(
                id=hospital.id,
                hospital_id=hospital.hospital_id,
                name=hospital.name,
                display_name=hospital.display_name,
                address=hospital.address,
                phone=hospital.phone,
                email=hospital.email,
                website=hospital.website,
                subscription_plan=hospital.subscription_plan,
                max_doctors=hospital.max_doctors,
                max_patients=hospital.max_patients,
                google_workspace_domain=hospital.google_workspace_domain,
                subscription_status=hospital.subscription_status,
                subscription_expires=hospital.subscription_expires,
                features_enabled=features_enabled,
                created_at=hospital.created_at,
                updated_at=hospital.updated_at,
                admin_users_count=admin_users_count,
                doctors_count=doctors_count,
                patients_count=patients_count
            )
            hospital_responses.append(hospital_response)
        
        return hospital_responses
        
    except Exception as e:
        logger.error(f"Get hospitals failed: {str(e)}")
        raise

@router.get("/hospitals/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: int,
    current_user: AdminUser = Depends(require_permission("hospital:read")),
    db: Session = Depends(get_db)
):
    """Get a specific hospital"""
    try:
        hospital = db.query(Hospital).filter_by(id=hospital_id).first()
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Check if user can access this hospital
        if not current_user.is_super_admin and hospital.id != current_user.hospital_id:
            raise HTTPException(status_code=403, detail="Cannot access other hospitals")
        
        # Get counts
        admin_users_count = db.query(AdminUser).filter_by(hospital_id=hospital.id).count()
        doctors_count = db.query(Doctor).filter_by(hospital_id=hospital.id).count()
        patients_count = db.query(Patient).filter_by(hospital_id=hospital.id).count()
        
        # Parse features_enabled
        features_enabled = []
        if hospital.features_enabled:
            import json
            try:
                features_enabled = json.loads(hospital.features_enabled)
            except json.JSONDecodeError:
                pass
        
        hospital_response = HospitalResponse(
            id=hospital.id,
            hospital_id=hospital.hospital_id,
            name=hospital.name,
            display_name=hospital.display_name,
            address=hospital.address,
            phone=hospital.phone,
            email=hospital.email,
            website=hospital.website,
            subscription_plan=hospital.subscription_plan,
            max_doctors=hospital.max_doctors,
            max_patients=hospital.max_patients,
            google_workspace_domain=hospital.google_workspace_domain,
            subscription_status=hospital.subscription_status,
            subscription_expires=hospital.subscription_expires,
            features_enabled=features_enabled,
            created_at=hospital.created_at,
            updated_at=hospital.updated_at,
            admin_users_count=admin_users_count,
            doctors_count=doctors_count,
            patients_count=patients_count
        )
        
        return hospital_response
        
    except Exception as e:
        logger.error(f"Get hospital failed: {str(e)}")
        raise

# ============================================================================
# ANALYTICS ROUTES
# ============================================================================

@router.get("/analytics/hospital", response_model=HospitalAnalytics)
async def get_hospital_analytics(
    current_user: AdminUser = Depends(require_permission("analytics:read")),
    db: Session = Depends(get_db)
):
    """Get analytics for current user's hospital"""
    try:
        hospital_id = current_user.hospital_id
        
        # Get basic counts
        total_doctors = db.query(Doctor).filter_by(hospital_id=hospital_id).count()
        total_patients = db.query(Patient).filter_by(hospital_id=hospital_id).count()
        total_appointments = db.query(Appointment).filter_by(hospital_id=hospital_id).count()
        
        # Get today's appointments
        from datetime import date
        today = date.today()
        appointments_today = db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.date == today
        ).count()
        
        # Get this week's appointments
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())
        appointments_this_week = db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.date >= week_start
        ).count()
        
        # Get this month's appointments
        month_start = today.replace(day=1)
        appointments_this_month = db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.date >= month_start
        ).count()
        
        # Get active sessions (placeholder - implement based on your session model)
        active_sessions = 0  # TODO: Implement based on your session tracking
        diagnostic_sessions = 0  # TODO: Implement based on your diagnostic session model
        
        analytics = HospitalAnalytics(
            hospital_id=hospital_id,
            total_doctors=total_doctors,
            total_patients=total_patients,
            total_appointments=total_appointments,
            appointments_today=appointments_today,
            appointments_this_week=appointments_this_week,
            appointments_this_month=appointments_this_month,
            active_sessions=active_sessions,
            diagnostic_sessions=diagnostic_sessions,
            top_departments=[],  # TODO: Implement department analytics
            recent_activities=[]  # TODO: Implement recent activities
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Get hospital analytics failed: {str(e)}")
        raise

@router.get("/analytics/system", response_model=SystemAnalytics)
async def get_system_analytics(
    current_user: AdminUser = Depends(require_permission("analytics:manage")),
    db: Session = Depends(get_db)
):
    """Get system-wide analytics (super admin only)"""
    try:
        if not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail="System analytics require super admin access")
        
        # Get system-wide counts
        total_hospitals = db.query(Hospital).count()
        total_admin_users = db.query(AdminUser).count()
        total_doctors = db.query(Doctor).count()
        total_patients = db.query(Patient).count()
        total_appointments = db.query(Appointment).count()
        
        # Get active hospitals (with recent activity)
        from datetime import datetime, timedelta
        recent_date = datetime.utcnow() - timedelta(days=30)
        active_hospitals = db.query(Hospital).join(Appointment).filter(
            Appointment.date >= recent_date.date()
        ).distinct().count()
        
        analytics = SystemAnalytics(
            total_hospitals=total_hospitals,
            total_admin_users=total_admin_users,
            total_doctors=total_doctors,
            total_patients=total_patients,
            total_appointments=total_appointments,
            active_hospitals=active_hospitals,
            system_health={},  # TODO: Implement system health checks
            recent_audit_logs=[]  # TODO: Implement recent audit logs
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Get system analytics failed: {str(e)}")
        raise

# ============================================================================
# AUDIT LOG ROUTES
# ============================================================================

@router.get("/audit-logs", response_model=PaginatedResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    current_user: AdminUser = Depends(require_permission("analytics:read")),
    db: Session = Depends(get_db)
):
    """Get paginated audit logs"""
    try:
        query = db.query(AuditLog)
        
        # Filter by hospital if not super admin
        if not current_user.is_super_admin:
            query = query.filter(AuditLog.hospital_id == current_user.hospital_id)
        
        # Apply filters
        if action:
            query = query.filter(AuditLog.action.contains(action))
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size).all()
        
        # Convert to response models
        log_responses = []
        for log in logs:
            # Get admin user name
            admin_user = db.query(AdminUser).filter_by(id=log.admin_user_id).first()
            admin_user_name = f"{admin_user.first_name} {admin_user.last_name}" if admin_user else "Unknown"
            
            # Parse details
            details = {}
            if log.details:
                import json
                try:
                    details = json.loads(log.details)
                except json.JSONDecodeError:
                    pass
            
            log_response = AuditLogResponse(
                id=log.id,
                hospital_id=log.hospital_id,
                admin_user_id=log.admin_user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
                admin_user_name=admin_user_name
            )
            log_responses.append(log_response)
        
        return PaginatedResponse(
            items=log_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
            has_next=page * size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Get audit logs failed: {str(e)}")
        raise

# ============================================================================
# DOCTOR MANAGEMENT ROUTES
# ============================================================================

@router.get("/doctors", response_model=List[DoctorResponse])
async def get_doctors(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: AdminUser = Depends(require_permission("doctor:read")),
    db: Session = Depends(get_db)
):
    """Get all doctors for the current hospital"""
    try:
        skip = (page - 1) * size
        doctors = DoctorService.get_doctors(
            db, current_user.hospital_id, skip=skip, limit=size, search=search
        )
        
        # Convert to response format
        doctor_responses = []
        for doctor in doctors:
            doctor_responses.append(DoctorResponse(
                id=doctor.id,
                name=doctor.name,
                email=doctor.email or "",
                phone=doctor.phone_number,
                specialization=doctor.profile or "",
                department="General",  # TODO: Get from department relationship
                experience_years=0,  # TODO: Add to model
                qualification="",  # TODO: Add to model
                consultation_fee=0.0,  # TODO: Add to model
                languages=doctor.tags or [],
                working_hours={},  # TODO: Add to model
                profile_image=None,
                medical_license=None,
                is_active=True,
                calendar_connected=bool(doctor.google_access_token),
                google_calendar_id=doctor.email,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ))
        
        return doctor_responses
        
    except Exception as e:
        logger.error(f"Get doctors failed: {str(e)}")
        raise

@router.post("/doctors", response_model=DoctorResponse)
async def create_doctor(
    doctor_data: DoctorCreateRequest,
    current_user: AdminUser = Depends(require_permission("doctor:create")),
    db: Session = Depends(get_db)
):
    """Create a new doctor"""
    try:
        doctor = DoctorService.create_doctor(db, doctor_data, current_user.hospital_id, current_user)
        
        return DoctorResponse(
            id=doctor.id,
            name=doctor.name,
            email=doctor.email or "",
            phone=doctor.phone_number,
            specialization=doctor.profile or "",
            department="General",
            experience_years=0,
            qualification="",
            consultation_fee=0.0,
            languages=doctor.tags or [],
            working_hours={},
            profile_image=None,
            medical_license=None,
            is_active=True,
            calendar_connected=bool(doctor.google_access_token),
            google_calendar_id=doctor.email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Create doctor failed: {str(e)}")
        raise

@router.put("/doctors/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdateRequest,
    current_user: AdminUser = Depends(require_permission("doctor:update")),
    db: Session = Depends(get_db)
):
    """Update an existing doctor"""
    try:
        doctor = DoctorService.update_doctor(db, doctor_id, doctor_data, current_user)
        
        return DoctorResponse(
            id=doctor.id,
            name=doctor.name,
            email=doctor.email or "",
            phone=doctor.phone_number,
            specialization=doctor.profile or "",
            department="General",
            experience_years=0,
            qualification="",
            consultation_fee=0.0,
            languages=doctor.tags or [],
            working_hours={},
            profile_image=None,
            medical_license=None,
            is_active=True,
            calendar_connected=bool(doctor.google_access_token),
            google_calendar_id=doctor.email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Update doctor failed: {str(e)}")
        raise

@router.delete("/doctors/{doctor_id}", response_model=SuccessResponse)
async def delete_doctor(
    doctor_id: int,
    current_user: AdminUser = Depends(require_permission("doctor:delete")),
    db: Session = Depends(get_db)
):
    """Delete a doctor"""
    try:
        success = DoctorService.delete_doctor(db, doctor_id, current_user)
        
        if success:
            return SuccessResponse(message="Doctor deleted successfully")
        else:
            raise HTTPException(status_code=400, detail="Failed to delete doctor")
        
    except Exception as e:
        logger.error(f"Delete doctor failed: {str(e)}")
        raise

@router.post("/doctors/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_doctors(
    file: UploadFile = File(...),
    current_user: AdminUser = Depends(require_permission("doctor:create")),
    db: Session = Depends(get_db)
):
    """Bulk upload doctors from CSV file"""
    try:
        result = DoctorService.bulk_upload_doctors(db, file, current_user.hospital_id, current_user)
        return result
        
    except Exception as e:
        logger.error(f"Bulk upload doctors failed: {str(e)}")
        raise

@router.get("/doctors/csv-template")
async def get_csv_template(
    current_user: AdminUser = Depends(require_permission("doctor:read"))
):
    """Get CSV template for bulk upload"""
    try:
        template = DoctorService.get_csv_template()
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=template,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=doctors_template.csv"}
        )
        
    except Exception as e:
        logger.error(f"Get CSV template failed: {str(e)}")
        raise

@router.post("/doctors/send-invitations", response_model=EmailInvitationResponse)
async def send_doctor_invitations(
    invitation_data: EmailInvitationRequest,
    current_user: AdminUser = Depends(require_permission("doctor:create")),
    db: Session = Depends(get_db)
):
    """Send email invitations to doctors"""
    try:
        result = DoctorService.send_email_invitations(
            db, invitation_data.doctor_ids, invitation_data.message, current_user
        )
        return result
        
    except Exception as e:
        logger.error(f"Send doctor invitations failed: {str(e)}")
        raise 