"""
Email Notification Service.
Sends alerts to admins using SMTP configuration from .env.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_user)
        self.admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
        
    def send_email(self, subject: str, body: str, recipients: Optional[List[str]] = None) -> bool:
        """Send an email alert."""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not set. Skipping email.")
            return False
            
        if not recipients:
            recipients = self.admin_emails
            
        recipients = [r.strip() for r in recipients if r.strip()]
        
        if not recipients:
            logger.warning("No recipients defined.")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"[Flood Alert] {subject}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {len(recipients)} recipients: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_flood_alert(self, location: str, severity: str, details: str):
        """Send a specific flood alert."""
        subject = f"High Risk Flood Alert - {location}"
        body = f"""
        FLOOD ALERT
        
        Location: {location}
        Severity: {severity.upper()}
        Time: {os.getenv('CURRENT_TIME', 'Now')}
        
        Details:
        {details}
        
        Access Dashboard: http://localhost:3000
        """
        return self.send_email(subject, body)

# Singleton
notification_service = NotificationService()
