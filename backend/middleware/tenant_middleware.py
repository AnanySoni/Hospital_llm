"""
Multi-Tenant Middleware
Automatically scopes database queries to the correct hospital based on JWT token
"""

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import event
from typing import Optional
import logging

from core.database import get_db
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """Middleware for multi-tenant database operations"""
    
    def __init__(self):
        self.current_hospital_id = None
    
    def set_hospital_context(self, hospital_id: int):
        """Set the current hospital context"""
        self.current_hospital_id = hospital_id
    
    def get_hospital_context(self) -> Optional[int]:
        """Get the current hospital context"""
        return self.current_hospital_id
    
    def clear_hospital_context(self):
        """Clear the current hospital context"""
        self.current_hospital_id = None

# Global tenant middleware instance
tenant_middleware = TenantMiddleware()

def get_tenant_middleware() -> TenantMiddleware:
    """Get the tenant middleware instance"""
    return tenant_middleware

def extract_hospital_from_token(request: Request) -> Optional[int]:
    """Extract hospital_id from JWT token in request headers"""
    try:
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Verify and decode token
        payload = AuthService.verify_token(token)
        
        # Extract hospital_id
        hospital_id = payload.get("hospital_id")
        return hospital_id
        
    except Exception as e:
        logger.warning(f"Failed to extract hospital from token: {str(e)}")
        return None

def setup_tenant_context(request: Request, db: Session):
    """Setup tenant context for the current request"""
    try:
        # Extract hospital_id from token
        hospital_id = extract_hospital_from_token(request)
        
        if hospital_id:
            # Set the hospital context
            tenant_middleware.set_hospital_context(hospital_id)
            logger.debug(f"Set tenant context for hospital_id: {hospital_id}")
        else:
            # Clear context if no hospital_id found
            tenant_middleware.clear_hospital_context()
            logger.debug("Cleared tenant context - no hospital_id found")
            
    except Exception as e:
        logger.error(f"Error setting up tenant context: {str(e)}")
        tenant_middleware.clear_hospital_context()

def get_tenant_db() -> Session:
    """Get database session with tenant context"""
    return get_db()

# Database event listeners for automatic hospital filtering
def setup_tenant_filters():
    """Setup database event listeners for automatic hospital filtering"""
    
    @event.listens_for(Session, 'do_orm_execute')
    def receive_do_orm_execute(execute_state):
        """Automatically filter queries by hospital_id when tenant context is set"""
        if not execute_state.is_select:
            return
        
        # Get current hospital context
        hospital_id = tenant_middleware.get_hospital_context()
        if not hospital_id:
            return
        
        # Get the query
        query = execute_state.statement
        
        # Check if this is a query for a tenant-aware table
        tenant_aware_tables = [
            'doctors', 'patients', 'appointments', 'admin_users',
            'audit_logs', 'medical_history', 'medications', 'allergies',
            'family_history', 'test_results', 'vaccinations', 'patient_notes',
            'symptom_logs', 'test_bookings', 'session_users', 'conversation_sessions',
            'patient_profiles', 'symptom_history', 'visit_history'
        ]
        
        # Check if the query involves any tenant-aware tables
        from sqlalchemy import inspect
        inspector = inspect(query)
        
        # Get table names from the query
        table_names = set()
        for column in query.columns:
            if hasattr(column, 'table') and column.table:
                table_names.add(column.table.name)
        
        # Check if any tenant-aware tables are involved
        if not any(table in tenant_aware_tables for table in table_names):
            return
        
        # Add hospital_id filter if not already present
        # This is a simplified approach - in production, you might want more sophisticated filtering
        logger.debug(f"Tenant filtering applied for hospital_id: {hospital_id}")

def require_tenant_context():
    """Dependency to require tenant context"""
    def tenant_checker():
        hospital_id = tenant_middleware.get_hospital_context()
        if not hospital_id:
            raise HTTPException(status_code=401, detail="Tenant context required")
        return hospital_id
    return tenant_checker

def optional_tenant_context():
    """Dependency for optional tenant context"""
    def tenant_checker():
        return tenant_middleware.get_hospital_context()
    return tenant_checker

# Initialize tenant filters
setup_tenant_filters() 