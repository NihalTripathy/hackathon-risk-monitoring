#!/usr/bin/env python3
"""
Database Setup Script
Helps users set up the PostgreSQL database for the first time.

This script:
1. Checks if PostgreSQL is accessible
2. Creates the database if it doesn't exist
3. Initializes all tables
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def get_database_url():
    """Get database URL from environment or prompt user"""
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url or "YOUR_PASSWORD" in db_url or "dbname" in db_url:
        print("\n" + "="*60)
        print("DATABASE CONFIGURATION REQUIRED")
        print("="*60)
        print("\nPlease configure your database connection.")
        print("\nOption 1: Set DATABASE_URL environment variable")
        print("  Format: postgresql://username:password@host:port/database_name")
        print("  Example: postgresql://postgres:mypassword@localhost:5432/schedule_risk_db")
        print("\nOption 2: Create a .env file in schedule-risk-backend/ directory")
        print("  Copy .env.example to .env and update with your credentials")
        print("\n" + "="*60)
        
        # Try to read from .env.example for guidance
        try:
            with open('.env.example', 'r') as f:
                print("\nExample .env file contents:")
                print("-" * 60)
                for line in f:
                    if line.strip() and not line.strip().startswith('#'):
                        print(line.strip())
                print("-" * 60)
        except FileNotFoundError:
            pass
        
        print("\nAfter configuring DATABASE_URL, run this script again.")
        sys.exit(1)
    
    return db_url

def check_postgres_connection(db_url):
    """Check if PostgreSQL server is accessible"""
    try:
        # Try to connect to PostgreSQL server (without specific database)
        # Extract connection info from URL
        if "postgresql://" in db_url:
            # Parse the URL to get base connection
            parts = db_url.split("://")[1].split("@")
            if len(parts) == 2:
                user_pass = parts[0].split(":")
                host_port_db = parts[1].split("/")
                if len(host_port_db) >= 2:
                    host_port = host_port_db[0].split(":")
                    host = host_port[0]
                    port = host_port[1] if len(host_port) > 1 else "5432"
                    user = user_pass[0]
                    password = user_pass[1] if len(user_pass) > 1 else ""
                    
                    # Try connecting to 'postgres' database (default)
                    base_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
                    engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    return True, host, port, user
    except Exception as e:
        print(f"\n⚠ Warning: Could not verify PostgreSQL connection: {e}")
        return False, None, None, None
    
    return True, None, None, None

def create_database_if_not_exists(db_url):
    """Create the database if it doesn't exist"""
    try:
        # Parse database name from URL
        if "postgresql://" in db_url:
            parts = db_url.split("/")
            if len(parts) >= 2:
                db_name = parts[-1].split("?")[0]  # Remove query params if any
                
                # Connect to 'postgres' database to create our database
                base_url = "/".join(parts[:-1]) + "/postgres"
                engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
                
                with engine.connect() as conn:
                    # Check if database exists
                    result = conn.execute(
                        text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                        {"db_name": db_name}
                    )
                    exists = result.fetchone() is not None
                    
                    if not exists:
                        print(f"\n📦 Creating database '{db_name}'...")
                        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                        print(f"✓ Database '{db_name}' created successfully!")
                        return True
                    else:
                        print(f"✓ Database '{db_name}' already exists.")
                        return True
    except Exception as e:
        print(f"\n⚠ Warning: Could not create database automatically: {e}")
        print("You may need to create it manually using pgAdmin or psql:")
        print(f"  CREATE DATABASE schedule_risk_db;")
        return False
    
    return True

def initialize_tables(db_url):
    """Initialize all database tables"""
    try:
        print("\n📋 Initializing database tables...")
        from infrastructure.database.connection import init_db
        init_db()
        print("✓ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error initializing tables: {e}")
        return False

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("DATABASE SETUP FOR SCHEDULE RISK MONITORING")
    print("="*60)
    
    # Step 1: Get database URL
    db_url = get_database_url()
    print(f"\n✓ Using database URL: {db_url.split('@')[0]}@...")  # Hide password
    
    # Step 2: Check PostgreSQL connection
    print("\n🔍 Checking PostgreSQL connection...")
    connected, host, port, user = check_postgres_connection(db_url)
    if connected:
        print("✓ PostgreSQL server is accessible")
    else:
        print("⚠ Could not verify PostgreSQL connection")
        print("  Make sure PostgreSQL is running and credentials are correct")
    
    # Step 3: Create database if needed
    print("\n📦 Checking database...")
    create_database_if_not_exists(db_url)
    
    # Step 4: Initialize tables
    success = initialize_tables(db_url)
    
    if success:
        print("\n" + "="*60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("="*60)
        print("\nYou can now start the backend server:")
        print("  python run.py")
        print("\nOr use:")
        print("  start.bat (Windows)")
        print("  ./start.sh (Linux/Mac)")
    else:
        print("\n" + "="*60)
        print("❌ DATABASE SETUP INCOMPLETE")
        print("="*60)
        print("\nPlease check the errors above and:")
        print("1. Ensure PostgreSQL is installed and running")
        print("2. Verify DATABASE_URL in .env file is correct")
        print("3. Make sure the database user has CREATE DATABASE privileges")
        print("4. Try creating the database manually in pgAdmin if needed")
        sys.exit(1)

if __name__ == "__main__":
    main()
