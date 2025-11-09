# Service Layer Architecture

## Overview

The service layer provides a clean separation between business logic and API route handlers. This architecture ensures:

- **Maintainability**: Business logic is centralized and reusable
- **Testability**: Services can be unit tested independently
- **Scalability**: Easy to add new business rules
- **Separation of Concerns**: Routes handle HTTP, services handle business logic

## Architecture

```
┌─────────────────┐
│   Route Layer   │  ← HTTP Request/Response handling
│  (routes_*.py)  │  ← Validation of HTTP inputs
└────────┬────────┘  ← Exception handling
         │
         ▼
┌─────────────────┐
│  Service Layer  │  ← Business logic
│  (services/)    │  ← Data validation
└────────┬────────┘  ← Business rules enforcement
         │
         ▼
┌─────────────────┐
│   Data Layer    │  ← Database operations
│   (models.py)   │  ← ORM models
└─────────────────┘
```

## Service Modules

### 1. BusinessPartnerService

**Location**: `services/business_partner_service.py`

**Business Logic Implemented**:

1. **BP Code Uniqueness Validation**
   - Ensures no duplicate BP codes across all partners
   - Validates on create and update operations
   
2. **Status Management**
   - Valid statuses: active, inactive, suspended, pending
   - Validates status transitions
   
3. **Active Contract Checking**
   - Prevents deletion of partners with active contracts
   - Counts active contracts before deletion
   
4. **Search and Filtering**
   - Search across legal name and BP code
   - Filter by business type and status
   
5. **Relationship Management**
   - Creates associated shipping addresses
   - Ensures proper foreign key relationships

**Example Usage**:
```python
from services import BusinessPartnerService

# Create partner with validation
partner = BusinessPartnerService.create_business_partner(db, partner_data)

# Get partners with filtering
partners = BusinessPartnerService.get_business_partners(
    db, business_type="vendor", status_filter="active"
)
```

### 2. SalesContractService

**Location**: `services/sales_contract_service.py`

**Business Logic Implemented**:

1. **Contract Number Generation**
   - Auto-generates unique contract numbers: SC-YYYY-NNNN
   - Year-based sequencing
   
2. **Contract Status Workflow**
   - Valid statuses: draft → active → completed/cancelled/amended
   - Validates status transitions
   
3. **Business Partner Validation**
   - Checks partner exists
   - Ensures partner is active before creating contract
   
4. **Date Validation**
   - End date must be after start date
   - Cannot invoice expired contracts
   
5. **Amendment Management**
   - Increments version number on amendments
   - Changes status to "amended"
   
6. **Cancellation Logic**
   - Cannot cancel if pending invoices exist
   - Only draft or active contracts can be cancelled

**Example Business Rules**:
```python
from services import SalesContractService

# Create contract with validation
contract = SalesContractService.create_sales_contract(db, contract_data)

# Cancel contract (checks for pending invoices)
cancelled = SalesContractService.cancel_sales_contract(db, contract_id, "reason")
```

### 3. FinancialService

**Location**: `services/financial_service.py`

**Business Logic Implemented**:

1. **Invoice Number Generation**
   - Auto-generates unique invoice numbers: INV-YYYY-NNNN
   - Year-based sequencing
   
2. **Contract Validation for Invoicing**
   - Contract must exist
   - Contract must be active or amended
   - Contract must not be expired
   
3. **Invoice Total Calculations**
   - Base amount = quantity × rate
   - GST amount = base amount × gst_rate
   - Total amount = base amount + gst_amount
   
4. **Payment Processing**
   - Updates invoice paid amount
   - Auto-updates invoice status (paid/partially_paid)
   - Prevents payment to cancelled invoices
   
5. **Commission Calculations**
   - Applies percentage or fixed rate commissions
   - Retrieves commission structure from contract
   - Calculates based on invoice amount
   
6. **Outstanding Balance Calculation**
   - Total invoice amount - total paid amount
   - Tracks all payments for an invoice

**Example Business Rules**:
```python
from services import FinancialService

# Create invoice with validation
invoice = FinancialService.create_invoice(db, invoice_data)

# Create payment (auto-updates invoice status)
payment = FinancialService.create_payment(db, payment_data)

# Calculate commission
commission_amount = FinancialService.calculate_commission(db, contract_id, invoice_amount)
```

### 4. UserService

**Location**: `services/user_service.py`

**Business Logic Implemented**:

1. **Email Uniqueness Validation**
   - Ensures unique email addresses
   - Validates on create and update
   
2. **Password Security**
   - Bcrypt password hashing
   - Password verification for authentication
   
3. **Role Validation**
   - Validates role exists before assignment
   - Checks role permissions
   
4. **User Authentication**
   - Email and password validation
   - Checks user active status
   - Returns user only if active
   
5. **Permission Checking**
   - Checks module-level permissions
   - Actions: create, read, update, delete, approve, share
   - Role-based access control
   
6. **User Deactivation**
   - Sets status to inactive
   - Prevents login after deactivation

**Example Business Rules**:
```python
from services import UserService

# Create user with hashed password
user = UserService.create_user(db, user_data)

# Authenticate user
authenticated_user = UserService.authenticate_user(db, email, password)

# Check permission
has_permission = UserService.check_permission(db, user_id, "invoices", "create")
```

### 5. ComplianceService

**Location**: `services/compliance_service.py`

**Business Logic Implemented**:

1. **GDPR Data Export**
   - Collects all user data across tables
   - Prevents duplicate pending requests
   - Sets completion and expiry dates
   
2. **GDPR Data Deletion**
   - Validates user exists
   - Checks for active data preventing deletion
   - Creates deletion request workflow
   
3. **Consent Management**
   - Records user consent with purpose
   - Withdrawal workflow
   - Prevents re-withdrawal
   
4. **Data Access Logging**
   - Article 30 compliance
   - Tracks who accessed what data
   - Records access purpose
   
5. **Retention Policy Application**
   - Auto-deletes/archives old data
   - Based on entity type and retention period
   - Calculates cutoff dates
   
6. **Security Event Management**
   - Logs security incidents
   - Severity tracking (low/medium/high/critical)
   - Resolution workflow

**Example Business Rules**:
```python
from services import ComplianceService

# Create data export request
export_req = ComplianceService.create_data_export_request(db, export_data)

# Process export (collects all user data)
user_data = ComplianceService.process_data_export(db, request_id)

# Withdraw consent
withdrawn = ComplianceService.withdraw_consent(db, consent_id)

# Apply retention policies
results = ComplianceService.apply_retention_policies(db)
```

## Business Logic Examples

### Trade Logic (Example)

```python
# Example: If trade is not paid, cannot close contract
def close_trade_contract(db: Session, contract_id: str):
    """Close a trade contract."""
    # Business Logic: Get contract
    contract = SalesContractService.get_sales_contract_by_id(db, contract_id)
    
    # Business Logic: Check if all invoices are paid
    unpaid_invoices = db.query(models.Invoice).filter(
        models.Invoice.sales_contract_id == contract_id,
        models.Invoice.status.in_(["draft", "pending", "partially_paid", "overdue"])
    ).count()
    
    if unpaid_invoices > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot close contract with {unpaid_invoices} unpaid invoices"
        )
    
    # Business Logic: Update contract status
    contract.status = "completed"
    db.commit()
    return contract
```

### Payment Validation Logic (Example)

```python
# Example: If payment amount exceeds outstanding balance, reject
def validate_payment_amount(db: Session, invoice_id: str, payment_amount: Decimal):
    """Validate payment amount doesn't exceed outstanding balance."""
    # Business Logic: Get outstanding balance
    outstanding = FinancialService.get_outstanding_balance(db, invoice_id)
    
    if payment_amount > outstanding:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount ({payment_amount}) exceeds outstanding balance ({outstanding})"
        )
    
    return True
```

## Benefits of Service Layer

### 1. Centralized Business Logic

All business rules are in one place, making it easy to:
- Update business logic without touching routes
- Ensure consistency across different endpoints
- Document business rules alongside code

### 2. Reusability

Services can be called from:
- API routes
- Background tasks
- Scheduled jobs
- Other services

### 3. Testability

Services can be unit tested independently:
```python
def test_create_business_partner():
    """Test business partner creation logic."""
    partner_data = BusinessPartnerCreate(...)
    partner = BusinessPartnerService.create_business_partner(db, partner_data)
    assert partner.bp_code == partner_data.bp_code
```

### 4. Maintainability

When business rules change:
- Update only the service method
- All routes using that service automatically get the new logic
- No duplication of validation code

## Integration with Routes

Routes should be thin wrappers that:
1. Accept HTTP requests
2. Call service methods
3. Return HTTP responses

**Example Route Integration**:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services import BusinessPartnerService
import schemas

router = APIRouter()

@router.post("/", response_model=schemas.BusinessPartnerResponse)
def create_business_partner(
    partner: schemas.BusinessPartnerCreate,
    db: Session = Depends(get_db)
):
    """Create a new business partner."""
    # Route only handles HTTP - business logic is in service
    return BusinessPartnerService.create_business_partner(db, partner)

@router.get("/", response_model=List[schemas.BusinessPartnerResponse])
def list_business_partners(
    skip: int = 0,
    limit: int = 100,
    business_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List business partners with filtering."""
    # Service handles all filtering logic
    return BusinessPartnerService.get_business_partners(
        db, skip, limit, business_type, status
    )
```

## Future Enhancements

The service layer can be extended to include:

1. **Notification Service**: Email/SMS notifications
2. **Workflow Service**: Multi-step approval workflows
3. **Integration Service**: External API integrations
4. **Reporting Service**: Report generation logic
5. **Caching Service**: Performance optimization
6. **Event Service**: Event-driven architecture

## Summary

The service layer provides:

✅ **Clear separation** of HTTP handling and business logic
✅ **Centralized validation** and business rules
✅ **Reusable** business logic across the application
✅ **Testable** independent service methods
✅ **Maintainable** codebase for evolving business requirements
✅ **Documented** business logic for team understanding

All business logic is now properly separated, documented, and ready for future enhancements as the ERP system evolves.
