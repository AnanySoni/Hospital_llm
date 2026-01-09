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

from backend.core.models import Doctor, AdminUser, Hospital

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails to doctors and admin users"""
    
    # Email configuration (in production, use environment variables)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "hospital.admin@example.com")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
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
    def send_verification_email(admin_user: AdminUser, token: str) -> bool:
        """Send email verification email to admin user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = EmailService.EMAIL_ADDRESS
            msg['To'] = admin_user.email
            msg['Subject'] = "Verify your email - Hospital AI Platform"
            
            body = EmailService._create_verification_email_body(admin_user, token)
            msg.attach(MIMEText(body, 'html'))
            
            success = EmailService._send_email(msg)
            
            if success:
                logger.info(f"Verification email sent successfully to {admin_user.email}")
            else:
                logger.error(f"Failed to send verification email to {admin_user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending verification email to {admin_user.email}: {str(e)}")
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
    def send_admin_welcome_email(admin_user: AdminUser, onboarding_session_id: Optional[int] = None) -> bool:
        """Send welcome email to admin user after email verification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = EmailService.EMAIL_ADDRESS
            msg['To'] = admin_user.email
            msg['Subject'] = "Welcome to Hospital AI Platform - Your Account is Verified"
            
            body = EmailService._create_admin_welcome_body(admin_user, admin_user.username, onboarding_session_id)
            msg.attach(MIMEText(body, 'html'))
            
            success = EmailService._send_email(msg)
            
            if success:
                logger.info(f"Welcome email sent successfully to {admin_user.email}")
            else:
                logger.error(f"Failed to send welcome email to {admin_user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {admin_user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(admin_user: AdminUser, token: str) -> bool:
        """Send password reset email to admin user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = EmailService.EMAIL_ADDRESS
            msg['To'] = admin_user.email
            msg['Subject'] = "Reset Your Password - Hospital AI Platform"
            
            body = EmailService._create_password_reset_body(admin_user, token)
            msg.attach(MIMEText(body, 'html'))
            
            success = EmailService._send_email(msg)
            
            if success:
                logger.info(f"Password reset email sent successfully to {admin_user.email}")
            else:
                logger.error(f"Failed to send password reset email to {admin_user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {admin_user.email}: {str(e)}")
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
    def _create_verification_email_body(admin_user: AdminUser, token: str) -> str:
        """Create HTML body for email verification email"""
        verification_url = f"{EmailService.FRONTEND_URL}/onboarding/verify-email?token={token}"
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
                .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Hospital AI Platform</h1>
                    <p>Email Verification</p>
                </div>
                
                <div class="content">
                    <h2>Hello,</h2>
                    
                    <p>Thank you for signing up for the Hospital AI Platform! Please verify your email address to complete your registration.</p>
                    
                    <p>Click the button below to verify your email:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #2563eb;">{verification_url}</p>
                    
                    <div class="warning">
                        <p><strong>⚠️ Important:</strong> This verification link will expire in 24 hours. Please verify your email as soon as possible.</p>
                    </div>
                    
                    <p>If you did not create an account with us, please ignore this email.</p>
                    
                    <p>Best regards,<br>
                    The Hospital AI Platform Team</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent from Hospital AI Platform</p>
                    <p>If you need assistance, please contact our support team.</p>
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
    def _create_admin_welcome_body(admin_user: AdminUser, username: str, onboarding_session_id: Optional[int] = None) -> str:
        """Create HTML body for admin welcome email"""
        company_name = admin_user.company_name or "your organization"
        onboarding_url = f"{EmailService.FRONTEND_URL}/onboarding/hospital-info"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .button {{ background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .steps {{ background-color: #e0f2fe; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .steps ol {{ margin: 10px 0; padding-left: 20px; }}
                .steps li {{ margin: 8px 0; }}
                .credentials {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .credentials h3 {{ margin-top: 0; color: #856404; }}
                .credentials code {{ background-color: #f8f9fa; padding: 4px 8px; border-radius: 3px; font-family: monospace; }}
                .credentials p {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Hospital AI Platform!</h1>
                    <p>Your email has been verified</p>
                </div>
                
                <div class="content">
                    <h2>Hello,</h2>
                    
                    <p>Congratulations! Your email address has been successfully verified, and your account is now active.</p>
                    
                    <p>Welcome to <strong>{company_name}</strong> on the Hospital AI Platform. You're now ready to set up your hospital and start using our AI-powered healthcare assistant.</p>
                    
                    <div class="credentials">
                        <h3>🔐 Your Login Credentials</h3>
                        <p><strong>Username:</strong> <code>{username}</code></p>
                        <p><strong>Password:</strong> The password you set during registration</p>
                        <p style="color: #856404;"><strong>⚠️ Important:</strong> Please save these credentials for future logins. You'll need them to access your admin panel after completing hospital setup.</p>
                        <p>After you complete hospital setup, you can log in at: <code>https://yourdomain.com/h/your-hospital-slug/admin</code></p>
                    </div>
                    
                    <div class="steps">
                        <h3>Next Steps:</h3>
                        <ol>
                            <li><strong>Complete Hospital Information</strong> - Add your hospital details and choose your unique URL</li>
                            <li><strong>Set Up Departments</strong> - Organize your hospital structure (in Admin Panel)</li>
                            <li><strong>Add Doctors</strong> - Invite your medical staff via CSV upload or manual entry (in Admin Panel)</li>
                            <li><strong>Launch Your AI Assistant</strong> - Start helping patients with AI-powered consultations</li>
                        </ol>
                    </div>
                    
                    <p>Click the button below to continue with your onboarding:</p>
                    
                    <div style="text-align: center;">
                        <a href="{onboarding_url}" class="button">Continue Onboarding</a>
                    </div>
                    
                    <p>Our platform provides:</p>
                    <ul>
                        <li>AI-powered patient consultation assistance</li>
                        <li>Automated appointment scheduling</li>
                        <li>Patient history and analytics</li>
                        <li>Secure communication tools</li>
                        <li>Multi-tenant hospital management</li>
                    </ul>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    
                    <p>Best regards,<br>
                    The Hospital AI Platform Team</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent from Hospital AI Platform</p>
                    <p>If you need assistance, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _create_password_reset_body(admin_user: AdminUser, token: str) -> str:
        """Create HTML body for password reset email"""
        reset_url = f"{EmailService.FRONTEND_URL}/onboarding/reset-password?token={token}"
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .button {{ background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .warning {{ background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 12px; margin: 20px 0; }}
                .security {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Hospital AI Platform</h1>
                    <p>Password Reset Request</p>
                </div>
                
                <div class="content">
                    <h2>Hello,</h2>
                    
                    <p>We received a request to reset your password for your Hospital AI Platform account.</p>
                    
                    <p>Click the button below to reset your password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #dc2626;">{reset_url}</p>
                    
                    <div class="warning">
                        <p><strong>⚠️ Important:</strong> This password reset link will expire in 1 hour. Please reset your password as soon as possible.</p>
                    </div>
                    
                    <div class="security">
                        <p><strong>🔒 Security Notice:</strong> If you did not request a password reset, please ignore this email. Your password will remain unchanged.</p>
                    </div>
                    
                    <p>For security reasons, this link can only be used once. If you need to reset your password again, please request a new reset link.</p>
                    
                    <p>If you continue to have issues, please contact our support team.</p>
                    
                    <p>Best regards,<br>
                    The Hospital AI Platform Team</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent from Hospital AI Platform</p>
                    <p>If you need assistance, please contact our support team.</p>
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