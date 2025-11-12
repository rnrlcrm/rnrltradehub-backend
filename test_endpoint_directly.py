"""
Test the settings/users endpoint directly to reproduce the error.
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys

# Mock the database connection
with patch('database.engine') as mock_engine, \
     patch('database.Base') as mock_base, \
     patch('database.get_db') as mock_get_db:
    
    # Import after patching
    from main import app
    
    client = TestClient(app)
    
    # Test the endpoint
    print("Testing GET /api/settings/users")
    print("=" * 60)
    
    response = client.get("/api/settings/users")
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Response: {response.text[:500] if len(response.text) > 500 else response.text}")
    
    if response.status_code != 200:
        print("\n❌ ENDPOINT RETURNED ERROR!")
        print("This matches the production error.")
    else:
        print("\n✓ Endpoint returned successfully")

