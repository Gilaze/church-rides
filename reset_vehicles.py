"""
Vehicle Reset Script - Run every Monday at 12:00 AM PST
This script:
1. Clears all passenger bookings
2. Deletes vehicles that don't have 'remember_vehicle' enabled
3. Keeps vehicles with 'remember_vehicle' enabled (but clears their passengers)
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz

def reset_vehicles():
    """Reset vehicles and clear bookings every Monday at 12am PST"""

    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # PostgreSQL
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        placeholder = "%s"
    else:
        # SQLite
        conn = sqlite3.connect('church_ride.db')
        conn.row_factory = sqlite3.Row
        placeholder = "?"

    cur = conn.cursor()

    try:
        # Step 1: Delete all bookings (clear all passengers from all vehicles)
        cur.execute("DELETE FROM bookings")
        deleted_bookings = cur.rowcount
        print(f"Cleared {deleted_bookings} passenger bookings")

        # Step 2: Delete vehicles that don't have remember_vehicle enabled
        if database_url:
            # PostgreSQL
            cur.execute("DELETE FROM vehicles WHERE remember_vehicle = FALSE OR remember_vehicle IS NULL")
        else:
            # SQLite
            cur.execute("DELETE FROM vehicles WHERE remember_vehicle = 0 OR remember_vehicle IS NULL")

        deleted_vehicles = cur.rowcount
        print(f"Deleted {deleted_vehicles} vehicles (not marked as 'Remember Vehicle')")

        # Step 3: Count remaining vehicles (those with remember_vehicle enabled)
        cur.execute("SELECT COUNT(*) as count FROM vehicles")
        result = cur.fetchone()
        remaining_vehicles = result['count'] if database_url else result[0]
        print(f"Kept {remaining_vehicles} vehicles marked as 'Remember Vehicle'")

        conn.commit()

        pst = pytz.timezone('America/Los_Angeles')
        current_time = datetime.now(pst)
        print(f"Vehicle reset completed successfully at {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    except Exception as e:
        conn.rollback()
        print(f"Error during vehicle reset: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    reset_vehicles()
