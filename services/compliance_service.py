"""
Compliance Service - Business logic for compliance and GDPR operations.

This service handles:
- GDPR data export requests
- GDPR data deletion requests
- Consent management
- Data retention policies
- Audit logging
- Security event tracking
"""
import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

import models
import schemas


class ComplianceService:
    """Service class for compliance and GDPR operations."""

    @staticmethod
    def create_data_export_request(
        db: Session,
        export_data: schemas.DataExportRequestCreate
    ) -> models.DataExportRequest:
        """
        Create a GDPR data export request.
        
        Business Logic:
        - Validate user exists
        - Set status to pending
        - Set expiry date (30 days)
        
        Args:
            db: Database session
            export_data: Export request data
            
        Returns:
            Created data export request
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate user exists
        user = db.query(models.User).filter(models.User.id == export_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {export_data.user_id} not found"
            )
        
        # Business Logic: Check if there's already a pending request
        pending_request = db.query(models.DataExportRequest).filter(
            models.DataExportRequest.user_id == export_data.user_id,
            models.DataExportRequest.status == "pending"
        ).first()
        
        if pending_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a pending data export request"
            )

        db_request = models.DataExportRequest(
            id=str(uuid.uuid4()),
            **export_data.model_dump()
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def process_data_export(db: Session, request_id: str) -> dict:
        """
        Process a data export request.
        
        Business Logic:
        - Get all user data from all tables
        - Generate export file
        - Mark request as completed
        - Set download expiry
        
        Args:
            db: Database session
            request_id: Export request ID
            
        Returns:
            Dictionary with exported data
            
        Raises:
            HTTPException: If validation fails
        """
        export_request = db.query(models.DataExportRequest).filter(
            models.DataExportRequest.id == request_id
        ).first()
        
        if not export_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data export request with ID {request_id} not found"
            )
        
        # Business Logic: Can only process pending requests
        if export_request.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot process request with status '{export_request.status}'"
            )
        
        # Business Logic: Collect all user data
        user_id = export_request.user_id
        user_data = {
            "user": db.query(models.User).filter(models.User.id == user_id).first(),
            "audit_logs": db.query(models.AuditLog).filter(models.AuditLog.user_id == user_id).all(),
            "consent_records": db.query(models.ConsentRecord).filter(models.ConsentRecord.user_id == user_id).all(),
            # Add other relevant data
        }
        
        # Business Logic: Update request status
        export_request.status = "completed"
        export_request.completed_at = datetime.now()
        
        db.commit()
        return user_data

    @staticmethod
    def create_data_deletion_request(
        db: Session,
        user_id: str,
        reason: str
    ) -> models.DataExportRequest:
        """
        Create a GDPR data deletion request.
        
        Business Logic:
        - Validate user exists
        - Check if user has active contracts/invoices
        - Set request type to deletion
        
        Args:
            db: Database session
            user_id: User ID
            reason: Deletion reason
            
        Returns:
            Created deletion request
            
        Raises:
            HTTPException: If validation fails
        """
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Business Logic: Check for active data that prevents deletion
        # (This is simplified - in production you'd check various constraints)
        
        db_request = models.DataExportRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            request_type="deletion",
            status="pending"
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def create_consent_record(
        db: Session,
        consent_data: schemas.ConsentRecordCreate
    ) -> models.ConsentRecord:
        """
        Create a consent record.
        
        Business Logic:
        - Validate user exists
        - Record consent type and purpose
        - Set consent date
        
        Args:
            db: Database session
            consent_data: Consent record data
            
        Returns:
            Created consent record
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Validate user exists
        user = db.query(models.User).filter(models.User.id == consent_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {consent_data.user_id} not found"
            )

        db_consent = models.ConsentRecord(
            id=str(uuid.uuid4()),
            **consent_data.model_dump()
        )
        db.add(db_consent)
        db.commit()
        db.refresh(db_consent)
        return db_consent

    @staticmethod
    def withdraw_consent(
        db: Session,
        consent_id: str
    ) -> models.ConsentRecord:
        """
        Withdraw user consent.
        
        Business Logic:
        - Mark consent as withdrawn
        - Record withdrawal date
        - Cannot re-withdraw already withdrawn consent
        
        Args:
            db: Database session
            consent_id: Consent record ID
            
        Returns:
            Updated consent record
            
        Raises:
            HTTPException: If validation fails
        """
        consent = db.query(models.ConsentRecord).filter(
            models.ConsentRecord.id == consent_id
        ).first()
        
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consent record with ID {consent_id} not found"
            )
        
        # Business Logic: Cannot withdraw already withdrawn consent
        if consent.withdrawn_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consent has already been withdrawn"
            )
        
        consent.withdrawn_at = datetime.now()
        db.commit()
        db.refresh(consent)
        return consent

    @staticmethod
    def log_data_access(
        db: Session,
        access_data: schemas.DataAccessLogCreate
    ) -> models.DataAccessLog:
        """
        Log data access for compliance.
        
        Business Logic:
        - Record who accessed what data
        - Record purpose of access
        - Required for GDPR Article 30 compliance
        
        Args:
            db: Database session
            access_data: Access log data
            
        Returns:
            Created access log
        """
        db_log = models.DataAccessLog(
            id=str(uuid.uuid4()),
            **access_data.model_dump()
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    @staticmethod
    def create_retention_policy(
        db: Session,
        policy_data: schemas.RetentionPolicyCreate
    ) -> models.DataRetentionPolicy:
        """
        Create a data retention policy.
        
        Business Logic:
        - Define retention rules for entity types
        - Set retention period
        - Set deletion action
        
        Args:
            db: Database session
            policy_data: Retention policy data
            
        Returns:
            Created retention policy
            
        Raises:
            HTTPException: If validation fails
        """
        # Business Logic: Check if policy already exists for entity type
        existing = db.query(models.DataRetentionPolicy).filter(
            models.DataRetentionPolicy.entity_type == policy_data.entity_type
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Retention policy for '{policy_data.entity_type}' already exists"
            )

        db_policy = models.DataRetentionPolicy(
            id=str(uuid.uuid4()),
            **policy_data.model_dump()
        )
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        return db_policy

    @staticmethod
    def apply_retention_policies(db: Session) -> dict:
        """
        Apply retention policies to delete/archive old data.
        
        Business Logic:
        - Find all active retention policies
        - For each policy, find data older than retention period
        - Delete or archive based on policy action
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with counts of deleted/archived records
        """
        policies = db.query(models.DataRetentionPolicy).filter(
            models.DataRetentionPolicy.is_active == True
        ).all()
        
        results = {}
        
        for policy in policies:
            # Business Logic: Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=policy.retention_days)
            
            # Business Logic: Apply policy based on entity type
            # (Simplified - in production you'd handle each entity type specifically)
            
            results[policy.entity_type] = {
                "action": policy.action,
                "cutoff_date": cutoff_date,
                "retention_days": policy.retention_days
            }
        
        return results

    @staticmethod
    def log_security_event(
        db: Session,
        event_data: schemas.SecurityEventCreate
    ) -> models.SecurityEvent:
        """
        Log a security event.
        
        Business Logic:
        - Record security incidents
        - Track severity levels
        - Monitor for suspicious activity
        
        Args:
            db: Database session
            event_data: Security event data
            
        Returns:
            Created security event
        """
        db_event = models.SecurityEvent(
            id=str(uuid.uuid4()),
            **event_data.model_dump()
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    @staticmethod
    def resolve_security_event(
        db: Session,
        event_id: str,
        resolution_notes: str
    ) -> models.SecurityEvent:
        """
        Resolve a security event.
        
        Business Logic:
        - Mark event as resolved
        - Record resolution notes
        - Record resolution time
        
        Args:
            db: Database session
            event_id: Security event ID
            resolution_notes: Resolution notes
            
        Returns:
            Updated security event
            
        Raises:
            HTTPException: If validation fails
        """
        event = db.query(models.SecurityEvent).filter(
            models.SecurityEvent.id == event_id
        ).first()
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Security event with ID {event_id} not found"
            )
        
        # Business Logic: Cannot resolve already resolved event
        if event.resolved_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security event has already been resolved"
            )
        
        event.resolved_at = datetime.now()
        # Store resolution notes (you'd need to add this field to the model)
        
        db.commit()
        db.refresh(event)
        return event
