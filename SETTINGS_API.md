# Settings Module API Documentation

## Overview

The Settings Module provides a comprehensive RESTful API for managing all configuration data in the RNRL TradeHub application. All endpoints follow a standardized response format and provide full CRUD operations.

**Base URL:** `http://localhost:8080/api/settings`

## Response Format

All API responses follow this standard format:

### Success Response
```json
{
  "success": true,
  "data": <response_data>,
  "message": "Optional success message"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message"
  }
}
```

## Status Codes

- `200 OK` - Successful GET, PUT, DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Invalid input data
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate entry
- `500 Internal Server Error` - Server error

## API Endpoints

### 1. Organizations

Manage organization/company information.

#### GET /api/settings/organizations
List all organizations.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "RNRL Trading",
      "legalName": "RNRL Trading Company Pvt Ltd",
      "code": "AAACR5555K",
      "gstin": "27AAACR5555K1Z5",
      "pan": "AAACR5555K",
      "address": "123 Trade Center",
      "city": "Mumbai",
      "state": "Maharashtra",
      "pincode": "400069",
      "phone": "",
      "email": "",
      "isActive": true,
      "createdAt": "2025-11-10T13:36:06.719880",
      "updatedAt": "2025-11-10T13:36:06.719885"
    }
  ]
}
```

#### POST /api/settings/organizations
Create a new organization.

**Request Body:**
```json
{
  "name": "RNRL Delhi Office",
  "legalName": "RNRL Delhi Pvt Ltd",
  "pan": "AABCD1234E",
  "gstin": "07AABCD1234E1Z5",
  "address": "456 Corporate Avenue",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110001",
  "phone": "9876543211",
  "email": "delhi@rnrl.com",
  "isActive": true
}
```

#### PUT /api/settings/organizations/:id
Update an existing organization.

#### DELETE /api/settings/organizations/:id
Delete an organization.

---

### 2. Master Data

Generic CRUD for 7 types of master data.

**Supported Types:**
- `trade-types` - Trading types (Domestic, Export, etc.)
- `bargain-types` - Bargain types (Ex-Gin, Delivery, etc.)
- `varieties` - Cotton varieties (Shankar-6, MCU-5, etc.)
- `dispute-reasons` - Dispute reasons
- `weightment-terms` - Weightment terms
- `passing-terms` - Passing terms  
- `financial-years` - Financial year names

#### GET /api/settings/master-data/:type
List items of specified type.

**Example:** `GET /api/settings/master-data/varieties`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Shankar-6",
      "createdAt": "2025-11-10T13:36:07.504413"
    },
    {
      "id": 2,
      "name": "MCU-5",
      "createdAt": "2025-11-10T13:36:07.504417"
    }
  ]
}
```

#### POST /api/settings/master-data/:type
Create a new item.

**Request Body:**
```json
{
  "name": "DCH-32"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "DCH-32",
    "createdAt": "2025-11-10T13:36:51.839170"
  },
  "message": "Item created successfully"
}
```

#### PUT /api/settings/master-data/:type/:id
Update an item.

#### DELETE /api/settings/master-data/:type/:id
Delete an item.

---

### 3. GST Rates

Manage GST rate configurations.

#### GET /api/settings/gst-rates
List all GST rates.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "description": "Nil Rate",
      "hsnCode": "0000",
      "rate": 0.0,
      "createdAt": "2025-11-10T13:36:07.489572"
    },
    {
      "id": 2,
      "description": "5% GST",
      "hsnCode": "5201",
      "rate": 5.0,
      "createdAt": "2025-11-10T13:36:07.489576"
    }
  ]
}
```

#### POST /api/settings/gst-rates
Create a new GST rate.

**Request Body:**
```json
{
  "description": "Cotton Yarn",
  "hsnCode": "5205",
  "rate": 5.0
}
```

#### PUT /api/settings/gst-rates/:id
Update a GST rate.

#### DELETE /api/settings/gst-rates/:id
Delete a GST rate.

---

### 4. Locations

Manage location data (country, state, city).

#### GET /api/settings/locations
List all locations.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "country": "India",
      "state": "Maharashtra",
      "city": "Mumbai",
      "createdAt": "2025-11-10T13:36:07.492255"
    }
  ]
}
```

#### POST /api/settings/locations
Create a new location.

**Request Body:**
```json
{
  "country": "India",
  "state": "Gujarat",
  "city": "Surat"
}
```

#### DELETE /api/settings/locations/:id
Delete a location.

**Note:** No PUT endpoint for locations - recreate if needed.

---

### 5. Commission Structures

Manage commission calculation configurations.

#### GET /api/settings/commissions
List all commission structures.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Standard 2%",
      "type": "PERCENTAGE",
      "value": 2.0,
      "createdAt": "2025-11-10T13:36:07.494806"
    },
    {
      "id": 2,
      "name": "Fixed ₹50 per bale",
      "type": "PER_BALE",
      "value": 50.0,
      "createdAt": "2025-11-10T13:36:07.494812"
    }
  ]
}
```

#### POST /api/settings/commissions
Create a new commission structure.

**Request Body:**
```json
{
  "name": "Premium Commission",
  "type": "PERCENTAGE",
  "value": 3.5
}
```

**Validation:**
- `name`: Required, unique
- `type`: Required, must be "PERCENTAGE" or "PER_BALE"
- `value`: Required, positive number

#### PUT /api/settings/commissions/:id
Update a commission structure.

#### DELETE /api/settings/commissions/:id
Delete a commission structure.

---

### 6. CCI Terms

Manage CCI (Cotton Corporation of India) term configurations.

#### GET /api/settings/cci-terms
List all CCI terms.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Standard CCI Terms 2024",
      "contractPeriodDays": 90,
      "emdPaymentDays": 7,
      "cashDiscountPercentage": 2.0,
      "carryingChargeTier1Days": 30,
      "carryingChargeTier1Percent": 0.5,
      "carryingChargeTier2Days": 60,
      "carryingChargeTier2Percent": 1.0,
      "additionalDepositPercent": 10.0,
      "depositInterestPercent": 6.0,
      "freeLiftingPeriodDays": 15,
      "lateLiftingTier1Days": 30,
      "lateLiftingTier1Percent": 0.25,
      "lateLiftingTier2Days": 60,
      "lateLiftingTier2Percent": 0.5,
      "lateLiftingTier3Percent": 1.0,
      "createdAt": "2025-11-10T13:36:07.497556"
    }
  ]
}
```

#### POST /api/settings/cci-terms
Create a new CCI term configuration.

#### PUT /api/settings/cci-terms/:id
Update a CCI term.

#### DELETE /api/settings/cci-terms/:id
Delete a CCI term.

---

### 7. Delivery Terms

Manage delivery timeframe configurations.

#### GET /api/settings/delivery-terms
List all delivery terms.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Immediate",
      "days": 0,
      "createdAt": "2025-11-10T13:36:07.507451"
    },
    {
      "id": 2,
      "name": "7 Days",
      "days": 7,
      "createdAt": "2025-11-10T13:36:07.507453"
    }
  ]
}
```

#### POST /api/settings/delivery-terms
Create a new delivery term.

**Request Body:**
```json
{
  "name": "30 Days",
  "days": 30
}
```

#### PUT /api/settings/delivery-terms/:id
Update a delivery term.

#### DELETE /api/settings/delivery-terms/:id
Delete a delivery term.

---

### 8. Payment Terms

Manage payment timeframe configurations.

#### GET /api/settings/payment-terms
List all payment terms.

**Response:** Same structure as delivery terms.

#### POST /api/settings/payment-terms
Create a new payment term.

#### PUT /api/settings/payment-terms/:id
Update a payment term.

#### DELETE /api/settings/payment-terms/:id
Delete a payment term.

---

## Testing Examples

### Using curl

```bash
# List organizations
curl http://localhost:8080/api/settings/organizations

# Create a master data item
curl -X POST http://localhost:8080/api/settings/master-data/varieties \
  -H "Content-Type: application/json" \
  -d '{"name":"New Variety"}'

# Update a GST rate
curl -X PUT http://localhost:8080/api/settings/gst-rates/1 \
  -H "Content-Type: application/json" \
  -d '{"rate":6.0}'

# Delete a location
curl -X DELETE http://localhost:8080/api/settings/locations/1
```

### Using Python

```python
import requests

# GET request
response = requests.get('http://localhost:8080/api/settings/organizations')
data = response.json()
print(data)

# POST request
new_item = {"name": "Test Variety"}
response = requests.post(
    'http://localhost:8080/api/settings/master-data/varieties',
    json=new_item
)
print(response.json())
```

## Implementation Details

### Database Tables Used
- `organizations` - Organization data
- `master_data_items` - Generic master data with category field
- `gst_rates` - GST rate configurations
- `locations` - Location master data
- `commission_structures` - Commission configurations
- `cci_terms` - CCI term configurations
- `structured_terms` - Payment and delivery terms

### Business Logic
- **Duplicate Prevention:** Name uniqueness checked (case-insensitive)
- **Validation:** Required fields validated before save
- **Relationships:** Foreign key constraints maintained
- **Timestamps:** Automatic created_at/updated_at tracking

### Error Handling
- **404:** Resource not found
- **409:** Duplicate entry (unique constraint violation)
- **400:** Invalid input data

## Total Endpoints

- **Organizations:** 4 endpoints (GET, POST, PUT, DELETE)
- **Master Data (7 types):** 28 endpoints (4 each × 7 types)
- **GST Rates:** 4 endpoints
- **Locations:** 3 endpoints (no PUT)
- **Commissions:** 4 endpoints
- **CCI Terms:** 4 endpoints
- **Delivery Terms:** 4 endpoints
- **Payment Terms:** 4 endpoints

**Total: 55 endpoints** across 8 resource groups

## Next Steps

For production deployment:
1. Add JWT authentication middleware
2. Implement role-based authorization (Admin only)
3. Add input validation with Pydantic schemas
4. Add rate limiting
5. Add pagination for large datasets
6. Add search/filter capabilities
7. Add audit logging
8. Configure CORS for frontend domain
