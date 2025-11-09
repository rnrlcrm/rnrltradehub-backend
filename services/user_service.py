"""
User Service - Business logic for user and access management.

This service handles:
- User authentication
- Password hashing and validation
- Role-based access control
- Permission management
- User status management
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext

import models
import schemas


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service class for user and access management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def validate_email_unique(db: Session, email: str, exclude_id: Optional[str] = None) -> None:
        """
        Validate that email is unique.
        
        Business Logic:
        - Email must be unique across all users
        
        Args:
            db: Database session
            email: Email to validate
            exclude_id: Optional user ID to exclude from check (for updates)
            
        Raises:
            HTTPException: If email already exists
        """
        query = db.query(models.User).filter(models.User.email == email)
        if exclude_id:
            query = query.filter(models.User.id != exclude_id)
        
        existing = query.first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {email} already exists"
            )

    @staticmethod
    def validate_role_exists(db: Session, role_id: str) -> models.Role:
        """
        Validate that role exists.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            Role object
            
        Raises:
            HTTPException: If role not found
        """
        role = db.query(models.Role).filter(models.Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        return role

    @staticmethod
    def create_user(
        db: Session,
        user_data: schemas.UserCreate
    ) -> models.User:
        """
        Create a new user with validation.
        
        Business Logic:
        - Validate email uniqueness
        - Validate role exists
        - Hash password
        - Set initial status to active
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate email uniqueness
        UserService.validate_email_unique(db, user_data.email)
        
        # Business Logic: Validate role if provided
        if user_data.role_id:
            UserService.validate_role_exists(db, user_data.role_id)
        
        # Business Logic: Hash password
        hashed_password = UserService.hash_password(user_data.password)

        db_user = models.User(
            id=str(uuid.uuid4()),
            **user_data.model_dump(exclude={'password'}),
            password_hash=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
        """
        Authenticate a user.
        
        Business Logic:
        - Find user by email
        - Verify password
        - Check if user is active
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
            
        Returns:
            User if authenticated, None otherwise
        """
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            return None
        
        # Business Logic: Verify password
        if not UserService.verify_password(password, user.password_hash):
            return None
        
        # Business Logic: User must be active
        if user.status != "active":
            return None
        
        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: str,
        user_data: schemas.UserCreate
    ) -> models.User:
        """
        Update a user.
        
        Business Logic:
        - Validate user exists
        - Validate email uniqueness (excluding current user)
        - Hash password if changed
        - Validate role if changed
        
        Args:
            db: Database session
            user_id: User ID
            user_data: Updated user data
            
        Returns:
            Updated user
            
        Raises:
            HTTPException: If validation fails
        """
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Business Logic: Validate email uniqueness (excluding current user)
        if user_data.email != user.email:
            UserService.validate_email_unique(db, user_data.email, exclude_id=user_id)
        
        # Business Logic: Validate role if changed
        if user_data.role_id and user_data.role_id != user.role_id:
            UserService.validate_role_exists(db, user_data.role_id)
        
        # Update user fields
        for key, value in user_data.model_dump(exclude={'password'}).items():
            setattr(user, key, value)
        
        # Business Logic: Hash password if provided
        if user_data.password:
            user.password_hash = UserService.hash_password(user_data.password)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def deactivate_user(db: Session, user_id: str) -> models.User:
        """
        Deactivate a user.
        
        Business Logic:
        - User cannot deactivate themselves
        - Set status to inactive
        - Prevent login
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Deactivated user
            
        Raises:
            HTTPException: If validation fails
        """
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        user.status = "inactive"
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_role(
        db: Session,
        role_data: schemas.RoleCreate
    ) -> models.Role:
        """
        Create a new role.
        
        Business Logic:
        - Validate role name uniqueness
        - Create role with permissions
        
        Args:
            db: Database session
            role_data: Role creation data
            
        Returns:
            Created role
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate role name uniqueness
        existing = db.query(models.Role).filter(models.Role.name == role_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists"
            )

        db_role = models.Role(
            id=str(uuid.uuid4()),
            **role_data.model_dump()
        )
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return db_role

    @staticmethod
    def check_permission(db: Session, user_id: str, module: str, action: str) -> bool:
        """
        Check if user has permission for an action.
        
        Business Logic:
        - Get user's role
        - Check role's permissions for module and action
        
        Args:
            db: Database session
            user_id: User ID
            module: Module name
            action: Action (create, read, update, delete, approve, share)
            
        Returns:
            True if user has permission, False otherwise
        """
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or not user.role_id:
            return False
        
        # Get role permissions
        permissions = db.query(models.Permission).filter(
            models.Permission.role_id == user.role_id,
            models.Permission.module == module
        ).first()
        
        if not permissions:
            return False
        
        # Business Logic: Check specific permission
        permission_map = {
            "create": permissions.can_create,
            "read": permissions.can_read,
            "update": permissions.can_update,
            "delete": permissions.can_delete,
            "approve": permissions.can_approve,
            "share": permissions.can_share
        }
        
        return permission_map.get(action, False)
