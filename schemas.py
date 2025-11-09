"""
Pydantic schemas for API request/response validation.

These schemas match the frontend TypeScript interfaces.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr
from enum import Enum


# Enums
class BusinessType(str, Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    BOTH = "BOTH"
    AGENT = "AGENT"


class BusinessPartnerStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_COMPLIANCE = "PENDING_COMPLIANCE"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLACKLISTED = "BLACKLISTED"


class ContractStatus(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    DISPUTED = "Disputed"
    CARRIED_FORWARD = "Carried Forward"
    AMENDED = "Amended"
    PENDING_APPROVAL = "Pending Approval"
    REJECTED = "Rejected"


class UserRole(str, Enum):
    ADMIN = "Admin"
    SALES = "Sales"
    ACCOUNTS = "Accounts"
    DISPUTE_MANAGER = "Dispute Manager"
    VENDOR_CLIENT = "Vendor/Client"


# Base Schemas
class AddressBase(BaseModel):
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: str

    class Config:
        from_attributes = True


class BusinessPartnerBase(BaseModel):
    bp_code: str
    legal_name: str
    organization: str
    business_type: BusinessType
    status: BusinessPartnerStatus = BusinessPartnerStatus.DRAFT
    kyc_due_date: Optional[datetime] = None
    contact_person: str
    contact_email: EmailStr
    contact_phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str
    pan: str
    gstin: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    pan_doc_url: Optional[str] = None
    gst_doc_url: Optional[str] = None
    cheque_doc_url: Optional[str] = None
    compliance_notes: Optional[str] = None


class BusinessPartnerCreate(BusinessPartnerBase):
    shipping_addresses: Optional[List[AddressCreate]] = []


class BusinessPartnerResponse(BusinessPartnerBase):
    id: str
    shipping_addresses: List[AddressResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CciTermBase(BaseModel):
    name: str
    contract_period_days: int
    emd_payment_days: int
    cash_discount_percentage: float
    carrying_charge_tier1_days: int
    carrying_charge_tier1_percent: float
    carrying_charge_tier2_days: int
    carrying_charge_tier2_percent: float
    additional_deposit_percent: float
    deposit_interest_percent: float
    free_lifting_period_days: int
    late_lifting_tier1_days: int
    late_lifting_tier1_percent: float
    late_lifting_tier2_days: int
    late_lifting_tier2_percent: float
    late_lifting_tier3_percent: float


class CciTermCreate(CciTermBase):
    pass


class CciTermResponse(CciTermBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesContractBase(BaseModel):
    sc_no: str
    version: int = 1
    amendment_reason: Optional[str] = None
    date: datetime
    organization: str
    financial_year: str
    client_id: str
    client_name: str
    vendor_id: str
    vendor_name: str
    agent_id: Optional[str] = None
    variety: str
    quantity_bales: int
    rate: float
    gst_rate_id: Optional[int] = None
    buyer_commission_id: Optional[int] = None
    seller_commission_id: Optional[int] = None
    buyer_commission_gst_id: Optional[int] = None
    seller_commission_gst_id: Optional[int] = None
    trade_type: str
    bargain_type: str
    weightment_terms: str
    passing_terms: str
    delivery_terms: str
    payment_terms: str
    location: str
    quality_specs: Dict[str, str]
    manual_terms: Optional[str] = None
    status: ContractStatus = ContractStatus.ACTIVE
    cci_contract_no: Optional[str] = None
    cci_term_id: Optional[int] = None


class SalesContractCreate(SalesContractBase):
    pass


class SalesContractResponse(SalesContractBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    database: Optional[str] = None
