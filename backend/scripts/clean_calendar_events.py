#!/usr/bin/env python3
"""
Clean Google Calendar Events for Test Appointments
================================================

This script searches for and deletes Google Calendar events that were created
for test appointments but may still exist in the calendar.

Usage:
    python clean_calendar_events.py [--dry-run]
"""

import sys
import os
from datetime import datetime, date, timedelta
import argparse

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request as GoogleRequest
    import json
    GOOGLE_AVAILABLE = True
except ImportError:
    print("❌ Google Calendar libraries not available")
    GOOGLE_AVAILABLE = False
    sys.exit(1)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import DATABASE_URL
from backend.core.models import Doctor

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_doctor_credentials(doctor):
    """Get Google credentials for a doctor"""
    if not doctor.google_access_token:
        return None
    
    try:
        # Load client secrets - try different possible filenames
        client_secrets_file = None
        possible_files = [
            "google_calendar_credentials.json",
            "credentials.json", 
            "client_secret.json"
        ]
        
        for filename in possible_files:
            if os.path.exists(filename):
                client_secrets_file = filename
                break
        
        if not client_secrets_file:
            print(f"❌ No Google credentials file found for {doctor.name}")
            return None
            
        with open(client_secrets_file, 'r') as f:
            client_secrets = json.load(f)
        
        credentials = Credentials(
            token=doctor.google_access_token,
            refresh_token=doctor.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_secrets['web']['client_id'],
            client_secret=client_secrets['web']['client_secret'],
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        
        # Refresh if needed
        if not credentials.valid and credentials.refresh_token:
            try:
                credentials.refresh(GoogleRequest())
                print(f"🔄 Refreshed credentials for {doctor.name}")
            except Exception as e:
                print(f"❌ Failed to refresh credentials for {doctor.name}: {e}")
                return None
        
        return credentials if credentials.valid else None
        
    except Exception as e:
        print(f"❌ Error getting credentials for {doctor.name}: {e}")
        return None

def clean_calendar_events_for_doctor(doctor, dry_run=False):
    """Clean test events from a doctor's calendar"""
    credentials = get_doctor_credentials(doctor)
    if not credentials:
        return 0
    
    try:
        service = build('calendar', 'v3', credentials=credentials)
        
        # Search for events in the last 30 days and next 30 days
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = (date.today() + timedelta(days=30)).isoformat()
        
        print(f"🔍 Searching calendar events for Dr. {doctor.name}...")
        
        # Get all events in the date range
        events_result = service.events().list(
            calendarId='primary',
            timeMin=f"{start_date}T00:00:00Z",
            timeMax=f"{end_date}T23:59:59Z",
            maxResults=100
        ).execute()
        
        events = events_result.get('items', [])
        test_events = []
        
        # Filter for test events
        test_patterns = [
            'test', 'systemtest', 'cancel', 'reschedule', 'double book',
            'e2e', 'arjun', 'kavya', 'sneha', 'cleanup', 'demo'
        ]
        
        for event in events:
            summary = event.get('summary', '').lower()
            description = event.get('description', '').lower()
            
            # Check if this looks like a test event
            is_test_event = any(
                pattern in summary or pattern in description 
                for pattern in test_patterns
            )
            
            if is_test_event:
                test_events.append(event)
        
        if dry_run:
            print(f"   Would delete {len(test_events)} test events:")
            for event in test_events:
                start_time = event.get('start', {}).get('dateTime', 'Unknown time')
                print(f"   - {event.get('summary', 'No title')} at {start_time}")
        else:
            deleted_count = 0
            for event in test_events:
                try:
                    service.events().delete(calendarId='primary', eventId=event['id']).execute()
                    print(f"   🗓️ Deleted: {event.get('summary', 'No title')}")
                    deleted_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to delete event {event.get('summary', 'No title')}: {e}")
            
            print(f"   ✅ Deleted {deleted_count} test events for Dr. {doctor.name}")
            return deleted_count
    
    except Exception as e:
        print(f"❌ Error cleaning calendar for Dr. {doctor.name}: {e}")
        return 0
    
    return len(test_events) if dry_run else 0

def main():
    parser = argparse.ArgumentParser(description='Clean test events from Google Calendar')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    
    args = parser.parse_args()
    
    print("🗓️ Google Calendar Test Events Cleanup")
    print("=" * 50)
    
    if not GOOGLE_AVAILABLE:
        print("❌ Google Calendar libraries not available")
        return 1
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No events will be deleted")
    else:
        print("⚠️  WARNING: This will permanently delete test calendar events!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cleanup cancelled.")
            return 0
    
    try:
        db_session = get_db_session()
        
        # Get all doctors with Google Calendar credentials
        doctors_with_calendar = db_session.query(Doctor).filter(
            Doctor.google_access_token.isnot(None)
        ).all()
        
        if not doctors_with_calendar:
            print("❌ No doctors found with Google Calendar credentials")
            return 0
        
        print(f"📅 Found {len(doctors_with_calendar)} doctors with Google Calendar access")
        
        total_deleted = 0
        for doctor in doctors_with_calendar:
            deleted = clean_calendar_events_for_doctor(doctor, args.dry_run)
            total_deleted += deleted
        
        if args.dry_run:
            print(f"\n🔍 Dry run completed. Would delete {total_deleted} total events.")
        else:
            print(f"\n✅ Cleanup completed. Deleted {total_deleted} total test events.")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        return 1
    
    finally:
        db_session.close()
    
    return 0

if __name__ == "__main__":
    exit(main()) 