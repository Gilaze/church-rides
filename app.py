import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection, init_db
from models import User
from notifications import send_reminder_email

# --- NEW CODE BLOCK START ---
# Run this immediately when the app loads, so tables are created on Leapcell
try:
    print("Initializing Database...")
    init_db()
    print("Database Initialized!")

    # ONE-TIME MIGRATION: Move capacity from vehicles to users
    # TODO: Remove this block after successful deployment
    import psycopg2
    from psycopg2.extras import RealDictCursor
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Add driver_capacity column to users if it doesn't exist
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users' AND column_name='driver_capacity';
        """)
        if not cur.fetchone():
            print("Running migration: Adding driver_capacity column to users...")
            cur.execute("ALTER TABLE users ADD COLUMN driver_capacity INTEGER;")

            # Migrate existing data
            cur.execute("""
                UPDATE users
                SET driver_capacity = (
                    SELECT COALESCE(MAX(capacity), 0)
                    FROM vehicles
                    WHERE vehicles.driver_id = users.id
                )
                WHERE is_driver = TRUE;
            """)
            conn.commit()
            print("✓ Driver capacity migration completed!")

        # Remove capacity column from vehicles if it exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='vehicles' AND column_name='capacity';
        """)
        if cur.fetchone():
            print("Running migration: Removing capacity column from vehicles...")
            cur.execute("ALTER TABLE vehicles DROP COLUMN capacity;")
            conn.commit()
            print("✓ Vehicle capacity column removed!")

        cur.close()
        conn.close()
except Exception as e:
    print(f"Error during initialization/migration: {e}")
# --- NEW CODE BLOCK END ---

app = Flask(__name__)
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
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # Use the correct placeholder based on database type
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Get all vehicles with driver capacity
        cur.execute("SELECT v.id, v.vehicle_name, v.driver_id, u.full_name as driver_name, u.driver_capacity FROM vehicles v JOIN users u ON v.driver_id = u.id")
        vehicles = cur.fetchall()

        # Group vehicles by driver to calculate total passengers per driver
        driver_totals = {}
        vehicles_data = []

        for v in vehicles:
            driver_id = v['driver_id']

            # Get passengers for this vehicle
            cur.execute(f"SELECT u.full_name, u.id FROM bookings b JOIN users u ON b.passenger_id = u.id WHERE b.vehicle_id = {placeholder}", (v['id'],))
            passengers = cur.fetchall()

            # Track total passengers for this driver across all vehicles
            if driver_id not in driver_totals:
                driver_totals[driver_id] = 0
            driver_totals[driver_id] += len(passengers)

            # Check if driver is at capacity (affects ALL their vehicles)
            driver_capacity = v['driver_capacity'] or 0
            is_driver_full = driver_totals[driver_id] >= driver_capacity

            vehicles_data.append({
                'id': v['id'],
                'name': v['vehicle_name'],
                'driver': v['driver_name'],
                'driver_id': driver_id,
                'driver_capacity': driver_capacity,
                'driver_total_passengers': driver_totals[driver_id],
                'passengers': passengers,
                'is_full': is_driver_full
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
            # Get vehicle and driver info
            cur.execute(f"SELECT v.driver_id, u.driver_capacity FROM vehicles v JOIN users u ON v.driver_id = u.id WHERE v.id = {placeholder}", (vehicle_id,))
            vehicle = cur.fetchone()

            if not vehicle:
                flash("Vehicle not found.")
                return redirect(url_for('index'))

            driver_id = vehicle['driver_id']
            driver_capacity = vehicle['driver_capacity'] or 0

            # Count total passengers across ALL vehicles for this driver
            cur.execute(f"""
                SELECT COUNT(*) as count FROM bookings b
                JOIN vehicles v ON b.vehicle_id = v.id
                WHERE v.driver_id = {placeholder}
            """, (driver_id,))
            count_result = cur.fetchone()
            current_count = count_result['count'] if count_result else 0

            if current_count >= driver_capacity:
                flash("This driver is at full capacity.")
            else:
                cur.execute(f"INSERT INTO bookings (passenger_id, vehicle_id) VALUES ({placeholder}, {placeholder})", (current_user.id, vehicle_id))
                conn.commit()
                flash("You've been added to the ride!")

                # TRIGGER NOTIFICATION (Mock)
                send_reminder_email(current_user.username, "The Driver", "The Car")
    except Exception as e:
        print(f"Join ride error: {e}")
        flash(f"Error joining ride: {str(e)}")
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
        grade = request.form['grade']
        is_driver = 'is_driver' in request.form
        register_as_admin = 'register_as_admin' in request.form

        # Check admin password if user is trying to register as admin
        if register_as_admin:
            admin_password = request.form.get('admin_password', '')
            if admin_password != 'berkeley':
                flash("Invalid admin password. Registration failed.")
                return redirect(url_for('register'))

        hashed = generate_password_hash(pwd)

        conn = get_db_connection()
        cur = conn.cursor()

        # Use the correct placeholder based on database type
        placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

        try:
            # Get driver capacity if user is a driver
            driver_capacity = None
            if is_driver and request.form.get('driver_capacity'):
                driver_capacity = int(request.form['driver_capacity'])

            cur.execute(f"INSERT INTO users (username, password_hash, full_name, grade, is_driver, is_admin, driver_capacity) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})",
                        (username, hashed, name, grade, is_driver, register_as_admin, driver_capacity))
            conn.commit()

            # If user is a driver and provided vehicle info, create vehicle
            if is_driver and request.form.get('vehicle_name'):
                vehicle_name = request.form['vehicle_name']

                # Get the newly created user's ID
                cur.execute(f"SELECT id FROM users WHERE username = {placeholder}", (username,))
                user_id = cur.fetchone()['id']

                cur.execute(f"INSERT INTO vehicles (driver_id, vehicle_name, remember_vehicle) VALUES ({placeholder}, {placeholder}, {placeholder})",
                            (user_id, vehicle_name, False))
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
                # Get admin status from database
                is_admin = user.get('is_admin', False)

                user_obj = User(user['id'], user['username'], user['full_name'], user['is_driver'], is_admin)
                remember = 'remember' in request.form
                login_user(user_obj, remember=remember)
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

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Admin access required.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Get all passengers (non-drivers)
        cur.execute(f"SELECT full_name, grade FROM users WHERE is_driver = {placeholder} OR is_driver IS NULL", (False,))
        passengers = cur.fetchall()

        # Get all drivers
        cur.execute(f"SELECT full_name, grade FROM users WHERE is_driver = {placeholder}", (True,))
        drivers = cur.fetchall()

        # Get all vehicles with driver info
        cur.execute("SELECT v.vehicle_name, u.full_name as driver_name, u.driver_capacity FROM vehicles v JOIN users u ON v.driver_id = u.id")
        vehicles = cur.fetchall()

        return render_template('admin_dashboard.html', passengers=passengers, drivers=drivers, vehicles=vehicles)
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash("Error loading admin dashboard.")
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/become_admin', methods=['POST'])
@login_required
def become_admin():
    admin_password = request.form.get('admin_password', '')

    if admin_password != 'berkeley':
        flash("Invalid admin password.")
        return redirect(url_for('profile'))

    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Update user's admin status in database
        cur.execute(f"UPDATE users SET is_admin = {placeholder} WHERE id = {placeholder}",
                    (True, current_user.id))
        conn.commit()

        # Update current_user object
        current_user.is_admin = True

        flash("You are now an admin!")
    except Exception as e:
        print(f"Become admin error: {e}")
        flash("Error upgrading to admin. Please try again.")
    finally:
        conn.close()

    return redirect(url_for('profile'))

# --- VEHICLE MANAGEMENT ROUTES ---

@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if not current_user.is_driver:
        flash("Only drivers can add vehicles.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        if request.method == 'POST':
            vehicle_name = request.form['vehicle_name']
            remember_vehicle = 'remember_vehicle' in request.form

            cur.execute(f"INSERT INTO vehicles (driver_id, vehicle_name, remember_vehicle) VALUES ({placeholder}, {placeholder}, {placeholder})",
                        (current_user.id, vehicle_name, remember_vehicle))
            conn.commit()
            flash("Vehicle added successfully!")
            return redirect(url_for('index'))
    except Exception as e:
        print(f"Add vehicle error: {e}")
        flash("Error adding vehicle. Please try again.")
    finally:
        conn.close()

    return render_template('add_vehicle.html')

@app.route('/remove_vehicle/<int:vehicle_id>')
@login_required
def remove_vehicle(vehicle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Get vehicle info
        cur.execute(f"SELECT driver_id FROM vehicles WHERE id = {placeholder}", (vehicle_id,))
        vehicle = cur.fetchone()

        if not vehicle:
            flash("Vehicle not found.")
            return redirect(url_for('index'))

        # Check if user owns this vehicle or is admin
        if vehicle['driver_id'] != current_user.id and not current_user.is_admin:
            flash("You can only remove your own vehicle.")
            return redirect(url_for('index'))

        # Delete all bookings for this vehicle first
        cur.execute(f"DELETE FROM bookings WHERE vehicle_id = {placeholder}", (vehicle_id,))

        # Delete the vehicle
        cur.execute(f"DELETE FROM vehicles WHERE id = {placeholder}", (vehicle_id,))
        conn.commit()
        flash("Vehicle removed successfully!")
    except Exception as e:
        print(f"Remove vehicle error: {e}")
        flash("Error removing vehicle. Please try again.")
    finally:
        conn.close()

    return redirect(url_for('index'))

@app.route('/remove_passenger/<int:vehicle_id>/<int:passenger_id>')
@login_required
def remove_passenger(vehicle_id, passenger_id):
    # Only admins or the passenger themselves can remove a passenger
    if not current_user.is_admin and current_user.id != passenger_id:
        flash("You don't have permission to remove this passenger.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        cur.execute(f"DELETE FROM bookings WHERE passenger_id = {placeholder} AND vehicle_id = {placeholder}",
                    (passenger_id, vehicle_id))
        conn.commit()
        flash("Passenger removed successfully!")
    except Exception as e:
        print(f"Remove passenger error: {e}")
        flash("Error removing passenger. Please try again.")
    finally:
        conn.close()

    return redirect(url_for('index'))

# --- ACCOUNT MANAGEMENT ROUTES ---

@app.route('/upgrade_to_driver', methods=['GET', 'POST'])
@login_required
def upgrade_to_driver():
    if current_user.is_driver:
        flash("You are already a driver.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

        try:
            # Get driver capacity from form
            driver_capacity = int(request.form.get('driver_capacity', 0))

            # Update user to driver
            cur.execute(f"UPDATE users SET is_driver = {placeholder}, driver_capacity = {placeholder} WHERE id = {placeholder}",
                        (True, driver_capacity, current_user.id))
            conn.commit()

            # Update current_user object
            current_user.is_driver = True

            flash("You are now a driver! You can add your vehicle.")
            return redirect(url_for('add_vehicle'))
        except Exception as e:
            print(f"Upgrade to driver error: {e}")
            flash("Error upgrading account. Please try again.")
        finally:
            conn.close()

    return render_template('upgrade_to_driver.html')

@app.route('/downgrade_to_passenger', methods=['POST'])
@login_required
def downgrade_to_passenger():
    if not current_user.is_driver:
        flash("You are already a passenger.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # First, find and delete any vehicle owned by this driver
        cur.execute(f"SELECT id FROM vehicles WHERE driver_id = {placeholder}", (current_user.id,))
        vehicle = cur.fetchone()

        if vehicle:
            # Delete all bookings for this vehicle
            cur.execute(f"DELETE FROM bookings WHERE vehicle_id = {placeholder}", (vehicle['id'],))
            # Delete the vehicle
            cur.execute(f"DELETE FROM vehicles WHERE id = {placeholder}", (vehicle['id'],))

        # Update user to passenger
        cur.execute(f"UPDATE users SET is_driver = {placeholder} WHERE id = {placeholder}",
                    (False, current_user.id))
        conn.commit()

        # Update current_user object
        current_user.is_driver = False

        flash("You are now a passenger. Your vehicle has been removed.")
    except Exception as e:
        print(f"Downgrade to passenger error: {e}")
        flash("Error changing account status. Please try again.")
    finally:
        conn.close()

    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        grade = request.form['grade']
        password = request.form.get('password', '').strip()

        try:
            # Update user information including driver capacity
            driver_capacity = None
            if current_user.is_driver and request.form.get('driver_capacity'):
                driver_capacity = int(request.form['driver_capacity'])

            # Check if password is being updated
            if password:
                # Update with new password
                hashed = generate_password_hash(password)
                cur.execute(f"UPDATE users SET full_name = {placeholder}, username = {placeholder}, grade = {placeholder}, driver_capacity = {placeholder}, password_hash = {placeholder} WHERE id = {placeholder}",
                            (full_name, username, grade, driver_capacity, hashed, current_user.id))
            else:
                # Update without changing password
                cur.execute(f"UPDATE users SET full_name = {placeholder}, username = {placeholder}, grade = {placeholder}, driver_capacity = {placeholder} WHERE id = {placeholder}",
                            (full_name, username, grade, driver_capacity, current_user.id))
            conn.commit()

            # Update all vehicles if user is a driver
            if current_user.is_driver:
                # Get all vehicle IDs and their updates from the form
                for key in request.form:
                    if key.startswith('vehicle_name_'):
                        vehicle_id = int(key.split('_')[-1])
                        vehicle_name = request.form[f'vehicle_name_{vehicle_id}']
                        remember_vehicle = f'remember_vehicle_{vehicle_id}' in request.form

                        cur.execute(f"UPDATE vehicles SET vehicle_name = {placeholder}, remember_vehicle = {placeholder} WHERE id = {placeholder} AND driver_id = {placeholder}",
                                    (vehicle_name, remember_vehicle, vehicle_id, current_user.id))
                conn.commit()

            # Update current_user object
            current_user.full_name = full_name
            current_user.username = username

            flash("Profile updated successfully!")
            return redirect(url_for('profile'))
        except Exception as e:
            print(f"Profile update error: {e}")
            flash("Error updating profile. Username may already be taken.")
        finally:
            conn.close()

    # GET request - fetch user data
    try:
        cur.execute(f"SELECT username, grade, driver_capacity FROM users WHERE id = {placeholder}", (current_user.id,))
        user_data = cur.fetchone()

        vehicles_data = []
        if current_user.is_driver:
            cur.execute(f"SELECT id, vehicle_name, remember_vehicle FROM vehicles WHERE driver_id = {placeholder}", (current_user.id,))
            vehicles_data = cur.fetchall()

        return render_template('profile.html', user_data=user_data, vehicles_data=vehicles_data)
    except Exception as e:
        print(f"Profile load error: {e}")
        flash("Error loading profile.")
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/demote_admin', methods=['POST'])
@login_required
def demote_admin():
    if not current_user.is_admin:
        flash("You are not an admin.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Update user to non-admin
        cur.execute(f"UPDATE users SET is_admin = {placeholder} WHERE id = {placeholder}",
                    (False, current_user.id))
        conn.commit()

        # Update current_user object
        current_user.is_admin = False

        flash("Admin privileges removed.")
    except Exception as e:
        print(f"Demote admin error: {e}")
        flash("Error removing admin privileges. Please try again.")
    finally:
        conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    # Initialize DB tables if they don't exist
    try:
        init_db() 
    except Exception as e:
        print(f"DB Init Warning (ignore if using existing DB): {e}")
    app.run(debug=True)