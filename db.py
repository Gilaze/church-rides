import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager
import time

# PostgreSQL connection pool for production (prevents connection exhaustion)
_pg_pool = None

def _get_pg_pool():
    """Get or create PostgreSQL connection pool (singleton pattern)"""
    global _pg_pool
    if _pg_pool is None:
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Create connection pool with 2-10 connections
            # Leapcell free tier can handle this range
            _pg_pool = pool.SimpleConnectionPool(
                minconn=2,  # Minimum connections
                maxconn=10,  # Maximum connections (safe for free tier)
                dsn=database_url,
                cursor_factory=RealDictCursor,
                connect_timeout=10,
                options='-c statement_timeout=30000'
            )
    return _pg_pool

def get_db_connection():
    """Get database connection with retry logic for SQLite locking issues"""
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Production (Leapcell/PostgreSQL) - use connection pooling
        pg_pool = _get_pg_pool()
        if pg_pool:
            try:
                conn = pg_pool.getconn()
                return conn
            except pool.PoolError:
                # Pool exhausted, fall back to direct connection
                return psycopg2.connect(
                    database_url,
                    cursor_factory=RealDictCursor,
                    connect_timeout=10,
                    options='-c statement_timeout=30000'
                )
    else:
        # Development (Local SQLite) - with retry logic for rapid clicks
        max_retries = 5
        retry_delay = 0.1  # 100ms between retries

        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(
                    'church_ride.db',
                    timeout=30,  # Increased from 10 to 30 seconds
                    isolation_level='DEFERRED',  # Less aggressive locking
                    check_same_thread=False  # Allow multi-threaded access
                )
                conn.row_factory = sqlite3.Row
                # Enable WAL mode for better concurrent access
                conn.execute('PRAGMA journal_mode=WAL')
                return conn
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    # Database locked, retry after brief delay
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    # Max retries exceeded or different error
                    raise

    return conn

def release_db_connection(conn):
    """Properly release database connection back to pool or close it"""
    database_url = os.environ.get('DATABASE_URL')

    if database_url and _pg_pool:
        # Return connection to pool
        try:
            _pg_pool.putconn(conn)
        except:
            # If pool is full or error, just close it
            try:
                conn.close()
            except:
                pass
    else:
        # SQLite - just close normally
        try:
            conn.close()
        except:
            pass

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
            phone_number VARCHAR(20),
            email VARCHAR(100),
            driver_capacity INTEGER,
            residence VARCHAR(100)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id SERIAL PRIMARY KEY,
            driver_id INTEGER REFERENCES users(id),
            vehicle_name VARCHAR(50),
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
            phone_number TEXT,
            email TEXT,
            driver_capacity INTEGER,
            residence TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER REFERENCES users(id),
            vehicle_name TEXT,
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

@contextmanager
def get_db():
    """Context manager for database connections - ensures proper cleanup"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except:
            pass