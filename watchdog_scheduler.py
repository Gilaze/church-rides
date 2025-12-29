"""
Watchdog script that checks the health of the church-rides website.
If the website is down, sends an email with all rides and passengers.
"""
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from db import get_db_connection

def check_website_health(url, timeout=10):
    """
    Check if the website is responding to requests.

    Args:
        url: The URL to check
        timeout: Request timeout in seconds

    Returns:
        tuple: (is_healthy: bool, status_message: str)
    """
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, f"Website is healthy (HTTP {response.status_code})"
        else:
            return False, f"Website returned HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, f"Website request timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to website (connection error)"
    except Exception as e:
        return False, f"Error checking website: {str(e)}"

def get_all_rides_data():
    """
    Fetch all rides and passengers from the database.

    Returns:
        list: List of dictionaries containing ride information
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Use the correct placeholder based on database type
        placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

        # Get all vehicles with driver information
        cur.execute("""
            SELECT v.id, v.vehicle_name, v.driver_id,
                   u.full_name as driver_name,
                   u.phone_number as driver_phone,
                   u.email as driver_email,
                   u.driver_capacity
            FROM vehicles v
            JOIN users u ON v.driver_id = u.id
            ORDER BY u.full_name
        """)
        vehicles = cur.fetchall()

        rides_data = []

        for vehicle in vehicles:
            vehicle_id = vehicle['id']

            # Get passengers for this vehicle
            cur.execute(f"""
                SELECT u.full_name, u.phone_number, u.email, u.residence
                FROM bookings b
                JOIN users u ON b.passenger_id = u.id
                WHERE b.vehicle_id = {placeholder}
                ORDER BY u.full_name
            """, (vehicle_id,))
            passengers = cur.fetchall()

            rides_data.append({
                'vehicle_name': vehicle['vehicle_name'],
                'driver_name': vehicle['driver_name'],
                'driver_phone': vehicle['driver_phone'],
                'driver_email': vehicle['driver_email'],
                'driver_capacity': vehicle['driver_capacity'],
                'passengers': [
                    {
                        'name': p['full_name'],
                        'phone': p['phone_number'],
                        'email': p['email'],
                        'residence': p['residence']
                    }
                    for p in passengers
                ]
            })

        return rides_data
    finally:
        conn.close()

def format_rides_email(rides_data, status_message):
    """
    Format ride data into an HTML email.

    Args:
        rides_data: List of ride dictionaries
        status_message: The error message from the health check

    Returns:
        str: HTML formatted email body
    """
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #d9534f; }}
            h2 {{ color: #333; margin-top: 20px; }}
            .ride {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
            .driver-info {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 10px; }}
            .passenger {{ margin-left: 20px; padding: 5px; }}
            .alert {{ background-color: #f2dede; border: 1px solid #ebccd1; color: #a94442; padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h1>⚠️ Church Rides Website Down - Backup Data</h1>
        <div class="alert">
            <strong>Status:</strong> {status_message}
        </div>

        <p>The church-rides website health check failed. Below is a complete backup of all current rides and passengers.</p>

        <h2>Total Rides: {len(rides_data)}</h2>
    """

    if not rides_data:
        html += "<p><em>No rides currently scheduled.</em></p>"
    else:
        for ride in rides_data:
            passenger_count = len(ride['passengers'])
            capacity = ride['driver_capacity'] or 'Not set'

            html += f"""
            <div class="ride">
                <h3>{ride['vehicle_name']}</h3>
                <div class="driver-info">
                    <strong>Driver:</strong> {ride['driver_name']}<br>
                    <strong>Phone:</strong> {ride['driver_phone'] or 'Not provided'}<br>
                    <strong>Email:</strong> {ride['driver_email'] or 'Not provided'}<br>
                    <strong>Capacity:</strong> {passenger_count} / {capacity} passengers
                </div>
                <strong>Passengers ({passenger_count}):</strong>
            """

            if not ride['passengers']:
                html += "<p class='passenger'><em>No passengers yet</em></p>"
            else:
                for passenger in ride['passengers']:
                    html += f"""
                    <div class="passenger">
                        • <strong>{passenger['name']}</strong>
                        {f" - {passenger['residence']}" if passenger['residence'] else ""}
                        {f" - {passenger['phone']}" if passenger['phone'] else ""}
                        {f" - {passenger['email']}" if passenger['email'] else ""}
                    </div>
                    """

            html += "</div>"

    html += """
        <hr>
        <p style="color: #666; font-size: 12px;">
            This is an automated alert from the Church Rides Watchdog service.
            This email is sent when the website health check fails.
        </p>
    </body>
    </html>
    """

    return html

def send_email(recipient_email, subject, html_body):
    """
    Send an email using SMTP.

    Args:
        recipient_email: Email address to send to
        subject: Email subject
        html_body: HTML content of the email

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_password = os.environ.get('SENDER_PASSWORD')

    if not sender_email or not sender_password:
        print("ERROR: SENDER_EMAIL or SENDER_PASSWORD environment variables not set")
        return False

    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = recipient_email

        # Attach HTML content
        html_part = MIMEText(html_body, 'html')
        message.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)

        print(f"✅ Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

def main():
    """Main function to run the watchdog check."""
    website_url = os.environ.get('WEBSITE_URL', 'https://church-rides.up.railway.app/health')
    recipient_email = os.environ.get('ALERT_EMAIL')

    if not recipient_email:
        print("ERROR: ALERT_EMAIL environment variable not set")
        sys.exit(1)

    print(f"🔍 Checking website health: {website_url}")

    # Check website health
    is_healthy, status_message = check_website_health(website_url)

    if is_healthy:
        print(f"✅ {status_message}")
        print("No action needed - website is healthy")
        sys.exit(0)
    else:
        print(f"❌ {status_message}")
        print("Website is down! Sending alert email...")

        # Get all rides data
        try:
            rides_data = get_all_rides_data()
            print(f"📊 Retrieved {len(rides_data)} rides from database")
        except Exception as e:
            print(f"❌ Error fetching rides data: {str(e)}")
            sys.exit(1)

        # Format and send email
        html_body = format_rides_email(rides_data, status_message)
        subject = f"🚨 Church Rides Website Alert - {status_message}"

        success = send_email(recipient_email, subject, html_body)

        if success:
            print("✅ Alert email sent successfully")
            sys.exit(0)
        else:
            print("❌ Failed to send alert email")
            sys.exit(1)

if __name__ == '__main__':
    main()
