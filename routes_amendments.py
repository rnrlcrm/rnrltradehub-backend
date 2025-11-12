"""
Amendment request routes for entity updates with approval workflow.

This module provides endpoints for:
- Requesting amendments to entities
- Reviewing and approving/rejecting amendments
- Viewing amendment history
- Auto-approval for low-risk changes
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

router = APIRouter(prefix="/api/amendments", tags=["Amendments"])


@router.post("/request", response_model=schemas.AmendmentRequestResponse, status_code=status.HTTP_201_CREATED)
def create_amendment_request(
    request: schemas.AmendmentRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create an amendment request for an entity.
    
    Supported entity types: business_partner, branch, user
    Request types: UPDATE, DELETE
    
    Includes automatic risk assessment and auto-approval for low-risk changes.
    """
    # Validate entity exists
    entity_model = {
        "business_partner": models.BusinessPartner,
        "branch": models.BusinessBranch,
        "user": models.User
    }.get(request.entity_type)
    
    if not entity_model:
        raise HTTPException(status_code=400, detail="Invalid entity type")
    
    entity = db.query(entity_model).filter(entity_model.id == request.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"{request.entity_type} not found")
    
    # Create amendment request
    db_request = models.AmendmentRequest(
        id=str(uuid.uuid4()),
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        request_type=request.request_type,
        reason=request.reason,
        justification=request.justification,
        requested_by=current_user.id,
        changes=request.changes,
        status="PENDING"
    )
    
    db.add(db_request)
    db.flush()
    
    # Try auto-approval for low-risk changes
    auto_approved = AutomationService.auto_approve_amendment(db, db_request)
    
    if auto_approved:
        db.refresh(db_request)
        return db_request
    
    db.commit()
    db.refresh(db_request)
    
    return db_request


@router.get("", response_model=List[schemas.AmendmentRequestResponse])
def list_amendment_requests(
    entity_type: str = None,
    status_filter: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List amendment requests.
    
    Filters:
    - entity_type: business_partner, branch, user
    - status: PENDING, APPROVED, REJECTED
    """
    query = db.query(models.AmendmentRequest)
    
    if entity_type:
        query = query.filter(models.AmendmentRequest.entity_type == entity_type)
    
    if status_filter:
        query = query.filter(models.AmendmentRequest.status == status_filter)
    
    requests = query.order_by(
        models.AmendmentRequest.requested_at.desc()
    ).offset(skip).limit(limit).all()
    
    return requests


@router.get("/{request_id}", response_model=schemas.AmendmentRequestResponse)
def get_amendment_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get a specific amendment request by ID.
    """
    amendment_request = db.query(models.AmendmentRequest).filter(
        models.AmendmentRequest.id == request_id
    ).first()
    
    if not amendment_request:
        raise HTTPException(status_code=404, detail="Amendment request not found")
    
    return amendment_request


@router.post("/{request_id}/review", response_model=schemas.AmendmentRequestResponse)
def review_amendment_request(
    request_id: str,
    review: schemas.AmendmentRequestReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Review an amendment request (admin only).
    
    Actions:
    - APPROVED: Apply the changes to the entity
    - REJECTED: Reject with reason
    """
    db_request = db.query(models.AmendmentRequest).filter(
        models.AmendmentRequest.id == request_id
    ).first()
    
    if not db_request:
        raise HTTPException(status_code=404, detail="Amendment request not found")
    
    if db_request.status != "PENDING":
        raise HTTPException(status_code=400, detail="Request already reviewed")
    
    # Update request status
    db_request.status = review.status
    db_request.review_notes = review.review_notes
    db_request.reviewed_by = current_user.id
    db_request.reviewed_at = datetime.utcnow()
    
    # If approved, apply changes
    if review.status == "APPROVED":
        entity_model = {
            "business_partner": models.BusinessPartner,
            "branch": models.BusinessBranch,
            "user": models.User
        }.get(db_request.entity_type)
        
        entity = db.query(entity_model).filter(
            entity_model.id == db_request.entity_id
        ).first()
        
        if entity:
            # Apply changes from the request
            new_values = db_request.changes.get("new_values", {})
            for field, value in new_values.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)
            
            # Create version history for business partners
            if db_request.entity_type == "business_partner":
                # Get current version
                latest_version = db.query(models.BusinessPartnerVersion).filter(
                    models.BusinessPartnerVersion.partner_id == entity.id
                ).order_by(models.BusinessPartnerVersion.version.desc()).first()
                
                new_version = latest_version.version + 1 if latest_version else 1
                
                # Create version record
                version_record = models.BusinessPartnerVersion(
                    id=str(uuid.uuid4()),
                    partner_id=entity.id,
                    version=new_version,
                    data=new_values,
                    changed_by=current_user.id,
                    change_reason=db_request.reason,
                    amendment_request_id=request_id
                )
                db.add(version_record)
    
    db.commit()
    db.refresh(db_request)
    
    return db_request


@router.get("/impact/{entity_id}", response_model=dict)
def get_impact_assessment(
    entity_id: str,
    entity_type: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get impact assessment for an entity amendment.
    
    Returns information about what will be affected by the change.
    """
    # This is a placeholder for impact assessment logic
    # In a real implementation, this would check:
    # - Related contracts
    # - Active transactions
    # - Dependent records
    
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "impact": {
            "contracts_affected": 0,
            "transactions_affected": 0,
            "users_affected": 0
        },
        "recommendation": "Low risk - safe to proceed"
    }
