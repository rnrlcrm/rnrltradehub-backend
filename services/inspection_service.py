"""
Quality Inspection Service - Business logic for quality inspection workflows.

Handles commodity-specific inspection flows, status progression,
OCR extraction, and approval workflows.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import (
    QualityInspection, InspectionEvent, SalesContract,
    Inventory, Document, AuditLog, User
)
from schemas import (
    QualityInspectionCreate, QualityInspectionUpdate,
    QualityInspectionApproval, InspectionEventCreate
)


class InspectionService:
    """Service for managing quality inspections."""

    @staticmethod
    def generate_inspection_number(db: Session, org_id: int, fy: str) -> str:
        """Generate unique inspection number."""
        prefix = f"QI-{fy[-2:]}-{org_id}"
        count = db.query(QualityInspection).filter(
            and_(
                QualityInspection.organization_id == org_id,
                QualityInspection.financial_year == fy,
                QualityInspection.inspection_number.like(f"{prefix}%")
            )
        ).count()
        return f"{prefix}-{(count + 1):05d}"

    @staticmethod
    def validate_parameters(commodity_type: str, parameters: Dict) -> Dict[str, Any]:
        """
        Validate inspection parameters based on commodity type.
        
        Each commodity has specific quality parameters that must be checked.
        """
        errors = []
        warnings = []

        # Cotton-specific parameters
        if commodity_type.lower() == 'cotton':
            required = ['staple_length', 'moisture', 'micronaire', 'strength', 'trash']
            for param in required:
                if param not in parameters:
                    errors.append(f"Missing required parameter: {param}")
                elif not isinstance(parameters[param], (int, float)):
                    errors.append(f"Parameter {param} must be numeric")

            # Range validations
            if 'moisture' in parameters:
                if parameters['moisture'] > 15:
                    warnings.append("High moisture content may affect quality")
            if 'trash' in parameters:
                if parameters['trash'] > 5:
                    warnings.append("High trash percentage detected")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    @staticmethod
    def create_inspection(
        db: Session,
        inspection_data: QualityInspectionCreate,
        user_id: int
    ) -> QualityInspection:
        """Create new quality inspection record."""
        # Validate contract exists
        contract = db.query(SalesContract).filter(
            SalesContract.id == inspection_data.contract_id
        ).first()
        if not contract:
            raise ValueError(f"Contract {inspection_data.contract_id} not found")

        # Validate inspector exists
        inspector = db.query(User).filter(User.id == inspection_data.inspector_id).first()
        if not inspector:
            raise ValueError(f"Inspector {inspection_data.inspector_id} not found")

        # Validate parameters (commodity-specific)
        # Note: In production, fetch commodity type from contract
        validation = InspectionService.validate_parameters('cotton', inspection_data.parameters)
        if not validation["valid"]:
            raise ValueError(f"Parameter validation failed: {', '.join(validation['errors'])}")

        # Generate inspection number
        inspection_number = InspectionService.generate_inspection_number(
            db,
            inspection_data.organization_id,
            inspection_data.financial_year
        )

        # Create inspection
        inspection = QualityInspection(
            id=str(uuid4()),
            inspection_number=inspection_number,
            organization_id=inspection_data.organization_id,
            financial_year=inspection_data.financial_year,
            contract_id=inspection_data.contract_id,
            lot_number=inspection_data.lot_number,
            inspection_date=inspection_data.inspection_date,
            inspector_id=inspection_data.inspector_id,
            inspection_location=inspection_data.inspection_location,
            parameters=inspection_data.parameters,
            remarks=inspection_data.remarks,
            status='SCHEDULED'
        )

        db.add(inspection)

        # Create initial event
        event = InspectionEvent(
            id=str(uuid4()),
            inspection_id=inspection.id,
            event_type='SCHEDULED',
            performed_by=user_id,
            event_data={"scheduled_by": user_id},
            notes=f"Inspection scheduled for {inspection_data.inspection_date}",
            event_timestamp=datetime.utcnow()
        )
        db.add(event)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Quality Inspector",
            module="Quality Inspection",
            action="CREATE",
            details=f"Created inspection {inspection_number} for contract {contract.sc_no}"
        )
        db.add(audit)

        db.commit()
        db.refresh(inspection)

        return inspection

    @staticmethod
    def update_inspection_status(
        db: Session,
        inspection_id: str,
        new_status: str,
        user_id: int,
        notes: Optional[str] = None,
        event_data: Optional[Dict] = None
    ) -> QualityInspection:
        """Update inspection status with event tracking."""
        inspection = db.query(QualityInspection).filter(
            QualityInspection.id == inspection_id
        ).first()
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found")

        # Validate status transition
        valid_transitions = {
            'SCHEDULED': ['IN_PROGRESS', 'COMPLETED'],
            'IN_PROGRESS': ['COMPLETED', 'RESAMPLING_REQUIRED'],
            'COMPLETED': ['APPROVED', 'REJECTED', 'RESAMPLING_REQUIRED'],
            'RESAMPLING_REQUIRED': ['IN_PROGRESS'],
            'APPROVED': [],  # Final state
            'REJECTED': []   # Final state
        }

        if new_status not in valid_transitions.get(inspection.status, []):
            raise ValueError(
                f"Invalid status transition from {inspection.status} to {new_status}"
            )

        old_status = inspection.status
        inspection.status = new_status

        # Map status to event type
        status_to_event = {
            'IN_PROGRESS': 'STARTED',
            'COMPLETED': 'COMPLETED',
            'APPROVED': 'APPROVED',
            'REJECTED': 'REJECTED',
            'RESAMPLING_REQUIRED': 'RESAMPLING_ORDERED'
        }

        event_type = status_to_event.get(new_status, 'STARTED')

        # Create status change event
        event = InspectionEvent(
            id=str(uuid4()),
            inspection_id=inspection.id,
            event_type=event_type,
            performed_by=user_id,
            event_data=event_data or {},
            notes=notes or f"Status changed from {old_status} to {new_status}",
            event_timestamp=datetime.utcnow()
        )
        db.add(event)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Quality Inspector",
            module="Quality Inspection",
            action="STATUS_CHANGE",
            details=f"Changed inspection {inspection.inspection_number} status to {new_status}"
        )
        db.add(audit)

        db.commit()
        db.refresh(inspection)

        return inspection

    @staticmethod
    def approve_inspection(
        db: Session,
        inspection_id: str,
        approval_data: QualityInspectionApproval,
        user_id: int
    ) -> QualityInspection:
        """Approve or reject inspection."""
        inspection = db.query(QualityInspection).filter(
            QualityInspection.id == inspection_id
        ).first()
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found")

        if inspection.status != 'COMPLETED':
            raise ValueError(f"Only COMPLETED inspections can be approved/rejected")

        if approval_data.approved:
            inspection.status = 'APPROVED'
            inspection.result = 'PASS'
            inspection.approved_by = user_id
            inspection.approved_at = datetime.utcnow()
            event_type = 'APPROVED'
        else:
            inspection.status = 'REJECTED'
            inspection.result = 'FAIL'
            inspection.rejection_reason = approval_data.rejection_reason
            event_type = 'REJECTED'

        # Create approval/rejection event
        event = InspectionEvent(
            id=str(uuid4()),
            inspection_id=inspection.id,
            event_type=event_type,
            performed_by=user_id,
            event_data={
                "approved": approval_data.approved,
                "rejection_reason": approval_data.rejection_reason
            },
            notes=approval_data.rejection_reason if not approval_data.approved else "Approved",
            event_timestamp=datetime.utcnow()
        )
        db.add(event)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Quality Manager",
            module="Quality Inspection",
            action="APPROVE" if approval_data.approved else "REJECT",
            details=f"{'Approved' if approval_data.approved else 'Rejected'} inspection {inspection.inspection_number}",
            reason=approval_data.rejection_reason
        )
        db.add(audit)

        db.commit()
        db.refresh(inspection)

        return inspection

    @staticmethod
    def link_document(
        db: Session,
        inspection_id: str,
        document_id: str,
        user_id: int
    ) -> QualityInspection:
        """Link inspection report document with OCR extraction."""
        inspection = db.query(QualityInspection).filter(
            QualityInspection.id == inspection_id
        ).first()
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found")

        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        inspection.report_document_id = document_id

        # TODO: Trigger OCR extraction and parameter mapping
        # This would extract data from the document and update inspection.parameters

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Quality Inspector",
            module="Quality Inspection",
            action="LINK_DOCUMENT",
            details=f"Linked document {document_id} to inspection {inspection.inspection_number}"
        )
        db.add(audit)

        db.commit()
        db.refresh(inspection)

        return inspection

    @staticmethod
    def get_inspection_history(
        db: Session,
        contract_id: Optional[str] = None,
        lot_number: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[QualityInspection]:
        """Get inspection history by contract or lot number."""
        query = db.query(QualityInspection)

        if contract_id:
            query = query.filter(QualityInspection.contract_id == contract_id)
        if lot_number:
            query = query.filter(QualityInspection.lot_number == lot_number)

        return query.order_by(
            QualityInspection.inspection_date.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_inspection_events(
        db: Session,
        inspection_id: str
    ) -> List[InspectionEvent]:
        """Get all events for an inspection."""
        return db.query(InspectionEvent).filter(
            InspectionEvent.inspection_id == inspection_id
        ).order_by(InspectionEvent.event_timestamp.asc()).all()
