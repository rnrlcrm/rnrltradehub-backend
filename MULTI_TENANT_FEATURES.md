# Multi-Tenant User Management Features

## Overview

This document describes the multi-tenant user management features added to the RNRL TradeHub backend.

## Database Schema Changes

### Users Table Updates

The `users` table has been enhanced with multi-tenant support:

**New Columns:**
- `client_id` (VARCHAR(36), FK to business_partners): Associates user with a specific client
- `vendor_id` (VARCHAR(36), FK to business_partners): Associates user with a specific vendor
- `parent_user_id` (INTEGER, FK to users): Links sub-users to their parent user
- `user_type` (ENUM: 'primary', 'sub_user'): Indicates if user is primary or sub-user
- `max_sub_users` (INTEGER, default 5): Maximum number of sub-users a primary user can create

**Relationships:**
- `parent_user`: Self-referential relationship for sub-users
- `sub_users`: Backref for accessing a user's sub-users
- `client`: Relationship to business_partners via client_id
- `vendor`: Relationship to business_partners via vendor_id

### User Audit Log Table

New table `user_audit_logs` for tracking all user activities:

**Columns:**
- `id` (INTEGER, PK): Auto-increment ID
- `user_id` (INTEGER, FK to users): User who performed the action
- `action` (VARCHAR(100)): Action type (login, logout, create, update, delete, etc.)
- `entity_type` (VARCHAR(100)): Type of entity affected (optional)
- `entity_id` (VARCHAR(100)): ID of entity affected (optional)
- `ip_address` (VARCHAR(50)): IP address of the request
- `user_agent` (VARCHAR(500)): User agent string
- `details` (JSON): Additional context/metadata
- `timestamp` (TIMESTAMP): When the action occurred
- `created_at`, `updated_at` (TIMESTAMP): Standard audit fields

## API Endpoints

### Authentication

#### POST /api/auth/login

Authenticate a user and receive a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "role_id": 1,
    "client_id": "client-uuid",
    "vendor_id": null,
    "user_type": "primary"
  }
}
```

**Features:**
- Returns JWT token valid for 30 minutes (configurable)
- Token includes user context (client_id, vendor_id, user_type) for authorization
- Logs successful and failed login attempts
- Multi-tenant aware: token contains tenant context

### Team Management

#### GET /api/users/my-team

List all sub-users for the authenticated user.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "role_id": 3,
    "is_active": true,
    "user_type": "sub_user",
    "parent_user_id": 1,
    "created_at": "2025-11-11T10:00:00",
    "updated_at": "2025-11-11T10:00:00"
  }
]
```

**Business Rules:**
- Only primary users can access this endpoint
- Returns only sub-users created by the authenticated user

#### POST /api/users/my-team

Create a new sub-user.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "temp_password_123",
  "role_id": 3
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "role_id": 3,
  "is_active": true,
  "user_type": "sub_user",
  "parent_user_id": 1,
  "created_at": "2025-11-11T10:00:00",
  "updated_at": "2025-11-11T10:00:00"
}
```

**Business Rules:**
- Only primary users can create sub-users
- Sub-user limit enforced (default: 5, configurable via `max_sub_users`)
- Sub-users automatically inherit `client_id` and `vendor_id` from parent
- Email uniqueness validated across all users
- Activity logged in audit log
- Invitation email sent to sub-user (TODO: integrate email service)

#### PUT /api/users/my-team/{sub_user_id}

Update a sub-user.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "password": "new_password_123",
  "role_id": 4,
  "is_active": false
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "role_id": 4,
  "is_active": false,
  "user_type": "sub_user",
  "parent_user_id": 1,
  "created_at": "2025-11-11T10:00:00",
  "updated_at": "2025-11-11T11:00:00"
}
```

**Business Rules:**
- Only primary users can update their sub-users
- Cannot change `client_id` or `vendor_id` (inherited from parent)
- All fields are optional
- Email uniqueness validated if changed
- Activity logged in audit log

#### DELETE /api/users/my-team/{sub_user_id}

Delete (deactivate) a sub-user.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
- Status: 204 No Content

**Business Rules:**
- Only primary users can delete their sub-users
- Soft delete: sets `is_active` to False
- Activity logged in audit log

#### GET /api/users/my-team/{sub_user_id}/activity

View activity logs for a sub-user.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 100): Maximum records to return

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 2,
    "action": "login",
    "entity_type": null,
    "entity_id": null,
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "details": {"success": true},
    "timestamp": "2025-11-11T10:30:00",
    "created_at": "2025-11-11T10:30:00",
    "updated_at": "2025-11-11T10:30:00"
  }
]
```

**Business Rules:**
- Only primary users can view their sub-users' activity
- Results ordered by timestamp (newest first)
- Pagination supported

## Security Features

### Multi-Tenant Data Filtering

The `middleware.py` module provides functions for filtering data by tenant:

**`filter_by_tenant(query, user, entity_class)`**
- Automatically filters query results based on user's `client_id` and `vendor_id`
- Applied to entities that support tenant fields
- Primary users without tenant restrictions see all data

**`check_tenant_permission(user, entity, action)`**
- Validates user has permission to access specific entity
- Checks `client_id` and `vendor_id` match
- Returns True/False for permission check

**`validate_tenant_access(user, entity, db)`**
- Wrapper that raises HTTPException if access denied
- Use in route handlers to enforce tenant isolation

### Permission Guards

**`@require_permission(module, action)`**
- Decorator to enforce role-based permissions
- Checks user's role permissions for specific module and action
- Raises 403 Forbidden if permission denied

**`@require_primary_user`**
- Decorator to ensure only primary users can access endpoint
- Used on team management endpoints

### Audit Logging

All user actions are logged via the `log_user_activity()` function:

```python
log_user_activity(
    db=db,
    user_id=current_user.id,
    action="create_sub_user",
    entity_type="user",
    entity_id=str(new_sub_user.id),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    details={"sub_user_email": sub_user_data.email}
)
```

**Logged Actions:**
- login, login_failed
- create_sub_user, update_sub_user, delete_sub_user
- All CRUD operations on entities
- Permission denials

## Email System

### Sub-User Invitation

When a sub-user is created, an invitation email is sent via `EmailService.send_sub_user_invitation()`:

**Email Content:**
- Welcome message
- Login credentials (email + temporary password)
- Link to login page
- Instructions to change password

**Email Template:** `sub_user_invitation`

### Password Reset

Password reset emails via `EmailService.send_password_reset()`:

**Email Content:**
- Password reset link with secure token
- Token expiration notice (24 hours)
- Security reminder

**Email Template:** `password_reset`

**Note:** Email sending is currently stubbed (TODO: integrate with SendGrid/SES/etc.)

## Configuration

Environment variables in `.env`:

```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/rnrltradehub

# Email (future)
# EMAIL_SERVICE=sendgrid
# EMAIL_API_KEY=your-api-key
```

## Usage Examples

### 1. Primary User Creates Sub-User

```bash
# Login as primary user
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "primary@example.com", "password": "password123"}'

# Response includes access_token
# TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Create sub-user
curl -X POST http://localhost:8080/api/users/my-team \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sub User",
    "email": "subuser@example.com",
    "password": "temp_pass_123",
    "role_id": 3
  }'
```

### 2. List Team Members

```bash
curl -X GET http://localhost:8080/api/users/my-team \
  -H "Authorization: Bearer $TOKEN"
```

### 3. View Sub-User Activity

```bash
curl -X GET http://localhost:8080/api/users/my-team/2/activity \
  -H "Authorization: Bearer $TOKEN"
```

## Migration Guide

### Updating Existing Users

Existing users in the database will need to be updated:

1. Set `user_type` to 'primary' for all existing users
2. Set `max_sub_users` to desired limit (default: 5)
3. Optionally associate users with `client_id` or `vendor_id`

```sql
-- Update all existing users to primary type
UPDATE users SET user_type = 'primary', max_sub_users = 5 
WHERE user_type IS NULL;

-- Associate user with client
UPDATE users SET client_id = 'client-uuid-here' 
WHERE email = 'client-user@example.com';
```

### Adding Indexes

For better performance, add indexes:

```sql
CREATE INDEX idx_users_client_id ON users(client_id);
CREATE INDEX idx_users_vendor_id ON users(vendor_id);
CREATE INDEX idx_users_parent_user_id ON users(parent_user_id);
CREATE INDEX idx_user_audit_logs_user_id ON user_audit_logs(user_id);
CREATE INDEX idx_user_audit_logs_timestamp ON user_audit_logs(timestamp);
```

## Testing

Run the test suite:

```bash
python test_multi_tenant.py
```

Tests cover:
- User creation with multi-tenant fields
- Sub-user creation and relationships
- User audit log creation
- Password hashing and verification

## Future Enhancements

1. **Email Integration**: Connect to SendGrid/SES for actual email delivery
2. **Password Reset Flow**: Complete password reset token generation and validation
3. **Sub-User Limits**: Make limits configurable per organization
4. **Activity Dashboard**: UI for viewing team activity
5. **Invitation Tokens**: Secure invitation links instead of passwords in emails
6. **Role Templates**: Predefined role sets for quick sub-user creation
7. **Bulk Operations**: Create/update multiple sub-users at once
8. **Export Activity**: Download activity logs as CSV/Excel

## Security Considerations

1. **JWT Secret**: Change `SECRET_KEY` in production to a strong random value
2. **Token Expiry**: Adjust `ACCESS_TOKEN_EXPIRE_MINUTES` based on security requirements
3. **Password Policy**: Enforce strong password requirements
4. **Email Security**: Use secure email templates, validate links
5. **Audit Retention**: Configure retention policy for audit logs
6. **Rate Limiting**: Add rate limiting to login endpoint to prevent brute force
7. **IP Whitelisting**: Consider IP restrictions for sensitive operations
