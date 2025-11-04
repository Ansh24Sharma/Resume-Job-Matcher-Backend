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

def send_hiring_email(
    candidate_email: str,
    candidate_name: str,
    recruiter_email: str,
    recruiter_name: str,
    company: str,
    job_title: str,
    additional_notes: Optional[str] = None
) -> bool:
    """
    Send hiring congratulation email to candidate
    """
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = candidate_email
        msg['Subject'] = f"Congratulations! You're Hired at {company}"
        
        # Email body
        body = f"""
Dear {candidate_name},

Congratulations! We are pleased to inform you that you have been selected for the position of {job_title} at {company}.

We were impressed with your qualifications and believe you will be a valuable addition to our team.

{f'Additional Information: {additional_notes}' if additional_notes else ''}

Our HR team will reach out to you shortly with the next steps, including onboarding details and paperwork.

If you have any questions, please feel free to contact {recruiter_name} at {recruiter_email}.

Welcome aboard!

Best regards,
{recruiter_name}
{company}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending hiring email: {str(e)}")
        return False


