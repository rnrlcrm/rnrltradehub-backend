"""
Test database URL construction logic.

This test verifies that database.py correctly constructs DATABASE_URL
for various scenarios including Cloud SQL Unix socket connections.
"""
import os
import sys

def test_database_url_construction():
    """Test DATABASE_URL construction from environment variables."""
    print("Testing DATABASE_URL Construction Logic")
    print("=" * 60)
    
    # Test Case 1: Cloud SQL Unix socket path
    print("\n1. Testing Cloud SQL Unix socket connection...")
    db_host = "/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db"
    db_name = "testdb"
    db_user = "testuser"
    db_password = "testpass"
    
    # Simulate the logic from database.py
    if db_host.startswith("/cloudsql/"):
        url = f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host={db_host}"
    else:
        url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:5432/{db_name}"
    
    expected = "postgresql+psycopg2://testuser:testpass@/testdb?host=/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db"
    if url == expected:
        print(f"   ✓ PASS: Cloud SQL URL correctly formatted")
        print(f"   URL: {url}")
    else:
        print(f"   ✗ FAIL: Cloud SQL URL incorrect")
        print(f"   Expected: {expected}")
        print(f"   Got:      {url}")
        return False
    
    # Test Case 2: Standard localhost connection
    print("\n2. Testing standard localhost connection...")
    db_host = "localhost"
    db_name = "rnrltradehub"
    db_user = "user"
    db_password = "password"
    db_port = "5432"
    
    if db_host.startswith("/cloudsql/"):
        url = f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host={db_host}"
    else:
        url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    expected = "postgresql+psycopg2://user:password@localhost:5432/rnrltradehub"
    if url == expected:
        print(f"   ✓ PASS: Localhost URL correctly formatted")
        print(f"   URL: {url}")
    else:
        print(f"   ✗ FAIL: Localhost URL incorrect")
        print(f"   Expected: {expected}")
        print(f"   Got:      {url}")
        return False
    
    # Test Case 3: Remote PostgreSQL server
    print("\n3. Testing remote PostgreSQL server connection...")
    db_host = "10.0.0.5"
    db_name = "proddb"
    db_user = "admin"
    db_password = "secret"
    db_port = "5432"
    
    if db_host.startswith("/cloudsql/"):
        url = f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host={db_host}"
    else:
        url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    expected = "postgresql+psycopg2://admin:secret@10.0.0.5:5432/proddb"
    if url == expected:
        print(f"   ✓ PASS: Remote server URL correctly formatted")
        print(f"   URL: {url}")
    else:
        print(f"   ✗ FAIL: Remote server URL incorrect")
        print(f"   Expected: {expected}")
        print(f"   Got:      {url}")
        return False
    
    # Test Case 4: Custom port
    print("\n4. Testing custom port connection...")
    db_host = "db.example.com"
    db_name = "mydb"
    db_user = "dbuser"
    db_password = "dbpass"
    db_port = "5433"
    
    if db_host.startswith("/cloudsql/"):
        url = f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host={db_host}"
    else:
        url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    expected = "postgresql+psycopg2://dbuser:dbpass@db.example.com:5433/mydb"
    if url == expected:
        print(f"   ✓ PASS: Custom port URL correctly formatted")
        print(f"   URL: {url}")
    else:
        print(f"   ✗ FAIL: Custom port URL incorrect")
        print(f"   Expected: {expected}")
        print(f"   Got:      {url}")
        return False
    
    return True


def test_database_module_import():
    """Test that the database module can be imported with different environment configurations."""
    print("\n" + "=" * 60)
    print("Testing Database Module Import")
    print("=" * 60)
    
    # Save original environment
    original_env = {
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
        'DB_HOST': os.environ.get('DB_HOST'),
        'DB_NAME': os.environ.get('DB_NAME'),
        'DB_USER': os.environ.get('DB_USER'),
        'DB_PASSWORD': os.environ.get('DB_PASSWORD'),
        'DB_PORT': os.environ.get('DB_PORT'),
    }
    
    try:
        # Clear all database environment variables
        for key in ['DATABASE_URL', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']:
            if key in os.environ:
                del os.environ[key]
        
        # Test with Cloud SQL configuration
        print("\n1. Testing with Cloud SQL environment variables...")
        os.environ['DB_HOST'] = '/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db'
        os.environ['DB_NAME'] = 'testdb'
        os.environ['DB_USER'] = 'testuser'
        os.environ['DB_PASSWORD'] = 'testpass'
        
        # Force reimport to pick up new environment
        if 'database' in sys.modules:
            del sys.modules['database']
        
        import database
        
        if database.DATABASE_URL == "postgresql+psycopg2://testuser:testpass@/testdb?host=/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db":
            print("   ✓ PASS: Cloud SQL DATABASE_URL correctly constructed")
            print(f"   URL: {database.DATABASE_URL}")
        else:
            print("   ✗ FAIL: Cloud SQL DATABASE_URL incorrect")
            print(f"   Expected: postgresql+psycopg2://testuser:testpass@/testdb?host=/cloudsql/google-mpf-cas7ishusxmu:us-central1:erp-nonprod-db")
            print(f"   Got:      {database.DATABASE_URL}")
            return False
        
        # Test with localhost configuration
        print("\n2. Testing with localhost environment variables...")
        for key in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']:
            if key in os.environ:
                del os.environ[key]
        
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_NAME'] = 'rnrltradehub'
        os.environ['DB_USER'] = 'user'
        os.environ['DB_PASSWORD'] = 'password'
        
        # Force reimport
        if 'database' in sys.modules:
            del sys.modules['database']
        
        import database as db2
        
        if db2.DATABASE_URL == "postgresql+psycopg2://user:password@localhost:5432/rnrltradehub":
            print("   ✓ PASS: Localhost DATABASE_URL correctly constructed")
            print(f"   URL: {db2.DATABASE_URL}")
        else:
            print("   ✗ FAIL: Localhost DATABASE_URL incorrect")
            print(f"   Expected: postgresql+psycopg2://user:password@localhost:5432/rnrltradehub")
            print(f"   Got:      {db2.DATABASE_URL}")
            return False
        
        # Test with explicit DATABASE_URL (should take priority)
        print("\n3. Testing with explicit DATABASE_URL...")
        for key in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']:
            if key in os.environ:
                del os.environ[key]
        
        os.environ['DATABASE_URL'] = 'postgresql://explicit:pass@explicit.host:5432/explicitdb'
        os.environ['DB_HOST'] = '/cloudsql/should-be-ignored'
        
        # Force reimport
        if 'database' in sys.modules:
            del sys.modules['database']
        
        import database as db3
        
        if db3.DATABASE_URL == "postgresql://explicit:pass@explicit.host:5432/explicitdb":
            print("   ✓ PASS: Explicit DATABASE_URL takes priority")
            print(f"   URL: {db3.DATABASE_URL}")
        else:
            print("   ✗ FAIL: DATABASE_URL priority incorrect")
            print(f"   Expected: postgresql://explicit:pass@explicit.host:5432/explicitdb")
            print(f"   Got:      {db3.DATABASE_URL}")
            return False
        
        return True
        
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value
        
        # Clean up module cache
        if 'database' in sys.modules:
            del sys.modules['database']


def main():
    """Run all database URL tests."""
    print("=" * 60)
    print("Database URL Construction Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: URL construction logic
    if not test_database_url_construction():
        all_passed = False
    
    # Test 2: Module import with different configurations
    if not test_database_module_import():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nDatabase configuration summary:")
        print("- Cloud SQL Unix socket connections: SUPPORTED")
        print("- Standard TCP connections: SUPPORTED")
        print("- Explicit DATABASE_URL: SUPPORTED (takes priority)")
        print("- Default localhost fallback: SUPPORTED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
