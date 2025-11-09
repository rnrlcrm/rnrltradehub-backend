"""
Financial Year Service - Indian Financial Year management per Income Tax Act.

This module handles financial year operations including:
- Financial year creation (April-March cycle)
- Assessment year calculation
- Active year validation
- Year-end closing
- Transaction date validation
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import FinancialYear
from datetime import datetime, date
from dateutil import parser


class FinancialYearService:
    """Service for managing financial years per Indian Income Tax Act."""

    @staticmethod
    def create_financial_year(
        db: Session,
        organization_id: int,
        year_code: str,
        start_date: date,
        end_date: date,
        is_active: bool = False,
        opening_balances: Optional[Dict[str, Any]] = None
    ) -> FinancialYear:
        """
        Create a new financial year.
        
        Indian Financial Year: April 1 to March 31
        Example: FY 2023-24 = April 1, 2023 to March 31, 2024
        Assessment Year = FY + 1 = 2024-25
        
        Args:
            db: Database session
            organization_id: Organization ID
            year_code: Year code (e.g., "2023-24")
            start_date: Financial year start date (typically April 1)
            end_date: Financial year end date (typically March 31)
            is_active: Whether this is the active financial year
            opening_balances: Opening balances as JSON
            
        Returns:
            Created FinancialYear instance
            
        Raises:
            ValueError: If year_code already exists or dates are invalid
        """
        # Check if year_code already exists for this organization
        existing = db.query(FinancialYear).filter(
            and_(
                FinancialYear.organization_id == organization_id,
                FinancialYear.year_code == year_code
            )
        ).first()
        
        if existing:
            raise ValueError(
                f"Financial year {year_code} already exists for this organization"
            )
        
        # Validate dates
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
        
        # Calculate assessment year (FY + 1)
        # E.g., FY 2023-24 → AY 2024-25
        start_year = int(year_code.split('-')[0])
        end_year = int(year_code.split('-')[1])
        assessment_year = f"{start_year + 1}-{end_year + 1}"
        
        # If setting as active, deactivate other active years
        if is_active:
            db.query(FinancialYear).filter(
                and_(
                    FinancialYear.organization_id == organization_id,
                    FinancialYear.is_active == True
                )
            ).update({"is_active": False})
        
        # Create financial year
        financial_year = FinancialYear(
            organization_id=organization_id,
            year_code=year_code,
            start_date=start_date,
            end_date=end_date,
            assessment_year=assessment_year,
            is_active=is_active,
            is_closed=False,
            opening_balances=opening_balances or {}
        )
        
        db.add(financial_year)
        db.commit()
        db.refresh(financial_year)
        
        return financial_year

    @staticmethod
    def get_financial_year(db: Session, financial_year_id: int) -> Optional[FinancialYear]:
        """Get financial year by ID."""
        return db.query(FinancialYear).filter(
            FinancialYear.id == financial_year_id
        ).first()

    @staticmethod
    def get_active_financial_year(
        db: Session,
        organization_id: int
    ) -> Optional[FinancialYear]:
        """
        Get the active financial year for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Active FinancialYear instance or None
        """
        return db.query(FinancialYear).filter(
            and_(
                FinancialYear.organization_id == organization_id,
                FinancialYear.is_active == True
            )
        ).first()

    @staticmethod
    def list_financial_years(
        db: Session,
        organization_id: int,
        is_active: Optional[bool] = None,
        is_closed: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FinancialYear]:
        """
        List financial years for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            is_active: Filter by active status
            is_closed: Filter by closed status
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of FinancialYear instances
        """
        query = db.query(FinancialYear).filter(
            FinancialYear.organization_id == organization_id
        )
        
        if is_active is not None:
            query = query.filter(FinancialYear.is_active == is_active)
        
        if is_closed is not None:
            query = query.filter(FinancialYear.is_closed == is_closed)
        
        return query.order_by(FinancialYear.start_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def close_financial_year(
        db: Session,
        financial_year_id: int
    ) -> Optional[FinancialYear]:
        """
        Close a financial year.
        
        Args:
            db: Database session
            financial_year_id: Financial year ID
            
        Returns:
            Updated FinancialYear instance or None
            
        Raises:
            ValueError: If year is already closed
        """
        financial_year = db.query(FinancialYear).filter(
            FinancialYear.id == financial_year_id
        ).first()
        
        if not financial_year:
            return None
        
        if financial_year.is_closed:
            raise ValueError(f"Financial year {financial_year.year_code} is already closed")
        
        # Close the financial year
        financial_year.is_closed = True
        financial_year.is_active = False
        
        db.commit()
        db.refresh(financial_year)
        
        return financial_year

    @staticmethod
    def validate_transaction_date(
        db: Session,
        organization_id: int,
        transaction_date: date,
        financial_year_code: Optional[str] = None
    ) -> bool:
        """
        Validate if transaction date falls in active financial year.
        
        Args:
            db: Database session
            organization_id: Organization ID
            transaction_date: Transaction date to validate
            financial_year_code: Optional FY code to validate against
            
        Returns:
            True if valid, False otherwise
        """
        if financial_year_code:
            # Validate against specific FY
            fy = db.query(FinancialYear).filter(
                and_(
                    FinancialYear.organization_id == organization_id,
                    FinancialYear.year_code == financial_year_code
                )
            ).first()
        else:
            # Validate against active FY
            fy = FinancialYearService.get_active_financial_year(db, organization_id)
        
        if not fy:
            return False
        
        # Check if date falls within FY range
        return fy.start_date <= transaction_date <= fy.end_date

    @staticmethod
    def get_financial_year_for_date(
        db: Session,
        organization_id: int,
        transaction_date: date
    ) -> Optional[FinancialYear]:
        """
        Get financial year for a given date.
        
        Args:
            db: Database session
            organization_id: Organization ID
            transaction_date: Transaction date
            
        Returns:
            FinancialYear instance or None
        """
        return db.query(FinancialYear).filter(
            and_(
                FinancialYear.organization_id == organization_id,
                FinancialYear.start_date <= transaction_date,
                FinancialYear.end_date >= transaction_date
            )
        ).first()

    @staticmethod
    def activate_financial_year(
        db: Session,
        financial_year_id: int
    ) -> Optional[FinancialYear]:
        """
        Activate a financial year (deactivates others).
        
        Args:
            db: Database session
            financial_year_id: Financial year ID to activate
            
        Returns:
            Activated FinancialYear instance or None
        """
        financial_year = db.query(FinancialYear).filter(
            FinancialYear.id == financial_year_id
        ).first()
        
        if not financial_year:
            return None
        
        # Deactivate other years for this organization
        db.query(FinancialYear).filter(
            and_(
                FinancialYear.organization_id == financial_year.organization_id,
                FinancialYear.id != financial_year_id
            )
        ).update({"is_active": False})
        
        # Activate this year
        financial_year.is_active = True
        
        db.commit()
        db.refresh(financial_year)
        
        return financial_year

    @staticmethod
    def update_opening_balances(
        db: Session,
        financial_year_id: int,
        opening_balances: Dict[str, Any]
    ) -> Optional[FinancialYear]:
        """
        Update opening balances for a financial year.
        
        Args:
            db: Database session
            financial_year_id: Financial year ID
            opening_balances: Opening balances as JSON
            
        Returns:
            Updated FinancialYear instance or None
        """
        financial_year = db.query(FinancialYear).filter(
            FinancialYear.id == financial_year_id
        ).first()
        
        if not financial_year:
            return None
        
        # Merge with existing opening balances
        current_balances = financial_year.opening_balances or {}
        current_balances.update(opening_balances)
        financial_year.opening_balances = current_balances
        
        db.commit()
        db.refresh(financial_year)
        
        return financial_year

    @staticmethod
    def generate_year_code(start_year: int) -> str:
        """
        Generate year code from start year.
        
        Args:
            start_year: Starting year (e.g., 2023)
            
        Returns:
            Year code (e.g., "2023-24")
        """
        end_year_short = str(start_year + 1)[-2:]  # Last 2 digits
        return f"{start_year}-{end_year_short}"

    @staticmethod
    def calculate_assessment_year(year_code: str) -> str:
        """
        Calculate assessment year from financial year.
        
        Args:
            year_code: Financial year code (e.g., "2023-24")
            
        Returns:
            Assessment year (e.g., "2024-25")
        """
        start_year = int(year_code.split('-')[0])
        end_year = int(year_code.split('-')[1])
        return f"{start_year + 1}-{end_year + 1}"
