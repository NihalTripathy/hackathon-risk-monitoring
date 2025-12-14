"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from core.database import get_db
from core.user_service import create_user, authenticate_user, get_user_by_id
from core.auth import create_access_token
from core.auth_dependencies import bearer_scheme

router = APIRouter()

# OAuth2 scheme for token extraction (used for login endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Request/Response models

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password length (bcrypt limit is 72 bytes)"""
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password cannot be longer than 72 bytes. Please use a shorter password.")
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Import centralized authentication dependencies
from core.auth_dependencies import get_current_user_from_token as _get_current_user, get_optional_user

# Re-export for backward compatibility and convenience
# All endpoints should use this for required authentication
get_current_user = _get_current_user

# Optional authentication - use for endpoints that work with or without auth
get_current_user_optional = get_optional_user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if email exists (even with different password)
        from core.user_service import get_user_by_email
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = create_user(db, user_data.email, user_data.password, user_data.full_name)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(id=user.id, email=user.email, full_name=user.full_name)
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        print(f"Registration error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token - sub must be a string per JWT spec
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(id=user.id, email=user.email, full_name=user.full_name)
    }


@router.post("/login-json", response_model=Token)
def login_json(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login using JSON body (alternative to form data)"""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token - sub must be a string per JWT spec
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(id=user.id, email=user.email, full_name=user.full_name)
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.get("/test-token")
def test_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    """Test endpoint to debug token validation"""
    from fastapi.security import HTTPBearer
    from core.auth_dependencies import bearer_scheme
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=== TOKEN DEBUG ===")
    logger.info(f"Credentials object: {credentials}")
    logger.info(f"Credentials type: {type(credentials)}")
    
    if credentials is None:
        return {"error": "No credentials provided", "credentials": None}
    
    token = credentials.credentials
    logger.info(f"Token extracted: {token[:50]}...")
    
    from core.auth import decode_access_token
    payload = decode_access_token(token)
    
    if payload is None:
        return {"error": "Token decode failed", "token_preview": token[:50]}
    
    return {
        "success": True,
        "payload": payload,
        "user_id": payload.get("sub"),
        "token_preview": token[:50]
    }

