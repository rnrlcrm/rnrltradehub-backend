"""
Client Portal API Routes.

This module provides API endpoints specific to the client portal where
client users can view and manage their contracts, invoices, payments, and profile.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
import models
from routes_auth import get_current_user
from access_control import (
    filter_contracts_by_user_type,
    filter_invoices_by_user_type,
    get_effective_business_partner_id,
    validate_sub_user_limit
)
from services.user_service import UserService


client_router = APIRouter(prefix="/api/client", tags=["Client Portal"])


# Schemas
class SubUserCreate(BaseModel):
    """Schema for creating a sub-user."""
    name: str
    email: EmailStr
    password: str


class SubUserResponse(BaseModel):
    """Schema for sub-user response."""
    id: int
    name: str
    email: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class ContractSummary(BaseModel):
    """Summary of a sales contract."""
    id: str
    sc_no: str
    date: str
    client_name: str
    vendor_name: str
    variety: str
    quantity_bales: int
    rate: float
    status: str

    class Config:
        from_attributes = True


class InvoiceSummary(BaseModel):
    """Summary of an invoice."""
    id: str
    invoice_no: str
    date: str
    amount: float
    status: str

    class Config:
        from_attributes = True


class PaymentSummary(BaseModel):
    """Summary of a payment."""
    id: str
    payment_id: str
    date: str
    amount: float
    method: str

    class Config:
        from_attributes = True


class BusinessPartnerProfile(BaseModel):
    """Business partner profile for client."""
    id: str
    bp_code: str
    legal_name: str
    organization: str
    business_type: str
    contact_person: str
    contact_email: str
    contact_phone: str
    address_line1: str
    city: str
    state: str
    country: str

    class Config:
        from_attributes = True


# Helper function to ensure user is CLIENT
def require_client_user(current_user: models.User = Depends(get_current_user)):
    """Ensure the current user is a CLIENT user."""
    if current_user.user_type != 'CLIENT':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint is for client users only."
        )
    return current_user


# Contract Endpoints
@client_router.get("/my-contracts", response_model=List[ContractSummary])
def list_my_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    Get all contracts where the user is the client (buyer).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional filter by contract status
        current_user: Current authenticated client user
        db: Database session
        
    Returns:
        List of contracts
    """
    query = db.query(models.SalesContract)
    query = filter_contracts_by_user_type(query, current_user, db)
    
    if status:
        query = query.filter(models.SalesContract.status == status)
    
    contracts = query.offset(skip).limit(limit).all()
    
    return [
        ContractSummary(
            id=c.id,
            sc_no=c.sc_no,
            date=c.date.isoformat(),
            client_name=c.client_name,
            vendor_name=c.vendor_name,
            variety=c.variety,
            quantity_bales=c.quantity_bales,
            rate=c.rate,
            status=c.status
        )
        for c in contracts
    ]


@client_router.get("/my-contracts/{contract_id}")
def get_contract_details(
    contract_id: str,
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific contract.
    
    Args:
        contract_id: Contract ID
        current_user: Current authenticated client user
        db: Database session
        
    Returns:
        Contract details
        
    Raises:
        HTTPException: If contract not found or access denied
    """
    bp_id = get_effective_business_partner_id(current_user, db)
    
    contract = db.query(models.SalesContract).filter(
        models.SalesContract.id == contract_id,
        models.SalesContract.client_id == bp_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or access denied"
        )
    
    return contract


# Invoice Endpoints
@client_router.get("/my-invoices", response_model=List[InvoiceSummary])
def list_my_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    Get all invoices related to user's contracts.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional filter by invoice status
        current_user: Current authenticated client user
        db: Database session
        
    Returns:
        List of invoices
    """
    query = db.query(models.Invoice)
    query = filter_invoices_by_user_type(query, current_user, db)
    
    if status:
        query = query.filter(models.Invoice.status == status)
    
    invoices = query.offset(skip).limit(limit).all()
    
    return [
        InvoiceSummary(
            id=i.id,
            invoice_no=i.invoice_no,
            date=i.date.isoformat(),
            amount=i.amount,
            status=i.status
        )
        for i in invoices
    ]


# Payment Endpoints
@client_router.get("/my-payments", response_model=List[PaymentSummary])
def list_my_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    Get all payments made by the user.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated client user
        db: Database session
        
    Returns:
        List of payments
    """
    bp_id = get_effective_business_partner_id(current_user, db)
    
    # Get payments for invoices related to user's contracts
    query = db.query(models.Payment).join(
        models.Invoice, models.Payment.invoice_id == models.Invoice.id
    ).join(
        models.SalesContract, models.Invoice.sales_contract_id == models.SalesContract.id
    ).filter(
        models.SalesContract.client_id == bp_id
    )
    
    payments = query.offset(skip).limit(limit).all()
    
    return [
        PaymentSummary(
            id=p.id,
            payment_id=p.payment_id,
            date=p.date.isoformat(),
            amount=p.amount,
            method=p.method
        )
        for p in payments
    ]


# Profile Endpoints
@client_router.get("/my-profile", response_model=BusinessPartnerProfile)
def get_my_profile(
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    Get user's business partner profile.
    
    Args:
        current_user: Current authenticated client user
        db: Database session
        
    Returns:
        Business partner profile
        
    Raises:
        HTTPException: If business partner not found
    """
    bp_id = get_effective_business_partner_id(current_user, db)
    
    if not bp_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business partner profile not found"
        )
    
    bp = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.id == bp_id
    ).first()
    
    if not bp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business partner profile not found"
        )
    
    return BusinessPartnerProfile(
        id=bp.id,
        bp_code=bp.bp_code,
        legal_name=bp.legal_name,
        organization=bp.organization,
        business_type=bp.business_type,
        contact_person=bp.contact_person,
        contact_email=bp.contact_email,
        contact_phone=bp.contact_phone,
        address_line1=bp.address_line1,
        city=bp.city,
        state=bp.state,
        country=bp.country
    )


# Sub-User Management Endpoints
@client_router.post("/sub-users", response_model=SubUserResponse, status_code=status.HTTP_201_CREATED)
def create_sub_user(
    sub_user_data: SubUserCreate,
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    Create a sub-user under the current user (max 2 sub-users).
    
    Sub-users automatically inherit:
    - user_type from parent
    - business_partner_id from parent
    - Same access rights as parent
    
    Args:
        sub_user_data: Sub-user creation data
        current_user: Current authenticated client user
        db: Database session
        
    Returns:
        Created sub-user
        
    Raises:
        HTTPException: If validation fails or limit exceeded
    """
    # Validate sub-user limit
    validate_sub_user_limit(current_user, db)
    
    # Validate email is unique
    UserService.validate_email_unique(db, sub_user_data.email)
    
    # Create sub-user
    sub_user = models.User(
        name=sub_user_data.name,
        email=sub_user_data.email,
        password_hash=UserService.hash_password(sub_user_data.password),
        user_type=current_user.user_type,  # Inherit user type
        business_partner_id=current_user.business_partner_id,  # Inherit business partner
        parent_user_id=current_user.id,  # Link to parent
        is_parent=False,  # Mark as sub-user
        is_active=True
    )
    
    db.add(sub_user)
    db.commit()
    db.refresh(sub_user)
    
    return SubUserResponse(
        id=sub_user.id,
        name=sub_user.name,
        email=sub_user.email,
        is_active=sub_user.is_active,
        created_at=sub_user.created_at.isoformat()
    )


@client_router.get("/sub-users", response_model=List[SubUserResponse])
def list_sub_users(
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    List all sub-users created by the current user.
    
    Args:
        current_user: Current authenticated client user
        db: Database session
        
    Returns:
        List of sub-users
        
    Raises:
        HTTPException: If current user is a sub-user
    """
    if current_user.parent_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sub-users cannot view other sub-users"
        )
    
    sub_users = db.query(models.User).filter(
        models.User.parent_user_id == current_user.id
    ).all()
    
    return [
        SubUserResponse(
            id=su.id,
            name=su.name,
            email=su.email,
            is_active=su.is_active,
            created_at=su.created_at.isoformat()
        )
        for su in sub_users
    ]


@client_router.delete("/sub-users/{sub_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sub_user(
    sub_user_id: int,
    current_user: models.User = Depends(require_client_user),
    db: Session = Depends(get_db)
):
    """
    Delete a sub-user.
    
    Args:
        sub_user_id: ID of sub-user to delete
        current_user: Current authenticated client user
        db: Database session
        
    Raises:
        HTTPException: If sub-user not found or not owned by current user
    """
    if current_user.parent_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sub-users cannot delete other sub-users"
        )
    
    sub_user = db.query(models.User).filter(
        models.User.id == sub_user_id,
        models.User.parent_user_id == current_user.id
    ).first()
    
    if not sub_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-user not found or not owned by you"
        )
    
    db.delete(sub_user)
    db.commit()
    
    return None
