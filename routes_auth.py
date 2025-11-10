"""
Authentication Routes for Multi-Tenant Access Control.

This module provides authentication endpoints including:
- Login with user_type detection
- User information retrieval
- Password change
- Portal routing based on user_type
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import jwt
import os

from database import get_db
import models
from services.user_service import UserService
from access_control import get_portal_url

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


# Schemas
class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    user_type: str
    portal_url: str
    user_id: int
    name: str
    email: str


class UserInfoResponse(BaseModel):
    """Current user info response."""
    id: int
    name: str
    email: str
    user_type: str
    portal_url: str
    is_parent: bool
    business_partner_id: Optional[str] = None
    organization_id: Optional[int] = None
    parent_user_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str
    new_password: str


# Helper Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


# Authentication Endpoints
@auth_router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token with portal information.
    
    The response includes the user_type and portal_url for client-side routing.
    
    Args:
        login_data: Login credentials
        db: Database session
        
    Returns:
        LoginResponse with access token and user info
        
    Raises:
        HTTPException: If authentication fails
    """
    # Find user by email
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not UserService.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "user_type": user.user_type}
    )
    
    # Get portal URL based on user type
    portal_url = get_portal_url(user.user_type)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type=user.user_type,
        portal_url=portal_url,
        user_id=user.id,
        name=user.name,
        email=user.email
    )


@auth_router.get("/me", response_model=UserInfoResponse)
def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information including portal URL
    """
    return UserInfoResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        user_type=current_user.user_type,
        portal_url=get_portal_url(current_user.user_type),
        is_parent=current_user.is_parent,
        business_partner_id=current_user.business_partner_id,
        organization_id=current_user.organization_id,
        parent_user_id=current_user.parent_user_id,
        is_active=current_user.is_active
    )


@auth_router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    Args:
        password_data: Current and new password
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not UserService.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    new_password_hash = UserService.hash_password(password_data.new_password)
    
    # Update password
    current_user.password_hash = new_password_hash
    db.commit()
    
    return {"message": "Password changed successfully"}


@auth_router.post("/logout")
def logout():
    """
    Logout endpoint (client-side token removal).
    
    Since we're using JWT tokens, logout is primarily handled client-side
    by removing the token. This endpoint is provided for consistency.
    
    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}
