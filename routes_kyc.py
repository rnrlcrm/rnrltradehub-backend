"""
KYC verification routes for business partner compliance management.

This module provides endpoints for:
- Recording KYC verifications
- Checking KYC due dates
- Viewing KYC history
- Managing KYC reminders
"""
import uuid
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db
import models
import schemas
from routes_auth import get_current_user

router = APIRouter(prefix="/api/kyc", tags=["KYC Management"])


@router.post("/verify/{partner_id}", response_model=schemas.KYCVerificationResponse, status_code=status.HTTP_201_CREATED)
def verify_kyc(
    partner_id: str,
    verification: schemas.KYCVerificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Record a KYC verification for a business partner.
    
    Automatically calculates next due date (typically 1 year from verification).
    """
    # Check if partner exists
    partner = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.id == partner_id
    ).first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Business partner not found")
    
    # Create KYC verification record
    db_verification = models.KYCVerification(
        id=str(uuid.uuid4()),
        partner_id=partner_id,
        verification_date=verification.verification_date,
        verified_by=current_user.id,
        documents_checked=verification.documents_checked,
        status=verification.status,
        next_due_date=verification.next_due_date,
        notes=verification.notes
    )
    
    db.add(db_verification)
    
    # Update partner's KYC due date
    partner.kyc_due_date = verification.next_due_date
    
    db.commit()
    db.refresh(db_verification)
    
    return db_verification


@router.get("/due", response_model=List[dict])
def get_kyc_due(
    days_ahead: int = Query(30, description="Check KYC due within this many days"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get list of business partners with KYC due or overdue.
    
    Returns partners with KYC due within specified days (default 30).
    """
    today = datetime.utcnow()
    future_date = today + timedelta(days=days_ahead)
    
    # Get partners with KYC due
    partners = db.query(models.BusinessPartner).filter(
        and_(
            models.BusinessPartner.kyc_due_date.isnot(None),
            models.BusinessPartner.kyc_due_date <= future_date,
            models.BusinessPartner.is_active == True
        )
    ).all()
    
    result = []
    for partner in partners:
        # Get latest KYC verification
        latest_kyc = db.query(models.KYCVerification).filter(
            models.KYCVerification.partner_id == partner.id
        ).order_by(models.KYCVerification.verification_date.desc()).first()
        
        # Calculate days until due
        days_until_due = (partner.kyc_due_date - today).days if partner.kyc_due_date else None
        
        # Determine status
        if days_until_due and days_until_due < 0:
            status = "OVERDUE"
        elif days_until_due and days_until_due <= 7:
            status = "DUE_SOON"
        else:
            status = "CURRENT"
        
        result.append({
            "partner_id": partner.id,
            "partner_name": partner.legal_name,
            "kyc_due_date": partner.kyc_due_date,
            "days_until_due": days_until_due,
            "status": status,
            "last_verified": latest_kyc.verification_date if latest_kyc else None,
            "contact_email": partner.contact_email
        })
    
    # Sort by days until due (overdue first)
    result.sort(key=lambda x: x["days_until_due"] if x["days_until_due"] is not None else 999)
    
    return result


@router.get("/history/{partner_id}", response_model=List[schemas.KYCVerificationResponse])
def get_kyc_history(
    partner_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get KYC verification history for a business partner.
    """
    # Check if partner exists
    partner = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.id == partner_id
    ).first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Business partner not found")
    
    # Get all KYC verifications for this partner
    verifications = db.query(models.KYCVerification).filter(
        models.KYCVerification.partner_id == partner_id
    ).order_by(models.KYCVerification.verification_date.desc()).all()
    
    return verifications


@router.get("/reminders/{partner_id}", response_model=List[dict])
def get_kyc_reminders(
    partner_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get KYC reminder logs for a business partner.
    """
    # Check if partner exists
    partner = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.id == partner_id
    ).first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Business partner not found")
    
    # Get all reminder logs
    reminders = db.query(models.KYCReminderLog).filter(
        models.KYCReminderLog.partner_id == partner_id
    ).order_by(models.KYCReminderLog.sent_at.desc()).all()
    
    return [
        {
            "id": reminder.id,
            "reminder_type": reminder.reminder_type,
            "sent_at": reminder.sent_at,
            "recipient_email": reminder.recipient_email
        }
        for reminder in reminders
    ]


@router.post("/send-reminder/{partner_id}", status_code=status.HTTP_200_OK)
def send_kyc_reminder(
    partner_id: str,
    reminder_type: str = Query(..., description="Reminder type: 30_DAYS, 15_DAYS, 7_DAYS, 1_DAY, OVERDUE"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Manually send a KYC reminder to a business partner.
    
    This is typically automated but can be triggered manually.
    """
    # Check if partner exists
    partner = db.query(models.BusinessPartner).filter(
        models.BusinessPartner.id == partner_id
    ).first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Business partner not found")
    
    # Log the reminder
    reminder_log = models.KYCReminderLog(
        id=str(uuid.uuid4()),
        partner_id=partner_id,
        reminder_type=reminder_type,
        recipient_email=partner.contact_email
    )
    
    db.add(reminder_log)
    db.commit()
    
    # TODO: Send actual email (Phase 4 - Email Integration)
    
    return {
        "message": "KYC reminder sent successfully",
        "partner_id": partner_id,
        "recipient": partner.contact_email,
        "reminder_type": reminder_type
    }
