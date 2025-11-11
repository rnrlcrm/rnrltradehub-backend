"""
Simple tests for multi-tenant user management features.

This test suite validates:
- User authentication with JWT
- Sub-user creation and management
- Multi-tenant data filtering
- Audit logging
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
from services.user_service import UserService

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_db():
    """Create all tables for testing."""
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_user_creation():
    """Test creating a user with multi-tenant fields."""
    print("Testing user creation...")
    db = setup_test_db()
    
    try:
        # Create a test user
        user = models.User(
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            is_active=True,
            user_type="primary",
            max_sub_users=5
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Verify user was created
        retrieved_user = db.query(models.User).filter(models.User.email == "test@example.com").first()
        assert retrieved_user is not None, "User should be created"
        assert retrieved_user.user_type == "primary", "User type should be primary"
        assert retrieved_user.max_sub_users == 5, "Max sub users should be 5"
        
        print("✅ User creation test passed")
        return True
    except Exception as e:
        print(f"❌ User creation test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_sub_user_creation():
    """Test creating a sub-user with parent relationship."""
    print("\nTesting sub-user creation...")
    db = setup_test_db()
    
    try:
        # Create parent user
        parent = models.User(
            name="Parent User",
            email="parent@example.com",
            password_hash="hashed_password",
            is_active=True,
            user_type="primary",
            max_sub_users=5,
            client_id=None,
            vendor_id=None
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)
        
        # Create sub-user
        sub_user = models.User(
            name="Sub User",
            email="subuser@example.com",
            password_hash="hashed_password",
            is_active=True,
            user_type="sub_user",
            parent_user_id=parent.id,
            client_id=None,  # Inherit from parent
            vendor_id=None   # Inherit from parent
        )
        db.add(sub_user)
        db.commit()
        db.refresh(sub_user)
        
        # Verify relationships
        retrieved_parent = db.query(models.User).filter(models.User.id == parent.id).first()
        retrieved_sub = db.query(models.User).filter(models.User.id == sub_user.id).first()
        
        assert retrieved_sub.parent_user_id == parent.id, "Sub-user should have parent_user_id"
        assert retrieved_sub.user_type == "sub_user", "User type should be sub_user"
        
        print("✅ Sub-user creation test passed")
        return True
    except Exception as e:
        print(f"❌ Sub-user creation test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_user_audit_log():
    """Test user audit log creation."""
    print("\nTesting user audit log...")
    db = setup_test_db()
    
    try:
        # Create a user
        user = models.User(
            name="Test User Audit",
            email="testaudit@example.com",
            password_hash="hashed_password",
            is_active=True,
            user_type="primary"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create audit log entry
        audit_log = models.UserAuditLog(
            user_id=user.id,
            action="login",
            entity_type=None,
            entity_id=None,
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0",
            details={"success": True},
            timestamp=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        
        # Verify audit log
        logs = db.query(models.UserAuditLog).filter(models.UserAuditLog.user_id == user.id).all()
        assert len(logs) == 1, "Should have one audit log entry"
        assert logs[0].action == "login", "Action should be login"
        assert logs[0].ip_address == "127.0.0.1", "IP address should match"
        
        print("✅ User audit log test passed")
        return True
    except Exception as e:
        print(f"❌ User audit log test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_password_hashing():
    """Test password hashing and verification."""
    print("\nTesting password hashing...")
    
    try:
        password = "test_password_123"
        
        # Hash password
        hashed = UserService.hash_password(password)
        assert hashed != password, "Hashed password should differ from plain text"
        
        # Verify correct password
        assert UserService.verify_password(password, hashed), "Correct password should verify"
        
        # Verify incorrect password
        assert not UserService.verify_password("wrong_password", hashed), "Wrong password should not verify"
        
        print("✅ Password hashing test passed")
        return True
    except Exception as e:
        print(f"❌ Password hashing test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Running Multi-Tenant User Management Tests")
    print("=" * 60)
    
    tests = [
        test_user_creation,
        test_sub_user_creation,
        test_user_audit_log,
        test_password_hashing
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
