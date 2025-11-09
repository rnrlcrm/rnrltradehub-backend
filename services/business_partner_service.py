"""
Business Partner Service - Business logic for business partner management.

This service handles:
- Business partner CRUD operations
- BP code uniqueness validation
- Status management
- Compliance checks
- Shipping address management
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

import models
import schemas


class BusinessPartnerService:
    """Service class for business partner operations."""

    @staticmethod
    def validate_bp_code_unique(db: Session, bp_code: str, exclude_id: Optional[str] = None) -> None:
        """
        Validate that BP code is unique.
        
        Args:
            db: Database session
            bp_code: BP code to validate
            exclude_id: Optional ID to exclude from check (for updates)
            
        Raises:
            HTTPException: If BP code already exists
        """
        query = db.query(models.BusinessPartner).filter(
            models.BusinessPartner.bp_code == bp_code
        )
        if exclude_id:
            query = query.filter(models.BusinessPartner.id != exclude_id)
        
        existing = query.first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Business partner with code {bp_code} already exists"
            )

    @staticmethod
    def validate_status(status_value: str) -> None:
        """
        Validate business partner status.
        
        Args:
            status_value: Status to validate
            
        Raises:
            HTTPException: If status is invalid
        """
        valid_statuses = ["active", "inactive", "suspended", "pending"]
        if status_value and status_value not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

    @staticmethod
    def create_business_partner(
        db: Session,
        partner_data: schemas.BusinessPartnerCreate
    ) -> models.BusinessPartner:
        """
        Create a new business partner with validation.
        
        Business Logic:
        - Validate BP code uniqueness
        - Validate status
        - Create partner and associated shipping addresses
        - Ensure proper relationships
        
        Args:
            db: Database session
            partner_data: Partner creation data
            
        Returns:
            Created business partner
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate BP code uniqueness
        BusinessPartnerService.validate_bp_code_unique(db, partner_data.bp_code)
        
        # Business Logic: Validate status if provided
        if partner_data.status:
            BusinessPartnerService.validate_status(partner_data.status)

        # Create partner
        partner_id = str(uuid.uuid4())
        db_partner = models.BusinessPartner(
            id=partner_id,
            **partner_data.model_dump(exclude={'shipping_addresses'})
        )
        db.add(db_partner)

        # Create shipping addresses
        for addr in partner_data.shipping_addresses:
            db_address = models.Address(
                id=str(uuid.uuid4()),
                business_partner_id=partner_id,
                **addr.model_dump()
            )
            db.add(db_address)

        db.commit()
        db.refresh(db_partner)
        return db_partner

    @staticmethod
    def get_business_partners(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        business_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[models.BusinessPartner]:
        """
        Get filtered list of business partners.
        
        Business Logic:
        - Apply business type filtering
        - Apply status filtering
        - Support search across legal name and BP code
        - Pagination support
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            business_type: Filter by business type
            status_filter: Filter by status
            search: Search term for legal name or BP code
            
        Returns:
            List of business partners
        """
        query = db.query(models.BusinessPartner)

        # Business Logic: Filter by business type
        if business_type:
            query = query.filter(models.BusinessPartner.business_type == business_type)
        
        # Business Logic: Filter by status
        if status_filter:
            query = query.filter(models.BusinessPartner.status == status_filter)
        
        # Business Logic: Search functionality
        if search:
            query = query.filter(
                (models.BusinessPartner.legal_name.ilike(f"%{search}%")) |
                (models.BusinessPartner.bp_code.ilike(f"%{search}%"))
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_business_partner_by_id(db: Session, partner_id: str) -> models.BusinessPartner:
        """
        Get a business partner by ID.
        
        Args:
            db: Database session
            partner_id: Partner ID
            
        Returns:
            Business partner
            
        Raises:
            HTTPException: If partner not found
        """
        partner = db.query(models.BusinessPartner).filter(
            models.BusinessPartner.id == partner_id
        ).first()
        
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business partner with ID {partner_id} not found"
            )
        
        return partner

    @staticmethod
    def update_business_partner(
        db: Session,
        partner_id: str,
        partner_data: schemas.BusinessPartnerCreate
    ) -> models.BusinessPartner:
        """
        Update a business partner.
        
        Business Logic:
        - Validate partner exists
        - Validate BP code uniqueness (excluding current partner)
        - Validate status
        - Update partner data
        
        Args:
            db: Database session
            partner_id: Partner ID
            partner_data: Updated partner data
            
        Returns:
            Updated business partner
            
        Raises:
            HTTPException: If validation fails
        """
        # Get existing partner
        partner = BusinessPartnerService.get_business_partner_by_id(db, partner_id)
        
        # Business Logic: Validate BP code uniqueness (excluding current partner)
        if partner_data.bp_code != partner.bp_code:
            BusinessPartnerService.validate_bp_code_unique(db, partner_data.bp_code, exclude_id=partner_id)
        
        # Business Logic: Validate status
        if partner_data.status:
            BusinessPartnerService.validate_status(partner_data.status)

        # Update partner
        for key, value in partner_data.model_dump(exclude={'shipping_addresses'}).items():
            setattr(partner, key, value)

        db.commit()
        db.refresh(partner)
        return partner

    @staticmethod
    def delete_business_partner(db: Session, partner_id: str) -> None:
        """
        Delete a business partner.
        
        Business Logic:
        - Check if partner has active contracts (prevent deletion)
        - Delete associated shipping addresses
        - Delete partner
        
        Args:
            db: Database session
            partner_id: Partner ID
            
        Raises:
            HTTPException: If validation fails
        """
        partner = BusinessPartnerService.get_business_partner_by_id(db, partner_id)
        
        # Business Logic: Check if partner has active contracts
        active_contracts = db.query(models.SalesContract).filter(
            models.SalesContract.business_partner_id == partner_id,
            models.SalesContract.status == "active"
        ).count()
        
        if active_contracts > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete business partner with {active_contracts} active contracts"
            )
        
        # Delete associated addresses
        db.query(models.Address).filter(
            models.Address.business_partner_id == partner_id
        ).delete()
        
        db.delete(partner)
        db.commit()
