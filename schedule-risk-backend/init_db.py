"""
Initialize database - creates all tables
Run this script once to set up the database schema
"""

from core.database import init_db

if __name__ == "__main__":
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure:")
        print("1. PostgreSQL is running")
        print("2. DATABASE_URL environment variable is set correctly")
        print("3. Database 'schedule_risk_db' exists in PostgreSQL")

