#!/usr/bin/env python3
"""
Test Google Calendar Sync for Appointments
This script tests reschedule and cancel operations with Google Calendar sync
"""

import sys
import os
import asyncio
from datetime import datetime, date, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from services.appointment_service import AppointmentService

async def test_calendar_sync():
    """Test calendar sync for reschedule and cancel operations"""
    print("🧪 Testing Google Calendar Sync for Appointments")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    # Find a doctor with Google Calendar connected
    doctor_with_calendar = db.query(models.Doctor).filter(
        models.Doctor.google_access_token.isnot(None)
    ).first()
    
    if not doctor_with_calendar:
        print("❌ No doctors found with Google Calendar connected")
        print("   Please connect at least one doctor's calendar first")
        return
    
    print(f"📅 Found doctor with calendar: {doctor_with_calendar.name}")
    
    # Create a test appointment
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    test_time = "14:00"
    
    try:
        print(f"\n1️⃣ Creating test appointment for {tomorrow} at {test_time}")
        appointment_result = await AppointmentService.create_appointment(
            db=db,
            doctor_id=doctor_with_calendar.id,
            patient_name="Calendar Test Patient",
            phone_number="9876543210",
            appointment_date=tomorrow,
            appointment_time=test_time,
            notes="Test appointment for calendar sync verification",
            symptoms="Calendar sync test"
        )
        
        appointment_id = appointment_result['id']
        calendar_created = appointment_result.get('calendar_event_created', False)
        
        print(f"✅ Appointment created: ID {appointment_id}")
        print(f"📅 Calendar event created: {'Yes' if calendar_created else 'No'}")
        
        if not calendar_created:
            print("⚠️ Calendar event was not created during appointment booking")
        
        # Test reschedule
        day_after_tomorrow = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
        new_time = "15:30"
        
        print(f"\n2️⃣ Rescheduling appointment to {day_after_tomorrow} at {new_time}")
        reschedule_result = await AppointmentService.reschedule_appointment(
            db=db,
            appointment_id=appointment_id,
            new_date=day_after_tomorrow,
            new_time=new_time
        )
        
        calendar_updated = reschedule_result.get('calendar_event_updated', False)
        print(f"✅ Appointment rescheduled")
        print(f"📅 Calendar event updated: {'Yes' if calendar_updated else 'No'}")
        
        if not calendar_updated:
            print("⚠️ Calendar event was not updated during reschedule")
        
        # Test cancellation
        print(f"\n3️⃣ Cancelling the test appointment")
        cancel_result = await AppointmentService.cancel_appointment(
            db=db,
            appointment_id=appointment_id
        )
        
        calendar_cancelled = cancel_result.get('calendar_event_cancelled', False)
        print(f"✅ Appointment cancelled")
        print(f"📅 Calendar event deleted: {'Yes' if calendar_cancelled else 'No'}")
        
        if not calendar_cancelled:
            print("⚠️ Calendar event was not deleted during cancellation")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   - Appointment Creation → Calendar: {'✅' if calendar_created else '❌'}")
        print(f"   - Appointment Reschedule → Calendar: {'✅' if calendar_updated else '❌'}")
        print(f"   - Appointment Cancellation → Calendar: {'✅' if calendar_cancelled else '❌'}")
        
        success_count = sum([calendar_created, calendar_updated, calendar_cancelled])
        print(f"\n🎯 Calendar Sync Success Rate: {success_count}/3 operations")
        
        if success_count == 3:
            print("🎉 All calendar sync operations successful!")
        elif success_count >= 1:
            print("⚠️ Partial calendar sync success - check doctor's Google Calendar connection")
        else:
            print("❌ No calendar sync operations successful - check Google Calendar integration")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_calendar_sync()) 