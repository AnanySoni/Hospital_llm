"""
Email Service for Hospital Admin Panel
Handles email invitations, notifications, and communication
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.models import Doctor, AdminUser, Hospital

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails to doctors and admin users"""
    
    # Email configuration (in production, use environment variables)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "hospital.admin@example.com")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")
    
    @staticmethod
    def send_doctor_invitation(doctor: Doctor, hospital: Hospital, admin_user: AdminUser, custom_message: str = None) -> bool:
        """Send invitation email to a doctor"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EmailService.EMAIL_ADDRESS
            msg['To'] = doctor.email
            msg['Subject'] = f"Invitation to join {hospital.display_name} - Hospital AI Assistant"
            
            # Email body
            body = EmailService._create_invitation_body(doctor, hospital, admin_user, custom_message)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            success = EmailService._send_email(msg)
            
            if success:
                logger.info(f"Invitation email sent successfully to {doctor.email}")
            else:
                logger.error(f"Failed to send invitation email to {doctor.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending invitation to {doctor.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_bulk_invitations(doctors: List[Doctor], hospital: Hospital, admin_user: AdminUser, custom_message: str = None) -> Dict[str, Any]:
        """Send bulk invitation emails to multiple doctors"""
        results = {
            'sent': 0,
            'failed': 0,
            'results': []
        }
        
        for doctor in doctors:
            success = EmailService.send_doctor_invitation(doctor, hospital, admin_user, custom_message)
            
            if success:
                results['sent'] += 1
                results['results'].append({
                    'doctor_id': doctor.id,
                    'doctor_name': doctor.name,
                    'email': doctor.email,
                    'status': 'sent',
                    'message': 'Invitation sent successfully'
                })
            else:
                results['failed'] += 1
                results['results'].append({
                    'doctor_id': doctor.id,
                    'doctor_name': doctor.name,
                    'email': doctor.email,
                    'status': 'failed',
                    'message': 'Failed to send invitation'
                })
        
        return results
    
    @staticmethod
    def send_calendar_setup_reminder(doctor: Doctor, hospital: Hospital) -> bool:
        """Send reminder email for Google Calendar setup"""
        try:
            msg = MIMEMultipart()
            msg['From'] = EmailService.EMAIL_ADDRESS
            msg['To'] = doctor.email
            msg['Subject'] = f"Google Calendar Setup Required - {hospital.display_name}"
            
            body = EmailService._create_calendar_reminder_body(doctor, hospital)
            msg.attach(MIMEText(body, 'html'))
            
            return EmailService._send_email(msg)
            
        except Exception as e:
            logger.error(f"Error sending calendar reminder to {doctor.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(doctor: Doctor, hospital: Hospital, login_credentials: Dict[str, str]) -> bool:
        """Send welcome email with login credentials"""
        try:
            msg = MIMEMultipart()
            msg['From'] = EmailService.EMAIL_ADDRESS
            msg['To'] = doctor.email
            msg['Subject'] = f"Welcome to {hospital.display_name} - Account Created"
            
            body = EmailService._create_welcome_body(doctor, hospital, login_credentials)
            msg.attach(MIMEText(body, 'html'))
            
            return EmailService._send_email(msg)
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {doctor.email}: {str(e)}")
            return False
    
    @staticmethod
    def _send_email(msg: MIMEMultipart) -> bool:
        """Send email using SMTP"""
        try:
            # Create SMTP session
            server = smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT)
            server.starttls()  # Enable TLS
            server.login(EmailService.EMAIL_ADDRESS, EmailService.EMAIL_PASSWORD)
            
            # Send email
            text = msg.as_string()
            server.sendmail(EmailService.EMAIL_ADDRESS, msg['To'], text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    @staticmethod
    def _create_invitation_body(doctor: Doctor, hospital: Hospital, admin_user: AdminUser, custom_message: str = None) -> str:
        """Create HTML body for invitation email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .button {{ background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{hospital.display_name}</h1>
                    <p>Hospital AI Assistant Platform</p>
                </div>
                
                <div class="content">
                    <h2>Dear Dr. {doctor.name},</h2>
                    
                    <p>You have been invited to join <strong>{hospital.display_name}</strong> on our Hospital AI Assistant platform.</p>
                    
                    <p>Our platform provides:</p>
                    <ul>
                        <li>AI-powered patient consultation assistance</li>
                        <li>Automated appointment scheduling</li>
                        <li>Google Calendar integration</li>
                        <li>Patient history and analytics</li>
                        <li>Secure communication tools</li>
                    </ul>
                    
                    {f'<p><strong>Message from {admin_user.first_name} {admin_user.last_name}:</strong></p><p style="font-style: italic;">{custom_message}</p>' if custom_message else ''}
                    
                    <p>To get started, please click the button below to set up your account:</p>
                    
                    <a href="http://localhost:3000/admin" class="button">Set Up Account</a>
                    
                    <p>If you have any questions, please contact our support team or reach out to {admin_user.first_name} {admin_user.last_name} at {admin_user.email}.</p>
                    
                    <p>Best regards,<br>
                    The {hospital.display_name} Team</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent from {hospital.display_name} Hospital AI Assistant Platform</p>
                    <p>If you did not expect this email, please ignore it.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _create_calendar_reminder_body(doctor: Doctor, hospital: Hospital) -> str:
        """Create HTML body for calendar setup reminder"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #059669; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .button {{ background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Google Calendar Setup Required</h1>
                    <p>{hospital.display_name}</p>
                </div>
                
                <div class="content">
                    <h2>Dear Dr. {doctor.name},</h2>
                    
                    <p>To complete your setup on the Hospital AI Assistant platform, please connect your Google Calendar.</p>
                    
                    <p>This will enable:</p>
                    <ul>
                        <li>Automatic appointment scheduling</li>
                        <li>Calendar conflict detection</li>
                        <li>Patient reminder notifications</li>
                        <li>Seamless availability management</li>
                    </ul>
                    
                    <a href="http://localhost:3000/admin" class="button">Connect Google Calendar</a>
                    
                    <p>If you need assistance, please contact our support team.</p>
                    
                    <p>Best regards,<br>
                    The {hospital.display_name} Team</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated reminder from {hospital.display_name} Hospital AI Assistant Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _create_welcome_body(doctor: Doctor, hospital: Hospital, login_credentials: Dict[str, str]) -> str:
        """Create HTML body for welcome email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #7c3aed; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .credentials {{ background-color: #e0e7ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .button {{ background-color: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {hospital.display_name}!</h1>
                    <p>Your account has been created</p>
                </div>
                
                <div class="content">
                    <h2>Dear Dr. {doctor.name},</h2>
                    
                    <p>Welcome to the Hospital AI Assistant platform! Your account has been successfully created.</p>
                    
                    <div class="credentials">
                        <h3>Your Login Credentials:</h3>
                        <p><strong>Username:</strong> {login_credentials.get('username', 'N/A')}</p>
                        <p><strong>Temporary Password:</strong> {login_credentials.get('password', 'N/A')}</p>
                        <p><em>Please change your password after first login</em></p>
                    </div>
                    
                    <p>Next steps:</p>
                    <ol>
                        <li>Log in to your account</li>
                        <li>Change your temporary password</li>
                        <li>Complete your profile</li>
                        <li>Connect your Google Calendar</li>
                        <li>Set your availability</li>
                    </ol>
                    
                    <a href="http://localhost:3000/admin" class="button">Login to Your Account</a>
                    
                    <p>If you need any assistance, please don't hesitate to contact our support team.</p>
                    
                    <p>Best regards,<br>
                    The {hospital.display_name} Team</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent from {hospital.display_name} Hospital AI Assistant Platform</p>
                    <p>Please keep your login credentials secure and do not share them with anyone.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def test_email_configuration() -> Dict[str, Any]:
        """Test email configuration"""
        try:
            # Test SMTP connection
            server = smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT)
            server.starttls()
            server.login(EmailService.EMAIL_ADDRESS, EmailService.EMAIL_PASSWORD)
            server.quit()
            
            return {
                'status': 'success',
                'message': 'Email configuration is working correctly',
                'smtp_server': EmailService.SMTP_SERVER,
                'email_address': EmailService.EMAIL_ADDRESS
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Email configuration error: {str(e)}',
                'smtp_server': EmailService.SMTP_SERVER,
                'email_address': EmailService.EMAIL_ADDRESS
            } 