"""
CSRF protection middleware for state-changing requests.
"""
import secrets
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.
    In production, use Redis or database for token storage instead of in-memory.
    """
    _csrf_tokens: Dict[str, str] = {}  # In-memory store (use Redis in production)
    
    # Endpoints that should skip CSRF (read-only or OAuth)
    SKIP_CSRF_PATHS = [
        '/onboarding/google/callback',  # OAuth callback handled by provider
        '/onboarding/google/login',  # OAuth redirect
        '/docs',  # API documentation
        '/openapi.json',  # OpenAPI schema
    ]
    
    # Methods that don't need CSRF (read-only)
    SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']
    
    async def dispatch(self, request: Request, call_next):
        """Check CSRF token for state-changing requests."""
        # Skip CSRF for safe methods
        if request.method in self.SAFE_METHODS:
            return await call_next(request)
        
        # Skip CSRF for specific paths
        if any(request.url.path.startswith(path) for path in self.SKIP_CSRF_PATHS):
            return await call_next(request)
        
        # Check CSRF token
        token = request.headers.get('X-CSRF-Token')
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
        
        if not token:
            raise HTTPException(
                status_code=403,
                detail="CSRF token missing. Please include X-CSRF-Token header."
            )
        
        if not session_id:
            raise HTTPException(
                status_code=403,
                detail="Session ID missing. Please include session_id cookie or X-Session-ID header."
            )
        
        if self._csrf_tokens.get(session_id) != token:
            raise HTTPException(
                status_code=403,
                detail="Invalid CSRF token. Please refresh the page and try again."
            )
        
        return await call_next(request)
    
    @staticmethod
    def generate_token(session_id: str) -> str:
        """
        Generate and store CSRF token.
        
        Args:
            session_id: Session identifier
        
        Returns:
            str: CSRF token
        """
        token = secrets.token_urlsafe(32)
        CSRFMiddleware._csrf_tokens[session_id] = token
        return token
    
    @staticmethod
    def get_token(session_id: str) -> Optional[str]:
        """
        Get existing CSRF token for session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Optional[str]: CSRF token if exists
        """
        return CSRFMiddleware._csrf_tokens.get(session_id)
    
    @staticmethod
    def invalidate_token(session_id: str):
        """
        Invalidate CSRF token for session.
        
        Args:
            session_id: Session identifier
        """
        CSRFMiddleware._csrf_tokens.pop(session_id, None)

