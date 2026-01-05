"""
Test Script for Email Notifications.
"""

from src.utils.notifications import notification_service
import sys

def test_email():
    print("📧 Testing Email Notification Service...")
    print(f"   SMTP Host: {notification_service.smtp_host}")
    print(f"   User: {notification_service.smtp_user or 'NOT SET'}")
    
    if not notification_service.smtp_user:
        print("❌ SMTP_USER not set in .env. Skipping send test.")
        return
    
    success = notification_service.send_email(
        subject="Test Alert System",
        body="This is a test email from the Flood Validation System.",
        recipients=["test@example.com"]  # Won't actually send if auth fails, but good test
    )
    
    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Failed to send email (Check logs/credentials)")

if __name__ == "__main__":
    test_email()
