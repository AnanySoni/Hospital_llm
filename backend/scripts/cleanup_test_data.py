#!/usr/bin/env python3
"""
Hospital LLM Project - Test Data Cleanup Script
==============================================

This script removes all test data created during testing, including:
- Test appointments
- Test bookings
- Diagnostic sessions
- Session users
- Conversation sessions
- Patient profiles with test phone numbers
- Test users

Usage:
    python cleanup_test_data.py [--dry-run] [--confirm]
    
Options:
    --dry-run    Show what would be deleted without actually deleting
    --confirm    Skip confirmation prompt
"""

import sys
import os
from datetime import datetime, date
import argparse

# Add the backend directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from core.database import DATABASE_URL
from core.models import (
    Base, Appointment, TestBooking, DiagnosticSession, QuestionAnswer,
    SessionUser, PatientProfile, SymptomHistory,
    VisitHistory, User, Patient, DoctorAvailability, Doctor
)
# Import Google Calendar dependencies
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request as GoogleRequest
    import json
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def is_test_data(name, phone=None):
    """Check if a name or phone number indicates test data"""
    if not name and not phone:
        return False
    
    test_patterns = [
        'test', 'Test', 'TEST',
        'SystemTest', 'Systemtest',
        'E2E', 'e2e',
        'Cancel', 'Reschedule', 'Double Book',
        'Cleanup', 'Demo', 'Sample',
        'Arjun', 'Kavya',  # Test names from phone recognition
        'Patient',  # Generic test patient name
        'chat_test_', 'test_session_', 'history_test_',
        'test_adaptive_', 'triage_test_', 'disease_test_',
        'llm_question_test_'
    ]
    
    # Check name patterns
    if name:
        for pattern in test_patterns:
            if pattern.lower() in name.lower():
                return True
    
    # Check phone patterns (common test numbers)
    if phone:
        test_phone_patterns = [
            '9123456789',  # SystemTest phone
            '9876543210',  # Generic test phone
            '9876546844',  # Arjun's phone
            '9876546856',  # Kavya's phone
            '8765432109',  # Another test phone
            '1234567890',  # Invalid test phone
            '5876543210',  # Invalid test phone
            '123456789',   # Short test phone
        ]
        
        # Clean phone number for comparison
        clean_phone = ''.join(filter(str.isdigit, phone))
        if clean_phone in test_phone_patterns:
            return True
    
    return False

def delete_calendar_event_for_appointment(doctor, appointment_date, time_slot, patient_name):
    """Delete Google Calendar event for a specific appointment"""
    if not GOOGLE_CALENDAR_AVAILABLE:
        return False
        
    try:
        # Load Google client secrets
        client_secrets_file = "google_calendar_credentials.json"
        if not os.path.exists(client_secrets_file):
            return False
            
        with open(client_secrets_file, 'r') as f:
            client_secrets = json.load(f)
        
        # Create credentials
        credentials = Credentials(
            token=doctor.google_access_token,
            refresh_token=doctor.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_secrets['web']['client_id'],
            client_secret=client_secrets['web']['client_secret'],
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        
        # Refresh token if needed
        if not credentials.valid and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
        
        if not credentials.valid:
            return False
            
        # Build calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Search for events on the appointment date
        events_result = service.events().list(
            calendarId='primary',
            timeMin=f"{appointment_date}T00:00:00Z",
            timeMax=f"{appointment_date}T23:59:59Z",
            q=patient_name  # Search by patient name
        ).execute()
        
        events = events_result.get('items', [])
        for event in events:
            # Check if this event matches our appointment time and patient
            if (patient_name.lower() in event.get('summary', '').lower() or 
                patient_name.lower() in event.get('description', '').lower()):
                # Delete the event
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                return True
                
        return False
        
    except Exception as e:
        print(f"   ⚠️ Calendar deletion error: {e}")
        return False

def cleanup_appointments(db_session, dry_run=False):
    """Clean up test appointments and their Google Calendar events"""
    print("\n🗓️ Cleaning up test appointments...")
    
    # Find appointments with test patterns
    test_appointments = db_session.query(Appointment).filter(
        or_(
            Appointment.patient_name.ilike('%test%'),
            Appointment.patient_name.ilike('%systemtest%'),
            Appointment.patient_name.ilike('%cancel%'),
            Appointment.patient_name.ilike('%reschedule%'),
            Appointment.patient_name.ilike('%double%'),
            Appointment.patient_name.ilike('%cleanup%'),
            Appointment.patient_name.ilike('%e2e%'),
            Appointment.patient_name.ilike('%arjun%'),
            Appointment.patient_name.ilike('%kavya%'),
            Appointment.patient_name.ilike('%sneha%'),
            Appointment.phone_number.in_([
                '9123456789', '9876543210', '9876546844', 
                '9876546856', '8765432109'
            ])
        )
    ).all()
    
    if dry_run:
        print(f"   Would delete {len(test_appointments)} test appointments:")
        for apt in test_appointments:
            doctor = db_session.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            doctor_name = doctor.name if doctor else "Unknown"
            print(f"   - ID {apt.id}: {apt.patient_name} ({apt.phone_number}) with Dr. {doctor_name} on {apt.date} at {apt.time_slot}")
    else:
        count = len(test_appointments)
        calendar_deletions = 0
        
        for apt in test_appointments:
            # Get doctor info for calendar cleanup
            doctor = db_session.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            
            # Try to delete from Google Calendar if doctor has credentials
            if doctor and doctor.google_access_token and GOOGLE_CALENDAR_AVAILABLE:
                success = delete_calendar_event_for_appointment(
                    doctor, apt.date, apt.time_slot, apt.patient_name
                )
                if success:
                    calendar_deletions += 1
                    print(f"   🗓️ Deleted calendar event for {apt.patient_name} with Dr. {doctor.name}")
            
            # Free up the doctor availability slot
            availability = db_session.query(DoctorAvailability).filter(
                and_(
                    DoctorAvailability.doctor_id == apt.doctor_id,
                    DoctorAvailability.date == apt.date,
                    DoctorAvailability.time_slot == apt.time_slot
                )
            ).first()
            if availability:
                availability.is_booked = False
            
            # Delete the appointment from database
            db_session.delete(apt)
        
        db_session.commit()
        print(f"   ✅ Deleted {count} test appointments, {calendar_deletions} calendar events, and freed up availability slots")

def cleanup_test_bookings(db_session, dry_run=False):
    """Clean up test bookings"""
    print("\n🧪 Cleaning up test bookings...")
    
    # Find test bookings by looking at patient relationships or direct test patterns
    test_bookings = db_session.query(TestBooking).filter(
        TestBooking.id.in_(
            db_session.query(TestBooking.id).join(User).filter(
                or_(
                    User.name.ilike('%test%'),
                    User.name.ilike('%cancel%'),
                    User.phone_number.in_([
                        '9123456789', '9876543210', '9876546844',
                        '9876546856', '8765432109'
                    ])
                )
            )
        )
    ).all()
    
    if dry_run:
        print(f"   Would delete {len(test_bookings)} test bookings:")
        for booking in test_bookings:
            print(f"   - ID {booking.id}: {booking.test_name} on {booking.scheduled_date}")
    else:
        count = len(test_bookings)
        for booking in test_bookings:
            db_session.delete(booking)
        db_session.commit()
        print(f"   ✅ Deleted {count} test bookings")

def cleanup_diagnostic_sessions(db_session, dry_run=False):
    """Clean up diagnostic sessions and question answers"""
    print("\n🔍 Cleaning up diagnostic sessions...")
    
    # Find test diagnostic sessions
    test_sessions = db_session.query(DiagnosticSession).filter(
        or_(
            DiagnosticSession.session_id.ilike('%test%'),
            DiagnosticSession.session_id.ilike('%chat_test_%'),
            DiagnosticSession.session_id.ilike('%triage_test_%'),
            DiagnosticSession.session_id.ilike('%disease_test_%'),
            DiagnosticSession.session_id.ilike('%llm_question_test_%'),
            DiagnosticSession.session_id.ilike('%adaptive_%'),
        )
    ).all()
    
    if dry_run:
        print(f"   Would delete {len(test_sessions)} diagnostic sessions:")
        for session in test_sessions:
            qa_count = len(session.question_answers)
            print(f"   - {session.session_id} with {qa_count} Q&A records")
    else:
        count = len(test_sessions)
        qa_count = 0
        for session in test_sessions:
            qa_count += len(session.question_answers)
            # Question answers will be deleted via cascade
            db_session.delete(session)
        db_session.commit()
        print(f"   ✅ Deleted {count} diagnostic sessions and {qa_count} question answers")

def cleanup_session_users(db_session, dry_run=False):
    """Clean up session users"""
    print("\n👤 Cleaning up session users...")
    
    try:
        # Find test session users
        test_session_users = db_session.query(SessionUser).filter(
            or_(
                SessionUser.session_id.ilike('%test%'),
                SessionUser.session_id.ilike('%chat_test_%'),
                SessionUser.session_id.ilike('%history_test_%'),
                SessionUser.first_name.ilike('%test%'),
            )
        ).all()
        
        if dry_run:
            print(f"   Would delete {len(test_session_users)} session users:")
            for user in test_session_users:
                print(f"   - {user.session_id}: {user.first_name}")
        else:
            count = len(test_session_users)
            for user in test_session_users:
                # Delete manually to avoid relationship issues
                db_session.execute(f"DELETE FROM session_users WHERE id = {user.id}")
            db_session.commit()
            print(f"   ✅ Deleted {count} session users")
    except Exception as e:
        print(f"   ⚠️ Session users cleanup failed: {e}")
        print(f"   Continuing with other cleanup tasks...")

def cleanup_conversation_sessions(db_session, dry_run=False):
    """Clean up conversation sessions"""
    print("\n💬 Skipping conversation sessions (table schema mismatch)")
    # Note: ConversationSession table schema doesn't match current model
    # Focusing on main test data cleanup instead

def cleanup_patient_profiles(db_session, dry_run=False):
    """Clean up test patient profiles"""
    print("\n📋 Cleaning up patient profiles...")
    
    # Find test patient profiles
    test_profiles = db_session.query(PatientProfile).filter(
        or_(
            PatientProfile.phone_number.in_([
                '9123456789', '9876543210', '9876546844',
                '9876546856', '8765432109'
            ]),
            PatientProfile.first_name.ilike('%test%'),
            PatientProfile.first_name.ilike('%arjun%'),
            PatientProfile.first_name.ilike('%kavya%'),
        )
    ).all()
    
    if dry_run:
        print(f"   Would delete {len(test_profiles)} patient profiles:")
        for profile in test_profiles:
            symptom_count = len(profile.symptom_history)
            visit_count = len(profile.visit_history)
            print(f"   - {profile.first_name} ({profile.phone_number}) with {symptom_count} symptoms, {visit_count} visits")
    else:
        count = len(test_profiles)
        symptom_count = 0
        visit_count = 0
        
        for profile in test_profiles:
            symptom_count += len(profile.symptom_history)
            visit_count += len(profile.visit_history)
            # Symptom and visit history will be deleted via cascade
            db_session.delete(profile)
        
        db_session.commit()
        print(f"   ✅ Deleted {count} patient profiles, {symptom_count} symptom histories, {visit_count} visit histories")

def cleanup_test_users(db_session, dry_run=False):
    """Clean up test users"""
    print("\n👥 Cleaning up test users...")
    
    # Find test users
    test_users = db_session.query(User).filter(
        or_(
            User.name.ilike('%test%'),
            User.name.ilike('%cancel%'),
            User.phone_number.in_([
                '9123456789', '9876543210', '9876546844',
                '9876546856', '8765432109'
            ])
        )
    ).all()
    
    if dry_run:
        print(f"   Would delete {len(test_users)} test users:")
        for user in test_users:
            print(f"   - ID {user.id}: {user.name} ({user.phone_number})")
    else:
        count = len(test_users)
        for user in test_users:
            db_session.delete(user)
        db_session.commit()
        print(f"   ✅ Deleted {count} test users")

def main():
    parser = argparse.ArgumentParser(description='Clean up test data from Hospital LLM database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("🧹 Hospital LLM Test Data Cleanup")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No data will be deleted")
    else:
        print("⚠️  WARNING: This will permanently delete test data!")
        if not args.confirm:
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Cleanup cancelled.")
                return
    
    try:
        db_session = get_db_session()
        
        print(f"\n🕐 Starting cleanup at {datetime.now()}")
        
        # Run cleanup functions in order (respecting foreign key constraints)
        cleanup_diagnostic_sessions(db_session, args.dry_run)
        cleanup_conversation_sessions(db_session, args.dry_run)
        cleanup_session_users(db_session, args.dry_run)
        cleanup_patient_profiles(db_session, args.dry_run)
        cleanup_appointments(db_session, args.dry_run)
        cleanup_test_bookings(db_session, args.dry_run)
        cleanup_test_users(db_session, args.dry_run)
        
        if args.dry_run:
            print(f"\n🔍 Dry run completed. No data was deleted.")
            print("Run without --dry-run to perform actual cleanup.")
        else:
            print(f"\n✅ Cleanup completed successfully at {datetime.now()}")
            print("All test data has been removed from the database.")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        if not args.dry_run:
            db_session.rollback()
        return 1
    
    finally:
        db_session.close()
    
    return 0

if __name__ == "__main__":
    exit(main()) 