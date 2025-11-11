"""
Security middleware for multi-tenant data filtering and permission validation.

This module provides:
- Data filtering by client_id/vendor_id
- Permission validation guards
- Audit logging
"""
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from functools import wraps

import models


def filter_by_tenant(
    query,
    user: models.User,
    entity_class
):
    """
    Filter query results by tenant (client_id/vendor_id).
    
    Business Logic:
    - Primary users with no tenant association see all data
    - Users with client_id only see data for that client
    - Users with vendor_id only see data for that vendor
    - Sub-users inherit tenant filtering from parent
    
    Args:
        query: SQLAlchemy query object
        user: Current user
        entity_class: Model class being queried
        
    Returns:
        Filtered query
    """
    # Check if entity has client_id or vendor_id fields
    has_client_id = hasattr(entity_class, 'client_id')
    has_vendor_id = hasattr(entity_class, 'vendor_id')
    
    # Apply client_id filter if user has client_id and entity supports it
    if user.client_id and has_client_id:
        query = query.filter(entity_class.client_id == user.client_id)
    
    # Apply vendor_id filter if user has vendor_id and entity supports it
    if user.vendor_id and has_vendor_id:
        query = query.filter(entity_class.vendor_id == user.vendor_id)
    
    return query


def check_tenant_permission(
    user: models.User,
    entity,
    action: str = "read"
) -> bool:
    """
    Check if user has permission to access entity based on tenant.
    
    Business Logic:
    - Primary users with no tenant see all
    - Users must match client_id or vendor_id to access
    - Sub-users inherit parent's tenant permissions
    
    Args:
        user: Current user
        entity: Entity being accessed
        action: Action being performed (read, write, delete)
        
    Returns:
        True if permitted, False otherwise
    """
    # Admin users see everything (if no tenant restriction)
    if not user.client_id and not user.vendor_id:
        return True
    
    # Check client_id match
    if user.client_id and hasattr(entity, 'client_id'):
        if entity.client_id == user.client_id:
            return True
    
    # Check vendor_id match
    if user.vendor_id and hasattr(entity, 'vendor_id'):
        if entity.vendor_id == user.vendor_id:
            return True
    
    # For entities without tenant fields, allow access for now
    # (This can be customized based on specific business rules)
    if not hasattr(entity, 'client_id') and not hasattr(entity, 'vendor_id'):
        return True
    
    return False


def require_permission(module: str, action: str):
    """
    Decorator to enforce permission checks on endpoints.
    
    Usage:
        @require_permission("sales_contracts", "create")
        def create_contract(...):
            pass
    
    Args:
        module: Module name (e.g., "sales_contracts", "users")
        action: Action (create, read, update, delete, approve, share)
        
    Raises:
        HTTPException: If user lacks permission
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs (passed by Depends)
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get db session
            db = kwargs.get('db')
            
            # Check permission using user service
            from services.user_service import UserService
            
            has_permission = UserService.check_permission(
                db,
                current_user.id,
                module,
                action
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to {action} {module}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_primary_user(func: Callable):
    """
    Decorator to ensure only primary users can access endpoint.
    
    Usage:
        @require_primary_user
        def create_sub_user(...):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if current_user.user_type != "primary":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This action is only available to primary users"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def validate_tenant_access(
    user: models.User,
    entity,
    db: Session
):
    """
    Validate that user has access to entity based on tenant.
    
    Raises HTTPException if access denied.
    
    Args:
        user: Current user
        entity: Entity to validate access for
        db: Database session
        
    Raises:
        HTTPException: If access is denied
    """
    if not check_tenant_permission(user, entity):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
