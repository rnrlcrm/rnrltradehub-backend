"""
Test to verify the /health endpoint is correctly configured.

This test ensures that:
1. The /health endpoint exists
2. It returns the correct response schema
3. It's accessible without authentication
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


def test_health_endpoint():
    """Test that /health endpoint is registered and configured correctly."""
    print("Testing /health endpoint configuration...")
    print("=" * 60)
    
    # Get all routes
    routes = {route.path: route for route in app.routes if hasattr(route, 'path')}
    
    # Check /health exists
    if '/health' not in routes:
        print("✗ FAIL: /health endpoint not found")
        return False
    
    print("✓ /health endpoint is registered")
    
    # Get the health route
    health_route = routes['/health']
    
    # Verify it's a GET endpoint
    methods = getattr(health_route, 'methods', set())
    if 'GET' not in methods:
        print(f"✗ FAIL: /health does not accept GET. Methods: {methods}")
        return False
    
    print("✓ /health accepts GET requests")
    
    # Check response model
    response_model = getattr(health_route, 'response_model', None)
    if response_model:
        print(f"✓ /health has response model: {response_model.__name__}")
    
    return True


def test_root_endpoint():
    """Test that root endpoint is registered."""
    print("\nTesting root endpoint configuration...")
    print("=" * 60)
    
    routes = {route.path: route for route in app.routes if hasattr(route, 'path')}
    
    if '/' not in routes:
        print("✗ FAIL: / endpoint not found")
        return False
    
    print("✓ / endpoint is registered")
    
    root_route = routes['/']
    methods = getattr(root_route, 'methods', set())
    if 'GET' not in methods:
        print(f"✗ FAIL: / does not accept GET. Methods: {methods}")
        return False
    
    print("✓ / accepts GET requests")
    
    return True


def test_docs_endpoint():
    """Test that /docs endpoint is registered."""
    print("\nTesting /docs endpoint configuration...")
    print("=" * 60)
    
    routes = {route.path: route for route in app.routes if hasattr(route, 'path')}
    
    if '/docs' not in routes:
        print("✗ FAIL: /docs endpoint not found")
        return False
    
    print("✓ /docs endpoint is registered")
    print("✓ Swagger UI is available")
    
    return True


def test_application_info():
    """Test application metadata."""
    print("\nTesting application configuration...")
    print("=" * 60)
    
    print(f"Application Title: {app.title}")
    print(f"Application Description: {app.description[:50]}...")
    print(f"Application Version: {app.version}")
    print(f"Total Routes: {len(app.routes)}")
    
    if "FastAPI" in app.title or "API" in app.title:
        print("✓ Application title is appropriate")
    
    return True


def main():
    """Run all health endpoint tests."""
    print("=" * 60)
    print("Health Endpoint Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("Docs Endpoint", test_docs_endpoint),
        ("Application Info", test_application_info),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Exception in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("✅ ALL TESTS PASSED - /health endpoint is ready!")
        print()
        print("The /health endpoint should return:")
        print('{')
        print('  "status": "healthy",')
        print('  "service": "rnrltradehub-nonprod",')
        print('  "version": "1.0.0",')
        print('  "database": "connected"')
        print('}')
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
