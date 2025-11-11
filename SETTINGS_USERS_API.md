# Settings/Users API Endpoints

This document describes the new settings/users API endpoints added to support user management in the frontend.

## Base URL
All endpoints are prefixed with: `/api/settings/users`

## Endpoints

### 1. List Users (GET)
**Endpoint:** `GET /api/settings/users`

**Description:** Retrieve a list of users with optional filtering.

**Query Parameters:**
- `userType` (optional): Filter by user type
  - Values: `primary`, `sub_user`
- `isActive` (optional): Filter by active status
  - Values: `true`, `false`
- `skip` (optional): Number of records to skip for pagination (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)

**Example Request:**
```bash
GET /api/settings/users?userType=primary&isActive=true
```

**Response:** Array of user objects
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "role_id": 1,
    "role_name": "Admin",
    "is_active": true,
    "user_type": "primary",
    "client_id": null,
    "vendor_id": null,
    "parent_user_id": null,
    "max_sub_users": 5,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

---

### 2. Create User (POST)
**Endpoint:** `POST /api/settings/users`

**Description:** Create a new user with multi-tenant support.

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "password": "SecurePassword123!",
  "role_id": 2,
  "user_type": "primary",
  "client_id": "uuid-string",
  "vendor_id": null,
  "parent_user_id": null,
  "max_sub_users": 10
}
```

**Required Fields:**
- `name`: User's full name
- `email`: Unique email address
- `password`: User's password (will be hashed)

**Optional Fields:**
- `role_id`: ID of the role to assign
- `user_type`: Type of user (`primary` or `sub_user`, default: `primary`)
- `client_id`: Associated client business partner ID
- `vendor_id`: Associated vendor business partner ID
- `parent_user_id`: Parent user ID (required for sub_users)
- `max_sub_users`: Maximum number of sub-users allowed (default: 5)

**Response:** Created user object (201 Created)
```json
{
  "id": 2,
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "role_id": 2,
  "role_name": "Sales",
  "is_active": true,
  "user_type": "primary",
  "client_id": "uuid-string",
  "vendor_id": null,
  "parent_user_id": null,
  "max_sub_users": 10,
  "created_at": "2024-01-02T00:00:00",
  "updated_at": "2024-01-02T00:00:00"
}
```

**Validation:**
- Email must be unique
- Role must exist if provided
- Parent user must exist for sub_users
- Sub-user limit is enforced on parent user

---

### 3. Update User (PUT)
**Endpoint:** `PUT /api/settings/users/{user_id}`

**Description:** Update an existing user's details.

**Path Parameters:**
- `user_id`: ID of the user to update

**Request Body:** (all fields optional)
```json
{
  "name": "Jane Smith Updated",
  "email": "jane.updated@example.com",
  "password": "NewPassword123!",
  "role_id": 3,
  "is_active": true,
  "user_type": "primary",
  "client_id": "new-uuid",
  "vendor_id": null,
  "max_sub_users": 15
}
```

**Response:** Updated user object (200 OK)

**Validation:**
- User must exist
- Email must be unique (if changed)
- Role must exist (if changed)
- Password is hashed if provided

---

### 4. Delete User (DELETE)
**Endpoint:** `DELETE /api/settings/users/{user_id}`

**Description:** Soft-delete a user by setting `is_active` to `false`.

**Path Parameters:**
- `user_id`: ID of the user to delete

**Response:** No content (204 No Content)

**Note:** This is a soft delete. The user record remains in the database but is marked as inactive.

---

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

### 400 Bad Request
- Duplicate email address
- Validation errors
- Sub-user limit exceeded

```json
{
  "detail": "User with email jane@example.com already exists"
}
```

### 404 Not Found
- User not found
- Role not found
- Parent user not found

```json
{
  "detail": "User with ID 999 not found"
}
```

---

## Multi-Tenant Features

The settings/users endpoints support multi-tenant user management:

1. **Primary Users:** Regular users with full access
2. **Sub-Users:** Users created under a parent user with limited scope
3. **Client/Vendor Association:** Users can be associated with business partners
4. **Sub-User Limits:** Parent users have configurable limits on sub-users

---

## Security

- All passwords are hashed using bcrypt before storage
- Passwords are never returned in API responses
- Email addresses must be unique across the system
- Proper validation is enforced at all levels

---

## Testing

Run the verification test to ensure all endpoints are correctly registered:

```bash
python test_settings_simple.py
```

This will verify:
- All required routes are registered
- Schemas are properly defined
- Query parameters are configured correctly
