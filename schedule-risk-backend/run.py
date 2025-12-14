#!/usr/bin/env python
"""
Simple server startup script
Works on Windows, Linux, Mac, AWS, Azure, and any platform
Usage: python run.py
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Check for required dependencies FIRST (before importing anything)
def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []
    
    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")
    
    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")
    
    try:
        import sqlalchemy
    except ImportError:
        missing.append("sqlalchemy")
    
    try:
        import psycopg2
    except ImportError:
        missing.append("psycopg2-binary")
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        missing.append("python-dotenv")
    
    if missing:
        print("❌ Error: Missing required dependencies!")
        print(f"   Missing packages: {', '.join(missing)}")
        print()
        print("📦 To install all dependencies, run:")
        print("   pip install -r requirements.txt")
        print()
        print("   Or install individually:")
        for pkg in missing:
            print(f"   pip install {pkg}")
        print()
        sys.exit(1)

# Check dependencies before proceeding
check_dependencies()

# Now safe to import (dependencies are installed)
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file
load_dotenv()

def main():
    """Start the FastAPI server"""
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")  # 127.0.0.1 for dev, 0.0.0.0 for production
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"  # Auto-reload in development
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠ Warning: .env file not found. Create one with DATABASE_URL and other settings.")
        print("   See README.md for setup instructions.\n")
    
    # Check if DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("⚠ Warning: DATABASE_URL not set in .env file")
        print("   The server will start but database operations will fail.\n")
    
    print("=" * 60)
    print("🚀 Starting Schedule Risk Monitoring API Server")
    print("=" * 60)
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    # Display URL (use localhost for 127.0.0.1 or 0.0.0.0)
    display_host = "localhost" if host in ["127.0.0.1", "0.0.0.0"] else host
    print(f"📝 API Docs: http://{display_host}:{port}/docs")
    print(f"❤️  Health: http://{display_host}:{port}/health")
    print("=" * 60)
    print()
    
    # Start the server
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

