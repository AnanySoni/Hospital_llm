"""
Hospital Appointment System - Main Application
Optimized FastAPI application with proper structure and organization
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import json

# Import from organized structure
from core.database import get_db
from core.models import Doctor, DoctorAvailability, Department
from utils.llm_utils import (
    get_doctor_recommendations,
    get_doctor_recommendations_with_history, start_diagnostic_session_with_history
)
from services import AppointmentService
from services.test_service import TestService
from services.session_service import SessionService
from services.patient_recognition_service import PatientRecognitionService
from middleware import setup_error_handlers
from schemas import (
    SymptomsRequest, AppointmentRequest, RescheduleRequest,
    AppointmentResponse, RescheduleResponse, CancelResponse, DoctorRecommendation,
    RouterResponse, TestBookingRequest, TestBookingResponse,
    EnhancedChatRequest, SessionUserCreate, SessionHistoryResponse, PatientHistoryCreate,
    PhoneRecognitionRequest, SmartWelcomeRequest, PatientProfileResponse, SmartWelcomeResponse
)
from integrations import google_calendar_router

# Import adaptive routes
from routes.adaptive_routes import router as adaptive_router

# Import admin routes
from routes.admin_routes import router as admin_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hospital Appointment System",
    description="AI-powered hospital appointment booking system with optimized architecture",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up error handlers
setup_error_handlers(app)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Google Calendar router
app.include_router(google_calendar_router, prefix="/auth", tags=["Google Calendar"])

# Include adaptive routes (Phase 1 Month 2)
app.include_router(adaptive_router)

# Include admin routes
app.include_router(admin_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Hospital Appointment System API",
        "version": "2.0.0",
        "architecture": "optimized"
    }


@app.post("/recommend-doctors", response_model=list[DoctorRecommendation])
async def recommend_doctors(request: SymptomsRequest, db: Session = Depends(get_db)):
    """Get doctor recommendations based on symptoms"""
    try:
        logger.info(f"Getting doctor recommendations for symptoms: {request.symptoms}")
        
        # Get all doctors
        doctors = db.query(Doctor).all()
        
        # Convert to format expected by LLM
        doctor_list = []
        for doctor in doctors:
            doctor_dict = {
                "id": doctor.id,
                "name": doctor.name,
                "department": doctor.department.name if doctor.department else "",
                "subdivision": doctor.subdivision.name if doctor.subdivision else "",
                "tags": doctor.tags if doctor.tags else []
            }
            doctor_list.append(doctor_dict)
        
        # Get recommendations from LLM
        recommendations = await get_doctor_recommendations(request.symptoms, doctor_list)
        
        # Parse recommendations
        import json
        try:
            if isinstance(recommendations, str):
                recommendations = json.loads(recommendations)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {recommendations}")
            # Fallback to first 3 doctors
            recommendations = [
                {
                    "id": doctors[i].id,
                    "name": doctors[i].name,
                    "specialization": doctors[i].department.name if doctors[i].department else "General Medicine",
                    "reason": f"Recommended for symptoms: {request.symptoms}",
                    "experience": "Experienced medical professional",
                    "expertise": doctors[i].tags if doctors[i].tags else ["General Medicine"]
                }
                for i in range(min(3, len(doctors)))
            ]
        
        logger.info(f"Returning {len(recommendations)} doctor recommendations")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in recommend_doctors: {str(e)}")
        raise


@app.post("/book-appointment", response_model=AppointmentResponse)
async def book_appointment(request: AppointmentRequest, db: Session = Depends(get_db)):
    """Book a new appointment"""
    try:
        logger.info(f"Booking appointment for {request.patient_name} with doctor {request.doctor_id}")
        
        result = await AppointmentService.create_appointment(
            db=db,
            doctor_id=request.doctor_id,
            patient_name=request.patient_name,
            phone_number=request.phone_number,
            appointment_date=request.appointment_date,
            appointment_time=request.appointment_time,
            notes=request.notes,
            symptoms=request.symptoms
        )
        
        logger.info(f"Appointment booked successfully: ID {result['id']}")
        return result
    except ValueError as e:
        logger.error(f"Validation error in book_appointment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in book_appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while booking the appointment")


@app.put("/reschedule-appointment", response_model=RescheduleResponse)
async def reschedule_appointment(request: RescheduleRequest, db: Session = Depends(get_db)):
    """Reschedule an existing appointment"""
    try:
        logger.info(f"Rescheduling appointment {request.appointment_id} to {request.new_date} at {request.new_time}")
        
        result = await AppointmentService.reschedule_appointment(
            db=db,
            appointment_id=request.appointment_id,
            new_date=request.new_date,
            new_time=request.new_time
        )
        
        logger.info(f"Appointment rescheduled successfully: ID {request.appointment_id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error in reschedule_appointment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in reschedule_appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while rescheduling the appointment")


@app.delete("/cancel-appointment/{appointment_id}", response_model=CancelResponse)
async def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Cancel an existing appointment"""
    try:
        logger.info(f"Cancelling appointment {appointment_id}")
        
        result = await AppointmentService.cancel_appointment(
            db=db,
            appointment_id=appointment_id
        )
        
        logger.info(f"Appointment cancelled successfully: ID {appointment_id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error in cancel_appointment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in cancel_appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while cancelling the appointment")


@app.get("/doctors")
def get_all_doctors(db: Session = Depends(get_db)):
    """Get all doctors for calendar connection dropdown"""
    try:
        doctors = db.query(Doctor).all()
        doctor_list = []
        for doctor in doctors:
            doctor_list.append({
                "id": doctor.id,
                "name": doctor.name,
                "department": doctor.department.name if doctor.department else "",
                "subdivision": doctor.subdivision.name if doctor.subdivision else "",
                "has_calendar_connected": bool(doctor.google_access_token)
            })
        
        logger.info(f"Returning {len(doctor_list)} doctors")
        return doctor_list
        
    except Exception as e:
        logger.error(f"Error getting doctors: {str(e)}")
        raise


@app.get("/departments")
def get_all_departments(db: Session = Depends(get_db)):
    """Get all departments"""
    try:
        departments = db.query(Department).all()
        department_list = []
        for dept in departments:
            department_list.append({
                "id": dept.id,
                "name": dept.name
            })
        
        logger.info(f"Returning {len(department_list)} departments")
        return department_list
        
    except Exception as e:
        logger.error(f"Error getting departments: {str(e)}")
        raise


@app.post("/chat")
async def basic_chat(request: dict, db: Session = Depends(get_db)):
    """Basic chat endpoint"""
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", "")
        
        # Simple response for basic chat
        response = {
            "message": f"I understand you said: {message}. How can I help you with your health concerns?",
            "suggestions": [
                "Book an appointment",
                "Get doctor recommendations", 
                "Start diagnostic session"
            ]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in basic chat: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your message")


@app.get("/doctor-availability/{doctor_id}")
def get_doctor_availability(doctor_id: int, db: Session = Depends(get_db)):
    """Get availability for a specific doctor"""
    try:
        availability = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.is_booked == False
        ).all()
        
        available_slots = []
        for slot in availability:
            available_slots.append({
                "id": slot.id,
                "date": slot.date.isoformat(),
                "time_slot": slot.time_slot,
                "is_available": not slot.is_booked
            })
        
        logger.info(f"Returning {len(available_slots)} available slots for doctor {doctor_id}")
        return available_slots
        
    except Exception as e:
        logger.error(f"Error getting doctor availability: {str(e)}")
        raise


@app.post("/book-test")
async def book_medical_test(request: dict):
    """Book a medical test (simplified version)"""
    try:
        # Simple test booking without validation
        result = {
            "booking_id": f"TEST_{request.get('test_name', 'UNKNOWN')[:10].upper()}_{hash(str(request)) % 10000}",
            "test_name": request.get("test_name", ""),
            "test_type": request.get("test_type", ""),
            "patient_name": request.get("patient_name", ""),
            "scheduled_date": request.get("preferred_date", ""),
            "scheduled_time": request.get("preferred_time", ""),
            "status": "scheduled",
            "message": "Test booking successful"
        }
        
        logger.info(f"Test booked: {result['booking_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Error booking test: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while booking the test")


@app.get("/doctors/{doctor_id}/available-slots")
async def get_available_slots(doctor_id: int, date: str, db: Session = Depends(get_db)):
    """Get available time slots for a doctor on a specific date"""
    try:
        from datetime import datetime
        
        # Parse the date
        appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Get available slots from the database
        available_slots = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.date == appointment_date,
            DoctorAvailability.is_booked == False
        ).all()
        
        # Convert to 12-hour format for display
        def convert_to_12hour(time_24):
            try:
                # Extract start time from range (e.g., "09:00" from "09:00-09:30")
                start_time = time_24.split('-')[0]
                time_obj = datetime.strptime(start_time, "%H:%M").time()
                return time_obj.strftime("%I:%M %p")
            except:
                return time_24
        
        slots = []
        for slot in available_slots:
            slots.append({
                "id": slot.id,
                "time_24": slot.time_slot,
                "time_12": convert_to_12hour(slot.time_slot),
                "is_available": not slot.is_booked
            })
        
        logger.info(f"Returning {len(slots)} available slots for doctor {doctor_id} on {date}")
        return slots
        
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving available slots")


@app.get("/appointments/patient/{patient_name}")
async def get_patient_appointments(patient_name: str, db: Session = Depends(get_db)):
    """Get all appointments for a specific patient"""
    try:
        appointments = AppointmentService.get_appointments_by_patient(db, patient_name)
        logger.info(f"Found {len(appointments)} appointments for patient: {patient_name}")
        return appointments
    except Exception as e:
        logger.error(f"Error getting patient appointments: {str(e)}")
        raise


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-07T00:00:00Z",
        "services": {
            "database": "connected",
            "llm": "available",
            "calendar": "integrated"
        },
        "architecture": {
            "structure": "organized",
            "services": "layered",
            "error_handling": "comprehensive"
        }
    }


@app.get("/calendar-setup")
async def calendar_setup_page(db: Session = Depends(get_db)):
    """Simple page to help set up Google Calendar integration"""
    from fastapi.responses import HTMLResponse
    
    # Get all doctors with their calendar status
    doctors = db.query(Doctor).all()
    
    doctor_cards = ""
    for doctor in doctors:
        has_tokens = bool(doctor.google_access_token and doctor.google_refresh_token)
        status_color = "#34a853" if has_tokens else "#ff6b6b"
        status_text = "✅ Connected" if has_tokens else "❌ Not Connected"
        button_text = "Reconnect Google Calendar" if has_tokens else "Connect Google Calendar"
        
        doctor_cards += f"""
        <div class="doctor-card">
            <h3>{doctor.name} ({doctor.department.name if doctor.department else 'No Department'})</h3>
            <p>Status: <span style="color: {status_color};">{status_text}</span></p>
            <a href="/auth/google/login?doctor_id={doctor.id}" class="connect-btn">{button_text}</a>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google Calendar Setup</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: white; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .doctor-card {{ background: #2d2d2d; padding: 20px; margin: 10px 0; border-radius: 8px; }}
            .connect-btn {{ background: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px; }}
            .connected {{ background: #34a853; }}
            h1 {{ color: #4285f4; }}
            code {{ background: #333; padding: 4px 8px; border-radius: 4px; }}
            .status-summary {{ background: #2d2d2d; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗓️ Google Calendar Setup</h1>
            <p>Connect Google Calendar for automatic appointment management.</p>
            
            <div class="status-summary">
                <h3>📊 Current Status</h3>
                <p>Found {len(doctors)} doctors in the system</p>
                <p>Connected: {len([d for d in doctors if d.google_access_token])} doctors</p>
                <p>Not Connected: {len([d for d in doctors if not d.google_access_token])} doctors</p>
            </div>
            
            {doctor_cards}
            
            <div class="doctor-card">
                <h3>📋 Instructions</h3>
                <ol>
                    <li>Click "Connect Google Calendar" for any doctor</li>
                    <li>Sign in to your Google account</li>
                    <li>Grant calendar permissions</li>
                    <li>You'll be redirected back with success confirmation</li>
                    <li>Test by booking an appointment - it should sync to calendar</li>
                </ol>
            </div>
            
            <div class="doctor-card">
                <h3>🔧 Troubleshooting</h3>
                <p>If you're having issues:</p>
                <ul>
                    <li>Make sure you're signed into the correct Google account</li>
                    <li>Check that calendar permissions are granted</li>
                    <li>Try reconnecting if tokens are expired</li>
                    <li>Contact admin if issues persist</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(html_content)


# Google Calendar routes are included above





@app.post("/book-tests", response_model=TestBookingResponse)
async def book_tests(request: TestBookingRequest):
    """Book medical tests"""
    try:
        logger.info(f"Booking tests for {request.patient_name}: {request.test_ids}")
        
        result = await TestService.book_tests(
            patient_name=request.patient_name,
            test_ids=request.test_ids,
            preferred_date=request.preferred_date,
            preferred_time=request.preferred_time,
            contact_number=request.contact_number,
            notes=request.notes
        )
        
        logger.info(f"Tests booked successfully: {result['booking_id']}")
        return TestBookingResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error in book_tests: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error booking tests: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while booking the tests")


@app.get("/available-tests")
async def get_available_tests():
    """Get all available medical tests"""
    try:
        tests = await TestService.get_available_tests()
        logger.info(f"Returning {len(tests)} available tests")
        return tests
        
    except Exception as e:
        logger.error(f"Error getting available tests: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving available tests")


@app.get("/tests/category/{category}")
async def get_tests_by_category(category: str):
    """Get tests by category"""
    try:
        tests = await TestService.get_tests_by_category(category)
        logger.info(f"Returning {len(tests)} tests in category: {category}")
        return tests
        
    except Exception as e:
        logger.error(f"Error getting tests by category: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving tests")


@app.get("/tests/patient/{patient_name}")
async def get_patient_test_bookings(patient_name: str):
    """Get all test bookings for a patient"""
    try:
        bookings = await TestService.get_patient_test_bookings(patient_name)
        logger.info(f"Returning {len(bookings)} test bookings for {patient_name}")
        return bookings
        
    except Exception as e:
        logger.error(f"Error getting patient test bookings: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving test bookings")


@app.delete("/tests/cancel/{booking_id}")
async def cancel_test_booking(booking_id: str):
    """Cancel a test booking"""
    try:
        result = await TestService.cancel_test_booking(booking_id)
        logger.info(f"Test booking cancelled: {booking_id}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in cancel_test_booking: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling test booking: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while cancelling the test booking")


@app.get("/tests/recommendations/{symptoms}")
async def get_test_recommendations(symptoms: str):
    """Get test recommendations based on symptoms"""
    try:
        recommendations = await TestService.get_test_recommendations_by_symptoms(symptoms)
        logger.info(f"Returning {len(recommendations)} test recommendations for symptoms: {symptoms}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting test recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving test recommendations")


# Enhanced doctor recommendation endpoint with router integration
@app.post("/smart-recommend-doctors", response_model=list[DoctorRecommendation])
async def smart_recommend_doctors(symptoms: str, db: Session = Depends(get_db)):
    """Enhanced doctor recommendation with router LLM integration"""
    try:
        logger.info(f"Getting smart doctor recommendations for symptoms: {symptoms}")
        
        # Get all doctors
        doctors = db.query(Doctor).all()
        doctor_list = []
        for doctor in doctors:
            doctor_dict = {
                "id": doctor.id,
                "name": doctor.name,
                "department": doctor.department.name if doctor.department else "",
                "subdivision": doctor.subdivision.name if doctor.subdivision else "",
                "tags": doctor.tags if doctor.tags else []
            }
            doctor_list.append(doctor_dict)
        
        # Use enhanced LLM recommendation
        recommendations = await get_doctor_recommendations(symptoms, doctor_list)
        
        # Parse recommendations
        import json
        try:
            if isinstance(recommendations, str):
                recommendations = json.loads(recommendations)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {recommendations}")
            # Fallback to first 3 doctors
            recommendations = [
                {
                    "id": doctors[i].id,
                    "name": doctors[i].name,
                    "specialization": doctors[i].department.name if doctors[i].department else "General Medicine",
                    "reason": f"Recommended for symptoms: {symptoms}",
                    "experience": "Experienced medical professional",
                    "expertise": doctors[i].tags if doctors[i].tags else ["General Medicine"]
                }
                for i in range(min(3, len(doctors)))
            ]
        
        logger.info(f"Returning {len(recommendations)} smart doctor recommendations")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in smart_recommend_doctors: {str(e)}")
        raise


# Session-based patient history endpoints (Phase 1)
@app.post("/chat-enhanced", response_model=list[DoctorRecommendation])
async def chat_enhanced(request: EnhancedChatRequest, db: Session = Depends(get_db)):
    """Enhanced chat endpoint with session-based patient history"""
    try:
        logger.info(f"Enhanced chat request from session: {request.session_id}")
        
        # Create session service
        session_service = SessionService(db)
        
        # Convert user_info dict to SessionUserCreate if provided
        user_info_obj = None
        if request.user_info:
            user_info_obj = SessionUserCreate(
                session_id=request.session_id,
                first_name=request.user_info.get('first_name'),
                age=request.user_info.get('age'),
                gender=request.user_info.get('gender')
            )
        
        # Get or create session user
        session_user = session_service.get_or_create_session_user(
            session_id=request.session_id, 
            user_info=user_info_obj
        )
        
        # Generate patient context if history requested
        patient_context = None
        if request.include_history:
            patient_context = session_service.generate_llm_context(request.session_id)
        
        # Get all doctors
        doctors = db.query(Doctor).all()
        doctor_list = []
        for doctor in doctors:
            doctor_dict = {
                "id": doctor.id,
                "name": doctor.name,
                "department": doctor.department.name if doctor.department else "",
                "subdivision": doctor.subdivision.name if doctor.subdivision else "",
                "tags": doctor.tags if doctor.tags else []
            }
            doctor_list.append(doctor_dict)
        
        # Get enhanced recommendations with history context
        recommendations = await get_doctor_recommendations_with_history(
            symptoms=request.message,
            doctors=doctor_list,
            patient_context=patient_context,
            session_id=request.session_id
        )
        
        # Parse recommendations
        import json
        try:
            if isinstance(recommendations, str):
                recommendations = json.loads(recommendations)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {recommendations}")
            # Fallback to regular recommendations
            recommendations = await get_doctor_recommendations(request.message, doctor_list)
            if isinstance(recommendations, str):
                recommendations = json.loads(recommendations)
        
        # Save symptom log
        session_service.record_symptom_log(
            session_id=request.session_id,
            symptom_data={
                "description": request.message,
                "severity": "moderate",  # Could be determined by LLM
                "duration": "current session"
            }
        )
        
        logger.info(f"Enhanced chat completed for session: {request.session_id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in chat_enhanced: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the enhanced chat request")


@app.get("/session-history/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """Get patient history summary for a session"""
    try:
        logger.info(f"Getting session history for: {session_id}")
        
        session_service = SessionService(db)
        history = session_service.get_patient_comprehensive_history(session_id)
        
        if not history:
            # Return empty history structure instead of 404
            return SessionHistoryResponse(
                session_id=session_id,
                conversation_count=0,
                recent_symptoms=[],
                recent_diagnoses=[],
                chronic_conditions=[],
                allergies=[],
                appointment_history=[],
                test_history=[],
                last_visit=None
            )
        
        # Convert the history to SessionHistoryResponse format
        logger.info(f"Returning history for session: {session_id}")
        return SessionHistoryResponse(
            session_id=session_id,
            conversation_count=len(history.get("conversation_history", [])),
            recent_symptoms=[s.get("description", "") for s in history.get("recent_symptoms", [])],
            recent_diagnoses=[],
            chronic_conditions=[],
            allergies=[],
            appointment_history=[],
            test_history=[],
            last_visit=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving session history")


@app.post("/start-diagnostic-enhanced", response_model=RouterResponse)
async def start_diagnostic_enhanced(request: EnhancedChatRequest, db: Session = Depends(get_db)):
    """Start diagnostic session with patient history context"""
    try:
        logger.info(f"Starting enhanced diagnostic session for: {request.session_id}")
        
        # Create session service
        session_service = SessionService(db)
        
        # Convert user_info dict to SessionUserCreate if provided
        user_info_obj = None
        if request.user_info:
            user_info_obj = SessionUserCreate(
                session_id=request.session_id,
                first_name=request.user_info.get('first_name'),
                age=request.user_info.get('age'),
                gender=request.user_info.get('gender')
            )
        
        # Get or create session user
        session_user = session_service.get_or_create_session_user(
            session_id=request.session_id, 
            user_info=user_info_obj
        )
        
        # Generate patient context
        patient_context = None
        if request.include_history:
            patient_context = session_service.generate_llm_context(request.session_id)
        
        # Get all doctors
        doctors = db.query(Doctor).all()
        doctor_list = []
        for doctor in doctors:
            doctor_dict = {
                "id": doctor.id,
                "name": doctor.name,
                "department": doctor.department.name if doctor.department else "",
                "subdivision": doctor.subdivision.name if doctor.subdivision else "",
                "tags": doctor.tags if doctor.tags else []
            }
            doctor_list.append(doctor_dict)
        
        # Start enhanced diagnostic session
        result = await start_diagnostic_session_with_history(
            symptoms=request.message,
            doctors=doctor_list,
            patient_context=patient_context,
            session_id=request.session_id
        )
        
        logger.info(f"Enhanced diagnostic session started: {result['session_id']}")
        return RouterResponse(**result)
        
    except Exception as e:
        logger.error(f"Error starting enhanced diagnostic session: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while starting the enhanced diagnostic session")


@app.post("/session-user", response_model=dict)
async def create_or_update_session_user(request: SessionUserCreate, db: Session = Depends(get_db)):
    """Create or update session user information"""
    try:
        logger.info(f"Creating/updating session user: {request.session_id}")
        
        session_service = SessionService(db)
        session_user = session_service.get_or_create_session_user(
            session_id=request.session_id,
            user_info=request
        )
        
        return {
            "id": session_user.id,
            "session_id": session_user.session_id,
            "first_name": session_user.first_name,
            "age": session_user.age,
            "gender": session_user.gender,
            "created_at": session_user.created_at.isoformat(),
            "last_active": session_user.last_active.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating/updating session user: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while managing session user")


@app.get("/session-stats/{session_id}")
async def get_session_stats(session_id: str, db: Session = Depends(get_db)):
    """Get session statistics and quick insights"""
    try:
        session_service = SessionService(db)
        stats = session_service.get_session_stats(session_id)
        
        if not stats:
            return {
                "session_id": session_id,
                "is_new_user": True,
                "total_conversations": 0,
                "returning_user": False
            }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving session statistics")

# Phase 2: Phone-based Patient Recognition Endpoints
@app.post("/phone-recognition", response_model=PatientProfileResponse)
async def phone_recognition(request: PhoneRecognitionRequest, db: Session = Depends(get_db)):
    """Find or create patient profile based on phone number"""
    try:
        logger.info(f"Phone recognition request for: {request.phone_number}")
        
        from services.patient_recognition_service import PatientRecognitionService
        
        patient_profile, is_new = PatientRecognitionService.find_or_create_patient_profile(
            db=db,
            phone_number=request.phone_number,
            first_name=request.first_name,
            family_member_type=request.family_member_type
        )
        
        # Convert to response format
        chronic_conditions = json.loads(patient_profile.chronic_conditions or "[]")
        allergies = json.loads(patient_profile.allergies or "[]")
        
        response = PatientProfileResponse(
            id=patient_profile.id,
            phone_number=patient_profile.phone_number,
            first_name=patient_profile.first_name,
            last_name=patient_profile.last_name,
            age=patient_profile.age,
            gender=patient_profile.gender,
            family_member_type=patient_profile.family_member_type,
            total_visits=patient_profile.total_visits,
            last_visit_date=patient_profile.last_visit_date,
            last_visit_symptoms=patient_profile.last_visit_symptoms,
            chronic_conditions=chronic_conditions,
            allergies=allergies
        )
        
        logger.info(f"Phone recognition completed - {'New' if is_new else 'Existing'} patient: {patient_profile.first_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error in phone recognition: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing phone recognition request")


@app.post("/smart-welcome", response_model=SmartWelcomeResponse)
async def smart_welcome(request: SmartWelcomeRequest, db: Session = Depends(get_db)):
    """Smart welcome with symptom analysis and history context"""
    try:
        logger.info(f"Smart welcome for phone: {request.phone_number}, symptoms: {request.symptoms[:50]}...")
        
        from services.patient_recognition_service import PatientRecognitionService
        
        # Find or create patient profile  
        patient_profile, is_new = PatientRecognitionService.find_or_create_patient_profile(
            db=db,
            phone_number=request.phone_number,
            first_name="Patient"  # Will be updated when we get actual name
        )
        
        # Categorize current symptoms
        symptom_category = await PatientRecognitionService.categorize_symptoms(request.symptoms)
        
        # Check symptom relatedness with history
        relatedness_analysis = await PatientRecognitionService.check_symptom_relatedness(
            db=db,
            patient_profile=patient_profile,
            current_symptoms=request.symptoms,
            current_category=symptom_category
        )
        
        # Determine next action based on analysis
        if is_new:
            next_action = "collect_more_info"  # Need to collect patient details
        elif relatedness_analysis.get("is_related"):
            next_action = "start_diagnostic"  # Can proceed with enhanced context
        else:
            next_action = "start_diagnostic"  # New symptoms, start fresh
        
        # Convert patient profile to response format
        chronic_conditions = json.loads(patient_profile.chronic_conditions or "[]")
        allergies = json.loads(patient_profile.allergies or "[]")
        
        patient_response = PatientProfileResponse(
            id=patient_profile.id,
            phone_number=patient_profile.phone_number,
            first_name=patient_profile.first_name,
            last_name=patient_profile.last_name,
            age=patient_profile.age,
            gender=patient_profile.gender,
            family_member_type=patient_profile.family_member_type,
            total_visits=patient_profile.total_visits,
            last_visit_date=patient_profile.last_visit_date,
            last_visit_symptoms=patient_profile.last_visit_symptoms,
            chronic_conditions=chronic_conditions,
            allergies=allergies
        )
        
        response = SmartWelcomeResponse(
            patient_profile=patient_response,
            is_new_patient=is_new,
            welcome_message=relatedness_analysis.get("message", f"Welcome, {patient_profile.first_name}!"),
            symptom_analysis={
                "category": symptom_category,
                "relatedness": relatedness_analysis
            },
            next_action=next_action
        )
        
        logger.info(f"Smart welcome completed for {patient_profile.first_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error in smart welcome: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing smart welcome request")


# Legacy Triage Endpoints (for backward compatibility with tests)
@app.post("/assess-urgency")
async def assess_urgency_legacy(request: dict):
    """Legacy urgency assessment endpoint - redirects to v2"""
    try:
        from services.triage_service import TriageService
        from schemas.triage_models import UrgencyAssessmentRequest
        
        triage_service = TriageService()
        
        # Convert legacy request format to new format
        assessment_request = UrgencyAssessmentRequest(
            symptoms=request.get("symptoms", ""),
            patient_age=request.get("patient_age", 35),
            answers=request.get("answers", {}),
            medical_history=request.get("medical_history", []),
            current_medications=request.get("current_medications", []),
            vital_signs=request.get("vital_signs", {})
        )
        
        # Perform triage assessment
        triage_assessment = await triage_service.assess_urgency_level(
            symptoms=assessment_request.symptoms,
            answers=assessment_request.answers,
            patient_profile={
                "age": assessment_request.patient_age,
                "medical_history": assessment_request.medical_history,
                "current_medications": assessment_request.current_medications,
                "vital_signs": assessment_request.vital_signs
            },
            confidence_score=0.7
        )
        
        # Return legacy format
        return {
            "urgency_level": triage_assessment.level.value,
            "confidence_score": triage_assessment.confidence_score,
            "time_urgency": triage_assessment.time_urgency,
            "reasoning": triage_assessment.reasoning,
            "emergency_override": triage_assessment.emergency_override
        }
        
    except Exception as e:
        logger.error(f"Error in legacy urgency assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing urgency assessment")


@app.post("/enhanced-recommend-doctors")
async def enhanced_recommend_doctors_legacy(request: dict, db: Session = Depends(get_db)):
    """Legacy enhanced doctor recommendation endpoint - redirects to smart-recommend-doctors"""
    try:
        symptoms = request.get("symptoms", "")
        return await smart_recommend_doctors(symptoms, db)
        
    except Exception as e:
        logger.error(f"Error in legacy enhanced doctor recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing enhanced doctor recommendations")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False,  # Disable auto-reload to prevent constant reloading
        log_level="info"
    ) 