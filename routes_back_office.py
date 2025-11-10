"""
Back Office Portal API Routes.

This module provides API endpoints specific to the back office portal where
back office staff have full access to all data and can manage the system.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
import models
from routes_auth import get_current_user


back_office_router = APIRouter(prefix="/api/back-office", tags=["Back Office Portal"])


# Helper function to ensure user is BACK_OFFICE
def require_back_office_user(current_user: models.User = Depends(get_current_user)):
    """Ensure the current user is a BACK_OFFICE user."""
    if current_user.user_type != 'BACK_OFFICE':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is for back office users only."
        )
    return current_user


# Business Partner Endpoints
@back_office_router.get("/business-partners")
def list_all_business_partners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    business_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    List all business partners (full access for back office).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        business_type: Optional filter by business type
        status: Optional filter by status
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        List of all business partners
    """
    query = db.query(models.BusinessPartner)
    
    if business_type:
        query = query.filter(models.BusinessPartner.business_type == business_type)
    
    if status:
        query = query.filter(models.BusinessPartner.status == status)
    
    return query.offset(skip).limit(limit).all()


@back_office_router.get("/business-partners/{partner_id}")
def get_business_partner(
    partner_id: str,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific business partner by ID.
    
    Args:
        partner_id: Business partner ID
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        Business partner details
        
    Raises:
        HTTPException: If business partner not found
    """
    partner = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.id == partner_id
    ).first()
    
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business partner not found"
        )
    
    return partner


# Sales Contract Endpoints
@back_office_router.get("/sales-contracts")
def list_all_sales_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    List all sales contracts (full access for back office).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional filter by contract status
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        List of all sales contracts
    """
    query = db.query(models.SalesContract)
    
    if status:
        query = query.filter(models.SalesContract.status == status)
    
    return query.offset(skip).limit(limit).all()


@back_office_router.get("/sales-contracts/{contract_id}")
def get_sales_contract(
    contract_id: str,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific sales contract by ID.
    
    Args:
        contract_id: Sales contract ID
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        Sales contract details
        
    Raises:
        HTTPException: If contract not found
    """
    contract = db.query(models.SalesContract).filter(
        models.SalesContract.id == contract_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales contract not found"
        )
    
    return contract


# Invoice Endpoints
@back_office_router.get("/invoices")
def list_all_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    List all invoices (full access for back office).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional filter by invoice status
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        List of all invoices
    """
    query = db.query(models.Invoice)
    
    if status:
        query = query.filter(models.Invoice.status == status)
    
    return query.offset(skip).limit(limit).all()


@back_office_router.get("/invoices/{invoice_id}")
def get_invoice(
    invoice_id: str,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific invoice by ID.
    
    Args:
        invoice_id: Invoice ID
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        Invoice details
        
    Raises:
        HTTPException: If invoice not found
    """
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice


# Payment Endpoints
@back_office_router.get("/payments")
def list_all_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    List all payments (full access for back office).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        List of all payments
    """
    query = db.query(models.Payment)
    return query.offset(skip).limit(limit).all()


@back_office_router.get("/payments/{payment_id}")
def get_payment(
    payment_id: str,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific payment by ID.
    
    Args:
        payment_id: Payment ID
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        Payment details
        
    Raises:
        HTTPException: If payment not found
    """
    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payment


# User Management Endpoints
@back_office_router.get("/users")
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_type: Optional[str] = None,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    List all users in the system (full access for back office).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        user_type: Optional filter by user type
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        List of all users
    """
    query = db.query(models.User)
    
    if user_type:
        query = query.filter(models.User.user_type == user_type)
    
    return query.offset(skip).limit(limit).all()


@back_office_router.get("/users/{user_id}")
def get_user(
    user_id: int,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.
    
    Args:
        user_id: User ID
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        User details
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# Dispute Endpoints
@back_office_router.get("/disputes")
def list_all_disputes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    List all disputes (full access for back office).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional filter by dispute status
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        List of all disputes
    """
    query = db.query(models.Dispute)
    
    if status:
        query = query.filter(models.Dispute.status == status)
    
    return query.offset(skip).limit(limit).all()


# Commission Endpoints
@back_office_router.get("/commissions")
def list_all_commissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: models.User = Depends(require_back_office_user),
    db: Session = Depends(get_db)
):
    """
    List all commissions (full access for back office).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional filter by commission status
        current_user: Current authenticated back office user
        db: Database session
        
    Returns:
        List of all commissions
    """
    query = db.query(models.Commission)
    
    if status:
        query = query.filter(models.Commission.status == status)
    
    return query.offset(skip).limit(limit).all()
