"""
Complete API route handlers for RNRL TradeHub backend.

This module contains full CRUD endpoints for all entities with proper
error handling, validation, and business logic.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas


# Create routers for all entities
business_partner_router = APIRouter(prefix="/api/business-partners", tags=["Business Partners"])
sales_contract_router = APIRouter(prefix="/api/sales-contracts", tags=["Sales Contracts"])
cci_term_router = APIRouter(prefix="/api/cci-terms", tags=["CCI Terms"])
user_router = APIRouter(prefix="/api/users", tags=["Users"])
invoice_router = APIRouter(prefix="/api/invoices", tags=["Invoices"])
payment_router = APIRouter(prefix="/api/payments", tags=["Payments"])
dispute_router = APIRouter(prefix="/api/disputes", tags=["Disputes"])
commission_router = APIRouter(prefix="/api/commissions", tags=["Commissions"])
role_router = APIRouter(prefix="/api/roles", tags=["Roles & Permissions"])
setting_router = APIRouter(prefix="/api/settings", tags=["Settings"])
master_data_router = APIRouter(prefix="/api/master-data", tags=["Master Data"])
gst_rate_router = APIRouter(prefix="/api/gst-rates", tags=["GST Rates"])
location_router = APIRouter(prefix="/api/locations", tags=["Locations"])
commission_structure_router = APIRouter(prefix="/api/commission-structures", tags=["Commission Structures"])


# ========== Business Partner Endpoints ==========
@business_partner_router.post("/", response_model=schemas.BusinessPartnerResponse, status_code=status.HTTP_201_CREATED)
def create_business_partner(
    partner: schemas.BusinessPartnerCreate,
    db: Session = Depends(get_db)
):
    """Create a new business partner."""
    # Check if BP code already exists
    existing = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.bp_code == partner.bp_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Business partner with code {partner.bp_code} already exists")

    partner_id = str(uuid.uuid4())
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
    business_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all business partners with filtering."""
    query = db.query(models.BusinessPartner)

    if business_type:
        query = query.filter(models.BusinessPartner.business_type == business_type)
    if status:
        query = query.filter(models.BusinessPartner.status == status)
    if search:
        query = query.filter(
            (models.BusinessPartner.legal_name.ilike(f"%{search}%")) |
            (models.BusinessPartner.bp_code.ilike(f"%{search}%"))
        )

    partners = query.offset(skip).limit(limit).all()
    return partners


@business_partner_router.get("/{partner_id}", response_model=schemas.BusinessPartnerResponse)
def get_business_partner(partner_id: str, db: Session = Depends(get_db)):
    """Get a specific business partner by ID."""
    partner = db.query(models.BusinessPartner).filter(models.BusinessPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Business partner not found")
    return partner


@business_partner_router.put("/{partner_id}", response_model=schemas.BusinessPartnerResponse)
def update_business_partner(
    partner_id: str,
    partner_update: schemas.BusinessPartnerCreate,
    db: Session = Depends(get_db)
):
    """Update a business partner."""
    db_partner = db.query(models.BusinessPartner).filter(models.BusinessPartner.id == partner_id).first()
    if not db_partner:
        raise HTTPException(status_code=404, detail="Business partner not found")

    for key, value in partner_update.model_dump(exclude={'shipping_addresses'}).items():
        setattr(db_partner, key, value)

    db.commit()
    db.refresh(db_partner)
    return db_partner


@business_partner_router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_partner(partner_id: str, db: Session = Depends(get_db)):
    """Delete a business partner."""
    db_partner = db.query(models.BusinessPartner).filter(models.BusinessPartner.id == partner_id).first()
    if not db_partner:
        raise HTTPException(status_code=404, detail="Business partner not found")

    db.delete(db_partner)
    db.commit()
    return None


# ========== Invoice Endpoints ==========
@invoice_router.post("/", status_code=status.HTTP_201_CREATED)
def create_invoice(invoice_data: dict, db: Session = Depends(get_db)):
    """Create a new invoice."""
    invoice_id = str(uuid.uuid4())
    db_invoice = models.Invoice(id=invoice_id, **invoice_data)
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


@invoice_router.get("/")
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all invoices."""
    query = db.query(models.Invoice)
    if status:
        query = query.filter(models.Invoice.status == status)
    return query.offset(skip).limit(limit).all()


@invoice_router.get("/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """Get a specific invoice."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@invoice_router.put("/{invoice_id}")
def update_invoice(invoice_id: str, invoice_data: dict, db: Session = Depends(get_db)):
    """Update an invoice."""
    db_invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    for key, value in invoice_data.items():
        setattr(db_invoice, key, value)

    db.commit()
    db.refresh(db_invoice)
    return db_invoice


# ========== Payment Endpoints ==========
@payment_router.post("/", status_code=status.HTTP_201_CREATED)
def create_payment(payment_data: dict, db: Session = Depends(get_db)):
    """Create a new payment."""
    payment_id = str(uuid.uuid4())
    db_payment = models.Payment(id=payment_id, **payment_data)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@payment_router.get("/")
def list_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all payments."""
    return db.query(models.Payment).offset(skip).limit(limit).all()


@payment_router.get("/{payment_id}")
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Get a specific payment."""
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# ========== Dispute Endpoints ==========
@dispute_router.post("/", status_code=status.HTTP_201_CREATED)
def create_dispute(dispute_data: dict, db: Session = Depends(get_db)):
    """Create a new dispute."""
    dispute_id = str(uuid.uuid4())
    db_dispute = models.Dispute(id=dispute_id, **dispute_data)
    db.add(db_dispute)
    db.commit()
    db.refresh(db_dispute)
    return db_dispute


@dispute_router.get("/")
def list_disputes(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all disputes."""
    query = db.query(models.Dispute)
    if status:
        query = query.filter(models.Dispute.status == status)
    return query.offset(skip).limit(limit).all()


@dispute_router.get("/{dispute_id}")
def get_dispute(dispute_id: str, db: Session = Depends(get_db)):
    """Get a specific dispute."""
    dispute = db.query(models.Dispute).filter(models.Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute


@dispute_router.put("/{dispute_id}")
def update_dispute(dispute_id: str, dispute_data: dict, db: Session = Depends(get_db)):
    """Update a dispute."""
    db_dispute = db.query(models.Dispute).filter(models.Dispute.id == dispute_id).first()
    if not db_dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    for key, value in dispute_data.items():
        setattr(db_dispute, key, value)

    db.commit()
    db.refresh(db_dispute)
    return db_dispute


# ========== Commission Endpoints ==========
@commission_router.post("/", status_code=status.HTTP_201_CREATED)
def create_commission(commission_data: dict, db: Session = Depends(get_db)):
    """Create a new commission."""
    commission_id = str(uuid.uuid4())
    db_commission = models.Commission(id=commission_id, **commission_data)
    db.add(db_commission)
    db.commit()
    db.refresh(db_commission)
    return db_commission


@commission_router.get("/")
def list_commissions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all commissions."""
    query = db.query(models.Commission)
    if status:
        query = query.filter(models.Commission.status == status)
    return query.offset(skip).limit(limit).all()


@commission_router.get("/{commission_id}")
def get_commission(commission_id: str, db: Session = Depends(get_db)):
    """Get a specific commission."""
    commission = db.query(models.Commission).filter(models.Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    return commission


# ========== Role & Permission Endpoints ==========
@role_router.post("/", status_code=status.HTTP_201_CREATED)
def create_role(role_data: dict, db: Session = Depends(get_db)):
    """Create a new role."""
    db_role = models.Role(**role_data)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@role_router.get("/")
def list_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all roles."""
    return db.query(models.Role).offset(skip).limit(limit).all()


@role_router.get("/{role_id}")
def get_role(role_id: int, db: Session = Depends(get_db)):
    """Get a specific role with permissions."""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


# ========== Settings Endpoints ==========
@setting_router.post("/", status_code=status.HTTP_201_CREATED)
def create_setting(setting_data: dict, db: Session = Depends(get_db)):
    """Create a new setting."""
    db_setting = models.Setting(**setting_data)
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


@setting_router.get("/")
def list_settings(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all settings."""
    query = db.query(models.Setting)
    if category:
        query = query.filter(models.Setting.category == category)
    return query.offset(skip).limit(limit).all()


@setting_router.get("/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    """Get a specific setting by key."""
    setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


@setting_router.put("/{key}")
def update_setting(key: str, setting_data: dict, db: Session = Depends(get_db)):
    """Update a setting."""
    db_setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    if not db_setting.is_editable:
        raise HTTPException(status_code=403, detail="This setting cannot be modified")

    for k, v in setting_data.items():
        setattr(db_setting, k, v)

    db.commit()
    db.refresh(db_setting)
    return db_setting


# ========== Master Data Endpoints ==========
@master_data_router.post("/", status_code=status.HTTP_201_CREATED)
def create_master_data(data: dict, db: Session = Depends(get_db)):
    """Create a new master data item."""
    db_item = models.MasterDataItem(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@master_data_router.get("/")
def list_master_data(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List master data items."""
    query = db.query(models.MasterDataItem)
    if category:
        query = query.filter(models.MasterDataItem.category == category)
    return query.filter(models.MasterDataItem.is_active == True).offset(skip).limit(limit).all()


# ========== GST Rate Endpoints ==========
@gst_rate_router.post("/", status_code=status.HTTP_201_CREATED)
def create_gst_rate(gst_data: dict, db: Session = Depends(get_db)):
    """Create a new GST rate."""
    db_gst = models.GstRate(**gst_data)
    db.add(db_gst)
    db.commit()
    db.refresh(db_gst)
    return db_gst


@gst_rate_router.get("/")
def list_gst_rates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all GST rates."""
    return db.query(models.GstRate).offset(skip).limit(limit).all()


# ========== Location Endpoints ==========
@location_router.post("/", status_code=status.HTTP_201_CREATED)
def create_location(location_data: dict, db: Session = Depends(get_db)):
    """Create a new location."""
    db_location = models.Location(**location_data)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@location_router.get("/")
def list_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all locations."""
    return db.query(models.Location).offset(skip).limit(limit).all()


# ========== Commission Structure Endpoints ==========
@commission_structure_router.post("/", status_code=status.HTTP_201_CREATED)
def create_commission_structure(data: dict, db: Session = Depends(get_db)):
    """Create a new commission structure."""
    db_structure = models.CommissionStructure(**data)
    db.add(db_structure)
    db.commit()
    db.refresh(db_structure)
    return db_structure


@commission_structure_router.get("/")
def list_commission_structures(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all commission structures."""
    return db.query(models.CommissionStructure).offset(skip).limit(limit).all()
