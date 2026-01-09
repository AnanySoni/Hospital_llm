from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator, model_validator
from typing import Optional
import os
import re
import json
import logging

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import secrets

from backend.core.database import get_db
from backend.core.models import (
    AdminUser,
    OnboardingSession,
    EmailVerification,
    Hospital,
    AuditLog,
    Role,
    UserRole,
)
from backend.services.auth_service import AuthService, get_current_user
from backend.services.email_service import EmailService
from backend.services.url_mapping_service import URLMappingService
from backend.services.onboarding_analytics_service import OnboardingAnalyticsService
from backend.utils.validation import (
    CompanyNameValidator, EmailValidator, SlugValidator, PasswordValidator
)
from backend.utils.rate_limiter import rate_limiter
from backend.middleware.csrf_middleware import CSRFMiddleware

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

# Company name validation pattern: Only letters, numbers, spaces, hyphens
COMPANY_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s-]+$')

# Reuse the same credentials.json as Google Calendar, but with different scopes/redirect
GOOGLE_CLIENT_SECRETS_FILE = "credentials.json"

# Scopes specifically for SIGN-IN (identity), not calendar
# Use full scope URLs to avoid scope expansion issues
GOOGLE_SIGNIN_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

# For now we only support local/dev callback; production URLs can be added later
# IMPORTANT: Redirect to FRONTEND so React can handle the callback UI.
# Google must be configured with this URI in the OAuth client.
GOOGLE_SIGNIN_REDIRECT_URI = "http://localhost:3000/onboarding/google/callback"


def _create_google_signin_flow(state: Optional[str] = None) -> Flow:
    """
    Create Google OAuth flow for SIGN-IN during onboarding.
    Uses the same credentials.json file as calendar, but different scopes and redirect URI.
    """
    if not os.path.exists(GOOGLE_CLIENT_SECRETS_FILE):
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth credentials file not found. Please create '{GOOGLE_CLIENT_SECRETS_FILE}' with your Google OAuth credentials.",
        )

    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=GOOGLE_SIGNIN_SCOPES,
        redirect_uri=GOOGLE_SIGNIN_REDIRECT_URI,
    )

    # Optional state for CSRF protection / tracking (we'll wire proper storage later)
    if state:
        flow.state = state

    return flow


@router.get("/google/login")
async def google_login():
    """
    Flow A (part 1): Start Google OAuth sign-up.

    Frontend should redirect the browser to this endpoint.
    This endpoint redirects the user to Google's consent screen.
    """
    try:
        flow = _create_google_signin_flow()
        authorization_url, _state = flow.authorization_url(
            access_type="online",
            include_granted_scopes="true",
            prompt="select_account",
        )
        return RedirectResponse(url=authorization_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting Google sign-in: {str(e)}")


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Flow A (part 2): Google redirects back here after sign-in.

    For step 1.2.1 we:
    - Exchange the code for tokens
    - Call Google userinfo API
    - Return normalized user_info and an action hint to the frontend
    - We DO NOT create AdminUser / Hospital yet (that's 1.2.2+)
    """
    # Rate limiting: 10 attempts per IP per hour
    ip_address = request.client.host if request.client else "unknown"
    allowed, remaining = rate_limiter.check_rate_limit(
        db=db,
        identifier=ip_address,
        endpoint='/onboarding/google/callback',
        max_requests=10,
        window_seconds=3600
    )
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many OAuth callback attempts. Please try again in an hour."
            },
            headers={"Retry-After": "3600", "X-RateLimit-Remaining": "0"}
        )
    # #region agent log
    import json
    try:
        with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"A","location":"onboarding_routes.py:89","message":"Google callback received","data":{"has_error":bool(request.query_params.get("error")),"has_code":bool(request.query_params.get("code")),"redirect_uri":GOOGLE_SIGNIN_REDIRECT_URI},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
    except: pass
    # #endregion
    
    error = request.query_params.get("error")
    if error:
        # #region agent log
        try:
            with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"A","location":"onboarding_routes.py:100","message":"Google returned error in callback","data":{"error":error},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
        except: pass
        # #endregion
        return JSONResponse(
            status_code=400,
            content={"error": "google_oauth_error", "message": error},
        )

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    # #region agent log
    import time
    request_start_time = time.time()
    code_hash = hash(code) if code else None  # Use hash to track same code without logging full value
    try:
        with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"B","location":"onboarding_routes.py:127","message":"Extracted code and state","data":{"code_length":len(code) if code else 0,"code_hash":code_hash,"has_state":bool(state),"state_value":state,"redirect_uri_configured":GOOGLE_SIGNIN_REDIRECT_URI,"request_timestamp":request_start_time},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
    except: pass
    # #endregion
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # #region agent log
    # Log code info for duplicate detection (we'll analyze logs to see if same code appears twice)
    try:
        with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"A","location":"onboarding_routes.py:139","message":"Code received for exchange","data":{"code_hash":code_hash,"code_length":len(code) if code else 0,"request_timestamp":request_start_time},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
    except: pass
    # #endregion

    try:
        # #region agent log
        time_before_flow_creation = time.time()
        try:
            with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"C","location":"onboarding_routes.py:148","message":"Creating flow for token exchange","data":{"redirect_uri":GOOGLE_SIGNIN_REDIRECT_URI,"scopes":GOOGLE_SIGNIN_SCOPES,"state_param":state,"time_since_request_start":time_before_flow_creation - request_start_time},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
        except: pass
        # #endregion
        
        # Create flow with the same redirect_uri and scopes used in authorization request
        flow = _create_google_signin_flow(state=state)
        
        # #region agent log
        time_before_token_exchange = time.time()
        try:
            with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"C","location":"onboarding_routes.py:155","message":"Attempting token exchange","data":{"code_hash":code_hash,"code_length":len(code) if code else 0,"flow_redirect_uri":flow.redirect_uri,"flow_state":getattr(flow, 'state', None),"time_since_request_start":time_before_token_exchange - request_start_time,"time_since_flow_creation":time_before_token_exchange - time_before_flow_creation},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
        except: pass
        # #endregion
        
        # Exchange authorization code for tokens
        # Note: This will fail with invalid_grant if:
        # 1. Code was already used (page refresh)
        # 2. Code expired (usually 10 minutes)
        # 3. Redirect URI doesn't match Google Cloud Console config
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # #region agent log
        time_after_token_exchange = time.time()
        try:
            with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"C","location":"onboarding_routes.py:170","message":"Token exchange successful","data":{"has_token":bool(credentials.token),"has_refresh_token":bool(credentials.refresh_token),"total_time_ms":(time_after_token_exchange - request_start_time) * 1000,"token_exchange_duration_ms":(time_after_token_exchange - time_before_token_exchange) * 1000},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
        except: pass
        # #endregion

        # Fetch basic profile info
        oauth2_service = build("oauth2", "v2", credentials=credentials)
        user_info = oauth2_service.userinfo().get().execute()

        normalized = {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
            "picture": user_info.get("picture"),
            "google_id": user_info.get("id"),
            "verified_email": user_info.get("verified_email", False),
        }

        return JSONResponse(
            status_code=200,
            content={
                "message": "Google sign-in successful",
                "user_info": normalized,
                "action": "collect_company_name",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        # #region agent log
        time_at_error = time.time()
        try:
            error_str = str(e)
            error_type = type(e).__name__
            with open('/Users/ananysoni/Downloads/Hospital_llm-main/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"oauth-debug","hypothesisId":"D","location":"onboarding_routes.py:196","message":"Token exchange failed","data":{"error_type":error_type,"error_message":error_str,"redirect_uri_used":GOOGLE_SIGNIN_REDIRECT_URI,"is_invalid_grant":"invalid_grant" in error_str.lower(),"code_hash":code_hash,"total_time_ms":(time_at_error - request_start_time) * 1000,"has_state":bool(state),"state_value":state},"timestamp":int(datetime.utcnow().timestamp()*1000)})+'\n')
        except: pass
        # #endregion
        
        # Provide more helpful error message for invalid_grant
        error_str = str(e)
        if "invalid_grant" in error_str.lower():
            logger.error(f"Google OAuth invalid_grant error. Redirect URI: {GOOGLE_SIGNIN_REDIRECT_URI}")
            raise HTTPException(
                status_code=400,
                detail=(
                    "Google sign-in failed: The authorization code is invalid or has expired. "
                    "This usually happens if:\n"
                    "1. The redirect URI in Google Cloud Console doesn't match: " + GOOGLE_SIGNIN_REDIRECT_URI + "\n"
                    "2. The authorization code was already used (page was refreshed)\n"
                    "3. The authorization code expired (try signing in again)\n\n"
                    "Please try signing in with Google again."
                )
            )
        raise HTTPException(status_code=500, detail=f"Error processing Google sign-in: {str(e)}")


class OnboardingRegisterRequest(BaseModel):
    """
    Shared body for Flow A (Google) + Flow B (Email) registration.
    Password is now required for both signup methods.
    """

    email: EmailStr
    company_name: str = Field(min_length=2, max_length=100)
    signup_method: str  # "google" or "email"
    password: str  # Required for both signup methods
    google_id: Optional[str] = None  # required when signup_method == "google"
    
    @validator('company_name')
    def validate_company_name(cls, v):
        """Validate company name format and content"""
        if not v or not v.strip():
            raise ValueError('Company name is required')
        
        v = v.strip()
        
        # Check for special characters
        if not COMPANY_NAME_PATTERN.match(v):
            raise ValueError(
                'Company name can only contain letters, numbers, spaces, and hyphens. '
                'Special characters are not allowed.'
            )
        
        # Check minimum length after trimming
        if len(v) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        
        return v
    
    @model_validator(mode='before')
    @classmethod
    def validate_signup_fields(cls, values):
        """Validate password and google_id based on signup method"""
        if isinstance(values, dict):
            password = values.get('password')
            signup_method = values.get('signup_method')
            google_id = values.get('google_id')
            
            # Password is required for all signup methods
            if not password or not password.strip():
                raise ValueError('Password is required for all signup methods')
            
            # Validate password length (minimum 8 characters)
            if len(password.strip()) < 8:
                raise ValueError('Password must be at least 8 characters long')
            
            # google_id is required for Google signup
            if signup_method == 'google' and not google_id:
                raise ValueError('google_id is required for Google signup')
        
        return values
    
class HospitalInfoRequest(BaseModel):
    """Request body for creating hospital during onboarding."""

    hospital_name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=3, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    phone: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=255)



@router.get("/csrf-token")
async def get_csrf_token(request: Request):
    """
    Generate CSRF token for the current session.
    Frontend should call this before making state-changing requests.
    """
    # Generate session ID if not exists
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = secrets.token_urlsafe(32)
    
    token = CSRFMiddleware.generate_token(session_id)
    
    response = JSONResponse({"token": token, "session_id": session_id})
    response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="lax")
    return response


@router.post("/register")
async def onboarding_register(
    request_body: OnboardingRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Flow B: Email sign-up entrypoint (and final step for Google sign-up).

    1.2.2 behavior:
    - Validate input
    - Check for existing user
    - Create AdminUser with appropriate flags
    - Create OnboardingSession
    - For email sign-up: create EmailVerification token (email sending will be wired later)
    """
    # Get IP address and user agent for logging
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get('user-agent', 'unknown')
    
    # Track registration start
    try:
        OnboardingAnalyticsService.track_event(
            db=db,
            event_type='registration_start',
            signup_method=request_body.signup_method,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.warning(f"Failed to track registration start: {str(e)}")
    
    # Rate limiting: 5 attempts per IP per hour
    allowed, remaining = rate_limiter.check_rate_limit(
        db=db,
        identifier=ip_address,
        endpoint='/onboarding/register',
        max_requests=5,
        window_seconds=3600
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please try again in an hour.",
            headers={"Retry-After": "3600", "X-RateLimit-Remaining": "0"}
        )
    
    if request_body.signup_method not in ("google", "email"):
        raise HTTPException(status_code=400, detail="Invalid signup_method")

    # Basic sanity rules (password validation is now handled by Pydantic model)
    if request_body.signup_method == "google" and not request_body.google_id:
        raise HTTPException(status_code=400, detail="google_id is required for Google signup")

    email = request_body.email.lower().strip()
    company_name = request_body.company_name.strip()
    
    # Enhanced validation using validators
    # Company name validation
    is_valid, error_msg = CompanyNameValidator.validate(company_name)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Email validation
    is_valid, error_msg = EmailValidator.validate(email, check_deliverability=False)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Password validation with strength
    is_valid, error_msg, strength_info = PasswordValidator.validate(request_body.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Check if email already exists
    existing_user = db.query(AdminUser).filter(AdminUser.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    # Check if google_user_id already exists (for Google signup)
    if request_body.signup_method == "google" and request_body.google_id:
        existing_google_user = db.query(AdminUser).filter(
            AdminUser.google_user_id == request_body.google_id
        ).first()
        if existing_google_user:
            raise HTTPException(
                status_code=400,
                detail="This Google account is already registered. Please log in instead."
            )

    # Check if company name already exists (case-insensitive)
    existing_company = db.query(AdminUser).filter(
        func.lower(AdminUser.company_name) == company_name.lower()
    ).first()
    if existing_company:
        raise HTTPException(
            status_code=400,
            detail="This company name is already registered. Please use a different name."
        )

    # Derive a simple username from email
    base_username = email.split("@")[0]
    username = base_username
    suffix = 1
    while db.query(AdminUser).filter(AdminUser.username == username).first():
        username = f"{base_username}{suffix}"
        suffix += 1

    # Default names can be refined later in the onboarding UI
    first_name = ""
    last_name = ""

    # Prepare password hash (password is now required for both signup methods)
    password_hash = AuthService.hash_password(request_body.password)
    
    if request_body.signup_method == "email":
        email_verified = False
        is_active = False
        auth_provider = "email"
        google_user_id = None
    else:
        # Google sign-up: email is already verified by Google
        email_verified = True
        is_active = True
        auth_provider = "google"
        google_user_id = request_body.google_id

    # Create AdminUser
    admin_user = AdminUser(
        hospital_id=None,  # Hospital will be created later in onboarding
        username=username,
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        phone=None,
        email_verified=email_verified,
        email_verified_at=datetime.utcnow() if email_verified else None,
        auth_provider=auth_provider,
        google_user_id=google_user_id,
        company_name=company_name,
        onboarding_session_id=None,
        last_onboarding_step=1,
        is_active=is_active,
        is_super_admin=False,
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # Ensure the admin user has the default hospital_admin role (if it exists)
    try:
        hospital_admin_role = db.query(Role).filter(Role.name == "hospital_admin").first()
        if hospital_admin_role:
            existing_user_role = (
                db.query(UserRole)
                .filter(
                    UserRole.admin_user_id == admin_user.id,
                    UserRole.role_id == hospital_admin_role.id,
                )
                .first()
            )
            if not existing_user_role:
                user_role = UserRole(
                    admin_user_id=admin_user.id,
                    role_id=hospital_admin_role.id,
                    granted_by=admin_user.id,
                )
                db.add(user_role)
                db.commit()
    except Exception as e:
        logger.warning(f"Failed to assign hospital_admin role during onboarding: {str(e)}")

    # Create onboarding session
    onboarding_session = OnboardingSession(
        admin_user_id=admin_user.id,
        hospital_id=None,
        current_step=1,
        completed_steps='[]',
        partial_data='{}',
        status='in_progress',
    )
    db.add(onboarding_session)
    db.commit()
    db.refresh(onboarding_session)

    # Link session back to user
    admin_user.onboarding_session_id = onboarding_session.id
    db.commit()
    
    # Track registration complete and step start
    try:
        OnboardingAnalyticsService.track_event(
            db=db,
            event_type='registration_complete',
            onboarding_session_id=onboarding_session.id,
            admin_user_id=admin_user.id,
            step_number=1,
            signup_method=request_body.signup_method,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Track step start for next step
        next_step = 2 if request_body.signup_method == 'email' else 3
        OnboardingAnalyticsService.track_step_start(
            db=db,
            onboarding_session_id=onboarding_session.id,
            step_number=next_step,
        )
    except Exception as e:
        logger.warning(f"Failed to track registration analytics: {str(e)}")
    
    # Log registration attempt for audit trail
    try:
        audit_log = AuditLog(
            hospital_id=1,  # System-wide for onboarding
            admin_user_id=admin_user.id,
            action='onboarding.register',
            resource_type='admin_user',
            resource_id=str(admin_user.id),
            details=json.dumps({
                'signup_method': request_body.signup_method,
                'email': email,
                'company_name': company_name,
                'password_strength': strength_info.get('level') if strength_info else 'unknown'
            }),
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to log registration audit: {str(e)}")

    response_payload = {
        "user_id": admin_user.id,
        "onboarding_session_id": onboarding_session.id,
        "signup_method": request_body.signup_method,
        "email": admin_user.email,
        "company_name": admin_user.company_name,
    }

    # For email sign-up, create verification token record
    if request_body.signup_method == "email":
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        verification = EmailVerification(
            admin_user_id=admin_user.id,
            email=admin_user.email,
            token=token,
            verification_type="email_verification",
            expires_at=expires_at,
        )
        db.add(verification)
        db.commit()

        # Send verification email
        try:
            email_sent = EmailService.send_verification_email(admin_user, token)
            if email_sent:
                logger.info(f"Verification email sent successfully to {admin_user.email}")
                # Track email verification sent
                try:
                    OnboardingAnalyticsService.track_event(
                        db=db,
                        event_type='email_verification_sent',
                        onboarding_session_id=onboarding_session.id,
                        admin_user_id=admin_user.id,
                        step_number=2,
                    )
                except Exception as e:
                    logger.warning(f"Failed to track email verification sent: {str(e)}")
            else:
                logger.warning(f"Failed to send verification email to {admin_user.email}, but token was created")
        except Exception as e:
            # Log error but don't fail registration - token is still created
            logger.error(f"Error sending verification email to {admin_user.email}: {str(e)}")

        response_payload.update(
            {
                "requires_email_verification": True,
            }
        )
    else:
        # Google sign-up: already verified email, can proceed to hospital info
        # Issue JWT tokens so the user is effectively logged in immediately
        permissions = AuthService._get_user_permissions(db, admin_user)
        token_data = {
            "user_id": admin_user.id,
            "username": admin_user.username,
            "hospital_id": admin_user.hospital_id,
            "is_super_admin": admin_user.is_super_admin,
            "permissions": permissions,
        }
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)

        response_payload.update(
            {
                "requires_email_verification": False,
                "email_verified": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 60 * 30,  # seconds
            }
        )

    return response_payload


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Verify email address using token from verification email.
    
    Validates token, marks email as verified, activates account, and updates onboarding session.
    Redirects to frontend verification page with status.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    if not token or len(token) < 10:
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{frontend_url}/onboarding/verify-email?token={token}&status=invalid&error=Invalid token format"
        )
    
    try:
        # Find verification record (check for unused tokens only)
        verification = db.query(EmailVerification).filter(
            EmailVerification.token == token,
            EmailVerification.verification_type == "email_verification",
            EmailVerification.used == False  # One-time use check
        ).first()
        
        if not verification:
            # Check if token was already used
            used_verification = db.query(EmailVerification).filter(
                EmailVerification.token == token,
                EmailVerification.verification_type == "email_verification",
                EmailVerification.used == True
            ).first()
            
            if used_verification:
                logger.warning(f"Verification attempt with already-used token: {token[:8]}...")
                return RedirectResponse(
                    url=f"{frontend_url}/onboarding/verify-email?token={token}&status=already_used&error=This verification link has already been used"
                )
            
            logger.warning(f"Verification attempt with invalid token: {token[:8]}...")
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/verify-email?token={token}&status=invalid&error=Token not found"
            )
        
        # Check if already verified (double-check)
        if verification.verified_at is not None:
            logger.info(f"Verification attempt with already-used token for user {verification.admin_user_id}")
            # Mark as used if not already
            if not verification.used:
                verification.used = True
                verification.used_at = datetime.utcnow()
                db.commit()
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/verify-email?token={token}&status=already_verified"
            )
        
        # Check if expired
        if verification.expires_at < datetime.utcnow():
            logger.warning(f"Verification attempt with expired token for user {verification.admin_user_id}")
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/verify-email?token={token}&status=expired&error=Token expired"
            )
        
        # Get user
        admin_user = db.query(AdminUser).filter(AdminUser.id == verification.admin_user_id).first()
        if not admin_user:
            logger.error(f"User not found for verification token: {verification.admin_user_id}")
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/verify-email?token={token}&status=invalid&error=User not found"
            )
        
        # Check if email matches (security: prevent email change attacks)
        if admin_user.email.lower() != verification.email.lower():
            logger.warning(
                f"Email mismatch for verification: token email={verification.email}, "
                f"user email={admin_user.email}, user_id={admin_user.id}"
            )
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/verify-email?token={token}&status=invalid&error=Email mismatch"
            )
        
        # Check if already verified (double-check)
        if admin_user.email_verified:
            logger.info(f"Email already verified for user {admin_user.id}, marking token as used")
            verification.verified_at = datetime.utcnow()
            db.commit()
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/verify-email?token={token}&status=already_verified"
            )
        
        # Mark email as verified
        admin_user.email_verified = True
        admin_user.email_verified_at = datetime.utcnow()
        admin_user.is_active = True  # Activate account
        
        # Mark token as used (one-time use)
        verification.verified_at = datetime.utcnow()
        verification.used = True
        verification.used_at = datetime.utcnow()
        
        # Track email verification completion
        try:
            OnboardingAnalyticsService.track_event(
                db=db,
                event_type='email_verification_completed',
                onboarding_session_id=admin_user.onboarding_session_id,
                admin_user_id=admin_user.id,
                step_number=2,
            )
            # Track step start for next step (hospital info)
            if admin_user.onboarding_session_id:
                OnboardingAnalyticsService.track_step_start(
                    db=db,
                    onboarding_session_id=admin_user.onboarding_session_id,
                    step_number=3,
                )
        except Exception as e:
            logger.warning(f"Failed to track email verification analytics: {str(e)}")
        
        # Update onboarding session if exists
        if admin_user.onboarding_session_id:
            onboarding_session = db.query(OnboardingSession).filter(
                OnboardingSession.id == admin_user.onboarding_session_id
            ).first()
            if onboarding_session:
                # Mark step 1 (email verification) as complete
                completed_steps = []
                try:
                    if onboarding_session.completed_steps:
                        completed_steps = json.loads(onboarding_session.completed_steps)
                    if not isinstance(completed_steps, list):
                        completed_steps = []
                except (json.JSONDecodeError, TypeError):
                    completed_steps = []
                
                if 1 not in completed_steps:
                    completed_steps.append(1)
                
                onboarding_session.completed_steps = json.dumps(completed_steps)
                # Update current step to 2 (hospital info) if still on step 1
                if onboarding_session.current_step == 1:
                    onboarding_session.current_step = 2
                onboarding_session.last_updated_at = datetime.utcnow()
        
        db.commit()
        
        # Send welcome email after successful verification (non-blocking)
        try:
            welcome_sent = EmailService.send_admin_welcome_email(
                admin_user=admin_user,
                onboarding_session_id=admin_user.onboarding_session_id
            )
            if welcome_sent:
                logger.info(f"Welcome email sent successfully to {admin_user.email}")
                # Track welcome email sent
                try:
                    OnboardingAnalyticsService.track_event(
                        db=db,
                        event_type='welcome_email_sent',
                        onboarding_session_id=admin_user.onboarding_session_id,
                        admin_user_id=admin_user.id,
                    )
                except Exception as e:
                    logger.warning(f"Failed to track welcome email analytics: {str(e)}")
            else:
                logger.warning(f"Failed to send welcome email to {admin_user.email}, but verification succeeded")
        except Exception as e:
            # Don't fail verification if welcome email fails
            logger.error(f"Error sending welcome email to {admin_user.email}: {str(e)}")
        
        logger.info(f"Email verified successfully for user {admin_user.id} ({admin_user.email})")

        # Auto-login: issue JWT tokens so onboarding can proceed without extra login step
        permissions = AuthService._get_user_permissions(db, admin_user)
        token_data = {
            "user_id": admin_user.id,
            "username": admin_user.username,
            "hospital_id": admin_user.hospital_id,
            "is_super_admin": admin_user.is_super_admin,
            "permissions": permissions,
        }
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)

        # NOTE: For simplicity in dev, we pass tokens via query params.
        # Frontend can capture and store them for authenticated onboarding steps.
        return RedirectResponse(
            url=(
                f"{frontend_url}/onboarding/verify-email"
                f"?token={token}"
                f"&status=success"
                f"&access_token={access_token}"
                f"&refresh_token={refresh_token}"
                f"&expires_in={60 * 30}"
            )
        )
        
    except Exception as e:
        logger.error(f"Error verifying email token: {str(e)}")
        db.rollback()
        return RedirectResponse(
            url=f"{frontend_url}/onboarding/verify-email?token={token}&status=error&error=Verification failed"
        )


class ResendVerificationRequest(BaseModel):
    """Request model for resending verification email"""
    email: EmailStr


@router.post("/resend-verification")
async def resend_verification(
    request_body: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Resend verification email to user.
    
    Includes rate limiting (max 3 per hour per user) and invalidates old tokens.
    """
    # Get IP address and user agent for logging
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get('user-agent', 'unknown')
    
    email = request_body.email.lower().strip()
    
    try:
        # Find user by email
        admin_user = db.query(AdminUser).filter(AdminUser.email == email).first()
        
        # Security: Don't reveal if email exists (prevent email enumeration)
        # Return same message whether user exists or not
        if not admin_user:
            # Log but don't reveal
            logger.warning(f"Resend verification attempt for non-existent email: {email}")
            # Return success message to prevent email enumeration
            return {
                "message": "If an account exists with this email, a verification email has been sent.",
                "success": True
            }
        
        # Check if email already verified
        if admin_user.email_verified:
            logger.info(f"Resend verification attempt for already-verified email: {email}")
            return {
                "message": "This email address has already been verified.",
                "success": True,
                "already_verified": True
            }
        
        # Rate limiting: Check recent verification attempts (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_attempts = db.query(EmailVerification).filter(
            EmailVerification.admin_user_id == admin_user.id,
            EmailVerification.verification_type == "email_verification",
            EmailVerification.created_at > one_hour_ago
        ).count()
        
        if recent_attempts >= 3:
            logger.warning(
                f"Rate limit exceeded for resend verification: user_id={admin_user.id}, "
                f"attempts={recent_attempts}"
            )
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait before requesting another verification email. "
                       "You can request up to 3 verification emails per hour."
            )
        
        # Invalidate old pending tokens (set expires_at to past)
        old_tokens = db.query(EmailVerification).filter(
            EmailVerification.admin_user_id == admin_user.id,
            EmailVerification.verification_type == "email_verification",
            EmailVerification.verified_at.is_(None),  # Not yet verified
            EmailVerification.expires_at > datetime.utcnow()  # Not expired yet
        ).all()
        
        for old_token in old_tokens:
            old_token.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        # Generate new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Create new verification record
        verification = EmailVerification(
            admin_user_id=admin_user.id,
            email=admin_user.email,
            token=token,
            verification_type="email_verification",
            expires_at=expires_at,
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Send verification email
        try:
            email_sent = EmailService.send_verification_email(admin_user, token)
            if email_sent:
                logger.info(f"Verification email resent successfully to {admin_user.email}")
            else:
                logger.warning(f"Failed to send verification email to {admin_user.email}, but token was created")
        except Exception as e:
            # Log error but don't fail - token is still created
            logger.error(f"Error sending verification email to {admin_user.email}: {str(e)}")
        
        # Return success (don't reveal if email exists)
        return {
            "message": "If an account exists with this email, a verification email has been sent.",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to resend verification email. Please try again later."
        )


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for resetting password"""
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8)


@router.post("/forgot-password")
async def forgot_password(
    request_body: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Request password reset. Sends password reset email.
    
    Security: Returns same response whether email exists or not (prevent email enumeration).
    Rate limited: max 3 requests per email per hour.
    """
    # Get IP address for logging
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get('user-agent', 'unknown')
    
    email = request_body.email.lower().strip()
    
    # Rate limiting: 3 requests per email per hour
    allowed, remaining = rate_limiter.check_rate_limit(
        db=db,
        identifier=email,  # Rate limit by email address
        endpoint='/onboarding/forgot-password',
        max_requests=3,
        window_seconds=3600
    )
    
    if not allowed:
        # Still return generic success to prevent email enumeration
        logger.warning(f"Rate limit exceeded for forgot password: {email}")
        return {
            "message": "If an account exists with this email, a password reset email has been sent.",
            "success": True
        }
    
    try:
        # Find user by email
        admin_user = db.query(AdminUser).filter(AdminUser.email == email).first()
        
        # Security: Don't reveal if email exists (prevent email enumeration)
        # Return same message whether user exists or not
        if not admin_user:
            logger.warning(f"Forgot password attempt for non-existent email: {email}")
            # Return success message to prevent email enumeration
            return {
                "message": "If an account exists with this email, a password reset email has been sent.",
                "success": True
            }
        
        # Check if user is active
        if not admin_user.is_active:
            logger.warning(f"Password reset attempt for inactive account: {email}")
            return {
                "message": "If an account exists with this email, a password reset email has been sent.",
                "success": True
            }
        
        # Invalidate old pending password reset tokens
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        old_tokens = db.query(EmailVerification).filter(
            EmailVerification.admin_user_id == admin_user.id,
            EmailVerification.verification_type == "password_reset",
            EmailVerification.used == False,
            EmailVerification.expires_at > datetime.utcnow()
        ).all()
        
        for old_token in old_tokens:
            old_token.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        # Generate new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
        
        # Create new verification record
        verification = EmailVerification(
            admin_user_id=admin_user.id,
            email=admin_user.email,
            token=token,
            verification_type="password_reset",
            expires_at=expires_at,
        )
        
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Send password reset email
        try:
            email_sent = EmailService.send_password_reset_email(admin_user, token)
            if email_sent:
                logger.info(f"Password reset email sent successfully to {admin_user.email}")
            else:
                logger.warning(f"Failed to send password reset email to {admin_user.email}, but token was created")
        except Exception as e:
            # Log error but don't fail - token is still created
            logger.error(f"Error sending password reset email to {admin_user.email}: {str(e)}")
        
        # Log for audit trail
        try:
            audit_log = AuditLog(
                hospital_id=admin_user.hospital_id or 1,  # System-wide if no hospital
                admin_user_id=admin_user.id,
                action='onboarding.forgot_password',
                resource_type='admin_user',
                resource_id=str(admin_user.id),
                details=json.dumps({
                    'email': email,
                }),
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to log forgot password audit: {str(e)}")
        
        # Return success (don't reveal if email exists)
        return {
            "message": "If an account exists with this email, a password reset email has been sent.",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing forgot password request: {str(e)}")
        db.rollback()
        # Still return generic success
        return {
            "message": "If an account exists with this email, a password reset email has been sent.",
            "success": True
        }


@router.get("/reset-password")
async def verify_reset_token(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
):
    """
    Verify password reset token and redirect to frontend reset page.
    
    Validates token and redirects with status.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    if not token or len(token) < 10:
        return RedirectResponse(
            url=f"{frontend_url}/onboarding/reset-password?token={token}&status=invalid&error=Invalid token format"
        )
    
    try:
        # Find verification record (check for unused tokens only)
        verification = db.query(EmailVerification).filter(
            EmailVerification.token == token,
            EmailVerification.verification_type == "password_reset",
            EmailVerification.used == False
        ).first()
        
        if not verification:
            # Check if token was already used
            used_verification = db.query(EmailVerification).filter(
                EmailVerification.token == token,
                EmailVerification.verification_type == "password_reset",
                EmailVerification.used == True
            ).first()
            
            if used_verification:
                logger.warning(f"Password reset attempt with already-used token: {token[:8]}...")
                return RedirectResponse(
                    url=f"{frontend_url}/onboarding/reset-password?token={token}&status=already_used&error=This password reset link has already been used"
                )
            
            logger.warning(f"Password reset attempt with invalid token: {token[:8]}...")
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/reset-password?token={token}&status=invalid&error=Token not found"
            )
        
        # Check if expired
        if verification.expires_at < datetime.utcnow():
            logger.warning(f"Password reset attempt with expired token for user {verification.admin_user_id}")
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/reset-password?token={token}&status=expired&error=Token expired"
            )
        
        # Get user
        admin_user = db.query(AdminUser).filter(AdminUser.id == verification.admin_user_id).first()
        if not admin_user:
            logger.error(f"User not found for password reset token: {verification.admin_user_id}")
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/reset-password?token={token}&status=invalid&error=User not found"
            )
        
        # Check if email matches (security: prevent email change attacks)
        if admin_user.email.lower() != verification.email.lower():
            logger.warning(
                f"Email mismatch for password reset: token email={verification.email}, "
                f"user email={admin_user.email}, user_id={admin_user.id}"
            )
            return RedirectResponse(
                url=f"{frontend_url}/onboarding/reset-password?token={token}&status=invalid&error=Email mismatch"
            )
        
        # Token is valid, redirect to frontend reset page
        return RedirectResponse(
            url=f"{frontend_url}/onboarding/reset-password?token={token}&status=valid"
        )
        
    except Exception as e:
        logger.error(f"Error verifying password reset token: {str(e)}")
        return RedirectResponse(
            url=f"{frontend_url}/onboarding/reset-password?token={token}&status=invalid&error=Error verifying token"
        )


@router.post("/reset-password")
async def reset_password(
    request_body: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Reset password using token.
    
    Validates token, checks password strength, and updates password.
    """
    # Get IP address for logging
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get('user-agent', 'unknown')
    
    token = request_body.token
    new_password = request_body.new_password
    
    try:
        # Find verification record
        verification = db.query(EmailVerification).filter(
            EmailVerification.token == token,
            EmailVerification.verification_type == "password_reset",
            EmailVerification.used == False
        ).first()
        
        if not verification:
            # Check if already used
            used_verification = db.query(EmailVerification).filter(
                EmailVerification.token == token,
                EmailVerification.verification_type == "password_reset",
                EmailVerification.used == True
            ).first()
            
            if used_verification:
                raise HTTPException(
                    status_code=400,
                    detail="This password reset link has already been used. Please request a new one."
                )
            
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired password reset token. Please request a new one."
            )
        
        # Check if expired
        if verification.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail="Password reset token has expired. Please request a new one."
            )
        
        # Get user
        admin_user = db.query(AdminUser).filter(AdminUser.id == verification.admin_user_id).first()
        if not admin_user:
            raise HTTPException(
                status_code=400,
                detail="User not found for this password reset token."
            )
        
        # Check if email matches
        if admin_user.email.lower() != verification.email.lower():
            raise HTTPException(
                status_code=400,
                detail="Email mismatch for password reset token."
            )
        
        # Validate new password
        is_valid, error_msg, strength_info = PasswordValidator.validate(new_password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Hash new password
        password_hash = AuthService.hash_password(new_password)
        
        # Update password
        admin_user.password_hash = password_hash
        
        # Mark token as used
        verification.used = True
        verification.used_at = datetime.utcnow()
        
        db.commit()
        
        # Log for audit trail
        try:
            audit_log = AuditLog(
                hospital_id=admin_user.hospital_id or 1,
                admin_user_id=admin_user.id,
                action='onboarding.password_reset',
                resource_type='admin_user',
                resource_id=str(admin_user.id),
                details=json.dumps({
                    'password_strength': strength_info.get('level') if strength_info else 'unknown'
                }),
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to log password reset audit: {str(e)}")
        
        logger.info(f"Password reset successfully for user {admin_user.id} ({admin_user.email})")
        
        return {
            "message": "Password has been reset successfully. You can now log in with your new password.",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to reset password. Please try again later."
        )


class SlugCheckResponse(BaseModel):
    slug: str
    valid: bool
    available: bool
    reason: Optional[str] = None
    suggestions: Optional[list[str]] = None


class OnboardingSessionResponse(BaseModel):
    id: int
    current_step: int
    completed_steps: list[int]
    partial_data: dict
    status: str

    class Config:
        orm_mode = True


class OnboardingSessionUpdateRequest(BaseModel):
    current_step: int
    completed_steps: Optional[list[int]] = None
    partial_data: Optional[dict] = None
    status: Optional[str] = None  # in_progress, completed, abandoned


@router.get("/slug/check", response_model=SlugCheckResponse)
async def check_slug(
    request: Request,
    slug: str = Query(..., min_length=1, max_length=50),
    db: Session = Depends(get_db),
):
    """
    Lightweight endpoint to validate a proposed hospital slug.

    - Checks format (lowercase, a-z0-9-, length)
    - Checks against reserved_slugs
    - Checks uniqueness in hospitals table
    - Returns a few alternative suggestions when not available
    """
    # Rate limiting: 100 requests per IP per minute
    ip_address = request.client.host if request.client else "unknown"
    allowed, remaining = rate_limiter.check_rate_limit(
        db=db,
        identifier=ip_address,
        endpoint='/onboarding/slug/check',
        max_requests=100,
        window_seconds=60
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many slug check requests. Please try again in a minute.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"}
        )
    
    # Enhanced slug validation
    is_valid, error_msg = SlugValidator.validate(slug)
    if not is_valid:
        return SlugCheckResponse(
            slug=slug,
            valid=False,
            available=False,
            reason=error_msg,
            suggestions=URLMappingService.suggest_alternatives(slug, max_suggestions=3) if slug else None,
        )
    
    slug = slug.strip().lower()
    result = URLMappingService.validate_slug(slug)

    suggestions = None
    if not (result.get("valid") and result.get("available")):
        suggestions = URLMappingService.suggest_alternatives(slug, max_suggestions=3)

    return SlugCheckResponse(
        slug=slug,
        valid=bool(result.get("valid")),
        available=bool(result.get("available")),
        reason=result.get("reason"),
        suggestions=suggestions,
    )


@router.get("/check-email")
async def check_email(
    email: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Check if email already exists (for real-time validation).
    Returns whether email exists without revealing if account is active.
    """
    email = email.lower().strip()
    
    # Validate email format first
    is_valid, error_msg = EmailValidator.validate(email, check_deliverability=False)
    if not is_valid:
        return {"exists": False, "valid": False, "error": error_msg}
    
    # Check if email exists
    existing_user = db.query(AdminUser).filter(AdminUser.email == email).first()
    
    return {
        "exists": existing_user is not None,
        "valid": True,
        "error": None
    }


@router.post("/password/strength")
async def check_password_strength(
    request_body: dict,
    db: Session = Depends(get_db),
):
    """Check password strength without creating account."""
    password = request_body.get('password', '')
    is_valid, error_msg, strength_info = PasswordValidator.validate(password)
    
    return {
        "valid": is_valid,
        "error": error_msg,
        "strength": strength_info
    }


@router.get("/analytics")
async def get_onboarding_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get onboarding analytics summary.
    Requires super admin access.
    """
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    summary = OnboardingAnalyticsService.get_analytics_summary(db, days=days)
    return summary


@router.get("/analytics/detailed")
async def get_detailed_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed per-step analytics.
    Requires super admin access.
    """
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    detailed = OnboardingAnalyticsService.get_detailed_analytics(db, days=days)
    return detailed


@router.get("/slug/suggest")
async def suggest_slug(
    name: str = Query(..., min_length=1, max_length=200),
):
    """
    Suggest a base slug and a few alternatives from a hospital/company name.
    """
    base_slug = URLMappingService.generate_slug(name)
    suggestions = URLMappingService.suggest_alternatives(base_slug, max_suggestions=3)
    return {
        "base_slug": base_slug,
        "suggestions": suggestions,
    }


@router.get("/session", response_model=OnboardingSessionResponse)
async def get_onboarding_session(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Get or create the current user's onboarding session.

    - If no session exists, create one starting at step 1.
    - Safely parses JSON fields for completed_steps and partial_data.
    """
    session = None
    if current_user.onboarding_session_id:
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == current_user.onboarding_session_id
        ).first()

    if not session:
        # Create a new session starting at step 1
        session = OnboardingSession(
            admin_user_id=current_user.id,
            hospital_id=current_user.hospital_id,
            current_step=1,
            completed_steps='[]',
            partial_data='{}',
            status='in_progress',
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        current_user.onboarding_session_id = session.id
        db.commit()

    # Normalize JSON fields
    try:
        completed_steps = json.loads(session.completed_steps or "[]")
        if not isinstance(completed_steps, list):
            completed_steps = []
    except (json.JSONDecodeError, TypeError):
        completed_steps = []

    try:
        partial_data = json.loads(session.partial_data or "{}")
        if not isinstance(partial_data, dict):
            partial_data = {}
    except (json.JSONDecodeError, TypeError):
        partial_data = {}

    return OnboardingSessionResponse(
        id=session.id,
        current_step=session.current_step,
        completed_steps=completed_steps,
        partial_data=partial_data,
        status=session.status,
    )


@router.post("/session/update-step", response_model=OnboardingSessionResponse)
async def update_onboarding_session_step(
    request_body: OnboardingSessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Update the user's onboarding session step and optional data.

    - Only allows moving the step forward (or staying the same).
    - Merges completed_steps and partial_data.
    """
    if not current_user.onboarding_session_id:
        raise HTTPException(status_code=400, detail="Onboarding session not found")

    session = db.query(OnboardingSession).filter(
        OnboardingSession.id == current_user.onboarding_session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Onboarding session not found")

    # Move step forward only
    if request_body.current_step > session.current_step:
        session.current_step = request_body.current_step

    # Merge completed_steps
    try:
        completed_steps = json.loads(session.completed_steps or "[]")
        if not isinstance(completed_steps, list):
            completed_steps = []
    except (json.JSONDecodeError, TypeError):
        completed_steps = []

    if request_body.completed_steps:
        for step in request_body.completed_steps:
            if isinstance(step, int) and step not in completed_steps:
                completed_steps.append(step)
                # Track step completion
                try:
                    OnboardingAnalyticsService.track_event(
                        db=db,
                        event_type='step_complete',
                        onboarding_session_id=session.id,
                        admin_user_id=current_user.id,
                        step_number=step,
                    )
                except Exception as e:
                    logger.warning(f"Failed to track step completion: {str(e)}")

    session.completed_steps = json.dumps(completed_steps)

    # Merge partial_data (semantic keys, e.g. "hospital_info")
    try:
        partial_data = json.loads(session.partial_data or "{}")
        if not isinstance(partial_data, dict):
            partial_data = {}
    except (json.JSONDecodeError, TypeError):
        partial_data = {}

    if request_body.partial_data:
        for key, value in request_body.partial_data.items():
            partial_data[key] = value

    session.partial_data = json.dumps(partial_data)

    # Update status if provided
    if request_body.status in {"in_progress", "completed", "abandoned"}:
        session.status = request_body.status
        if request_body.status == "completed":
            session.completed_at = datetime.utcnow()
            # Track onboarding completion
            try:
                OnboardingAnalyticsService.track_event(
                    db=db,
                    event_type='onboarding_completed',
                    onboarding_session_id=session.id,
                    admin_user_id=current_user.id,
                )
            except Exception as e:
                logger.warning(f"Failed to track onboarding completion: {str(e)}")
        elif request_body.status == "abandoned":
            session.abandoned_at = datetime.utcnow()
            # Track abandonment
            try:
                OnboardingAnalyticsService.track_event(
                    db=db,
                    event_type='drop_off',
                    onboarding_session_id=session.id,
                    admin_user_id=current_user.id,
                    step_number=session.current_step,
                )
            except Exception as e:
                logger.warning(f"Failed to track abandonment: {str(e)}")

    # Track step start for next step
    if request_body.current_step and request_body.current_step > session.current_step:
        try:
            OnboardingAnalyticsService.track_step_start(
                db=db,
                onboarding_session_id=session.id,
                step_number=request_body.current_step,
            )
        except Exception as e:
            logger.warning(f"Failed to track step start: {str(e)}")

    session.last_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    return OnboardingSessionResponse(
        id=session.id,
        current_step=session.current_step,
        completed_steps=completed_steps,
        partial_data=partial_data,
        status=session.status,
    )


@router.get("/session/resume")
async def resume_onboarding(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Return the step and suggested frontend route the user should resume at.

    This is a lightweight helper; the frontend can also call /onboarding/session
    directly if it needs full session details.
    """
    session = None
    if current_user.onboarding_session_id:
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == current_user.onboarding_session_id
        ).first()

    if not session:
        # No session yet: start at registration
        return {
            "current_step": 1,
            "route": "/onboarding/register",
            "status": "in_progress",
        }

    step = session.current_step or 1

    # Map step → route (keep in sync with frontend)
    if step <= 1:
        route = "/onboarding/register"
    elif step == 2:
        route = "/onboarding/verify-email"
    else:
        route = "/onboarding/hospital-info"

    return {
        "current_step": step,
        "route": route,
        "status": session.status,
    }


@router.post("/hospital-info")
async def create_hospital_info(
    request_body: HospitalInfoRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Create a Hospital record as part of onboarding.

    Requirements:
    - Authenticated admin user (via JWT)
    - Email verified and account active
    """
    if not current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email must be verified before creating a hospital")
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Account is not active")

    name = request_body.hospital_name.strip()
    if len(name) < 2 or len(name) > 200:
        raise HTTPException(status_code=400, detail="Hospital name must be between 2 and 200 characters")

    # Enhanced slug validation
    slug = request_body.slug.strip().lower()
    is_valid, error_msg = SlugValidator.validate(slug)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid slug: {error_msg}")
    
    # Check availability using URLMappingService
    slug_result = URLMappingService.validate_slug(slug)
    if not slug_result.get("available"):
        reason = slug_result.get("reason") or "unavailable"
        raise HTTPException(status_code=400, detail=f"Slug is not available ({reason})")

    # Basic phone/website validation (very lightweight for now)
    phone = (request_body.phone or "").strip() or None
    website = (request_body.website or "").strip() or None

    # Create hospital
    hospital = Hospital(
        name=name,
        display_name=name,
        slug=slug,
        address=request_body.address.strip() if request_body.address else None,
        phone=phone,
        website=website,
        status="active",  # Consider onboarding_status for finer-grained tracking later
    )

    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    
    # Link admin user to hospital
    # Query user fresh from database to ensure it's tracked by the session
    user = db.query(AdminUser).filter(AdminUser.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hospital_id = hospital.id
    
    # Track hospital creation completion
    try:
        OnboardingAnalyticsService.track_event(
            db=db,
            event_type='hospital_info_submitted',
            onboarding_session_id=user.onboarding_session_id,
            admin_user_id=user.id,
            step_number=3,
        )
    except Exception as e:
        logger.warning(f"Failed to track hospital creation analytics: {str(e)}")

    # Update onboarding session if present
    if user.onboarding_session_id:
        onboarding_session = db.query(OnboardingSession).filter(
            OnboardingSession.id == user.onboarding_session_id
        ).first()
        if onboarding_session:
            onboarding_session.hospital_id = hospital.id

            # Safely update completed_steps JSON
            completed_steps = []
            try:
                if onboarding_session.completed_steps:
                    completed_steps = json.loads(onboarding_session.completed_steps)
                if not isinstance(completed_steps, list):
                    completed_steps = []
            except (json.JSONDecodeError, TypeError):
                completed_steps = []

            # Step numbering: step 1 = email verification, step 2 = hospital info
            if 2 not in completed_steps:
                completed_steps.append(2)
            onboarding_session.completed_steps = json.dumps(completed_steps)

            # Move to next step (e.g., slug / departments) if still on step 2
            if onboarding_session.current_step <= 2:
                onboarding_session.current_step = 3

            # Store partial data for this step
            partial_data = {}
            try:
                if onboarding_session.partial_data:
                    partial_data = json.loads(onboarding_session.partial_data)
                if not isinstance(partial_data, dict):
                    partial_data = {}
            except (json.JSONDecodeError, TypeError):
                partial_data = {}

            partial_data["hospital_info"] = {
                "hospital_name": name,
                "slug": slug,
                "address": hospital.address,
                "phone": phone,
                "website": website,
            }
            onboarding_session.partial_data = json.dumps(partial_data)
            onboarding_session.last_updated_at = datetime.utcnow()
            
            # Mark onboarding session as completed
            onboarding_session.status = 'completed'
            onboarding_session.completed_at = datetime.utcnow()
            onboarding_session.current_step = 4  # Mark as final step
            
            # Track onboarding completion
            try:
                OnboardingAnalyticsService.track_event(
                    db=db,
                    event_type='onboarding_completed',
                    onboarding_session_id=onboarding_session.id,
                    admin_user_id=user.id,
                    step_number=4,
                )
            except Exception as e:
                logger.warning(f"Failed to track onboarding completion: {str(e)}")

    # Mark onboarding as completed
    hospital.onboarding_status = 'completed'
    hospital.onboarding_completed_at = datetime.utcnow()

    db.commit()

    return {
        "hospital_id": hospital.id,
        "name": hospital.name,
        "slug": hospital.slug,
        "address": hospital.address,
        "phone": hospital.phone,
        "website": hospital.website,
        "status": hospital.status,
    }


@router.get("/complete/status")
async def get_completion_status(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    """
    Get onboarding completion status and hospital URLs for the completion screen.
    """
    # Query fresh user data from database (JWT may be stale after hospital creation)
    user = db.query(AdminUser).filter(AdminUser.id == current_user.id).first()
    
    if not user or not user.hospital_id:
        raise HTTPException(
            status_code=400,
            detail="Hospital not found. Please complete hospital setup first."
        )
    
    hospital = db.query(Hospital).filter(Hospital.id == user.hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    public_base_url = os.getenv("FRONTEND_URL", "https://yourdomain.com")
    
    return {
        "completed": hospital.onboarding_status == "completed",
        "hospital_slug": hospital.slug,
        "hospital_name": hospital.name,
        "admin_panel_url": f"{public_base_url}/h/{hospital.slug}/admin",
        "chat_url": f"{public_base_url}/h/{hospital.slug}",
        "checklist": [
            {"item": "Account created", "status": "completed"},
            {"item": "Email verified", "status": "completed" if user.email_verified else "incomplete"},
            {"item": "Hospital information saved", "status": "completed"},
            {"item": "URL created", "status": "completed", "details": f"{public_base_url}/h/{hospital.slug}"}
        ]
    }



