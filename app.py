import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection, init_db, release_db_connection
from models import User

# Watchdog monitoring is now handled externally
WATCHDOG_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'f557d923d5679644c2b94cd0ad194313')

# Initialize database tables only in local development (SQLite)
# In production (Leapcell/serverless), skip to avoid cold start overhead
if not os.environ.get('DATABASE_URL'):
    # Local development with SQLite - auto-create tables
    print("🔧 Initializing local SQLite database...")
    try:
        init_db()
        print("✅ Local database initialized")
    except Exception as e:
        print(f"⚠️ DB Init: {e}")
else:
    # Production (PostgreSQL) - tables already exist, skip init for performance
    print("✅ Using production database (skipping init for serverless optimization)")

# Force HTTPS in production
@app.before_request
def force_https():
    if os.environ.get('DATABASE_URL'):  # Only in production
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

# Security Headers - Make website appear safe to antivirus/browsers
@app.after_request
def set_security_headers(response):
    # Prevent clickjacking attacks
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    # Prevent XSS attacks
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Enable browser XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Only send referrer for same-origin requests
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Content Security Policy - prevents malicious scripts
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https:; img-src 'self' data: https:;"

    # Force HTTPS for 1 year (only if using HTTPS)
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    return response

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Watchdog monitoring is handled externally by Railway service
# No integrated watchdog needed - Railway monitors from outside

# --- ROUTES ---

@app.route('/')
def index():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # OPTIMIZED: Single query with JOIN to get all data at once (eliminates N+1 query problem)
        cur.execute("""
            SELECT
                v.id as vehicle_id,
                v.vehicle_name,
                v.driver_id,
                u.full_name as driver_name,
                u.phone_number as driver_phone,
                u.driver_capacity,
                p.full_name as passenger_name,
                p.id as passenger_id
            FROM vehicles v
            JOIN users u ON v.driver_id = u.id
            LEFT JOIN bookings b ON b.vehicle_id = v.id
            LEFT JOIN users p ON b.passenger_id = p.id
            ORDER BY u.full_name, v.vehicle_name, p.full_name
        """)
        rows = cur.fetchall()

        # Process results into structured data
        vehicles_dict = {}
        driver_totals = {}

        for row in rows:
            vehicle_id = row['vehicle_id']
            driver_id = row['driver_id']

            # Initialize vehicle if not seen before
            if vehicle_id not in vehicles_dict:
                vehicles_dict[vehicle_id] = {
                    'id': vehicle_id,
                    'name': row['vehicle_name'],
                    'driver': row['driver_name'],
                    'driver_phone': row['driver_phone'],
                    'driver_id': driver_id,
                    'driver_capacity': row['driver_capacity'] or 0,
                    'passengers': []
                }
                driver_totals[driver_id] = 0

            # Add passenger if exists
            if row['passenger_id']:
                passenger = {
                    'full_name': row['passenger_name'],
                    'id': row['passenger_id']
                }
                # Avoid duplicates (in case of data issues)
                if passenger not in vehicles_dict[vehicle_id]['passengers']:
                    vehicles_dict[vehicle_id]['passengers'].append(passenger)
                    driver_totals[driver_id] += 1

        # Add driver totals and capacity check to each vehicle
        vehicles_data = []
        for vehicle in vehicles_dict.values():
            driver_id = vehicle['driver_id']
            driver_total = driver_totals.get(driver_id, 0)
            vehicle['driver_total_passengers'] = driver_total
            vehicle['is_full'] = driver_total >= vehicle['driver_capacity']
            vehicles_data.append(vehicle)

        return render_template('index.html', vehicles=vehicles_data)
    except Exception as e:
        print(f"Index route error: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
        flash("Error loading rides. Please try again.")
        return render_template('index.html', vehicles=[])
    finally:
        if conn:
            release_db_connection(conn)

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
    except Exception as e:
        print(f"Join ride error: {e}")
        flash(f"Error joining ride: {str(e)}")
    finally:
        release_db_connection(conn)

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
        release_db_connection(conn)

    return redirect(url_for('index'))

# --- AUTH ROUTES (Login/Register) --- 

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        name = request.form['full_name']
        grade = request.form.get('grade', '').strip() or None
        residence = request.form.get('residence', '').strip() or None
        phone_number = request.form.get('phone_number', '').strip() or None
        email = request.form.get('email', '').strip() or None
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

            cur.execute(f"INSERT INTO users (username, password_hash, full_name, grade, residence, phone_number, email, is_driver, is_admin, driver_capacity) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})",
                        (username, hashed, name, grade, residence, phone_number, email, is_driver, register_as_admin, driver_capacity))
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

            release_db_connection(conn)
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            release_db_connection(conn)
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
            release_db_connection(conn)

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
        # Get all passengers who have active bookings with their driver info
        cur.execute("""
            SELECT u.full_name, u.residence, u.email, d.full_name as driver_name
            FROM users u
            JOIN bookings b ON u.id = b.passenger_id
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN users d ON v.driver_id = d.id
            ORDER BY d.full_name, u.full_name
        """)
        passengers = cur.fetchall()

        # Get all drivers who have active vehicles
        cur.execute("""
            SELECT DISTINCT u.full_name, u.grade, u.phone_number
            FROM users u
            JOIN vehicles v ON u.id = v.driver_id
            WHERE u.is_driver = TRUE
            ORDER BY u.full_name
        """)
        drivers = cur.fetchall()

        # Get all users
        cur.execute("SELECT full_name, grade, residence, phone_number, email FROM users ORDER BY full_name")
        all_users = cur.fetchall()

        # OPTIMIZED: Single query with GROUP BY to get vehicle capacity (eliminates N+1 query problem)
        cur.execute("""
            SELECT
                v.vehicle_name,
                v.driver_id,
                d.full_name as driver_name,
                d.driver_capacity,
                COUNT(b.id) as driver_occupied
            FROM vehicles v
            JOIN users d ON v.driver_id = d.id
            LEFT JOIN bookings b ON b.vehicle_id = v.id
            GROUP BY v.id, v.vehicle_name, v.driver_id, d.full_name, d.driver_capacity
            ORDER BY d.full_name, v.vehicle_name
        """)
        vehicles = cur.fetchall()

        return render_template('admin_dashboard.html', passengers=passengers, drivers=drivers, vehicles=vehicles, all_users=all_users)
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash("Error loading admin dashboard.")
        return redirect(url_for('index'))
    finally:
        release_db_connection(conn)

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
        release_db_connection(conn)

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
        release_db_connection(conn)

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
        release_db_connection(conn)

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
        release_db_connection(conn)

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
            release_db_connection(conn)

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
        release_db_connection(conn)

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
        residence = request.form['residence']
        phone_number = request.form.get('phone_number', '').strip() or None
        email = request.form.get('email', '').strip() or None
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
                cur.execute(f"UPDATE users SET full_name = {placeholder}, username = {placeholder}, grade = {placeholder}, residence = {placeholder}, phone_number = {placeholder}, email = {placeholder}, driver_capacity = {placeholder}, password_hash = {placeholder} WHERE id = {placeholder}",
                            (full_name, username, grade, residence, phone_number, email, driver_capacity, hashed, current_user.id))
            else:
                # Update without changing password
                cur.execute(f"UPDATE users SET full_name = {placeholder}, username = {placeholder}, grade = {placeholder}, residence = {placeholder}, phone_number = {placeholder}, email = {placeholder}, driver_capacity = {placeholder} WHERE id = {placeholder}",
                            (full_name, username, grade, residence, phone_number, email, driver_capacity, current_user.id))
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
            release_db_connection(conn)

    # GET request - fetch user data
    try:
        cur.execute(f"SELECT username, grade, residence, phone_number, email, driver_capacity FROM users WHERE id = {placeholder}", (current_user.id,))
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
        release_db_connection(conn)

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
        release_db_connection(conn)

    return redirect(url_for('index'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    confirm_username = request.form.get('confirm_username', '').strip()
    confirm_password = request.form.get('confirm_password', '')

    # Verify username matches
    if confirm_username != current_user.username:
        flash("Username does not match. Account deletion cancelled.")
        return redirect(url_for('profile'))

    # Verify password is correct
    conn = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if os.environ.get('DATABASE_URL') else "?"

    try:
        # Get user's password hash
        cur.execute(f"SELECT password_hash FROM users WHERE id = {placeholder}", (current_user.id,))
        user_row = cur.fetchone()

        if not user_row or not check_password_hash(user_row['password_hash'], confirm_password):
            flash("Incorrect password. Account deletion cancelled.")
            return redirect(url_for('profile'))

        # Delete all bookings where user is a passenger
        cur.execute(f"DELETE FROM bookings WHERE passenger_id = {placeholder}", (current_user.id,))

        # If user is a driver, remove all passengers from their vehicles and delete vehicles
        if current_user.is_driver:
            # Get all vehicle IDs for this driver
            cur.execute(f"SELECT id FROM vehicles WHERE driver_id = {placeholder}", (current_user.id,))
            vehicle_rows = cur.fetchall()

            for vehicle_row in vehicle_rows:
                vehicle_id = vehicle_row['id']
                # Delete all bookings for this vehicle
                cur.execute(f"DELETE FROM bookings WHERE vehicle_id = {placeholder}", (vehicle_id,))

            # Delete all vehicles owned by this user
            cur.execute(f"DELETE FROM vehicles WHERE driver_id = {placeholder}", (current_user.id,))

        # Finally, delete the user account
        cur.execute(f"DELETE FROM users WHERE id = {placeholder}", (current_user.id,))

        conn.commit()

        # Log the user out
        logout_user()

        flash("Your account has been permanently deleted. We're sorry to see you go.")
        return redirect(url_for('index'))

    except Exception as e:
        conn.rollback()
        print(f"Delete account error: {e}")
        flash("An error occurred while deleting your account. Please try again or contact support.")
        return redirect(url_for('profile'))
    finally:
        release_db_connection(conn)

# --- SECURITY & SEO ROUTES ---

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt to establish legitimacy with search engines"""
    return app.send_static_file('robots.txt')

@app.route('/.well-known/security.txt')
def security_txt():
    """Serve security.txt to show responsible security practices"""
    return app.send_static_file('.well-known/security.txt')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring services"""
    return {'status': 'healthy', 'service': 'church-rides'}, 200

@app.route('/privacy')
def privacy():
    """Privacy policy page - establishes trust with users and antivirus"""
    return render_template('privacy.html')

if __name__ == '__main__':
    # DB already initialized at module level (line 18)
    # No need to initialize again here
    app.run(debug=True)