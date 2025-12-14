"""
Authentication and Request Logging Middleware
Provides centralized request logging, authentication tracking, and security headers.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class AuthLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging authenticated requests and adding security headers.
    Tracks API usage, response times, and authentication status.
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/login-json",
        "/api/llm/status",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    
    # Health check endpoint
    HEALTH_ENDPOINT = "/health"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through middleware.
        
        - Logs request details
        - Tracks authentication status
        - Adds security headers
        - Measures response time
        """
        start_time = time.time()
        
        # Check if endpoint is public
        path = request.url.path
        is_public = any(path.startswith(public) for public in self.PUBLIC_ENDPOINTS) or path == self.HEALTH_ENDPOINT
        
        # Extract authentication info
        auth_header = request.headers.get("Authorization", "")
        is_authenticated = auth_header.startswith("Bearer ")
        token_preview = ""
        if is_authenticated:
            token = auth_header.replace("Bearer ", "")
            token_preview = f"{token[:10]}..." if len(token) > 10 else token
        
        # Log request
        logger.info(
            f"Request: {request.method} {path} | "
            f"Auth: {'Yes' if is_authenticated else 'No'} | "
            f"Public: {'Yes' if is_public else 'No'} | "
            f"Token: {token_preview}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            
            # Add security headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "unknown")
            
            # Add CORS and security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Log response
            logger.info(
                f"Response: {request.method} {path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {path} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.3f}s"
            )
            raise


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Future: Rate limiting middleware for API protection.
    Can be implemented when needed for production scaling.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Placeholder for rate limiting implementation.
        Can use Redis or in-memory store for rate limiting.
        """
        # TODO: Implement rate limiting
        # 1. Track requests per IP/user
        # 2. Check rate limits
        # 3. Return 429 if exceeded
        return await call_next(request)

