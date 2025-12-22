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

    # Determine if we're using PostgreSQL or SQLite
    is_postgres = os.environ.get('DATABASE_URL') is not None

    if is_postgres:
        # PostgreSQL syntax
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            grade VARCHAR(20),
            is_driver BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE,
            phone_number VARCHAR(20)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id SERIAL PRIMARY KEY,
            driver_id INTEGER REFERENCES users(id),
            vehicle_name VARCHAR(50),
            capacity INTEGER,
            remember_vehicle BOOLEAN DEFAULT FALSE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            passenger_id INTEGER UNIQUE REFERENCES users(id),
            vehicle_id INTEGER REFERENCES vehicles(id)
        );
        """)
    else:
        # SQLite syntax
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            grade TEXT,
            is_driver INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            phone_number TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER REFERENCES users(id),
            vehicle_name TEXT,
            capacity INTEGER,
            remember_vehicle INTEGER DEFAULT 0
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_id INTEGER UNIQUE REFERENCES users(id),
            vehicle_id INTEGER REFERENCES vehicles(id)
        );
        """)

    conn.commit()
    conn.close()