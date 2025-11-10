# Multi-Tenant Access Control Specification

## Overview

This document specifies the multi-tenant (multi-organization) access control architecture for RNRL TradeHub Backend. The system supports multiple organizations using the same application instance with complete data isolation and organization-scoped access control.

## Architecture Principles

### 1. Data Isolation
- **Complete data separation** between organizations
- All business entities must be scoped to an organization
- No cross-organization data visibility (unless explicitly permitted for super-admin)
- Organization ID filtering applied at the database query level

### 2. Access Control Hierarchy
```
Super Admin (System-level)
    └── Organization Admin (Organization-level)
        └── Roles (Organization-scoped)
            └── Users (Organization-scoped)
                └── Permissions (Module/Action-level)
```

### 3. Security Requirements
- Users belong to exactly one organization
- Users can only access data from their organization
- Role-based permissions are organization-scoped
- API requests must include organization context
- Database queries must filter by organization_id

## Database Schema Changes

### Tables Requiring organization_id

#### Core Business Entities
1. **users** - User accounts scoped to organization
2. **business_partners** - Vendors, clients, agents per organization
3. **sales_contracts** - Sales contracts per organization
4. **addresses** - Shipping addresses (via business_partner)
5. **audit_logs** - Audit trail per organization
6. **documents** - File storage per organization

#### Configuration & Master Data (Organization-specific)
7. **cci_terms** - CCI configuration per organization
8. **commission_structures** - Commission templates per organization
9. **settings** - Settings per organization (optional global)
10. **master_data_items** - Master data per organization
11. **structured_terms** - Terms per organization

#### Already Have organization_id
- ✅ **invoices**
- ✅ **payments**
- ✅ **disputes**
- ✅ **commissions**
- ✅ **financial_years**
- ✅ **year_end_transfers**

#### Shared/Global Tables (No organization_id)
- **gst_rates** - Government-defined GST rates (shared)
- **locations** - Location master (shared)
- **roles** - Role definitions (can be shared or org-specific)
- **permissions** - Permission definitions (role-scoped)

#### System Tables (No organization_id)
- **organizations** - Organization registry
- **system_configurations** - Global system settings
- **email_templates** - Can be global or org-specific
- **email_logs** - Should have organization_id
- **data_retention_policies** - Should have organization_id
- **data_access_logs** - Should have organization_id
- **consent_records** - Should have organization_id
- **data_export_requests** - Should have organization_id
- **security_events** - Should have organization_id

## Implementation Requirements

### 1. Model Updates

#### Add organization_id to Models
```python
# Core business tables
users.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
business_partners.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
sales_contracts.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)

# Configuration tables
cci_terms.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)  # Nullable for global templates
commission_structures.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)
settings.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)
master_data_items.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
structured_terms.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)

# Compliance & audit tables
audit_logs.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
documents.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
email_logs.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
data_retention_policies.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)
data_access_logs.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
consent_records.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
data_export_requests.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
security_events.organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)
```

#### Add Relationships
```python
# In Organization model
users = relationship("User", back_populates="organization")
business_partners = relationship("BusinessPartner", back_populates="organization")
# ... other relationships

# In User model
organization = relationship("Organization", back_populates="users")

# In BusinessPartner model
organization = relationship("Organization", back_populates="business_partners")
```

### 2. API Context Management

#### Organization Context Dependency
Create a FastAPI dependency to extract and validate organization context:

```python
# dependencies.py
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

async def get_organization_context(
    x_organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db)
) -> int:
    """
    Extract and validate organization ID from request headers.
    
    Headers:
        X-Organization-ID: Organization identifier
        
    Returns:
        Validated organization ID
        
    Raises:
        HTTPException: If organization not found or inactive
    """
    from services.organization_service import OrganizationService
    
    if not OrganizationService.validate_organization_access(db, x_organization_id):
        raise HTTPException(status_code=403, detail="Invalid or inactive organization")
    
    return x_organization_id
```

#### User Authentication + Organization Context
```python
async def get_current_user(
    token: str = Header(..., alias="Authorization"),
    organization_id: int = Depends(get_organization_context),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Validate user token and ensure user belongs to the organization.
    
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If authentication fails or organization mismatch
    """
    # Decode token and get user
    user = authenticate_user(token, db)
    
    # Verify user belongs to the organization
    if user.organization_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="User does not belong to this organization"
        )
    
    return user
```

### 3. Route Handler Updates

All route handlers must:
1. Include organization context dependency
2. Filter queries by organization_id
3. Validate organization ownership on create/update

#### Example - List Endpoint
```python
@business_partner_router.get("/", response_model=List[schemas.BusinessPartnerResponse])
def list_business_partners(
    organization_id: int = Depends(get_organization_context),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List business partners for the organization."""
    query = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.organization_id == organization_id
    )
    return query.offset(skip).limit(limit).all()
```

#### Example - Create Endpoint
```python
@business_partner_router.post("/", response_model=schemas.BusinessPartnerResponse)
def create_business_partner(
    partner: schemas.BusinessPartnerCreate,
    organization_id: int = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    """Create a business partner in the organization."""
    db_partner = models.BusinessPartner(
        id=str(uuid.uuid4()),
        organization_id=organization_id,  # Always set from context
        **partner.model_dump()
    )
    db.add(db_partner)
    db.commit()
    return db_partner
```

#### Example - Get/Update/Delete Endpoints
```python
@business_partner_router.get("/{partner_id}")
def get_business_partner(
    partner_id: str,
    organization_id: int = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    """Get business partner, ensuring organization ownership."""
    partner = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.id == partner_id,
        models.BusinessPartner.organization_id == organization_id  # Organization check
    ).first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Business partner not found")
    
    return partner
```

### 4. Service Layer Updates

Services must accept and use organization_id for filtering:

```python
class BusinessPartnerService:
    @staticmethod
    def get_partner(db: Session, partner_id: str, organization_id: int):
        """Get partner ensuring organization ownership."""
        return db.query(models.BusinessPartner).filter(
            models.BusinessPartner.id == partner_id,
            models.BusinessPartner.organization_id == organization_id
        ).first()
    
    @staticmethod
    def list_partners(db: Session, organization_id: int, **filters):
        """List partners for organization."""
        query = db.query(models.BusinessPartner).filter(
            models.BusinessPartner.organization_id == organization_id
        )
        # Apply additional filters
        return query.all()
```

### 5. Permission Checks

Combine organization context with RBAC permissions:

```python
def check_permission(
    user: models.User,
    module: str,
    action: str,
    db: Session
) -> bool:
    """
    Check if user has permission for action on module.
    
    Args:
        user: Authenticated user
        module: Module name (e.g., 'business_partners')
        action: Action name (e.g., 'create', 'read', 'update', 'delete')
        db: Database session
        
    Returns:
        True if user has permission
    """
    if not user.role_id:
        return False
    
    permission = db.query(models.Permission).filter(
        models.Permission.role_id == user.role_id,
        models.Permission.module == module
    ).first()
    
    if not permission:
        return False
    
    action_map = {
        'create': permission.can_create,
        'read': permission.can_read,
        'update': permission.can_update,
        'delete': permission.can_delete,
        'approve': permission.can_approve,
        'share': permission.can_share
    }
    
    return action_map.get(action, False)
```

### 6. Migration Strategy

#### Phase 1: Add Columns (Non-Breaking)
1. Add organization_id columns as NULLABLE
2. Deploy schema changes
3. Backfill organization_id for existing data (all to default org)

#### Phase 2: Enforce Constraints
1. Make organization_id NOT NULL where appropriate
2. Add foreign key constraints
3. Add indexes on organization_id

#### Phase 3: Update Application Code
1. Update models with organization_id
2. Update route handlers with organization context
3. Update services with organization filtering
4. Add organization context dependency

#### Phase 4: Testing & Validation
1. Test data isolation between organizations
2. Test cross-organization access prevention
3. Test permission enforcement
4. Load testing with multiple organizations

## API Request Flow

### Headers Required
```
X-Organization-ID: 1
Authorization: Bearer <token>
```

### Request Flow
1. **Request arrives** with X-Organization-ID header
2. **Organization validation**: Check organization exists and is active
3. **User authentication**: Verify token and get user
4. **Organization membership**: Verify user.organization_id == X-Organization-ID
5. **Permission check**: Verify user has permission for the action
6. **Data access**: Filter query by organization_id
7. **Response**: Return organization-scoped data

### Error Cases
- **403 Forbidden**: Invalid organization, inactive organization, or organization mismatch
- **401 Unauthorized**: Invalid/missing token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found in user's organization

## Security Considerations

### 1. Data Leakage Prevention
- Always filter by organization_id in WHERE clauses
- Never expose organization_id in URLs (use headers)
- Validate organization ownership before any operation
- Use prepared statements to prevent SQL injection

### 2. Super Admin Access
- Super admins can access all organizations
- Require explicit super_admin flag on user
- Log all super admin actions
- Require MFA for super admin access

### 3. Audit Trail
- Log all cross-organization access attempts
- Track organization changes
- Monitor for data access anomalies
- Include organization_id in all audit logs

### 4. Rate Limiting
- Apply rate limits per organization
- Prevent one organization from affecting others
- Monitor resource usage per organization

## Testing Requirements

### 1. Unit Tests
- Test organization filtering in all queries
- Test organization validation
- Test permission checks
- Test cross-organization access prevention

### 2. Integration Tests
- Test complete request flow with organization context
- Test data isolation between organizations
- Test user switching organizations (should fail)
- Test super admin access

### 3. Security Tests
- Test SQL injection with organization_id
- Test unauthorized organization access
- Test token replay across organizations
- Test permission bypass attempts

## Configuration

### Environment Variables
```bash
# Enable multi-tenant mode
MULTI_TENANT_ENABLED=true

# Default organization for system users
DEFAULT_ORGANIZATION_ID=1

# Super admin email (can access all orgs)
SUPER_ADMIN_EMAIL=admin@rnrltradehub.com
```

### Organization Settings
Each organization can have custom settings:
```json
{
  "email_domain": "company.com",
  "logo_url": "https://...",
  "timezone": "Asia/Kolkata",
  "currency": "INR",
  "fiscal_year_start": "04-01",
  "features_enabled": ["invoices", "contracts", "disputes"],
  "integrations": {
    "email": {"provider": "smtp", "config": {...}},
    "storage": {"provider": "gcs", "bucket": "..."}
  }
}
```

## Migration Checklist

- [ ] Add organization_id to User model
- [ ] Add organization_id to BusinessPartner model
- [ ] Add organization_id to SalesContract model
- [ ] Add organization_id to configuration tables
- [ ] Add organization_id to compliance tables
- [ ] Add organization_id to audit tables
- [ ] Create organization context dependency
- [ ] Update all route handlers
- [ ] Update all service methods
- [ ] Create permission checking decorator
- [ ] Add integration tests
- [ ] Update API documentation
- [ ] Create organization admin guide
- [ ] Performance test with multiple organizations

## References

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Complete database schema
- [API_ENDPOINTS.md](API_ENDPOINTS.md) - API documentation
- [SERVICE_LAYER.md](SERVICE_LAYER.md) - Service layer architecture
- [COMPLIANCE.md](COMPLIANCE.md) - Compliance requirements

---

**Version**: 1.0  
**Status**: Specification  
**Last Updated**: 2025-11-10
