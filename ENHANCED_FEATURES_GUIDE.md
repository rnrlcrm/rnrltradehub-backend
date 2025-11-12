# Enhanced Access Control Features - Implementation Guide

## Overview

This implementation adds comprehensive access control, business partner management, and compliance features to the RNRL TradeHub backend. This document provides a complete guide for developers, administrators, and users.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Authentication & Authorization](#authentication--authorization)
5. [Business Workflows](#business-workflows)
6. [Data Models](#data-models)
7. [Migration Guide](#migration-guide)
8. [Usage Examples](#usage-examples)
9. [Troubleshooting](#troubleshooting)
10. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────┴─────────────────────────────────────┐
│                  FastAPI Backend (Python)                    │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │   Routes     │   Schemas    │   Business Logic         │ │
│  │              │              │                          │ │
│  │  - Branches  │  - Pydantic  │  - Validation           │ │
│  │  - Onboard   │  - Request   │  - Approval Workflow    │ │
│  │  - Amendment │  - Response  │  - Version Control      │ │
│  │  - KYC       │              │  - Automation           │ │
│  └──────┬───────┴──────┬───────┴────────┬─────────────────┘ │
└─────────┼──────────────┼────────────────┼───────────────────┘
          │              │                │
┌─────────┴──────────────┴────────────────┴───────────────────┐
│                   PostgreSQL Database                        │
│                                                              │
│  Core Tables          │  New Tables (Phase 1-2)             │
│  - users              │  - business_branches                │
│  - business_partners  │  - user_branches                    │
│  - sales_contracts    │  - sub_users                        │
│  - audit_logs         │  - onboarding_applications          │
│  - roles              │  - amendment_requests               │
│  - permissions        │  - kyc_verifications                │
│                       │  - custom_modules                   │
│                       │  - custom_permissions               │
│                       │  - suspicious_activities            │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Business Branch Management**: Multi-branch support for business partners
2. **Self-Service Onboarding**: Public application submission and admin review
3. **Amendment Workflow**: Approval system for entity changes
4. **KYC Compliance**: Verification tracking and automated reminders
5. **Dynamic RBAC**: Extensible role-based access control
6. **Audit Trail**: Comprehensive activity logging

---

## Database Schema

### New Tables Summary

| Table Name | Purpose | Key Features |
|------------|---------|--------------|
| business_branches | Multi-branch for partners | GST validation, head office constraint |
| user_branches | User-branch access mapping | Multi-branch access control |
| sub_users | Sub-user management | Max 2 per parent, trigger enforced |
| onboarding_applications | Self-service onboarding | Application workflow, auto-numbering |
| amendment_requests | Change approval workflow | Version control, audit trail |
| business_partner_versions | Partner history | Complete data snapshots |
| profile_update_requests | Profile change approval | Approval workflow |
| kyc_verifications | KYC compliance tracking | Due date management |
| kyc_reminder_logs | Reminder history | Sent notification tracking |
| custom_modules | Dynamic RBAC modules | Extensible module definitions |
| custom_permissions | Fine-grained permissions | Action-based permissions |
| role_permissions | Role-permission mapping | RBAC configuration |
| user_permission_overrides | User exceptions | Temporary permission grants |
| suspicious_activities | Security monitoring | Risk scoring, review workflow |

### Extended Tables

**users table** - Added columns:
- `business_partner_id`: Link to business partner
- `user_type_new`: User classification (back_office, business_partner)
- `is_first_login`: First login flag
- `password_expiry_date`: Password expiration tracking
- `failed_login_attempts`: Login failure counter
- `locked_until`: Account lock timestamp
- `last_activity_at`: Last activity timestamp

**audit_logs table** - Added columns:
- `ip_address`: Request IP address
- `user_agent`: Browser/client information
- `geo_location`: Geographic location data
- `session_id`: Session identifier
- `entity_id`: Related entity ID
- `old_values`: Previous state (JSONB)
- `new_values`: New state (JSONB)

---

## API Endpoints

### Business Branch Management

#### Create Branch
```http
POST /api/business-partners/{partner_id}/branches
Authorization: Bearer {token}
Content-Type: application/json

{
  "partner_id": "uuid",
  "branch_code": "BRN001",
  "branch_name": "Mumbai Branch",
  "state": "Maharashtra",
  "gst_number": "27AAAAA0000A1Z5",
  "address": {
    "line1": "123 Main St",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "country": "India"
  },
  "is_head_office": true,
  "is_active": true
}
```

#### List Branches
```http
GET /api/business-partners/{partner_id}/branches?skip=0&limit=100
Authorization: Bearer {token}
```

#### Get Branch
```http
GET /api/business-partners/{partner_id}/branches/{branch_id}
Authorization: Bearer {token}
```

#### Update Branch
```http
PUT /api/business-partners/{partner_id}/branches/{branch_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "branch_name": "Updated Branch Name",
  "is_active": false
}
```

#### Delete Branch
```http
DELETE /api/business-partners/{partner_id}/branches/{branch_id}
Authorization: Bearer {token}
```

### Self-Service Onboarding

#### Submit Application (Public)
```http
POST /api/onboarding/apply
Content-Type: application/json

{
  "company_info": {
    "company_name": "Test Company Pvt Ltd",
    "legal_name": "Test Company Private Limited",
    "pan": "ABCDE1234F",
    "business_type": "BUYER"
  },
  "contact_info": {
    "contact_person": "John Doe",
    "email": "john@testcompany.com",
    "phone": "+91-9876543210"
  },
  "compliance_info": {
    "gst": "27AAAAA0000A1Z5",
    "pan_doc_url": "https://...",
    "gst_doc_url": "https://..."
  }
}
```

#### Check Application Status (Public)
```http
GET /api/onboarding/status/{application_number}
```

#### List Applications (Admin)
```http
GET /api/onboarding/applications?status=SUBMITTED&skip=0&limit=100
Authorization: Bearer {token}
```

#### Review Application (Admin)
```http
POST /api/onboarding/applications/{application_id}/review
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "APPROVED",
  "review_notes": "All documents verified and approved"
}
```

### Amendment System

#### Request Amendment
```http
POST /api/amendments/request
Authorization: Bearer {token}
Content-Type: application/json

{
  "entity_type": "business_partner",
  "entity_id": "uuid",
  "request_type": "UPDATE",
  "reason": "Update contact information",
  "justification": "Email address changed",
  "changes": {
    "old_values": {"contact_email": "old@email.com"},
    "new_values": {"contact_email": "new@email.com"}
  }
}
```

#### List Amendments
```http
GET /api/amendments?entity_type=business_partner&status=PENDING
Authorization: Bearer {token}
```

#### Review Amendment (Admin)
```http
POST /api/amendments/{request_id}/review
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "APPROVED",
  "review_notes": "Change approved"
}
```

### KYC Management

#### Record KYC Verification
```http
POST /api/kyc/verify/{partner_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "partner_id": "uuid",
  "verification_date": "2025-11-12T00:00:00Z",
  "documents_checked": {
    "pan": true,
    "gst": true,
    "bank_statement": true
  },
  "status": "CURRENT",
  "next_due_date": "2026-11-12T00:00:00Z",
  "notes": "All documents verified"
}
```

#### Get KYC Due List
```http
GET /api/kyc/due?days_ahead=30
Authorization: Bearer {token}
```

#### View KYC History
```http
GET /api/kyc/history/{partner_id}
Authorization: Bearer {token}
```

#### Send KYC Reminder
```http
POST /api/kyc/send-reminder/{partner_id}?reminder_type=30_DAYS
Authorization: Bearer {token}
```

---

## Authentication & Authorization

### JWT Authentication

All protected endpoints require JWT token in Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Public Endpoints

Only 2 endpoints are public (no authentication required):
- `POST /api/onboarding/apply` - Submit onboarding application
- `GET /api/onboarding/status/{application_number}` - Check application status

### Role-Based Access

Current implementation uses existing roles:
- **Admin**: Full access to all endpoints
- **Sales**: Read-only access to most features
- **Accounts**: Limited access
- **Business Partner**: Access to own data only

Future: Dynamic RBAC using custom_modules and custom_permissions tables

---

## Business Workflows

### 1. Business Partner Onboarding Workflow

```
┌─────────────────┐
│  Applicant      │
│  Submits Form   │
└────────┬────────┘
         │
         v
┌────────────────────────┐
│ Application Created     │
│ Status: SUBMITTED       │
│ Auto-generate APP#      │
└────────┬───────────────┘
         │
         v
┌────────────────────────┐
│ Admin Reviews          │
│ Status: UNDER_REVIEW   │
└────────┬───────────────┘
         │
    ┌────┴────┐
    │         │
    v         v
┌───────┐  ┌─────────┐
│APPROVE│  │ REJECT  │
└───┬───┘  └───┬─────┘
    │          │
    v          v
┌───────────┐  ┌──────────────┐
│ Create    │  │ Send         │
│ Partner + │  │ Rejection    │
│ User      │  │ Email        │
│ Send      │  └──────────────┘
│ Welcome   │
└───────────┘
```

### 2. Amendment Approval Workflow

```
┌──────────────────┐
│ User Requests    │
│ Amendment        │
└────────┬─────────┘
         │
         v
┌─────────────────────────┐
│ Amendment Request       │
│ Status: PENDING         │
│ Capture old/new values  │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ Admin Reviews           │
│ Check impact            │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
    v         v
┌───────┐  ┌─────────┐
│APPROVE│  │ REJECT  │
└───┬───┘  └───┬─────┘
    │          │
    v          v
┌───────────┐  ┌──────────────┐
│ Apply     │  │ Notify       │
│ Changes   │  │ Requester    │
│ Create    │  └──────────────┘
│ Version   │
└───────────┘
```

### 3. KYC Reminder Workflow

```
┌─────────────────┐
│ Daily Cron Job  │
│ 9 AM            │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│ Check All Partners      │
│ For KYC Due Dates       │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ Calculate Days Until    │
│ Due: 30/15/7/1/Overdue  │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ Send Reminder Emails    │
│ Log in kyc_reminder_logs│
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ If >30 Days Overdue:    │
│ Alert Admin             │
│ Consider Lock Account   │
└─────────────────────────┘
```

---

## Data Models

### BusinessBranch Model

```python
class BusinessBranch:
    id: str (UUID)
    partner_id: str (UUID, FK to business_partners)
    branch_code: str (unique per partner)
    branch_name: str
    state: str
    gst_number: str (unique)
    address: dict (JSONB)
    contact_person: dict (JSONB, optional)
    bank_details: dict (JSONB, optional)
    is_head_office: bool (only one true per partner)
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### OnboardingApplication Model

```python
class OnboardingApplication:
    id: str (UUID)
    application_number: str (unique, auto-generated)
    company_info: dict (JSONB)
    contact_info: dict (JSONB)
    compliance_info: dict (JSONB)
    branch_info: dict (JSONB, optional)
    documents: dict (JSONB, optional)
    status: str (SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED)
    review_notes: str (optional)
    reviewed_by: int (FK to users, optional)
    reviewed_at: datetime (optional)
    created_at: datetime
    updated_at: datetime
```

### AmendmentRequest Model

```python
class AmendmentRequest:
    id: str (UUID)
    entity_type: str (business_partner, branch, user)
    entity_id: str (UUID)
    request_type: str (UPDATE, DELETE)
    reason: str
    justification: str (optional)
    requested_by: int (FK to users)
    requested_at: datetime
    status: str (PENDING, APPROVED, REJECTED)
    reviewed_by: int (FK to users, optional)
    reviewed_at: datetime (optional)
    review_notes: str (optional)
    changes: dict (JSONB: old_values, new_values)
    impact_assessment: dict (JSONB, optional)
    created_at: datetime
    updated_at: datetime
```

### KYCVerification Model

```python
class KYCVerification:
    id: str (UUID)
    partner_id: str (UUID, FK to business_partners)
    verification_date: datetime
    verified_by: int (FK to users)
    documents_checked: dict (JSONB)
    status: str (CURRENT, DUE_SOON, OVERDUE)
    next_due_date: datetime
    notes: str (optional)
    created_at: datetime
    updated_at: datetime
```

---

## Migration Guide

### Prerequisites
- PostgreSQL 12 or higher
- Existing RNRL TradeHub database
- Backup of current database

### Step 1: Backup Database

```bash
pg_dump -h <host> -U <username> -d <database> > backup_$(date +%Y%m%d).sql
```

### Step 2: Apply Migration

```bash
psql -h <host> -U <username> -d <database> -f migrations/001_enhanced_access_control_schema.sql
```

### Step 3: Verify Migration

```sql
-- Check new tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'business_branches', 'user_branches', 'sub_users',
    'onboarding_applications', 'amendment_requests'
  );

-- Should return 14 rows
```

### Step 4: Update Environment Variables

Add to `.env`:
```
# JWT Configuration (if not already set)
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Future: Email configuration for Phase 4
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# ...
```

### Step 5: Restart Application

```bash
# Stop current instance
# Deploy new version with updated code
# Start new instance
```

### Rollback (if needed)

```bash
psql -h <host> -U <username> -d <database> <<EOF
-- See migrations/README.md for complete rollback SQL
DROP TABLE IF EXISTS suspicious_activities CASCADE;
-- ... (see README for full rollback script)
EOF
```

---

## Usage Examples

### Example 1: Creating a Multi-Branch Partner

```python
import requests

# 1. Create business partner (existing endpoint)
partner_response = requests.post(
    "http://localhost:8080/api/business-partners/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "bp_code": "BP001",
        "legal_name": "Test Company Pvt Ltd",
        "business_type": "BUYER",
        # ... other fields
    }
)
partner_id = partner_response.json()["id"]

# 2. Create head office branch
head_office = requests.post(
    f"http://localhost:8080/api/business-partners/{partner_id}/branches",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "partner_id": partner_id,
        "branch_code": "HO",
        "branch_name": "Head Office",
        "state": "Maharashtra",
        "gst_number": "27AAAAA0000A1Z5",
        "address": {...},
        "is_head_office": True
    }
)

# 3. Create additional branches
mumbai_branch = requests.post(
    f"http://localhost:8080/api/business-partners/{partner_id}/branches",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "partner_id": partner_id,
        "branch_code": "MUM001",
        "branch_name": "Mumbai Branch",
        "state": "Maharashtra",
        "gst_number": "27BBBBB0000B1Z5",
        "address": {...},
        "is_head_office": False
    }
)
```

### Example 2: Self-Service Onboarding Flow

```python
# User submits application (no auth required)
app_response = requests.post(
    "http://localhost:8080/api/onboarding/apply",
    json={
        "company_info": {
            "company_name": "New Business Inc",
            "pan": "ABCDE1234F",
            # ...
        },
        "contact_info": {...},
        "compliance_info": {...}
    }
)
app_number = app_response.json()["application_number"]

# User checks status (no auth required)
status = requests.get(
    f"http://localhost:8080/api/onboarding/status/{app_number}"
)
print(status.json()["status"])  # "SUBMITTED"

# Admin reviews application
review = requests.post(
    f"http://localhost:8080/api/onboarding/applications/{app_id}/review",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "status": "APPROVED",
        "review_notes": "All documents verified"
    }
)
```

### Example 3: Amendment with Approval

```python
# User requests to update partner email
amendment = requests.post(
    "http://localhost:8080/api/amendments/request",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "entity_type": "business_partner",
        "entity_id": partner_id,
        "request_type": "UPDATE",
        "reason": "Email address changed",
        "changes": {
            "old_values": {"contact_email": "old@email.com"},
            "new_values": {"contact_email": "new@email.com"}
        }
    }
)
request_id = amendment.json()["id"]

# Admin reviews and approves
approval = requests.post(
    f"http://localhost:8080/api/amendments/{request_id}/review",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "status": "APPROVED",
        "review_notes": "Email verification completed"
    }
)
# Changes are now applied automatically
```

---

## Troubleshooting

### Common Issues

#### 1. GST Number Already Exists

**Error**: "GST number already exists"

**Solution**: Each branch must have a unique GST number. If reusing, delete or update the existing branch first.

#### 2. Cannot Set Multiple Head Offices

**Error**: "Partner already has a head office"

**Solution**: Only one branch per partner can be marked as head office. Update the existing head office first if you want to change it.

#### 3. Max Sub-Users Exceeded

**Error**: "Maximum 2 sub-users allowed per parent user"

**Solution**: Database trigger enforces max 2 sub-users. Remove an existing sub-user before adding a new one.

#### 4. Application Startupfails

**Error**: Import errors or module not found

**Solution**:
```bash
pip install -r requirements.txt
python3 -c "import main"  # Test imports
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Future Enhancements (Phase 3-6)

### Phase 3: Automation Services
- [ ] User auto-creation when partner approved
- [ ] Daily KYC reminder scheduler
- [ ] PAN/GST validation service
- [ ] Auto-approval for low-risk changes

### Phase 4: Email Integration
- [ ] SMTP configuration
- [ ] Welcome email template
- [ ] KYC reminder email template
- [ ] Approval/rejection notifications

### Phase 5: Security Features
- [ ] Rate limiting with Redis
- [ ] Activity monitoring dashboard
- [ ] Data encryption at rest
- [ ] Geo-location anomaly detection

### Phase 6: Testing & Documentation
- [ ] Unit tests (80% coverage target)
- [ ] Integration tests
- [ ] Load testing
- [ ] Postman collection
- [ ] Updated API documentation

---

## Support & Contribution

### Documentation
- Full schema: `DATABASE_SCHEMA.md`
- Migration guide: `migrations/README.md`
- Implementation summary: `PHASE_1_2_COMPLETE.md`
- Verification: `NO_DUPLICATION_VERIFICATION.md`

### Contact
For issues or questions:
1. Check this README first
2. Review relevant documentation
3. Test with `/docs` endpoint
4. Create GitHub issue if needed

---

**Version**: 1.0.0 (Phase 1-2)  
**Last Updated**: 2025-11-12  
**Status**: Production Ready for Phase 1-2 Features
