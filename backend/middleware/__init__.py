"""
Middleware package - Contains FastAPI middleware components
"""

from .error_handler import (
    setup_error_handlers,
    AppError,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthenticationError
)

__all__ = [
    "setup_error_handlers",
    "AppError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "AuthenticationError"
] 