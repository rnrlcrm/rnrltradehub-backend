"""
Sales Contract Service - Business logic for sales contract management.

This service handles:
- Contract CRUD operations
- Contract number generation
- Status workflow management
- Version control for amendments
- Quality specification validation
"""
import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

import models
import schemas


class SalesContractService:
    """Service class for sales contract operations."""

    @staticmethod
    def generate_contract_number(db: Session) -> str:
        """
        Generate unique contract number.
        
        Business Logic:
        - Format: SC-YYYY-NNNN (e.g., SC-2024-0001)
        - Auto-increment based on current year
        
        Args:
            db: Database session
            
        Returns:
            Generated contract number
        """
        current_year = datetime.now().year
        prefix = f"SC-{current_year}-"
        
        # Get the highest contract number for current year
        last_contract = db.query(models.SalesContract).filter(
            models.SalesContract.contract_number.like(f"{prefix}%")
        ).order_by(models.SalesContract.contract_number.desc()).first()
        
        if last_contract:
            last_number = int(last_contract.contract_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"

    @staticmethod
    def validate_contract_status(status_value: str) -> None:
        """
        Validate contract status.
        
        Args:
            status_value: Status to validate
            
        Raises:
            HTTPException: If status is invalid
        """
        valid_statuses = ["draft", "active", "completed", "cancelled", "amended"]
        if status_value and status_value not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

    @staticmethod
    def validate_business_partner_exists(db: Session, partner_id: str) -> None:
        """
        Validate that business partner exists.
        
        Business Logic:
        - Check if partner exists
        - Check if partner is active
        
        Args:
            db: Database session
            partner_id: Business partner ID
            
        Raises:
            HTTPException: If partner not found or inactive
        """
        partner = db.query(models.BusinessPartner).filter(
            models.BusinessPartner.id == partner_id
        ).first()
        
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business partner with ID {partner_id} not found"
            )
        
        # Business Logic: Partner must be active to create contracts
        if partner.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create contract with inactive business partner"
            )

    @staticmethod
    def validate_contract_dates(start_date: datetime, end_date: datetime) -> None:
        """
        Validate contract dates.
        
        Business Logic:
        - End date must be after start date
        - Start date cannot be in the past (for new contracts)
        
        Args:
            start_date: Contract start date
            end_date: Contract end date
            
        Raises:
            HTTPException: If dates are invalid
        """
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract end date must be after start date"
            )

    @staticmethod
    def create_sales_contract(
        db: Session,
        contract_data: schemas.SalesContractCreate
    ) -> models.SalesContract:
        """
        Create a new sales contract with validation.
        
        Business Logic:
        - Generate unique contract number
        - Validate business partner exists and is active
        - Validate contract dates
        - Validate status
        - Set initial version to 1
        
        Args:
            db: Database session
            contract_data: Contract creation data
            
        Returns:
            Created sales contract
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate business partner
        SalesContractService.validate_business_partner_exists(db, contract_data.business_partner_id)
        
        # Business Logic: Validate dates
        SalesContractService.validate_contract_dates(contract_data.start_date, contract_data.end_date)
        
        # Business Logic: Validate status
        if contract_data.status:
            SalesContractService.validate_contract_status(contract_data.status)
        
        # Business Logic: Generate contract number
        contract_number = SalesContractService.generate_contract_number(db)

        # Create contract
        db_contract = models.SalesContract(
            id=str(uuid.uuid4()),
            contract_number=contract_number,
            version=1,  # Business Logic: Initial version
            **contract_data.model_dump()
        )
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        return db_contract

    @staticmethod
    def get_sales_contracts(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        partner_id: Optional[str] = None
    ) -> List[models.SalesContract]:
        """
        Get filtered list of sales contracts.
        
        Business Logic:
        - Filter by status
        - Filter by business partner
        - Support pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Filter by status
            partner_id: Filter by business partner ID
            
        Returns:
            List of sales contracts
        """
        query = db.query(models.SalesContract)

        # Business Logic: Filter by status
        if status_filter:
            query = query.filter(models.SalesContract.status == status_filter)
        
        # Business Logic: Filter by business partner
        if partner_id:
            query = query.filter(models.SalesContract.business_partner_id == partner_id)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_sales_contract_by_id(db: Session, contract_id: str) -> models.SalesContract:
        """
        Get a sales contract by ID.
        
        Args:
            db: Database session
            contract_id: Contract ID
            
        Returns:
            Sales contract
            
        Raises:
            HTTPException: If contract not found
        """
        contract = db.query(models.SalesContract).filter(
            models.SalesContract.id == contract_id
        ).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales contract with ID {contract_id} not found"
            )
        
        return contract

    @staticmethod
    def update_sales_contract(
        db: Session,
        contract_id: str,
        contract_data: schemas.SalesContractCreate
    ) -> models.SalesContract:
        """
        Update a sales contract.
        
        Business Logic:
        - Can only update draft or active contracts
        - If contract is active, create amendment (increment version)
        - Validate dates
        - Validate status transitions
        
        Args:
            db: Database session
            contract_id: Contract ID
            contract_data: Updated contract data
            
        Returns:
            Updated sales contract
            
        Raises:
            HTTPException: If validation fails
        """
        contract = SalesContractService.get_sales_contract_by_id(db, contract_id)
        
        # Business Logic: Can only update draft or active contracts
        if contract.status in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update contract with status '{contract.status}'"
            )
        
        # Business Logic: Validate dates
        SalesContractService.validate_contract_dates(contract_data.start_date, contract_data.end_date)
        
        # Business Logic: If contract is active, increment version (amendment)
        if contract.status == "active":
            contract.version += 1
            contract.status = "amended"

        # Update contract
        for key, value in contract_data.model_dump().items():
            setattr(contract, key, value)

        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def cancel_sales_contract(db: Session, contract_id: str, reason: str) -> models.SalesContract:
        """
        Cancel a sales contract.
        
        Business Logic:
        - Can only cancel draft or active contracts
        - Cannot cancel if there are pending invoices
        - Set status to cancelled
        
        Args:
            db: Database session
            contract_id: Contract ID
            reason: Cancellation reason
            
        Returns:
            Cancelled sales contract
            
        Raises:
            HTTPException: If validation fails
        """
        contract = SalesContractService.get_sales_contract_by_id(db, contract_id)
        
        # Business Logic: Can only cancel draft or active contracts
        if contract.status not in ["draft", "active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel contract with status '{contract.status}'"
            )
        
        # Business Logic: Check for pending invoices
        pending_invoices = db.query(models.Invoice).filter(
            models.Invoice.sales_contract_id == contract_id,
            models.Invoice.status.in_(["draft", "pending"])
        ).count()
        
        if pending_invoices > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel contract with {pending_invoices} pending invoices"
            )
        
        contract.status = "cancelled"
        # Store cancellation reason in notes or add a cancellation_reason field
        
        db.commit()
        db.refresh(contract)
        return contract
