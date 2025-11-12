"""
Utility functions for RNRL TradeHub backend.

This module contains reusable utility functions to eliminate code duplication.
"""
from typing import Dict
from passlib.context import CryptContext


# CORS headers for exception responses
def get_cors_headers() -> Dict[str, str]:
    """
    Get standard CORS headers for exception responses.
    
    Returns:
        dict: CORS headers for non-production environment.
    """
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }


# Password hashing context (singleton)
_pwd_context = None


def get_password_context() -> CryptContext:
    """
    Get or create the password hashing context.
    
    Uses bcrypt for secure password hashing. Context is created once
    and reused for efficiency.
    
    Returns:
        CryptContext: Password hashing context.
    """
    global _pwd_context
    if _pwd_context is None:
        _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return _pwd_context


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash.
        
    Returns:
        str: Hashed password.
    """
    pwd_context = get_password_context()
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to verify against.
        
    Returns:
        bool: True if password matches, False otherwise.
    """
    pwd_context = get_password_context()
    return pwd_context.verify(plain_password, hashed_password)
