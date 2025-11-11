"""
Access Control Utilities for Multi-Tenant System.

This module provides helper functions for implementing user_type based
access control across the three portals: BACK_OFFICE, CLIENT, and VENDOR.
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

import models


def get_effective_business_partner_id(user: models.User, db: Session) -> Optional[str]:
    """
    Get the effective business partner ID for a user (handles sub-users).
    
    For parent users: Returns their own business_partner_id
    For sub-users: Returns their parent's business_partner_id
    For back office users: Returns None
    
    Args:
        user: The user object
        db: Database session
        
    Returns:
        Business partner ID or None
    """
    if user.user_type == 'BACK_OFFICE':
        return None
    
    if user.parent_user_id:
        # Sub-user: get parent's business_partner_id
        parent = db.query(models.User).filter(
            models.User.id == user.parent_user_id
        ).first()
        return parent.business_partner_id if parent else user.business_partner_id
    
    return user.business_partner_id


def check_contract_access(user: models.User, contract: models.SalesContract, db: Session) -> bool:
    """
    Check if user has access to view a specific contract.
    
    Access rules:
    - BACK_OFFICE: Full access to all contracts
    - CLIENT: Only contracts where client_id matches business_partner_id
    - VENDOR: Only contracts where vendor_id matches business_partner_id
    
    Args:
        user: The user requesting access
        contract: The sales contract to check
        db: Database session
        
    Returns:
        True if user has access, False otherwise
    """
    if user.user_type == 'BACK_OFFICE':
        return True
    
    bp_id = get_effective_business_partner_id(user, db)
    if not bp_id:
        return False
    
    if user.user_type == 'CLIENT':
        return contract.client_id == bp_id
    elif user.user_type == 'VENDOR':
        return contract.vendor_id == bp_id
    
    return False


def validate_sub_user_limit(parent_user: models.User, db: Session) -> None:
    """
    Validate that a parent user hasn't exceeded the sub-user limit (max 2).
    
    Args:
        parent_user: The parent user
        db: Database session
        
    Raises:
        HTTPException: If sub-user limit is exceeded
    """
    if parent_user.parent_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sub-users cannot create other sub-users"
        )
    
    existing_count = db.query(models.User).filter(
        models.User.parent_user_id == parent_user.id
    ).count()
    
    if existing_count >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 2 sub-users allowed per user"
        )


def filter_contracts_by_user_type(
    query,
    user: models.User,
    db: Session
):
    """
    Apply user_type based filtering to a contracts query.
    
    Args:
        query: SQLAlchemy query object
        user: The current user
        db: Database session
        
    Returns:
        Filtered query
    """
    if user.user_type == 'BACK_OFFICE':
        return query
    
    bp_id = get_effective_business_partner_id(user, db)
    if not bp_id:
        # No business partner = no access
        return query.filter(False)
    
    if user.user_type == 'CLIENT':
        return query.filter(models.SalesContract.client_id == bp_id)
    elif user.user_type == 'VENDOR':
        return query.filter(models.SalesContract.vendor_id == bp_id)
    
    return query.filter(False)


def filter_invoices_by_user_type(
    query,
    user: models.User,
    db: Session
):
    """
    Apply user_type based filtering to an invoices query.
    
    Args:
        query: SQLAlchemy query object
        user: The current user
        db: Database session
        
    Returns:
        Filtered query
    """
    if user.user_type == 'BACK_OFFICE':
        return query
    
    bp_id = get_effective_business_partner_id(user, db)
    if not bp_id:
        return query.filter(False)
    
    # Join with sales_contracts to filter by business_partner_id
    query = query.join(models.SalesContract, models.Invoice.sales_contract_id == models.SalesContract.id)
    
    if user.user_type == 'CLIENT':
        return query.filter(models.SalesContract.client_id == bp_id)
    elif user.user_type == 'VENDOR':
        return query.filter(models.SalesContract.vendor_id == bp_id)
    
    return query.filter(False)


def require_user_type(*allowed_types: str):
    """
    Decorator factory to restrict endpoint access to specific user types.
    
    Usage:
        @router.get("/endpoint")
        @require_user_type('BACK_OFFICE')
        def my_endpoint(user: User = Depends(get_current_user)):
            ...
    
    Args:
        *allowed_types: Variable number of allowed user types
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = kwargs.get('user') or kwargs.get('current_user')
            if not user or user.user_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required user types: {', '.join(allowed_types)}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_portal_url(user_type: str) -> str:
    """
    Get the portal URL for a given user type.
    
    Args:
        user_type: The user type
        
    Returns:
        Portal URL path
    """
    portal_map = {
        'BACK_OFFICE': '/back-office/dashboard',
        'CLIENT': '/client/dashboard',
        'VENDOR': '/vendor/dashboard'
    }
    return portal_map.get(user_type, '/')
