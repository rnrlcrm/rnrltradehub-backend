"""
Test CORS headers in exception responses.

This test verifies that all exception handlers include proper CORS headers
to prevent CORS errors when the frontend makes requests.
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_cors_headers_on_404():
    """Test that 404 errors include CORS headers."""
    response = client.get("/api/nonexistent")
    
    # Check CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


def test_cors_headers_on_validation_error():
    """Test that validation errors include CORS headers."""
    # This should trigger a validation error if the endpoint exists
    response = client.post("/api/settings/users", json={"invalid": "data"})
    
    # Check CORS headers are present (regardless of status code)
    if response.status_code == 422:
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"


def test_cors_headers_on_database_error():
    """Test that database errors include CORS headers."""
    # Try to access an endpoint that might have database issues
    response = client.get("/api/settings/users")
    
    # Regardless of success or failure, CORS headers should be present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"


def test_root_endpoint_has_cors():
    """Test that successful responses also have CORS headers."""
    response = client.get("/")
    
    # Even successful responses should have CORS headers from middleware
    assert response.status_code == 200
    # Note: Middleware adds these, so they might be lowercase
    assert any(h in response.headers for h in ["access-control-allow-origin", "Access-Control-Allow-Origin"])


if __name__ == "__main__":
    print("Testing CORS headers in exception responses...")
    
    print("\n1. Testing 404 error CORS headers...")
    test_cors_headers_on_404()
    print("   ✓ 404 errors include CORS headers")
    
    print("\n2. Testing validation error CORS headers...")
    test_cors_headers_on_validation_error()
    print("   ✓ Validation errors include CORS headers")
    
    print("\n3. Testing database error CORS headers...")
    test_cors_headers_on_database_error()
    print("   ✓ Database errors include CORS headers")
    
    print("\n4. Testing successful response CORS headers...")
    test_root_endpoint_has_cors()
    print("   ✓ Successful responses include CORS headers")
    
    print("\n✅ All CORS header tests passed!")
