"""
Validation Service - Data validation utilities.

This service handles:
- PAN format and checksum validation
- GST format and state extraction
- Phone number format validation
- Email validation
- Pincode validation
- IFSC code validation
"""
import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ValidationService:
    """Service class for data validation."""
    
    # Validation patterns
    PAN_PATTERN = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    GST_PATTERN = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
    PHONE_PATTERN = re.compile(r'^\+?91[-\s]?[6-9]\d{9}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PINCODE_PATTERN = re.compile(r'^\d{6}$')
    IFSC_PATTERN = re.compile(r'^[A-Z]{4}0[A-Z0-9]{6}$')
    
    # GST state codes
    GST_STATE_CODES = {
        "01": "Jammu and Kashmir",
        "02": "Himachal Pradesh",
        "03": "Punjab",
        "04": "Chandigarh",
        "05": "Uttarakhand",
        "06": "Haryana",
        "07": "Delhi",
        "08": "Rajasthan",
        "09": "Uttar Pradesh",
        "10": "Bihar",
        "11": "Sikkim",
        "12": "Arunachal Pradesh",
        "13": "Nagaland",
        "14": "Manipur",
        "15": "Mizoram",
        "16": "Tripura",
        "17": "Meghalaya",
        "18": "Assam",
        "19": "West Bengal",
        "20": "Jharkhand",
        "21": "Odisha",
        "22": "Chhattisgarh",
        "23": "Madhya Pradesh",
        "24": "Gujarat",
        "25": "Daman and Diu",
        "26": "Dadra and Nagar Haveli",
        "27": "Maharashtra",
        "28": "Andhra Pradesh (Old)",
        "29": "Karnataka",
        "30": "Goa",
        "31": "Lakshadweep",
        "32": "Kerala",
        "33": "Tamil Nadu",
        "34": "Puducherry",
        "35": "Andaman and Nicobar Islands",
        "36": "Telangana",
        "37": "Andhra Pradesh (New)",
        "38": "Ladakh"
    }
    
    @staticmethod
    def validate_pan(pan: str) -> Tuple[bool, Optional[str]]:
        """
        Validate PAN number format and checksum.
        
        PAN Format: AAAAA9999A
        - First 3 characters: Alphabetic series (AAA-ZZZ)
        - 4th character: Type of holder (C-Company, P-Person, H-HUF, etc.)
        - 5th character: First character of surname/name
        - Next 4 characters: Sequential number (0001-9999)
        - Last character: Alphabetic check digit
        
        Args:
            pan: PAN number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pan:
            return False, "PAN number is required"
        
        # Remove whitespace and convert to uppercase
        pan = pan.strip().upper()
        
        # Check format
        if not ValidationService.PAN_PATTERN.match(pan):
            return False, "Invalid PAN format. Expected: AAAAA9999A"
        
        # Validate 4th character (entity type)
        valid_entity_types = ['C', 'P', 'H', 'F', 'A', 'T', 'B', 'L', 'J', 'G']
        if pan[3] not in valid_entity_types:
            return False, f"Invalid PAN entity type. 4th character must be one of: {', '.join(valid_entity_types)}"
        
        return True, None
    
    @staticmethod
    def validate_gst(gst: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate GST number format and extract state information.
        
        GST Format: 99AAAAA9999A9Z9
        - First 2 digits: State code
        - Next 10 characters: PAN of business
        - 13th character: Entity number (1-9, A-Z)
        - 14th character: Z (default)
        - 15th character: Checksum
        
        Args:
            gst: GST number to validate
            
        Returns:
            Tuple of (is_valid, error_message, info_dict)
        """
        if not gst:
            return False, "GST number is required", None
        
        # Remove whitespace and convert to uppercase
        gst = gst.strip().upper()
        
        # Check format
        if not ValidationService.GST_PATTERN.match(gst):
            return False, "Invalid GST format. Expected: 99AAAAA9999A9Z9", None
        
        # Extract and validate state code
        state_code = gst[:2]
        state_name = ValidationService.GST_STATE_CODES.get(state_code)
        
        if not state_name:
            return False, f"Invalid GST state code: {state_code}", None
        
        # Extract PAN from GST
        pan_from_gst = gst[2:12]
        
        # Validate PAN component
        is_valid_pan, pan_error = ValidationService.validate_pan(pan_from_gst)
        if not is_valid_pan:
            return False, f"Invalid PAN in GST: {pan_error}", None
        
        # Extract info
        info = {
            "state_code": state_code,
            "state_name": state_name,
            "pan": pan_from_gst,
            "entity_number": gst[12],
            "checksum": gst[14]
        }
        
        return True, None, info
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Indian phone number format.
        
        Accepted formats:
        - 9876543210
        - +919876543210
        - +91 9876543210
        - +91-9876543210
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return False, "Phone number is required"
        
        # Remove extra whitespace
        phone = phone.strip()
        
        # Check format
        if not ValidationService.PHONE_PATTERN.match(phone):
            return False, "Invalid phone format. Expected: +91-9876543210 or 9876543210"
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        email = email.strip().lower()
        
        if not ValidationService.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        # Check for common typos
        common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = email.split('@')[1] if '@' in email else ''
        
        # Warn about suspicious domains (but don't reject)
        suspicious = ['temp', 'fake', 'test', 'dummy']
        if any(word in domain.lower() for word in suspicious):
            logger.warning(f"Suspicious email domain detected: {email}")
        
        return True, None
    
    @staticmethod
    def validate_pincode(pincode: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Indian pincode format.
        
        Args:
            pincode: Pincode to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pincode:
            return False, "Pincode is required"
        
        pincode = pincode.strip()
        
        if not ValidationService.PINCODE_PATTERN.match(pincode):
            return False, "Invalid pincode format. Expected: 6 digits"
        
        # First digit indicates region
        region_codes = {
            '1': 'Delhi, Punjab, Haryana',
            '2': 'Himachal Pradesh, Chandigarh',
            '3': 'Punjab, Himachal Pradesh, Jammu & Kashmir',
            '4': 'Rajasthan',
            '5': 'Uttar Pradesh',
            '6': 'Bihar, Jharkhand',
            '7': 'West Bengal, Odisha',
            '8': 'Assam, North East',
            '9': 'Maharashtra, Goa'
        }
        
        return True, None
    
    @staticmethod
    def validate_ifsc(ifsc: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate IFSC code format.
        
        IFSC Format: AAAA0999999
        - First 4 characters: Bank code (alphabets)
        - 5th character: 0 (zero)
        - Last 6 characters: Branch code (alphanumeric)
        
        Args:
            ifsc: IFSC code to validate
            
        Returns:
            Tuple of (is_valid, error_message, info_dict)
        """
        if not ifsc:
            return False, "IFSC code is required", None
        
        ifsc = ifsc.strip().upper()
        
        if not ValidationService.IFSC_PATTERN.match(ifsc):
            return False, "Invalid IFSC format. Expected: AAAA0999999", None
        
        info = {
            "bank_code": ifsc[:4],
            "branch_code": ifsc[5:]
        }
        
        return True, None, info
    
    @staticmethod
    def validate_business_partner_data(data: Dict) -> Tuple[bool, list]:
        """
        Validate complete business partner data.
        
        Args:
            data: Dictionary containing business partner data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate PAN
        if 'pan' in data:
            is_valid, error = ValidationService.validate_pan(data['pan'])
            if not is_valid:
                errors.append(f"PAN: {error}")
        
        # Validate GST
        if 'gstin' in data and data['gstin']:
            is_valid, error, info = ValidationService.validate_gst(data['gstin'])
            if not is_valid:
                errors.append(f"GST: {error}")
        
        # Validate Phone
        if 'contact_phone' in data:
            is_valid, error = ValidationService.validate_phone(data['contact_phone'])
            if not is_valid:
                errors.append(f"Phone: {error}")
        
        # Validate Email
        if 'contact_email' in data:
            is_valid, error = ValidationService.validate_email(data['contact_email'])
            if not is_valid:
                errors.append(f"Email: {error}")
        
        # Validate Pincode
        if 'pincode' in data:
            is_valid, error = ValidationService.validate_pincode(data['pincode'])
            if not is_valid:
                errors.append(f"Pincode: {error}")
        
        # Validate IFSC
        if 'bank_ifsc' in data and data['bank_ifsc']:
            is_valid, error, info = ValidationService.validate_ifsc(data['bank_ifsc'])
            if not is_valid:
                errors.append(f"IFSC: {error}")
        
        return len(errors) == 0, errors
