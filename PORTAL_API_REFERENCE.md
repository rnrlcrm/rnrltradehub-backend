# Portal API Endpoints - Quick Reference

This document provides a quick reference for all portal-specific API endpoints.

## Authentication Endpoints

### POST `/api/auth/login`
Login and receive JWT token with portal information.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_type": "CLIENT",
  "portal_url": "/client/dashboard",
  "user_id": 1,
  "name": "John Doe",
  "email": "user@example.com"
}
```

### GET `/api/auth/me`
Get current user information.

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "user@example.com",
  "user_type": "CLIENT",
  "portal_url": "/client/dashboard",
  "is_parent": true,
  "business_partner_id": "bp-123",
  "organization_id": null,
  "parent_user_id": null,
  "is_active": true
}
```

### POST `/api/auth/change-password`
Change user password.

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

### POST `/api/auth/logout`
Logout (client removes token).

**Headers:** `Authorization: Bearer {token}`

---

## Client Portal Endpoints (`/api/client`)

All endpoints require `Authorization: Bearer {token}` and user_type must be `CLIENT`.

### GET `/api/client/my-contracts`
List contracts where user is the buyer.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

### GET `/api/client/my-contracts/{contract_id}`
Get detailed information about a specific contract.

### GET `/api/client/my-invoices`
List invoices for user's contracts.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

### GET `/api/client/my-payments`
List payments made by user.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)

### GET `/api/client/my-profile`
Get business partner profile.

### POST `/api/client/sub-users`
Create a sub-user (max 2 per parent).

**Request:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "password123"
}
```

### GET `/api/client/sub-users`
List all sub-users created by current user.

### DELETE `/api/client/sub-users/{sub_user_id}`
Delete a sub-user.

---

## Vendor Portal Endpoints (`/api/vendor`)

All endpoints require `Authorization: Bearer {token}` and user_type must be `VENDOR`.

### GET `/api/vendor/my-contracts`
List contracts where user is the seller.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

### GET `/api/vendor/my-contracts/{contract_id}`
Get detailed information about a specific contract.

### GET `/api/vendor/my-invoices`
List invoices for user's contracts.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

### GET `/api/vendor/my-payments`
List payments received by user.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)

### GET `/api/vendor/my-profile`
Get business partner profile.

### POST `/api/vendor/sub-users`
Create a sub-user (max 2 per parent).

**Request:**
```json
{
  "name": "John Smith",
  "email": "john@example.com",
  "password": "password123"
}
```

### GET `/api/vendor/sub-users`
List all sub-users created by current user.

### DELETE `/api/vendor/sub-users/{sub_user_id}`
Delete a sub-user.

---

## Back Office Portal Endpoints (`/api/back-office`)

All endpoints require `Authorization: Bearer {token}` and user_type must be `BACK_OFFICE`.

### GET `/api/back-office/business-partners`
List all business partners (full access).

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `business_type` (optional)
- `status` (optional)

### GET `/api/back-office/business-partners/{partner_id}`
Get a specific business partner.

### GET `/api/back-office/sales-contracts`
List all sales contracts (full access).

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

### GET `/api/back-office/sales-contracts/{contract_id}`
Get a specific sales contract.

### GET `/api/back-office/invoices`
List all invoices (full access).

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

### GET `/api/back-office/invoices/{invoice_id}`
Get a specific invoice.

### GET `/api/back-office/payments`
List all payments (full access).

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)

### GET `/api/back-office/payments/{payment_id}`
Get a specific payment.

### GET `/api/back-office/users`
List all users in the system.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `user_type` (optional)

### GET `/api/back-office/users/{user_id}`
Get a specific user.

### GET `/api/back-office/disputes`
List all disputes (full access).

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

### GET `/api/back-office/commissions`
List all commissions (full access).

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 100)
- `status` (optional)

---

## Access Control Rules

### Data Isolation

1. **BACK_OFFICE Users:**
   - Full access to all data
   - No restrictions based on business_partner_id

2. **CLIENT Users:**
   - Can ONLY access contracts where `client_id == business_partner_id`
   - Can ONLY access invoices/payments for their contracts
   - Cannot see vendor-specific data or other clients' data

3. **VENDOR Users:**
   - Can ONLY access contracts where `vendor_id == business_partner_id`
   - Can ONLY access invoices/payments for their contracts
   - Cannot see client-specific data or other vendors' data

### Sub-User Rules

- Each parent user (CLIENT or VENDOR) can create up to 2 sub-users
- Sub-users automatically inherit:
  - `user_type` from parent
  - `business_partner_id` from parent
  - Same access rights as parent
- Sub-users cannot create other sub-users
- Sub-users cannot view or manage other sub-users

### Authentication

All protected endpoints require:
1. Valid JWT token in Authorization header: `Authorization: Bearer {token}`
2. Active user account (`is_active = true`)
3. Appropriate user_type for the portal being accessed

---

## Error Responses

### 401 Unauthorized
Invalid or missing token, or token expired.

### 403 Forbidden
- User account is inactive
- User type doesn't match required portal
- Sub-user attempting forbidden action

### 404 Not Found
- Resource not found
- Resource exists but user doesn't have access to it

### 400 Bad Request
- Validation errors
- Sub-user limit exceeded (max 2)
- Current password incorrect (password change)

---

**Version:** 1.0  
**Last Updated:** 2025-11-10
