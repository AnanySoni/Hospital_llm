"""
Add Doctor Availability Slots
Creates availability slots for all doctors for August 2025
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.models import Doctor, DoctorAvailability
from datetime import datetime, date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_availability_slots():
    """Create availability slots for all doctors for August 2025"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all doctors
        doctors = db.query(Doctor).all()
        logger.info(f"Found {len(doctors)} doctors")
        
        if not doctors:
            logger.error("No doctors found in database")
            return
        
        # Define time slots (morning, afternoon, evening)
        time_slots = [
            "09:00-09:30", "09:30-10:00", "10:00-10:30", "10:30-11:00", "11:00-11:30", "11:30-12:00",  # Morning
            "14:00-14:30", "14:30-15:00", "15:00-15:30", "15:30-16:00", "16:00-16:30", "16:30-17:00",  # Afternoon
            "18:00-18:30", "18:30-19:00", "19:00-19:30", "19:30-20:00", "20:00-20:30", "20:30-21:00"   # Evening
        ]
        
        # Define August 2025 dates (1st to 31st)
        start_date = date(2025, 8, 1)
        end_date = date(2025, 8, 31)
        
        # Skip weekends (Saturday = 5, Sunday = 6)
        def is_weekend(d):
            return d.weekday() >= 5
        
        # Generate dates for August 2025 (excluding weekends)
        august_dates = []
        current_date = start_date
        while current_date <= end_date:
            if not is_weekend(current_date):
                august_dates.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(august_dates)} working days in August 2025")
        
        # Create availability slots for each doctor
        total_slots_created = 0
        
        for doctor in doctors:
            logger.info(f"Creating availability slots for Dr. {doctor.name} (ID: {doctor.id})")
            
            for appointment_date in august_dates:
                for time_slot in time_slots:
                    # Check if slot already exists
                    existing_slot = db.query(DoctorAvailability).filter(
                        DoctorAvailability.doctor_id == doctor.id,
                        DoctorAvailability.date == appointment_date,
                        DoctorAvailability.time_slot == time_slot
                    ).first()
                    
                    if not existing_slot:
                        # Create new availability slot
                        availability = DoctorAvailability(
                            doctor_id=doctor.id,
                            date=appointment_date,
                            time_slot=time_slot,
                            is_booked=False
                        )
                        db.add(availability)
                        total_slots_created += 1
                        
                        if total_slots_created % 100 == 0:
                            logger.info(f"Created {total_slots_created} slots so far...")
        
        # Commit all changes
        db.commit()
        
        logger.info(f"✅ Successfully created {total_slots_created} availability slots")
        logger.info(f"📅 August 2025 availability created for {len(doctors)} doctors")
        logger.info(f"🕐 {len(time_slots)} time slots per day (morning, afternoon, evening)")
        logger.info(f"📆 {len(august_dates)} working days (excluding weekends)")
        
        # Show summary by doctor
        for doctor in doctors:
            slot_count = db.query(DoctorAvailability).filter(
                DoctorAvailability.doctor_id == doctor.id,
                DoctorAvailability.date >= start_date,
                DoctorAvailability.date <= end_date
            ).count()
            logger.info(f"   Dr. {doctor.name}: {slot_count} slots")
        
    except Exception as e:
        logger.error(f"Error creating availability slots: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Main function to create doctor availability slots"""
    logger.info("🚀 Starting doctor availability slot creation...")
    create_availability_slots()
    logger.info("✅ Doctor availability slot creation completed!")

if __name__ == "__main__":
    main() 