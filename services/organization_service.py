"""
Organization Service - Multi-company management and data isolation.

This module handles organization (multi-company) operations including:
- Organization creation and management
- Organization settings
- Data isolation by organization
- Organization validation
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Organization
from datetime import datetime


class OrganizationService:
    """Service for managing organizations (multi-company support)."""

    @staticmethod
    def create_organization(
        db: Session,
        legal_name: str,
        display_name: str,
        pan: str,
        gstin: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
        logo_url: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Organization:
        """
        Create a new organization.
        
        Args:
            db: Database session
            legal_name: Company legal name
            display_name: Display name
            pan: Company PAN
            gstin: Company GSTIN (optional)
            address: Registered address as JSON
            logo_url: Company logo URL
            settings: Organization settings as JSON
            
        Returns:
            Created Organization instance
            
        Raises:
            ValueError: If PAN already exists
        """
        # Check if PAN already exists
        existing = db.query(Organization).filter(
            Organization.pan == pan.upper()
        ).first()
        
        if existing:
            raise ValueError(f"Organization with PAN {pan} already exists")
        
        # Check if GSTIN already exists (if provided)
        if gstin:
            existing_gstin = db.query(Organization).filter(
                Organization.gstin == gstin.upper()
            ).first()
            if existing_gstin:
                raise ValueError(f"Organization with GSTIN {gstin} already exists")
        
        # Create organization
        organization = Organization(
            legal_name=legal_name,
            display_name=display_name,
            pan=pan.upper(),
            gstin=gstin.upper() if gstin else None,
            address=address or {},
            logo_url=logo_url,
            settings=settings or {},
            is_active=True
        )
        
        db.add(organization)
        db.commit()
        db.refresh(organization)
        
        return organization

    @staticmethod
    def get_organization(db: Session, organization_id: int) -> Optional[Organization]:
        """Get organization by ID."""
        return db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

    @staticmethod
    def get_active_organization(db: Session, organization_id: int) -> Optional[Organization]:
        """Get active organization by ID."""
        return db.query(Organization).filter(
            and_(
                Organization.id == organization_id,
                Organization.is_active == True
            )
        ).first()

    @staticmethod
    def list_organizations(
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """
        List organizations with optional filtering.
        
        Args:
            db: Database session
            is_active: Filter by active status (None = all)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Organization instances
        """
        query = db.query(Organization)
        
        if is_active is not None:
            query = query.filter(Organization.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_organization(
        db: Session,
        organization_id: int,
        **kwargs
    ) -> Optional[Organization]:
        """
        Update organization details.
        
        Args:
            db: Database session
            organization_id: Organization ID
            **kwargs: Fields to update
            
        Returns:
            Updated Organization instance or None
        """
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'legal_name', 'display_name', 'gstin', 'address',
            'logo_url', 'settings', 'is_active'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'gstin' and value:
                    value = value.upper()
                setattr(organization, field, value)
        
        db.commit()
        db.refresh(organization)
        
        return organization

    @staticmethod
    def deactivate_organization(db: Session, organization_id: int) -> bool:
        """
        Deactivate an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            True if deactivated, False if not found
        """
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            return False
        
        organization.is_active = False
        db.commit()
        
        return True

    @staticmethod
    def validate_organization_access(
        db: Session,
        organization_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Validate if organization exists and is active.
        Can be extended to check user permissions.
        
        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID (for future RBAC check)
            
        Returns:
            True if access allowed, False otherwise
        """
        organization = db.query(Organization).filter(
            and_(
                Organization.id == organization_id,
                Organization.is_active == True
            )
        ).first()
        
        return organization is not None

    @staticmethod
    def get_organization_settings(
        db: Session,
        organization_id: int,
        setting_key: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get organization settings.
        
        Args:
            db: Database session
            organization_id: Organization ID
            setting_key: Specific setting key (None = all settings)
            
        Returns:
            Settings dict or specific setting value
        """
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            return None
        
        if setting_key:
            return organization.settings.get(setting_key)
        
        return organization.settings

    @staticmethod
    def update_organization_settings(
        db: Session,
        organization_id: int,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Update organization settings.
        
        Args:
            db: Database session
            organization_id: Organization ID
            settings: New settings dict (merged with existing)
            
        Returns:
            True if updated, False if not found
        """
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            return False
        
        # Merge with existing settings
        current_settings = organization.settings or {}
        current_settings.update(settings)
        organization.settings = current_settings
        
        db.commit()
        
        return True
