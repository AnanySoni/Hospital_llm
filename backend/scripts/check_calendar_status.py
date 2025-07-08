#!/usr/bin/env python3
"""
Check Google Calendar Connection Status for All Doctors
This script helps diagnose which doctors have calendar sync enabled
"""

import sys
import os
from datetime import datetime, date

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from integrations.google_calendar import get_doctor_credentials

def check_calendar_status():
    """Check Google Calendar connection status for all doctors"""
    print("🩺 Doctor Google Calendar Status Check")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all doctors
        doctors = db.query(models.Doctor).all()
        
        if not doctors:
            print("❌ No doctors found in the database")
            return
        
        print(f"📊 Checking {len(doctors)} doctors...\n")
        
        connected_count = 0
        disconnected_count = 0
        expired_count = 0
        
        for doctor in doctors:
            print(f"👨‍⚕️ {doctor.name} (ID: {doctor.id})")
            print(f"   Department: {doctor.department.name if doctor.department else 'None'}")
            print(f"   Subdivision: {doctor.subdivision.name if doctor.subdivision else 'None'}")
            
            # Check token status
            has_access_token = bool(doctor.google_access_token)
            has_refresh_token = bool(doctor.google_refresh_token)
            
            if not has_access_token and not has_refresh_token:
                print("   📅 Calendar Status: ❌ Not Connected")
                print("   💡 Solution: Visit /calendar-setup to connect this doctor's calendar")
                disconnected_count += 1
            else:
                # Check if credentials are valid
                credentials = get_doctor_credentials(doctor)
                if credentials and credentials.valid:
                    print("   📅 Calendar Status: ✅ Connected & Valid")
                    connected_count += 1
                    
                    # Check expiry
                    if doctor.token_expiry:
                        days_until_expiry = (doctor.token_expiry - date.today()).days
                        if days_until_expiry <= 7:
                            print(f"   ⚠️  Token expires in {days_until_expiry} days")
                        else:
                            print(f"   📆 Token expires in {days_until_expiry} days")
                else:
                    print("   📅 Calendar Status: ❌ Connected but Invalid/Expired")
                    print("   💡 Solution: Reconnect this doctor's calendar")
                    expired_count += 1
            
            print()  # Empty line between doctors
        
        # Summary
        print("📊 Summary:")
        print(f"   ✅ Connected & Valid: {connected_count}")
        print(f"   ❌ Not Connected: {disconnected_count}")
        print(f"   ⚠️  Connected but Expired: {expired_count}")
        print(f"   📈 Total Coverage: {connected_count}/{len(doctors)} ({(connected_count/len(doctors)*100):.1f}%)")
        
        if connected_count == len(doctors):
            print("\n🎉 All doctors have Google Calendar connected!")
        elif connected_count > 0:
            print(f"\n⚠️ {len(doctors) - connected_count} doctors need calendar setup")
            print("   💡 Visit http://localhost:8000/calendar-setup to connect missing calendars")
        else:
            print("\n❌ No doctors have Google Calendar connected")
            print("   💡 Visit http://localhost:8000/calendar-setup to set up calendar integration")
        
        # Check for recent appointment issues
        print(f"\n🔍 Checking recent appointments for sync issues...")
        
        # Get appointments from last 7 days
        from datetime import timedelta
        week_ago = date.today() - timedelta(days=7)
        
        recent_appointments = db.query(models.Appointment).filter(
            models.Appointment.date >= week_ago
        ).all()
        
        print(f"   📅 Found {len(recent_appointments)} appointments in last 7 days")
        
        sync_issues = 0
        for appointment in recent_appointments:
            appointment_doctor = db.query(models.Doctor).filter(
                models.Doctor.id == appointment.doctor_id
            ).first()
            
            if appointment_doctor and not get_doctor_credentials(appointment_doctor):
                sync_issues += 1
        
        if sync_issues > 0:
            print(f"   ⚠️  {sync_issues} appointments may have had calendar sync issues")
        else:
            print("   ✅ No obvious calendar sync issues found")
        
    except Exception as e:
        print(f"❌ Error checking calendar status: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    check_calendar_status() 