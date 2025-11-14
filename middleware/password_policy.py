"""
Password Policy Validation
Enforces password strength and security requirements
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordPolicy:
    """Password policy enforcement."""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    PASSWORD_EXPIRY_DAYS = 90
    PREVENT_REUSE_COUNT = 5
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 30
    
    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, List[str]]:
        """
        Validate password against policy.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.MAX_LENGTH} characters")
        
        # Uppercase check
        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Lowercase check
        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Number check
        if cls.REQUIRE_NUMBERS and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")
        
        # Special character check
        if cls.REQUIRE_SPECIAL:
            if not any(char in cls.SPECIAL_CHARS for char in password):
                errors.append(f"Password must contain at least one special character ({cls.SPECIAL_CHARS})")
        
        # Common password check (basic)
        common_passwords = [
            "password", "12345678", "qwerty", "abc123", "password123",
            "admin", "letmein", "welcome", "monkey", "dragon"
        ]
        if password.lower() in common_passwords:
            errors.append("Password is too common. Please choose a stronger password")
        
        return len(errors) == 0, errors
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @classmethod
    def is_password_expired(cls, password_changed_at: Optional[datetime]) -> bool:
        """Check if password has expired."""
        if not password_changed_at:
            return True
        
        expiry_date = password_changed_at + timedelta(days=cls.PASSWORD_EXPIRY_DAYS)
        return datetime.utcnow() > expiry_date
    
    @classmethod
    def can_reuse_password(cls, new_password: str, password_history: List[str]) -> bool:
        """
        Check if password can be reused.
        password_history should be list of hashed passwords.
        """
        if not password_history:
            return True
        
        # Check against last N passwords
        recent_passwords = password_history[-cls.PREVENT_REUSE_COUNT:]
        
        for old_hash in recent_passwords:
            if cls.verify_password(new_password, old_hash):
                return False
        
        return True
    
    @classmethod
    def should_lock_account(cls, failed_attempts: int) -> bool:
        """Check if account should be locked due to failed attempts."""
        return failed_attempts >= cls.MAX_FAILED_ATTEMPTS
    
    @classmethod
    def calculate_lockout_until(cls) -> datetime:
        """Calculate when account lockout should expire."""
        return datetime.utcnow() + timedelta(minutes=cls.LOCKOUT_MINUTES)
