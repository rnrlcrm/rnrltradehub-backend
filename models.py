"""
SQLAlchemy database models matching frontend TypeScript schema.

This module contains all database table definitions based on the frontend types.
All models inherit common timestamp fields for audit tracking.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    Text, Enum, ForeignKey, JSON
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


class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True, index=True)

    @declared_attr
    def deleted_by(cls):
        return Column(Integer, ForeignKey('users.id'), nullable=True)

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False, index=True)


class VersionMixin:
    """Mixin to add version tracking."""

    @declared_attr
    def version(cls):
        return Column(Integer, default=1, nullable=False)

    @declared_attr
    def version_comment(cls):
        return Column(Text, nullable=True)

    @declared_attr
    def last_modified_by(cls):
        return Column(Integer, ForeignKey('users.id'), nullable=True)


class CciTerm(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
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


class CommissionStructure(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """Commission structure configuration table."""

    __tablename__ = "commission_structures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum('PERCENTAGE', 'PER_BALE', name='commission_type'), nullable=False)
    value = Column(Float, nullable=False)


class GstRate(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """GST rates configuration table."""

    __tablename__ = "gst_rates"

    id = Column(Integer, primary_key=True, index=True)
    rate = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    hsn_code = Column(String(50), nullable=False)


class Location(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
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


class BusinessPartner(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
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


class Commission(Base, TimestampMixin):
    """Commission table."""

    __tablename__ = "commissions"

    id = Column(String(36), primary_key=True)
    commission_id = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    sales_contract_id = Column(String(36), ForeignKey('sales_contracts.id'), nullable=False)
    agent = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(
        Enum('Due', 'Paid', name='commission_status'),
        nullable=False,
        default='Due'
    )


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


class MasterDataItem(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """Generic master data table for various configurations."""

    __tablename__ = "master_data_items"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., 'variety', 'quality_parameter'
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON)  # Additional flexible data


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


class Setting(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
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


class DataRetentionPolicy(Base, TimestampMixin):
    """Data retention policies for compliance."""

    __tablename__ = "data_retention_policies"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), unique=True, nullable=False, index=True)
    retention_days = Column(Integer, nullable=False)  # How long to keep data
    archive_after_days = Column(Integer)  # When to archive
    delete_after_days = Column(Integer)  # When to permanently delete
    policy_type = Column(String(100), nullable=False)  # 'legal', 'business', 'regulatory'
    description = Column(Text)
    is_active = Column(Boolean, default=True)


class DataAccessLog(Base, TimestampMixin):
    """Access logs for sensitive data (GDPR/compliance)."""

    __tablename__ = "data_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # 'view', 'export', 'modify', 'delete'
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    purpose = Column(Text)  # Why the data was accessed
    metadata_json = Column(JSON)


class ConsentRecord(Base, TimestampMixin):
    """User consent records for GDPR compliance."""

    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    business_partner_id = Column(String(36), ForeignKey('business_partners.id'))
    consent_type = Column(String(100), nullable=False)  # 'data_processing', 'marketing', 'third_party'
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime, nullable=False)
    withdrawn_date = Column(DateTime)
    ip_address = Column(String(50))
    metadata_json = Column(JSON)


class DataExportRequest(Base, TimestampMixin):
    """GDPR data export requests."""

    __tablename__ = "data_export_requests"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    business_partner_id = Column(String(36), ForeignKey('business_partners.id'))
    request_type = Column(String(100), nullable=False)  # 'export', 'deletion'
    status = Column(
        Enum('pending', 'processing', 'completed', 'failed', name='export_status'),
        default='pending',
        nullable=False,
        index=True
    )
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    export_file_path = Column(String(1000))
    metadata_json = Column(JSON)


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


class SystemConfiguration(Base, TimestampMixin):
    """System configuration for encryption, storage, etc."""

    __tablename__ = "system_configurations"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(255), unique=True, nullable=False, index=True)
    config_value = Column(Text)
    config_type = Column(String(50), default='string')  # 'string', 'json', 'encrypted'
    category = Column(String(100), nullable=False, index=True)  # 'storage', 'email', 'security', 'compliance'
    is_encrypted = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)


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

class UserBranch(Base, TimestampMixin):
    """User branch assignments for multi-branch access control."""

    __tablename__ = "user_branches"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey('business_branches.id', ondelete='CASCADE'), nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="user_branches")
    branch = relationship("BusinessBranch", backref="user_assignments")


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


class BusinessPartnerVersion(Base, TimestampMixin):
    """Version history for business partners."""

    __tablename__ = "business_partner_versions"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)  # Complete partner data at this version
    changed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    change_reason = Column(Text, nullable=True)
    amendment_request_id = Column(String(36), ForeignKey('amendment_requests.id'), nullable=True)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)

    # Relationships
    partner = relationship("BusinessPartner", backref="versions")
    user = relationship("User")
    amendment = relationship("AmendmentRequest")


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


class ProfileUpdateRequest(Base, TimestampMixin):
    """User profile update requests for approval workflow."""

    __tablename__ = "profile_update_requests"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    partner_id = Column(String(36), ForeignKey('business_partners.id'), nullable=True, index=True)
    update_type = Column(String(50), nullable=False)  # CONTACT, ADDRESS, COMPLIANCE, DOCUMENT, BRANCH
    old_values = Column(JSON, nullable=False)
    new_values = Column(JSON, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default='PENDING', index=True)  # PENDING, APPROVED, REJECTED
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    partner = relationship("BusinessPartner")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


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


class KYCReminderLog(Base, TimestampMixin):
    """KYC reminder logs for tracking sent reminders."""

    __tablename__ = "kyc_reminder_logs"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), ForeignKey('business_partners.id'), nullable=False, index=True)
    reminder_type = Column(String(50), nullable=False)  # 30_DAYS, 15_DAYS, 7_DAYS, 1_DAY, OVERDUE
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    recipient_email = Column(String(255), nullable=False)

    # Relationships
    partner = relationship("BusinessPartner", backref="kyc_reminders")


class CustomModule(Base, TimestampMixin):
    """Custom modules for dynamic RBAC system."""

    __tablename__ = "custom_modules"

    id = Column(String(36), primary_key=True)
    module_key = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)


class CustomPermission(Base, TimestampMixin):
    """Custom permissions for dynamic RBAC system."""

    __tablename__ = "custom_permissions"

    id = Column(String(36), primary_key=True)
    module_id = Column(String(36), ForeignKey('custom_modules.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_key = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE, EXECUTE, APPROVE
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    module = relationship("CustomModule", backref="permissions")


class RolePermission(Base, TimestampMixin):
    """Role permissions mapping for dynamic RBAC."""

    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey('custom_permissions.id', ondelete='CASCADE'), nullable=False, index=True)
    granted = Column(Boolean, default=True)

    # Relationships
    role = relationship("Role")
    permission = relationship("CustomPermission")


class UserPermissionOverride(Base, TimestampMixin):
    """User-specific permission overrides."""

    __tablename__ = "user_permission_overrides"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey('custom_permissions.id', ondelete='CASCADE'), nullable=False, index=True)
    granted = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=True)
    granted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    permission = relationship("CustomPermission")
    granter = relationship("User", foreign_keys=[granted_by])


class SuspiciousActivity(Base, TimestampMixin):
    """Suspicious activities log for security monitoring."""

    __tablename__ = "suspicious_activities"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, index=True)  # RAPID_FIRE, GEO_ANOMALY, AFTER_HOURS, UNUSUAL_ACTION
    details = Column(JSON, nullable=False)
    risk_score = Column(Integer, nullable=False)  # 0-100
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    action_taken = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# ============================================================================
# TRADE DESK & CHATBOT MODELS
# ============================================================================

class ChatSession(Base, TimestampMixin):
    """Chat sessions for AI-powered trade capture."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    session_type = Column(String(50), nullable=False)  # TRADE_CAPTURE, PAYMENT_QUERY, DISPUTE, STATEMENT
    status = Column(
        Enum('ACTIVE', 'COMPLETED', 'ABANDONED', 'ERROR', name='chat_session_status'),
        nullable=False,
        default='ACTIVE'
    )
    context_data = Column(JSON)  # Session state/context
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="chat_sessions")
    organization = relationship("Organization", backref="chat_sessions")


class ChatMessage(Base, TimestampMixin):
    """Individual messages in chat sessions."""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    message_type = Column(
        Enum('USER_INPUT', 'BOT_RESPONSE', 'BOT_QUESTION', 'VALIDATION_ERROR', 'SYSTEM', name='chat_message_type'),
        nullable=False
    )
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON)  # Additional context
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    session = relationship("ChatSession", backref="messages")


class Trade(Base, TimestampMixin):
    """Trade records from AI or manual capture."""

    __tablename__ = "trades"

    id = Column(String(36), primary_key=True)
    trade_number = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    
    # Source
    source = Column(
        Enum('AI_CHATBOT', 'MANUAL_ENTRY', 'API_IMPORT', name='trade_source'),
        nullable=False
    )
    session_id = Column(String(36), ForeignKey('chat_sessions.id'), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Trade details
    trade_date = Column(DateTime, nullable=False)
    commodity_id = Column(Integer, ForeignKey('master_data_items.id'), nullable=False)
    client_id = Column(String(36), ForeignKey('business_partners.id'), nullable=False)
    vendor_id = Column(String(36), ForeignKey('business_partners.id'), nullable=False)
    agent_id = Column(String(36), ForeignKey('business_partners.id'), nullable=True)
    
    # Quantity and pricing
    quantity_bales = Column(Integer, nullable=False)
    quantity_kg = Column(Float, nullable=True)
    rate_per_unit = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # PER_BALE, PER_KG, etc.
    
    # Terms
    location = Column(String(255), nullable=False)
    delivery_terms = Column(String(255), nullable=False)
    payment_terms = Column(String(255), nullable=False)
    quality_terms = Column(JSON)  # Quality specifications
    
    # Status
    status = Column(
        Enum('DRAFT', 'PENDING_APPROVAL', 'CONFIRMED', 'CONTRACT_GENERATED', 'CANCELLED', 'AMENDED', name='trade_status'),
        nullable=False,
        default='DRAFT'
    )
    
    # Conversion to contract
    contract_id = Column(String(36), ForeignKey('sales_contracts.id'), nullable=True)
    converted_at = Column(DateTime, nullable=True)
    
    # Audit
    version = Column(Integer, nullable=False, default=1)
    amendment_reason = Column(Text)
    cancelled_reason = Column(Text)
    cancelled_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("ChatSession", backref="trades")
    creator = relationship("User", foreign_keys=[created_by])
    commodity = relationship("MasterDataItem")
    client = relationship("BusinessPartner", foreign_keys=[client_id])
    vendor = relationship("BusinessPartner", foreign_keys=[vendor_id])
    agent = relationship("BusinessPartner", foreign_keys=[agent_id])
    contract = relationship("SalesContract", backref="source_trade")
    canceller = relationship("User", foreign_keys=[cancelled_by])


# ============================================================================
# QUALITY INSPECTION & INVENTORY MODELS
# ============================================================================

class QualityInspection(Base, TimestampMixin):
    """Quality inspection records for contracts."""

    __tablename__ = "quality_inspections"

    id = Column(String(36), primary_key=True)
    inspection_number = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    
    # Links
    contract_id = Column(String(36), ForeignKey('sales_contracts.id'), nullable=False, index=True)
    lot_number = Column(String(100), nullable=True)
    
    # Inspection details
    inspection_date = Column(DateTime, nullable=False)
    inspector_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    inspection_location = Column(String(255), nullable=False)
    
    # Commodity specific parameters (stored as JSON for flexibility)
    parameters = Column(JSON, nullable=False)  # e.g., {"moisture": 12.5, "staple_length": 28, ...}
    
    # Status
    status = Column(
        Enum('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'APPROVED', 'REJECTED', 'RESAMPLING_REQUIRED', name='inspection_status'),
        nullable=False,
        default='SCHEDULED'
    )
    
    # Results
    result = Column(
        Enum('PASS', 'FAIL', 'CONDITIONAL_PASS', name='inspection_result'),
        nullable=True
    )
    remarks = Column(Text)
    
    # Approvals
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text)
    
    # Documents
    report_document_id = Column(String(36), ForeignKey('documents.id'), nullable=True)
    
    # Relationships
    contract = relationship("SalesContract", backref="inspections")
    inspector = relationship("User", foreign_keys=[inspector_id])
    approver = relationship("User", foreign_keys=[approved_by])
    report_document = relationship("Document")


class InspectionEvent(Base, TimestampMixin):
    """Events/actions during inspection lifecycle."""

    __tablename__ = "inspection_events"

    id = Column(String(36), primary_key=True)
    inspection_id = Column(String(36), ForeignKey('quality_inspections.id', ondelete='CASCADE'), nullable=False, index=True)
    event_type = Column(
        Enum('SCHEDULED', 'STARTED', 'SAMPLE_COLLECTED', 'TESTED', 'APPROVED', 'REJECTED', 'RESAMPLING_ORDERED', 'COMPLETED', name='inspection_event_type'),
        nullable=False
    )
    performed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_data = Column(JSON)  # Event-specific data
    notes = Column(Text)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    inspection = relationship("QualityInspection", backref="events")
    performer = relationship("User")


class Inventory(Base, TimestampMixin):
    """Inventory tracking for commodities."""

    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    
    # Item details
    commodity_id = Column(Integer, ForeignKey('master_data_items.id'), nullable=False)
    lot_number = Column(String(100), nullable=False, index=True)
    contract_id = Column(String(36), ForeignKey('sales_contracts.id'), nullable=True)
    
    # Location
    warehouse_location = Column(String(255), nullable=False)
    storage_zone = Column(String(100))
    
    # Quantity
    quantity_bales = Column(Integer, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    unit_weight_kg = Column(Float)
    
    # Status
    status = Column(
        Enum('IN_STOCK', 'RESERVED', 'IN_TRANSIT', 'DELIVERED', 'DAMAGED', 'RETURNED', name='inventory_status'),
        nullable=False,
        default='IN_STOCK'
    )
    
    # Quality
    quality_grade = Column(String(50))
    inspection_id = Column(String(36), ForeignKey('quality_inspections.id'), nullable=True)
    
    # Tracking
    received_date = Column(DateTime)
    dispatch_date = Column(DateTime)
    last_movement_date = Column(DateTime)
    
    # Metadata
    metadata_json = Column(JSON)
    
    # Relationships
    commodity = relationship("MasterDataItem")
    contract = relationship("SalesContract", backref="inventory_items")
    inspection = relationship("QualityInspection")


# ============================================================================
# LOGISTICS & DELIVERY MODELS
# ============================================================================

class Transporter(Base, TimestampMixin):
    """Transporter/logistics provider master."""

    __tablename__ = "transporters"

    id = Column(String(36), primary_key=True)
    transporter_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Contact
    contact_person = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(255))
    
    # Address
    address = Column(Text, nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(20))
    
    # Compliance
    pan = Column(String(50))
    gstin = Column(String(50))
    
    # Status
    status = Column(
        Enum('ACTIVE', 'INACTIVE', 'BLACKLISTED', name='transporter_status'),
        nullable=False,
        default='ACTIVE'
    )
    rating = Column(Float)  # 0-5 rating
    
    # Metadata
    notes = Column(Text)
    metadata_json = Column(JSON)


class DeliveryOrder(Base, TimestampMixin):
    """Delivery order for contract fulfillment."""

    __tablename__ = "delivery_orders"

    id = Column(String(36), primary_key=True)
    do_number = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    
    # Links
    contract_id = Column(String(36), ForeignKey('sales_contracts.id'), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey('invoices.id'), nullable=True)
    
    # Delivery details
    delivery_date = Column(DateTime, nullable=False)
    planned_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    
    # Quantity
    quantity_bales = Column(Integer, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    
    # Logistics
    transporter_id = Column(String(36), ForeignKey('transporters.id'), nullable=True)
    vehicle_number = Column(String(50))
    driver_name = Column(String(255))
    driver_phone = Column(String(50))
    
    # Locations
    pickup_location = Column(String(255), nullable=False)
    delivery_location = Column(String(255), nullable=False)
    
    # Status
    status = Column(
        Enum('DRAFT', 'SCHEDULED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED', 'PARTIALLY_DELIVERED', name='delivery_status'),
        nullable=False,
        default='DRAFT'
    )
    
    # Documents
    lr_number = Column(String(100))  # Lorry Receipt
    eway_bill_number = Column(String(100))
    
    # Notes
    remarks = Column(Text)
    cancellation_reason = Column(Text)
    
    # Relationships
    contract = relationship("SalesContract", backref="delivery_orders")
    transporter = relationship("Transporter", backref="delivery_orders")
    invoice = relationship("Invoice", backref="delivery_orders")


class DeliveryEvent(Base, TimestampMixin):
    """Track delivery order lifecycle events."""

    __tablename__ = "delivery_events"

    id = Column(String(36), primary_key=True)
    delivery_order_id = Column(String(36), ForeignKey('delivery_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    event_type = Column(
        Enum('CREATED', 'SCHEDULED', 'TRANSPORTER_ASSIGNED', 'DISPATCHED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED', 'RESCHEDULED', name='delivery_event_type'),
        nullable=False
    )
    performed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_data = Column(JSON)  # Event-specific data
    notes = Column(Text)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    location = Column(String(255))  # GPS or manual location entry
    
    # Relationships
    delivery_order = relationship("DeliveryOrder", backref="events")
    performer = relationship("User")


# ============================================================================
# ACCOUNTING & LEDGER MODELS
# ============================================================================

class ChartOfAccounts(Base, TimestampMixin):
    """Chart of accounts for double-entry bookkeeping."""

    __tablename__ = "chart_of_accounts"

    id = Column(String(36), primary_key=True)
    account_code = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Account type
    account_type = Column(
        Enum('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE', name='account_type'),
        nullable=False
    )
    account_subtype = Column(String(100))  # e.g., CURRENT_ASSET, FIXED_ASSET, ACCOUNTS_RECEIVABLE
    
    # Hierarchy
    parent_account_id = Column(String(36), ForeignKey('chart_of_accounts.id'), nullable=True)
    level = Column(Integer, default=1)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system_account = Column(Boolean, default=False)  # Cannot be deleted
    
    # Metadata
    description = Column(Text)
    
    # Relationships
    parent = relationship("ChartOfAccounts", remote_side=[id], backref="children")


class LedgerEntry(Base, TimestampMixin):
    """Double-entry ledger transactions."""

    __tablename__ = "ledger_entries"

    id = Column(String(36), primary_key=True)
    entry_number = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    
    # Transaction details
    transaction_date = Column(DateTime, nullable=False, index=True)
    transaction_type = Column(String(100), nullable=False)  # SALE, PURCHASE, PAYMENT, RECEIPT, ADJUSTMENT
    
    # Source reference
    source_type = Column(String(100), nullable=False)  # SALES_CONTRACT, INVOICE, PAYMENT, DISPUTE_RESOLUTION
    source_id = Column(String(36), nullable=False, index=True)
    
    # Voucher reference
    voucher_id = Column(String(36), ForeignKey('vouchers.id'), nullable=True)
    
    # Entry details
    account_id = Column(String(36), ForeignKey('chart_of_accounts.id'), nullable=False, index=True)
    entry_type = Column(
        Enum('DEBIT', 'CREDIT', name='ledger_entry_type'),
        nullable=False
    )
    amount = Column(Float, nullable=False)
    
    # Party reference
    party_type = Column(String(100))  # BUSINESS_PARTNER, TRANSPORTER, etc.
    party_id = Column(String(36))
    
    # Description
    narration = Column(Text, nullable=False)
    
    # Status
    status = Column(
        Enum('DRAFT', 'POSTED', 'CANCELLED', 'REVERSED', name='ledger_status'),
        nullable=False,
        default='DRAFT'
    )
    
    # Audit
    posted_by = Column(Integer, ForeignKey('users.id'))
    posted_at = Column(DateTime)
    reversed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reversed_at = Column(DateTime, nullable=True)
    reversal_reason = Column(Text)
    
    # Relationships
    account = relationship("ChartOfAccounts", backref="entries")
    voucher = relationship("Voucher", backref="entries")
    poster = relationship("User", foreign_keys=[posted_by])
    reverser = relationship("User", foreign_keys=[reversed_by])


class Voucher(Base, TimestampMixin):
    """Accounting vouchers (groups related ledger entries)."""

    __tablename__ = "vouchers"

    id = Column(String(36), primary_key=True)
    voucher_number = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    
    # Voucher details
    voucher_type = Column(
        Enum('JOURNAL', 'PAYMENT', 'RECEIPT', 'CONTRA', 'SALES', 'PURCHASE', 'CREDIT_NOTE', 'DEBIT_NOTE', name='voucher_type'),
        nullable=False
    )
    voucher_date = Column(DateTime, nullable=False, index=True)
    
    # Reference
    reference_number = Column(String(100))
    reference_date = Column(DateTime)
    
    # Description
    narration = Column(Text, nullable=False)
    
    # Status
    status = Column(
        Enum('DRAFT', 'POSTED', 'CANCELLED', 'REVERSED', name='voucher_status'),
        nullable=False,
        default='DRAFT'
    )
    
    # Total (for validation)
    debit_total = Column(Float, nullable=False, default=0)
    credit_total = Column(Float, nullable=False, default=0)
    
    # Audit
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    posted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    poster = relationship("User", foreign_keys=[posted_by])
    approver = relationship("User", foreign_keys=[approved_by])


class Reconciliation(Base, TimestampMixin):
    """Bank and ledger reconciliation records."""

    __tablename__ = "reconciliations"

    id = Column(String(36), primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    financial_year = Column(String(20), nullable=False, index=True)
    
    # Reconciliation details
    reconciliation_date = Column(DateTime, nullable=False, index=True)
    account_id = Column(String(36), ForeignKey('chart_of_accounts.id'), nullable=False)
    
    # Balances
    book_balance = Column(Float, nullable=False)
    bank_balance = Column(Float, nullable=False)
    difference = Column(Float, nullable=False)
    
    # Status
    status = Column(
        Enum('IN_PROGRESS', 'COMPLETED', 'DISCREPANCY', name='reconciliation_status'),
        nullable=False,
        default='IN_PROGRESS'
    )
    
    # Details
    reconciled_items = Column(JSON)  # Array of matched entries
    unmatched_items = Column(JSON)  # Array of unmatched entries
    notes = Column(Text)
    
    # Audit
    performed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    account = relationship("ChartOfAccounts")
    performer = relationship("User", foreign_keys=[performed_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# ============================================================================
# ENHANCED DISPUTE MODELS
# ============================================================================

class DisputeComment(Base, TimestampMixin):
    """Threaded comments on disputes."""

    __tablename__ = "dispute_comments"

    id = Column(String(36), primary_key=True)
    dispute_id = Column(String(36), ForeignKey('disputes.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_comment_id = Column(String(36), ForeignKey('dispute_comments.id'), nullable=True)
    
    # Comment details
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment_text = Column(Text, nullable=False)
    comment_type = Column(
        Enum('COMMENT', 'RESOLUTION_PROPOSAL', 'EVIDENCE_LINK', 'STATUS_UPDATE', name='comment_type'),
        nullable=False,
        default='COMMENT'
    )
    
    # Metadata
    attachments = Column(JSON)  # Array of document IDs
    is_internal = Column(Boolean, default=False)  # Internal notes not visible to external parties
    
    # Relationships
    dispute = relationship("Dispute", backref="comments")
    user = relationship("User")
    parent = relationship("DisputeComment", remote_side=[id], backref="replies")


class DisputeEvidence(Base, TimestampMixin):
    """Evidence documents linked to disputes."""

    __tablename__ = "dispute_evidence"

    id = Column(String(36), primary_key=True)
    dispute_id = Column(String(36), ForeignKey('disputes.id', ondelete='CASCADE'), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey('documents.id'), nullable=False)
    
    # Evidence details
    evidence_type = Column(String(100), nullable=False)  # CONTRACT, INVOICE, EMAIL, PHOTO, VIDEO, etc.
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(Text)
    
    # Metadata
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    dispute = relationship("Dispute", backref="evidence")
    document = relationship("Document")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    verifier = relationship("User", foreign_keys=[verified_by])


# ============================================================================
# REPORTING & NOTIFICATION MODELS
# ============================================================================

class ReportDefinition(Base, TimestampMixin):
    """Predefined reports configuration."""

    __tablename__ = "report_definitions"

    id = Column(String(36), primary_key=True)
    report_code = Column(String(50), unique=True, nullable=False, index=True)
    report_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # FINANCIAL, OPERATIONAL, COMPLIANCE, AUDIT
    
    # Configuration
    description = Column(Text)
    query_template = Column(Text)  # SQL or query structure
    parameters_schema = Column(JSON)  # Expected parameters
    
    # Access control
    required_permission = Column(String(100))
    is_public = Column(Boolean, default=False)
    
    # Format options
    supported_formats = Column(JSON)  # ['PDF', 'EXCEL', 'CSV']
    
    # Status
    is_active = Column(Boolean, default=True)


class ReportExecution(Base, TimestampMixin):
    """Track report generation requests."""

    __tablename__ = "report_executions"

    id = Column(String(36), primary_key=True)
    report_definition_id = Column(String(36), ForeignKey('report_definitions.id'), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Execution details
    requested_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    parameters = Column(JSON)  # Report parameters used
    
    # Status
    status = Column(
        Enum('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', name='report_status'),
        nullable=False,
        default='QUEUED'
    )
    
    # Results
    output_format = Column(String(20))  # PDF, EXCEL, CSV
    file_size = Column(Integer)
    storage_path = Column(String(1000))
    download_url = Column(String(1000))
    url_expires_at = Column(DateTime)  # Expiring download link
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Relationships
    report_definition = relationship("ReportDefinition", backref="executions")
    requester = relationship("User")


class NotificationQueue(Base, TimestampMixin):
    """Queue for batched notifications."""

    __tablename__ = "notification_queue"

    id = Column(String(36), primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String(100), nullable=False, index=True)  # EMAIL, SMS, WEBHOOK, PUSH
    recipient_type = Column(String(100), nullable=False)  # USER, PARTNER, ROLE
    recipient_id = Column(String(100), nullable=False)
    
    # Content
    subject = Column(String(500))
    message = Column(Text, nullable=False)
    template_id = Column(Integer, ForeignKey('email_templates.id'), nullable=True)
    template_data = Column(JSON)  # Template variables
    
    # Priority and scheduling
    priority = Column(
        Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', name='notification_priority'),
        nullable=False,
        default='NORMAL'
    )
    scheduled_for = Column(DateTime, nullable=True)
    
    # Status
    status = Column(
        Enum('QUEUED', 'PROCESSING', 'SENT', 'FAILED', 'CANCELLED', name='notification_status'),
        nullable=False,
        default='QUEUED'
    )
    
    # Delivery
    sent_at = Column(DateTime)
    delivery_status = Column(String(100))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Audit
    created_by_user = Column(Integer, ForeignKey('users.id'), nullable=True)
    source_entity_type = Column(String(100))  # What triggered this notification
    source_entity_id = Column(String(100))
    
    # Relationships
    template = relationship("EmailTemplate")
    creator = relationship("User")


class BackupLog(Base, TimestampMixin):
    """Track system backups and exports."""

    __tablename__ = "backup_logs"

    id = Column(String(36), primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)
    
    # Backup details
    backup_type = Column(
        Enum('FULL', 'INCREMENTAL', 'DATA_EXPORT', 'COMPLIANCE_EXPORT', name='backup_type'),
        nullable=False
    )
    backup_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Scope
    entities_included = Column(JSON)  # List of table/entity types backed up
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    
    # Storage
    storage_location = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    checksum = Column(String(100))  # For integrity verification
    encryption_used = Column(Boolean, default=False)
    
    # Status
    status = Column(
        Enum('IN_PROGRESS', 'COMPLETED', 'FAILED', name='backup_status'),
        nullable=False,
        default='IN_PROGRESS'
    )
    
    # Details
    triggered_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    trigger_type = Column(String(50))  # MANUAL, SCHEDULED, AUTOMATED
    error_message = Column(Text)
    
    # Retention
    retention_period_days = Column(Integer)
    expires_at = Column(DateTime)
    
    # Relationships
    triggerer = relationship("User")
