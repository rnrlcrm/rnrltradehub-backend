"""
Pydantic schemas for API request/response validation.

These schemas match the frontend TypeScript interfaces.
"""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, Field
from enum import Enum
from validators import (
    validate_pan, validate_gstin, validate_mobile, validate_pincode, validate_ifsc,
    sanitize_pan, sanitize_gstin, sanitize_mobile, sanitize_pincode, sanitize_ifsc,
    ValidationError
)


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


class UserType(str, Enum):
    PRIMARY = "primary"
    SUB_USER = "sub_user"


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
    
    @field_validator('pan')
    @classmethod
    def validate_pan_format(cls, v):
        """Validate PAN format."""
        try:
            validate_pan(v)
            return sanitize_pan(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @field_validator('gstin')
    @classmethod
    def validate_gstin_format(cls, v):
        """Validate GSTIN format."""
        if v:
            try:
                validate_gstin(v)
                return sanitize_gstin(v)
            except ValidationError as e:
                raise ValueError(str(e))
        return v
    
    @field_validator('contact_phone')
    @classmethod
    def validate_mobile_format(cls, v):
        """Validate mobile number format."""
        try:
            validate_mobile(v)
            return sanitize_mobile(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @field_validator('pincode')
    @classmethod
    def validate_pincode_format(cls, v):
        """Validate pincode format."""
        try:
            validate_pincode(v)
            return sanitize_pincode(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @field_validator('bank_ifsc')
    @classmethod
    def validate_ifsc_format(cls, v):
        """Validate IFSC code format."""
        if v:
            try:
                validate_ifsc(v)
                return sanitize_ifsc(v)
            except ValidationError as e:
                raise ValueError(str(e))
        return v


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


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Optional[UserRole] = Field(None, validation_alias='role_name')
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# Enhanced User Schemas for Settings Module
class SettingsUserCreate(BaseModel):
    """Schema for creating a user through the settings module."""
    name: str
    email: EmailStr
    password: str
    role_id: Optional[int] = None
    user_type: Optional[UserType] = UserType.PRIMARY
    client_id: Optional[str] = None
    vendor_id: Optional[str] = None
    parent_user_id: Optional[int] = None
    max_sub_users: Optional[int] = 5


class SettingsUserUpdate(BaseModel):
    """Schema for updating a user through the settings module."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    user_type: Optional[UserType] = None
    client_id: Optional[str] = None
    vendor_id: Optional[str] = None
    max_sub_users: Optional[int] = None


class SettingsUserResponse(BaseModel):
    """Schema for user response from the settings module."""
    id: int
    name: str
    email: str
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    is_active: bool
    user_type: str
    client_id: Optional[str] = None
    vendor_id: Optional[str] = None
    parent_user_id: Optional[int] = None
    max_sub_users: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    database: Optional[str] = None


# Invoice Schemas
class InvoiceBase(BaseModel):
    invoice_no: str
    organization_id: int
    financial_year: str
    sales_contract_id: str
    date: datetime
    amount: float
    status: Optional[str] = 'Unpaid'


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceResponse(InvoiceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Payment Schemas
class PaymentBase(BaseModel):
    payment_id: str
    organization_id: int
    financial_year: str
    invoice_id: str
    date: datetime
    amount: float
    method: str


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Commission Schemas
class CommissionBase(BaseModel):
    commission_id: str
    organization_id: int
    financial_year: str
    sales_contract_id: str
    agent: str
    amount: float
    status: Optional[str] = 'Due'


class CommissionCreate(CommissionBase):
    pass


class CommissionResponse(CommissionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Data Retention Policy Schemas  
class RetentionPolicyBase(BaseModel):
    entity_type: str
    retention_days: int
    archive_after_days: Optional[int] = None
    delete_after_days: Optional[int] = None
    policy_type: str
    description: Optional[str] = None
    is_active: Optional[bool] = True


class RetentionPolicyCreate(RetentionPolicyBase):
    pass


class RetentionPolicyResponse(RetentionPolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Data Access Log Schemas
class DataAccessLogBase(BaseModel):
    user_id: int
    entity_type: str
    entity_id: str
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    purpose: Optional[str] = None
    metadata_json: Optional[dict] = None


class DataAccessLogCreate(DataAccessLogBase):
    pass


class DataAccessLogResponse(DataAccessLogBase):
    id: int
    accessed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Consent Record Schemas
class ConsentRecordBase(BaseModel):
    user_id: Optional[int] = None
    business_partner_id: Optional[str] = None
    consent_type: str
    consent_given: bool
    consent_date: datetime
    withdrawn_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    metadata_json: Optional[dict] = None


class ConsentRecordCreate(ConsentRecordBase):
    pass


class ConsentRecordResponse(ConsentRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Data Export Request Schemas
class DataExportRequestBase(BaseModel):
    user_id: Optional[int] = None
    business_partner_id: Optional[str] = None
    request_type: str
    status: Optional[str] = 'pending'


class DataExportRequestCreate(DataExportRequestBase):
    pass


class DataExportRequestResponse(DataExportRequestBase):
    id: str
    requested_at: datetime
    completed_at: Optional[datetime] = None
    export_file_path: Optional[str] = None
    metadata_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Security Event Schemas
class SecurityEventBase(BaseModel):
    event_type: str
    severity: str
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    description: str


class SecurityEventCreate(SecurityEventBase):
    pass


class SecurityEventResponse(SecurityEventBase):
    id: int
    event_time: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None
    metadata_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Authentication Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# Team Management Schemas
class SubUserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_id: Optional[int] = None


class SubUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class SubUserResponse(BaseModel):
    id: int
    name: str
    email: str
    role_id: Optional[int] = None
    is_active: bool
    user_type: str
    parent_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
