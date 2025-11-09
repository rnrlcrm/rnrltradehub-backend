"""
Year-End Service - Automate year-end closing and data transfer per Income Tax Act.

This module handles year-end operations including:
- Transfer of pending invoices to new financial year
- Transfer of pending payments
- Transfer of due commissions
- Transfer of open disputes
- Calculation of opening balances
- Complete year-end closing process
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import (
    Invoice, Payment, Commission, Dispute,
    FinancialYear, YearEndTransfer
)
from datetime import datetime
import uuid


class YearEndService:
    """Service for year-end closing and data transfer operations."""

    @staticmethod
    def transfer_pending_invoices(
        db: Session,
        from_fy_id: int,
        to_fy_id: int,
        organization_id: int,
        performed_by: str
    ) -> int:
        """
        Transfer unpaid and partially paid invoices to new financial year.
        
        Args:
            db: Database session
            from_fy_id: Source financial year ID
            to_fy_id: Target financial year ID
            organization_id: Organization ID
            performed_by: User performing the transfer
            
        Returns:
            Count of invoices transferred
        """
        # Get financial years
        from_fy = db.query(FinancialYear).filter(FinancialYear.id == from_fy_id).first()
        to_fy = db.query(FinancialYear).filter(FinancialYear.id == to_fy_id).first()
        
        if not from_fy or not to_fy:
            raise ValueError("Invalid financial year IDs")
        
        # Get pending invoices (Unpaid or Partially Paid)
        pending_invoices = db.query(Invoice).filter(
            and_(
                Invoice.organization_id == organization_id,
                Invoice.financial_year == from_fy.year_code,
                Invoice.status.in_(['Unpaid', 'Partially Paid'])
            )
        ).all()
        
        # Update financial year for pending invoices
        count = 0
        for invoice in pending_invoices:
            invoice.financial_year = to_fy.year_code
            count += 1
        
        # Log transfer
        transfer = YearEndTransfer(
            organization_id=organization_id,
            from_financial_year_id=from_fy_id,
            to_financial_year_id=to_fy_id,
            transfer_type='pending_invoices',
            entity_type='invoice',
            entity_count=count,
            transfer_summary={'status': ['Unpaid', 'Partially Paid']},
            performed_by=performed_by
        )
        
        db.add(transfer)
        db.commit()
        
        return count

    @staticmethod
    def transfer_due_commissions(
        db: Session,
        from_fy_id: int,
        to_fy_id: int,
        organization_id: int,
        performed_by: str
    ) -> int:
        """Transfer due commissions to new financial year."""
        from_fy = db.query(FinancialYear).filter(FinancialYear.id == from_fy_id).first()
        to_fy = db.query(FinancialYear).filter(FinancialYear.id == to_fy_id).first()
        
        if not from_fy or not to_fy:
            raise ValueError("Invalid financial year IDs")
        
        # Get due commissions
        due_commissions = db.query(Commission).filter(
            and_(
                Commission.organization_id == organization_id,
                Commission.financial_year == from_fy.year_code,
                Commission.status == 'Due'
            )
        ).all()
        
        # Update financial year
        count = 0
        for commission in due_commissions:
            commission.financial_year = to_fy.year_code
            count += 1
        
        # Log transfer
        transfer = YearEndTransfer(
            organization_id=organization_id,
            from_financial_year_id=from_fy_id,
            to_financial_year_id=to_fy_id,
            transfer_type='pending_commissions',
            entity_type='commission',
            entity_count=count,
            transfer_summary={'status': 'Due'},
            performed_by=performed_by
        )
        
        db.add(transfer)
        db.commit()
        
        return count

    @staticmethod
    def transfer_open_disputes(
        db: Session,
        from_fy_id: int,
        to_fy_id: int,
        organization_id: int,
        performed_by: str
    ) -> int:
        """Transfer open disputes to new financial year."""
        from_fy = db.query(FinancialYear).filter(FinancialYear.id == from_fy_id).first()
        to_fy = db.query(FinancialYear).filter(FinancialYear.id == to_fy_id).first()
        
        if not from_fy or not to_fy:
            raise ValueError("Invalid financial year IDs")
        
        # Get open disputes
        open_disputes = db.query(Dispute).filter(
            and_(
                Dispute.organization_id == organization_id,
                Dispute.financial_year == from_fy.year_code,
                Dispute.status == 'Open'
            )
        ).all()
        
        # Update financial year
        count = 0
        for dispute in open_disputes:
            dispute.financial_year = to_fy.year_code
            count += 1
        
        # Log transfer
        transfer = YearEndTransfer(
            organization_id=organization_id,
            from_financial_year_id=from_fy_id,
            to_financial_year_id=to_fy_id,
            transfer_type='open_disputes',
            entity_type='dispute',
            entity_count=count,
            transfer_summary={'status': 'Open'},
            performed_by=performed_by
        )
        
        db.add(transfer)
        db.commit()
        
        return count

    @staticmethod
    def calculate_opening_balances(
        db: Session,
        financial_year_id: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Calculate opening balances for new financial year.
        
        Returns:
            Dict with opening balance details
        """
        fy = db.query(FinancialYear).filter(FinancialYear.id == financial_year_id).first()
        
        if not fy:
            raise ValueError("Invalid financial year ID")
        
        # Calculate total outstanding invoices
        outstanding_invoices = db.query(Invoice).filter(
            and_(
                Invoice.organization_id == organization_id,
                Invoice.financial_year == fy.year_code,
                Invoice.status != 'Paid'
            )
        ).all()
        
        total_outstanding = sum(inv.amount for inv in outstanding_invoices)
        
        # Calculate total due commissions
        due_commissions = db.query(Commission).filter(
            and_(
                Commission.organization_id == organization_id,
                Commission.financial_year == fy.year_code,
                Commission.status == 'Due'
            )
        ).all()
        
        total_commissions_due = sum(comm.amount for comm in due_commissions)
        
        opening_balances = {
            'outstanding_invoices': total_outstanding,
            'due_commissions': total_commissions_due,
            'invoice_count': len(outstanding_invoices),
            'commission_count': len(due_commissions)
        }
        
        # Update financial year opening balances
        fy.opening_balances = opening_balances
        db.commit()
        
        return opening_balances

    @staticmethod
    def complete_year_end_closing(
        db: Session,
        from_fy_id: int,
        to_fy_id: int,
        organization_id: int,
        performed_by: str
    ) -> Dict[str, Any]:
        """
        Complete year-end closing process - all-in-one operation.
        
        This method:
        1. Transfers pending invoices
        2. Transfers due commissions
        3. Transfers open disputes
        4. Calculates opening balances
        5. Closes old financial year
        6. Activates new financial year
        
        Args:
            db: Database session
            from_fy_id: Source FY ID
            to_fy_id: Target FY ID
            organization_id: Organization ID
            performed_by: User performing closure
            
        Returns:
            Summary dict with all transfer counts
        """
        # Transfer data
        invoices_transferred = YearEndService.transfer_pending_invoices(
            db, from_fy_id, to_fy_id, organization_id, performed_by
        )
        
        commissions_transferred = YearEndService.transfer_due_commissions(
            db, from_fy_id, to_fy_id, organization_id, performed_by
        )
        
        disputes_transferred = YearEndService.transfer_open_disputes(
            db, from_fy_id, to_fy_id, organization_id, performed_by
        )
        
        # Calculate opening balances
        opening_balances = YearEndService.calculate_opening_balances(
            db, to_fy_id, organization_id
        )
        
        # Close old FY
        from_fy = db.query(FinancialYear).filter(FinancialYear.id == from_fy_id).first()
        from_fy.is_closed = True
        from_fy.is_active = False
        
        # Activate new FY
        to_fy = db.query(FinancialYear).filter(FinancialYear.id == to_fy_id).first()
        to_fy.is_active = True
        
        db.commit()
        
        return {
            'invoices_transferred': invoices_transferred,
            'commissions_transferred': commissions_transferred,
            'disputes_transferred': disputes_transferred,
            'opening_balances': opening_balances,
            'from_financial_year': from_fy.year_code,
            'to_financial_year': to_fy.year_code,
            'closed_at': datetime.utcnow().isoformat()
        }
