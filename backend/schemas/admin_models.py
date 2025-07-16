"""
Admin Panel Pydantic Models
Schema definitions for admin panel API requests and responses
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================

class LoginRequest(BaseModel):
    """Login request model"""
    username: str  # Can be username or email
    password: str
    two_factor_code: Optional[str] = None

class TokenResponse(BaseModel):
    """JWT token response model"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str

# ============================================================================
# ADMIN USER MODELS
# ============================================================================

class AdminUserBase(BaseModel):
    """Base admin user model"""
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_super_admin: bool = False

class AdminUserCreate(AdminUserBase):
    """Create admin user model"""
    password: str
    hospital_id: int
    role_ids: Optional[List[int]] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class AdminUserUpdate(BaseModel):
    """Update admin user model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class AdminUserResponse(AdminUserBase):
    """Admin user response model"""
    id: int
    hospital_id: int
    is_active: bool
    is_super_admin: bool
    last_login: Optional[datetime] = None
    two_factor_enabled: bool
    created_at: datetime
    updated_at: datetime
    roles: List[Dict[str, Any]] = []
    permissions: List[str] = []

    class Config:
        from_attributes = True

# ============================================================================
# HOSPITAL MODELS
# ============================================================================

class HospitalBase(BaseModel):
    """Base hospital model"""
    hospital_id: str
    name: str
    display_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    subscription_plan: str = "basic"
    max_doctors: int = 10
    max_patients: int = 1000
    google_workspace_domain: Optional[str] = None

class HospitalCreate(HospitalBase):
    """Create hospital model"""
    pass

class HospitalUpdate(BaseModel):
    """Update hospital model"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    subscription_plan: Optional[str] = None
    max_doctors: Optional[int] = None
    max_patients: Optional[int] = None
    google_workspace_domain: Optional[str] = None

class HospitalResponse(HospitalBase):
    """Hospital response model"""
    id: int
    subscription_status: str
    subscription_expires: Optional[datetime] = None
    features_enabled: List[str] = []
    created_at: datetime
    updated_at: datetime
    admin_users_count: int = 0
    doctors_count: int = 0
    patients_count: int = 0

    class Config:
        from_attributes = True

# ============================================================================
# ROLE MODELS
# ============================================================================

class RoleBase(BaseModel):
    """Base role model"""
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str] = []

class RoleCreate(RoleBase):
    """Create role model"""
    pass

class RoleUpdate(BaseModel):
    """Update role model"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleResponse(RoleBase):
    """Role response model"""
    id: int
    is_system_role: bool
    created_at: datetime
    users_count: int = 0

    class Config:
        from_attributes = True

# ============================================================================
# PERMISSION MODELS
# ============================================================================

class PermissionResponse(BaseModel):
    """Permission response model"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    resource_type: Optional[str] = None
    action: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# AUDIT LOG MODELS
# ============================================================================

class AuditLogResponse(BaseModel):
    """Audit log response model"""
    id: int
    hospital_id: int
    admin_user_id: int
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    admin_user_name: Optional[str] = None

    class Config:
        from_attributes = True

# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class HospitalAnalytics(BaseModel):
    """Hospital analytics model"""
    hospital_id: int
    total_doctors: int
    total_patients: int
    total_appointments: int
    appointments_today: int
    appointments_this_week: int
    appointments_this_month: int
    active_sessions: int
    diagnostic_sessions: int
    revenue_this_month: Optional[float] = None
    top_departments: List[Dict[str, Any]] = []
    recent_activities: List[Dict[str, Any]] = []

class SystemAnalytics(BaseModel):
    """System-wide analytics model"""
    total_hospitals: int
    total_admin_users: int
    total_doctors: int
    total_patients: int
    total_appointments: int
    active_hospitals: int
    system_health: Dict[str, Any] = {}
    recent_audit_logs: List[Dict[str, Any]] = []

# ============================================================================
# 2FA MODELS
# ============================================================================

class TwoFactorSetupResponse(BaseModel):
    """2FA setup response model"""
    secret: str
    backup_codes: List[str]
    provisioning_uri: str
    qr_code_data: str

class TwoFactorEnableRequest(BaseModel):
    """2FA enable request model"""
    secret: str
    verification_code: str
    backup_codes: List[str]

class TwoFactorDisableRequest(BaseModel):
    """2FA disable request model"""
    verification_code: str

# ============================================================================
# PAGINATION MODELS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    size: int = 20
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"  # asc or desc
    search: Optional[str] = None

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    error: str = "Validation Error"
    detail: List[Dict[str, Any]] = []

# ============================================================================
# SUCCESS MODELS
# ============================================================================

class SuccessResponse(BaseModel):
    """Success response model"""
    message: str
    data: Optional[Dict[str, Any]] = None

class BulkOperationResponse(BaseModel):
    """Bulk operation response model"""
    message: str
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = [] 

# ============================================================================
# DOCTOR MANAGEMENT SCHEMAS
# ============================================================================

class DoctorCreateRequest(BaseModel):
    """Request model for creating a new doctor"""
    name: str
    email: str
    phone: Optional[str] = None
    specialization: str
    department: str
    experience_years: int
    qualification: str
    consultation_fee: float
    languages: List[str] = []
    working_hours: Optional[dict] = None
    profile_image: Optional[str] = None
    medical_license: Optional[str] = None
    
class DoctorUpdateRequest(BaseModel):
    """Request model for updating doctor information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None
    experience_years: Optional[int] = None
    qualification: Optional[str] = None
    consultation_fee: Optional[float] = None
    languages: Optional[List[str]] = None
    working_hours: Optional[dict] = None
    profile_image: Optional[str] = None
    medical_license: Optional[str] = None
    is_active: Optional[bool] = None

class DoctorResponse(BaseModel):
    """Response model for doctor information"""
    id: int
    name: str
    email: str
    phone: Optional[str]
    specialization: str
    department: str
    experience_years: int
    qualification: str
    consultation_fee: float
    languages: List[str]
    working_hours: Optional[dict]
    profile_image: Optional[str]
    medical_license: Optional[str]
    is_active: bool
    calendar_connected: bool
    google_calendar_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# BULK UPLOAD SCHEMAS
# ============================================================================

class BulkUploadResult(BaseModel):
    """Result of a single row in bulk upload"""
    row_number: int
    status: str  # 'success', 'error', 'warning'
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    message: str
    errors: List[str] = []

class BulkUploadResponse(BaseModel):
    """Response model for bulk upload operations"""
    total_rows: int
    successful: int
    failed: int
    warnings: int
    results: List[BulkUploadResult]
    summary: str

# ============================================================================
# DEPARTMENT MANAGEMENT SCHEMAS
# ============================================================================

class DepartmentCreateRequest(BaseModel):
    """Request model for creating a new department"""
    name: str
    description: Optional[str] = None
    head_doctor_id: Optional[int] = None
    
class DepartmentUpdateRequest(BaseModel):
    """Request model for updating department information"""
    name: Optional[str] = None
    description: Optional[str] = None
    head_doctor_id: Optional[int] = None
    is_active: Optional[bool] = None

class DepartmentResponse(BaseModel):
    """Response model for department information"""
    id: int
    name: str
    description: Optional[str]
    head_doctor_id: Optional[int]
    head_doctor_name: Optional[str]
    doctor_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# EMAIL INVITATION SCHEMAS
# ============================================================================

class EmailInvitationRequest(BaseModel):
    """Request model for sending email invitations"""
    doctor_ids: List[int]
    message: Optional[str] = None
    
class EmailInvitationResponse(BaseModel):
    """Response model for email invitation results"""
    sent: int
    failed: int
    results: List[dict] 