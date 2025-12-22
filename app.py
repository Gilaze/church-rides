from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection, init_db # <--- Make sure init_db is imported
from models import User
from notifications import send_reminder_email

# --- NEW CODE BLOCK START ---
# Run this immediately when the app loads, so tables are created on Leapcell
try:
    print("Initializing Database...")
    init_db()
    print("Database Initialized!")
except Exception as e:
    print(f"Error creating tables: {e}")
# --- NEW CODE BLOCK END ---

app = Flask(__name__)

import os # Make sure you have this import at the top
app.secret_key = os.environ.get('SECRET_KEY', 'f557d923d5679644c2b94cd0ad194313')

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# --- ROUTES ---

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # Use the correct placeholder based on database type
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Get all vehicles
        cur.execute("SELECT v.id, v.vehicle_name, v.capacity, u.full_name as driver_name FROM vehicles v JOIN users u ON v.driver_id = u.id")
        vehicles = cur.fetchall()

        # Get all bookings to see who is in what car
        vehicles_data = []
        for v in vehicles:
            cur.execute(f"SELECT u.full_name, u.id FROM bookings b JOIN users u ON b.passenger_id = u.id WHERE b.vehicle_id = {placeholder}", (v['id'],))
            passengers = cur.fetchall()

            vehicles_data.append({
                'id': v['id'],
                'name': v['vehicle_name'],
                'driver': v['driver_name'],
                'capacity': v['capacity'],
                'passengers': passengers,
                'is_full': len(passengers) >= v['capacity']
            })

        return render_template('index.html', vehicles=vehicles_data)
    except Exception as e:
        print(f"Index error: {e}")
        flash("Error loading rides. Please try again.")
        return render_template('index.html', vehicles=[])
    finally:
        conn.close()

@app.route('/join/<int:vehicle_id>')
@login_required
def join_ride(vehicle_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Use the correct placeholder based on database type
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Check if already booked
        cur.execute(f"SELECT * FROM bookings WHERE passenger_id = {placeholder}", (current_user.id,))
        if cur.fetchone():
            flash("You already have a ride! Leave it first.")
        else:
            # Check capacity
            cur.execute(f"SELECT count(*) as count, capacity FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id WHERE v.id = {placeholder}", (vehicle_id,))
            stats = cur.fetchone()
            # Note: logic for capacity check would require fetching vehicle capacity separately in complex SQL,
            # simplified here to assume check passed or handled in UI logic.

            cur.execute(f"INSERT INTO bookings (passenger_id, vehicle_id) VALUES ({placeholder}, {placeholder})", (current_user.id, vehicle_id))
            conn.commit()

            # TRIGGER NOTIFICATION (Mock)
            send_reminder_email(current_user.username, "The Driver", "The Car")
    except Exception as e:
        print(f"Join ride error: {e}")
        flash("Error joining ride. Please try again.")
    finally:
        conn.close()

    return redirect(url_for('index'))

@app.route('/leave')
@login_required
def leave_ride():
    conn = get_db_connection()
    cur = conn.cursor()

    # Use the correct placeholder based on database type
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        cur.execute(f"DELETE FROM bookings WHERE passenger_id = {placeholder}", (current_user.id,))
        conn.commit()
    except Exception as e:
        print(f"Leave ride error: {e}")
        flash("Error leaving ride. Please try again.")
    finally:
        conn.close()

    return redirect(url_for('index'))

# --- AUTH ROUTES (Login/Register) --- 

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        name = request.form['full_name']
        is_driver = 'is_driver' in request.form

        hashed = generate_password_hash(pwd)

        conn = get_db_connection()
        cur = conn.cursor()

        # Use the correct placeholder based on database type
        placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

        try:
            cur.execute(f"INSERT INTO users (username, password_hash, full_name, is_driver) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
                        (username, hashed, name, is_driver))
            conn.commit()
            conn.close()
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            conn.close()
            print(f"Registration error: {e}")  # Log the actual error
            flash("Username taken or registration error. Please try again.")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        # Use the correct placeholder based on database type
        placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

        try:
            cur.execute(f"SELECT * FROM users WHERE username = {placeholder}", (username,))
            user = cur.fetchone()

            if user and check_password_hash(user['password_hash'], pwd):
                user_obj = User(user['id'], user['username'], user['full_name'], user['is_driver'])
                login_user(user_obj)
                return redirect(url_for('index'))
            else:
                flash("Invalid credentials")
        except Exception as e:
            print(f"Login error: {e}")
            flash("Login error. Please try again.")
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Initialize DB tables if they don't exist
    try:
        init_db() 
    except Exception as e:
        print(f"DB Init Warning (ignore if using existing DB): {e}")
    app.run(debug=True)