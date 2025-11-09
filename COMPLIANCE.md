# Compliance & Security Documentation

## Overview

The RNRL TradeHub backend is designed with comprehensive compliance and security features suitable for enterprise and regulated environments.

## GDPR Compliance

### Right to Access
Users and business partners can request access to their data.

**Implementation:**
- `data_export_requests` table tracks export requests
- API endpoint: `POST /api/data-export-requests/`
- Status tracking: pending → processing → completed
- Automated data compilation
- Secure file delivery

**Example:**
```json
POST /api/data-export-requests/
{
  "user_id": 123,
  "request_type": "export"
}
```

### Right to Erasure (Right to be Forgotten)
Users can request deletion of their personal data.

**Implementation:**
- `data_export_requests` table with `request_type: deletion`
- Soft delete mechanism on all entities
- Cascade deletion rules
- Retention policy compliance
- Audit trail of deletions

### Consent Management
Track and manage user consent for data processing.

**Implementation:**
- `consent_records` table
- Consent types: data_processing, marketing, third_party
- Consent given/withdrawn tracking
- IP address logging
- Timestamp tracking

**Consent Types:**
- `data_processing`: Core business operations
- `marketing`: Marketing communications
- `third_party`: Third-party data sharing

### Data Access Logging
Track who accesses what data and when (Article 30 GDPR).

**Implementation:**
- `data_access_logs` table
- Logs: view, export, modify, delete actions
- Tracks: user_id, entity_type, entity_id, timestamp
- IP address and user agent logging
- Purpose tracking

**Example Usage:**
```python
# Log when viewing sensitive data
POST /api/access-logs/
{
  "user_id": 123,
  "entity_type": "business_partner",
  "entity_id": "bp-456",
  "action": "view",
  "purpose": "Contract review",
  "ip_address": "192.168.1.1"
}
```

## Data Retention Policies

### Policy Management
Configure retention periods per entity type.

**Implementation:**
- `data_retention_policies` table
- Per-entity retention rules
- Archive and delete timelines
- Policy types: legal, business, regulatory

**Example Policy:**
```json
{
  "entity_type": "sales_contract",
  "retention_days": 2555,  // 7 years
  "archive_after_days": 1825,  // 5 years
  "delete_after_days": 2555,
  "policy_type": "legal",
  "description": "Legal requirement for contract retention"
}
```

### Automatic Data Lifecycle
- **Active**: Data in primary storage
- **Archived**: Moved to cold storage after archive_after_days
- **Deleted**: Permanently removed after delete_after_days

## Security Features

### Security Event Logging
Track security-related events and incidents.

**Implementation:**
- `security_events` table
- Event types: login_failed, access_denied, suspicious_activity
- Severity levels: low, medium, high, critical
- Incident resolution tracking

**Event Types:**
- `login_failed`: Failed login attempts
- `access_denied`: Permission violations
- `suspicious_activity`: Unusual patterns
- `data_breach_attempt`: Security breach attempts
- `unauthorized_access`: Access without proper auth

**Severity Levels:**
- `low`: Minor issues, informational
- `medium`: Potential security concerns
- `high`: Active security threats
- `critical`: Active breaches or critical issues

### Password Security
- **Bcrypt hashing**: Industry-standard password hashing
- **Salt rounds**: Configurable work factor
- **No plaintext storage**: Never store passwords in plain text

### SQL Injection Protection
- **SQLAlchemy ORM**: Parameterized queries
- **Input validation**: Pydantic schemas
- **Type checking**: Strong typing

### Access Control
- **RBAC**: Role-based access control
- **Granular permissions**: Module-level permissions
- **Permission types**: create, read, update, delete, approve, share

## File Storage & Document Management

### Document Security
**Implementation:**
- `documents` table
- Access control per document
- Cloud storage integration (GCS/S3)
- Signed URLs for secure access
- Upload tracking (who uploaded, when)

### Supported Storage
- Google Cloud Storage (GCS)
- Amazon S3
- Azure Blob Storage

### Access Control
- `is_public`: Public vs private documents
- `uploaded_by`: Track uploader
- Entity-level permissions
- URL expiration (signed URLs)

## Email System

### Email Tracking
**Implementation:**
- `email_logs` table
- Status tracking: pending, sent, failed, bounced
- Error logging
- Template usage tracking

### Email Security
- Template validation
- Anti-spam compliance
- Bounce handling
- Unsubscribe management

## System Configuration

### Encryption Configuration
**Implementation:**
- `system_configurations` table
- `is_encrypted` flag for sensitive configs
- `is_sensitive` flag for access control
- Category-based organization

### Configuration Categories
- `storage`: File storage settings
- `email`: Email service configuration
- `security`: Security parameters
- `compliance`: Compliance settings

## Audit Trail

### Comprehensive Logging
Every table includes automatic audit fields via TimestampMixin:
- `created_at`: When record was created
- `updated_at`: When record was last modified

### Dedicated Audit Log
`audit_logs` table for tracking:
- Who made the change
- What was changed
- When it was changed
- Why it was changed (reason field)

### Access Logging
`data_access_logs` tracks all data access for compliance.

## Data Protection

### Encryption at Rest
Configure via `system_configurations`:
```json
{
  "config_key": "encryption.enabled",
  "config_value": "true",
  "category": "security",
  "is_encrypted": false
}
```

### Encryption in Transit
- HTTPS/TLS for all communications
- Secure database connections
- Encrypted backup transmission

### Data Minimization
- Only collect necessary data
- JSON metadata fields for optional data
- Flexible schema for minimal required fields

## Compliance Reporting

### Available Reports
1. **Data Access Report**: Who accessed what data
2. **Consent Report**: Consent status by user
3. **Retention Report**: Data age and retention status
4. **Security Report**: Security events by severity
5. **Export Request Report**: GDPR request status

### Generating Reports
Use API filters to generate compliance reports:

```bash
# Security events in last 30 days
GET /api/security-events/?severity=high&resolved=false

# Data access for specific user
GET /api/access-logs/?user_id=123

# Pending export requests
GET /api/data-export-requests/?status=pending
```

## Best Practices

### For Administrators
1. ✅ Configure retention policies for all entity types
2. ✅ Monitor security events regularly
3. ✅ Review access logs for sensitive data
4. ✅ Process export/deletion requests within 30 days
5. ✅ Maintain consent records
6. ✅ Enable encryption for sensitive configurations

### For Developers
1. ✅ Log all data access using access logs
2. ✅ Use proper error handling
3. ✅ Validate all inputs
4. ✅ Follow principle of least privilege
5. ✅ Document security decisions
6. ✅ Keep dependencies updated

### For Users
1. ✅ Use strong passwords
2. ✅ Review consent settings
3. ✅ Request data export if needed
4. ✅ Report security incidents

## Incident Response

### Security Event Workflow
1. Event logged in `security_events`
2. Severity assessed automatically
3. High/Critical events trigger alerts
4. Investigation and resolution
5. Mark as resolved with notes

### Data Breach Protocol
1. Log event immediately
2. Assess scope and impact
3. Notify affected parties (GDPR: 72 hours)
4. Document in security events
5. Implement corrective measures

## Regulatory Compliance

### Supported Regulations
- ✅ **GDPR**: EU General Data Protection Regulation
- ✅ **Data Protection**: General data protection best practices
- ✅ **Audit Requirements**: Complete audit trail
- ✅ **Record Retention**: Configurable retention policies

### Future Compliance (Extensible)
- CCPA (California Consumer Privacy Act)
- HIPAA (Healthcare)
- SOC 2
- ISO 27001

## API Security

### Authentication (To be implemented)
- JWT tokens
- API keys
- OAuth 2.0

### Rate Limiting (To be implemented)
- Per-user limits
- Per-IP limits
- Burst protection

### Input Validation
- ✅ Pydantic schemas
- ✅ Type checking
- ✅ Length limits
- ✅ Format validation

## Monitoring & Alerts

### Security Monitoring
Monitor these tables regularly:
- `security_events`: Security incidents
- `data_access_logs`: Unusual access patterns
- `email_logs`: Failed email deliveries
- `audit_logs`: System changes

### Alert Triggers
Set up alerts for:
- Critical security events
- Failed login attempts > threshold
- Unresolved high-severity events
- Pending export requests > 30 days
- Data retention policy violations

## Conclusion

The RNRL TradeHub backend provides enterprise-grade compliance and security features out of the box. All major compliance requirements (GDPR, audit trail, data retention) are implemented and ready for production use.

For questions or additional compliance requirements, refer to the API documentation or contact the development team.
