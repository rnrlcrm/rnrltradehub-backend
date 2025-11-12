"""
Self-service onboarding routes for business partners.

This module provides endpoints for:
- Submitting onboarding applications
- Checking application status
- Admin review and approval
"""
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from routes_auth import get_current_user
from services.automation_service import AutomationService
from services.validation_service import ValidationService

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


def generate_application_number() -> str:
    """Generate a unique application number."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"APP-{timestamp}"


@router.post("/apply", response_model=schemas.OnboardingApplicationResponse, status_code=status.HTTP_201_CREATED)
def submit_application(
    application: schemas.OnboardingApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a self-service onboarding application.
    
    This endpoint is public (no authentication required) to allow new business partners to apply.
    Includes validation of PAN, GST, phone, and email.
    """
    # Validate the application data
    validation_data = {
        "pan": application.compliance_info.get("pan"),
        "gstin": application.compliance_info.get("gst"),
        "contact_phone": application.contact_info.get("phone"),
        "contact_email": application.contact_info.get("email")
    }
    
    is_valid, errors = ValidationService.validate_business_partner_data(validation_data)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Validation errors: {'; '.join(errors)}"
        )
    
    # Create new application
    db_application = models.OnboardingApplication(
        id=str(uuid.uuid4()),
        application_number=generate_application_number(),
        company_info=application.company_info,
        contact_info=application.contact_info,
        compliance_info=application.compliance_info,
        branch_info=application.branch_info,
        documents=application.documents,
        status="SUBMITTED"
    )
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    # TODO: Send notification email to admin (Phase 4)
    
    return db_application


@router.get("/status/{application_number}", response_model=schemas.OnboardingApplicationResponse)
def check_status(
    application_number: str,
    db: Session = Depends(get_db)
):
    """
    Check the status of an onboarding application.
    
    This endpoint is public to allow applicants to check their status.
    """
    application = db.query(models.OnboardingApplication).filter(
        models.OnboardingApplication.application_number == application_number
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.get("/applications", response_model=List[schemas.OnboardingApplicationResponse])
def list_applications(
    status_filter: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all onboarding applications (admin only).
    
    Filter by status: SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED
    """
    query = db.query(models.OnboardingApplication)
    
    if status_filter:
        query = query.filter(models.OnboardingApplication.status == status_filter)
    
    applications = query.order_by(
        models.OnboardingApplication.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return applications


@router.get("/applications/{application_id}", response_model=schemas.OnboardingApplicationResponse)
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get a specific application by ID (admin only).
    """
    application = db.query(models.OnboardingApplication).filter(
        models.OnboardingApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.post("/applications/{application_id}/review", response_model=schemas.OnboardingApplicationResponse)
def review_application(
    application_id: str,
    review: schemas.OnboardingApplicationReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Review an onboarding application (admin only).
    
    Actions:
    - APPROVED: Auto-create business partner, branches, and user account
    - REJECTED: Reject with reason
    """
    db_application = db.query(models.OnboardingApplication).filter(
        models.OnboardingApplication.id == application_id
    ).first()
    
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if db_application.status not in ["SUBMITTED", "UNDER_REVIEW"]:
        raise HTTPException(status_code=400, detail="Application already processed")
    
    # Update application status
    db_application.status = review.status
    db_application.review_notes = review.review_notes
    db_application.reviewed_by = current_user.id
    db_application.reviewed_at = datetime.utcnow()
    
    # If approved, auto-create partner and user using automation service
    if review.status == "APPROVED":
        result = AutomationService.process_approved_onboarding(
            db=db,
            application=db_application,
            reviewed_by_user_id=current_user.id
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create partner: {result.get('error')}"
            )
    
    db.commit()
    db.refresh(db_application)
    
    # TODO: Send notification email to applicant (Phase 4)
    
    return db_application
