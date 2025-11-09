"""
Input validation utilities for Indian business identifiers and contact information.

Provides comprehensive validation for:
- GST/GSTIN (Goods and Services Tax Identification Number)
- PAN (Permanent Account Number)
- Mobile numbers (Indian format)
- Email addresses
- Pincode (Indian postal codes)
"""
import re
from typing import Optional


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_pan(pan: str) -> bool:
    """
    Validate PAN (Permanent Account Number) format.
    
    Format: AAAAA9999A
    - First 5 characters: Alphabets (uppercase)
    - Next 4 characters: Digits
    - Last character: Alphabet (uppercase)
    
    Args:
        pan: PAN string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If PAN format is invalid
    """
    if not pan:
        raise ValidationError("PAN cannot be empty")
    
    pan = pan.strip().upper()
    
    # PAN format: AAAAA9999A
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    
    if not re.match(pattern, pan):
        raise ValidationError(
            f"Invalid PAN format: {pan}. "
            "Expected format: AAAAA9999A (e.g., ABCDE1234F)"
        )
    
    return True


def validate_gstin(gstin: Optional[str]) -> bool:
    """
    Validate GSTIN (GST Identification Number) format.
    
    Format: 99AAAAA9999A9Z9
    - First 2 characters: State code (digits)
    - Next 10 characters: PAN
    - Next 1 character: Entity number (alphanumeric)
    - Next 1 character: 'Z' by default
    - Last character: Check digit (alphanumeric)
    
    Args:
        gstin: GSTIN string to validate (optional)
        
    Returns:
        True if valid or None
        
    Raises:
        ValidationError: If GSTIN format is invalid
    """
    if not gstin:
        return True  # GSTIN is optional
    
    gstin = gstin.strip().upper()
    
    # GSTIN format: 99AAAAA9999A9Z9
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    if not re.match(pattern, gstin):
        raise ValidationError(
            f"Invalid GSTIN format: {gstin}. "
            "Expected format: 99AAAAA9999A9Z9 (e.g., 27ABCDE1234F1Z5)"
        )
    
    # Extract PAN from GSTIN (characters 3-12) and validate it
    pan_from_gstin = gstin[2:12]
    try:
        validate_pan(pan_from_gstin)
    except ValidationError:
        raise ValidationError(
            f"Invalid PAN in GSTIN: {pan_from_gstin}. "
            f"GSTIN {gstin} contains an invalid PAN number."
        )
    
    return True


def validate_mobile(mobile: str) -> bool:
    """
    Validate Indian mobile number format.
    
    Accepts:
    - 10 digits: 9876543210
    - With +91: +919876543210
    - With country code: 919876543210
    - With spaces/hyphens: +91 98765 43210, 98765-43210
    
    Args:
        mobile: Mobile number string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If mobile format is invalid
    """
    if not mobile:
        raise ValidationError("Mobile number cannot be empty")
    
    # Remove spaces, hyphens, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', mobile)
    
    # Remove +91 or 91 prefix if present
    if cleaned.startswith('+91'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('91') and len(cleaned) == 12:
        cleaned = cleaned[2:]
    
    # Must be exactly 10 digits and start with 6-9
    pattern = r'^[6-9][0-9]{9}$'
    
    if not re.match(pattern, cleaned):
        raise ValidationError(
            f"Invalid mobile number: {mobile}. "
            "Expected 10 digits starting with 6-9 (e.g., 9876543210 or +91 9876543210)"
        )
    
    return True


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")
    
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email.strip()):
        raise ValidationError(
            f"Invalid email format: {email}"
        )
    
    return True


def validate_pincode(pincode: str) -> bool:
    """
    Validate Indian pincode format.
    
    Format: 6 digits
    
    Args:
        pincode: Pincode string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If pincode format is invalid
    """
    if not pincode:
        raise ValidationError("Pincode cannot be empty")
    
    cleaned = pincode.strip()
    
    # Must be exactly 6 digits
    pattern = r'^[1-9][0-9]{5}$'
    
    if not re.match(pattern, cleaned):
        raise ValidationError(
            f"Invalid pincode: {pincode}. "
            "Expected 6 digits (e.g., 110001, 400001)"
        )
    
    return True


def validate_ifsc(ifsc: Optional[str]) -> bool:
    """
    Validate IFSC (Indian Financial System Code) format.
    
    Format: AAAA0999999
    - First 4 characters: Bank code (alphabets)
    - 5th character: 0 (zero)
    - Last 6 characters: Branch code (alphanumeric)
    
    Args:
        ifsc: IFSC code string to validate (optional)
        
    Returns:
        True if valid or None
        
    Raises:
        ValidationError: If IFSC format is invalid
    """
    if not ifsc:
        return True  # IFSC is optional
    
    ifsc = ifsc.strip().upper()
    
    # IFSC format: AAAA0999999
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    
    if not re.match(pattern, ifsc):
        raise ValidationError(
            f"Invalid IFSC code: {ifsc}. "
            "Expected format: AAAA0999999 (e.g., SBIN0001234)"
        )
    
    return True


def sanitize_pan(pan: str) -> str:
    """Sanitize and normalize PAN."""
    return pan.strip().upper() if pan else ""


def sanitize_gstin(gstin: Optional[str]) -> Optional[str]:
    """Sanitize and normalize GSTIN."""
    return gstin.strip().upper() if gstin else None


def sanitize_mobile(mobile: str) -> str:
    """Sanitize mobile number to 10-digit format."""
    if not mobile:
        return ""
    
    # Remove all non-digits
    cleaned = re.sub(r'\D', '', mobile)
    
    # Remove +91 or 91 prefix if present
    if cleaned.startswith('91') and len(cleaned) > 10:
        cleaned = cleaned[2:]
    
    return cleaned


def sanitize_pincode(pincode: str) -> str:
    """Sanitize pincode."""
    return pincode.strip() if pincode else ""


def sanitize_ifsc(ifsc: Optional[str]) -> Optional[str]:
    """Sanitize and normalize IFSC."""
    return ifsc.strip().upper() if ifsc else None
