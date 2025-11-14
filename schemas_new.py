"""
Clean Pydantic Schemas - Matching Frontend Requirements Only

This file contains ONLY the schemas that the frontend actually uses.
All unused schemas have been removed for clarity.

Frontend Modules Supported:
1. Settings (Organizations, Locations, CCI Terms, Commodities)
2. Trade Desk (Trades, Offers, Tested Lots, Negotiations)
3. Business Partners
4. Financial Year
5. Auth & Users
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class BusinessType(str, Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    BOTH = "BOTH"
    AGENT = "AGENT"


class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    OFFERS_RECEIVED = "OFFERS_RECEIVED"
    NEGOTIATION = "NEGOTIATION"
    AGREED = "AGREED"
    CONTRACT_CREATED = "CONTRACT_CREATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class OfferStatus(str, Enum):
    PENDING = "PENDING"
    COUNTERED = "COUNTERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TestedLotStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    DEPLETED = "DEPLETED"


class NegotiationRole(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"


class UrgencyLevel(str, Enum):
    NORMAL = "normal"
    URGENT = "urgent"


# ============================================================================
# AUTH & USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role_id: Optional[int] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    role_id: int
    module: str
    action: str


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SETTINGS MODULE SCHEMAS
# ============================================================================

# Organization Schemas
class OrganizationBase(BaseModel):
    name: str
    code: str
    organization_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    tan: Optional[str] = None
    cin: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    organization_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    tan: Optional[str] = None
    cin: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Location Schemas
class LocationBase(BaseModel):
    country: str
    state: str
    region: Optional[str] = None
    city: str


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    country: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None


class LocationResponse(LocationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# CCI Term Schemas
class CciTermBase(BaseModel):
    name: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    version: int = 1
    is_active: bool = True
    candy_factor: float
    gst_rate: float
    emd_by_buyer_type: Dict[str, float]
    emd_payment_days: Optional[int] = None
    emd_interest_percent: Optional[float] = None
    emd_late_interest_percent: Optional[float] = None
    emd_block_do_if_not_full: bool = True
    carrying_charge_tier1_days: Optional[int] = None
    carrying_charge_tier1_percent: Optional[float] = None
    carrying_charge_tier2_days: Optional[int] = None
    carrying_charge_tier2_percent: Optional[float] = None
    free_lifting_period_days: Optional[int] = None
    late_lifting_tier1_days: Optional[int] = None
    late_lifting_tier1_percent: Optional[float] = None
    late_lifting_tier2_days: Optional[int] = None
    late_lifting_tier2_percent: Optional[float] = None
    late_lifting_tier3_percent: Optional[float] = None
    cash_discount_percentage: Optional[float] = None
    interest_lc_bg_percent: Optional[float] = None
    penal_interest_lc_bg_percent: Optional[float] = None
    additional_deposit_percent: Optional[float] = None
    deposit_interest_percent: Optional[float] = None
    lifting_period_days: Optional[int] = None
    contract_period_days: Optional[int] = None
    lockin_charge_min: Optional[float] = None
    lockin_charge_max: Optional[float] = None
    moisture_lower_limit: Optional[float] = None
    moisture_upper_limit: Optional[float] = None
    moisture_sample_count: Optional[int] = None
    email_reminder_days: Optional[int] = None
    email_template_emd_reminder: Optional[str] = None
    email_template_payment_due: Optional[str] = None


class CciTermCreate(CciTermBase):
    pass


class CciTermUpdate(BaseModel):
    name: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None
    # ... (all other fields optional for updates)


class CciTermResponse(CciTermBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Commodity Schemas
class CommodityBase(BaseModel):
    name: str
    symbol: str
    unit: str
    rate_unit: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = None
    gst_exemption_available: bool = False
    gst_category: Optional[str] = None
    is_processed: bool = False
    trade_types: Optional[List[Dict]] = None
    bargain_types: Optional[List[Dict]] = None
    varieties: Optional[List[Dict]] = None
    weightment_terms: Optional[List[Dict]] = None
    passing_terms: Optional[List[Dict]] = None
    delivery_terms: Optional[List[Dict]] = None
    payment_terms: Optional[List[Dict]] = None
    commissions: Optional[List[Dict]] = None
    quality_parameters: Optional[List[Dict]] = None
    certificates: Optional[List[str]] = None
    supports_cci_terms: bool = False
    description: Optional[str] = None
    is_active: bool = True


class CommodityCreate(CommodityBase):
    pass


class CommodityUpdate(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    unit: Optional[str] = None
    # ... (all fields optional)
    is_active: Optional[bool] = None


class CommodityResponse(CommodityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BUSINESS PARTNER SCHEMAS
# ============================================================================

class AddressBase(BaseModel):
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: str
    business_partner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BusinessPartnerBase(BaseModel):
    bp_code: str
    legal_name: str
    business_type: BusinessType
    status: str = "ACTIVE"
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    pan: Optional[str] = None
    gstin: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None


class BusinessPartnerCreate(BusinessPartnerBase):
    shipping_addresses: List[AddressCreate] = []


class BusinessPartnerUpdate(BaseModel):
    bp_code: Optional[str] = None
    legal_name: Optional[str] = None
    business_type: Optional[BusinessType] = None
    status: Optional[str] = None
    # ... (all fields optional)


class BusinessPartnerResponse(BusinessPartnerBase):
    id: str
    created_at: datetime
    updated_at: datetime
    addresses: List[AddressResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# FINANCIAL YEAR SCHEMAS
# ============================================================================

class FinancialYearBase(BaseModel):
    organization_id: int
    year_code: str
    start_date: datetime
    end_date: datetime
    assessment_year: str
    is_active: bool = False
    is_closed: bool = False
    opening_balances: Optional[Dict] = None


class FinancialYearCreate(FinancialYearBase):
    pass


class FinancialYearUpdate(BaseModel):
    year_code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    assessment_year: Optional[str] = None
    is_active: Optional[bool] = None
    is_closed: Optional[bool] = None
    opening_balances: Optional[Dict] = None


class FinancialYearResponse(FinancialYearBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TRADE DESK SCHEMAS
# ============================================================================

# Trade Schemas
class TradeBase(BaseModel):
    action: TradeAction
    buyer_id: str
    commodity_id: int
    quantity: float
    unit: str
    variety_id: Optional[int] = None
    parameters: Dict[str, Dict[str, float]]  # {"staple_mm": {"min": 28, "max": 30}}
    trade_type_id: Optional[int] = None
    bargain_type_id: Optional[int] = None
    passing_id: Optional[int] = None
    weightment_id: Optional[int] = None
    delivery_term_id: Optional[int] = None
    delivery_days: Optional[int] = None
    payment_term_id: Optional[int] = None
    payment_days: Optional[int] = None
    location_state_id: Optional[int] = None
    location_region_id: Optional[int] = None
    location_station_id: Optional[int] = None
    certificates: Optional[List[str]] = None
    target_price: Optional[float] = None
    currency: str = "INR"
    price_unit: Optional[str] = None
    notes: Optional[str] = None
    urgency: UrgencyLevel = UrgencyLevel.NORMAL


class TradeCreate(TradeBase):
    pass


class TradeUpdate(BaseModel):
    status: Optional[TradeStatus] = None
    expires_at: Optional[datetime] = None
    assigned_to_user_id: Optional[int] = None
    # ... other updatable fields


class TradeResponse(TradeBase):
    id: int
    status: TradeStatus
    expires_at: Optional[datetime]
    assigned_to_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Offer Schemas
class OfferBase(BaseModel):
    trade_id: int
    seller_id: str
    station_id: int
    price: float
    currency: str = "INR"
    price_unit: str
    quantity: float
    unit: str
    variety_id: Optional[int] = None
    parameters: Dict[str, float]  # {"staple_mm": 29.0, "mic": 4.1}
    test_report_url: Optional[str] = None
    test_report_date: Optional[datetime] = None
    tested_lot_id: Optional[int] = None
    delivery_term_id: Optional[int] = None
    payment_term_id: Optional[int] = None
    valid_until: datetime
    validity_hours: Optional[int] = None
    notes: Optional[str] = None


class OfferCreate(OfferBase):
    pass


class OfferUpdate(BaseModel):
    status: Optional[OfferStatus] = None
    match_score: Optional[float] = None
    match_breakdown: Optional[Dict] = None
    parameter_deviations: Optional[List] = None


class OfferResponse(OfferBase):
    id: int
    status: OfferStatus
    match_score: Optional[float]
    match_breakdown: Optional[Dict]
    parameter_deviations: Optional[List]
    negotiation_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Tested Lot Schemas
class TestedLotBase(BaseModel):
    seller_id: str
    commodity_id: int
    station_id: int
    quantity: float
    quantity_available: float
    unit: str
    variety_id: Optional[int] = None
    parameters: Dict[str, float]
    test_report_url: str
    test_report_date: datetime
    testing_lab: Optional[str] = None
    valid_until: datetime
    notes: Optional[str] = None


class TestedLotCreate(TestedLotBase):
    pass


class TestedLotUpdate(BaseModel):
    quantity_available: Optional[float] = None
    quantity_offered: Optional[float] = None
    status: Optional[TestedLotStatus] = None
    matched_trade_ids: Optional[List[int]] = None


class TestedLotResponse(TestedLotBase):
    id: int
    quantity_offered: float
    status: TestedLotStatus
    matched_trade_ids: Optional[List[int]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Negotiation Schemas
class NegotiationBase(BaseModel):
    offer_id: int
    version: int
    sender_id: int
    sender_role: NegotiationRole
    new_price: Optional[float] = None
    new_quantity: Optional[float] = None
    new_valid_until: Optional[datetime] = None
    message: str


class NegotiationCreate(NegotiationBase):
    pass


class NegotiationResponse(NegotiationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# HEALTH CHECK & UTILITY SCHEMAS
# ============================================================================

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str


# ============================================================================
# SETTINGS USER MANAGEMENT (from routes_complete.py)
# ============================================================================

class SettingsUserResponse(BaseModel):
    """User response for settings module."""
    id: int
    name: str
    email: str
    role_id: Optional[int]
    role_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
