"""
Centralized Authentication Dependencies
Provides scalable, token-based authentication for all API endpoints.
Designed to support multiple authentication methods (JWT, API Keys, OAuth) in the future.
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from .database import get_db
from .user_service import get_user_by_id
from .auth import decode_access_token

# Import UserResponse at runtime to avoid circular dependency
def _get_user_response_class():
    from api.auth import UserResponse
    return UserResponse

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom exception for authentication errors"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Extract and validate JWT token, return authenticated user.
    This is the core authentication dependency used by all protected endpoints.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        UserResponse: Authenticated user object
        
    Raises:
        AuthenticationError: If token is missing, invalid, or user not found
    """
    import logging
    logger = logging.getLogger(__name__)
    
    UserResponse = _get_user_response_class()
    
    if credentials is None:
        logger.warning("Authentication failed: No credentials provided")
        raise AuthenticationError("Authentication required. Please provide a valid Bearer token.")
    
    token = credentials.credentials
    logger.info(f"Token received: {token[:20]}..." if len(token) > 20 else token)
    
    # Decode and validate token
    payload = decode_access_token(token)
    if payload is None:
        logger.warning(f"Token decode failed for token: {token[:20]}...")
        raise AuthenticationError("Invalid or expired token. Please login again.")
    
    logger.info(f"Token decoded successfully. Payload: {payload}")
    
    # Extract user ID from token - sub is stored as string, convert to int
    user_id_str = payload.get("sub")
    if user_id_str is None:
        logger.warning(f"Token missing 'sub' field. Payload: {payload}")
        raise AuthenticationError("Invalid token format. User ID not found.")
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        logger.warning(f"Invalid user_id format in token: {user_id_str}")
        raise AuthenticationError("Invalid token format. User ID must be a number.")
    
    logger.info(f"Extracted user_id from token: {user_id}")
    
    # Verify user exists and is active
    user = get_user_by_id(db, user_id)
    if user is None:
        logger.warning(f"User not found for user_id: {user_id}")
        raise AuthenticationError("User not found. Token may be invalid.")
    
    if not user.is_active:
        logger.warning(f"User account inactive for user_id: {user_id}")
        raise AuthenticationError("User account is inactive.")
    
    logger.info(f"Authentication successful for user: {user.email} (id: {user.id})")
    return UserResponse(id=user.id, email=user.email, full_name=user.full_name)


# Primary dependency for protected endpoints
# Use this for all endpoints that require authentication
get_current_user = get_current_user_from_token


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Optional authentication - returns user if token is valid, None otherwise.
    Use this for endpoints that work with or without authentication.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        Optional[UserResponse]: User if authenticated, None otherwise
    """
    UserResponse = _get_user_response_class()
    
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        # Extract user ID from token - sub is stored as string, convert to int
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None
        
        user = get_user_by_id(db, user_id)
        if user is None or not user.is_active:
            return None
        
        return UserResponse(id=user.id, email=user.email, full_name=user.full_name)
    except Exception:
        return None


# Future: API Key authentication support
# This structure allows easy addition of API key authentication later
async def get_user_from_api_key(
    api_key: str,
    db: Session = Depends(get_db)
):
    """
    Future: Authenticate user via API key.
    This can be implemented when API key support is needed.
    
    Args:
        api_key: API key string
        db: Database session
        
    Returns:
        Optional[UserResponse]: User if API key is valid, None otherwise
    """
    # TODO: Implement API key validation
    # 1. Check if API key exists in database
    # 2. Verify API key is not expired
    # 3. Return associated user
    raise NotImplementedError("API key authentication not yet implemented")


# Future: Multi-method authentication
async def get_current_user_multi_method(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Future: Support multiple authentication methods (JWT, API Key, etc.)
    Tries each method in order until one succeeds.
    
    Args:
        credentials: HTTP Bearer token credentials
        api_key: Optional API key
        db: Database session
        
    Returns:
        UserResponse: Authenticated user
        
    Raises:
        AuthenticationError: If no authentication method succeeds
    """
    # Try JWT token first
    if credentials:
        try:
            return await get_current_user_from_token(credentials, db)
        except AuthenticationError:
            pass
    
    # Try API key if provided
    if api_key:
        user = await get_user_from_api_key(api_key, db)
        if user:
            return user
    
    raise AuthenticationError("No valid authentication method provided.")

