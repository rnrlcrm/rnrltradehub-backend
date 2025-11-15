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


# ========== NEW SCHEMAS FOR ENHANCED ACCESS CONTROL (PHASE 2) ==========

# Business Branch Schemas
class BusinessBranchBase(BaseModel):
    branch_code: str
    branch_name: str
    state: str
    gst_number: str
    address: dict
    contact_person: Optional[dict] = None
    bank_details: Optional[dict] = None
    is_head_office: bool = False
    is_active: bool = True


class BusinessBranchCreate(BusinessBranchBase):
    partner_id: str


class BusinessBranchUpdate(BaseModel):
    branch_name: Optional[str] = None
    state: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[dict] = None
    contact_person: Optional[dict] = None
    bank_details: Optional[dict] = None
    is_head_office: Optional[bool] = None
    is_active: Optional[bool] = None


class BusinessBranchResponse(BusinessBranchBase):
    id: str
    partner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Amendment Request Schemas
class AmendmentRequestBase(BaseModel):
    entity_type: str
    entity_id: str
    request_type: str
    reason: str
    justification: Optional[str] = None
    changes: dict


class AmendmentRequestCreate(AmendmentRequestBase):
    pass


class AmendmentRequestReview(BaseModel):
    status: str  # APPROVED or REJECTED
    review_notes: Optional[str] = None


class AmendmentRequestResponse(AmendmentRequestBase):
    id: str
    requested_by: int
    requested_at: datetime
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    impact_assessment: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Onboarding Application Schemas
class OnboardingApplicationBase(BaseModel):
    company_info: dict
    contact_info: dict
    compliance_info: dict
    branch_info: Optional[dict] = None
    documents: Optional[dict] = None


class OnboardingApplicationCreate(OnboardingApplicationBase):
    pass


class OnboardingApplicationReview(BaseModel):
    status: str  # APPROVED or REJECTED
    review_notes: Optional[str] = None


class OnboardingApplicationResponse(OnboardingApplicationBase):
    id: str
    application_number: str
    status: str
    review_notes: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Profile Update Request Schemas
class ProfileUpdateRequestBase(BaseModel):
    update_type: str
    old_values: dict
    new_values: dict
    reason: Optional[str] = None


class ProfileUpdateRequestCreate(ProfileUpdateRequestBase):
    partner_id: Optional[str] = None


class ProfileUpdateRequestReview(BaseModel):
    status: str  # APPROVED or REJECTED
    review_notes: Optional[str] = None


class ProfileUpdateRequestResponse(ProfileUpdateRequestBase):
    id: str
    user_id: int
    partner_id: Optional[str] = None
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# KYC Verification Schemas
class KYCVerificationBase(BaseModel):
    partner_id: str
    verification_date: datetime
    documents_checked: dict
    status: str
    next_due_date: datetime
    notes: Optional[str] = None


class KYCVerificationCreate(KYCVerificationBase):
    pass


class KYCVerificationResponse(KYCVerificationBase):
    id: str
    verified_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Custom Module Schemas
class CustomModuleBase(BaseModel):
    module_key: str
    display_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True


class CustomModuleCreate(CustomModuleBase):
    pass


class CustomModuleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class CustomModuleResponse(CustomModuleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Custom Permission Schemas
class CustomPermissionBase(BaseModel):
    module_id: str
    permission_key: str
    action: str
    description: Optional[str] = None
    is_active: bool = True


class CustomPermissionCreate(CustomPermissionBase):
    pass


class CustomPermissionResponse(CustomPermissionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Role Permission Schemas
class RolePermissionBase(BaseModel):
    role_id: int
    permission_id: str
    granted: bool = True


class RolePermissionCreate(RolePermissionBase):
    pass


class RolePermissionResponse(RolePermissionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Permission Override Schemas
class UserPermissionOverrideBase(BaseModel):
    user_id: int
    permission_id: str
    granted: bool
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserPermissionOverrideCreate(UserPermissionOverrideBase):
    pass


class UserPermissionOverrideResponse(UserPermissionOverrideBase):
    id: str
    granted_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Suspicious Activity Schemas
class SuspiciousActivityBase(BaseModel):
    user_id: int
    activity_type: str
    details: dict
    risk_score: int


class SuspiciousActivityCreate(SuspiciousActivityBase):
    pass


class SuspiciousActivityReview(BaseModel):
    reviewed: bool = True
    action_taken: Optional[str] = None


class SuspiciousActivityResponse(SuspiciousActivityBase):
    id: str
    detected_at: datetime
    reviewed: bool
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    action_taken: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Sub-User Schemas
class SubUserCreate(BaseModel):
    sub_user_id: int


class SubUserResponse(BaseModel):
    id: str
    parent_user_id: int
    sub_user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TRADE DESK & CHATBOT SCHEMAS
# ============================================================================

class ChatSessionBase(BaseModel):
    session_type: str
    context_data: Optional[dict] = None


class ChatSessionCreate(ChatSessionBase):
    user_id: int
    organization_id: int


class ChatSessionResponse(ChatSessionBase):
    id: str
    user_id: int
    organization_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    message_type: str
    content: str
    metadata_json: Optional[dict] = None


class ChatMessageCreate(ChatMessageBase):
    session_id: str


class ChatMessageResponse(ChatMessageBase):
    id: str
    session_id: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeBase(BaseModel):
    trade_date: datetime
    commodity_id: int
    client_id: str
    vendor_id: str
    agent_id: Optional[str] = None
    quantity_bales: int
    quantity_kg: Optional[float] = None
    rate_per_unit: float
    unit: str
    location: str
    delivery_terms: str
    payment_terms: str
    quality_terms: Optional[dict] = None


class TradeCreate(TradeBase):
    organization_id: int
    financial_year: str
    source: str
    session_id: Optional[str] = None
    created_by: int


class TradeUpdate(BaseModel):
    trade_date: Optional[datetime] = None
    quantity_bales: Optional[int] = None
    quantity_kg: Optional[float] = None
    rate_per_unit: Optional[float] = None
    location: Optional[str] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    quality_terms: Optional[dict] = None
    amendment_reason: Optional[str] = None


class TradeResponse(TradeBase):
    id: str
    trade_number: str
    organization_id: int
    financial_year: str
    source: str
    session_id: Optional[str] = None
    created_by: int
    status: str
    contract_id: Optional[str] = None
    converted_at: Optional[datetime] = None
    version: int
    amendment_reason: Optional[str] = None
    cancelled_reason: Optional[str] = None
    cancelled_by: Optional[int] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# QUALITY INSPECTION SCHEMAS
# ============================================================================

class QualityInspectionBase(BaseModel):
    inspection_date: datetime
    inspection_location: str
    parameters: dict
    remarks: Optional[str] = None


class QualityInspectionCreate(QualityInspectionBase):
    organization_id: int
    financial_year: str
    contract_id: str
    lot_number: Optional[str] = None
    inspector_id: int


class QualityInspectionUpdate(BaseModel):
    inspection_date: Optional[datetime] = None
    inspection_location: Optional[str] = None
    parameters: Optional[dict] = None
    status: Optional[str] = None
    result: Optional[str] = None
    remarks: Optional[str] = None
    rejection_reason: Optional[str] = None


class QualityInspectionApproval(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class QualityInspectionResponse(QualityInspectionBase):
    id: str
    inspection_number: str
    organization_id: int
    financial_year: str
    contract_id: str
    lot_number: Optional[str] = None
    inspector_id: int
    status: str
    result: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    report_document_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InspectionEventCreate(BaseModel):
    inspection_id: str
    event_type: str
    performed_by: int
    event_data: Optional[dict] = None
    notes: Optional[str] = None


class InspectionEventResponse(BaseModel):
    id: str
    inspection_id: str
    event_type: str
    performed_by: int
    event_data: Optional[dict] = None
    notes: Optional[str] = None
    event_timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryBase(BaseModel):
    commodity_id: int
    lot_number: str
    warehouse_location: str
    storage_zone: Optional[str] = None
    quantity_bales: int
    quantity_kg: float
    unit_weight_kg: Optional[float] = None
    quality_grade: Optional[str] = None


class InventoryCreate(InventoryBase):
    organization_id: int
    financial_year: str
    contract_id: Optional[str] = None
    inspection_id: Optional[str] = None


class InventoryUpdate(BaseModel):
    warehouse_location: Optional[str] = None
    storage_zone: Optional[str] = None
    quantity_bales: Optional[int] = None
    quantity_kg: Optional[float] = None
    status: Optional[str] = None
    quality_grade: Optional[str] = None
    metadata_json: Optional[dict] = None


class InventoryResponse(InventoryBase):
    id: str
    organization_id: int
    financial_year: str
    contract_id: Optional[str] = None
    status: str
    inspection_id: Optional[str] = None
    received_date: Optional[datetime] = None
    dispatch_date: Optional[datetime] = None
    last_movement_date: Optional[datetime] = None
    metadata_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# LOGISTICS & DELIVERY SCHEMAS
# ============================================================================

class TransporterBase(BaseModel):
    name: str
    contact_person: str
    contact_phone: str
    contact_email: Optional[str] = None
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None


class TransporterCreate(TransporterBase):
    organization_id: int


class TransporterUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None


class TransporterResponse(TransporterBase):
    id: str
    transporter_code: str
    organization_id: int
    status: str
    rating: Optional[float] = None
    notes: Optional[str] = None
    metadata_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryOrderBase(BaseModel):
    delivery_date: datetime
    quantity_bales: int
    quantity_kg: float
    pickup_location: str
    delivery_location: str
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None


class DeliveryOrderCreate(DeliveryOrderBase):
    organization_id: int
    financial_year: str
    contract_id: str
    invoice_id: Optional[str] = None
    transporter_id: Optional[str] = None


class DeliveryOrderUpdate(BaseModel):
    delivery_date: Optional[datetime] = None
    planned_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    transporter_id: Optional[str] = None
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    status: Optional[str] = None
    lr_number: Optional[str] = None
    eway_bill_number: Optional[str] = None
    remarks: Optional[str] = None
    cancellation_reason: Optional[str] = None


class DeliveryOrderResponse(DeliveryOrderBase):
    id: str
    do_number: str
    organization_id: int
    financial_year: str
    contract_id: str
    invoice_id: Optional[str] = None
    planned_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    transporter_id: Optional[str] = None
    status: str
    lr_number: Optional[str] = None
    eway_bill_number: Optional[str] = None
    remarks: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryEventCreate(BaseModel):
    delivery_order_id: str
    event_type: str
    performed_by: int
    event_data: Optional[dict] = None
    notes: Optional[str] = None
    location: Optional[str] = None


class DeliveryEventResponse(BaseModel):
    id: str
    delivery_order_id: str
    event_type: str
    performed_by: int
    event_data: Optional[dict] = None
    notes: Optional[str] = None
    event_timestamp: datetime
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ACCOUNTING & LEDGER SCHEMAS
# ============================================================================

class ChartOfAccountsBase(BaseModel):
    account_name: str
    account_type: str
    account_subtype: Optional[str] = None
    description: Optional[str] = None


class ChartOfAccountsCreate(ChartOfAccountsBase):
    organization_id: int
    parent_account_id: Optional[str] = None


class ChartOfAccountsResponse(ChartOfAccountsBase):
    id: str
    account_code: str
    organization_id: int
    parent_account_id: Optional[str] = None
    level: int
    is_active: bool
    is_system_account: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LedgerEntryBase(BaseModel):
    transaction_date: datetime
    transaction_type: str
    source_type: str
    source_id: str
    account_id: str
    entry_type: str
    amount: float
    narration: str
    party_type: Optional[str] = None
    party_id: Optional[str] = None


class LedgerEntryCreate(LedgerEntryBase):
    organization_id: int
    financial_year: str
    voucher_id: Optional[str] = None


class LedgerEntryResponse(LedgerEntryBase):
    id: str
    entry_number: str
    organization_id: int
    financial_year: str
    voucher_id: Optional[str] = None
    status: str
    posted_by: Optional[int] = None
    posted_at: Optional[datetime] = None
    reversed_by: Optional[int] = None
    reversed_at: Optional[datetime] = None
    reversal_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VoucherBase(BaseModel):
    voucher_type: str
    voucher_date: datetime
    narration: str
    reference_number: Optional[str] = None
    reference_date: Optional[datetime] = None


class VoucherCreate(VoucherBase):
    organization_id: int
    financial_year: str
    created_by: int


class VoucherUpdate(BaseModel):
    narration: Optional[str] = None
    reference_number: Optional[str] = None
    reference_date: Optional[datetime] = None


class VoucherPost(BaseModel):
    debit_total: float
    credit_total: float


class VoucherResponse(VoucherBase):
    id: str
    voucher_number: str
    organization_id: int
    financial_year: str
    status: str
    debit_total: float
    credit_total: float
    created_by: int
    posted_by: Optional[int] = None
    posted_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReconciliationCreate(BaseModel):
    organization_id: int
    financial_year: str
    reconciliation_date: datetime
    account_id: str
    book_balance: float
    bank_balance: float
    difference: float
    reconciled_items: Optional[dict] = None
    unmatched_items: Optional[dict] = None
    notes: Optional[str] = None
    performed_by: int


class ReconciliationResponse(BaseModel):
    id: str
    organization_id: int
    financial_year: str
    reconciliation_date: datetime
    account_id: str
    book_balance: float
    bank_balance: float
    difference: float
    status: str
    reconciled_items: Optional[dict] = None
    unmatched_items: Optional[dict] = None
    notes: Optional[str] = None
    performed_by: int
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ENHANCED DISPUTE SCHEMAS
# ============================================================================

class DisputeCommentBase(BaseModel):
    comment_text: str
    comment_type: str = 'COMMENT'
    attachments: Optional[dict] = None
    is_internal: bool = False


class DisputeCommentCreate(DisputeCommentBase):
    dispute_id: str
    user_id: int
    parent_comment_id: Optional[str] = None


class DisputeCommentResponse(DisputeCommentBase):
    id: str
    dispute_id: str
    user_id: int
    parent_comment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DisputeEvidenceCreate(BaseModel):
    dispute_id: str
    document_id: str
    evidence_type: str
    uploaded_by: int
    description: Optional[str] = None


class DisputeEvidenceResponse(BaseModel):
    id: str
    dispute_id: str
    document_id: str
    evidence_type: str
    uploaded_by: int
    description: Optional[str] = None
    is_verified: bool
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# REPORTING & NOTIFICATION SCHEMAS
# ============================================================================

class ReportDefinitionBase(BaseModel):
    report_name: str
    category: str
    description: Optional[str] = None
    query_template: Optional[str] = None
    parameters_schema: Optional[dict] = None
    supported_formats: Optional[dict] = None


class ReportDefinitionCreate(ReportDefinitionBase):
    required_permission: Optional[str] = None
    is_public: bool = False


class ReportDefinitionResponse(ReportDefinitionBase):
    id: str
    report_code: str
    required_permission: Optional[str] = None
    is_public: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportExecutionCreate(BaseModel):
    report_definition_id: str
    organization_id: int
    requested_by: int
    parameters: Optional[dict] = None
    output_format: str = 'PDF'


class ReportExecutionResponse(BaseModel):
    id: str
    report_definition_id: str
    organization_id: int
    requested_by: int
    requested_at: datetime
    parameters: Optional[dict] = None
    status: str
    output_format: Optional[str] = None
    file_size: Optional[int] = None
    storage_path: Optional[str] = None
    download_url: Optional[str] = None
    url_expires_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationQueueCreate(BaseModel):
    organization_id: int
    notification_type: str
    recipient_type: str
    recipient_id: str
    subject: Optional[str] = None
    message: str
    template_id: Optional[int] = None
    template_data: Optional[dict] = None
    priority: str = 'NORMAL'
    scheduled_for: Optional[datetime] = None
    created_by_user: Optional[int] = None
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str] = None


class NotificationQueueResponse(BaseModel):
    id: str
    organization_id: int
    notification_type: str
    recipient_type: str
    recipient_id: str
    subject: Optional[str] = None
    message: str
    template_id: Optional[int] = None
    template_data: Optional[dict] = None
    priority: str
    scheduled_for: Optional[datetime] = None
    status: str
    sent_at: Optional[datetime] = None
    delivery_status: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    created_by_user: Optional[int] = None
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BackupLogCreate(BaseModel):
    organization_id: Optional[int] = None
    backup_type: str
    entities_included: Optional[dict] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    storage_location: str
    triggered_by: Optional[int] = None
    trigger_type: str = 'MANUAL'


class BackupLogResponse(BaseModel):
    id: str
    organization_id: Optional[int] = None
    backup_type: str
    backup_date: datetime
    entities_included: Optional[dict] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    storage_location: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    encryption_used: bool
    status: str
    triggered_by: Optional[int] = None
    trigger_type: str
    error_message: Optional[str] = None
    retention_period_days: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
