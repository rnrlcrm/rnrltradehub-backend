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


# ========== User Endpoints ==========
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

    # Hash password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(user.password)

    db_user = models.User(
        name=user.name,
        email=user.email,
        role_name=user.role,
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


@user_router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    """Update a user."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate email uniqueness if being updated
    if user_data.email and user_data.email != user.email:
        existing = db.query(models.User).filter(
            models.User.email == user_data.email,
            models.User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"User with email {user_data.email} already exists"
            )

    # Update fields
    update_dict = user_data.model_dump(exclude_unset=True, exclude={'password'})
    for key, value in update_dict.items():
        if key == 'role':
            setattr(user, 'role_name', value)
        else:
            setattr(user, key, value)

    # Hash password if being updated
    if user_data.password:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user.password_hash = pwd_context.hash(user_data.password)

    db.commit()
    db.refresh(user)
    return user


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete (deactivate) a user."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Soft delete - set is_active to False
    user.is_active = False

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
# NOTE: Specific routes like /users must come BEFORE generic routes like /{key}
# to ensure FastAPI matches them correctly

# ========== Settings/Users Endpoints ==========
@setting_router.get("/users", response_model=List[schemas.SettingsUserResponse])
def list_settings_users(
    userType: Optional[str] = Query(None, alias="userType"),
    isActive: Optional[bool] = Query(None, alias="isActive"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List users with filtering options for settings module.
    
    Query Parameters:
    - userType: Filter by user type (primary, sub_user)
    - isActive: Filter by active status (true/false)
    """
    from sqlalchemy.orm import joinedload
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        query = db.query(models.User).options(joinedload(models.User.role))
        
        if userType:
            query = query.filter(models.User.user_type == userType)
        if isActive is not None:
            query = query.filter(models.User.is_active == isActive)
        
        users = query.offset(skip).limit(limit).all()
        
        # Manually construct response to ensure role_name is properly populated
        response_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role_id": user.role_id,
                "role_name": user.role.name if user.role else None,
                "is_active": user.is_active,
                "user_type": user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type),
                "client_id": user.client_id,
                "vendor_id": user.vendor_id,
                "parent_user_id": user.parent_user_id,
                "max_sub_users": user.max_sub_users,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            response_data.append(user_dict)
        
        return response_data
    except Exception as e:
        logger.error(f"Error in list_settings_users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@setting_router.post("/users", response_model=schemas.SettingsUserResponse, status_code=status.HTTP_201_CREATED)
def create_settings_user(
    user_data: schemas.SettingsUserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user through settings module.
    
    Supports creating both primary users and sub-users with multi-tenant capabilities.
    """
    # Check if user with email already exists
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists"
        )
    
    # Validate role if provided
    if user_data.role_id:
        role = db.query(models.Role).filter(models.Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {user_data.role_id} not found"
            )
    
    # Validate parent user if sub_user
    if user_data.user_type == schemas.UserType.SUB_USER and user_data.parent_user_id:
        parent = db.query(models.User).filter(models.User.id == user_data.parent_user_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent user with ID {user_data.parent_user_id} not found"
            )
        
        # Check sub-user limit
        sub_user_count = db.query(models.User).filter(
            models.User.parent_user_id == user_data.parent_user_id
        ).count()
        if sub_user_count >= parent.max_sub_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent user has reached maximum sub-user limit of {parent.max_sub_users}"
            )
    
    # Hash password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(user_data.password)
    
    # Create user
    db_user = models.User(
        **user_data.model_dump(exclude={'password'}),
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Manually construct response to ensure role_name is properly populated
    from sqlalchemy.orm import joinedload
    db_user = db.query(models.User).options(joinedload(models.User.role)).filter(
        models.User.id == db_user.id
    ).first()
    
    return {
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "role_id": db_user.role_id,
        "role_name": db_user.role.name if db_user.role else None,
        "is_active": db_user.is_active,
        "user_type": db_user.user_type.value if hasattr(db_user.user_type, 'value') else str(db_user.user_type),
        "client_id": db_user.client_id,
        "vendor_id": db_user.vendor_id,
        "parent_user_id": db_user.parent_user_id,
        "max_sub_users": db_user.max_sub_users,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at
    }


@setting_router.put("/users/{user_id}", response_model=schemas.SettingsUserResponse)
def update_settings_user(
    user_id: int,
    user_data: schemas.SettingsUserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a user through settings module.
    
    Allows updating user details including role, status, and multi-tenant associations.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Validate email uniqueness if being updated
    if user_data.email and user_data.email != user.email:
        existing = db.query(models.User).filter(
            models.User.email == user_data.email,
            models.User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists"
            )
    
    # Validate role if being updated
    if user_data.role_id:
        role = db.query(models.Role).filter(models.Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {user_data.role_id} not found"
            )
    
    # Update fields
    update_dict = user_data.model_dump(exclude_unset=True, exclude={'password'})
    for key, value in update_dict.items():
        setattr(user, key, value)
    
    # Hash password if being updated
    if user_data.password:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user.password_hash = pwd_context.hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    # Manually construct response to ensure role_name is properly populated
    from sqlalchemy.orm import joinedload
    user = db.query(models.User).options(joinedload(models.User.role)).filter(
        models.User.id == user_id
    ).first()
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role_id": user.role_id,
        "role_name": user.role.name if user.role else None,
        "is_active": user.is_active,
        "user_type": user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type),
        "client_id": user.client_id,
        "vendor_id": user.vendor_id,
        "parent_user_id": user.parent_user_id,
        "max_sub_users": user.max_sub_users,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


@setting_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_settings_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) a user through settings module.
    
    Users are soft-deleted by setting is_active to False.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Soft delete - set is_active to False
    user.is_active = False
    
    db.commit()
    return None


# ========== General Settings Endpoints ==========
# NOTE: These generic routes must come AFTER specific routes like /users

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


# ========== Document/File Storage Endpoints ==========
document_router = APIRouter(prefix="/api/documents", tags=["Documents & Files"])

@document_router.post("/", status_code=status.HTTP_201_CREATED)
def create_document(document_data: dict, db: Session = Depends(get_db)):
    """Create a new document record."""
    document_id = str(uuid.uuid4())
    db_document = models.Document(id=document_id, **document_data)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@document_router.get("/")
def list_documents(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    document_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List documents with filtering."""
    query = db.query(models.Document).filter(models.Document.is_active == True)
    if entity_type:
        query = query.filter(models.Document.entity_type == entity_type)
    if entity_id:
        query = query.filter(models.Document.entity_id == entity_id)
    if document_type:
        query = query.filter(models.Document.document_type == document_type)
    return query.offset(skip).limit(limit).all()


@document_router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get a specific document."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@document_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Soft delete a document."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document.is_active = False
    db.commit()
    return None


# ========== Email Template Endpoints ==========
email_template_router = APIRouter(prefix="/api/email-templates", tags=["Email System"])

@email_template_router.post("/", status_code=status.HTTP_201_CREATED)
def create_email_template(template_data: dict, db: Session = Depends(get_db)):
    """Create a new email template."""
    db_template = models.EmailTemplate(**template_data)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@email_template_router.get("/")
def list_email_templates(
    category: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List email templates."""
    query = db.query(models.EmailTemplate)
    if category:
        query = query.filter(models.EmailTemplate.category == category)
    if is_active is not None:
        query = query.filter(models.EmailTemplate.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@email_template_router.get("/{template_id}")
def get_email_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific email template."""
    template = db.query(models.EmailTemplate).filter(models.EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    return template


@email_template_router.put("/{template_id}")
def update_email_template(template_id: int, template_data: dict, db: Session = Depends(get_db)):
    """Update an email template."""
    db_template = db.query(models.EmailTemplate).filter(models.EmailTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Email template not found")
    for key, value in template_data.items():
        setattr(db_template, key, value)
    db.commit()
    db.refresh(db_template)
    return db_template


# ========== Email Log Endpoints ==========
email_log_router = APIRouter(prefix="/api/email-logs", tags=["Email System"])

@email_log_router.get("/")
def list_email_logs(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List email logs."""
    query = db.query(models.EmailLog)
    if status:
        query = query.filter(models.EmailLog.status == status)
    return query.order_by(models.EmailLog.created_at.desc()).offset(skip).limit(limit).all()


@email_log_router.get("/{log_id}")
def get_email_log(log_id: int, db: Session = Depends(get_db)):
    """Get a specific email log."""
    log = db.query(models.EmailLog).filter(models.EmailLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")
    return log


# ========== Data Retention Policy Endpoints ==========
retention_policy_router = APIRouter(prefix="/api/retention-policies", tags=["Compliance"])

@retention_policy_router.post("/", status_code=status.HTTP_201_CREATED)
def create_retention_policy(policy_data: dict, db: Session = Depends(get_db)):
    """Create a new data retention policy."""
    db_policy = models.DataRetentionPolicy(**policy_data)
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy


@retention_policy_router.get("/")
def list_retention_policies(
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List data retention policies."""
    query = db.query(models.DataRetentionPolicy)
    if is_active is not None:
        query = query.filter(models.DataRetentionPolicy.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@retention_policy_router.get("/{policy_id}")
def get_retention_policy(policy_id: int, db: Session = Depends(get_db)):
    """Get a specific retention policy."""
    policy = db.query(models.DataRetentionPolicy).filter(models.DataRetentionPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Retention policy not found")
    return policy


@retention_policy_router.put("/{policy_id}")
def update_retention_policy(policy_id: int, policy_data: dict, db: Session = Depends(get_db)):
    """Update a retention policy."""
    db_policy = db.query(models.DataRetentionPolicy).filter(models.DataRetentionPolicy.id == policy_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="Retention policy not found")
    for key, value in policy_data.items():
        setattr(db_policy, key, value)
    db.commit()
    db.refresh(db_policy)
    return db_policy


# ========== Data Access Log Endpoints ==========
access_log_router = APIRouter(prefix="/api/access-logs", tags=["Compliance"])

@access_log_router.post("/", status_code=status.HTTP_201_CREATED)
def log_data_access(access_data: dict, db: Session = Depends(get_db)):
    """Log a data access event."""
    db_log = models.DataAccessLog(**access_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@access_log_router.get("/")
def list_access_logs(
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List data access logs."""
    query = db.query(models.DataAccessLog)
    if user_id:
        query = query.filter(models.DataAccessLog.user_id == user_id)
    if entity_type:
        query = query.filter(models.DataAccessLog.entity_type == entity_type)
    if action:
        query = query.filter(models.DataAccessLog.action == action)
    return query.order_by(models.DataAccessLog.accessed_at.desc()).offset(skip).limit(limit).all()


# ========== Consent Record Endpoints ==========
consent_router = APIRouter(prefix="/api/consent-records", tags=["Compliance - GDPR"])

@consent_router.post("/", status_code=status.HTTP_201_CREATED)
def create_consent_record(consent_data: dict, db: Session = Depends(get_db)):
    """Create a new consent record."""
    consent = models.ConsentRecord(**consent_data)
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


@consent_router.get("/")
def list_consent_records(
    user_id: Optional[int] = None,
    consent_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List consent records."""
    query = db.query(models.ConsentRecord)
    if user_id:
        query = query.filter(models.ConsentRecord.user_id == user_id)
    if consent_type:
        query = query.filter(models.ConsentRecord.consent_type == consent_type)
    return query.offset(skip).limit(limit).all()


@consent_router.put("/{consent_id}/withdraw")
def withdraw_consent(consent_id: int, db: Session = Depends(get_db)):
    """Withdraw a consent."""
    consent = db.query(models.ConsentRecord).filter(models.ConsentRecord.id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")
    consent.consent_given = False
    consent.withdrawn_date = datetime.utcnow()
    db.commit()
    db.refresh(consent)
    return consent


# ========== Data Export Request Endpoints ==========
export_request_router = APIRouter(prefix="/api/data-export-requests", tags=["Compliance - GDPR"])

@export_request_router.post("/", status_code=status.HTTP_201_CREATED)
def create_export_request(request_data: dict, db: Session = Depends(get_db)):
    """Create a new data export/deletion request."""
    request_id = str(uuid.uuid4())
    db_request = models.DataExportRequest(id=request_id, **request_data)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@export_request_router.get("/")
def list_export_requests(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List data export requests."""
    query = db.query(models.DataExportRequest)
    if status:
        query = query.filter(models.DataExportRequest.status == status)
    if request_type:
        query = query.filter(models.DataExportRequest.request_type == request_type)
    return query.order_by(models.DataExportRequest.requested_at.desc()).offset(skip).limit(limit).all()


@export_request_router.get("/{request_id}")
def get_export_request(request_id: str, db: Session = Depends(get_db)):
    """Get a specific export request."""
    request = db.query(models.DataExportRequest).filter(models.DataExportRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Export request not found")
    return request


# ========== Security Event Endpoints ==========
security_event_router = APIRouter(prefix="/api/security-events", tags=["Security & Compliance"])

@security_event_router.post("/", status_code=status.HTTP_201_CREATED)
def log_security_event(event_data: dict, db: Session = Depends(get_db)):
    """Log a security event."""
    event = models.SecurityEvent(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@security_event_router.get("/")
def list_security_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List security events."""
    query = db.query(models.SecurityEvent)
    if event_type:
        query = query.filter(models.SecurityEvent.event_type == event_type)
    if severity:
        query = query.filter(models.SecurityEvent.severity == severity)
    if resolved is not None:
        query = query.filter(models.SecurityEvent.resolved == resolved)
    return query.order_by(models.SecurityEvent.occurred_at.desc()).offset(skip).limit(limit).all()


@security_event_router.put("/{event_id}/resolve")
def resolve_security_event(event_id: int, db: Session = Depends(get_db)):
    """Mark a security event as resolved."""
    event = db.query(models.SecurityEvent).filter(models.SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Security event not found")
    event.resolved = True
    event.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    return event


# ========== System Configuration Endpoints ==========
sys_config_router = APIRouter(prefix="/api/system-config", tags=["System Configuration"])

@sys_config_router.post("/", status_code=status.HTTP_201_CREATED)
def create_system_config(config_data: dict, db: Session = Depends(get_db)):
    """Create a new system configuration."""
    db_config = models.SystemConfiguration(**config_data)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@sys_config_router.get("/")
def list_system_configs(
    category: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List system configurations."""
    query = db.query(models.SystemConfiguration)
    if category:
        query = query.filter(models.SystemConfiguration.category == category)
    if is_active is not None:
        query = query.filter(models.SystemConfiguration.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@sys_config_router.get("/{config_key}")
def get_system_config(config_key: str, db: Session = Depends(get_db)):
    """Get a specific system configuration."""
    config = db.query(models.SystemConfiguration).filter(
        models.SystemConfiguration.config_key == config_key
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@sys_config_router.put("/{config_key}")
def update_system_config(config_key: str, config_data: dict, db: Session = Depends(get_db)):
    """Update a system configuration."""
    db_config = db.query(models.SystemConfiguration).filter(
        models.SystemConfiguration.config_key == config_key
    ).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    for key, value in config_data.items():
        setattr(db_config, key, value)
    db.commit()
    db.refresh(db_config)
    return db_config
