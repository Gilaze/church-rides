import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_database():
    """Add grade column to existing users table"""
    database_url = os.environ.get('DATABASE_URL')

    try:
        if database_url:
            # PostgreSQL migration
            print("Migrating PostgreSQL database...")
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            # Check if grade column exists
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='grade';
            """)

            if not cur.fetchone():
                print("Adding grade column to users table...")
                cur.execute("ALTER TABLE users ADD COLUMN grade VARCHAR(20);")
                conn.commit()
                print("Grade column added successfully!")
            else:
                print("Grade column already exists.")

            conn.close()
        else:
            # SQLite migration
            print("Migrating SQLite database...")
            conn = sqlite3.connect('church_ride.db')
            cur = conn.cursor()

            # Check if grade column exists
            cur.execute("PRAGMA table_info(users);")
            columns = [column[1] for column in cur.fetchall()]

            if 'grade' not in columns:
                print("Adding grade column to users table...")
                cur.execute("ALTER TABLE users ADD COLUMN grade TEXT;")
                conn.commit()
                print("Grade column added successfully!")
            else:
                print("Grade column already exists.")

            conn.close()

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration error: {e}")
        print("Please run this script to update your database schema.")

if __name__ == '__main__':
    migrate_database()
