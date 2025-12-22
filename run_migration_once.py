"""
ONE-TIME MIGRATION SCRIPT
Add this to app.py temporarily to run migration on production startup.
Remove after first successful deployment.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def add_remember_vehicle_column():
    """Add remember_vehicle column if it doesn't exist"""
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("No DATABASE_URL found - skipping production migration")
        return

    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Check if column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='vehicles' AND column_name='remember_vehicle';
        """)

        if not cur.fetchone():
            print("Adding remember_vehicle column to production database...")
            cur.execute("ALTER TABLE vehicles ADD COLUMN remember_vehicle BOOLEAN DEFAULT FALSE;")
            conn.commit()
            print("✓ Migration completed successfully!")
        else:
            print("✓ Column already exists, no migration needed.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")
        raise

# Add this to the top of app.py, right after init_db():
# add_remember_vehicle_column()
