"""
SQLAlchemy database models matching frontend TypeScript schema.

This module contains all database table definitions based on the frontend types.
All models inherit common timestamp fields for audit tracking.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    Text, Enum, ForeignKey, JSON, Numeric, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from database import Base


class TimestampMixin:
    """Mixin to add timestamp fields to all models."""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CciTerm(Base, TimestampMixin):
    """CCI Terms configuration table."""

    __tablename__ = "cci_terms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contract_period_days = Column(Integer, nullable=False)
    emd_payment_days = Column(Integer, nullable=False)
    cash_discount_percentage = Column(Float, nullable=False)
    carrying_charge_tier1_days = Column(Integer, nullable=False)
    carrying_charge_tier1_percent = Column(Float, nullable=False)
    carrying_charge_tier2_days = Column(Integer, nullable=False)
    carrying_charge_tier2_percent = Column(Float, nullable=False)
    additional_deposit_percent = Column(Float, nullable=False)
    deposit_interest_percent = Column(Float, nullable=False)
    free_lifting_period_days = Column(Integer, nullable=False)
    late_lifting_tier1_days = Column(Integer, nullable=False)
    late_lifting_tier1_percent = Column(Float, nullable=False)
    late_lifting_tier2_days = Column(Integer, nullable=False)
    late_lifting_tier2_percent = Column(Float, nullable=False)
    late_lifting_tier3_percent = Column(Float, nullable=False)


class CommissionStructure(Base, TimestampMixin):
    """Commission structure configuration table."""

    __tablename__ = "commission_structures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum('PERCENTAGE', 'PER_BALE', name='commission_type'), nullable=False)
    value = Column(Float, nullable=False)


class GstRate(Base, TimestampMixin):
    """GST rates configuration table."""

    __tablename__ = "gst_rates"

    id = Column(Integer, primary_key=True, index=True)
    rate = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    hsn_code = Column(String(50), nullable=False)


class Location(Base, TimestampMixin):
    """Location master data table."""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)


class User(Base, TimestampMixin):
    """User table for authentication and role management."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)  # Foreign key to roles table
    role_name = Column(
        Enum('Admin', 'Sales', 'Accounts', 'Dispute Manager', 'Vendor/Client', name='user_role'),
        nullable=True
    )  # Kept for backward compatibility
    is_active = Column(Boolean, default=True)
    
    # Multi-tenant support
    client_id = Column(String(36), ForeignKey('business_partners.id'), nullable=True, index=True)
    vendor_id = Column(String(36), ForeignKey('business_partners.id'), nullable=True, index=True)
    parent_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    user_type = Column(
        Enum('primary', 'sub_user', name='user_type'),
        nullable=False,
        default='primary'
    )
    max_sub_users = Column(Integer, default=5)  # Limit for sub-users

    # Enhanced user management columns (Phase 1.1)
    business_partner_id = Column(String(36), ForeignKey('business_partners.id'), nullable=True, index=True)
    user_type_new = Column(String(50), default='back_office')  # back_office, business_partner
    is_first_login = Column(Boolean, default=True)
    password_expiry_date = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users")
    parent_user = relationship("User", remote_side=[id], backref="sub_users")
    client = relationship("BusinessPartner", foreign_keys=[client_id])
    vendor = relationship("BusinessPartner", foreign_keys=[vendor_id])
    business_partner = relationship("BusinessPartner", foreign_keys=[business_partner_id])
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    sub_user_invites = relationship("SubUserInvite", back_populates="parent_user", cascade="all, delete-orphan")


class Address(Base, TimestampMixin):
    """Address table for business partners."""

    __tablename__ = "addresses"

    id = Column(String(36), primary_key=True)
    business_partner_id = Column(String(36), ForeignKey('business_partners.id'), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)

    business_partner = relationship("BusinessPartner", back_populates="shipping_addresses")


class BusinessPartner(Base, TimestampMixin):
    """Business Partner (Vendor/Client/Agent) table."""

    __tablename__ = "business_partners"

    id = Column(String(36), primary_key=True)
    bp_code = Column(String(50), unique=True, nullable=False, index=True)
    legal_name = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    business_type = Column(
        Enum('BUYER', 'SELLER', 'BOTH', 'AGENT', name='business_type'),
        nullable=False
    )
    status = Column(
        Enum('DRAFT', 'PENDING_COMPLIANCE', 'ACTIVE', 'INACTIVE', 'BLACKLISTED', name='bp_status'),
        nullable=False,
        default='DRAFT'
    )
    kyc_due_date = Column(DateTime)

    # Contact Information
    contact_person = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)

    # Registered Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)

    # Compliance Information
    pan = Column(String(50), nullable=False)
    gstin = Column(String(50))
    bank_name = Column(String(255))
    bank_account_no = Column(String(50))
    bank_ifsc = Column(String(50))

    # Document URLs
    pan_doc_url = Column(String(500))
    gst_doc_url = Column(String(500))
    cheque_doc_url = Column(String(500))

    # Internal Notes
    compliance_notes = Column(Text)


    # Relationships
    shipping_addresses = relationship("Address", back_populates="business_partner", cascade="all, delete-orphan")
    certifications = relationship("PartnerCertification", back_populates="partner", cascade="all, delete-orphan")
    verifications = relationship("PartnerVerification", back_populates="partner", cascade="all, delete-orphan")


class SalesContract(Base, TimestampMixin):
    """Sales Contract table."""

    __tablename__ = "sales_contracts"

    id = Column(String(36), primary_key=True)
    sc_no = Column(String(50), unique=True, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    amendment_reason = Column(Text)
    date = Column(DateTime, nullable=False)
    organization = Column(String(255), nullable=False)
    financial_year = Column(String(20), nullable=False)

    # Parties
    client_id = Column(String(36), ForeignKey('business_partners.id'), nullable=False)
    client_name = Column(String(255), nullable=False)
    vendor_id = Column(String(36), ForeignKey('business_partners.id'), nullable=False)
    vendor_name = Column(String(255), nullable=False)
    agent_id = Column(String(36), ForeignKey('business_partners.id'))

    # Product Details
    variety = Column(String(255), nullable=False)
    quantity_bales = Column(Integer, nullable=False)
    rate = Column(Float, nullable=False)

    # GST and Commission
    gst_rate_id = Column(Integer, ForeignKey('gst_rates.id'))
    buyer_commission_id = Column(Integer, ForeignKey('commission_structures.id'))
    seller_commission_id = Column(Integer, ForeignKey('commission_structures.id'))
    buyer_commission_gst_id = Column(Integer, ForeignKey('gst_rates.id'))
    seller_commission_gst_id = Column(Integer, ForeignKey('gst_rates.id'))

    # Terms
    trade_type = Column(String(100), nullable=False)
    bargain_type = Column(String(100), nullable=False)
    weightment_terms = Column(String(255), nullable=False)
    passing_terms = Column(String(255), nullable=False)
    delivery_terms = Column(String(255), nullable=False)
    payment_terms = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)

    # Quality Specifications
    quality_specs = Column(JSON)

    # Additional Terms
    manual_terms = Column(Text)

    # Status
    status = Column(
        Enum('Active', 'Completed', 'Disputed', 'Carried Forward', 'Amended',
             'Pending Approval', 'Rejected', name='contract_status'),
        nullable=False,
        default='Active'
    )

    # CCI Details
    cci_contract_no = Column(String(100))
    cci_term_id = Column(Integer, ForeignKey('cci_terms.id'))



class Invoice(Base, TimestampMixin):
    """Invoice table."""

    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    sales_contract_id = Column(String(36), ForeignKey('sales_contracts.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(
        Enum('Unpaid', 'Partially Paid', 'Paid', name='invoice_status'),
        nullable=False,
        default='Unpaid'
    )


class Payment(Base, TimestampMixin):
    """Payment table."""

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True)
    payment_id = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey('invoices.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(
        Enum('Bank Transfer', 'Cheque', 'Cash', name='payment_method'),
        nullable=False
    )


class Dispute(Base, TimestampMixin):
    """Dispute table."""

    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True)
    dispute_id = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    sales_contract_id = Column(String(36), ForeignKey('sales_contracts.id'), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(
        Enum('Open', 'Resolved', 'Closed', name='dispute_status'),
        nullable=False,
        default='Open'
    )
    resolution = Column(Text)
    date_raised = Column(DateTime, nullable=False)





class AuditLog(Base, TimestampMixin):
    """Audit log table for tracking all system changes."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = Column(String(255), nullable=False)
    role = Column(
        Enum('Admin', 'Sales', 'Accounts', 'Dispute Manager', 'Vendor/Client', name='user_role_audit'),
        nullable=False
    )
    module = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=False)
    reason = Column(Text)


class UserAuditLog(Base, TimestampMixin):
    """User audit log table for tracking user activities."""

    __tablename__ = "user_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # login, logout, create, update, delete, etc.
    entity_type = Column(String(100), nullable=True)  # Type of entity affected
    entity_id = Column(String(100), nullable=True)  # ID of entity affected
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)  # Additional context
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship
    user = relationship("User", backref="audit_logs")


class MasterDataItem(Base, TimestampMixin):
    """Generic master data table for various configurations."""

    __tablename__ = "master_data_items"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., 'variety', 'quality_parameter'
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON)  # Additional flexible data


class Commodity(Base, TimestampMixin):
    """Dedicated Commodity Master table for product/variety management."""

    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True, index=True)
    commodity_code = Column(String(50), unique=True, nullable=False, index=True)
    commodity_name = Column(String(255), nullable=False, index=True)
    commodity_type = Column(String(100), nullable=False)  # e.g., 'Cotton', 'Wheat', 'Rice'
    variety = Column(String(255))  # Specific variety within commodity type
    grade = Column(String(100))  # Quality grade
    hsn_code = Column(String(50), index=True)  # HSN code for taxation
    uom = Column(String(50), default='BALES')  # Unit of measurement (BALES, KG, QUINTAL, MT)
    description = Column(Text)
    quality_parameters = Column(JSON)  # Store quality specs like length, mic, rd, etc.
    is_active = Column(Boolean, default=True, index=True)
    metadata_json = Column(JSON)  # Additional flexible data (renamed from 'metadata' to avoid conflict)


class StructuredTerm(Base, TimestampMixin):
    """Structured terms for payments, delivery, etc."""

    __tablename__ = "structured_terms"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # 'payment', 'delivery', 'passing', etc.
    name = Column(String(255), nullable=False)
    days = Column(Integer, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)


class Role(Base, TimestampMixin):
    """User roles for RBAC."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relationships
    permissions = relationship("Permission", back_populates="role", cascade="all, delete-orphan")
    users = relationship("User", back_populates="role")


class Permission(Base, TimestampMixin):
    """Permissions for role-based access control."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    module = Column(String(100), nullable=False)  # 'Sales Contracts', 'Invoices', etc.
    can_create = Column(Boolean, default=False)
    can_read = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_approve = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)

    # Relationships
    role = relationship("Role", back_populates="permissions")


class Setting(Base, TimestampMixin):
    """System settings and configuration."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # 'system', 'email', 'notification', etc.
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String(50), default='string')  # 'string', 'number', 'boolean', 'json'
    description = Column(Text)
    is_public = Column(Boolean, default=False)  # Whether setting can be viewed by non-admins
    is_editable = Column(Boolean, default=True)  # Whether setting can be modified via UI


class Document(Base, TimestampMixin):
    """Document/file storage table for managing uploaded files."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., 'business_partner', 'sales_contract'
    entity_id = Column(String(36), nullable=False, index=True)  # ID of the related entity
    document_type = Column(String(100), nullable=False)  # e.g., 'PAN', 'GST', 'Invoice', 'Contract'
    file_name = Column(String(500), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    file_type = Column(String(100))  # MIME type
    storage_path = Column(String(1000), nullable=False)  # Cloud storage path (GCS/S3)
    storage_url = Column(String(1000))  # Public/signed URL
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    metadata_json = Column(JSON)  # Additional file metadata


class EmailTemplate(Base, TimestampMixin):
    """Email templates for automated notifications."""

    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # 'notification', 'alert', 'report'
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)  # HTML template
    body_text = Column(Text)  # Plain text fallback
    variables = Column(JSON)  # List of template variables
    is_active = Column(Boolean, default=True)
    description = Column(Text)


class EmailLog(Base, TimestampMixin):
    """Email log for tracking sent emails."""

    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('email_templates.id'))
    recipient = Column(String(500), nullable=False)
    cc = Column(String(1000))
    bcc = Column(String(1000))
    subject = Column(String(500), nullable=False)
    body = Column(Text)
    status = Column(
        Enum('pending', 'sent', 'failed', 'bounced', name='email_status'),
        default='pending',
        nullable=False,
        index=True
    )
    sent_at = Column(DateTime)
    error_message = Column(Text)
    metadata_json = Column(JSON)  # Additional tracking data














class SecurityEvent(Base, TimestampMixin):
    """Security events and incidents log."""

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # 'login_failed', 'access_denied', 'suspicious_activity'
    severity = Column(
        Enum('low', 'medium', 'high', 'critical', name='severity_level'),
        nullable=False,
        index=True
    )
    user_id = Column(Integer, ForeignKey('users.id'))
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    description = Column(Text, nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    metadata_json = Column(JSON)





class Organization(Base, TimestampMixin):
    """Organization table for multi-company support."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    legal_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    pan = Column(String(50), unique=True, nullable=False, index=True)
    gstin = Column(String(50), unique=True, index=True)
    address = Column(JSON)  # Registered address as JSON
    logo_url = Column(String(500))
    settings = Column(JSON)  # Organization-specific settings
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    financial_years = relationship("FinancialYear", back_populates="organization")


class FinancialYear(Base, TimestampMixin):
    """Financial year table for Indian accounting (April-March)."""

    __tablename__ = "financial_years"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    year_code = Column(String(20), nullable=False, index=True)  # e.g., "2023-24"
    start_date = Column(DateTime, nullable=False)  # April 1
    end_date = Column(DateTime, nullable=False)  # March 31
    assessment_year = Column(String(20), nullable=False)  # e.g., "2024-25" (FY + 1)
    is_active = Column(Boolean, default=False, index=True)  # Current active year
    is_closed = Column(Boolean, default=False, index=True)  # Year-end closed
    opening_balances = Column(JSON)  # Opening balances for this year

    # Relationships
    organization = relationship("Organization", back_populates="financial_years")
    transfers_from = relationship(
        "YearEndTransfer",
        foreign_keys="YearEndTransfer.from_financial_year_id",
        back_populates="from_financial_year"
    )
    transfers_to = relationship(
        "YearEndTransfer",
        foreign_keys="YearEndTransfer.to_financial_year_id",
        back_populates="to_financial_year"
    )


class YearEndTransfer(Base, TimestampMixin):
    """Year-end transfer log for tracking data moved between financial years."""

    __tablename__ = "year_end_transfers"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    from_financial_year_id = Column(Integer, ForeignKey('financial_years.id'), nullable=False)
    to_financial_year_id = Column(Integer, ForeignKey('financial_years.id'), nullable=False)
    transfer_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    transfer_type = Column(String(100), nullable=False, index=True)  # 'pending_invoices', 'opening_balances', etc.
    entity_type = Column(String(100), nullable=False)  # 'invoice', 'payment', 'commission', 'dispute'
    entity_count = Column(Integer, default=0)
    transfer_summary = Column(JSON)  # Details of what was transferred
    performed_by = Column(String(255), nullable=False)  # User who performed the transfer
    notes = Column(Text)

    # Relationships
    from_financial_year = relationship(
        "FinancialYear",
        foreign_keys=[from_financial_year_id],
        back_populates="transfers_from"
    )
    to_financial_year = relationship(
        "FinancialYear",
        foreign_keys=[to_financial_year_id],
        back_populates="transfers_to"
    )


# ========== NEW MODELS FOR ENHANCED ACCESS CONTROL (PHASE 1) ==========





class SubUser(Base, TimestampMixin):
    """Sub-users table - max 2 per parent user."""

    __tablename__ = "sub_users"

    id = Column(String(36), primary_key=True)
    parent_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    sub_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    parent = relationship("User", foreign_keys=[parent_user_id], backref="managed_sub_users")
    sub_user = relationship("User", foreign_keys=[sub_user_id])


class BusinessBranch(Base, TimestampMixin):
    """Business branches for multi-branch support."""

    __tablename__ = "business_branches"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_code = Column(String(50), nullable=False)
    branch_name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    gst_number = Column(String(15), unique=True, nullable=False)
    address = Column(JSON, nullable=False)
    contact_person = Column(JSON, nullable=True)
    bank_details = Column(JSON, nullable=True)
    is_head_office = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    partner = relationship("BusinessPartner", backref="branches")


class AmendmentRequest(Base, TimestampMixin):
    """Amendment requests for entities with approval workflow."""

    __tablename__ = "amendment_requests"

    id = Column(String(36), primary_key=True)
    entity_type = Column(String(50), nullable=False, index=True)  # business_partner, branch, user
    entity_id = Column(String(36), nullable=False, index=True)
    request_type = Column(String(50), nullable=False)  # UPDATE, DELETE
    reason = Column(Text, nullable=False)
    justification = Column(Text, nullable=True)
    requested_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default='PENDING', index=True)  # PENDING, APPROVED, REJECTED
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    changes = Column(JSON, nullable=False)  # old_values and new_values
    impact_assessment = Column(JSON, nullable=True)

    # Relationships
    requester = relationship("User", foreign_keys=[requested_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])






class OnboardingApplication(Base, TimestampMixin):
    """Self-service onboarding applications."""

    __tablename__ = "onboarding_applications"

    id = Column(String(36), primary_key=True)
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    company_info = Column(JSON, nullable=False)
    contact_info = Column(JSON, nullable=False)
    compliance_info = Column(JSON, nullable=False)
    branch_info = Column(JSON, nullable=True)
    documents = Column(JSON, nullable=True)
    status = Column(String(50), default='SUBMITTED', index=True)  # SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    reviewer = relationship("User")






class KYCVerification(Base, TimestampMixin):
    """KYC verification records for business partners."""

    __tablename__ = "kyc_verifications"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey('business_partners.id'), nullable=False, index=True)
    verification_date = Column(DateTime, nullable=False)
    verified_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    documents_checked = Column(JSON, nullable=False)  # List of documents verified
    status = Column(String(50), nullable=False, index=True)  # CURRENT, DUE_SOON, OVERDUE
    next_due_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    partner = relationship("BusinessPartner", backref="kyc_records")
    verifier = relationship("User")

























# ============================================================================
# NEW MODELS - Added based on frontend requirements
# ============================================================================


class Session(Base, TimestampMixin):
    """User session management for JWT refresh tokens."""
    
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(String(500), unique=True, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    
    # Relationship
    user = relationship("User", back_populates="sessions")


class PasswordResetToken(Base, TimestampMixin):
    """Password reset token management."""
    
    __tablename__ = "password_reset_tokens"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    
    # Relationship
    user = relationship("User", back_populates="password_reset_tokens")


class PartnerCertification(Base, TimestampMixin):
    """Product certifications for business partners (visible in trades)."""
    
    __tablename__ = "partner_certifications"
    
    id = Column(String(36), primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    certification_type = Column(String(100), nullable=False)
    certification_name = Column(String(255), nullable=False)
    certification_body = Column(String(255), nullable=False)
    certificate_number = Column(String(100))
    products_scope = Column(JSON)  # List of products covered
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    status = Column(Enum("PENDING", "VERIFIED", "EXPIRED", "REJECTED", name="cert_status"), default="PENDING")
    verified_by = Column(String(36))
    verified_at = Column(DateTime)
    document_url = Column(String(500))
    is_visible_in_trade = Column(Boolean, default=True)
    
    # Relationship
    partner = relationship("BusinessPartner", back_populates="certifications")


class PartnerVerification(Base, TimestampMixin):
    """OTP verification for partner registration."""
    
    __tablename__ = "partner_verifications"
    
    id = Column(String(36), primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    verification_type = Column(Enum("EMAIL", "MOBILE", name="verification_type"), nullable=False)
    value = Column(String(255), nullable=False)  # Email or phone number
    otp = Column(String(10), nullable=False)
    attempts = Column(Integer, default=0)
    verified_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationship
    partner = relationship("BusinessPartner", back_populates="verifications")


class ApprovalWorkflow(Base, TimestampMixin):
    """Approval workflows for users and partners."""
    
    __tablename__ = "approval_workflows"
    
    id = Column(String(36), primary_key=True, index=True)
    request_type = Column(Enum("USER_CREATION", "USER_MODIFICATION", "ROLE_ASSIGNMENT", "PARTNER_APPROVAL", name="request_type"), nullable=False)
    requester_id = Column(String(36))
    requester_name = Column(String(255), nullable=False)
    target_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    target_user_email = Column(String(255), nullable=False)
    details = Column(JSON, nullable=False)
    status = Column(Enum("PENDING", "APPROVED", "REJECTED", name="workflow_status"), default="PENDING")
    approved_by = Column(String(36))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)


class SubUserInvite(Base, TimestampMixin):
    """Sub-user invitation system."""
    
    __tablename__ = "sub_user_invites"
    
    id = Column(String(36), primary_key=True, index=True)
    parent_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    branch_ids = Column(JSON, nullable=False)  # List of branch IDs
    permissions = Column(JSON, nullable=False)
    status = Column(Enum("PENDING", "ACCEPTED", "EXPIRED", "CANCELLED", name="invite_status"), default="PENDING")
    invite_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationship
    parent_user = relationship("User", back_populates="sub_user_invites")


class Trade(Base, TimestampMixin):
    """Trade requests from buyers (Trade Desk module)."""
    
    __tablename__ = "trades"
    
    id = Column(String(36), primary_key=True, index=True)
    trade_number = Column(String(50), unique=True, nullable=False)
    buyer_id = Column(String(36), ForeignKey("business_partners.id"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    price_range_min = Column(Numeric(12, 2))
    price_range_max = Column(Numeric(12, 2))
    delivery_location_id = Column(Integer, ForeignKey("locations.id"))
    delivery_date = Column(DateTime)
    quality_parameters = Column(JSON)
    status = Column(Enum("OPEN", "MATCHED", "PARTIAL", "CLOSED", "CANCELLED", name="trade_status"), default="OPEN")
    parsed_from_text = Column(Text)  # Original NLP input
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    buyer = relationship("BusinessPartner", foreign_keys=[buyer_id])
    commodity = relationship("Commodity")
    location = relationship("Location", foreign_keys=[delivery_location_id])
    offers = relationship("Offer", back_populates="trade")


class Offer(Base, TimestampMixin):
    """Seller offers in response to trade requests."""
    
    __tablename__ = "offers"
    
    id = Column(String(36), primary_key=True, index=True)
    offer_number = Column(String(50), unique=True, nullable=False)
    trade_id = Column(String(36), ForeignKey("trades.id", ondelete="CASCADE"), nullable=False)
    seller_id = Column(String(36), ForeignKey("business_partners.id"), nullable=False)
    tested_lot_id = Column(String(36), ForeignKey("tested_lots.id"))
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    delivery_location_id = Column(Integer, ForeignKey("locations.id"))
    delivery_date = Column(DateTime)
    quality_specs = Column(JSON)
    matching_score = Column(Float)  # Algorithm-calculated match score
    status = Column(Enum("PENDING", "ACCEPTED", "REJECTED", "NEGOTIATING", "EXPIRED", name="offer_status"), default="PENDING")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    trade = relationship("Trade", back_populates="offers")
    seller = relationship("BusinessPartner", foreign_keys=[seller_id])
    tested_lot = relationship("TestedLot")
    location = relationship("Location", foreign_keys=[delivery_location_id])
    negotiations = relationship("Negotiation", back_populates="offer")


class TestedLot(Base, TimestampMixin):
    """Pre-tested commodity inventory for quick matching."""
    
    __tablename__ = "tested_lots"
    
    id = Column(String(36), primary_key=True, index=True)
    lot_number = Column(String(50), unique=True, nullable=False)
    seller_id = Column(String(36), ForeignKey("business_partners.id"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    test_report_url = Column(String(500))
    quality_parameters = Column(JSON, nullable=False)
    storage_location_id = Column(Integer, ForeignKey("locations.id"))
    available_from = Column(DateTime, nullable=False)
    available_until = Column(DateTime)
    status = Column(Enum("AVAILABLE", "RESERVED", "SOLD", "EXPIRED", name="lot_status"), default="AVAILABLE")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    seller = relationship("BusinessPartner", foreign_keys=[seller_id])
    commodity = relationship("Commodity")
    location = relationship("Location", foreign_keys=[storage_location_id])


class Negotiation(Base, TimestampMixin):
    """Counter-offer negotiation history."""
    
    __tablename__ = "negotiations"
    
    id = Column(String(36), primary_key=True, index=True)
    offer_id = Column(String(36), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    initiated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    counter_price = Column(Numeric(12, 2))
    counter_quantity = Column(Float)
    counter_delivery_date = Column(DateTime)
    message = Column(Text)
    status = Column(Enum("PENDING", "ACCEPTED", "REJECTED", "COUNTERED", name="negotiation_status"), default="PENDING")
    responded_by = Column(String(36))
    responded_at = Column(DateTime)
    
    # Relationships
    offer = relationship("Offer", back_populates="negotiations")
    initiator = relationship("User", foreign_keys=[initiated_by])

