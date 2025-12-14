"""
Main FastAPI application entry point
Modular, SOLID-compliant architecture with dependency injection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
import os
from framework.bootstrap import bootstrap_container
from infrastructure.database.connection import init_db
from core.middleware import AuthLoggingMiddleware
from core.config import CORS_ORIGINS, ENABLE_REQUEST_LOGGING

# Load environment variables from .env file
load_dotenv()

# Bootstrap dependency injection container
bootstrap_container()

from api import projects, risks, forecast, simulate, explain, auth, ml_training, portfolio, notifications, webhooks, user_preferences, feedback, gantt, onboarding

app = FastAPI(
    title="Schedule Risk Monitoring API",
    description="API for project risk monitoring and forecasting with token-based authentication",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add response compression for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add authentication and logging middleware
if ENABLE_REQUEST_LOGGING:
    app.add_middleware(AuthLoggingMiddleware)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    try:
        init_db()
        print("✓ Database initialized successfully")
        print("✓ Dependency injection container initialized")
    except Exception as e:
        print(f"⚠ Database initialization warning: {e}")
        print("⚠ Make sure PostgreSQL is running and DATABASE_URL is set correctly")

# Health check endpoint (public, no auth required)
@app.get("/health")
def health_check():
    """Health check endpoint - public, no authentication required"""
    return {"status": "healthy", "service": "schedule-risk-monitoring", "version": "2.0.0"}

# Authentication endpoints (public)
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

# Protected API endpoints (require authentication)
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(risks.router, prefix="/api", tags=["risks"])
app.include_router(forecast.router, prefix="/api", tags=["forecast"])
app.include_router(simulate.router, prefix="/api", tags=["simulation"])
app.include_router(explain.router, prefix="/api", tags=["explain"])
app.include_router(ml_training.router, prefix="/api", tags=["ml-training"])
app.include_router(portfolio.router, prefix="/api", tags=["portfolio"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])
app.include_router(user_preferences.router, prefix="/api", tags=["user-preferences"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(gantt.router, prefix="/api", tags=["gantt"])
app.include_router(onboarding.router, prefix="/api", tags=["onboarding"])

