# Database Schema Documentation

## Overview

The RNRL TradeHub backend uses PostgreSQL with SQLAlchemy ORM. The schema is designed to match the frontend TypeScript interfaces exactly, ensuring seamless integration.

## Tables

### Business Partners (`business_partners`)

Stores information about vendors, clients, and agents.

**Columns:**
- `id` (VARCHAR(36), PK): Unique identifier (UUID)
- `bp_code` (VARCHAR(50), UNIQUE): Business partner code
- `legal_name` (VARCHAR(255)): Legal business name
- `organization` (VARCHAR(255)): Organization name
- `business_type` (ENUM): BUYER, SELLER, BOTH, AGENT
- `status` (ENUM): DRAFT, PENDING_COMPLIANCE, ACTIVE, INACTIVE, BLACKLISTED
- `kyc_due_date` (TIMESTAMP): KYC renewal due date
- `contact_person` (VARCHAR(255)): Contact person name
- `contact_email` (VARCHAR(255)): Contact email
- `contact_phone` (VARCHAR(50)): Contact phone
- `address_line1` (VARCHAR(255)): Registered address line 1
- `address_line2` (VARCHAR(255)): Registered address line 2
- `city` (VARCHAR(100)): City
- `state` (VARCHAR(100)): State
- `pincode` (VARCHAR(20)): PIN/ZIP code
- `country` (VARCHAR(100)): Country
- `pan` (VARCHAR(50)): PAN number
- `gstin` (VARCHAR(50)): GST identification number
- `bank_name` (VARCHAR(255)): Bank name
- `bank_account_no` (VARCHAR(50)): Bank account number
- `bank_ifsc` (VARCHAR(50)): IFSC code
- `pan_doc_url` (VARCHAR(500)): PAN document URL
- `gst_doc_url` (VARCHAR(500)): GST document URL
- `cheque_doc_url` (VARCHAR(500)): Cancelled cheque URL
- `compliance_notes` (TEXT): Internal compliance notes
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

**Relationships:**
- One-to-many with `addresses` (shipping addresses)
- Referenced by `sales_contracts` (as client, vendor, or agent)

### Addresses (`addresses`)

Shipping addresses for business partners.

**Columns:**
- `id` (VARCHAR(36), PK): Unique identifier (UUID)
- `business_partner_id` (VARCHAR(36), FK): Reference to business partner
- `address_line1` (VARCHAR(255)): Address line 1
- `address_line2` (VARCHAR(255)): Address line 2
- `city` (VARCHAR(100)): City
- `state` (VARCHAR(100)): State
- `pincode` (VARCHAR(20)): PIN/ZIP code
- `country` (VARCHAR(100)): Country
- `is_default` (BOOLEAN): Default shipping address flag
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Sales Contracts (`sales_contracts`)

Main contract management table.

**Columns:**
- `id` (VARCHAR(36), PK): Unique identifier (UUID)
- `sc_no` (VARCHAR(50), UNIQUE): Sales contract number
- `version` (INTEGER): Contract version (for amendments)
- `amendment_reason` (TEXT): Reason for amendment
- `date` (TIMESTAMP): Contract date
- `organization` (VARCHAR(255)): Organization name
- `financial_year` (VARCHAR(20)): Financial year
- `client_id` (VARCHAR(36), FK): Reference to buyer
- `client_name` (VARCHAR(255)): Buyer name (denormalized)
- `vendor_id` (VARCHAR(36), FK): Reference to seller
- `vendor_name` (VARCHAR(255)): Seller name (denormalized)
- `agent_id` (VARCHAR(36), FK): Reference to agent (optional)
- `variety` (VARCHAR(255)): Product variety
- `quantity_bales` (INTEGER): Quantity in bales
- `rate` (FLOAT): Rate per unit
- `gst_rate_id` (INTEGER, FK): GST rate reference
- `buyer_commission_id` (INTEGER, FK): Buyer commission structure
- `seller_commission_id` (INTEGER, FK): Seller commission structure
- `buyer_commission_gst_id` (INTEGER, FK): Buyer commission GST
- `seller_commission_gst_id` (INTEGER, FK): Seller commission GST
- `trade_type` (VARCHAR(100)): Trade type
- `bargain_type` (VARCHAR(100)): Bargain type
- `weightment_terms` (VARCHAR(255)): Weightment terms
- `passing_terms` (VARCHAR(255)): Passing terms
- `delivery_terms` (VARCHAR(255)): Delivery terms
- `payment_terms` (VARCHAR(255)): Payment terms
- `location` (VARCHAR(255)): Delivery location
- `quality_specs` (JSON): Quality specifications (length, mic, rd, etc.)
- `manual_terms` (TEXT): Additional manual terms
- `status` (ENUM): Active, Completed, Disputed, Carried Forward, Amended, Pending Approval, Rejected
- `cci_contract_no` (VARCHAR(100)): CCI contract number
- `cci_term_id` (INTEGER, FK): Reference to CCI terms
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### CCI Terms (`cci_terms`)

Cotton Corporation of India terms configuration.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `name` (VARCHAR(255)): Term name
- `contract_period_days` (INTEGER): Contract period in days
- `emd_payment_days` (INTEGER): EMD payment days
- `cash_discount_percentage` (FLOAT): Cash discount percentage
- `carrying_charge_tier1_days` (INTEGER): Tier 1 carrying charge days
- `carrying_charge_tier1_percent` (FLOAT): Tier 1 carrying charge percentage
- `carrying_charge_tier2_days` (INTEGER): Tier 2 carrying charge days
- `carrying_charge_tier2_percent` (FLOAT): Tier 2 carrying charge percentage
- `additional_deposit_percent` (FLOAT): Additional deposit percentage
- `deposit_interest_percent` (FLOAT): Deposit interest percentage
- `free_lifting_period_days` (INTEGER): Free lifting period
- `late_lifting_tier1_days` (INTEGER): Late lifting tier 1 days
- `late_lifting_tier1_percent` (FLOAT): Late lifting tier 1 penalty
- `late_lifting_tier2_days` (INTEGER): Late lifting tier 2 days
- `late_lifting_tier2_percent` (FLOAT): Late lifting tier 2 penalty
- `late_lifting_tier3_percent` (FLOAT): Late lifting tier 3 penalty
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Commission Structures (`commission_structures`)

Commission configuration.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `name` (VARCHAR(255)): Commission structure name
- `type` (ENUM): PERCENTAGE, PER_BALE
- `value` (FLOAT): Commission value
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### GST Rates (`gst_rates`)

GST rate configuration.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `rate` (FLOAT): GST rate percentage
- `description` (VARCHAR(255)): Description
- `hsn_code` (VARCHAR(50)): HSN code
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Locations (`locations`)

Location master data.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `country` (VARCHAR(100)): Country
- `state` (VARCHAR(100)): State
- `city` (VARCHAR(100)): City
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Users (`users`)

User authentication and authorization.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `name` (VARCHAR(255)): User name
- `email` (VARCHAR(255), UNIQUE): Email address
- `password_hash` (VARCHAR(255)): Bcrypt password hash
- `role` (ENUM): Admin, Sales, Accounts, Dispute Manager, Vendor/Client
- `is_active` (BOOLEAN): Account active status
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Invoices (`invoices`)

Invoice tracking.

**Columns:**
- `id` (VARCHAR(36), PK): Unique identifier (UUID)
- `invoice_no` (VARCHAR(50), UNIQUE): Invoice number
- `sales_contract_id` (VARCHAR(36), FK): Reference to sales contract
- `date` (TIMESTAMP): Invoice date
- `amount` (FLOAT): Invoice amount
- `status` (ENUM): Unpaid, Partially Paid, Paid
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Payments (`payments`)

Payment tracking.

**Columns:**
- `id` (VARCHAR(36), PK): Unique identifier (UUID)
- `payment_id` (VARCHAR(50), UNIQUE): Payment ID
- `invoice_id` (VARCHAR(36), FK): Reference to invoice
- `date` (TIMESTAMP): Payment date
- `amount` (FLOAT): Payment amount
- `method` (ENUM): Bank Transfer, Cheque, Cash
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Disputes (`disputes`)

Dispute management.

**Columns:**
- `id` (VARCHAR(36), PK): Unique identifier (UUID)
- `dispute_id` (VARCHAR(50), UNIQUE): Dispute ID
- `sales_contract_id` (VARCHAR(36), FK): Reference to sales contract
- `reason` (TEXT): Dispute reason
- `status` (ENUM): Open, Resolved, Closed
- `resolution` (TEXT): Resolution details
- `date_raised` (TIMESTAMP): Date dispute was raised
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Commissions (`commissions`)

Commission tracking.

**Columns:**
- `id` (VARCHAR(36), PK): Unique identifier (UUID)
- `commission_id` (VARCHAR(50), UNIQUE): Commission ID
- `sales_contract_id` (VARCHAR(36), FK): Reference to sales contract
- `agent` (VARCHAR(255)): Agent name
- `amount` (FLOAT): Commission amount
- `status` (ENUM): Due, Paid
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Audit Logs (`audit_logs`)

Complete audit trail.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `timestamp` (TIMESTAMP): Event timestamp
- `user` (VARCHAR(255)): User who performed action
- `role` (ENUM): User role at time of action
- `module` (VARCHAR(100)): Module/entity affected
- `action` (VARCHAR(100)): Action performed
- `details` (TEXT): Action details
- `reason` (TEXT): Reason for action
- `created_at` (TIMESTAMP): Record creation timestamp

## Entity Relationship Diagram

```
business_partners
    |-- addresses (1:many)
    |-- sales_contracts as client (1:many)
    |-- sales_contracts as vendor (1:many)
    |-- sales_contracts as agent (1:many)

sales_contracts
    |-- invoices (1:many)
    |-- disputes (1:many)
    |-- commissions (1:many)
    |-- references cci_terms
    |-- references gst_rates
    |-- references commission_structures

invoices
    |-- payments (1:many)
```

## Indexes

- Primary keys on all tables
- Unique constraints on codes/numbers (bp_code, sc_no, invoice_no, etc.)
- Foreign key indexes for relationships
- Email index on users table
- Timestamp index on audit_logs

## Notes

- All tables include `created_at` and `updated_at` timestamps
- UUIDs (VARCHAR(36)) used for transaction tables (contracts, invoices, etc.)
- Auto-increment integers used for configuration tables (users, rates, etc.)
- JSON column for quality_specs allows flexible schema
- Enums ensure data integrity for status fields
- Password hashing uses bcrypt
- Cascading deletes configured for dependent records (e.g., addresses)
