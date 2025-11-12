"""
KYC Scheduler Service - Automated KYC reminder system.

This service handles:
- Daily KYC checks
- Automated reminder emails
- Overdue escalation
- Account locking for severely overdue KYC
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

import models
from services.email_service import EmailService

logger = logging.getLogger(__name__)


class KYCSchedulerService:
    """Service class for KYC automation and reminders."""
    
    @staticmethod
    def check_and_send_reminders(db: Session) -> Dict[str, Any]:
        """
        Check all partners for KYC due dates and send reminders.
        
        This should be run daily (e.g., 9 AM via cron job).
        
        Business Logic:
        - Check partners with KYC due within 30 days
        - Send reminders at 30, 15, 7, 1 days before due
        - Send overdue alerts for past due
        - Escalate severely overdue (>30 days) to admin
        - Lock accounts if severely overdue (>30 days)
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with reminder statistics
        """
        try:
            today = datetime.utcnow()
            stats = {
                "checked": 0,
                "reminders_sent": 0,
                "overdue": 0,
                "locked": 0,
                "errors": 0
            }
            
            # Get all active partners with KYC due date
            partners = db.query(models.BusinessPartner).filter(
                and_(
                    models.BusinessPartner.kyc_due_date.isnot(None),
                    models.BusinessPartner.is_active == True
                )
            ).all()
            
            stats["checked"] = len(partners)
            
            for partner in partners:
                try:
                    days_until_due = (partner.kyc_due_date - today).days
                    
                    # Determine reminder type
                    reminder_type = None
                    if days_until_due == 30:
                        reminder_type = "30_DAYS"
                    elif days_until_due == 15:
                        reminder_type = "15_DAYS"
                    elif days_until_due == 7:
                        reminder_type = "7_DAYS"
                    elif days_until_due == 1:
                        reminder_type = "1_DAY"
                    elif days_until_due < 0:
                        reminder_type = "OVERDUE"
                        stats["overdue"] += 1
                    
                    # Send reminder if applicable
                    if reminder_type:
                        # Check if reminder already sent today
                        existing_reminder = db.query(models.KYCReminderLog).filter(
                            and_(
                                models.KYCReminderLog.partner_id == partner.id,
                                models.KYCReminderLog.reminder_type == reminder_type,
                                models.KYCReminderLog.sent_at >= today.replace(hour=0, minute=0, second=0)
                            )
                        ).first()
                        
                        if not existing_reminder:
                            success = EmailService.send_kyc_reminder(
                                db=db,
                                partner=partner,
                                reminder_type=reminder_type,
                                days_until_due=days_until_due
                            )
                            
                            if success:
                                stats["reminders_sent"] += 1
                    
                    # Handle severely overdue (>30 days past due)
                    if days_until_due < -30:
                        logger.warning(f"Partner {partner.id} KYC is {abs(days_until_due)} days overdue")
                        
                        # Lock account if not already locked
                        if partner.status != "INACTIVE":
                            partner.status = "INACTIVE"
                            db.commit()
                            stats["locked"] += 1
                            logger.info(f"Locked partner account {partner.id} due to severely overdue KYC")
                        
                        # TODO: Send escalation email to admin
                
                except Exception as e:
                    logger.error(f"Error processing partner {partner.id}: {str(e)}")
                    stats["errors"] += 1
                    continue
            
            logger.info(f"KYC reminder run complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"KYC reminder check failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def get_partners_needing_kyc(
        db: Session,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get list of partners that need KYC attention.
        
        Args:
            db: Database session
            days_ahead: Check KYC due within this many days
            
        Returns:
            List of partners with KYC status
        """
        try:
            today = datetime.utcnow()
            future_date = today + timedelta(days=days_ahead)
            
            partners = db.query(models.BusinessPartner).filter(
                and_(
                    models.BusinessPartner.kyc_due_date.isnot(None),
                    models.BusinessPartner.kyc_due_date <= future_date,
                    models.BusinessPartner.is_active == True
                )
            ).all()
            
            result = []
            for partner in partners:
                days_until_due = (partner.kyc_due_date - today).days
                
                if days_until_due < 0:
                    status = "OVERDUE"
                elif days_until_due <= 7:
                    status = "DUE_SOON"
                else:
                    status = "DUE_WITHIN_30_DAYS"
                
                result.append({
                    "partner_id": partner.id,
                    "partner_name": partner.legal_name,
                    "kyc_due_date": partner.kyc_due_date,
                    "days_until_due": days_until_due,
                    "status": status,
                    "contact_email": partner.contact_email
                })
            
            # Sort by urgency (overdue first)
            result.sort(key=lambda x: x["days_until_due"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting partners needing KYC: {str(e)}")
            return []
    
    @staticmethod
    def update_kyc_status(db: Session, partner_id: str) -> bool:
        """
        Update KYC status for a partner based on due date.
        
        Args:
            db: Database session
            partner_id: Partner ID
            
        Returns:
            True if updated successfully
        """
        try:
            partner = db.query(models.BusinessPartner).filter(
                models.BusinessPartner.id == partner_id
            ).first()
            
            if not partner or not partner.kyc_due_date:
                return False
            
            today = datetime.utcnow()
            days_until_due = (partner.kyc_due_date - today).days
            
            # Update latest KYC verification status
            latest_kyc = db.query(models.KYCVerification).filter(
                models.KYCVerification.partner_id == partner_id
            ).order_by(models.KYCVerification.verification_date.desc()).first()
            
            if latest_kyc:
                if days_until_due < 0:
                    latest_kyc.status = "OVERDUE"
                elif days_until_due <= 7:
                    latest_kyc.status = "DUE_SOON"
                else:
                    latest_kyc.status = "CURRENT"
                
                db.commit()
                logger.info(f"Updated KYC status for partner {partner_id} to {latest_kyc.status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating KYC status: {str(e)}")
            return False
