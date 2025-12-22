"""
Migration: Add residence column to users table
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_database():
    """Add residence column to users table"""
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # PostgreSQL migration
        print("Migrating PostgreSQL database...")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Check if residence column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users' AND column_name='residence';
        """)

        if not cur.fetchone():
            print("Adding residence column to users table...")
            cur.execute("ALTER TABLE users ADD COLUMN residence VARCHAR(100);")
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
        cur.execute("PRAGMA table_info(users);")
        columns = [column[1] for column in cur.fetchall()]

        if 'residence' not in columns:
            print("Adding residence column to users table...")
            cur.execute("ALTER TABLE users ADD COLUMN residence TEXT;")
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Column already exists, no migration needed.")

        cur.close()
        conn.close()

if __name__ == '__main__':
    migrate_database()
