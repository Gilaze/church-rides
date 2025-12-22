import smtplib

def send_reminder_email(user_email, driver_name, vehicle_name):
    # This is a MOCK function. 
    # To make it real, you need a sender email and app password.
    print(f"--- SIMULATING EMAIL ---")
    print(f"To: {user_email}")
    print(f"Subject: Church Ride Reminder")
    print(f"Body: Don't forget! You are riding with {driver_name} in the {vehicle_name} tomorrow.")
    print("------------------------")
    return True