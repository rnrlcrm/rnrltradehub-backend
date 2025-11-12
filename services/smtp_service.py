"""
SMTP Email Sender - Actual email sending via SMTP.

This service handles:
- Gmail SMTP configuration
- Sending emails via SMTP
- Email queue processing
- Error handling and retry logic
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)


class SMTPEmailSender:
    """Service class for sending emails via SMTP."""
    
    # SMTP Configuration from environment variables
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App password for Gmail
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@rnrltradehub.com")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "RNRL TradeHub")
    SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Check if SMTP is enabled
            if not SMTPEmailSender.SMTP_ENABLED:
                logger.warning(f"SMTP disabled - would send to {to_email}: {subject}")
                return False
            
            # Check if SMTP credentials are configured
            if not SMTPEmailSender.SMTP_USER or not SMTPEmailSender.SMTP_PASSWORD:
                logger.error("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{SMTPEmailSender.SMTP_FROM_NAME} <{SMTPEmailSender.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add plain text part
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Create SMTP connection
            with smtplib.SMTP(SMTPEmailSender.SMTP_HOST, SMTPEmailSender.SMTP_PORT) as server:
                server.starttls()  # Enable TLS
                server.login(SMTPEmailSender.SMTP_USER, SMTPEmailSender.SMTP_PASSWORD)
                
                # Send email
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(
                    SMTPEmailSender.SMTP_FROM_EMAIL,
                    recipients,
                    msg.as_string()
                )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def process_email_queue(db: Session, limit: int = 50) -> dict:
        """
        Process pending emails from the email queue.
        
        This can be run periodically to send queued emails.
        
        Args:
            db: Database session
            limit: Maximum number of emails to process
            
        Returns:
            Dictionary with processing statistics
        """
        try:
            stats = {
                "processed": 0,
                "sent": 0,
                "failed": 0,
                "errors": []
            }
            
            # Get pending emails
            pending_emails = db.query(models.EmailLog).filter(
                models.EmailLog.status == "pending"
            ).limit(limit).all()
            
            stats["processed"] = len(pending_emails)
            
            for email_log in pending_emails:
                try:
                    # Send email
                    success = SMTPEmailSender.send_email(
                        to_email=email_log.recipient,
                        subject=email_log.subject,
                        body_html=email_log.body,
                        body_text=email_log.body  # Could extract text version
                    )
                    
                    if success:
                        email_log.status = "sent"
                        email_log.sent_at = models.datetime.utcnow()
                        stats["sent"] += 1
                    else:
                        email_log.status = "failed"
                        email_log.error_message = "SMTP sending failed"
                        stats["failed"] += 1
                    
                    db.commit()
                    
                except Exception as e:
                    email_log.status = "failed"
                    email_log.error_message = str(e)
                    stats["failed"] += 1
                    stats["errors"].append(str(e))
                    db.commit()
                    logger.error(f"Error processing email {email_log.id}: {str(e)}")
            
            logger.info(f"Email queue processed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing email queue: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def test_smtp_connection() -> dict:
        """
        Test SMTP connection and authentication.
        
        Returns:
            Dictionary with test results
        """
        try:
            if not SMTPEmailSender.SMTP_ENABLED:
                return {
                    "success": False,
                    "message": "SMTP is disabled"
                }
            
            if not SMTPEmailSender.SMTP_USER or not SMTPEmailSender.SMTP_PASSWORD:
                return {
                    "success": False,
                    "message": "SMTP credentials not configured"
                }
            
            # Test connection
            with smtplib.SMTP(SMTPEmailSender.SMTP_HOST, SMTPEmailSender.SMTP_PORT) as server:
                server.starttls()
                server.login(SMTPEmailSender.SMTP_USER, SMTPEmailSender.SMTP_PASSWORD)
            
            return {
                "success": True,
                "message": "SMTP connection successful",
                "host": SMTPEmailSender.SMTP_HOST,
                "port": SMTPEmailSender.SMTP_PORT,
                "user": SMTPEmailSender.SMTP_USER
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": "SMTP authentication failed - check credentials"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"SMTP connection failed: {str(e)}"
            }
