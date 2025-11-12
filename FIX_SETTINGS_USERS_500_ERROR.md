# Fix for 500 Internal Server Error on /api/settings/users

## Issue Summary

The `/api/settings/users` endpoint was returning a 500 Internal Server Error when the frontend attempted to fetch the user list.

**Error in frontend:**
```
https://erp-nonprod-backend-502095789065.us-central1.run.app/api/settings/users 500 (Internal Server Error)
Failed to fetch users: {message: 'Request failed', code: '500', details: {…}}
```

## Root Cause Analysis

The issue was caused by a mismatch between the database model structure and the response schema:

### The User Model
The `User` model in `models.py` has TWO ways to represent a user's role:

1. **`role_name` column** - An Enum column with values like 'Admin', 'Sales', etc. (kept for backward compatibility)
   ```python
   role_name = Column(
       Enum('Admin', 'Sales', 'Accounts', 'Dispute Manager', 'Vendor/Client', name='user_role'),
       nullable=True
   )
   ```

2. **`role` relationship** - A foreign key relationship to the `Role` table
   ```python
   role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
   role = relationship("Role", back_populates="users")
   ```

### The Response Schema
The `SettingsUserResponse` schema expects:
```python
role_id: Optional[int] = None
role_name: Optional[str] = None  # Expects a STRING from the Role table
```

### The Problem
When the endpoint returned User objects directly (without manual serialization), Pydantic would:

1. Read `role_name` from the User model's `role_name` Enum column
2. NOT automatically access the `role.name` from the relationship
3. Potentially encounter lazy loading errors if the relationship wasn't loaded

This caused serialization failures, especially when:
- The role relationship wasn't eagerly loaded (lazy loading after session close)
- The Enum value format didn't match the expected string format
- Users had roles assigned via `role_id` but the relationship wasn't populated

## The Fix

Modified three endpoints in `routes_complete.py`:

### 1. GET /api/settings/users

**Before:**
```python
@setting_router.get("/users", response_model=List[schemas.SettingsUserResponse])
def list_settings_users(...):
    query = db.query(models.User)
    # ... filters ...
    users = query.offset(skip).limit(limit).all()
    return users  # Returns User objects directly
```

**After:**
```python
@setting_router.get("/users", response_model=List[schemas.SettingsUserResponse])
def list_settings_users(...):
    from sqlalchemy.orm import joinedload
    
    # Eagerly load role relationship
    query = db.query(models.User).options(joinedload(models.User.role))
    # ... filters ...
    users = query.offset(skip).limit(limit).all()
    
    # Manually construct response dictionaries
    response_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,  # From Role table
            "is_active": user.is_active,
            "user_type": str(user.user_type) if hasattr(user.user_type, 'value') else user.user_type,
            # ... other fields ...
        }
        response_data.append(user_dict)
    
    return response_data
```

### 2. POST /api/settings/users

Similar changes:
- Eagerly load role relationship after user creation
- Manually construct response dictionary
- Ensure `role_name` comes from `user.role.name`

### 3. PUT /api/settings/users/{user_id}

Similar changes:
- Eagerly load role relationship after user update
- Manually construct response dictionary
- Ensure `role_name` comes from `user.role.name`

## Key Changes

1. **Eager Loading**: Use `joinedload(models.User.role)` to load the role relationship in the same query, preventing lazy loading errors

2. **Manual Serialization**: Construct response dictionaries manually instead of relying on Pydantic's automatic serialization

3. **Explicit role_name**: Populate `role_name` from `user.role.name` (the Role table's name field) instead of the User model's `role_name` Enum column

4. **Enum to String**: Convert `user_type` Enum to string explicitly to avoid serialization issues

## Testing

The fix was verified with:
- ✅ Unit tests with mock data
- ✅ Route registration tests
- ✅ Schema validation tests
- ✅ CodeQL security scan (0 alerts)

To test in production:
```bash
python verify_settings_users_fix.py https://erp-nonprod-backend-502095789065.us-central1.run.app
```

## Impact

**Affected Endpoints:**
- GET `/api/settings/users` - Now returns proper user list with role names
- POST `/api/settings/users` - Now returns proper user data on creation
- PUT `/api/settings/users/{user_id}` - Now returns proper user data on update

**No Breaking Changes:**
- Response format remains the same
- All fields are populated correctly
- Backward compatibility maintained

## Prevention

To prevent similar issues in the future:

1. **Always eagerly load relationships** when they're needed for the response
2. **Be careful with dual representations** (column + relationship for the same data)
3. **Test serialization explicitly** when models have Enum columns
4. **Consider using DTOs or computed fields** instead of dual representations

## Related Files

- `routes_complete.py` - Contains the fixed endpoints
- `models.py` - User model with dual role representation
- `schemas.py` - SettingsUserResponse schema
- `verify_settings_users_fix.py` - Verification script for production testing
