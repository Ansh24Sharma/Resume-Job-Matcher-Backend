import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()  # it will look for the env file

# Email configuration - Use environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_interview_invitation_email(
    candidate_email: str,
    candidate_name: str,
    recruiter_email: str,
    recruiter_name: str,
    company: str,
    job_title: str,
    interview_date: str,
    interview_time: str,
    interview_type: str,
    meeting_link: Optional[str] = None,
    additional_notes: Optional[str] = None
) -> bool:
    """
    Send interview invitation email to candidate
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Interview Invitation - {job_title} at {company}"
        message["From"] = recruiter_email
        message["To"] = candidate_email
        message["Reply-To"] = recruiter_email
        
        # Create email body
        interview_type_display = {
            "phone": "Phone Interview",
            "video": "Video Interview",
            "in-person": "In-Person Interview"
        }.get(interview_type, interview_type)
        
        # Plain text version
        text_content = f"""
Dear {candidate_name},

Congratulations! We are pleased to invite you for an interview for the position of {job_title} at {company}.

Interview Details:
------------------
Date: {interview_date}
Time: {interview_time}
Type: {interview_type_display}
"""
        
        if meeting_link:
            text_content += f"Meeting Link: {meeting_link}\n"
        
        if additional_notes:
            text_content += f"\nAdditional Information:\n{additional_notes}\n"
        
        text_content += f"""

Please confirm your attendance by replying to this email.

If you have any questions or need to reschedule, please don't hesitate to contact me.

Best regards,
{recruiter_name}
{company}
{recruiter_email}
"""
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .details-box {{
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #4CAF50;
            border-radius: 4px;
        }}
        .detail-row {{
            margin: 10px 0;
        }}
        .detail-label {{
            font-weight: bold;
            color: #555;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            margin: 20px 0;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #777;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Interview Invitation</h1>
        </div>
        <div class="content">
            <p>Dear {candidate_name},</p>
            
            <p>Congratulations! We are pleased to invite you for an interview for the position of <strong>{job_title}</strong> at <strong>{company}</strong>.</p>
            
            <div class="details-box">
                <h3 style="margin-top: 0; color: #4CAF50;">Interview Details</h3>
                <div class="detail-row">
                    <span class="detail-label">Date:</span> {interview_date}
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time:</span> {interview_time}
                </div>
                <div class="detail-row">
                    <span class="detail-label">Type:</span> {interview_type_display}
                </div>
"""
        
        if meeting_link:
            html_content += f"""
                <div class="detail-row">
                    <span class="detail-label">Meeting Link:</span> 
                    <a href="{meeting_link}" style="color: #4CAF50;">{meeting_link}</a>
                </div>
"""
        
        html_content += """
            </div>
"""
        
        if additional_notes:
            html_content += f"""
            <div class="details-box">
                <h3 style="margin-top: 0; color: #4CAF50;">Additional Information</h3>
                <p>{additional_notes}</p>
            </div>
"""
        
        html_content += f"""
            <p>Please confirm your attendance by replying to this email.</p>
            
            <p>If you have any questions or need to reschedule, please don't hesitate to contact me.</p>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>{recruiter_name}</strong><br>
                {company}<br>
                <a href="mailto:{recruiter_email}" style="color: #4CAF50;">{recruiter_email}</a>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email directly.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Attach both versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        
        print(f"✅ Interview invitation sent to {candidate_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending interview invitation: {e}")
        return False


def send_status_update_email(
    candidate_email: str,
    candidate_name: str,
    recruiter_email: str,
    recruiter_name: str,
    company: str,
    job_title: str,
    new_status: str
) -> bool:
    """
    Send status update notification to candidate
    """
    try:
        status_messages = {
            "under_review": "Your application is currently under review",
            "rejected": "Update on your application",
            "hired": "Congratulations! Job offer"
        }
        
        subject = f"{status_messages.get(new_status, 'Application Status Update')} - {job_title}"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = recruiter_email
        message["To"] = candidate_email
        message["Reply-To"] = recruiter_email
        
        # Customize message based on status
        if new_status == "hired":
            content = f"""
Dear {candidate_name},

Congratulations! We are delighted to offer you the position of {job_title} at {company}.

We were impressed by your qualifications and believe you would be a great addition to our team.

We will be sending you the formal offer letter shortly with all the details.

Best regards,
{recruiter_name}
{company}
"""
        elif new_status == "rejected":
            content = f"""
Dear {candidate_name},

Thank you for your interest in the {job_title} position at {company}.

After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs.

We appreciate the time you invested in the application process and wish you the best in your job search.

Best regards,
{recruiter_name}
{company}
"""
        else:
            content = f"""
Dear {candidate_name},

This is to inform you that your application for the {job_title} position at {company} is currently under review.

We will contact you soon with the next steps.

Best regards,
{recruiter_name}
{company}
"""
        
        text_part = MIMEText(content, "plain")
        message.attach(text_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        
        print(f"✅ Status update email sent to {candidate_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending status update email: {e}")
        return False