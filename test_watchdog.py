#!/usr/bin/env python3
"""
Quick test script to verify watchdog email functionality.
Run this to test if your email settings are configured correctly.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email settings (same as watchdog.py)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'your-email@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'your-app-password')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', 'admin@example.com')

def test_email():
    """Send a test email to verify configuration."""

    print("=" * 60)
    print("Church Rides Watchdog - Email Configuration Test")
    print("=" * 60)
    print(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"From: {SMTP_USERNAME}")
    print(f"To: {ALERT_EMAIL}")
    print("-" * 60)

    if SMTP_USERNAME == 'your-email@gmail.com' or ALERT_EMAIL == 'admin@example.com':
        print("\n⚠️  ERROR: Email configuration not set!")
        print("\nPlease set the following environment variables:")
        print("  - SMTP_USERNAME")
        print("  - SMTP_PASSWORD")
        print("  - ALERT_EMAIL")
        print("\nExample (Windows CMD):")
        print('  set SMTP_USERNAME=your-email@gmail.com')
        print('  set SMTP_PASSWORD=your-app-password')
        print('  set ALERT_EMAIL=admin@example.com')
        return False

    try:
        print("\n📧 Creating test email...")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = '✅ Watchdog Test Email - Configuration Successful'
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL

        text_body = f"""
This is a test email from the Church Rides Watchdog Service.

If you're receiving this, your email configuration is working correctly! ✅

Configuration Details:
- SMTP Server: {SMTP_SERVER}:{SMTP_PORT}
- From: {SMTP_USERNAME}
- To: {ALERT_EMAIL}
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Next Steps:
1. Verify you received this email at {ALERT_EMAIL}
2. Run the watchdog service: python watchdog.py
3. The watchdog will monitor your website and send alerts when it's down

---
Church Rides Watchdog Test Email
"""

        msg.attach(MIMEText(text_body, 'plain'))

        print("📤 Connecting to SMTP server...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print("🔐 Starting TLS encryption...")
            server.starttls()

            print("🔑 Logging in...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)

            print("📨 Sending test email...")
            server.send_message(msg)

        print("\n" + "=" * 60)
        print("✅ SUCCESS! Test email sent successfully!")
        print("=" * 60)
        print(f"\nCheck your inbox at: {ALERT_EMAIL}")
        print("\nIf you received the email, your watchdog is ready to use!")
        print("Run: python watchdog.py")
        print("=" * 60)
        return True

    except smtplib.SMTPAuthenticationError:
        print("\n" + "=" * 60)
        print("❌ AUTHENTICATION FAILED")
        print("=" * 60)
        print("\nPossible causes:")
        print("1. Incorrect username or password")
        print("2. For Gmail: You need to use an App Password")
        print("   - Visit: https://myaccount.google.com/apppasswords")
        print("   - Enable 2FA first if not already enabled")
        print("   - Generate an App Password for 'Mail'")
        print("3. Check if 'Less secure app access' is enabled (not recommended)")
        print("=" * 60)
        return False

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR SENDING EMAIL")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nPossible causes:")
        print("1. Internet connection issues")
        print("2. SMTP server or port incorrect")
        print("3. Firewall blocking outgoing mail")
        print("=" * 60)
        return False


if __name__ == '__main__':
    test_email()
