"""
Email Notification Service for Flood Validation System.

Sends email alerts to admins when:
- High-priority reports are validated
- System statistics (daily digest)
- Alert thresholds are reached
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    SMTP-based email notification service.
    
    Configure via environment variables:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port (default: 587)
    - SMTP_USER: SMTP username/email
    - SMTP_PASSWORD: SMTP password
    - ADMIN_EMAILS: Comma-separated list of admin emails
    """
    
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
        self.sender_email = os.getenv("SENDER_EMAIL", self.user)
        self.enabled = bool(self.user and self.password)
        
        if not self.enabled:
            logger.warning("Email notifications disabled (SMTP credentials not configured)")
    
    def send_email(self, to_emails: List[str], subject: str, 
                   body_html: str, body_text: Optional[str] = None) -> bool:
        """
        Send an email to specified recipients.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional)
            
        Returns:
            True if email sent successfully
        """
        if not self.enabled:
            logger.info(f"Email skipped (disabled): {subject}")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(to_emails)
            
            # Add plain text and HTML parts
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender_email, to_emails, msg.as_string())
            
            logger.info(f"Email sent: {subject} to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False
    
    def notify_admins(self, subject: str, body_html: str) -> bool:
        """Send notification to all configured admin emails."""
        if not self.admin_emails or not self.admin_emails[0]:
            logger.warning("No admin emails configured")
            return False
        
        return self.send_email(self.admin_emails, subject, body_html)
    
    def send_validated_report_alert(self, report: Dict) -> bool:
        """
        Send alert when a high-priority report is validated.
        
        Args:
            report: Report data dictionary
        """
        subject = f"🚨 Flood Report Validated - {report.get('location', 'Unknown')}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #1565c0;">Flood Report Validated</h2>
            
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Report ID:</td>
                    <td style="padding: 8px;">{report.get('report_id', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Location:</td>
                    <td style="padding: 8px;">{report.get('latitude', 0):.4f}, {report.get('longitude', 0):.4f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Depth:</td>
                    <td style="padding: 8px;">{report.get('depth_meters', 0):.1f} meters</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Validation Score:</td>
                    <td style="padding: 8px;">{report.get('final_score', 0):.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Timestamp:</td>
                    <td style="padding: 8px;">{report.get('timestamp', 'N/A')}</td>
                </tr>
            </table>
            
            <p style="color: #666;">
                View on dashboard: <a href="http://localhost:3000/reports/{report.get('report_id')}">Open Report</a>
            </p>
            
            <hr style="border: none; border-top: 1px solid #ddd;">
            <p style="color: #999; font-size: 12px;">
                Odisha Flood Validation System - Automated Alert
            </p>
        </body>
        </html>
        """
        
        return self.notify_admins(subject, body_html)
    
    def send_daily_digest(self, stats: Dict) -> bool:
        """
        Send daily statistics digest to admins.
        
        Args:
            stats: System statistics dictionary
        """
        subject = f"📊 Daily Flood Report Digest - {datetime.now().strftime('%Y-%m-%d')}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2e7d32;">Daily Report Digest</h2>
            
            <table style="border-collapse: collapse; margin: 20px 0; width: 100%; max-width: 400px;">
                <tr style="background: #e8f5e9;">
                    <td style="padding: 12px; font-weight: bold;">Total Reports</td>
                    <td style="padding: 12px; text-align: right;">{stats.get('total_reports', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; font-weight: bold;">Validated</td>
                    <td style="padding: 12px; text-align: right; color: #2e7d32;">{stats.get('validated', 0)}</td>
                </tr>
                <tr style="background: #fff3e0;">
                    <td style="padding: 12px; font-weight: bold;">Flagged</td>
                    <td style="padding: 12px; text-align: right; color: #ef6c00;">{stats.get('flagged', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; font-weight: bold;">Rejected</td>
                    <td style="padding: 12px; text-align: right; color: #c62828;">{stats.get('rejected', 0)}</td>
                </tr>
                <tr style="background: #e3f2fd;">
                    <td style="padding: 12px; font-weight: bold;">Validation Rate</td>
                    <td style="padding: 12px; text-align: right;">{stats.get('validation_rate', 0):.1f}%</td>
                </tr>
            </table>
            
            <p style="color: #666;">
                <a href="http://localhost:3000/dashboard">View Full Dashboard</a>
            </p>
            
            <hr style="border: none; border-top: 1px solid #ddd;">
            <p style="color: #999; font-size: 12px;">
                This is an automated daily digest from the Odisha Flood Validation System.
            </p>
        </body>
        </html>
        """
        
        return self.notify_admins(subject, body_html)
    
    def send_alert_threshold(self, alert_type: str, count: int, 
                             threshold: int, details: Dict) -> bool:
        """
        Send alert when a threshold is exceeded.
        
        Args:
            alert_type: Type of alert (e.g., "hourly_reports", "flagged_reports")
            count: Current count
            threshold: Threshold that was exceeded
            details: Additional context
        """
        subject = f"⚠️ Alert Threshold Exceeded: {alert_type}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #c62828;">⚠️ Threshold Alert</h2>
            
            <p>The following threshold has been exceeded:</p>
            
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Alert Type:</td>
                    <td style="padding: 8px;">{alert_type}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Current Count:</td>
                    <td style="padding: 8px; color: #c62828; font-weight: bold;">{count}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Threshold:</td>
                    <td style="padding: 8px;">{threshold}</td>
                </tr>
            </table>
            
            <p style="color: #666;">
                Please review the system status immediately.
            </p>
            
            <hr style="border: none; border-top: 1px solid #ddd;">
            <p style="color: #999; font-size: 12px;">
                Odisha Flood Validation System - Automated Alert
            </p>
        </body>
        </html>
        """
        
        return self.notify_admins(subject, body_html)


# Singleton instance
email_service = EmailNotificationService()


if __name__ == "__main__":
    print("📧 Email Notification Service")
    print(f"   SMTP Host: {email_service.host}")
    print(f"   Enabled: {email_service.enabled}")
    print(f"   Admin Emails: {email_service.admin_emails}")
    
    # Test (won't actually send without SMTP config)
    if email_service.enabled:
        email_service.send_daily_digest({
            "total_reports": 150,
            "validated": 100,
            "flagged": 35,
            "rejected": 15,
            "validation_rate": 66.7
        })
