"""
Scheduler routes for automated background jobs.

This module provides endpoints for:
- KYC reminder scheduler (daily cron job)
- Other scheduled tasks
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
import os

from database import get_db
from services.kyc_scheduler_service import KYCSchedulerService

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])

# Cron job secret for authentication
CRON_SECRET = os.getenv("CRON_SECRET", "change-this-in-production")


def verify_cron_auth(x_cron_secret: Optional[str] = Header(None)):
    """Verify cron job authentication."""
    if x_cron_secret != CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret"
        )
    return True


@router.post("/kyc-reminders")
def run_kyc_reminders(
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_cron_auth)
):
    """
    Run KYC reminder checks and send emails.
    
    This endpoint should be called daily (e.g., 9 AM) by Cloud Scheduler.
    
    Cloud Scheduler Configuration:
    - Schedule: 0 9 * * * (Daily at 9 AM)
    - Target: POST https://erp-nonprod-backend-502095789065.us-central1.run.app/api/scheduler/kyc-reminders
    - Headers: X-Cron-Secret: <secret>
    
    Returns:
        Statistics about reminders sent
    """
    result = KYCSchedulerService.check_and_send_reminders(db)
    
    return {
        "status": "success",
        "message": "KYC reminder check completed",
        "stats": result
    }


@router.get("/kyc-status")
def get_kyc_status(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_cron_auth)
):
    """
    Get current KYC status for all partners.
    
    This endpoint can be used for monitoring and alerts.
    
    Args:
        days_ahead: Check KYC due within this many days
        
    Returns:
        List of partners needing KYC attention
    """
    partners = KYCSchedulerService.get_partners_needing_kyc(db, days_ahead)
    
    return {
        "status": "success",
        "total": len(partners),
        "partners": partners
    }
