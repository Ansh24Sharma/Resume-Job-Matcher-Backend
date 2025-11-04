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

def send_rejection_email(
    candidate_email: str,
    candidate_name: str,
    recruiter_email: str,
    recruiter_name: str,
    company: str,
    job_title: str,
    additional_notes: Optional[str] = None
) -> bool:
    """
    Send rejection email to candidate
    """
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = candidate_email
        msg['Subject'] = f"Application Update - {job_title} at {company}"
        
        # Email body
        body = f"""
Dear {candidate_name},

Thank you for your interest in the {job_title} position at {company} and for taking the time to interview with us.

After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs.

{f'Feedback: {additional_notes}' if additional_notes else ''}

We appreciate your interest in joining our team and encourage you to apply for future openings that match your skills and experience.

We wish you all the best in your job search and future endeavors.

Best regards,
{recruiter_name}
{company}

If you have any questions, please contact {recruiter_email}.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending rejection email: {str(e)}")
        return False