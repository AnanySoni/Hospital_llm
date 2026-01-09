"""
Authentication Service for Admin Panel
Handles JWT token management, password hashing, and role-based permissions
"""

import jwt
import bcrypt
import secrets
import pyotp
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.models import AdminUser, Hospital, Role, UserRole, Permission, AuditLog
from backend.core.database import get_db
from backend.schemas.admin_models import AdminUserCreate, AdminUserUpdate, LoginRequest, TokenResponse

# JWT Configuration
SECRET_KEY = "4ujiOYQONbkD-GG8yCqRFkLZ1NVDokVyYABo8LtDWtE"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security
security = HTTPBearer()

class AuthService:
    """Authentication service for admin users"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        # Always include hospital_id and is_super_admin in token
        if 'hospital_id' not in to_encode:
            to_encode['hospital_id'] = None
        if 'is_super_admin' not in to_encode:
            to_encode['is_super_admin'] = False
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[AdminUser]:
        """Authenticate a user with username and password"""
        user = db.query(AdminUser).filter_by(username=username).first()
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is deactivated")
        
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(status_code=401, detail="Account is temporarily locked")
        
        return user
    
    @staticmethod
    def login_user(db: Session, login_request: LoginRequest, ip_address: str, user_agent: str) -> TokenResponse:
        """Login a user and return JWT tokens"""
        # Find user by username or email
        user = db.query(AdminUser).filter(
            (AdminUser.username == login_request.username) | 
            (AdminUser.email == login_request.username)
        ).first()
        
        if not user:
            AuthService._increment_login_attempts(db, login_request.username)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(status_code=401, detail="Account is temporarily locked")
        
        if not AuthService.verify_password(login_request.password, user.password_hash):
            AuthService._increment_login_attempts(db, user.username)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if user.two_factor_enabled:
            if not login_request.two_factor_code:
                raise HTTPException(status_code=401, detail="2FA code required")
            
            if not AuthService._verify_2fa_code(user, login_request.two_factor_code):
                raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
        user.login_attempts = 0
        user.last_login = datetime.utcnow()
        db.commit()
        
        permissions = AuthService._get_user_permissions(db, user)
        
        # Validate user belongs to correct hospital (if not superadmin)
        if not user.is_super_admin:
            requested_hospital_id = getattr(login_request, 'hospital_id', None)
            if requested_hospital_id and user.hospital_id != requested_hospital_id:
                raise HTTPException(status_code=403, detail="User does not belong to requested hospital")
        
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "hospital_id": user.hospital_id,
            "is_super_admin": user.is_super_admin,
            "permissions": permissions
        }
        
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)
        
        AuthService._log_action(db, user, "user.login", "user", str(user.id), {
            "ip_address": ip_address,
            "user_agent": user_agent
        })
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "hospital_id": user.hospital_id,
                "is_super_admin": user.is_super_admin,
                "permissions": permissions
            }
        )
    
    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a refresh token"""
        try:
            payload = AuthService.verify_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            user_id = payload.get("user_id")
            user = db.query(AdminUser).filter_by(id=user_id).first()
            
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User not found or inactive")
            
            # Get updated permissions
            permissions = AuthService._get_user_permissions(db, user)
            
            # Create new access token
            token_data = {
                "user_id": user.id,
                "username": user.username,
                "hospital_id": user.hospital_id,
                "is_super_admin": user.is_super_admin,
                "permissions": permissions
            }
            
            access_token = AuthService.create_access_token(token_data)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,  # Keep the same refresh token
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_info={
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "hospital_id": user.hospital_id,
                    "is_super_admin": user.is_super_admin,
                    "permissions": permissions
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    @staticmethod
    def create_admin_user(db: Session, user_data: AdminUserCreate, created_by: AdminUser) -> AdminUser:
        """Create a new admin user"""
        # Check if username or email already exists
        existing_user = db.query(AdminUser).filter(
            (AdminUser.username == user_data.username) | 
            (AdminUser.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Hash password
        hashed_password = AuthService.hash_password(user_data.password)
        
        # Create user
        user = AdminUser(
            hospital_id=user_data.hospital_id,
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            is_super_admin=user_data.is_super_admin
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Assign roles
        if user_data.role_ids:
            for role_id in user_data.role_ids:
                user_role = UserRole(
                    admin_user_id=user.id,
                    role_id=role_id,
                    granted_by=created_by.id
                )
                db.add(user_role)
        
        db.commit()
        
        # Log the action
        AuthService._log_action(db, created_by, "admin_user.create", "admin_user", str(user.id), {
            "username": user.username,
            "email": user.email
        })
        
        return user
    
    @staticmethod
    def update_admin_user(db: Session, user_id: int, user_data: AdminUserUpdate, updated_by: AdminUser) -> AdminUser:
        """Update an admin user"""
        user = db.query(AdminUser).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.phone is not None:
            user.phone = user_data.phone
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        # Update password if provided
        if user_data.password:
            user.password_hash = AuthService.hash_password(user_data.password)
        
        db.commit()
        db.refresh(user)
        
        # Log the action
        AuthService._log_action(db, updated_by, "admin_user.update", "admin_user", str(user.id), {
            "updated_fields": list(user_data.dict(exclude_unset=True).keys())
        })
        
        return user
    
    @staticmethod
    def setup_2fa(db: Session, user: AdminUser) -> Dict[str, Any]:
        """Setup 2FA for a user"""
        if user.two_factor_enabled:
            raise HTTPException(status_code=400, detail="2FA is already enabled")
        
        # Generate secret
        secret = pyotp.random_base32()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Hospital LLM Admin"
        )
        
        return {
            "secret": secret,
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri,
            "qr_code_data": provisioning_uri
        }
    
    @staticmethod
    def enable_2fa(db: Session, user: AdminUser, secret: str, verification_code: str, backup_codes: List[str]) -> bool:
        """Enable 2FA for a user"""
        # Verify the code
        totp = pyotp.TOTP(secret)
        if not totp.verify(verification_code):
            raise HTTPException(status_code=400, detail="Invalid verification code")
        
        # Enable 2FA
        user.two_factor_enabled = True
        user.two_factor_secret = secret
        user.backup_codes = str(backup_codes)  # Store as JSON string
        
        db.commit()
        
        # Log the action
        AuthService._log_action(db, user, "2fa.enable", "admin_user", str(user.id), {})
        
        return True
    
    @staticmethod
    def disable_2fa(db: Session, user: AdminUser, verification_code: str) -> bool:
        """Disable 2FA for a user"""
        if not user.two_factor_enabled:
            raise HTTPException(status_code=400, detail="2FA is not enabled")
        
        # Verify the code
        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(verification_code):
            raise HTTPException(status_code=400, detail="Invalid verification code")
        
        # Disable 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.backup_codes = None
        
        db.commit()
        
        # Log the action
        AuthService._log_action(db, user, "2fa.disable", "admin_user", str(user.id), {})
        
        return True
    
    @staticmethod
    def _verify_2fa_code(user: AdminUser, code: str) -> bool:
        """Verify a 2FA code"""
        if not user.two_factor_enabled or not user.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(user.two_factor_secret)
        return totp.verify(code)
    
    @staticmethod
    def _get_user_permissions(db: Session, user: AdminUser) -> List[str]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Get roles for the user
        user_roles = db.query(UserRole).filter_by(admin_user_id=user.id).all()
        
        for user_role in user_roles:
            role = db.query(Role).filter_by(id=user_role.role_id).first()
            if role and role.permissions:
                import json
                try:
                    role_permissions = json.loads(role.permissions)
                    permissions.update(role_permissions)
                except json.JSONDecodeError:
                    continue
        
        return list(permissions)
    
    @staticmethod
    def _increment_login_attempts(db: Session, username: str) -> None:
        """Increment login attempts for security"""
        user = db.query(AdminUser).filter_by(username=username).first()
        if user:
            user.login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            db.commit()
    
    @staticmethod
    def _log_action(db: Session, user: AdminUser, action: str, resource_type: str, resource_id: str, details: Dict[str, Any]) -> None:
        """Log an admin action for audit trail"""
        import json
        
        # For super admins without a hospital_id, use a default system-wide scope (hospital_id=1)
        hospital_id = user.hospital_id if user.hospital_id is not None else 1
        
        audit_log = AuditLog(
            hospital_id=hospital_id,
            admin_user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details)
        )
        
        db.add(audit_log)
        db.commit()

# Dependency functions
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
) -> AdminUser:
    """Get the current authenticated user"""
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(AdminUser).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")
    # Validate hospital context unless superadmin
    token_hospital_id = payload.get("hospital_id")
    if not user.is_super_admin and token_hospital_id is not None and user.hospital_id != token_hospital_id:
        raise HTTPException(status_code=403, detail="User does not belong to this hospital context")
    return user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(
        current_user: AdminUser = Depends(get_current_user), 
        db: Session = Depends(get_db)
    ):
        permissions = AuthService._get_user_permissions(db, current_user)
        if permission not in permissions and not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
        return current_user
    return permission_checker