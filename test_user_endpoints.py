"""
Test to verify /api/users endpoints are registered correctly.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from routes_complete import user_router


def test_user_routes_registered():
    """Test that /api/users routes are registered correctly."""
    print("Testing /api/users routes registration...")
    print("=" * 60)
    
    app = FastAPI()
    app.include_router(user_router)
    
    # Get all routes that include /api/users
    user_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and '/api/users' in route.path:
            methods = getattr(route, 'methods', set())
            if methods:
                for method in methods:
                    user_routes.append((method, route.path))
    
    # Expected routes
    expected_routes = [
        ('GET', '/api/users/'),
        ('POST', '/api/users/'),
        ('GET', '/api/users/{user_id}'),
        ('PUT', '/api/users/{user_id}'),
        ('DELETE', '/api/users/{user_id}'),
    ]
    
    print("\nExpected Routes:")
    for method, path in expected_routes:
        print(f"  {method:<8} {path}")
    
    print("\nActual Routes:")
    for method, path in sorted(user_routes):
        print(f"  {method:<8} {path}")
    
    print("\nVerifying required routes exist:")
    success = True
    for method, path in expected_routes:
        if (method, path) in user_routes:
            print(f"  ✓ {method:<8} {path}")
        else:
            print(f"  ✗ {method:<8} {path} - MISSING!")
            success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL REQUIRED USER ROUTES ARE REGISTERED")
    else:
        print("✗ SOME ROUTES ARE MISSING")
    print("=" * 60)
    return success


def test_schemas_importable():
    """Test that UserUpdate schema is importable."""
    print("\nTesting user schemas...")
    print("=" * 60)
    
    try:
        import schemas
        
        # Check if schemas exist
        required_schemas = [
            'UserCreate',
            'UserUpdate',
            'UserResponse',
            'UserRole'
        ]
        
        print("\nVerifying schemas:")
        success = True
        for schema_name in required_schemas:
            if hasattr(schemas, schema_name):
                print(f"  ✓ {schema_name}")
            else:
                print(f"  ✗ {schema_name} - MISSING!")
                success = False
        
        print("\n" + "=" * 60)
        if success:
            print("✓ ALL USER SCHEMAS ARE AVAILABLE")
        else:
            print("✗ SOME SCHEMAS ARE MISSING")
        print("=" * 60)
        return success
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = True
    success = test_user_routes_registered() and success
    success = test_schemas_importable() and success
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - /api/users ENDPOINTS ARE READY!")
        print("=" * 60)
        print("\nThe following endpoints are now available:")
        print("  GET    /api/users/")
        print("  POST   /api/users/")
        print("  GET    /api/users/{user_id}")
        print("  PUT    /api/users/{user_id}")
        print("  DELETE /api/users/{user_id}")
        print("=" * 60)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
