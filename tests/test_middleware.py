"""
Tests for middleware components
"""
import pytest
from middleware.password_policy import PasswordPolicy
from middleware.auth_middleware import create_access_token, verify_token
from datetime import datetime, timedelta


class TestPasswordPolicy:
    """Test password policy validation."""
    
    def test_valid_password(self):
        """Test valid password."""
        is_valid, errors = PasswordPolicy.validate_password("Test@123")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_password_too_short(self):
        """Test password too short."""
        is_valid, errors = PasswordPolicy.validate_password("Test@1")
        assert is_valid is False
        assert any("at least 8" in err for err in errors)
    
    def test_password_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, errors = PasswordPolicy.validate_password("test@123")
        assert is_valid is False
        assert any("uppercase" in err for err in errors)
    
    def test_password_no_lowercase(self):
        """Test password without lowercase."""
        is_valid, errors = PasswordPolicy.validate_password("TEST@123")
        assert is_valid is False
        assert any("lowercase" in err for err in errors)
    
    def test_password_no_number(self):
        """Test password without number."""
        is_valid, errors = PasswordPolicy.validate_password("Test@test")
        assert is_valid is False
        assert any("number" in err for err in errors)
    
    def test_password_no_special(self):
        """Test password without special character."""
        is_valid, errors = PasswordPolicy.validate_password("Test1234")
        assert is_valid is False
        assert any("special character" in err for err in errors)
    
    def test_common_password(self):
        """Test common password."""
        is_valid, errors = PasswordPolicy.validate_password("password")
        assert is_valid is False
        assert any("too common" in err for err in errors)
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "Test@123"
        hashed = PasswordPolicy.hash_password(password)
        
        assert hashed != password
        assert PasswordPolicy.verify_password(password, hashed) is True
        assert PasswordPolicy.verify_password("wrong", hashed) is False
    
    def test_password_expiry(self):
        """Test password expiry check."""
        old_date = datetime.utcnow() - timedelta(days=100)
        assert PasswordPolicy.is_password_expired(old_date) is True
        
        recent_date = datetime.utcnow() - timedelta(days=30)
        assert PasswordPolicy.is_password_expired(recent_date) is False


class TestAuthMiddleware:
    """Test authentication middleware."""
    
    def test_create_and_verify_token(self):
        """Test token creation and verification."""
        payload = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        
        verified = verify_token(token, token_type="access")
        assert verified["sub"] == "user123"
        assert verified["email"] == "test@example.com"
    
    def test_expired_token(self):
        """Test expired token handling."""
        payload = {"sub": "user123"}
        expired_delta = timedelta(minutes=-10)  # Expired 10 minutes ago
        
        token = create_access_token(payload, expires_delta=expired_delta)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            verify_token(token, token_type="access")
