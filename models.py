"""
SQLAlchemy database models matching frontend TypeScript schema.

This module contains all database table definitions based on the frontend types.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    Text, Enum, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database import Base


class CciTerm(Base):
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommissionStructure(Base):
    """Commission structure configuration table."""

    __tablename__ = "commission_structures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum('PERCENTAGE', 'PER_BALE', name='commission_type'), nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GstRate(Base):
    """GST rates configuration table."""

    __tablename__ = "gst_rates"

    id = Column(Integer, primary_key=True, index=True)
    rate = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    hsn_code = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Location(Base):
    """Location master data table."""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User table for authentication and role management."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        Enum('Admin', 'Sales', 'Accounts', 'Dispute Manager', 'Vendor/Client', name='user_role'),
        nullable=False
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Address(Base):
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business_partner = relationship("BusinessPartner", back_populates="shipping_addresses")


class BusinessPartner(Base):
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

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipping_addresses = relationship("Address", back_populates="business_partner", cascade="all, delete-orphan")


class SalesContract(Base):
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

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Invoice(Base):
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(Base):
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Dispute(Base):
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Commission(Base):
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
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
    created_at = Column(DateTime, default=datetime.utcnow)
