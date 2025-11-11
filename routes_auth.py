"""
Authentication and team management routes.

This module handles:
- User authentication (login)
- Team management (sub-users)
- User activity tracking
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
import models
import schemas
from services.user_service import UserService

# JWT configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
team_router = APIRouter(prefix="/api/users/my-team", tags=["Team Management"])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> models.User:
    """Get current user from JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user


def log_user_activity(
    db: Session,
    user_id: int,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[dict] = None
):
    """Log user activity to audit log."""
    audit_log = models.UserAuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()


@auth_router.post("/login", response_model=schemas.LoginResponse)
def login(
    login_data: schemas.LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    Multi-tenant support:
    - Filters data by client_id/vendor_id for sub-users
    - Returns user context for permission enforcement
    """
    # Authenticate user
    user = UserService.authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        # Log failed login attempt
        log_user_activity(
            db,
            user_id=0,  # Unknown user
            action="login_failed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={"email": login_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "client_id": user.client_id,
            "vendor_id": user.vendor_id,
            "user_type": user.user_type
        },
        expires_delta=access_token_expires
    )
    
    # Log successful login
    log_user_activity(
        db,
        user_id=user.id,
        action="login",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Return token and user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role_id": user.role_id,
            "client_id": user.client_id,
            "vendor_id": user.vendor_id,
            "user_type": user.user_type
        }
    }


@team_router.get("/", response_model=List[schemas.SubUserResponse])
def list_team_members(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all sub-users for the current user.
    
    Business Logic:
    - Only primary users can have sub-users
    - Sub-users inherit client_id/vendor_id from parent
    """
    if current_user.user_type != "primary":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only primary users can manage team members"
        )
    
    sub_users = db.query(models.User).filter(
        models.User.parent_user_id == current_user.id
    ).all()
    
    return sub_users


@team_router.post("/", response_model=schemas.SubUserResponse, status_code=status.HTTP_201_CREATED)
def create_team_member(
    sub_user_data: schemas.SubUserCreate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new sub-user with limit enforcement.
    
    Business Logic:
    - Enforce max_sub_users limit
    - Inherit client_id/vendor_id from parent
    - Sub-users cannot create their own sub-users
    """
    if current_user.user_type != "primary":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only primary users can create team members"
        )
    
    # Check sub-user limit
    current_sub_user_count = db.query(func.count(models.User.id)).filter(
        models.User.parent_user_id == current_user.id
    ).scalar()
    
    if current_sub_user_count >= current_user.max_sub_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum sub-user limit ({current_user.max_sub_users}) reached"
        )
    
    # Check email uniqueness
    existing_user = db.query(models.User).filter(
        models.User.email == sub_user_data.email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create sub-user
    hashed_password = UserService.hash_password(sub_user_data.password)
    
    new_sub_user = models.User(
        name=sub_user_data.name,
        email=sub_user_data.email,
        password_hash=hashed_password,
        role_id=sub_user_data.role_id,
        parent_user_id=current_user.id,
        user_type="sub_user",
        client_id=current_user.client_id,  # Inherit from parent
        vendor_id=current_user.vendor_id,  # Inherit from parent
        is_active=True
    )
    
    db.add(new_sub_user)
    db.commit()
    db.refresh(new_sub_user)
    
    # Log activity
    log_user_activity(
        db,
        user_id=current_user.id,
        action="create_sub_user",
        entity_type="user",
        entity_id=str(new_sub_user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"sub_user_email": sub_user_data.email}
    )
    
    # TODO: Send invitation email
    
    return new_sub_user


@team_router.put("/{sub_user_id}", response_model=schemas.SubUserResponse)
def update_team_member(
    sub_user_id: int,
    sub_user_data: schemas.SubUserUpdate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a sub-user.
    
    Business Logic:
    - Only parent can update their sub-users
    - Cannot change client_id/vendor_id (inherited from parent)
    """
    if current_user.user_type != "primary":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only primary users can update team members"
        )
    
    sub_user = db.query(models.User).filter(
        models.User.id == sub_user_id,
        models.User.parent_user_id == current_user.id
    ).first()
    
    if not sub_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-user not found or you don't have permission to update"
        )
    
    # Update fields
    if sub_user_data.name is not None:
        sub_user.name = sub_user_data.name
    
    if sub_user_data.email is not None:
        # Check email uniqueness
        existing_user = db.query(models.User).filter(
            models.User.email == sub_user_data.email,
            models.User.id != sub_user_id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        sub_user.email = sub_user_data.email
    
    if sub_user_data.password is not None:
        sub_user.password_hash = UserService.hash_password(sub_user_data.password)
    
    if sub_user_data.role_id is not None:
        sub_user.role_id = sub_user_data.role_id
    
    if sub_user_data.is_active is not None:
        sub_user.is_active = sub_user_data.is_active
    
    db.commit()
    db.refresh(sub_user)
    
    # Log activity
    log_user_activity(
        db,
        user_id=current_user.id,
        action="update_sub_user",
        entity_type="user",
        entity_id=str(sub_user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return sub_user


@team_router.delete("/{sub_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team_member(
    sub_user_id: int,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a sub-user.
    
    Business Logic:
    - Only parent can delete their sub-users
    - Soft delete by setting is_active to False
    """
    if current_user.user_type != "primary":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only primary users can delete team members"
        )
    
    sub_user = db.query(models.User).filter(
        models.User.id == sub_user_id,
        models.User.parent_user_id == current_user.id
    ).first()
    
    if not sub_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-user not found or you don't have permission to delete"
        )
    
    # Soft delete
    sub_user.is_active = False
    db.commit()
    
    # Log activity
    log_user_activity(
        db,
        user_id=current_user.id,
        action="delete_sub_user",
        entity_type="user",
        entity_id=str(sub_user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return None


@team_router.get("/{sub_user_id}/activity", response_model=List[schemas.UserAuditLogResponse])
def get_team_member_activity(
    sub_user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get activity logs for a sub-user.
    
    Business Logic:
    - Only parent can view their sub-users' activity
    """
    if current_user.user_type != "primary":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only primary users can view team member activity"
        )
    
    sub_user = db.query(models.User).filter(
        models.User.id == sub_user_id,
        models.User.parent_user_id == current_user.id
    ).first()
    
    if not sub_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-user not found or you don't have permission to view activity"
        )
    
    activity_logs = db.query(models.UserAuditLog).filter(
        models.UserAuditLog.user_id == sub_user_id
    ).order_by(
        models.UserAuditLog.timestamp.desc()
    ).offset(skip).limit(limit).all()
    
    return activity_logs
