"""
Email Service - Business logic for email notifications.

This service handles:
- Sub-user invitation emails
- Password reset emails
- Email template rendering
- Email logging
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session
import logging

import models
import schemas

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for email operations."""
    
    @staticmethod
    def send_sub_user_invitation(
        db: Session,
        sub_user: models.User,
        parent_user: models.User,
        temporary_password: str
    ) -> bool:
        """
        Send invitation email to new sub-user.
        
        Business Logic:
        - Use email template for consistency
        - Log email for tracking
        - Include login credentials and instructions
        
        Args:
            db: Database session
            sub_user: New sub-user
            parent_user: Parent user who created the sub-user
            temporary_password: Temporary password for initial login
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Get or create email template
            template = db.query(models.EmailTemplate).filter(
                models.EmailTemplate.name == "sub_user_invitation"
            ).first()
            
            if not template:
                # Create default template
                template = models.EmailTemplate(
                    name="sub_user_invitation",
                    category="notification",
                    subject="You've been invited to RNRL TradeHub",
                    body_html="""
                    <h2>Welcome to RNRL TradeHub!</h2>
                    <p>Hello {{sub_user_name}},</p>
                    <p>{{parent_user_name}} has invited you to join their team on RNRL TradeHub.</p>
                    <p><strong>Your login credentials:</strong></p>
                    <ul>
                        <li>Email: {{sub_user_email}}</li>
                        <li>Temporary Password: {{temporary_password}}</li>
                    </ul>
                    <p>Please log in and change your password immediately.</p>
                    <p>Login at: <a href="{{login_url}}">{{login_url}}</a></p>
                    <p>Best regards,<br>RNRL TradeHub Team</p>
                    """,
                    body_text="""
                    Welcome to RNRL TradeHub!
                    
                    Hello {{sub_user_name}},
                    
                    {{parent_user_name}} has invited you to join their team on RNRL TradeHub.
                    
                    Your login credentials:
                    - Email: {{sub_user_email}}
                    - Temporary Password: {{temporary_password}}
                    
                    Please log in and change your password immediately.
                    
                    Login at: {{login_url}}
                    
                    Best regards,
                    RNRL TradeHub Team
                    """,
                    is_active=True
                )
                db.add(template)
                db.commit()
            
            # Render email with variables
            variables = {
                "sub_user_name": sub_user.name,
                "sub_user_email": sub_user.email,
                "parent_user_name": parent_user.name,
                "temporary_password": temporary_password,
                "login_url": "https://tradehub.rnrl.com/login"  # Update with actual URL
            }
            
            subject = template.subject
            body_html = template.body_html
            body_text = template.body_text
            
            # Simple variable replacement
            for key, value in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                body_html = body_html.replace(f"{{{{{key}}}}}", str(value))
                body_text = body_text.replace(f"{{{{{key}}}}}", str(value))
            
            # Log email (actual sending would happen here)
            email_log = models.EmailLog(
                template_id=template.id,
                recipient=sub_user.email,
                subject=subject,
                body=body_html,
                status="pending",
                metadata_json=variables
            )
            db.add(email_log)
            db.commit()
            
            # TODO: Integrate with actual email service (SendGrid, SES, etc.)
            logger.info(f"Invitation email queued for {sub_user.email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset(
        db: Session,
        user: models.User,
        reset_token: str
    ) -> bool:
        """
        Send password reset email.
        
        Business Logic:
        - Use email template
        - Include secure reset link with token
        - Log email for tracking
        
        Args:
            db: Database session
            user: User requesting password reset
            reset_token: Secure token for password reset
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Get or create email template
            template = db.query(models.EmailTemplate).filter(
                models.EmailTemplate.name == "password_reset"
            ).first()
            
            if not template:
                # Create default template
                template = models.EmailTemplate(
                    name="password_reset",
                    category="notification",
                    subject="Reset your RNRL TradeHub password",
                    body_html="""
                    <h2>Password Reset Request</h2>
                    <p>Hello {{user_name}},</p>
                    <p>You requested to reset your password for RNRL TradeHub.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{{reset_url}}">Reset Password</a></p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <p>Best regards,<br>RNRL TradeHub Team</p>
                    """,
                    body_text="""
                    Password Reset Request
                    
                    Hello {{user_name}},
                    
                    You requested to reset your password for RNRL TradeHub.
                    
                    Click the link below to reset your password:
                    {{reset_url}}
                    
                    This link will expire in 24 hours.
                    
                    If you didn't request this, please ignore this email.
                    
                    Best regards,
                    RNRL TradeHub Team
                    """,
                    is_active=True
                )
                db.add(template)
                db.commit()
            
            # Render email with variables
            variables = {
                "user_name": user.name,
                "reset_url": f"https://tradehub.rnrl.com/reset-password?token={reset_token}"
            }
            
            subject = template.subject
            body_html = template.body_html
            body_text = template.body_text
            
            for key, value in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                body_html = body_html.replace(f"{{{{{key}}}}}", str(value))
                body_text = body_text.replace(f"{{{{{key}}}}}", str(value))
            
            # Log email
            email_log = models.EmailLog(
                template_id=template.id,
                recipient=user.email,
                subject=subject,
                body=body_html,
                status="pending",
                metadata_json=variables
            )
            db.add(email_log)
            db.commit()
            
            # TODO: Integrate with actual email service
            logger.info(f"Password reset email queued for {user.email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False
