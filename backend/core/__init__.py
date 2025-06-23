"""
Core package - Contains database configuration and core utilities
"""

from .database import engine, SessionLocal, get_db
from .models import Base, Doctor, Department, Subdivision, Appointment

__all__ = [
    "engine",
    "SessionLocal", 
    "get_db",
    "Base",
    "Doctor",
    "Department",
    "Subdivision",
    "Appointment"
] 