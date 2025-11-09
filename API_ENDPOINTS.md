# API Endpoints Documentation

## Overview

Complete RESTful API for RNRL TradeHub CRM system with full CRUD operations for all entities.

Base URL: `http://localhost:8080` (development)

API Documentation:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## Core Endpoints

### Health & Status
- `GET /` - API status message
- `GET /health` - Health check with database connectivity

## Business Partner Management

### Business Partners
- `POST /api/business-partners/` - Create business partner
- `GET /api/business-partners/` - List all (with filtering: `?business_type=BUYER&status=ACTIVE&search=term`)
- `GET /api/business-partners/{id}` - Get by ID
- `PUT /api/business-partners/{id}` - Update business partner
- `DELETE /api/business-partners/{id}` - Delete business partner

## Contract Management

### Sales Contracts
- `POST /api/sales-contracts/` - Create sales contract
- `GET /api/sales-contracts/` - List all
- `GET /api/sales-contracts/{id}` - Get by ID
- `PUT /api/sales-contracts/{id}` - Update contract
- `DELETE /api/sales-contracts/{id}` - Delete contract

### CCI Terms
- `POST /api/cci-terms/` - Create CCI term
- `GET /api/cci-terms/` - List all
- `GET /api/cci-terms/{id}` - Get by ID
- `PUT /api/cci-terms/{id}` - Update term
- `DELETE /api/cci-terms/{id}` - Delete term

## Financial Management

### Invoices
- `POST /api/invoices/` - Create invoice
- `GET /api/invoices/` - List all (filter: `?status=Paid`)
- `GET /api/invoices/{id}` - Get by ID
- `PUT /api/invoices/{id}` - Update invoice
- `DELETE /api/invoices/{id}` - Delete invoice

### Payments
- `POST /api/payments/` - Create payment
- `GET /api/payments/` - List all
- `GET /api/payments/{id}` - Get by ID
- `PUT /api/payments/{id}` - Update payment
- `DELETE /api/payments/{id}` - Delete payment

### Commissions
- `POST /api/commissions/` - Create commission
- `GET /api/commissions/` - List all (filter: `?status=Due`)
- `GET /api/commissions/{id}` - Get by ID
- `PUT /api/commissions/{id}` - Update commission
- `DELETE /api/commissions/{id}` - Delete commission

### Commission Structures
- `POST /api/commission-structures/` - Create structure
- `GET /api/commission-structures/` - List all
- `GET /api/commission-structures/{id}` - Get by ID
- `PUT /api/commission-structures/{id}` - Update structure

## Dispute Management

### Disputes
- `POST /api/disputes/` - Create dispute
- `GET /api/disputes/` - List all (filter: `?status=Open`)
- `GET /api/disputes/{id}` - Get by ID
- `PUT /api/disputes/{id}` - Update/resolve dispute
- `DELETE /api/disputes/{id}` - Delete dispute

## User & Access Management

### Users
- `POST /api/users/` - Create user
- `GET /api/users/` - List all users
- `GET /api/users/{id}` - Get by ID
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Roles & Permissions
- `POST /api/roles/` - Create role
- `GET /api/roles/` - List all roles
- `GET /api/roles/{id}` - Get role with permissions
- `PUT /api/roles/{id}` - Update role
- `DELETE /api/roles/{id}` - Delete role

## System Configuration

### Settings
- `POST /api/settings/` - Create setting
- `GET /api/settings/` - List all (filter: `?category=system`)
- `GET /api/settings/{key}` - Get by key
- `PUT /api/settings/{key}` - Update setting (if editable)

### Master Data
- `POST /api/master-data/` - Create master data item
- `GET /api/master-data/` - List all (filter: `?category=variety`)
- `GET /api/master-data/{id}` - Get by ID
- `PUT /api/master-data/{id}` - Update item

### GST Rates
- `POST /api/gst-rates/` - Create GST rate
- `GET /api/gst-rates/` - List all
- `GET /api/gst-rates/{id}` - Get by ID
- `PUT /api/gst-rates/{id}` - Update rate

### Locations
- `POST /api/locations/` - Create location
- `GET /api/locations/` - List all
- `GET /api/locations/{id}` - Get by ID
- `PUT /api/locations/{id}` - Update location

## Common Query Parameters

All list endpoints support:
- `skip` - Number of records to skip (pagination)
- `limit` - Maximum records to return (default: 100, max: 100)

Additional filters are available on specific endpoints as documented above.

## Response Codes

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid input data
- `404 Not Found` - Resource not found
- `403 Forbidden` - Action not allowed
- `500 Internal Server Error` - Server error

## Request/Response Format

All requests and responses use JSON format with proper content-type headers.

Example POST request:
```json
POST /api/business-partners/
Content-Type: application/json

{
  "bp_code": "BP001",
  "legal_name": "ABC Trading Co.",
  "business_type": "BUYER",
  ...
}
```

Example response:
```json
{
  "id": "uuid-here",
  "bp_code": "BP001",
  "legal_name": "ABC Trading Co.",
  "created_at": "2025-11-09T12:00:00",
  "updated_at": "2025-11-09T12:00:00",
  ...
}
```

## Authentication (Future)

Currently, all endpoints are public. Authentication and authorization will be implemented using:
- JWT tokens for session management
- Role-based access control (RBAC) using the roles and permissions tables
- API key authentication for service-to-service communication

## Rate Limiting (Future)

Rate limiting will be implemented to prevent abuse:
- Per-user limits: 1000 requests/hour
- Per-IP limits: 100 requests/minute
- Burst allowance: 20 requests/second
