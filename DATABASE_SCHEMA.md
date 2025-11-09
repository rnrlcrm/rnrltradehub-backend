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

### Master Data Items (`master_data_items`)

Generic master data for various configurations.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `category` (VARCHAR(100)): Category (e.g., 'variety', 'quality_parameter')
- `name` (VARCHAR(255)): Item name
- `code` (VARCHAR(50)): Item code
- `description` (TEXT): Description
- `is_active` (BOOLEAN): Active status
- `metadata` (JSON): Additional flexible data
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Structured Terms (`structured_terms`)

Structured terms for payments, delivery, etc.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `category` (VARCHAR(100)): Term category (payment, delivery, passing, etc.)
- `name` (VARCHAR(255)): Term name
- `days` (INTEGER): Number of days
- `description` (TEXT): Description
- `is_active` (BOOLEAN): Active status
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Roles (`roles`)

User roles for RBAC.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `name` (VARCHAR(100), UNIQUE): Role name
- `description` (TEXT): Role description
- `is_active` (BOOLEAN): Active status
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

**Relationships:**
- One-to-many with `permissions`
- One-to-many with `users`

### Permissions (`permissions`)

Permissions for role-based access control.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `role_id` (INTEGER, FK): Reference to role
- `module` (VARCHAR(100)): Module name
- `can_create` (BOOLEAN): Create permission
- `can_read` (BOOLEAN): Read permission
- `can_update` (BOOLEAN): Update permission
- `can_delete` (BOOLEAN): Delete permission
- `can_approve` (BOOLEAN): Approval permission
- `can_share` (BOOLEAN): Share permission
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### Settings (`settings`)

System settings and configuration.

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `category` (VARCHAR(100)): Setting category
- `key` (VARCHAR(255), UNIQUE): Setting key
- `value` (TEXT): Setting value
- `value_type` (VARCHAR(50)): Value type (string, number, boolean, json)
- `description` (TEXT): Description
- `is_public` (BOOLEAN): Public visibility flag
- `is_editable` (BOOLEAN): Editability flag
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

## Updated Entity Relationship Diagram

```
roles
    |-- permissions (1:many)
    |-- users (1:many)

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

master_data_items
    - Generic configuration data

structured_terms
    - Payment/delivery term definitions

settings
    - System configuration
```

## Architecture Improvements

### TimestampMixin
All models now inherit from `TimestampMixin` which provides:
- `created_at` - Automatic timestamp on creation
- `updated_at` - Automatic timestamp on updates

This ensures consistent audit tracking across all tables.

### Flexible Schema
- `master_data_items.metadata` (JSON) - Store category-specific data
- `settings.value_type` - Support different data types
- `structured_terms` - Standardize common business terms

### Future Extensions
The schema is designed to support:
- Multi-tenancy (add `organization_id` to relevant tables)
- Soft deletes (add `deleted_at` timestamp)
- Versioning (already implemented for sales_contracts)
- Workflow/approval states
- Document attachments
- Activity logging beyond audit trail

## File Storage & Document Management

### Documents (`documents`)

Document/file storage with access control.

**Columns:**
- `id` (VARCHAR(36), PK): UUID
- `entity_type` (VARCHAR(100)): Related entity type
- `entity_id` (VARCHAR(36)): Related entity ID
- `document_type` (VARCHAR(100)): Document category (PAN, GST, Invoice, etc.)
- `file_name` (VARCHAR(500)): Original filename
- `file_size` (INTEGER): Size in bytes
- `file_type` (VARCHAR(100)): MIME type
- `storage_path` (VARCHAR(1000)): Cloud storage path
- `storage_url` (VARCHAR(1000)): Signed/public URL
- `uploaded_by` (INTEGER, FK): User who uploaded
- `description` (TEXT): Description
- `is_active` (BOOLEAN): Soft delete flag
- `is_public` (BOOLEAN): Public access flag
- `metadata` (JSON): Additional metadata
- `created_at`, `updated_at` (TIMESTAMP)

## Email System

### Email Templates (`email_templates`)

Templates for automated emails.

**Columns:**
- `id` (INTEGER, PK)
- `name` (VARCHAR(255), UNIQUE): Template name
- `category` (VARCHAR(100)): notification, alert, report
- `subject` (VARCHAR(500)): Email subject
- `body_html` (TEXT): HTML template
- `body_text` (TEXT): Plain text fallback
- `variables` (JSON): Template variables
- `is_active` (BOOLEAN)
- `description` (TEXT)
- `created_at`, `updated_at` (TIMESTAMP)

### Email Logs (`email_logs`)

Log of sent emails.

**Columns:**
- `id` (INTEGER, PK)
- `template_id` (INTEGER, FK)
- `recipient` (VARCHAR(500))
- `cc` (VARCHAR(1000))
- `bcc` (VARCHAR(1000))
- `subject` (VARCHAR(500))
- `body` (TEXT)
- `status` (ENUM): pending, sent, failed, bounced
- `sent_at` (TIMESTAMP)
- `error_message` (TEXT)
- `metadata` (JSON)
- `created_at`, `updated_at` (TIMESTAMP)

## Compliance & GDPR

### Data Retention Policies (`data_retention_policies`)

Retention policies per entity type.

**Columns:**
- `id` (INTEGER, PK)
- `entity_type` (VARCHAR(100), UNIQUE): Entity to apply policy to
- `retention_days` (INTEGER): Days to retain
- `archive_after_days` (INTEGER): When to archive
- `delete_after_days` (INTEGER): When to delete
- `policy_type` (VARCHAR(100)): legal, business, regulatory
- `description` (TEXT)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

### Data Access Logs (`data_access_logs`)

GDPR-compliant access logging.

**Columns:**
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK)
- `entity_type` (VARCHAR(100))
- `entity_id` (VARCHAR(100))
- `action` (VARCHAR(100)): view, export, modify, delete
- `ip_address` (VARCHAR(50))
- `user_agent` (VARCHAR(500))
- `accessed_at` (TIMESTAMP)
- `purpose` (TEXT): Why data was accessed
- `metadata` (JSON)
- `created_at`, `updated_at` (TIMESTAMP)

### Consent Records (`consent_records`)

User consent tracking (GDPR).

**Columns:**
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK)
- `business_partner_id` (VARCHAR(36), FK)
- `consent_type` (VARCHAR(100)): data_processing, marketing, third_party
- `consent_given` (BOOLEAN)
- `consent_date` (TIMESTAMP)
- `withdrawn_date` (TIMESTAMP)
- `ip_address` (VARCHAR(50))
- `metadata` (JSON)
- `created_at`, `updated_at` (TIMESTAMP)

### Data Export Requests (`data_export_requests`)

GDPR right to access/erasure.

**Columns:**
- `id` (VARCHAR(36), PK): UUID
- `user_id` (INTEGER, FK)
- `business_partner_id` (VARCHAR(36), FK)
- `request_type` (VARCHAR(100)): export, deletion
- `status` (ENUM): pending, processing, completed, failed
- `requested_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP)
- `export_file_path` (VARCHAR(1000))
- `metadata` (JSON)
- `created_at`, `updated_at` (TIMESTAMP)

## Security Management

### Security Events (`security_events`)

Security incident logging.

**Columns:**
- `id` (INTEGER, PK)
- `event_type` (VARCHAR(100)): login_failed, access_denied, suspicious_activity
- `severity` (ENUM): low, medium, high, critical
- `user_id` (INTEGER, FK)
- `ip_address` (VARCHAR(50))
- `user_agent` (VARCHAR(500))
- `description` (TEXT)
- `occurred_at` (TIMESTAMP)
- `resolved` (BOOLEAN)
- `resolved_at` (TIMESTAMP)
- `metadata` (JSON)
- `created_at`, `updated_at` (TIMESTAMP)

### System Configurations (`system_configurations`)

System-wide configuration.

**Columns:**
- `id` (INTEGER, PK)
- `config_key` (VARCHAR(255), UNIQUE)
- `config_value` (TEXT)
- `config_type` (VARCHAR(50)): string, json, encrypted
- `category` (VARCHAR(100)): storage, email, security, compliance
- `is_encrypted` (BOOLEAN)
- `is_sensitive` (BOOLEAN)
- `description` (TEXT)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

## Updated Table Count

**Total: 26 Tables**

Previously: 16 tables
**New additions: 10 tables**

1. documents
2. email_templates
3. email_logs
4. data_retention_policies
5. data_access_logs
6. consent_records
7. data_export_requests
8. security_events
9. system_configurations

## Compliance Features Summary

### GDPR Compliance
✅ Right to access (data export)
✅ Right to erasure (data deletion)
✅ Consent management
✅ Data access logging
✅ Data retention policies

### Security Features
✅ Security event logging
✅ Failed login tracking
✅ Access control logging
✅ Suspicious activity detection

### Audit Trail
✅ Timestamps on all tables (TimestampMixin)
✅ Dedicated audit_logs table
✅ Data access logs
✅ Security event logs
✅ Email logs
