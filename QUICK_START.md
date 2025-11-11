# Quick Start Guide - Settings/Users API

This guide shows how to quickly test the settings/users API endpoints.

## Prerequisites Check

Before starting the server, verify everything is configured correctly:

```bash
# Run startup verification
python verify_startup.py
```

This will check:
- ✓ All required packages are installed
- ✓ FastAPI application can be imported
- ✓ All critical endpoints are registered
- ✓ Database configuration is valid

## Starting the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

The server will start on port 8080 by default.

## API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

## Testing with curl

### 1. Create a User

```bash
curl -X POST "http://localhost:8080/api/settings/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "user_type": "primary",
    "max_sub_users": 10
  }'
```

### 2. List All Users

```bash
curl -X GET "http://localhost:8080/api/settings/users"
```

### 3. List Users with Filters

```bash
# Get only active primary users
curl -X GET "http://localhost:8080/api/settings/users?userType=primary&isActive=true"

# Get only sub-users
curl -X GET "http://localhost:8080/api/settings/users?userType=sub_user"

# Get inactive users
curl -X GET "http://localhost:8080/api/settings/users?isActive=false"
```

### 4. Update a User

```bash
curl -X PUT "http://localhost:8080/api/settings/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe Updated",
    "max_sub_users": 15
  }'
```

### 5. Delete (Deactivate) a User

```bash
curl -X DELETE "http://localhost:8080/api/settings/users/1"
```

## Testing with Python

```python
import requests

BASE_URL = "http://localhost:8080/api/settings/users"

# Create a user
response = requests.post(BASE_URL, json={
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "password": "SecurePass123!",
    "user_type": "primary"
})
print(f"Created user: {response.json()}")

# List users
response = requests.get(BASE_URL)
users = response.json()
print(f"Total users: {len(users)}")

# List filtered users
response = requests.get(f"{BASE_URL}?userType=primary&isActive=true")
active_users = response.json()
print(f"Active primary users: {len(active_users)}")

# Update user
user_id = users[0]["id"]
response = requests.put(f"{BASE_URL}/{user_id}", json={
    "name": "Updated Name"
})
print(f"Updated user: {response.json()}")

# Delete user
response = requests.delete(f"{BASE_URL}/{user_id}")
print(f"Delete status: {response.status_code}")
```

## Verification Test

Run the automated test to verify all endpoints are working:

```bash
python test_settings_simple.py
```

Expected output:
```
============================================================
✅ ALL TESTS PASSED - ENDPOINTS ARE READY!
============================================================

The following endpoints are now available:
  GET    /api/settings/users?userType=&isActive=
  POST   /api/settings/users
  PUT    /api/settings/users/:id
  DELETE /api/settings/users/:id
============================================================
```

## Frontend Integration

### JavaScript/TypeScript Example

```typescript
// API base URL
const API_BASE = 'http://localhost:8080/api/settings/users';

// Create user
async function createUser(userData) {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  return response.json();
}

// Get users with filters
async function getUsers(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

// Update user
async function updateUser(userId, updates) {
  const response = await fetch(`${API_BASE}/${userId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });
  return response.json();
}

// Delete user
async function deleteUser(userId) {
  const response = await fetch(`${API_BASE}/${userId}`, {
    method: 'DELETE'
  });
  return response.ok;
}

// Usage examples
const newUser = await createUser({
  name: 'Test User',
  email: 'test@example.com',
  password: 'SecurePass123!',
  user_type: 'primary'
});

const activeUsers = await getUsers({ isActive: 'true' });
const primaryUsers = await getUsers({ userType: 'primary' });
```

## Environment Variables

Required environment variables for database connection:

```bash
# PostgreSQL (production)
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password

# Or use DATABASE_URL
DATABASE_URL=postgresql://user:password@host:port/dbname
```

## Troubleshooting

### Database Connection Issues
If you get database errors, ensure:
1. PostgreSQL is running
2. Database credentials are correct in `.env` file
3. Database tables are created (run migrations if needed)

### Import Errors
If you get import errors:
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use
If port 8080 is already in use:
```bash
# Use a different port
PORT=8081 python main.py
```

## Next Steps

1. Configure authentication/authorization if needed
2. Set up database migrations
3. Add rate limiting for production
4. Configure CORS for your frontend domain
5. Set up logging and monitoring

## Support

For detailed API documentation, see `SETTINGS_USERS_API.md`.
