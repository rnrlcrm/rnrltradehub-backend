"""
OTP Service Layer
Handles OTP generation and verification
Note: Requires Twilio or MSG91 configuration for SMS
"""
import os
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


class OTPService:
    """OTP generation and verification service."""
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a random 6-digit OTP."""
        return ''.join(random.choices(string.digits, k=OTPService.OTP_LENGTH))
    
    @staticmethod
    async def send_sms_otp(phone_number: str, otp: str) -> bool:
        """
        Send OTP via SMS.
        Returns True if successful, False otherwise.
        """
        try:
            if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
                # Use Twilio
                from twilio.rest import Client
                
                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                
                message = client.messages.create(
                    body=f"Your RNRL TradeHub verification code is: {otp}. Valid for {OTPService.OTP_EXPIRY_MINUTES} minutes.",
                    from_=TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                
                logger.info(f"SMS OTP sent to {phone_number}")
                return message.status in ['queued', 'sent', 'delivered']
            
            else:
                # Mock SMS for development
                logger.warning(f"[MOCK SMS] To: {phone_number}, OTP: {otp}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to send SMS OTP to {phone_number}: {e}")
            return False
    
    @staticmethod
    async def send_email_otp(email: str, otp: str) -> bool:
        """Send OTP via email."""
        from services.email_service import EmailService
        return await EmailService.send_otp_email(email, otp)
    
    @staticmethod
    def verify_otp(provided_otp: str, stored_otp: str, created_at: datetime, attempts: int) -> tuple[bool, str]:
        """
        Verify OTP.
        Returns (is_valid, error_message)
        """
        # Check attempts
        if attempts >= OTPService.MAX_ATTEMPTS:
            return False, "Maximum verification attempts exceeded"
        
        # Check expiry
        expiry_time = created_at + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES)
        if datetime.utcnow() > expiry_time:
            return False, "OTP has expired"
        
        # Verify OTP
        if provided_otp != stored_otp:
            return False, "Invalid OTP"
        
        return True, "OTP verified successfully"
    
    @staticmethod
    def calculate_expiry() -> datetime:
        """Calculate OTP expiry time."""
        return datetime.utcnow() + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES)
