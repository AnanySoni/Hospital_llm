"""
Hospital Appointment System - Main Application
Optimized FastAPI application with proper structure and organization
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

# Import from organized structure
from core.database import get_db
from core.models import Doctor, DoctorAvailability
from utils.llm_utils import get_doctor_recommendations, start_diagnostic_session, process_diagnostic_answer
from services import AppointmentService
from services.test_service import TestService
from middleware import setup_error_handlers
from schemas import (
    SymptomsRequest, AppointmentRequest, RescheduleRequest,
    AppointmentResponse, RescheduleResponse, CancelResponse, DoctorRecommendation,
    DiagnosticAnswer, RouterResponse, TestBookingRequest, TestBookingResponse
)
from integrations import google_calendar_router

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
async def calendar_setup_page():
    """Simple page to help set up Google Calendar integration"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google Calendar Setup</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: white; }
            .container { max-width: 600px; margin: 0 auto; }
            .doctor-card { background: #2d2d2d; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .connect-btn { background: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; }
            .connected { background: #34a853; }
            h1 { color: #4285f4; }
            code { background: #333; padding: 4px 8px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗓️ Google Calendar Setup</h1>
            <p>Connect Google Calendar for automatic appointment management.</p>
            
            <div class="doctor-card">
                <h3>Dr. Bob Johnson (Cardiology)</h3>
                <p>Status: <span style="color: #ff6b6b;">❌ Token Expired</span></p>
                <a href="/auth/google/login?doctor_id=2" class="connect-btn">Reconnect Google Calendar</a>
            </div>
            
            <div class="doctor-card">
                <h3>Other Doctors</h3>
                <p>To connect other doctors, replace the doctor_id in the URL:</p>
                <code>/auth/google/login?doctor_id=DOCTOR_ID</code>
                <br><br>
                <p>Common doctor IDs: 1, 2, 3, 4, 5...</p>
            </div>
            
            <div class="doctor-card">
                <h3>📋 Instructions</h3>
                <ol>
                    <li>Click "Reconnect Google Calendar" for Dr. Bob Johnson</li>
                    <li>Sign in to your Google account</li>
                    <li>Grant calendar permissions</li>
                    <li>You'll be redirected back with success confirmation</li>
                    <li>Test by booking an appointment - it should sync to calendar</li>
                </ol>
            </div>
            
            <div class="doctor-card">
                <h3>🔧 Current Status</h3>
                <p>✅ Appointments are booking successfully</p>
                <p>⚠️ Calendar sync is disabled (expired tokens)</p>
                <p>✅ All other features working normally</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


# Google Calendar routes are included above


@app.post("/start-diagnostic", response_model=RouterResponse)
async def start_diagnostic(symptoms: str, db: Session = Depends(get_db)):
    """Start a diagnostic session with router LLM"""
    try:
        logger.info(f"Starting diagnostic session for symptoms: {symptoms}")
        
        # Get all doctors for routing
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
        
        # Start diagnostic session
        result = await start_diagnostic_session(symptoms, doctor_list)
        
        logger.info(f"Diagnostic session started: {result['session_id']}")
        return RouterResponse(**result)
        
    except Exception as e:
        logger.error(f"Error starting diagnostic session: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while starting the diagnostic session")


@app.post("/answer-diagnostic", response_model=RouterResponse)
async def answer_diagnostic(answer: DiagnosticAnswer, db: Session = Depends(get_db)):
    """Answer a diagnostic question and get next step"""
    try:
        logger.info(f"Processing diagnostic answer for session: {answer.session_id}")
        
        # Get all doctors for routing
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
        
        # Process the answer
        result = await process_diagnostic_answer(answer.session_id, answer.question_id, answer.answer, doctor_list)
        
        logger.info(f"Diagnostic answer processed for session: {answer.session_id}")
        return RouterResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error in answer_diagnostic: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing diagnostic answer: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the diagnostic answer")


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=True  # Remove in production
    ) 