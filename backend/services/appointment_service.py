"""
Appointment Service Layer
Handles all appointment-related business logic
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core import models
from integrations.google_calendar import create_calendar_event


class AppointmentService:
    
    @staticmethod
    async def create_appointment(
        db: Session,
        doctor_id: int,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        notes: Optional[str] = None,
        symptoms: Optional[str] = None
    ) -> dict:
        """Create a new appointment with validation"""
        
        # Validate doctor exists
        doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
        if not doctor:
            raise ValueError(f"Doctor with ID {doctor_id} not found")
        
        # Validate date is not in the past
        appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        if appointment_date_obj < date.today():
            raise ValueError("Cannot book appointments in the past")
        
        # Validate time format
        try:
            datetime.strptime(appointment_time, "%H:%M")
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM format (e.g., 14:30)")
        
        # Check for conflicts (optional - can be enhanced)
        existing_appointment = db.query(models.Appointment).filter(
            and_(
                models.Appointment.doctor_id == doctor_id,
                models.Appointment.date == appointment_date_obj,
                models.Appointment.time_slot == appointment_time,
                models.Appointment.status != 'cancelled'  # Exclude cancelled appointments
            )
        ).first()
        
        if existing_appointment:
            raise ValueError("This time slot is already booked")
        
        # Create appointment
        appointment = models.Appointment(
            doctor_id=doctor_id,
            patient_name=patient_name.strip(),
            date=appointment_date_obj,
            time_slot=appointment_time,
            status="scheduled",
            notes=notes.strip() if notes else None
        )
        
        db.add(appointment)
        db.flush()  # Get the ID without committing
        
        # Create calendar event if doctor has connected calendar
        appointment_data = {
            "patient_name": patient_name,
            "date": appointment_date,
            "time_slot": appointment_time,
            "notes": notes,
            "symptoms": symptoms,
            "doctor_name": doctor.name
        }
        
        calendar_success = False
        try:
            calendar_success = await create_calendar_event(doctor, appointment_data, db)
        except Exception as e:
            print(f"Calendar integration failed: {e}")
        
        db.commit()
        db.refresh(appointment)
        
        return {
            "id": appointment.id,
            "message": "Appointment booked successfully",
            "doctor_name": doctor.name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "calendar_event_created": calendar_success,
            "note": "Calendar event automatically added to doctor's Google Calendar" if calendar_success else "Doctor needs to connect Google Calendar for automatic sync"
        }
    
    @staticmethod
    async def reschedule_appointment(
        db: Session,
        appointment_id: int,
        new_date: str,
        new_time: str
    ) -> dict:
        """Reschedule an existing appointment"""
        
        # Validate appointment exists
        appointment = db.query(models.Appointment).filter(
            models.Appointment.id == appointment_id
        ).first()
        if not appointment:
            raise ValueError(f"Appointment with ID {appointment_id} not found")
        
        # Validate new date is not in the past
        new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
        if new_date_obj < date.today():
            raise ValueError("Cannot reschedule to a past date")
        
        # Validate time format
        try:
            datetime.strptime(new_time, "%H:%M")
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM format (e.g., 14:30)")
        
        doctor = db.query(models.Doctor).filter(
            models.Doctor.id == appointment.doctor_id
        ).first()
        
        # Store old values for calendar update
        old_date = appointment.date
        old_time = appointment.time_slot
        
        # Update appointment
        appointment.date = new_date_obj
        appointment.time_slot = new_time
        appointment.status = "rescheduled"
        
        # Update calendar event
        appointment_data = {
            "patient_name": appointment.patient_name,
            "date": new_date,
            "time_slot": new_time,
            "notes": appointment.notes,
            "doctor_name": doctor.name,
            "old_date": old_date.strftime("%Y-%m-%d"),
            "old_time": old_time
        }
        
        calendar_success = False
        try:
            calendar_success = await create_calendar_event(
                doctor, appointment_data, db, is_reschedule=True
            )
        except Exception as e:
            print(f"Calendar update failed: {e}")
        
        db.commit()
        db.refresh(appointment)
        
        return {
            "message": "Appointment rescheduled successfully",
            "id": appointment.id,
            "doctor_name": doctor.name,
            "patient_name": appointment.patient_name,
            "appointment_date": new_date,
            "appointment_time": new_time,
            "notes": appointment.notes,
            "status": appointment.status,
            "calendar_event_updated": calendar_success
        }
    
    @staticmethod
    async def cancel_appointment(db: Session, appointment_id: int) -> dict:
        """Cancel an existing appointment"""
        
        appointment = db.query(models.Appointment).filter(
            models.Appointment.id == appointment_id
        ).first()
        if not appointment:
            raise ValueError(f"Appointment with ID {appointment_id} not found")
        
        if appointment.status == "cancelled":
            raise ValueError("Appointment is already cancelled")
        
        doctor = db.query(models.Doctor).filter(
            models.Doctor.id == appointment.doctor_id
        ).first()
        
        # Update appointment status
        appointment.status = "cancelled"
        
        # Update calendar event
        appointment_data = {
            "patient_name": appointment.patient_name,
            "date": appointment.date.strftime("%Y-%m-%d"),
            "time_slot": appointment.time_slot,
            "doctor_name": doctor.name
        }
        
        calendar_success = False
        try:
            calendar_success = await create_calendar_event(
                doctor, appointment_data, db, is_cancellation=True
            )
        except Exception as e:
            print(f"Calendar update failed: {e}")
        
        db.commit()
        
        return {
            "message": "Appointment cancelled successfully",
            "calendar_event_cancelled": calendar_success
        }
    
    @staticmethod
    def get_appointments_by_patient(db: Session, patient_name: str) -> List[dict]:
        """Get all appointments for a specific patient"""
        
        appointments = db.query(models.Appointment).filter(
            models.Appointment.patient_name.ilike(f"%{patient_name}%")
        ).all()
        
        result = []
        for appointment in appointments:
            doctor = db.query(models.Doctor).filter(
                models.Doctor.id == appointment.doctor_id
            ).first()
            
            result.append({
                "id": appointment.id,
                "doctor_name": doctor.name if doctor else "Unknown",
                "appointment_date": appointment.date.strftime("%Y-%m-%d"),
                "appointment_time": appointment.time_slot,
                "status": appointment.status,
                "notes": appointment.notes
            })
        
        return result 