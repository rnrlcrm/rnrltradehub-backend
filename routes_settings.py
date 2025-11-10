"""
Settings Module API Routes for RNRL TradeHub Backend.

This module provides RESTful API endpoints for the Settings module including:
- Organizations management
- Master data (trade types, bargain types, varieties, etc.)
- GST Rates
- Locations
- Commission structures
- CCI Terms
- Delivery Terms
- Payment Terms

All endpoints follow a standardized response format and require Admin role authorization.
"""
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
import models
import schemas

# Create router for settings module
settings_router = APIRouter(prefix="/api/settings", tags=["Settings Module"])


# ==================== Helper Functions ====================

def success_response(data: Any = None, message: str = None) -> Dict:
    """Standard success response format."""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


def error_response(message: str, code: str = "ERROR") -> Dict:
    """Standard error response format."""
    return {
        "success": False,
        "message": message,
        "error": {
            "code": code,
            "message": message
        }
    }


# ==================== Organizations Endpoints ====================

@settings_router.get("/organizations")
def list_organizations(db: Session = Depends(get_db)):
    """
    List all organizations.
    
    Returns:
        List of all organizations with full details
    """
    orgs = db.query(models.Organization).all()
    
    # Convert to response format
    data = []
    for org in orgs:
        org_dict = {
            "id": org.id,
            "name": org.display_name,
            "legalName": org.legal_name,
            "code": org.pan,  # Using PAN as code for now
            "gstin": org.gstin,
            "pan": org.pan,
            "isActive": org.is_active,
            "createdAt": org.created_at.isoformat() if org.created_at else None,
            "updatedAt": org.updated_at.isoformat() if org.updated_at else None,
        }
        
        # Parse address JSON if available
        if org.address:
            if isinstance(org.address, dict):
                org_dict.update({
                    "address": org.address.get("line1", ""),
                    "city": org.address.get("city", ""),
                    "state": org.address.get("state", ""),
                    "pincode": org.address.get("pincode", ""),
                })
        
        # Parse settings JSON for additional fields
        if org.settings and isinstance(org.settings, dict):
            org_dict.update({
                "phone": org.settings.get("phone", ""),
                "email": org.settings.get("email", ""),
                "website": org.settings.get("website", ""),
                "bankName": org.settings.get("bank_name", ""),
                "accountNumber": org.settings.get("account_number", ""),
                "ifscCode": org.settings.get("ifsc_code", ""),
                "branch": org.settings.get("branch", ""),
            })
        
        data.append(org_dict)
    
    return success_response(data=data)


@settings_router.post("/organizations", status_code=status.HTTP_201_CREATED)
def create_organization(org_data: dict, db: Session = Depends(get_db)):
    """
    Create a new organization.
    
    Request body should include:
    - name, code, gstin, pan, address, city, state, pincode
    - phone, email, website, bankName, accountNumber, ifscCode, branch
    - isActive
    """
    try:
        # Build address JSON
        address = {
            "line1": org_data.get("address", ""),
            "line2": org_data.get("address2", ""),
            "city": org_data.get("city", ""),
            "state": org_data.get("state", ""),
            "pincode": org_data.get("pincode", ""),
            "country": "India"
        }
        
        # Build settings JSON for additional fields
        settings = {
            "phone": org_data.get("phone", ""),
            "email": org_data.get("email", ""),
            "website": org_data.get("website", ""),
            "bank_name": org_data.get("bankName", ""),
            "account_number": org_data.get("accountNumber", ""),
            "ifsc_code": org_data.get("ifscCode", ""),
            "branch": org_data.get("branch", ""),
        }
        
        # Create organization
        db_org = models.Organization(
            legal_name=org_data.get("legalName", org_data.get("name")),
            display_name=org_data.get("name"),
            pan=org_data.get("pan"),
            gstin=org_data.get("gstin"),
            address=address,
            settings=settings,
            is_active=org_data.get("isActive", True),
            logo_url=org_data.get("logoUrl")
        )
        
        db.add(db_org)
        db.commit()
        db.refresh(db_org)
        
        # Return created organization
        return success_response(
            data={
                "id": db_org.id,
                "name": db_org.display_name,
                "legalName": db_org.legal_name,
                "code": db_org.pan,
                "gstin": db_org.gstin,
                "pan": db_org.pan,
                "isActive": db_org.is_active,
                "createdAt": db_org.created_at.isoformat(),
                "updatedAt": db_org.updated_at.isoformat(),
            },
            message="Organization created successfully"
        )
        
    except IntegrityError as e:
        db.rollback()
        if "gstin" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="Organization with this GSTIN already exists"
            )
        elif "pan" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail="Organization with this PAN already exists"
            )
        else:
            raise HTTPException(
                status_code=409,
                detail="Organization with this code or GSTIN already exists"
            )


@settings_router.put("/organizations/{org_id}")
def update_organization(org_id: int, org_data: dict, db: Session = Depends(get_db)):
    """Update an existing organization."""
    db_org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        # Update fields
        if "name" in org_data:
            db_org.display_name = org_data["name"]
        if "legalName" in org_data:
            db_org.legal_name = org_data["legalName"]
        if "pan" in org_data:
            db_org.pan = org_data["pan"]
        if "gstin" in org_data:
            db_org.gstin = org_data["gstin"]
        if "isActive" in org_data:
            db_org.is_active = org_data["isActive"]
        if "logoUrl" in org_data:
            db_org.logo_url = org_data["logoUrl"]
        
        # Update address
        if any(k in org_data for k in ["address", "city", "state", "pincode"]):
            address = db_org.address or {}
            if "address" in org_data:
                address["line1"] = org_data["address"]
            if "city" in org_data:
                address["city"] = org_data["city"]
            if "state" in org_data:
                address["state"] = org_data["state"]
            if "pincode" in org_data:
                address["pincode"] = org_data["pincode"]
            db_org.address = address
        
        # Update settings
        if any(k in org_data for k in ["phone", "email", "website", "bankName", "accountNumber", "ifscCode", "branch"]):
            settings = db_org.settings or {}
            if "phone" in org_data:
                settings["phone"] = org_data["phone"]
            if "email" in org_data:
                settings["email"] = org_data["email"]
            if "website" in org_data:
                settings["website"] = org_data["website"]
            if "bankName" in org_data:
                settings["bank_name"] = org_data["bankName"]
            if "accountNumber" in org_data:
                settings["account_number"] = org_data["accountNumber"]
            if "ifscCode" in org_data:
                settings["ifsc_code"] = org_data["ifscCode"]
            if "branch" in org_data:
                settings["branch"] = org_data["branch"]
            db_org.settings = settings
        
        db.commit()
        db.refresh(db_org)
        
        return success_response(
            data={
                "id": db_org.id,
                "name": db_org.display_name,
                "isActive": db_org.is_active,
            },
            message="Organization updated successfully"
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Organization with this code or GSTIN already exists"
        )


@settings_router.delete("/organizations/{org_id}")
def delete_organization(org_id: int, db: Session = Depends(get_db)):
    """Delete an organization."""
    db_org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    db.delete(db_org)
    db.commit()
    
    return success_response(message="Organization deleted successfully")


# ==================== Master Data Endpoints ====================

MASTER_DATA_TYPES = {
    "trade-types": "trade_type",
    "bargain-types": "bargain_type",
    "varieties": "variety",
    "dispute-reasons": "dispute_reason",
    "weightment-terms": "weightment_term",
    "passing-terms": "passing_term",
    "financial-years": "financial_year",
}


@settings_router.get("/master-data/{data_type}")
def list_master_data(data_type: str, db: Session = Depends(get_db)):
    """List master data items of specified type."""
    if data_type not in MASTER_DATA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid master data type. Must be one of: {', '.join(MASTER_DATA_TYPES.keys())}"
        )
    
    category = MASTER_DATA_TYPES[data_type]
    items = db.query(models.MasterDataItem).filter(
        models.MasterDataItem.category == category
    ).all()
    
    data = [
        {
            "id": item.id,
            "name": item.name,
            "createdAt": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]
    
    return success_response(data=data)


@settings_router.post("/master-data/{data_type}", status_code=status.HTTP_201_CREATED)
def create_master_data(data_type: str, item_data: dict, db: Session = Depends(get_db)):
    """Create a new master data item."""
    if data_type not in MASTER_DATA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid master data type. Must be one of: {', '.join(MASTER_DATA_TYPES.keys())}"
        )
    
    if not item_data.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    
    category = MASTER_DATA_TYPES[data_type]
    
    # Check for duplicate
    existing = db.query(models.MasterDataItem).filter(
        models.MasterDataItem.category == category,
        models.MasterDataItem.name.ilike(item_data["name"])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Item with name '{item_data['name']}' already exists"
        )
    
    db_item = models.MasterDataItem(
        category=category,
        name=item_data["name"],
        is_active=True
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return success_response(
        data={
            "id": db_item.id,
            "name": db_item.name,
            "createdAt": db_item.created_at.isoformat(),
        },
        message="Item created successfully"
    )


@settings_router.put("/master-data/{data_type}/{item_id}")
def update_master_data(data_type: str, item_id: int, item_data: dict, db: Session = Depends(get_db)):
    """Update a master data item."""
    if data_type not in MASTER_DATA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid master data type. Must be one of: {', '.join(MASTER_DATA_TYPES.keys())}"
        )
    
    category = MASTER_DATA_TYPES[data_type]
    
    db_item = db.query(models.MasterDataItem).filter(
        models.MasterDataItem.id == item_id,
        models.MasterDataItem.category == category
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if "name" in item_data:
        # Check for duplicate
        existing = db.query(models.MasterDataItem).filter(
            models.MasterDataItem.category == category,
            models.MasterDataItem.name.ilike(item_data["name"]),
            models.MasterDataItem.id != item_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Item with name '{item_data['name']}' already exists"
            )
        
        db_item.name = item_data["name"]
    
    db.commit()
    db.refresh(db_item)
    
    return success_response(
        data={
            "id": db_item.id,
            "name": db_item.name,
            "createdAt": db_item.created_at.isoformat(),
        },
        message="Item updated successfully"
    )


@settings_router.delete("/master-data/{data_type}/{item_id}")
def delete_master_data(data_type: str, item_id: int, db: Session = Depends(get_db)):
    """Delete a master data item."""
    if data_type not in MASTER_DATA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid master data type. Must be one of: {', '.join(MASTER_DATA_TYPES.keys())}"
        )
    
    category = MASTER_DATA_TYPES[data_type]
    
    db_item = db.query(models.MasterDataItem).filter(
        models.MasterDataItem.id == item_id,
        models.MasterDataItem.category == category
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    
    return success_response(message="Item deleted successfully")


# ==================== GST Rates Endpoints ====================

@settings_router.get("/gst-rates")
def list_gst_rates(db: Session = Depends(get_db)):
    """List all GST rates."""
    rates = db.query(models.GstRate).all()
    
    data = [
        {
            "id": rate.id,
            "description": rate.description,
            "hsnCode": rate.hsn_code,
            "rate": float(rate.rate),
            "createdAt": rate.created_at.isoformat() if rate.created_at else None,
        }
        for rate in rates
    ]
    
    return success_response(data=data)


@settings_router.post("/gst-rates", status_code=status.HTTP_201_CREATED)
def create_gst_rate(rate_data: dict, db: Session = Depends(get_db)):
    """Create a new GST rate."""
    if not rate_data.get("description"):
        raise HTTPException(status_code=400, detail="Description is required")
    if not rate_data.get("hsnCode"):
        raise HTTPException(status_code=400, detail="HSN Code is required")
    if "rate" not in rate_data:
        raise HTTPException(status_code=400, detail="Rate is required")
    
    db_rate = models.GstRate(
        description=rate_data["description"],
        hsn_code=rate_data["hsnCode"],
        rate=float(rate_data["rate"])
    )
    
    db.add(db_rate)
    db.commit()
    db.refresh(db_rate)
    
    return success_response(
        data={
            "id": db_rate.id,
            "description": db_rate.description,
            "hsnCode": db_rate.hsn_code,
            "rate": float(db_rate.rate),
            "createdAt": db_rate.created_at.isoformat(),
        },
        message="GST rate created successfully"
    )


@settings_router.put("/gst-rates/{rate_id}")
def update_gst_rate(rate_id: int, rate_data: dict, db: Session = Depends(get_db)):
    """Update a GST rate."""
    db_rate = db.query(models.GstRate).filter(models.GstRate.id == rate_id).first()
    
    if not db_rate:
        raise HTTPException(status_code=404, detail="GST rate not found")
    
    if "description" in rate_data:
        db_rate.description = rate_data["description"]
    if "hsnCode" in rate_data:
        db_rate.hsn_code = rate_data["hsnCode"]
    if "rate" in rate_data:
        db_rate.rate = float(rate_data["rate"])
    
    db.commit()
    db.refresh(db_rate)
    
    return success_response(
        data={
            "id": db_rate.id,
            "description": db_rate.description,
            "hsnCode": db_rate.hsn_code,
            "rate": float(db_rate.rate),
        },
        message="GST rate updated successfully"
    )


@settings_router.delete("/gst-rates/{rate_id}")
def delete_gst_rate(rate_id: int, db: Session = Depends(get_db)):
    """Delete a GST rate."""
    db_rate = db.query(models.GstRate).filter(models.GstRate.id == rate_id).first()
    
    if not db_rate:
        raise HTTPException(status_code=404, detail="GST rate not found")
    
    db.delete(db_rate)
    db.commit()
    
    return success_response(message="GST rate deleted successfully")


# ==================== Locations Endpoints ====================

@settings_router.get("/locations")
def list_locations(db: Session = Depends(get_db)):
    """List all locations."""
    locations = db.query(models.Location).all()
    
    data = [
        {
            "id": loc.id,
            "country": loc.country,
            "state": loc.state,
            "city": loc.city,
            "createdAt": loc.created_at.isoformat() if loc.created_at else None,
        }
        for loc in locations
    ]
    
    return success_response(data=data)


@settings_router.post("/locations", status_code=status.HTTP_201_CREATED)
def create_location(loc_data: dict, db: Session = Depends(get_db)):
    """Create a new location."""
    if not loc_data.get("country"):
        raise HTTPException(status_code=400, detail="Country is required")
    if not loc_data.get("state"):
        raise HTTPException(status_code=400, detail="State is required")
    if not loc_data.get("city"):
        raise HTTPException(status_code=400, detail="City is required")
    
    # Check for duplicate
    existing = db.query(models.Location).filter(
        models.Location.country == loc_data["country"],
        models.Location.state == loc_data["state"],
        models.Location.city == loc_data["city"]
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Location with this combination already exists"
        )
    
    db_loc = models.Location(
        country=loc_data["country"],
        state=loc_data["state"],
        city=loc_data["city"]
    )
    
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    
    return success_response(
        data={
            "id": db_loc.id,
            "country": db_loc.country,
            "state": db_loc.state,
            "city": db_loc.city,
            "createdAt": db_loc.created_at.isoformat(),
        },
        message="Location created successfully"
    )


@settings_router.delete("/locations/{loc_id}")
def delete_location(loc_id: int, db: Session = Depends(get_db)):
    """Delete a location."""
    db_loc = db.query(models.Location).filter(models.Location.id == loc_id).first()
    
    if not db_loc:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(db_loc)
    db.commit()
    
    return success_response(message="Location deleted successfully")


# ==================== Commissions Endpoints ====================

@settings_router.get("/commissions")
def list_commissions(db: Session = Depends(get_db)):
    """List all commission structures."""
    commissions = db.query(models.CommissionStructure).all()
    
    data = [
        {
            "id": comm.id,
            "name": comm.name,
            "type": comm.type,
            "value": float(comm.value),
            "createdAt": comm.created_at.isoformat() if comm.created_at else None,
        }
        for comm in commissions
    ]
    
    return success_response(data=data)


@settings_router.post("/commissions", status_code=status.HTTP_201_CREATED)
def create_commission(comm_data: dict, db: Session = Depends(get_db)):
    """Create a new commission structure."""
    if not comm_data.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    if not comm_data.get("type"):
        raise HTTPException(status_code=400, detail="Type is required")
    if "value" not in comm_data:
        raise HTTPException(status_code=400, detail="Value is required")
    
    # Validate type
    if comm_data["type"] not in ["PERCENTAGE", "PER_BALE"]:
        raise HTTPException(
            status_code=400,
            detail="Type must be PERCENTAGE or PER_BALE"
        )
    
    # Check for duplicate name
    existing = db.query(models.CommissionStructure).filter(
        models.CommissionStructure.name.ilike(comm_data["name"])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Commission with name '{comm_data['name']}' already exists"
        )
    
    db_comm = models.CommissionStructure(
        name=comm_data["name"],
        type=comm_data["type"],
        value=float(comm_data["value"])
    )
    
    db.add(db_comm)
    db.commit()
    db.refresh(db_comm)
    
    return success_response(
        data={
            "id": db_comm.id,
            "name": db_comm.name,
            "type": db_comm.type,
            "value": float(db_comm.value),
            "createdAt": db_comm.created_at.isoformat(),
        },
        message="Commission created successfully"
    )


@settings_router.put("/commissions/{comm_id}")
def update_commission(comm_id: int, comm_data: dict, db: Session = Depends(get_db)):
    """Update a commission structure."""
    db_comm = db.query(models.CommissionStructure).filter(
        models.CommissionStructure.id == comm_id
    ).first()
    
    if not db_comm:
        raise HTTPException(status_code=404, detail="Commission not found")
    
    if "name" in comm_data:
        # Check for duplicate
        existing = db.query(models.CommissionStructure).filter(
            models.CommissionStructure.name.ilike(comm_data["name"]),
            models.CommissionStructure.id != comm_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Commission with name '{comm_data['name']}' already exists"
            )
        
        db_comm.name = comm_data["name"]
    
    if "type" in comm_data:
        if comm_data["type"] not in ["PERCENTAGE", "PER_BALE"]:
            raise HTTPException(
                status_code=400,
                detail="Type must be PERCENTAGE or PER_BALE"
            )
        db_comm.type = comm_data["type"]
    
    if "value" in comm_data:
        db_comm.value = float(comm_data["value"])
    
    db.commit()
    db.refresh(db_comm)
    
    return success_response(
        data={
            "id": db_comm.id,
            "name": db_comm.name,
            "type": db_comm.type,
            "value": float(db_comm.value),
        },
        message="Commission updated successfully"
    )


@settings_router.delete("/commissions/{comm_id}")
def delete_commission(comm_id: int, db: Session = Depends(get_db)):
    """Delete a commission structure."""
    db_comm = db.query(models.CommissionStructure).filter(
        models.CommissionStructure.id == comm_id
    ).first()
    
    if not db_comm:
        raise HTTPException(status_code=404, detail="Commission not found")
    
    db.delete(db_comm)
    db.commit()
    
    return success_response(message="Commission deleted successfully")


# ==================== CCI Terms Endpoints ====================

@settings_router.get("/cci-terms")
def list_cci_terms(db: Session = Depends(get_db)):
    """List all CCI terms."""
    terms = db.query(models.CciTerm).all()
    
    data = [
        {
            "id": term.id,
            "name": term.name,
            "contractPeriodDays": term.contract_period_days,
            "emdPaymentDays": term.emd_payment_days,
            "cashDiscountPercentage": float(term.cash_discount_percentage),
            "carryingChargeTier1Days": term.carrying_charge_tier1_days,
            "carryingChargeTier1Percent": float(term.carrying_charge_tier1_percent),
            "carryingChargeTier2Days": term.carrying_charge_tier2_days,
            "carryingChargeTier2Percent": float(term.carrying_charge_tier2_percent),
            "additionalDepositPercent": float(term.additional_deposit_percent),
            "depositInterestPercent": float(term.deposit_interest_percent),
            "freeLiftingPeriodDays": term.free_lifting_period_days,
            "lateLiftingTier1Days": term.late_lifting_tier1_days,
            "lateLiftingTier1Percent": float(term.late_lifting_tier1_percent),
            "lateLiftingTier2Days": term.late_lifting_tier2_days,
            "lateLiftingTier2Percent": float(term.late_lifting_tier2_percent),
            "lateLiftingTier3Percent": float(term.late_lifting_tier3_percent),
            "createdAt": term.created_at.isoformat() if term.created_at else None,
        }
        for term in terms
    ]
    
    return success_response(data=data)


@settings_router.post("/cci-terms", status_code=status.HTTP_201_CREATED)
def create_cci_term(term_data: dict, db: Session = Depends(get_db)):
    """Create a new CCI term."""
    if not term_data.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    
    db_term = models.CciTerm(
        name=term_data["name"],
        contract_period_days=term_data.get("contractPeriodDays", 90),
        emd_payment_days=term_data.get("emdPaymentDays", 7),
        cash_discount_percentage=term_data.get("cashDiscountPercentage", 2.0),
        carrying_charge_tier1_days=term_data.get("carryingChargeTier1Days", 30),
        carrying_charge_tier1_percent=term_data.get("carryingChargeTier1Percent", 0.5),
        carrying_charge_tier2_days=term_data.get("carryingChargeTier2Days", 60),
        carrying_charge_tier2_percent=term_data.get("carryingChargeTier2Percent", 1.0),
        additional_deposit_percent=term_data.get("additionalDepositPercent", 10.0),
        deposit_interest_percent=term_data.get("depositInterestPercent", 6.0),
        free_lifting_period_days=term_data.get("freeLiftingPeriodDays", 15),
        late_lifting_tier1_days=term_data.get("lateLiftingTier1Days", 30),
        late_lifting_tier1_percent=term_data.get("lateLiftingTier1Percent", 0.25),
        late_lifting_tier2_days=term_data.get("lateLiftingTier2Days", 60),
        late_lifting_tier2_percent=term_data.get("lateLiftingTier2Percent", 0.5),
        late_lifting_tier3_percent=term_data.get("lateLiftingTier3Percent", 1.0),
    )
    
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    
    return success_response(
        data={"id": db_term.id, "name": db_term.name},
        message="CCI term created successfully"
    )


@settings_router.put("/cci-terms/{term_id}")
def update_cci_term(term_id: int, term_data: dict, db: Session = Depends(get_db)):
    """Update a CCI term."""
    db_term = db.query(models.CciTerm).filter(models.CciTerm.id == term_id).first()
    
    if not db_term:
        raise HTTPException(status_code=404, detail="CCI term not found")
    
    # Update fields if provided
    field_mapping = {
        "name": "name",
        "contractPeriodDays": "contract_period_days",
        "emdPaymentDays": "emd_payment_days",
        "cashDiscountPercentage": "cash_discount_percentage",
        "carryingChargeTier1Days": "carrying_charge_tier1_days",
        "carryingChargeTier1Percent": "carrying_charge_tier1_percent",
        "carryingChargeTier2Days": "carrying_charge_tier2_days",
        "carryingChargeTier2Percent": "carrying_charge_tier2_percent",
        "additionalDepositPercent": "additional_deposit_percent",
        "depositInterestPercent": "deposit_interest_percent",
        "freeLiftingPeriodDays": "free_lifting_period_days",
        "lateLiftingTier1Days": "late_lifting_tier1_days",
        "lateLiftingTier1Percent": "late_lifting_tier1_percent",
        "lateLiftingTier2Days": "late_lifting_tier2_days",
        "lateLiftingTier2Percent": "late_lifting_tier2_percent",
        "lateLiftingTier3Percent": "late_lifting_tier3_percent",
    }
    
    for frontend_field, db_field in field_mapping.items():
        if frontend_field in term_data:
            setattr(db_term, db_field, term_data[frontend_field])
    
    db.commit()
    db.refresh(db_term)
    
    return success_response(
        data={"id": db_term.id, "name": db_term.name},
        message="CCI term updated successfully"
    )


@settings_router.delete("/cci-terms/{term_id}")
def delete_cci_term(term_id: int, db: Session = Depends(get_db)):
    """Delete a CCI term."""
    db_term = db.query(models.CciTerm).filter(models.CciTerm.id == term_id).first()
    
    if not db_term:
        raise HTTPException(status_code=404, detail="CCI term not found")
    
    db.delete(db_term)
    db.commit()
    
    return success_response(message="CCI term deleted successfully")


# ==================== Delivery Terms Endpoints ====================

@settings_router.get("/delivery-terms")
def list_delivery_terms(db: Session = Depends(get_db)):
    """List all delivery terms."""
    terms = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.category == "delivery"
    ).all()
    
    data = [
        {
            "id": term.id,
            "name": term.name,
            "days": term.days,
            "createdAt": term.created_at.isoformat() if term.created_at else None,
        }
        for term in terms
    ]
    
    return success_response(data=data)


@settings_router.post("/delivery-terms", status_code=status.HTTP_201_CREATED)
def create_delivery_term(term_data: dict, db: Session = Depends(get_db)):
    """Create a new delivery term."""
    if not term_data.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    if "days" not in term_data:
        raise HTTPException(status_code=400, detail="Days is required")
    
    # Check for duplicate
    existing = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.category == "delivery",
        models.StructuredTerm.name.ilike(term_data["name"])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Delivery term with name '{term_data['name']}' already exists"
        )
    
    db_term = models.StructuredTerm(
        category="delivery",
        name=term_data["name"],
        days=int(term_data["days"]),
        description=term_data.get("description", ""),
        is_active=True
    )
    
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    
    return success_response(
        data={
            "id": db_term.id,
            "name": db_term.name,
            "days": db_term.days,
            "createdAt": db_term.created_at.isoformat(),
        },
        message="Delivery term created successfully"
    )


@settings_router.put("/delivery-terms/{term_id}")
def update_delivery_term(term_id: int, term_data: dict, db: Session = Depends(get_db)):
    """Update a delivery term."""
    db_term = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.id == term_id,
        models.StructuredTerm.category == "delivery"
    ).first()
    
    if not db_term:
        raise HTTPException(status_code=404, detail="Delivery term not found")
    
    if "name" in term_data:
        # Check for duplicate
        existing = db.query(models.StructuredTerm).filter(
            models.StructuredTerm.category == "delivery",
            models.StructuredTerm.name.ilike(term_data["name"]),
            models.StructuredTerm.id != term_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Delivery term with name '{term_data['name']}' already exists"
            )
        
        db_term.name = term_data["name"]
    
    if "days" in term_data:
        db_term.days = int(term_data["days"])
    
    if "description" in term_data:
        db_term.description = term_data["description"]
    
    db.commit()
    db.refresh(db_term)
    
    return success_response(
        data={
            "id": db_term.id,
            "name": db_term.name,
            "days": db_term.days,
        },
        message="Delivery term updated successfully"
    )


@settings_router.delete("/delivery-terms/{term_id}")
def delete_delivery_term(term_id: int, db: Session = Depends(get_db)):
    """Delete a delivery term."""
    db_term = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.id == term_id,
        models.StructuredTerm.category == "delivery"
    ).first()
    
    if not db_term:
        raise HTTPException(status_code=404, detail="Delivery term not found")
    
    db.delete(db_term)
    db.commit()
    
    return success_response(message="Delivery term deleted successfully")


# ==================== Payment Terms Endpoints ====================

@settings_router.get("/payment-terms")
def list_payment_terms(db: Session = Depends(get_db)):
    """List all payment terms."""
    terms = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.category == "payment"
    ).all()
    
    data = [
        {
            "id": term.id,
            "name": term.name,
            "days": term.days,
            "createdAt": term.created_at.isoformat() if term.created_at else None,
        }
        for term in terms
    ]
    
    return success_response(data=data)


@settings_router.post("/payment-terms", status_code=status.HTTP_201_CREATED)
def create_payment_term(term_data: dict, db: Session = Depends(get_db)):
    """Create a new payment term."""
    if not term_data.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    if "days" not in term_data:
        raise HTTPException(status_code=400, detail="Days is required")
    
    # Check for duplicate
    existing = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.category == "payment",
        models.StructuredTerm.name.ilike(term_data["name"])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Payment term with name '{term_data['name']}' already exists"
        )
    
    db_term = models.StructuredTerm(
        category="payment",
        name=term_data["name"],
        days=int(term_data["days"]),
        description=term_data.get("description", ""),
        is_active=True
    )
    
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    
    return success_response(
        data={
            "id": db_term.id,
            "name": db_term.name,
            "days": db_term.days,
            "createdAt": db_term.created_at.isoformat(),
        },
        message="Payment term created successfully"
    )


@settings_router.put("/payment-terms/{term_id}")
def update_payment_term(term_id: int, term_data: dict, db: Session = Depends(get_db)):
    """Update a payment term."""
    db_term = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.id == term_id,
        models.StructuredTerm.category == "payment"
    ).first()
    
    if not db_term:
        raise HTTPException(status_code=404, detail="Payment term not found")
    
    if "name" in term_data:
        # Check for duplicate
        existing = db.query(models.StructuredTerm).filter(
            models.StructuredTerm.category == "payment",
            models.StructuredTerm.name.ilike(term_data["name"]),
            models.StructuredTerm.id != term_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Payment term with name '{term_data['name']}' already exists"
            )
        
        db_term.name = term_data["name"]
    
    if "days" in term_data:
        db_term.days = int(term_data["days"])
    
    if "description" in term_data:
        db_term.description = term_data["description"]
    
    db.commit()
    db.refresh(db_term)
    
    return success_response(
        data={
            "id": db_term.id,
            "name": db_term.name,
            "days": db_term.days,
        },
        message="Payment term updated successfully"
    )


@settings_router.delete("/payment-terms/{term_id}")
def delete_payment_term(term_id: int, db: Session = Depends(get_db)):
    """Delete a payment term."""
    db_term = db.query(models.StructuredTerm).filter(
        models.StructuredTerm.id == term_id,
        models.StructuredTerm.category == "payment"
    ).first()
    
    if not db_term:
        raise HTTPException(status_code=404, detail="Payment term not found")
    
    db.delete(db_term)
    db.commit()
    
    return success_response(message="Payment term deleted successfully")
