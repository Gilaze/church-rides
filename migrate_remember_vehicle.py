import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_database():
    """Add remember_vehicle column to existing vehicles table"""
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # PostgreSQL migration
        print("Migrating PostgreSQL database...")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Check if column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='vehicles' AND column_name='remember_vehicle';
        """)

        if not cur.fetchone():
            print("Adding remember_vehicle column to vehicles table...")
            cur.execute("ALTER TABLE vehicles ADD COLUMN remember_vehicle BOOLEAN DEFAULT FALSE;")
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Column already exists, no migration needed.")

        cur.close()
        conn.close()
    else:
        # SQLite migration
        print("Migrating SQLite database...")
        conn = sqlite3.connect('church_ride.db')
        cur = conn.cursor()

        # Check if column exists
        cur.execute("PRAGMA table_info(vehicles);")
        columns = [column[1] for column in cur.fetchall()]

        if 'remember_vehicle' not in columns:
            print("Adding remember_vehicle column to vehicles table...")
            cur.execute("ALTER TABLE vehicles ADD COLUMN remember_vehicle INTEGER DEFAULT 0;")
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Column already exists, no migration needed.")

        cur.close()
        conn.close()

if __name__ == '__main__':
    migrate_database()
