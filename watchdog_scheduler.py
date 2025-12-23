"""
Watchdog integrated into Flask app using APScheduler
This runs the monitoring checks as background scheduled tasks within your Flask app
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from db import get_db_connection

# Configuration from environment variables
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://your-app.leapcell.dev')
CHECK_INTERVAL_MINUTES = int(os.environ.get('CHECK_INTERVAL_MINUTES', 5))
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', '')
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 10))
FAILURE_THRESHOLD = int(os.environ.get('FAILURE_THRESHOLD', 2))

# Global state
consecutive_failures = 0
last_alert_time = None
was_down = False
ALERT_COOLDOWN = 3600  # 1 hour


def get_timestamp():
    """Return formatted timestamp for logging."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def check_website_health():
    """Check if the website is responding."""
    try:
        response = requests.get(WEBSITE_URL, timeout=REQUEST_TIMEOUT)
        return 200 <= response.status_code < 400
    except Exception as e:
        print(f"[{get_timestamp()}] Health check error: {e}")
        return False


def get_rides_data():
    """Retrieve all rides and passengers from the database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

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
            conn.close()
            return "No vehicles currently available.\n"

        rides_info = []
        rides_info.append("=" * 60)
        rides_info.append("CURRENT RIDE ASSIGNMENTS")
        rides_info.append("=" * 60)
        rides_info.append("")

        for vehicle in vehicles:
            vehicle_id = vehicle['vehicle_id']

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
        error_msg = f"Error retrieving ride data: {e}"
        print(f"[{get_timestamp()}] {error_msg}")
        return error_msg


def send_alert_email(rides_data):
    """Send email alert with ride data."""
    global last_alert_time

    if not SMTP_USERNAME or not ALERT_EMAIL:
        print(f"[{get_timestamp()}] Email not configured, skipping alert")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🚨 Church Rides Service DOWN - {get_timestamp()}'
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL

        text_body = f"""
ALERT: Church Rides Service is DOWN

The church rides website ({WEBSITE_URL}) is currently not responding.

Time of Alert: {get_timestamp()}
Consecutive Failures: {consecutive_failures}

Current Ride Assignments:
{rides_data}

---
This is an automated alert from the Church Rides Monitoring Service.
"""

        msg.attach(MIMEText(text_body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[{get_timestamp()}] Alert email sent to {ALERT_EMAIL}")
        last_alert_time = datetime.now().timestamp()
        return True

    except Exception as e:
        print(f"[{get_timestamp()}] Error sending email: {e}")
        return False


def send_recovery_email():
    """Send recovery notification email."""
    if not SMTP_USERNAME or not ALERT_EMAIL:
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

---
This is an automated notification from the Church Rides Monitoring Service.
"""

        msg.attach(MIMEText(text_body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[{get_timestamp()}] Recovery email sent to {ALERT_EMAIL}")
        return True

    except Exception as e:
        print(f"[{get_timestamp()}] Error sending recovery email: {e}")
        return False


def should_send_alert():
    """Check if enough time has passed since last alert."""
    if last_alert_time is None:
        return True

    time_since_last = datetime.now().timestamp() - last_alert_time
    return time_since_last >= ALERT_COOLDOWN


def scheduled_health_check():
    """
    Scheduled task that runs periodically to check website health.
    This is called by APScheduler.
    """
    global consecutive_failures, was_down

    print(f"[{get_timestamp()}] Running scheduled health check...")

    is_healthy = check_website_health()

    if is_healthy:
        print(f"[{get_timestamp()}] ✓ Website is healthy")

        # If it was down and now recovered, send recovery email
        if was_down:
            print(f"[{get_timestamp()}] Service recovered! Sending notification...")
            send_recovery_email()
            was_down = False

        consecutive_failures = 0

    else:
        consecutive_failures += 1
        print(f"[{get_timestamp()}] ✗ Website check failed ({consecutive_failures}/{FAILURE_THRESHOLD})")

        # Send alert if threshold reached and cooldown period has passed
        if consecutive_failures >= FAILURE_THRESHOLD and should_send_alert():
            print(f"[{get_timestamp()}] Failure threshold reached! Retrieving ride data...")
            rides_data = get_rides_data()

            print(f"[{get_timestamp()}] Sending alert email...")
            if send_alert_email(rides_data):
                was_down = True


def init_scheduler(app):
    """
    Initialize APScheduler with the Flask app.
    Call this from your app.py to start the monitoring.
    """
    if os.environ.get('DISABLE_WATCHDOG') == 'true':
        print("Watchdog monitoring is disabled")
        return

    scheduler = BackgroundScheduler()

    # Schedule the health check to run every X minutes
    scheduler.add_job(
        func=scheduled_health_check,
        trigger=IntervalTrigger(minutes=CHECK_INTERVAL_MINUTES),
        id='website_health_check',
        name='Check website health and send alerts',
        replace_existing=True
    )

    scheduler.start()

    print(f"[{get_timestamp()}] Watchdog monitoring started")
    print(f"Checking {WEBSITE_URL} every {CHECK_INTERVAL_MINUTES} minutes")
    print(f"Alert email: {ALERT_EMAIL}")

    # Run one check immediately on startup
    scheduled_health_check()

    # Shut down scheduler when app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())

    return scheduler
