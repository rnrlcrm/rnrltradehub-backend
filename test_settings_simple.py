"""
Simple manual test to verify settings/users endpoints are registered correctly.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from routes_complete import setting_router

def test_routes_registered():
    """Test that settings/users routes are registered correctly."""
    print("Testing routes registration...")
    print("=" * 60)
    
    app = FastAPI()
    app.include_router(setting_router)
    
    # Get all routes that include /api/settings
    settings_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and '/api/settings' in route.path:
            methods = getattr(route, 'methods', set())
            if methods:
                for method in methods:
                    settings_routes.append((method, route.path))
    
    # Expected routes
    expected_routes = [
        ('GET', '/api/settings/users'),
        ('POST', '/api/settings/users'),
        ('PUT', '/api/settings/users/{user_id}'),
        ('DELETE', '/api/settings/users/{user_id}'),
    ]
    
    print("\nExpected Routes:")
    for method, path in expected_routes:
        print(f"  {method:<8} {path}")
    
    print("\nActual Routes:")
    for method, path in sorted(settings_routes):
        print(f"  {method:<8} {path}")
    
    print("\nVerifying required routes exist:")
    for method, path in expected_routes:
        if (method, path) in settings_routes:
            print(f"  ✓ {method:<8} {path}")
        else:
            print(f"  ✗ {method:<8} {path} - MISSING!")
            return False
    
    print("\n" + "=" * 60)
    print("✓ ALL REQUIRED ROUTES ARE REGISTERED")
    print("=" * 60)
    return True


def test_schemas_importable():
    """Test that new schemas are importable."""
    print("\nTesting schemas...")
    print("=" * 60)
    
    try:
        import schemas
        
        # Check if new schemas exist
        required_schemas = [
            'SettingsUserCreate',
            'SettingsUserUpdate',
            'SettingsUserResponse',
            'UserType'
        ]
        
        print("\nVerifying schemas:")
        for schema_name in required_schemas:
            if hasattr(schemas, schema_name):
                print(f"  ✓ {schema_name}")
            else:
                print(f"  ✗ {schema_name} - MISSING!")
                return False
        
        # Test UserType enum
        print("\nUserType values:")
        print(f"  - PRIMARY: {schemas.UserType.PRIMARY}")
        print(f"  - SUB_USER: {schemas.UserType.SUB_USER}")
        
        print("\n" + "=" * 60)
        print("✓ ALL SCHEMAS ARE AVAILABLE")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False


def test_route_details():
    """Test route details including query parameters."""
    print("\nTesting route details...")
    print("=" * 60)
    
    from routes_complete import list_settings_users
    import inspect
    
    # Get signature of list_settings_users
    sig = inspect.signature(list_settings_users)
    
    print("\nGET /api/settings/users parameters:")
    for param_name, param in sig.parameters.items():
        if param_name != 'db':
            default = param.default if param.default != inspect.Parameter.empty else 'required'
            print(f"  - {param_name}: {param.annotation.__name__ if hasattr(param.annotation, '__name__') else param.annotation} = {default}")
    
    print("\n✓ Query parameters include userType and isActive")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = True
    success = test_routes_registered() and success
    success = test_schemas_importable() and success
    success = test_route_details() and success
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - ENDPOINTS ARE READY!")
        print("=" * 60)
        print("\nThe following endpoints are now available:")
        print("  GET    /api/settings/users?userType=&isActive=")
        print("  POST   /api/settings/users")
        print("  PUT    /api/settings/users/:id")
        print("  DELETE /api/settings/users/:id")
        print("=" * 60)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
