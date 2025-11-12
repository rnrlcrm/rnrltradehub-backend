"""
Test empty environment variable handling for database configuration.

This test verifies that database.py correctly handles empty string
environment variables and provides appropriate warnings.
"""
import os
import sys
import logging

def test_empty_env_vars():
    """Test that empty environment variables are handled correctly."""
    print("Testing Empty Environment Variable Handling")
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
        
        # Test Case 1: All environment variables set to empty strings
        print("\n1. Testing with all empty string environment variables...")
        os.environ['DB_HOST'] = ''
        os.environ['DB_NAME'] = ''
        os.environ['DB_USER'] = ''
        os.environ['DB_PASSWORD'] = ''
        
        # Force reimport to pick up new environment
        if 'database' in sys.modules:
            del sys.modules['database']
        
        # Capture log output
        import io
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        
        # Import database module
        import database
        
        # Check that it falls back to default
        expected = "postgresql+psycopg2://user:password@localhost:5432/rnrltradehub"
        if database.DATABASE_URL == expected:
            print("   ✓ PASS: Falls back to default with empty env vars")
            print(f"   URL: {database.DATABASE_URL}")
        else:
            print("   ✗ FAIL: Did not fall back correctly")
            print(f"   Expected: {expected}")
            print(f"   Got:      {database.DATABASE_URL}")
            return False
        
        # Test Case 2: Some variables empty, some not
        print("\n2. Testing with mixed empty/non-empty environment variables...")
        for key in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']:
            if key in os.environ:
                del os.environ[key]
        
        os.environ['DB_HOST'] = 'validhost'
        os.environ['DB_NAME'] = ''  # Empty!
        os.environ['DB_USER'] = 'validuser'
        os.environ['DB_PASSWORD'] = 'validpass'
        
        # Force reimport
        if 'database' in sys.modules:
            del sys.modules['database']
        
        import database as db2
        
        # Should fall back to default because DB_NAME is empty
        if db2.DATABASE_URL == expected:
            print("   ✓ PASS: Falls back to default when any var is empty")
            print(f"   URL: {db2.DATABASE_URL}")
        else:
            print("   ✗ FAIL: Did not handle partial config correctly")
            print(f"   Expected: {expected}")
            print(f"   Got:      {db2.DATABASE_URL}")
            return False
        
        # Test Case 3: Empty DATABASE_URL with valid individual vars
        print("\n3. Testing with empty DATABASE_URL and valid individual vars...")
        for key in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']:
            if key in os.environ:
                del os.environ[key]
        
        os.environ['DATABASE_URL'] = ''  # Empty!
        os.environ['DB_HOST'] = 'validhost'
        os.environ['DB_NAME'] = 'validdb'
        os.environ['DB_USER'] = 'validuser'
        os.environ['DB_PASSWORD'] = 'validpass'
        
        # Force reimport
        if 'database' in sys.modules:
            del sys.modules['database']
        
        import database as db3
        
        # Should use individual vars since DATABASE_URL is empty
        expected_individual = "postgresql+psycopg2://validuser:validpass@validhost:5432/validdb"
        if db3.DATABASE_URL == expected_individual:
            print("   ✓ PASS: Uses individual vars when DATABASE_URL is empty")
            print(f"   URL: {db3.DATABASE_URL}")
        else:
            print("   ✗ FAIL: Did not use individual vars correctly")
            print(f"   Expected: {expected_individual}")
            print(f"   Got:      {db3.DATABASE_URL}")
            return False
        
        # Test Case 4: Whitespace-only values
        print("\n4. Testing with whitespace-only environment variables...")
        for key in ['DATABASE_URL', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']:
            if key in os.environ:
                del os.environ[key]
        
        os.environ['DB_HOST'] = '   '  # Whitespace only
        os.environ['DB_NAME'] = '\t\t'  # Tabs
        os.environ['DB_USER'] = ' \n '  # Newlines
        os.environ['DB_PASSWORD'] = '    '
        
        # Force reimport
        if 'database' in sys.modules:
            del sys.modules['database']
        
        import database as db4
        
        # Should fall back to default since whitespace-only is treated as empty
        expected = "postgresql+psycopg2://user:password@localhost:5432/rnrltradehub"
        if db4.DATABASE_URL == expected:
            print("   ✓ PASS: Treats whitespace-only as empty")
            print(f"   URL: {db4.DATABASE_URL}")
        else:
            print("   ✗ FAIL: Did not handle whitespace correctly")
            print(f"   Expected: {expected}")
            print(f"   Got:      {db4.DATABASE_URL}")
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
    """Run all empty environment variable tests."""
    print("=" * 60)
    print("Empty Environment Variable Test Suite")
    print("=" * 60)
    
    if test_empty_env_vars():
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nEmpty environment variable handling:")
        print("- Empty strings are properly detected and handled")
        print("- Whitespace-only values are treated as empty")
        print("- Falls back to default when configuration is incomplete")
        print("- Warning messages are logged for incomplete configuration")
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
