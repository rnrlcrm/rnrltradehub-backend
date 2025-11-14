"""
Master Data API routes for RNRL TradeHub backend.

This module contains CRUD endpoints for all master data entities:
- Organization Master
- Financial Year Master  
- Location Master
- Commodity Master
- GST Rates
- Commission Structures
- Settings
"""
import uuid
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

logger = logging.getLogger(__name__)

# Create routers for master data
organization_router = APIRouter(prefix="/api/organizations", tags=["Organization Master"])
financial_year_router = APIRouter(prefix="/api/financial-years", tags=["Financial Year Master"])
commodity_router = APIRouter(prefix="/api/commodities", tags=["Commodity Master"])
location_router = APIRouter(prefix="/api/locations", tags=["Location Master"])
gst_rate_router = APIRouter(prefix="/api/gst-rates", tags=["GST Rate Master"])
commission_structure_router = APIRouter(prefix="/api/commission-structures", tags=["Commission Structure Master"])
setting_router = APIRouter(prefix="/api/settings", tags=["Settings Master"])
master_data_router = APIRouter(prefix="/api/master-data", tags=["Generic Master Data"])


# ========== Organization Master Endpoints ==========
@organization_router.post("/", status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: schemas.OrganizationCreate,
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    # Check if PAN already exists
    existing = db.query(models.Organization).filter(
        models.Organization.pan == org_data.pan
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Organization with PAN {org_data.pan} already exists"
        )
    
    db_org = models.Organization(**org_data.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


@organization_router.get("/")
def list_organizations(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all organizations."""
    query = db.query(models.Organization)
    
    if is_active is not None:
        query = query.filter(models.Organization.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


@organization_router.get("/{org_id}")
def get_organization(org_id: int, db: Session = Depends(get_db)):
    """Get organization by ID."""
    org = db.query(models.Organization).filter(
        models.Organization.id == org_id
    ).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org


@organization_router.put("/{org_id}")
def update_organization(
    org_id: int,
    org_data: schemas.OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """Update organization."""
    org = db.query(models.Organization).filter(
        models.Organization.id == org_id
    ).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check PAN uniqueness if being updated
    if org_data.pan and org_data.pan != org.pan:
        existing = db.query(models.Organization).filter(
            models.Organization.pan == org_data.pan,
            models.Organization.id != org_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Organization with PAN {org_data.pan} already exists"
            )
    
    for key, value in org_data.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    
    db.commit()
    db.refresh(org)
    return org


@organization_router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(org_id: int, db: Session = Depends(get_db)):
    """Soft delete organization."""
    org = db.query(models.Organization).filter(
        models.Organization.id == org_id
    ).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org.is_active = False
    db.commit()


# ========== Financial Year Master Endpoints ==========
@financial_year_router.post("/", status_code=status.HTTP_201_CREATED)
def create_financial_year(
    fy_data: schemas.FinancialYearCreate,
    db: Session = Depends(get_db)
):
    """Create a new financial year."""
    # Check if year_code already exists for organization
    existing = db.query(models.FinancialYear).filter(
        models.FinancialYear.organization_id == fy_data.organization_id,
        models.FinancialYear.year_code == fy_data.year_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Financial year {fy_data.year_code} already exists for this organization"
        )
    
    db_fy = models.FinancialYear(**fy_data.model_dump())
    db.add(db_fy)
    db.commit()
    db.refresh(db_fy)
    return db_fy


@financial_year_router.get("/")
def list_financial_years(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_closed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all financial years."""
    query = db.query(models.FinancialYear)
    
    if organization_id:
        query = query.filter(models.FinancialYear.organization_id == organization_id)
    if is_active is not None:
        query = query.filter(models.FinancialYear.is_active == is_active)
    if is_closed is not None:
        query = query.filter(models.FinancialYear.is_closed == is_closed)
    
    return query.offset(skip).limit(limit).all()


@financial_year_router.get("/{fy_id}")
def get_financial_year(fy_id: int, db: Session = Depends(get_db)):
    """Get financial year by ID."""
    fy = db.query(models.FinancialYear).filter(
        models.FinancialYear.id == fy_id
    ).first()
    
    if not fy:
        raise HTTPException(status_code=404, detail="Financial year not found")
    
    return fy


@financial_year_router.put("/{fy_id}")
def update_financial_year(
    fy_id: int,
    fy_data: schemas.FinancialYearUpdate,
    db: Session = Depends(get_db)
):
    """Update financial year."""
    fy = db.query(models.FinancialYear).filter(
        models.FinancialYear.id == fy_id
    ).first()
    
    if not fy:
        raise HTTPException(status_code=404, detail="Financial year not found")
    
    for key, value in fy_data.model_dump(exclude_unset=True).items():
        setattr(fy, key, value)
    
    db.commit()
    db.refresh(fy)
    return fy


@financial_year_router.post("/{fy_id}/close", status_code=status.HTTP_200_OK)
def close_financial_year(fy_id: int, db: Session = Depends(get_db)):
    """Close a financial year (year-end process)."""
    fy = db.query(models.FinancialYear).filter(
        models.FinancialYear.id == fy_id
    ).first()
    
    if not fy:
        raise HTTPException(status_code=404, detail="Financial year not found")
    
    if fy.is_closed:
        raise HTTPException(status_code=400, detail="Financial year already closed")
    
    fy.is_closed = True
    fy.is_active = False
    db.commit()
    db.refresh(fy)
    
    return {"message": f"Financial year {fy.year_code} closed successfully", "financial_year": fy}


# ========== Commodity Master Endpoints ==========
@commodity_router.post("/", status_code=status.HTTP_201_CREATED)
def create_commodity(
    commodity_data: schemas.CommodityCreate,
    db: Session = Depends(get_db)
):
    """Create a new commodity."""
    # Check if commodity code already exists
    existing = db.query(models.Commodity).filter(
        models.Commodity.commodity_code == commodity_data.commodity_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Commodity with code '{commodity_data.commodity_code}' already exists"
        )
    
    db_commodity = models.Commodity(**commodity_data.model_dump())
    db.add(db_commodity)
    db.commit()
    db.refresh(db_commodity)
    return db_commodity


@commodity_router.get("/")
def list_commodities(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = True,
    commodity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all commodities."""
    query = db.query(models.Commodity)
    
    if is_active is not None:
        query = query.filter(models.Commodity.is_active == is_active)
    if commodity_type:
        query = query.filter(models.Commodity.commodity_type == commodity_type)
    
    return query.offset(skip).limit(limit).all()


@commodity_router.get("/{commodity_id}")
def get_commodity(commodity_id: int, db: Session = Depends(get_db)):
    """Get commodity by ID."""
    commodity = db.query(models.Commodity).filter(
        models.Commodity.id == commodity_id
    ).first()
    
    if not commodity:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    return commodity


@commodity_router.put("/{commodity_id}")
def update_commodity(
    commodity_id: int,
    commodity_data: schemas.CommodityUpdate,
    db: Session = Depends(get_db)
):
    """Update commodity."""
    commodity = db.query(models.Commodity).filter(
        models.Commodity.id == commodity_id
    ).first()
    
    if not commodity:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    # Check commodity code uniqueness if being updated
    if commodity_data.commodity_code and commodity_data.commodity_code != commodity.commodity_code:
        existing = db.query(models.Commodity).filter(
            models.Commodity.commodity_code == commodity_data.commodity_code,
            models.Commodity.id != commodity_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Commodity with code '{commodity_data.commodity_code}' already exists"
            )
    
    for key, value in commodity_data.model_dump(exclude_unset=True).items():
        setattr(commodity, key, value)
    
    db.commit()
    db.refresh(commodity)
    return commodity


@commodity_router.delete("/{commodity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_commodity(commodity_id: int, db: Session = Depends(get_db)):
    """Soft delete commodity."""
    commodity = db.query(models.Commodity).filter(
        models.Commodity.id == commodity_id
    ).first()
    
    if not commodity:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    commodity.is_active = False
    db.commit()


# ========== Location Master Endpoints ==========
@location_router.post("/", status_code=status.HTTP_201_CREATED)
def create_location(
    location_data: schemas.LocationCreate,
    db: Session = Depends(get_db)
):
    """Create a new location."""
    db_location = models.Location(**location_data.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


@location_router.get("/")
def list_locations(
    skip: int = 0,
    limit: int = 100,
    country: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all locations."""
    query = db.query(models.Location)
    
    if country:
        query = query.filter(models.Location.country == country)
    if state:
        query = query.filter(models.Location.state == state)
    
    return query.offset(skip).limit(limit).all()


@location_router.get("/{location_id}")
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get location by ID."""
    location = db.query(models.Location).filter(
        models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location


@location_router.put("/{location_id}")
def update_location(
    location_id: int,
    location_data: schemas.LocationUpdate,
    db: Session = Depends(get_db)
):
    """Update location."""
    location = db.query(models.Location).filter(
        models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    for key, value in location_data.model_dump(exclude_unset=True).items():
        setattr(location, key, value)
    
    db.commit()
    db.refresh(location)
    return location


@location_router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Delete location."""
    location = db.query(models.Location).filter(
        models.Location.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(location)
    db.commit()


# ========== GST Rate Master Endpoints ==========
@gst_rate_router.post("/", status_code=status.HTTP_201_CREATED)
def create_gst_rate(
    gst_data: schemas.GstRateCreate,
    db: Session = Depends(get_db)
):
    """Create a new GST rate."""
    db_gst = models.GstRate(**gst_data.model_dump())
    db.add(db_gst)
    db.commit()
    db.refresh(db_gst)
    return db_gst


@gst_rate_router.get("/")
def list_gst_rates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all GST rates."""
    return db.query(models.GstRate).offset(skip).limit(limit).all()


@gst_rate_router.get("/{gst_id}")
def get_gst_rate(gst_id: int, db: Session = Depends(get_db)):
    """Get GST rate by ID."""
    gst = db.query(models.GstRate).filter(models.GstRate.id == gst_id).first()
    
    if not gst:
        raise HTTPException(status_code=404, detail="GST rate not found")
    
    return gst


@gst_rate_router.put("/{gst_id}")
def update_gst_rate(
    gst_id: int,
    gst_data: schemas.GstRateUpdate,
    db: Session = Depends(get_db)
):
    """Update GST rate."""
    gst = db.query(models.GstRate).filter(models.GstRate.id == gst_id).first()
    
    if not gst:
        raise HTTPException(status_code=404, detail="GST rate not found")
    
    for key, value in gst_data.model_dump(exclude_unset=True).items():
        setattr(gst, key, value)
    
    db.commit()
    db.refresh(gst)
    return gst


@gst_rate_router.delete("/{gst_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gst_rate(gst_id: int, db: Session = Depends(get_db)):
    """Delete GST rate."""
    gst = db.query(models.GstRate).filter(models.GstRate.id == gst_id).first()
    
    if not gst:
        raise HTTPException(status_code=404, detail="GST rate not found")
    
    db.delete(gst)
    db.commit()


# ========== Commission Structure Master Endpoints ==========
@commission_structure_router.post("/", status_code=status.HTTP_201_CREATED)
def create_commission_structure(
    comm_data: schemas.CommissionStructureCreate,
    db: Session = Depends(get_db)
):
    """Create a new commission structure."""
    db_comm = models.CommissionStructure(**comm_data.model_dump())
    db.add(db_comm)
    db.commit()
    db.refresh(db_comm)
    return db_comm


@commission_structure_router.get("/")
def list_commission_structures(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all commission structures."""
    return db.query(models.CommissionStructure).offset(skip).limit(limit).all()


@commission_structure_router.get("/{comm_id}")
def get_commission_structure(comm_id: int, db: Session = Depends(get_db)):
    """Get commission structure by ID."""
    comm = db.query(models.CommissionStructure).filter(
        models.CommissionStructure.id == comm_id
    ).first()
    
    if not comm:
        raise HTTPException(status_code=404, detail="Commission structure not found")
    
    return comm


@commission_structure_router.put("/{comm_id}")
def update_commission_structure(
    comm_id: int,
    comm_data: schemas.CommissionStructureUpdate,
    db: Session = Depends(get_db)
):
    """Update commission structure."""
    comm = db.query(models.CommissionStructure).filter(
        models.CommissionStructure.id == comm_id
    ).first()
    
    if not comm:
        raise HTTPException(status_code=404, detail="Commission structure not found")
    
    for key, value in comm_data.model_dump(exclude_unset=True).items():
        setattr(comm, key, value)
    
    db.commit()
    db.refresh(comm)
    return comm


@commission_structure_router.delete("/{comm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_commission_structure(comm_id: int, db: Session = Depends(get_db)):
    """Delete commission structure."""
    comm = db.query(models.CommissionStructure).filter(
        models.CommissionStructure.id == comm_id
    ).first()
    
    if not comm:
        raise HTTPException(status_code=404, detail="Commission structure not found")
    
    db.delete(comm)
    db.commit()


# ========== Settings Master Endpoints ==========
@setting_router.post("/", status_code=status.HTTP_201_CREATED)
def create_setting(
    setting_data: schemas.SettingCreate,
    db: Session = Depends(get_db)
):
    """Create a new setting."""
    # Check if key already exists
    existing = db.query(models.Setting).filter(
        models.Setting.key == setting_data.key
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Setting with key '{setting_data.key}' already exists"
        )
    
    db_setting = models.Setting(**setting_data.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


@setting_router.get("/")
def list_settings(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all settings."""
    query = db.query(models.Setting)
    
    if category:
        query = query.filter(models.Setting.category == category)
    if is_public is not None:
        query = query.filter(models.Setting.is_public == is_public)
    
    return query.offset(skip).limit(limit).all()


@setting_router.get("/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    """Get setting by key."""
    setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return setting


@setting_router.put("/{key}")
def update_setting(
    key: str,
    setting_data: schemas.SettingUpdate,
    db: Session = Depends(get_db)
):
    """Update setting."""
    setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    if not setting.is_editable:
        raise HTTPException(status_code=400, detail="This setting is not editable")
    
    for field_key, value in setting_data.model_dump(exclude_unset=True).items():
        setattr(setting, field_key, value)
    
    db.commit()
    db.refresh(setting)
    return setting


# ========== Generic Master Data Endpoints ==========
@master_data_router.post("/", status_code=status.HTTP_201_CREATED)
def create_master_data(
    data: schemas.MasterDataCreate,
    db: Session = Depends(get_db)
):
    """Create a new master data item."""
    db_item = models.MasterDataItem(**data.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@master_data_router.get("/")
def list_master_data(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """List master data items."""
    query = db.query(models.MasterDataItem)
    
    if category:
        query = query.filter(models.MasterDataItem.category == category)
    if is_active is not None:
        query = query.filter(models.MasterDataItem.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


@master_data_router.get("/{item_id}")
def get_master_data(item_id: int, db: Session = Depends(get_db)):
    """Get master data item by ID."""
    item = db.query(models.MasterDataItem).filter(
        models.MasterDataItem.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    return item


@master_data_router.put("/{item_id}")
def update_master_data(
    item_id: int,
    data: schemas.MasterDataUpdate,
    db: Session = Depends(get_db)
):
    """Update master data item."""
    item = db.query(models.MasterDataItem).filter(
        models.MasterDataItem.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item


@master_data_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_master_data(item_id: int, db: Session = Depends(get_db)):
    """Soft delete master data item."""
    item = db.query(models.MasterDataItem).filter(
        models.MasterDataItem.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Master data item not found")
    
    item.is_active = False
    db.commit()
