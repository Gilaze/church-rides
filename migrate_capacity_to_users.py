"""
Migration: Move capacity from vehicles table to users table
- Add driver_capacity column to users table
- Migrate existing vehicle capacity data to driver capacity (use max capacity from all vehicles)
- Remove capacity column from vehicles table
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_database():
    """Migrate capacity from vehicles to users table"""
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # PostgreSQL migration
        print("Migrating PostgreSQL database...")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Step 1: Add driver_capacity column to users if it doesn't exist
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users' AND column_name='driver_capacity';
        """)
        if not cur.fetchone():
            print("Adding driver_capacity column to users table...")
            cur.execute("ALTER TABLE users ADD COLUMN driver_capacity INTEGER;")
            conn.commit()

        # Step 2: Migrate existing data - set driver capacity to max vehicle capacity they have
        print("Migrating existing capacity data from vehicles to users...")
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

        # Step 3: Remove capacity column from vehicles table
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='vehicles' AND column_name='capacity';
        """)
        if cur.fetchone():
            print("Removing capacity column from vehicles table...")
            cur.execute("ALTER TABLE vehicles DROP COLUMN capacity;")
            conn.commit()

        print("PostgreSQL migration completed successfully!")
        cur.close()
        conn.close()

    else:
        # SQLite migration
        print("Migrating SQLite database...")
        conn = sqlite3.connect('church_ride.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Step 1: Add driver_capacity column to users if it doesn't exist
        cur.execute("PRAGMA table_info(users);")
        columns = [column[1] for column in cur.fetchall()]

        if 'driver_capacity' not in columns:
            print("Adding driver_capacity column to users table...")
            cur.execute("ALTER TABLE users ADD COLUMN driver_capacity INTEGER;")
            conn.commit()

        # Step 2: Migrate existing data
        print("Migrating existing capacity data from vehicles to users...")
        cur.execute("""
            UPDATE users
            SET driver_capacity = (
                SELECT COALESCE(MAX(capacity), 0)
                FROM vehicles
                WHERE vehicles.driver_id = users.id
            )
            WHERE is_driver = 1;
        """)
        conn.commit()

        # Step 3: Remove capacity column from vehicles (SQLite doesn't support DROP COLUMN easily)
        # Need to recreate the table
        cur.execute("PRAGMA table_info(vehicles);")
        vehicle_columns = [column[1] for column in cur.fetchall()]

        if 'capacity' in vehicle_columns:
            print("Removing capacity column from vehicles table...")
            # Create new table without capacity
            cur.execute("""
                CREATE TABLE vehicles_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_id INTEGER REFERENCES users(id),
                    vehicle_name TEXT,
                    remember_vehicle INTEGER DEFAULT 0
                );
            """)

            # Copy data
            cur.execute("""
                INSERT INTO vehicles_new (id, driver_id, vehicle_name, remember_vehicle)
                SELECT id, driver_id, vehicle_name, remember_vehicle
                FROM vehicles;
            """)

            # Drop old table and rename new one
            cur.execute("DROP TABLE vehicles;")
            cur.execute("ALTER TABLE vehicles_new RENAME TO vehicles;")
            conn.commit()

        print("SQLite migration completed successfully!")
        cur.close()
        conn.close()

if __name__ == '__main__':
    migrate_database()
