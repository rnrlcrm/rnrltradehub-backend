"""
Clean Backend Database Models - Matching Frontend Requirements Only

This file contains ONLY the database models that the frontend actually uses.
All unused tables have been removed for clarity and simplicity.

Frontend Modules Supported:
1. Settings (Organizations, Locations, CCI Terms, Commodities)
2. Trade Desk (Trades, Offers, Tested Lots, Negotiations) 
3. Business Partners
4. Financial Year
5. Auth & Users
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    Text, Enum, ForeignKey, JSON, Numeric
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


# ============================================================================
# AUTH & USER MANAGEMENT
# ============================================================================

class User(Base, TimestampMixin):
    """User authentication and profile."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")


class Role(Base, TimestampMixin):
    """User roles (Admin, Sales, Buyer Partner, Seller Partner, etc.)."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", back_populates="role")


class Permission(Base, TimestampMixin):
    """Role-based permissions."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    module = Column(String(100), nullable=False)  # e.g., 'trade_desk', 'settings'
    action = Column(String(100), nullable=False)  # e.g., 'create', 'read', 'update', 'delete'
    
    # Relationships
    role = relationship("Role", back_populates="permissions")


# ============================================================================
# SETTINGS MODULE
# ============================================================================

class Organization(Base, TimestampMixin):
    """Organization/Company master."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    organization_type = Column(String(50))  # PROPRIETORSHIP, PARTNERSHIP, etc.
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    country = Column(String(100), default='India')
    phone = Column(String(20))
    email = Column(String(255))
    gstin = Column(String(50), unique=True, index=True)
    pan = Column(String(20), index=True)
    tan = Column(String(20))
    cin = Column(String(50))
    bank_name = Column(String(255))
    account_number = Column(String(50))
    ifsc_code = Column(String(20))
    branch = Column(String(255))
    website = Column(String(255))
    logo_url = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    financial_years = relationship("FinancialYear", back_populates="organization")


class Location(Base, TimestampMixin):
    """Location hierarchy (Country > State > Region > City/Station)."""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    region = Column(String(100), index=True)  # Optional: Vidarbha, Saurashtra, etc.
    city = Column(String(100), nullable=False, index=True)  # Also called Station


class CciTerm(Base, TimestampMixin):
    """CCI (Cotton Corporation of India) Terms configuration."""

    __tablename__ = "cci_terms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Versioning
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)
    
    # Core Financial Parameters
    candy_factor = Column(Numeric(10, 4), nullable=False)  # e.g., 0.2812
    gst_rate = Column(Numeric(5, 2), nullable=False)  # e.g., 5.00
    
    # EMD Configuration (JSON for buyer type percentages)
    emd_by_buyer_type = Column(JSON)  # {"kvic": 5, "privateMill": 10, "trader": 15}
    emd_payment_days = Column(Integer)
    emd_interest_percent = Column(Numeric(5, 2))
    emd_late_interest_percent = Column(Numeric(5, 2))
    emd_block_do_if_not_full = Column(Boolean, default=True)
    
    # Carrying Charges
    carrying_charge_tier1_days = Column(Integer)
    carrying_charge_tier1_percent = Column(Numeric(5, 2))
    carrying_charge_tier2_days = Column(Integer)
    carrying_charge_tier2_percent = Column(Numeric(5, 2))
    
    # Late Lifting Charges
    free_lifting_period_days = Column(Integer)
    late_lifting_tier1_days = Column(Integer)
    late_lifting_tier1_percent = Column(Numeric(5, 2))
    late_lifting_tier2_days = Column(Integer)
    late_lifting_tier2_percent = Column(Numeric(5, 2))
    late_lifting_tier3_percent = Column(Numeric(5, 2))
    
    # Payment & Discount
    cash_discount_percentage = Column(Numeric(5, 2))
    interest_lc_bg_percent = Column(Numeric(5, 2))
    penal_interest_lc_bg_percent = Column(Numeric(5, 2))
    
    # Additional Deposits
    additional_deposit_percent = Column(Numeric(5, 2))
    deposit_interest_percent = Column(Numeric(5, 2))
    
    # Periods
    lifting_period_days = Column(Integer)
    contract_period_days = Column(Integer)
    
    # Lock-in Charges
    lockin_charge_min = Column(Numeric(10, 2))  # Rs/bale
    lockin_charge_max = Column(Numeric(10, 2))  # Rs/bale
    
    # Moisture Adjustment
    moisture_lower_limit = Column(Numeric(5, 2))  # e.g., 7.00%
    moisture_upper_limit = Column(Numeric(5, 2))  # e.g., 9.00%
    moisture_sample_count = Column(Integer)
    
    # Email Configuration
    email_reminder_days = Column(Integer)
    email_template_emd_reminder = Column(Text)
    email_template_payment_due = Column(Text)


class Commodity(Base, TimestampMixin):
    """Commodity/Product master with trading parameters."""

    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Cotton, Wheat, Rice
    symbol = Column(String(10), unique=True, nullable=False)  # CTN, WHT, RIC
    unit = Column(String(50), nullable=False)  # Bales, Kgs, Tonnes
    rate_unit = Column(String(50))  # Candy (for cotton rate basis)
    
    # GST Configuration
    hsn_code = Column(String(50), index=True)
    gst_rate = Column(Numeric(5, 2))  # Auto-determined from HSN
    gst_exemption_available = Column(Boolean, default=False)
    gst_category = Column(String(50))  # Agricultural, Processed, Industrial, Service
    is_processed = Column(Boolean, default=False)
    
    # Trading Parameters (stored as JSON arrays)
    trade_types = Column(JSON)  # [{"id": 1, "name": "Purchase"}, ...]
    bargain_types = Column(JSON)  # [{"id": 1, "name": "FOB"}, ...]
    varieties = Column(JSON)  # [{"id": 1, "name": "Shankar-6"}, ...]
    weightment_terms = Column(JSON)
    passing_terms = Column(JSON)
    delivery_terms = Column(JSON)  # Structured terms with days
    payment_terms = Column(JSON)  # Structured terms with days
    commissions = Column(JSON)  # Commission structures
    
    # Quality Parameters Configuration
    quality_parameters = Column(JSON)  # Array of parameter definitions
    certificates = Column(JSON)  # Array of available certificates ["NPOP", "Organic", ...]
    
    # CCI Support
    supports_cci_terms = Column(Boolean, default=False)  # Only for cotton
    
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)


# ============================================================================
# BUSINESS PARTNER MODULE
# ============================================================================

class BusinessPartner(Base, TimestampMixin):
    """Business partner (buyer/seller) master."""

    __tablename__ = "business_partners"

    id = Column(String(50), primary_key=True)  # UUID
    bp_code = Column(String(50), unique=True, nullable=False, index=True)
    legal_name = Column(String(255), nullable=False)
    business_type = Column(Enum('BUYER', 'SELLER', 'BOTH', 'AGENT', name='business_type'), nullable=False)
    status = Column(String(50), default='ACTIVE')
    
    # Contact Information
    contact_person = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    country = Column(String(100), default='India')
    
    # Legal Documents
    pan = Column(String(20), index=True)
    gstin = Column(String(50), index=True)
    
    # Banking
    bank_name = Column(String(255))
    bank_account_no = Column(String(50))
    bank_ifsc = Column(String(20))
    
    # Relationships
    addresses = relationship("Address", back_populates="business_partner")


class Address(Base, TimestampMixin):
    """Additional shipping/billing addresses for business partners."""

    __tablename__ = "addresses"

    id = Column(String(50), primary_key=True)  # UUID
    business_partner_id = Column(String(50), ForeignKey('business_partners.id'), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    country = Column(String(100), default='India')
    is_default = Column(Boolean, default=False)
    
    # Relationships
    business_partner = relationship("BusinessPartner", back_populates="addresses")


# ============================================================================
# FINANCIAL YEAR MODULE
# ============================================================================

class FinancialYear(Base, TimestampMixin):
    """Financial year (April-March for India)."""

    __tablename__ = "financial_years"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    year_code = Column(String(20), nullable=False, index=True)  # "2023-24"
    start_date = Column(DateTime, nullable=False)  # April 1
    end_date = Column(DateTime, nullable=False)  # March 31
    assessment_year = Column(String(20), nullable=False)  # "2024-25"
    is_active = Column(Boolean, default=False, index=True)
    is_closed = Column(Boolean, default=False, index=True)
    opening_balances = Column(JSON)
    
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
    """Year-end data transfer log."""

    __tablename__ = "year_end_transfers"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    from_financial_year_id = Column(Integer, ForeignKey('financial_years.id'), nullable=False)
    to_financial_year_id = Column(Integer, ForeignKey('financial_years.id'), nullable=False)
    transfer_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    transfer_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_count = Column(Integer, default=0)
    transfer_summary = Column(JSON)
    performed_by = Column(String(255), nullable=False)
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


# ============================================================================
# TRADE DESK MODULE (NEW)
# ============================================================================

class Trade(Base, TimestampMixin):
    """Trade request/demand from buyer."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(Enum('buy', 'sell', name='trade_action'), nullable=False)
    buyer_id = Column(String(50), ForeignKey('business_partners.id'), nullable=False, index=True)
    commodity_id = Column(Integer, ForeignKey('commodities.id'), nullable=False, index=True)
    
    # Quantity & Unit
    quantity = Column(Numeric(15, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    variety_id = Column(Integer)  # Reference to variety in commodity.varieties JSON
    
    # Quality Parameters (ranges)
    parameters = Column(JSON, nullable=False)  # {"staple_mm": {"min": 28, "max": 30}, ...}
    
    # Trading Terms
    trade_type_id = Column(Integer)
    bargain_type_id = Column(Integer)
    passing_id = Column(Integer)
    weightment_id = Column(Integer)
    delivery_term_id = Column(Integer)
    delivery_days = Column(Integer)
    payment_term_id = Column(Integer)
    payment_days = Column(Integer)
    
    # Location
    location_state_id = Column(Integer)
    location_region_id = Column(Integer)
    location_station_id = Column(Integer)
    
    # Certificates & Pricing
    certificates = Column(JSON)  # ["NPOP", "Organic", ...]
    target_price = Column(Numeric(15, 2))
    currency = Column(String(10), default='INR')
    price_unit = Column(String(50))  # per_candy, per_quintal, etc.
    
    # Additional Info
    notes = Column(Text)
    urgency = Column(Enum('normal', 'urgent', name='urgency_level'), default='normal')
    
    # Status & Lifecycle
    status = Column(
        Enum('DRAFT', 'POSTED', 'OFFERS_RECEIVED', 'NEGOTIATION', 'AGREED', 
             'CONTRACT_CREATED', 'COMPLETED', 'CANCELLED', 'EXPIRED', name='trade_status'),
        default='DRAFT',
        index=True
    )
    expires_at = Column(DateTime)
    assigned_to_user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    buyer = relationship("BusinessPartner", foreign_keys=[buyer_id])
    commodity = relationship("Commodity")
    offers = relationship("Offer", back_populates="trade")


class Offer(Base, TimestampMixin):
    """Seller offer for a trade."""

    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=False, index=True)
    seller_id = Column(String(50), ForeignKey('business_partners.id'), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    
    # Pricing
    price = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default='INR')
    price_unit = Column(String(50), nullable=False)
    
    # Quantity
    quantity = Column(Numeric(15, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    variety_id = Column(Integer)
    
    # Quality Parameters (actual values)
    parameters = Column(JSON, nullable=False)  # {"staple_mm": 29.0, "mic": 4.1, ...}
    
    # Test Report
    test_report_url = Column(String(500))
    test_report_date = Column(DateTime)
    tested_lot_id = Column(Integer, ForeignKey('tested_lots.id'))
    
    # Terms
    delivery_term_id = Column(Integer)
    payment_term_id = Column(Integer)
    
    # Validity
    valid_until = Column(DateTime, nullable=False)
    validity_hours = Column(Integer)
    
    # Match Score
    match_score = Column(Numeric(5, 2))  # 0-100
    match_breakdown = Column(JSON)  # {"parameterScore": 100, "priceScore": 98, ...}
    parameter_deviations = Column(JSON)  # Array of deviation details
    
    # Notes & Status
    notes = Column(Text)
    status = Column(
        Enum('PENDING', 'COUNTERED', 'ACCEPTED', 'REJECTED', 'EXPIRED', name='offer_status'),
        default='PENDING',
        index=True
    )
    negotiation_version = Column(Integer, default=1)
    
    # Relationships
    trade = relationship("Trade", back_populates="offers")
    seller = relationship("BusinessPartner", foreign_keys=[seller_id])
    station = relationship("Location")
    tested_lot = relationship("TestedLot")
    negotiations = relationship("Negotiation", back_populates="offer")


class TestedLot(Base, TimestampMixin):
    """Pre-tested commodity lot from seller."""

    __tablename__ = "tested_lots"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(String(50), ForeignKey('business_partners.id'), nullable=False, index=True)
    commodity_id = Column(Integer, ForeignKey('commodities.id'), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    
    # Quantity Management
    quantity = Column(Numeric(15, 2), nullable=False)
    quantity_available = Column(Numeric(15, 2), nullable=False)
    quantity_offered = Column(Numeric(15, 2), default=0)
    unit = Column(String(50), nullable=False)
    variety_id = Column(Integer)
    
    # Quality Parameters
    parameters = Column(JSON, nullable=False)
    
    # Test Report
    test_report_url = Column(String(500), nullable=False)
    test_report_date = Column(DateTime, nullable=False)
    testing_lab = Column(String(255))
    
    # Validity & Status
    valid_until = Column(DateTime, nullable=False)
    notes = Column(Text)
    status = Column(
        Enum('ACTIVE', 'EXPIRED', 'DEPLETED', name='tested_lot_status'),
        default='ACTIVE',
        index=True
    )
    
    # Matched Trades
    matched_trade_ids = Column(JSON)  # Array of trade IDs
    
    # Relationships
    seller = relationship("BusinessPartner")
    commodity = relationship("Commodity")
    station = relationship("Location")


class Negotiation(Base, TimestampMixin):
    """Negotiation history for an offer."""

    __tablename__ = "negotiations"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey('offers.id'), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    
    # Sender Info
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sender_role = Column(Enum('buyer', 'seller', name='negotiation_role'), nullable=False)
    
    # Counter Offer Terms
    new_price = Column(Numeric(15, 2))
    new_quantity = Column(Numeric(15, 2))
    new_valid_until = Column(DateTime)
    
    # Message
    message = Column(Text, nullable=False)
    
    # Relationships
    offer = relationship("Offer", back_populates="negotiations")
    sender = relationship("User")
