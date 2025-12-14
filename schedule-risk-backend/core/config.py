"""
Application Configuration
Centralized configuration for authentication, API settings, and feature flags.
"""

import os
from typing import List, Set

# Authentication Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# API Configuration
API_PREFIX = "/api"
API_VERSION = "v1"

# Public Endpoints (don't require authentication)
PUBLIC_ENDPOINTS: Set[str] = {
    f"{API_PREFIX}/auth/register",
    f"{API_PREFIX}/auth/login",
    f"{API_PREFIX}/auth/login-json",
    f"{API_PREFIX}/llm/status",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
}

# Feature Flags
ENABLE_API_KEY_AUTH = os.getenv("ENABLE_API_KEY_AUTH", "false").lower() == "true"
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
ENABLE_REQUEST_LOGGING = os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true"

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# Add custom CORS origins from environment
CUSTOM_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
if CUSTOM_CORS_ORIGINS:
    CORS_ORIGINS.extend([origin.strip() for origin in CUSTOM_CORS_ORIGINS.split(",")])

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# Security Configuration
REQUIRE_HTTPS = os.getenv("REQUIRE_HTTPS", "false").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# ML Model Configuration
USE_ML_MODEL = os.getenv("USE_ML_MODEL", "false").lower() == "true"
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "models/ml_risk_model.pkl")
ML_ENSEMBLE_WEIGHT = float(os.getenv("ML_ENSEMBLE_WEIGHT", "0.7"))  # Weight for ML in ensemble (0.0-1.0)
ML_FALLBACK_TO_RULE_BASED = os.getenv("ML_FALLBACK_TO_RULE_BASED", "true").lower() == "true"
ML_MIN_TRAINING_SAMPLES = int(os.getenv("ML_MIN_TRAINING_SAMPLES", "50"))  # Minimum projects needed for training

