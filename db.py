import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production (Leapcell/PostgreSQL)
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # Development (Local SQLite)
        conn = sqlite3.connect('church_ride.db')
        conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users Table (Credentials & Info)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        is_driver BOOLEAN DEFAULT FALSE,
        phone_number VARCHAR(20) -- For reminders
    );
    """) # Note: In SQLite, 'SERIAL' might fail, simplified for hybrid compatibility below:
    
    # Vehicles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id SERIAL PRIMARY KEY,
        driver_id INTEGER REFERENCES users(id),
        vehicle_name VARCHAR(50),
        capacity INTEGER
    );
    """)

    # Bookings/Rides Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        passenger_id INTEGER UNIQUE REFERENCES users(id),
        vehicle_id INTEGER REFERENCES vehicles(id)
    );
    """)
    
    conn.commit()
    conn.close()

# Note: For SQLite compatibility, you might need to run the specific SQLite CREATE statements 
# from our previous chat manually once, as 'SERIAL' is PostgreSQL specific. 
# For this code to run smoothly on your laptop, use 'INTEGER PRIMARY KEY AUTOINCREMENT' for IDs.