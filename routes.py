"""
API route handlers for RNRL TradeHub backend.

This module contains CRUD endpoints for all entities.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas


# Create routers
business_partner_router = APIRouter(prefix="/api/business-partners", tags=["Business Partners"])
sales_contract_router = APIRouter(prefix="/api/sales-contracts", tags=["Sales Contracts"])
cci_term_router = APIRouter(prefix="/api/cci-terms", tags=["CCI Terms"])
user_router = APIRouter(prefix="/api/users", tags=["Users"])


# Business Partner endpoints
@business_partner_router.post("/", response_model=schemas.BusinessPartnerResponse, status_code=status.HTTP_201_CREATED)
def create_business_partner(
    partner: schemas.BusinessPartnerCreate,
    db: Session = Depends(get_db)
):
    """Create a new business partner."""
    # Generate UUID for business partner
    partner_id = str(uuid.uuid4())

    # Create business partner
    db_partner = models.BusinessPartner(
        id=partner_id,
        **partner.model_dump(exclude={'shipping_addresses'})
    )

    db.add(db_partner)

    # Add shipping addresses
    for addr in partner.shipping_addresses:
        db_address = models.Address(
            id=str(uuid.uuid4()),
            business_partner_id=partner_id,
            **addr.model_dump()
        )
        db.add(db_address)

    db.commit()
    db.refresh(db_partner)
    return db_partner


@business_partner_router.get("/", response_model=List[schemas.BusinessPartnerResponse])
def list_business_partners(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all business partners."""
    partners = db.query(models.BusinessPartner).offset(skip).limit(limit).all()
    return partners


@business_partner_router.get("/{partner_id}", response_model=schemas.BusinessPartnerResponse)
def get_business_partner(partner_id: str, db: Session = Depends(get_db)):
    """Get a specific business partner by ID."""
    partner = db.query(models.BusinessPartner).filter(models.BusinessPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Business partner not found")
    return partner


# Sales Contract endpoints
@sales_contract_router.post("/", response_model=schemas.SalesContractResponse, status_code=status.HTTP_201_CREATED)
def create_sales_contract(
    contract: schemas.SalesContractCreate,
    db: Session = Depends(get_db)
):
    """Create a new sales contract."""
    contract_id = str(uuid.uuid4())

    db_contract = models.SalesContract(
        id=contract_id,
        **contract.model_dump()
    )

    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


@sales_contract_router.get("/", response_model=List[schemas.SalesContractResponse])
def list_sales_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all sales contracts."""
    contracts = db.query(models.SalesContract).offset(skip).limit(limit).all()
    return contracts


@sales_contract_router.get("/{contract_id}", response_model=schemas.SalesContractResponse)
def get_sales_contract(contract_id: str, db: Session = Depends(get_db)):
    """Get a specific sales contract by ID."""
    contract = db.query(models.SalesContract).filter(models.SalesContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Sales contract not found")
    return contract


# CCI Terms endpoints
@cci_term_router.post("/", response_model=schemas.CciTermResponse, status_code=status.HTTP_201_CREATED)
def create_cci_term(
    term: schemas.CciTermCreate,
    db: Session = Depends(get_db)
):
    """Create a new CCI term configuration."""
    db_term = models.CciTerm(**term.model_dump())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term


@cci_term_router.get("/", response_model=List[schemas.CciTermResponse])
def list_cci_terms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all CCI terms."""
    terms = db.query(models.CciTerm).offset(skip).limit(limit).all()
    return terms


@cci_term_router.get("/{term_id}", response_model=schemas.CciTermResponse)
def get_cci_term(term_id: int, db: Session = Depends(get_db)):
    """Get a specific CCI term by ID."""
    term = db.query(models.CciTerm).filter(models.CciTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="CCI term not found")
    return term


# User endpoints
@user_router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # In production, hash the password properly
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(user.password)

    db_user = models.User(
        name=user.name,
        email=user.email,
        role=user.role,
        password_hash=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@user_router.get("/", response_model=List[schemas.UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all users."""
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@user_router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
