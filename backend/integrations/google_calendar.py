"""
Google Calendar Integration for Hospital Appointment System
Provides OAuth2 authentication and calendar event management
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

from core.database import get_db
from core import models

router = APIRouter()

# Google Calendar configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CLIENT_SECRETS_FILE = "credentials.json"
REDIRECT_URI = "http://localhost:8000/auth/callback"

@router.get("/calendar-status")
async def check_calendar_status():
    """Check if Google Calendar integration is properly configured."""
    try:
        if not os.path.exists(GOOGLE_CLIENT_SECRETS_FILE):
            return {
                "configured": False,
                "message": "Google Calendar credentials not found. Please set up credentials.json file.",
                "file_expected": GOOGLE_CLIENT_SECRETS_FILE
            }
        
        # Try to read the credentials file
        try:
            with open(GOOGLE_CLIENT_SECRETS_FILE, 'r') as f:
                credentials_data = json.load(f)
            
            # Check if it has the required structure
            if 'web' in credentials_data and 'client_id' in credentials_data['web']:
                return {
                    "configured": True,
                    "message": "Google Calendar integration is properly configured",
                    "client_id": credentials_data['web']['client_id'][:20] + "..."
                }
            else:
                return {
                    "configured": False,
                    "message": "Invalid credentials.json format. Expected 'web' section with 'client_id'."
                }
        except json.JSONDecodeError:
            return {
                "configured": False,
                "message": "credentials.json file is not valid JSON"
            }
    except Exception as e:
        return {
            "configured": False,
            "message": f"Error checking calendar configuration: {str(e)}"
        }

def create_flow():
    """Create and return a Google OAuth2 flow."""
    if not os.path.exists(GOOGLE_CLIENT_SECRETS_FILE):
        raise HTTPException(
            status_code=500, 
            detail=f"Google Calendar credentials file not found. Please create '{GOOGLE_CLIENT_SECRETS_FILE}' with your Google OAuth credentials."
        )
    
    try:
        return Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading Google Calendar credentials: {str(e)}"
        )

@router.get("/google/login")
async def google_login(doctor_id: int):
    """Start the OAuth2 flow for a specific doctor."""
    flow = create_flow()
    # Include doctor_id in the state parameter
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent screen to get refresh token
        state=str(doctor_id)  # Pass doctor_id as state
    )
    return RedirectResponse(authorization_url)

@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle the OAuth2 callback and store tokens."""
    # Get the authorization code and state (doctor_id)
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # This contains our doctor_id
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")
    
    try:
        doctor_id = int(state)
        print(f"🔍 OAuth callback for doctor ID: {doctor_id}")
        
        doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
        if not doctor:
            print(f"❌ Doctor with ID {doctor_id} not found")
            raise HTTPException(status_code=404, detail="Doctor not found")

        print(f"✅ Found doctor: {doctor.name}")

        # Complete the OAuth flow
        flow = create_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        print(f"🔑 Received credentials - Access token: {credentials.token[:20]}...")
        print(f"🔑 Refresh token: {credentials.refresh_token[:20] if credentials.refresh_token else 'None'}...")

        # Update doctor's Google Calendar credentials
        doctor.google_access_token = credentials.token
        doctor.google_refresh_token = credentials.refresh_token
        
        if credentials.expiry:
            doctor.token_expiry = datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc).date()
        
        print(f"💾 Saving credentials to database for {doctor.name}")
        db.commit()
        db.refresh(doctor)  # Refresh the doctor object to get updated data
        
        # Verify the credentials were saved
        print(f"✅ Verification - Access token saved: {bool(doctor.google_access_token)}")
        print(f"✅ Verification - Refresh token saved: {bool(doctor.google_refresh_token)}")

        return HTMLResponse("""
            <html>
                <body style="background-color: #1a1a1a; color: #ffffff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
                    <div style="text-align: center; padding: 20px; background-color: #2d2d2d; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.5);">
                        <h2 style="color: #4CAF50;">✅ Google Calendar Connected!</h2>
                        <p>""" + doctor.name + """'s calendar is now connected.</p>
                        <p>You can close this window and return to the application.</p>
                    </div>
                </body>
            </html>
        """)
    
    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def get_doctor_credentials(doctor: models.Doctor):
    """Get valid Google credentials for a doctor."""
    print(f"🔍 Checking credentials for {doctor.name} (ID: {doctor.id})")
    print(f"   - Access token exists: {bool(doctor.google_access_token)}")
    print(f"   - Refresh token exists: {bool(doctor.google_refresh_token)}")
    
    if not doctor.google_access_token and not doctor.google_refresh_token:
        print(f"❌ No credentials found for {doctor.name}")
        return None

    # Load client secrets
    import json
    try:
        with open(GOOGLE_CLIENT_SECRETS_FILE, 'r') as f:
            client_secrets = json.load(f)
    except FileNotFoundError:
        print(f"❌ Google Calendar credentials file not found: {GOOGLE_CLIENT_SECRETS_FILE}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in credentials file: {GOOGLE_CLIENT_SECRETS_FILE}")
        return None
    
    credentials = Credentials(
        token=doctor.google_access_token,
        refresh_token=doctor.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_secrets['web']['client_id'],
        client_secret=client_secrets['web']['client_secret'],
        scopes=SCOPES
    )
    
    # Check if credentials are expired and refresh if possible
    if not credentials.valid and credentials.refresh_token:
        try:
            print(f"🔄 Refreshing expired token for {doctor.name}")
            credentials.refresh(GoogleRequest())
            
            # Update the stored credentials
            doctor.google_access_token = credentials.token
            if credentials.refresh_token:  # Sometimes a new refresh token is issued
                doctor.google_refresh_token = credentials.refresh_token
            if credentials.expiry:
                doctor.token_expiry = datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc).date()
            
            print(f"✅ Successfully refreshed token for {doctor.name}")
            return credentials
            
        except Exception as e:
            print(f"❌ Failed to refresh token for {doctor.name}: {str(e)}")
            # Clear invalid credentials
            doctor.google_access_token = None
            doctor.google_refresh_token = None
            doctor.token_expiry = None
            return None
    
    return credentials if credentials.valid else None

async def create_calendar_event(doctor: models.Doctor, appointment_data: dict, db: Session, is_reschedule=False, is_cancellation=False):
    """Create, update or cancel a Google Calendar event for an appointment."""
    try:
        print(f"🗓️ Starting calendar operation for Dr. {doctor.name}")
        print(f"   - Operation: {'Reschedule' if is_reschedule else 'Cancel' if is_cancellation else 'Create'}")
        print(f"   - Patient: {appointment_data['patient_name']}")
        print(f"   - Date: {appointment_data['date']}")
        
        credentials = get_doctor_credentials(doctor)
        if not credentials:
            print(f"❌ No Google Calendar credentials found for doctor {doctor.name}")
            return False
        
        # Build the calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # For reschedules and cancellations, first find the existing event
        if is_reschedule or is_cancellation:
            # Search for events on the original date (for reschedules) or current date (for cancellations)
            search_date = appointment_data.get('old_date', appointment_data['date']) if is_reschedule else appointment_data['date']
            
            # Use patient name as the search term, but also search by appointment title
            search_queries = [
                appointment_data['patient_name'],
                f"Appointment - {appointment_data['patient_name']}",
                appointment_data['patient_name'].split()[0]  # First name only
            ]
            
            existing_event = None
            for search_query in search_queries:
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=f"{search_date}T00:00:00Z",
                    timeMax=f"{search_date}T23:59:59Z",
                    q=search_query
                ).execute()
                
                events = events_result.get('items', [])
                if events:
                    # Find the most likely match
                    for event in events:
                        event_title = event.get('summary', '')
                        event_description = event.get('description', '')
                        if (appointment_data['patient_name'].lower() in event_title.lower() or 
                            appointment_data['patient_name'].lower() in event_description.lower()):
                            existing_event = event
                            break
                    if existing_event:
                        break
            
            if not existing_event:
                print(f"⚠️ No matching calendar event found for {appointment_data['patient_name']} on {search_date}")
                if is_cancellation:
                    return True  # If we're cancelling and there's no event, that's fine
                # For reschedules, continue to create new event
            else:
                event_id = existing_event['id']
                print(f"✅ Found existing calendar event: {existing_event.get('summary', 'No title')}")
                
                if is_cancellation:
                    # Delete the event for cancellations
                    service.events().delete(calendarId='primary', eventId=event_id).execute()
                    print(f"✅ Calendar event deleted for {doctor.name}")
                    return True
        
        if not is_cancellation:  # Create/update event for new bookings and reschedules
            # Parse time slot
            time_parts = appointment_data["time_slot"].split("-")
            start_time = time_parts[0].strip()
            end_time = time_parts[1].strip() if len(time_parts) > 1 else start_time
            
            if len(start_time) == 5:  # "09:00" format
                start_time += ":00"
            if len(end_time) == 5:  # "09:30" format
                end_time += ":00"
            
            # Create event description
            description_parts = [
                f"Patient: {appointment_data['patient_name']}",
            ]
            
            if appointment_data.get('symptoms'):
                description_parts.append(f"Reason for visit: {appointment_data['symptoms']}")
            
            if appointment_data.get('notes'):
                description_parts.append(f"Additional notes: {appointment_data['notes']}")
            
            if is_reschedule:
                description_parts.append(f"\nRescheduled from: {appointment_data['old_date']} at {appointment_data['old_time']}")
            
            event = {
                'summary': f"Appointment - {appointment_data['patient_name']}",
                'description': '\n'.join(description_parts),
                'start': {
                    'dateTime': f"{appointment_data['date']}T{start_time}",
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': f"{appointment_data['date']}T{end_time}",
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},
                        {'method': 'email', 'minutes': 60},
                    ],
                },
                'colorId': '1',  # Blue for all active appointments
            }
            
            if is_reschedule and existing_event:
                # Update existing event
                service.events().update(
                    calendarId='primary',
                    eventId=event_id,
                    body=event
                ).execute()
                print(f"✅ Calendar event updated for {doctor.name}")
            else:
                # Create new event
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                print(f"✅ Calendar event created for {doctor.name}")
                print(f"   📅 Date: {appointment_data['date']} at {appointment_data['time_slot']}")
                print(f"   👤 Patient: {appointment_data['patient_name']}")
                print(f"   🔗 Event link: {created_event.get('htmlLink')}")
            
            return True
            
    except Exception as e:
        error_msg = str(e)
        if "invalid_grant" in error_msg and "expired or revoked" in error_msg:
            print(f"⚠️ Google Calendar token expired for {doctor.name} - appointment will still be saved")
            # Clear expired credentials
            doctor.google_access_token = None
            doctor.google_refresh_token = None
            doctor.token_expiry = None
            try:
                db.commit()
            except:
                pass  # Don't fail if we can't update the DB
        else:
            print(f"❌ Error managing calendar event for {doctor.name}: {error_msg}")
        import traceback
        traceback.print_exc()
        return False 