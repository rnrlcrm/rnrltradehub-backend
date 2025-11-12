"""
Automation Service - Auto-creation and approval workflows.

This service handles:
- User auto-creation when business partner is approved
- Auto-approval for low-risk changes
- Password generation
- Account initialization
"""
import uuid
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging

import models
import schemas
from services.email_service import EmailService
from services.user_service import UserService

logger = logging.getLogger(__name__)


class AutomationService:
    """Service class for automated workflows."""
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length (default 12)
            
        Returns:
            Secure random password
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def calculate_risk_score(entity_type: str, changes: Dict[str, Any]) -> int:
        """
        Calculate risk score for an amendment request.
        
        Risk Scoring:
        - 0-20: Low risk (auto-approve)
        - 21-50: Medium risk (requires review)
        - 51-100: High risk (requires admin approval)
        
        Args:
            entity_type: Type of entity being changed
            changes: Dictionary of changes with old/new values
            
        Returns:
            Risk score (0-100)
        """
        risk_score = 0
        
        # Base risk by entity type
        entity_risk = {
            "business_partner": 30,
            "branch": 20,
            "user": 25
        }
        risk_score += entity_risk.get(entity_type, 50)
        
        # Risk based on fields changed
        high_risk_fields = ["pan", "gstin", "bank_account_no", "legal_name"]
        medium_risk_fields = ["contact_email", "contact_phone", "address"]
        low_risk_fields = ["branch_name", "notes", "description"]
        
        new_values = changes.get("new_values", {})
        
        for field in new_values.keys():
            if field in high_risk_fields:
                risk_score += 30
            elif field in medium_risk_fields:
                risk_score += 10
            elif field in low_risk_fields:
                risk_score += 5
        
        # Cap at 100
        return min(risk_score, 100)
    
    @staticmethod
    def auto_approve_amendment(
        db: Session,
        amendment_request: models.AmendmentRequest
    ) -> bool:
        """
        Auto-approve amendment if risk score is low enough.
        
        Business Logic:
        - Calculate risk score
        - If score < 20, auto-approve
        - Otherwise, require manual review
        
        Args:
            db: Database session
            amendment_request: Amendment request to evaluate
            
        Returns:
            True if auto-approved, False if manual review needed
        """
        try:
            # Calculate risk score
            risk_score = AutomationService.calculate_risk_score(
                amendment_request.entity_type,
                amendment_request.changes
            )
            
            # Store risk score
            if not amendment_request.impact_assessment:
                amendment_request.impact_assessment = {}
            amendment_request.impact_assessment["risk_score"] = risk_score
            amendment_request.impact_assessment["auto_evaluated"] = True
            amendment_request.impact_assessment["evaluated_at"] = datetime.utcnow().isoformat()
            
            # Auto-approve if low risk
            if risk_score < 20:
                amendment_request.status = "APPROVED"
                amendment_request.review_notes = f"Auto-approved (risk score: {risk_score})"
                amendment_request.reviewed_at = datetime.utcnow()
                
                # Apply changes
                entity_model = {
                    "business_partner": models.BusinessPartner,
                    "branch": models.BusinessBranch,
                    "user": models.User
                }.get(amendment_request.entity_type)
                
                if entity_model:
                    entity = db.query(entity_model).filter(
                        entity_model.id == amendment_request.entity_id
                    ).first()
                    
                    if entity:
                        new_values = amendment_request.changes.get("new_values", {})
                        for field, value in new_values.items():
                            if hasattr(entity, field):
                                setattr(entity, field, value)
                
                db.commit()
                logger.info(f"Auto-approved amendment {amendment_request.id} with risk score {risk_score}")
                return True
            else:
                logger.info(f"Amendment {amendment_request.id} requires manual review (risk score: {risk_score})")
                return False
                
        except Exception as e:
            logger.error(f"Error in auto-approval: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def create_user_for_partner(
        db: Session,
        partner: models.BusinessPartner,
        approved_by_user_id: Optional[int] = None
    ) -> Optional[models.User]:
        """
        Automatically create user account when business partner is approved.
        
        Business Logic:
        1. Generate secure password
        2. Create user with partner link
        3. Assign to all partner branches
        4. Set first login flag
        5. Send welcome email with credentials
        
        Args:
            db: Database session
            partner: Approved business partner
            approved_by_user_id: ID of user who approved the partner
            
        Returns:
            Created user or None if failed
        """
        try:
            # Generate secure password
            temp_password = AutomationService.generate_secure_password()
            
            # Create user
            user = models.User(
                name=partner.contact_person,
                email=partner.contact_email,
                password_hash=UserService.hash_password(temp_password),
                user_type_new="business_partner",
                business_partner_id=partner.id,
                is_first_login=True,
                is_active=True,
                password_expiry_date=datetime.utcnow() + timedelta(days=90)
            )
            db.add(user)
            db.flush()
            
            # Assign user to all partner branches
            branches = db.query(models.BusinessBranch).filter(
                models.BusinessBranch.partner_id == partner.id,
                models.BusinessBranch.is_active == True
            ).all()
            
            for branch in branches:
                user_branch = models.UserBranch(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    branch_id=branch.id
                )
                db.add(user_branch)
            
            db.commit()
            
            # Send welcome email (will be implemented in Phase 4)
            # EmailService.send_welcome_email(
            #     db=db,
            #     user=user,
            #     partner=partner,
            #     temporary_password=temp_password
            # )
            logger.info(f"Welcome email queued for {user.email} (temp password: {temp_password})")
            
            # Log user creation in audit
            audit_log = models.UserAuditLog(
                user_id=user.id,
                action="auto_created",
                entity_type="business_partner",
                entity_id=partner.id,
                details={
                    "created_from": "partner_approval",
                    "approved_by": approved_by_user_id
                }
            )
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Auto-created user {user.id} for partner {partner.id}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to auto-create user for partner {partner.id}: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def process_approved_onboarding(
        db: Session,
        application: models.OnboardingApplication,
        reviewed_by_user_id: int
    ) -> Dict[str, Any]:
        """
        Process an approved onboarding application.
        
        Business Logic:
        1. Create business partner
        2. Create branches if provided
        3. Create user account
        4. Send notification emails
        
        Args:
            db: Database session
            application: Approved onboarding application
            reviewed_by_user_id: ID of user who approved
            
        Returns:
            Dictionary with created entities
        """
        try:
            company_info = application.company_info
            contact_info = application.contact_info
            compliance_info = application.compliance_info
            branch_info = application.branch_info or {}
            
            # Create business partner
            partner = models.BusinessPartner(
                id=str(uuid.uuid4()),
                bp_code=f"BP{datetime.now().strftime('%Y%m%d%H%M%S')}",
                legal_name=company_info.get("legal_name", company_info.get("company_name")),
                organization=company_info.get("company_name"),
                business_type=company_info.get("business_type", "BUYER"),
                status="ACTIVE",
                contact_person=contact_info.get("contact_person"),
                contact_email=contact_info.get("email"),
                contact_phone=contact_info.get("phone"),
                address_line1=company_info.get("address", {}).get("line1", ""),
                address_line2=company_info.get("address", {}).get("line2", ""),
                city=company_info.get("address", {}).get("city", ""),
                state=company_info.get("address", {}).get("state", ""),
                pincode=company_info.get("address", {}).get("pincode", ""),
                country=company_info.get("address", {}).get("country", "India"),
                pan=compliance_info.get("pan"),
                gstin=compliance_info.get("gst"),
                pan_doc_url=compliance_info.get("pan_doc_url"),
                gst_doc_url=compliance_info.get("gst_doc_url")
            )
            db.add(partner)
            db.flush()
            
            # Create head office branch if branch info provided
            if branch_info:
                branch = models.BusinessBranch(
                    id=str(uuid.uuid4()),
                    partner_id=partner.id,
                    branch_code="HO",
                    branch_name=branch_info.get("branch_name", "Head Office"),
                    state=branch_info.get("state", company_info.get("address", {}).get("state", "")),
                    gst_number=compliance_info.get("gst"),
                    address=branch_info.get("address", company_info.get("address", {})),
                    is_head_office=True,
                    is_active=True
                )
                db.add(branch)
            
            db.commit()
            
            # Create user for partner
            user = AutomationService.create_user_for_partner(
                db=db,
                partner=partner,
                approved_by_user_id=reviewed_by_user_id
            )
            
            return {
                "partner_id": partner.id,
                "user_id": user.id if user else None,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to process approved onboarding: {str(e)}")
            db.rollback()
            return {
                "status": "error",
                "error": str(e)
            }
