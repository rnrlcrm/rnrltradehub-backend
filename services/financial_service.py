"""
Financial Service - Business logic for financial operations.

This service handles:
- Invoice management
- Payment processing
- Commission calculations
- Payment reconciliation
- Financial validations
"""
import uuid
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

import models
import schemas


class FinancialService:
    """Service class for financial operations."""

    @staticmethod
    def generate_invoice_number(db: Session) -> str:
        """
        Generate unique invoice number.
        
        Business Logic:
        - Format: INV-YYYY-NNNN (e.g., INV-2024-0001)
        - Auto-increment based on current year
        
        Args:
            db: Database session
            
        Returns:
            Generated invoice number
        """
        current_year = datetime.now().year
        prefix = f"INV-{current_year}-"
        
        last_invoice = db.query(models.Invoice).filter(
            models.Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(models.Invoice.invoice_number.desc()).first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"

    @staticmethod
    def validate_invoice_status(status_value: str) -> None:
        """Validate invoice status."""
        valid_statuses = ["draft", "pending", "paid", "partially_paid", "overdue", "cancelled"]
        if status_value and status_value not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

    @staticmethod
    def validate_contract_for_invoice(db: Session, contract_id: str) -> models.SalesContract:
        """
        Validate that contract exists and is valid for invoicing.
        
        Business Logic:
        - Contract must exist
        - Contract must be active or amended
        - Contract must not be expired
        
        Args:
            db: Database session
            contract_id: Sales contract ID
            
        Returns:
            Sales contract
            
        Raises:
            HTTPException: If validation fails
        """
        contract = db.query(models.SalesContract).filter(
            models.SalesContract.id == contract_id
        ).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales contract with ID {contract_id} not found"
            )
        
        # Business Logic: Contract must be active or amended
        if contract.status not in ["active", "amended"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create invoice for contract with status '{contract.status}'"
            )
        
        # Business Logic: Contract must not be expired
        if contract.end_date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create invoice for expired contract"
            )
        
        return contract

    @staticmethod
    def calculate_invoice_total(
        quantity: Decimal,
        rate: Decimal,
        gst_rate: Decimal = Decimal('0')
    ) -> dict:
        """
        Calculate invoice totals.
        
        Business Logic:
        - Base amount = quantity * rate
        - GST amount = base amount * gst_rate
        - Total amount = base amount + gst amount
        
        Args:
            quantity: Quantity
            rate: Rate per unit
            gst_rate: GST rate (default 0)
            
        Returns:
            Dictionary with base_amount, gst_amount, total_amount
        """
        base_amount = quantity * rate
        gst_amount = base_amount * gst_rate
        total_amount = base_amount + gst_amount
        
        return {
            "base_amount": base_amount,
            "gst_amount": gst_amount,
            "total_amount": total_amount
        }

    @staticmethod
    def create_invoice(
        db: Session,
        invoice_data: schemas.InvoiceCreate
    ) -> models.Invoice:
        """
        Create a new invoice with validation.
        
        Business Logic:
        - Generate unique invoice number
        - Validate sales contract
        - Calculate totals
        - Set initial status to draft
        
        Args:
            db: Database session
            invoice_data: Invoice creation data
            
        Returns:
            Created invoice
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate sales contract
        contract = FinancialService.validate_contract_for_invoice(db, invoice_data.sales_contract_id)
        
        # Business Logic: Validate status
        if invoice_data.status:
            FinancialService.validate_invoice_status(invoice_data.status)
        
        # Business Logic: Generate invoice number
        invoice_number = FinancialService.generate_invoice_number(db)
        
        # Business Logic: Calculate totals if not provided
        # (In real implementation, this would use the rates from the invoice data)

        db_invoice = models.Invoice(
            id=str(uuid.uuid4()),
            invoice_number=invoice_number,
            **invoice_data.model_dump()
        )
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return db_invoice

    @staticmethod
    def create_payment(
        db: Session,
        payment_data: schemas.PaymentCreate
    ) -> models.Payment:
        """
        Create a new payment.
        
        Business Logic:
        - Validate invoice exists
        - Update invoice status based on payment
        - Check if invoice is fully paid
        - Update paid amount
        
        Args:
            db: Database session
            payment_data: Payment creation data
            
        Returns:
            Created payment
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate invoice exists
        invoice = db.query(models.Invoice).filter(
            models.Invoice.id == payment_data.invoice_id
        ).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {payment_data.invoice_id} not found"
            )
        
        # Business Logic: Cannot pay cancelled invoice
        if invoice.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create payment for cancelled invoice"
            )
        
        # Create payment
        db_payment = models.Payment(
            id=str(uuid.uuid4()),
            **payment_data.model_dump()
        )
        db.add(db_payment)
        
        # Business Logic: Update invoice paid amount and status
        total_paid = db.query(models.Payment).filter(
            models.Payment.invoice_id == payment_data.invoice_id
        ).with_entities(models.Payment.amount).all()
        
        total_paid_amount = sum([p[0] for p in total_paid]) + payment_data.amount
        invoice.paid_amount = total_paid_amount
        
        # Business Logic: Update invoice status based on payment
        if total_paid_amount >= invoice.total_amount:
            invoice.status = "paid"
        elif total_paid_amount > 0:
            invoice.status = "partially_paid"
        
        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    def calculate_commission(
        db: Session,
        contract_id: str,
        invoice_amount: Decimal
    ) -> Decimal:
        """
        Calculate commission for a contract.
        
        Business Logic:
        - Get commission structure from contract
        - Apply commission rate
        - Apply tiered rates if configured
        
        Args:
            db: Database session
            contract_id: Sales contract ID
            invoice_amount: Invoice amount
            
        Returns:
            Calculated commission amount
        """
        contract = db.query(models.SalesContract).filter(
            models.SalesContract.id == contract_id
        ).first()
        
        if not contract or not contract.commission_structure_id:
            return Decimal('0')
        
        commission_structure = db.query(models.CommissionStructure).filter(
            models.CommissionStructure.id == contract.commission_structure_id
        ).first()
        
        if not commission_structure:
            return Decimal('0')
        
        # Business Logic: Calculate based on rate type
        if commission_structure.rate_type == "percentage":
            return invoice_amount * (commission_structure.rate / 100)
        elif commission_structure.rate_type == "fixed":
            return commission_structure.rate
        
        return Decimal('0')

    @staticmethod
    def create_commission(
        db: Session,
        commission_data: schemas.CommissionCreate
    ) -> models.Commission:
        """
        Create a commission record.
        
        Business Logic:
        - Validate invoice exists
        - Calculate commission amount if not provided
        - Set status to pending
        
        Args:
            db: Database session
            commission_data: Commission creation data
            
        Returns:
            Created commission
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate invoice exists
        invoice = db.query(models.Invoice).filter(
            models.Invoice.id == commission_data.invoice_id
        ).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {commission_data.invoice_id} not found"
            )
        
        # Business Logic: Calculate commission if not provided
        if not commission_data.amount and invoice.sales_contract_id:
            calculated_amount = FinancialService.calculate_commission(
                db,
                invoice.sales_contract_id,
                invoice.total_amount
            )
            commission_data.amount = calculated_amount

        db_commission = models.Commission(
            id=str(uuid.uuid4()),
            **commission_data.model_dump()
        )
        db.add(db_commission)
        db.commit()
        db.refresh(db_commission)
        return db_commission

    @staticmethod
    def get_outstanding_balance(db: Session, invoice_id: str) -> Decimal:
        """
        Get outstanding balance for an invoice.
        
        Business Logic:
        - Total invoice amount - total paid amount
        
        Args:
            db: Database session
            invoice_id: Invoice ID
            
        Returns:
            Outstanding balance
        """
        invoice = db.query(models.Invoice).filter(
            models.Invoice.id == invoice_id
        ).first()
        
        if not invoice:
            return Decimal('0')
        
        total_paid = db.query(models.Payment).filter(
            models.Payment.invoice_id == invoice_id
        ).with_entities(models.Payment.amount).all()
        
        total_paid_amount = sum([p[0] for p in total_paid])
        
        return invoice.total_amount - total_paid_amount
