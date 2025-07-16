"""
Doctor Management Service
Handles doctor CRUD operations, bulk upload, and email invitations
"""

import csv
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from datetime import datetime

from core.models import Doctor, Department, AdminUser, Hospital
from schemas.admin_models import (
    DoctorCreateRequest, DoctorUpdateRequest, DoctorResponse,
    BulkUploadResponse, BulkUploadResult, EmailInvitationResponse
)

class DoctorService:
    """Service class for doctor management operations"""
    
    @staticmethod
    def create_doctor(db: Session, doctor_data: DoctorCreateRequest, hospital_id: int, created_by: AdminUser) -> Doctor:
        """Create a new doctor"""
        # Check if email already exists
        existing_doctor = db.query(Doctor).filter_by(email=doctor_data.email).first()
        if existing_doctor:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create doctor
        doctor = Doctor(
            hospital_id=hospital_id,
            name=doctor_data.name,
            email=doctor_data.email,
            phone_number=doctor_data.phone,
            profile=f"{doctor_data.specialization} with {doctor_data.experience_years} years experience",
            tags=doctor_data.languages,
            # Additional fields would be added to the Doctor model
        )
        
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        
        return doctor
    
    @staticmethod
    def update_doctor(db: Session, doctor_id: int, doctor_data: DoctorUpdateRequest, updated_by: AdminUser) -> Doctor:
        """Update an existing doctor"""
        doctor = db.query(Doctor).filter_by(id=doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Update fields
        if doctor_data.name is not None:
            doctor.name = doctor_data.name
        if doctor_data.email is not None:
            doctor.email = doctor_data.email
        if doctor_data.phone is not None:
            doctor.phone_number = doctor_data.phone
        if doctor_data.specialization is not None:
            doctor.profile = f"{doctor_data.specialization} with {doctor_data.experience_years or 0} years experience"
        if doctor_data.languages is not None:
            doctor.tags = doctor_data.languages
        
        db.commit()
        db.refresh(doctor)
        
        return doctor
    
    @staticmethod
    def delete_doctor(db: Session, doctor_id: int, deleted_by: AdminUser) -> bool:
        """Delete a doctor"""
        doctor = db.query(Doctor).filter_by(id=doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        db.delete(doctor)
        db.commit()
        
        return True
    
    @staticmethod
    def get_doctor(db: Session, doctor_id: int) -> Doctor:
        """Get a single doctor by ID"""
        doctor = db.query(Doctor).filter_by(id=doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        return doctor
    
    @staticmethod
    def get_doctors(db: Session, hospital_id: int, skip: int = 0, limit: int = 100, search: str = None) -> List[Doctor]:
        """Get all doctors for a hospital"""
        query = db.query(Doctor).filter_by(hospital_id=hospital_id)
        
        if search:
            query = query.filter(
                (Doctor.name.ilike(f"%{search}%")) |
                (Doctor.email.ilike(f"%{search}%"))
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def bulk_upload_doctors(db: Session, file: UploadFile, hospital_id: int, created_by: AdminUser) -> BulkUploadResponse:
        """Bulk upload doctors from CSV file"""
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = file.file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        results = []
        successful = 0
        failed = 0
        warnings = 0
        
        required_fields = ['name', 'email', 'specialization', 'department', 'experience_years', 'qualification', 'consultation_fee']
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 to account for header
            result = BulkUploadResult(
                row_number=row_num,
                status='success',
                message='',
                errors=[]
            )
            
            try:
                # Validate required fields
                missing_fields = [field for field in required_fields if not row.get(field)]
                if missing_fields:
                    result.status = 'error'
                    result.message = f"Missing required fields: {', '.join(missing_fields)}"
                    result.errors = missing_fields
                    failed += 1
                    results.append(result)
                    continue
                
                # Check if email already exists
                existing_doctor = db.query(Doctor).filter_by(email=row['email']).first()
                if existing_doctor:
                    result.status = 'error'
                    result.message = f"Email {row['email']} already exists"
                    result.errors = ['duplicate_email']
                    failed += 1
                    results.append(result)
                    continue
                
                # Create doctor
                doctor_data = DoctorCreateRequest(
                    name=row['name'],
                    email=row['email'],
                    phone=row.get('phone', ''),
                    specialization=row['specialization'],
                    department=row['department'],
                    experience_years=int(row['experience_years']),
                    qualification=row['qualification'],
                    consultation_fee=float(row['consultation_fee']),
                    languages=row.get('languages', '').split(',') if row.get('languages') else []
                )
                
                doctor = DoctorService.create_doctor(db, doctor_data, hospital_id, created_by)
                
                result.doctor_id = doctor.id
                result.doctor_name = doctor.name
                result.message = f"Doctor {doctor.name} created successfully"
                successful += 1
                
            except ValueError as e:
                result.status = 'error'
                result.message = f"Invalid data format: {str(e)}"
                result.errors = ['invalid_format']
                failed += 1
            except Exception as e:
                result.status = 'error'
                result.message = f"Error creating doctor: {str(e)}"
                result.errors = ['creation_error']
                failed += 1
            
            results.append(result)
        
        total_rows = len(results)
        summary = f"Processed {total_rows} rows: {successful} successful, {failed} failed, {warnings} warnings"
        
        return BulkUploadResponse(
            total_rows=total_rows,
            successful=successful,
            failed=failed,
            warnings=warnings,
            results=results,
            summary=summary
        )
    
    @staticmethod
    def send_email_invitations(db: Session, doctor_ids: List[int], message: str = None, admin_user: AdminUser = None) -> EmailInvitationResponse:
        """Send email invitations to doctors"""
        from services.email_service import EmailService
        
        sent = 0
        failed = 0
        results = []
        
        # Get hospital info
        hospital = db.query(Hospital).filter_by(id=admin_user.hospital_id).first() if admin_user else None
        
        for doctor_id in doctor_ids:
            try:
                doctor = db.query(Doctor).filter_by(id=doctor_id).first()
                if not doctor:
                    results.append({
                        'doctor_id': doctor_id,
                        'status': 'error',
                        'message': 'Doctor not found'
                    })
                    failed += 1
                    continue
                
                # Send email using EmailService
                if hospital and admin_user:
                    success = EmailService.send_doctor_invitation(doctor, hospital, admin_user, message)
                else:
                    # Fallback to mock implementation
                    success = DoctorService._send_invitation_email(doctor, message)
                
                if success:
                    results.append({
                        'doctor_id': doctor_id,
                        'doctor_name': doctor.name,
                        'email': doctor.email,
                        'status': 'sent',
                        'message': 'Invitation sent successfully'
                    })
                    sent += 1
                else:
                    results.append({
                        'doctor_id': doctor_id,
                        'doctor_name': doctor.name,
                        'email': doctor.email,
                        'status': 'failed',
                        'message': 'Failed to send email'
                    })
                    failed += 1
                    
            except Exception as e:
                results.append({
                    'doctor_id': doctor_id,
                    'status': 'error',
                    'message': str(e)
                })
                failed += 1
        
        return EmailInvitationResponse(
            sent=sent,
            failed=failed,
            results=results
        )
    
    @staticmethod
    def _send_invitation_email(doctor: Doctor, message: str = None) -> bool:
        """Send invitation email to doctor (mock implementation)"""
        try:
            # Mock email sending - in production, use actual SMTP
            print(f"📧 Sending invitation email to {doctor.name} ({doctor.email})")
            print(f"   Message: {message or 'Welcome to our hospital system!'}")
            
            # Simulate email sending
            import time
            time.sleep(0.1)  # Simulate network delay
            
            return True
        except Exception as e:
            print(f"❌ Failed to send email to {doctor.email}: {str(e)}")
            return False
    
    @staticmethod
    def get_csv_template() -> str:
        """Get CSV template for bulk upload"""
        template = """name,email,phone,specialization,department,experience_years,qualification,consultation_fee,languages
Dr. John Smith,john.smith@hospital.com,+1-555-0123,Cardiologist,Cardiology,10,MD FACC,150,"English,Spanish"
Dr. Jane Doe,jane.doe@hospital.com,+1-555-0124,Neurologist,Neurology,8,MD PhD,200,"English,French"
Dr. Mike Johnson,mike.johnson@hospital.com,+1-555-0125,Pediatrician,Pediatrics,5,MD FAAP,120,"English,German"
"""
        return template 