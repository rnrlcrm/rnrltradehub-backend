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

    # Relationships
    role = relationship("Role", back_populates="users")


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


class MasterDataItem(Base, TimestampMixin):
    """Generic master data table for various configurations."""

    __tablename__ = "master_data_items"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., 'variety', 'quality_parameter'
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)  # Additional flexible data


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
