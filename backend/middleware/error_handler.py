"""
Error handling middleware and custom exceptions
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback
from typing import Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(AppError):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(message, 400, "VALIDATION_ERROR")


class NotFoundError(AppError):
    """Resource not found error"""
    def __init__(self, message: str):
        super().__init__(message, 404, "NOT_FOUND")


class ConflictError(AppError):
    """Resource conflict error"""
    def __init__(self, message: str):
        super().__init__(message, 409, "CONFLICT")


class AuthenticationError(AppError):
    """Authentication error"""
    def __init__(self, message: str):
        super().__init__(message, 401, "AUTHENTICATION_ERROR")


async def app_error_handler(request: Request, exc: AppError):
    """Handle custom application errors"""
    logger.error(f"App error: {exc.message} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "path": str(request.url.path)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors"""
    logger.error(f"Validation error: {exc.errors()} - Path: {request.url.path}")
    
    # Format validation errors nicely
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": errors,
            "path": str(request.url.path)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)} - Path: {request.url.path}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )


def setup_error_handlers(app):
    """Set up error handlers for the FastAPI app"""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


def handle_service_errors(func):
    """Decorator to convert service layer exceptions to HTTP exceptions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise ValidationError(str(e))
        except KeyError as e:
            raise NotFoundError(f"Resource not found: {str(e)}")
        except Exception as e:
            logger.error(f"Service error in {func.__name__}: {str(e)}")
            raise AppError(f"Service error: {str(e)}")
    return wrapper


# Removed async decorator - using direct error handling in endpoints instead 