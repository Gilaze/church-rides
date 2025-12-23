#!/usr/bin/env python3
"""
Church Rides Watchdog Service
Monitors the church rides website and sends email alerts when the service is down.
"""

import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from db import get_db_connection

# ==================== CONFIGURATION ====================
# You can set these via environment variables or modify them here

# Website URL to monitor
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://your-app.leapcell.dev')

# Check interval in seconds (default: 5 minutes)
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 300))

# Email settings
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'your-email@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'your-app-password')

# Alert recipient
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', 'admin@example.com')

# Request timeout in seconds
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 10))

# Number of consecutive failures before sending alert
FAILURE_THRESHOLD = int(os.environ.get('FAILURE_THRESHOLD', 2))

# ==================== GLOBALS ====================
consecutive_failures = 0
last_alert_sent = False  # Track if we've sent alert for current outage
was_down = False  # Track if site was down in previous check

# ==================== FUNCTIONS ====================

def check_website_health():
    """
    Check if the website is responding.
    Returns True if healthy, False otherwise.
    """
    try:
        response = requests.get(WEBSITE_URL, timeout=REQUEST_TIMEOUT)
        # Consider 200-399 status codes as healthy
        if 200 <= response.status_code < 400:
            return True
        else:
            print(f"[{get_timestamp()}] Website returned status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"[{get_timestamp()}] Request timed out after {REQUEST_TIMEOUT} seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"[{get_timestamp()}] Connection error - website may be down")
        return False
    except Exception as e:
        print(f"[{get_timestamp()}] Error checking website: {e}")
        return False


def get_rides_data():
    """
    Retrieve all rides and passengers from the database.
    Returns a formatted string with ride information.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all vehicles with driver information
        is_postgres = os.environ.get('DATABASE_URL') is not None
        placeholder = "%s" if is_postgres else "?"

        cur.execute(f"""
            SELECT
                v.id as vehicle_id,
                v.vehicle_name,
                u.full_name as driver_name,
                u.phone_number as driver_phone,
                u.driver_capacity
            FROM vehicles v
            JOIN users u ON v.driver_id = u.id
            ORDER BY v.vehicle_name
        """)

        vehicles = cur.fetchall()

        if not vehicles:
            return "No vehicles currently available.\n"

        rides_info = []
        rides_info.append("=" * 60)
        rides_info.append("CURRENT RIDE ASSIGNMENTS")
        rides_info.append("=" * 60)
        rides_info.append("")

        for vehicle in vehicles:
            vehicle_id = vehicle['vehicle_id']

            # Get passengers for this vehicle
            cur.execute(f"""
                SELECT u.full_name, u.phone_number, u.grade
                FROM bookings b
                JOIN users u ON b.passenger_id = u.id
                WHERE b.vehicle_id = {placeholder}
                ORDER BY u.full_name
            """, (vehicle_id,))

            passengers = cur.fetchall()

            rides_info.append(f"Vehicle: {vehicle['vehicle_name']}")
            rides_info.append(f"Driver: {vehicle['driver_name']}")
            if vehicle['driver_phone']:
                rides_info.append(f"Driver Phone: {vehicle['driver_phone']}")
            rides_info.append(f"Capacity: {len(passengers)}/{vehicle['driver_capacity'] or 'N/A'}")
            rides_info.append("")

            if passengers:
                rides_info.append("Passengers:")
                for i, passenger in enumerate(passengers, 1):
                    passenger_info = f"  {i}. {passenger['full_name']}"
                    if passenger['grade']:
                        passenger_info += f" ({passenger['grade']})"
                    if passenger['phone_number']:
                        passenger_info += f" - {passenger['phone_number']}"
                    rides_info.append(passenger_info)
            else:
                rides_info.append("Passengers: None")

            rides_info.append("")
            rides_info.append("-" * 60)
            rides_info.append("")

        conn.close()
        return "\n".join(rides_info)

    except Exception as e:
        error_msg = f"Error retrieving ride data from database: {e}"
        print(f"[{get_timestamp()}] {error_msg}")
        return error_msg


def send_alert_email(rides_data):
    """
    Send an email alert with the current rides and passengers.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD or not ALERT_EMAIL:
        print(f"[{get_timestamp()}] ❌ Email not configured! Cannot send alert.")
        print(f"   SMTP_USERNAME: {'SET' if SMTP_USERNAME else 'NOT SET'}")
        print(f"   SMTP_PASSWORD: {'SET' if SMTP_PASSWORD else 'NOT SET'}")
        print(f"   ALERT_EMAIL: {'SET' if ALERT_EMAIL else 'NOT SET'}")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🚨 Church Rides Service DOWN - {get_timestamp()}'
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL

        # Create email body
        text_body = f"""
ALERT: Church Rides Service is DOWN

The church rides website ({WEBSITE_URL}) is currently not responding.

Time of Alert: {get_timestamp()}
Consecutive Failures: {consecutive_failures}

Current Ride Assignments:
{rides_data}

---
This is an automated alert from the Church Rides Watchdog Service.
The service will continue monitoring and will notify you when it's back online.
"""

        # Attach text body
        msg.attach(MIMEText(text_body, 'plain'))

        # Send email
        print(f"[{get_timestamp()}] 📧 Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print(f"[{get_timestamp()}] 🔐 Logging in as {SMTP_USERNAME}...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print(f"[{get_timestamp()}] 📨 Sending email to {ALERT_EMAIL}...")
            server.send_message(msg)

        print(f"[{get_timestamp()}] ✅ Alert email sent successfully to {ALERT_EMAIL}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[{get_timestamp()}] ❌ SMTP Authentication failed!")
        print(f"   Error: {e}")
        print(f"   Check that SMTP_PASSWORD is your Gmail App Password (16 chars, no spaces)")
        return False
    except Exception as e:
        print(f"[{get_timestamp()}] ❌ Error sending email: {e}")
        return False


def send_recovery_email():
    """
    Send an email notification when the service is back online.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD or not ALERT_EMAIL:
        print(f"[{get_timestamp()}] ❌ Email not configured! Cannot send recovery notification.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'✅ Church Rides Service RECOVERED - {get_timestamp()}'
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL

        text_body = f"""
GOOD NEWS: Church Rides Service is BACK ONLINE

The church rides website ({WEBSITE_URL}) is now responding normally.

Recovery Time: {get_timestamp()}

The watchdog service will continue monitoring.

---
This is an automated notification from the Church Rides Watchdog Service.
"""

        msg.attach(MIMEText(text_body, 'plain'))

        print(f"[{get_timestamp()}] 📧 Sending recovery email to {ALERT_EMAIL}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[{get_timestamp()}] ✅ Recovery email sent successfully to {ALERT_EMAIL}")
        return True

    except Exception as e:
        print(f"[{get_timestamp()}] ❌ Error sending recovery email: {e}")
        return False


def get_timestamp():
    """Return formatted timestamp for logging."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def run_watchdog():
    """
    Main watchdog loop.
    Sends exactly 2 emails per outage: 1) Alert when down, 2) Recovery when back up
    """
    global consecutive_failures, last_alert_sent, was_down

    print(f"[{get_timestamp()}] Church Rides Watchdog Service started")
    print(f"Monitoring: {WEBSITE_URL}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print(f"Failure threshold: {FAILURE_THRESHOLD}")
    print(f"Alert email: {ALERT_EMAIL}")
    print("-" * 60)

    while True:
        try:
            is_healthy = check_website_health()

            if is_healthy:
                print(f"[{get_timestamp()}] ✓ Website is healthy")

                # If it was down and now recovered, send recovery email (Email #2)
                if was_down:
                    print(f"[{get_timestamp()}] Service recovered! Sending recovery notification...")
                    send_recovery_email()
                    was_down = False
                    last_alert_sent = False  # Reset for next outage

                consecutive_failures = 0

            else:
                consecutive_failures += 1
                print(f"[{get_timestamp()}] ✗ Website check failed ({consecutive_failures}/{FAILURE_THRESHOLD})")

                # Send alert if threshold reached AND we haven't sent one for this outage yet (Email #1)
                if consecutive_failures >= FAILURE_THRESHOLD and not last_alert_sent:
                    print(f"[{get_timestamp()}] Failure threshold reached! Retrieving ride data...")
                    rides_data = get_rides_data()

                    print(f"[{get_timestamp()}] Sending alert email...")
                    if send_alert_email(rides_data):
                        last_alert_sent = True  # Sent first email (alert)
                        was_down = True  # Mark as down so we can send recovery later

            # Wait before next check
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n[{get_timestamp()}] Watchdog service stopped by user")
            break
        except Exception as e:
            print(f"[{get_timestamp()}] Unexpected error in watchdog loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    # Validate configuration
    if SMTP_USERNAME == 'your-email@gmail.com' or ALERT_EMAIL == 'admin@example.com':
        print("=" * 60)
        print("WARNING: Email configuration not set!")
        print("=" * 60)
        print("Please configure the following environment variables:")
        print("  - SMTP_USERNAME: Your email address")
        print("  - SMTP_PASSWORD: Your email app password")
        print("  - ALERT_EMAIL: Email address to receive alerts")
        print("  - WEBSITE_URL: Your website URL to monitor")
        print("\nOr edit the configuration section at the top of this file.")
        print("=" * 60)
        print()

    run_watchdog()
