#!/usr/bin/env python3
"""
Bulk Google Calendar Setup Helper
Generates calendar connection URLs for multiple doctors
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.core.database import get_db
from core import models

def generate_calendar_urls():
    """Generate calendar connection URLs for doctors that need setup"""
    print("🔗 Bulk Google Calendar Setup Helper")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get doctors without calendar connection
        disconnected_doctors = db.query(models.Doctor).filter(
            models.Doctor.google_access_token.is_(None)
        ).all()
        
        if not disconnected_doctors:
            print("✅ All doctors already have Google Calendar connected!")
            return
        
        print(f"📊 Found {len(disconnected_doctors)} doctors without calendar connection")
        print()
        
        # Group by department for easier management
        departments = {}
        for doctor in disconnected_doctors:
            dept_name = doctor.department.name if doctor.department else "No Department"
            if dept_name not in departments:
                departments[dept_name] = []
            departments[dept_name].append(doctor)
        
        base_url = "http://localhost:8000/auth/google/login"
        
        print("🏥 Calendar Connection URLs by Department:")
        print("=" * 50)
        
        for dept_name, doctors in departments.items():
            print(f"\n📋 {dept_name} ({len(doctors)} doctors):")
            print("-" * 40)
            
            for doctor in doctors:
                url = f"{base_url}?doctor_id={doctor.id}"
                print(f"👨‍⚕️ {doctor.name}")
                print(f"   🔗 {url}")
                print()
        
        # Generate a simple HTML page for easy clicking
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Doctor Calendar Setup</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .doctor {{ margin: 15px 0; padding: 15px; background: #ecf0f1; border-radius: 5px; }}
        .doctor-name {{ font-weight: bold; color: #2c3e50; }}
        .connect-btn {{ 
            display: inline-block; margin-top: 10px; padding: 8px 16px; 
            background: #3498db; color: white; text-decoration: none; 
            border-radius: 4px; font-size: 14px;
        }}
        .connect-btn:hover {{ background: #2980b9; }}
        .stats {{ background: #3498db; color: white; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗓️ Google Calendar Setup for Doctors</h1>
        <div class="stats">
            <strong>{len(disconnected_doctors)} doctors</strong> need Google Calendar connection
        </div>
        """
        
        for dept_name, doctors in departments.items():
            html_content += f"""
        <h2>📋 {dept_name}</h2>
        """
            for doctor in doctors:
                url = f"{base_url}?doctor_id={doctor.id}"
                subdivision = f" - {doctor.subdivision.name}" if doctor.subdivision else ""
                html_content += f"""
        <div class="doctor">
            <div class="doctor-name">👨‍⚕️ {doctor.name}{subdivision}</div>
            <a href="{url}" class="connect-btn" target="_blank">Connect Google Calendar</a>
        </div>
        """
        
        html_content += """
    </div>
</body>
</html>
        """
        
        # Save HTML file
        html_file = "calendar_setup.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("\n📄 Generated easy-to-use setup page:")
        print(f"   📁 File: {os.path.abspath(html_file)}")
        print(f"   🌐 Open this file in your browser for easy clicking!")
        
        print("\n💡 Instructions:")
        print("   1. Open the generated HTML file in your browser")
        print("   2. Click 'Connect Google Calendar' for each doctor")
        print("   3. Follow the OAuth authorization flow")
        print("   4. Repeat for all doctors you want to connect")
        
        print(f"\n🎯 Priority: Connect calendars for doctors with recent appointments first!")
        
        # Show recent appointment doctors
        from datetime import date, timedelta
        week_ago = date.today() - timedelta(days=7)
        
        recent_appointments = db.query(models.Appointment).filter(
            models.Appointment.date >= week_ago
        ).all()
        
        recent_doctor_ids = set(apt.doctor_id for apt in recent_appointments)
        priority_doctors = [doc for doc in disconnected_doctors if doc.id in recent_doctor_ids]
        
        if priority_doctors:
            print(f"\n⚡ HIGH PRIORITY ({len(priority_doctors)} doctors with recent appointments):")
            for doctor in priority_doctors:
                print(f"   👨‍⚕️ {doctor.name} - {base_url}?doctor_id={doctor.id}")
        
    except Exception as e:
        print(f"❌ Error generating setup URLs: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    generate_calendar_urls() 