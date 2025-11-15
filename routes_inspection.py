"""
Quality Inspection API Routes.

Provides endpoints for:
- Quality inspection CRUD
- Inspection status management
- Inspection event tracking
- Document linking with OCR
- Inspection history queries
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    QualityInspectionCreate, QualityInspectionUpdate,
    QualityInspectionResponse, QualityInspectionApproval,
    InspectionEventCreate, InspectionEventResponse
)
from services.inspection_service import InspectionService
from models import QualityInspection

router = APIRouter(prefix="/api/quality-inspections", tags=["Quality Inspection"])


# ============================================================================
# INSPECTION CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=QualityInspectionResponse)
def create_inspection(
    inspection: QualityInspectionCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Create new quality inspection.
    
    Validates:
    - Contract exists
    - Inspector exists
    - Parameters are valid for commodity type
    """
    try:
        new_inspection = InspectionService.create_inspection(
            db=db,
            inspection_data=inspection,
            user_id=user_id
        )
        return new_inspection
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[QualityInspectionResponse])
def list_inspections(
    org_id: int,
    status: Optional[str] = Query(None),
    contract_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List quality inspections with filters.
    
    Status options:
    - SCHEDULED
    - IN_PROGRESS
    - COMPLETED
    - APPROVED
    - REJECTED
    - RESAMPLING_REQUIRED
    """
    query = db.query(QualityInspection).filter(
        QualityInspection.organization_id == org_id
    )
    
    if status:
        query = query.filter(QualityInspection.status == status)
    if contract_id:
        query = query.filter(QualityInspection.contract_id == contract_id)
    
    inspections = query.order_by(
        QualityInspection.inspection_date.desc()
    ).offset(skip).limit(limit).all()
    
    return inspections


@router.get("/{inspection_id}", response_model=QualityInspectionResponse)
def get_inspection(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """Get inspection by ID."""
    inspection = db.query(QualityInspection).filter(
        QualityInspection.id == inspection_id
    ).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.put("/{inspection_id}", response_model=QualityInspectionResponse)
def update_inspection(
    inspection_id: str,
    inspection_update: QualityInspectionUpdate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Update inspection details."""
    inspection = db.query(QualityInspection).filter(
        QualityInspection.id == inspection_id
    ).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    update_data = inspection_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(inspection, field):
            setattr(inspection, field, value)
    
    db.commit()
    db.refresh(inspection)
    return inspection


# ============================================================================
# STATUS MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/{inspection_id}/start")
def start_inspection(
    inspection_id: str,
    user_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Start inspection (SCHEDULED → IN_PROGRESS).
    """
    try:
        inspection = InspectionService.update_inspection_status(
            db=db,
            inspection_id=inspection_id,
            new_status='IN_PROGRESS',
            user_id=user_id,
            notes=notes
        )
        return {
            "message": "Inspection started",
            "inspection_id": inspection_id,
            "status": inspection.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{inspection_id}/complete")
def complete_inspection(
    inspection_id: str,
    user_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Complete inspection (IN_PROGRESS → COMPLETED).
    """
    try:
        inspection = InspectionService.update_inspection_status(
            db=db,
            inspection_id=inspection_id,
            new_status='COMPLETED',
            user_id=user_id,
            notes=notes
        )
        return {
            "message": "Inspection completed",
            "inspection_id": inspection_id,
            "status": inspection.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{inspection_id}/approve")
def approve_inspection(
    inspection_id: str,
    approval: QualityInspectionApproval,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Approve or reject inspection (COMPLETED → APPROVED/REJECTED).
    
    Requires manager approval.
    """
    try:
        inspection = InspectionService.approve_inspection(
            db=db,
            inspection_id=inspection_id,
            approval_data=approval,
            user_id=user_id
        )
        return {
            "message": "Approved" if approval.approved else "Rejected",
            "inspection_id": inspection_id,
            "status": inspection.status,
            "result": inspection.result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{inspection_id}/request-resampling")
def request_resampling(
    inspection_id: str,
    user_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    Request resampling (COMPLETED → RESAMPLING_REQUIRED).
    """
    try:
        inspection = InspectionService.update_inspection_status(
            db=db,
            inspection_id=inspection_id,
            new_status='RESAMPLING_REQUIRED',
            user_id=user_id,
            notes=reason
        )
        return {
            "message": "Resampling requested",
            "inspection_id": inspection_id,
            "status": inspection.status,
            "reason": reason
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EVENT TRACKING ENDPOINTS
# ============================================================================

@router.get("/{inspection_id}/events", response_model=List[InspectionEventResponse])
def get_inspection_events(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """Get all events for an inspection."""
    events = InspectionService.get_inspection_events(db=db, inspection_id=inspection_id)
    return events


@router.post("/{inspection_id}/events", response_model=InspectionEventResponse)
def add_inspection_event(
    inspection_id: str,
    event: InspectionEventCreate,
    db: Session = Depends(get_db)
):
    """Add custom event to inspection (e.g., sample collected, tested)."""
    from models import InspectionEvent
    from uuid import uuid4
    from datetime import datetime
    
    new_event = InspectionEvent(
        id=str(uuid4()),
        inspection_id=inspection_id,
        event_type=event.event_type,
        performed_by=event.performed_by,
        event_data=event.event_data or {},
        notes=event.notes,
        event_timestamp=datetime.utcnow()
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return new_event


# ============================================================================
# DOCUMENT & OCR ENDPOINTS
# ============================================================================

@router.post("/{inspection_id}/link-document")
def link_inspection_document(
    inspection_id: str,
    document_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Link inspection report document and trigger OCR extraction.
    
    OCR will extract quality parameters from the document
    and update the inspection record.
    """
    try:
        inspection = InspectionService.link_document(
            db=db,
            inspection_id=inspection_id,
            document_id=document_id,
            user_id=user_id
        )
        return {
            "message": "Document linked successfully",
            "inspection_id": inspection_id,
            "document_id": document_id,
            "ocr_status": "pending"  # In production, trigger OCR job
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HISTORY & REPORTING ENDPOINTS
# ============================================================================

@router.get("/history/by-contract/{contract_id}", response_model=List[QualityInspectionResponse])
def get_inspection_history_by_contract(
    contract_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get inspection history for a specific contract."""
    inspections = InspectionService.get_inspection_history(
        db=db,
        contract_id=contract_id,
        skip=skip,
        limit=limit
    )
    return inspections


@router.get("/history/by-lot/{lot_number}", response_model=List[QualityInspectionResponse])
def get_inspection_history_by_lot(
    lot_number: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get inspection history for a specific lot."""
    inspections = InspectionService.get_inspection_history(
        db=db,
        lot_number=lot_number,
        skip=skip,
        limit=limit
    )
    return inspections


@router.get("/stats/by-result")
def get_inspection_stats(
    org_id: int,
    db: Session = Depends(get_db)
):
    """Get inspection statistics by result."""
    from sqlalchemy import func
    
    stats = db.query(
        QualityInspection.result,
        func.count(QualityInspection.id).label('count')
    ).filter(
        QualityInspection.organization_id == org_id
    ).group_by(QualityInspection.result).all()
    
    return [
        {
            "result": stat.result or "PENDING",
            "count": stat.count
        }
        for stat in stats
    ]


@router.get("/pending-approvals", response_model=List[QualityInspectionResponse])
def get_pending_approvals(
    org_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get inspections pending approval."""
    inspections = db.query(QualityInspection).filter(
        QualityInspection.organization_id == org_id,
        QualityInspection.status == 'COMPLETED'
    ).order_by(
        QualityInspection.inspection_date.desc()
    ).offset(skip).limit(limit).all()
    
    return inspections
