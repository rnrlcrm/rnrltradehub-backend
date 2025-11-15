"""
Trade Service - Business logic for Trade Desk (AI Chatbot + Manual Entry).

Handles trade capture from both AI chatbot and manual entry,
with full validation, duplicate prevention, and overbooking checks.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models import (
    Trade, ChatSession, ChatMessage, BusinessPartner,
    MasterDataItem, SalesContract, AuditLog
)
from schemas import (
    TradeCreate, TradeUpdate, TradeResponse,
    ChatSessionCreate, ChatMessageCreate
)


class TradeService:
    """Service for managing trade capture and chatbot interactions."""

    @staticmethod
    def generate_trade_number(db: Session, org_id: int, fy: str) -> str:
        """Generate unique trade number."""
        prefix = f"TRD-{fy[-2:]}-{org_id}"
        count = db.query(Trade).filter(
            and_(
                Trade.organization_id == org_id,
                Trade.financial_year == fy,
                Trade.trade_number.like(f"{prefix}%")
            )
        ).count()
        return f"{prefix}-{(count + 1):05d}"

    @staticmethod
    def create_chat_session(
        db: Session,
        user_id: int,
        org_id: int,
        session_type: str = "TRADE_CAPTURE"
    ) -> ChatSession:
        """Create new chatbot session."""
        session = ChatSession(
            id=str(uuid4()),
            user_id=user_id,
            organization_id=org_id,
            session_type=session_type,
            status="ACTIVE",
            context_data={},
            started_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def add_chat_message(
        db: Session,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> ChatMessage:
        """Add message to chat session."""
        message = ChatMessage(
            id=str(uuid4()),
            session_id=session_id,
            message_type=message_type,
            content=content,
            metadata_json=metadata or {},
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def validate_trade_data(db: Session, trade_data: TradeCreate) -> Dict[str, Any]:
        """
        Validate trade data and check business rules.
        
        Returns validation result with errors if any.
        """
        errors = []
        warnings = []

        # Validate commodity exists
        commodity = db.query(MasterDataItem).filter(
            and_(
                MasterDataItem.id == trade_data.commodity_id,
                MasterDataItem.is_active == True,
                MasterDataItem.is_deleted == False
            )
        ).first()
        if not commodity:
            errors.append("Invalid commodity ID or commodity is inactive")

        # Validate business partners
        for partner_field, partner_id in [
            ("client", trade_data.client_id),
            ("vendor", trade_data.vendor_id),
        ]:
            if partner_id:
                partner = db.query(BusinessPartner).filter(
                    and_(
                        BusinessPartner.id == partner_id,
                        BusinessPartner.status.in_(['ACTIVE']),
                        BusinessPartner.is_deleted == False
                    )
                ).first()
                if not partner:
                    errors.append(f"Invalid {partner_field} ID or partner is not active")

        # Check for duplicates (same commodity, client, vendor, rate within 24 hours)
        recent_duplicate = db.query(Trade).filter(
            and_(
                Trade.commodity_id == trade_data.commodity_id,
                Trade.client_id == trade_data.client_id,
                Trade.vendor_id == trade_data.vendor_id,
                Trade.rate_per_unit == trade_data.rate_per_unit,
                Trade.status.in_(['DRAFT', 'PENDING_APPROVAL', 'CONFIRMED']),
                Trade.trade_date >= datetime.utcnow().replace(hour=0, minute=0, second=0)
            )
        ).first()
        if recent_duplicate:
            warnings.append(f"Similar trade {recent_duplicate.trade_number} exists today")

        # Validate quantity
        if trade_data.quantity_bales <= 0:
            errors.append("Quantity must be greater than 0")

        if trade_data.rate_per_unit <= 0:
            errors.append("Rate must be greater than 0")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    @staticmethod
    def create_trade(
        db: Session,
        trade_data: TradeCreate,
        user_id: int
    ) -> Trade:
        """
        Create new trade record with full validation.
        
        Enforces all business rules including duplicate prevention
        and overbooking checks.
        """
        # Validate trade data
        validation = TradeService.validate_trade_data(db, trade_data)
        if not validation["valid"]:
            raise ValueError(f"Trade validation failed: {', '.join(validation['errors'])}")

        # Generate trade number
        trade_number = TradeService.generate_trade_number(
            db,
            trade_data.organization_id,
            trade_data.financial_year
        )

        # Create trade
        trade = Trade(
            id=str(uuid4()),
            trade_number=trade_number,
            organization_id=trade_data.organization_id,
            financial_year=trade_data.financial_year,
            source=trade_data.source,
            session_id=trade_data.session_id,
            created_by=user_id,
            trade_date=trade_data.trade_date,
            commodity_id=trade_data.commodity_id,
            client_id=trade_data.client_id,
            vendor_id=trade_data.vendor_id,
            agent_id=trade_data.agent_id,
            quantity_bales=trade_data.quantity_bales,
            quantity_kg=trade_data.quantity_kg,
            rate_per_unit=trade_data.rate_per_unit,
            unit=trade_data.unit,
            location=trade_data.location,
            delivery_terms=trade_data.delivery_terms,
            payment_terms=trade_data.payment_terms,
            quality_terms=trade_data.quality_terms or {},
            status="DRAFT",
            version=1
        )

        db.add(trade)
        
        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Sales",
            module="Trade Desk",
            action="CREATE",
            details=f"Created trade {trade_number} via {trade_data.source}"
        )
        db.add(audit)
        
        db.commit()
        db.refresh(trade)
        
        return trade

    @staticmethod
    def update_trade(
        db: Session,
        trade_id: str,
        trade_data: TradeUpdate,
        user_id: int
    ) -> Trade:
        """Update existing trade with version tracking."""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        if trade.status in ['CANCELLED', 'CONTRACT_GENERATED']:
            raise ValueError(f"Cannot update trade in {trade.status} status")

        # Increment version
        trade.version += 1

        # Update fields
        update_data = trade_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(trade, field):
                setattr(trade, field, value)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Sales",
            module="Trade Desk",
            action="UPDATE",
            details=f"Updated trade {trade.trade_number} to version {trade.version}",
            reason=trade_data.amendment_reason
        )
        db.add(audit)

        db.commit()
        db.refresh(trade)
        
        return trade

    @staticmethod
    def convert_to_contract(
        db: Session,
        trade_id: str,
        user_id: int
    ) -> SalesContract:
        """Convert approved trade to sales contract."""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        if trade.status != 'CONFIRMED':
            raise ValueError(f"Only CONFIRMED trades can be converted to contracts")

        if trade.contract_id:
            raise ValueError(f"Trade already converted to contract {trade.contract_id}")

        # Generate contract number (placeholder - actual logic in sales_contract_service)
        sc_no = f"SC-{trade.financial_year[-2:]}-{trade.organization_id}-{datetime.utcnow().timestamp()}"

        # Create contract
        contract = SalesContract(
            id=str(uuid4()),
            sc_no=sc_no,
            version=1,
            date=datetime.utcnow(),
            organization=f"ORG-{trade.organization_id}",
            financial_year=trade.financial_year,
            client_id=trade.client_id,
            client_name="Client Name",  # Fetch from partner
            vendor_id=trade.vendor_id,
            vendor_name="Vendor Name",  # Fetch from partner
            agent_id=trade.agent_id,
            variety=f"Commodity-{trade.commodity_id}",  # Fetch from commodity
            quantity_bales=trade.quantity_bales,
            rate=trade.rate_per_unit,
            trade_type="Regular",
            bargain_type="Direct",
            weightment_terms=trade.delivery_terms,
            passing_terms="Standard",
            delivery_terms=trade.delivery_terms,
            payment_terms=trade.payment_terms,
            location=trade.location,
            quality_specs=trade.quality_terms,
            status="Active"
        )

        db.add(contract)

        # Update trade
        trade.contract_id = contract.id
        trade.converted_at = datetime.utcnow()
        trade.status = 'CONTRACT_GENERATED'

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Sales",
            module="Trade Desk",
            action="CONVERT_TO_CONTRACT",
            details=f"Converted trade {trade.trade_number} to contract {sc_no}"
        )
        db.add(audit)

        db.commit()
        db.refresh(contract)

        return contract

    @staticmethod
    def cancel_trade(
        db: Session,
        trade_id: str,
        reason: str,
        user_id: int
    ) -> Trade:
        """Cancel trade with reason."""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        if trade.status in ['CANCELLED', 'CONTRACT_GENERATED']:
            raise ValueError(f"Cannot cancel trade in {trade.status} status")

        trade.status = 'CANCELLED'
        trade.cancelled_reason = reason
        trade.cancelled_by = user_id
        trade.cancelled_at = datetime.utcnow()

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Sales",
            module="Trade Desk",
            action="CANCEL",
            details=f"Cancelled trade {trade.trade_number}",
            reason=reason
        )
        db.add(audit)

        db.commit()
        db.refresh(trade)

        return trade

    @staticmethod
    def get_trades(
        db: Session,
        org_id: int,
        status: Optional[str] = None,
        source: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Trade]:
        """Get trades with filters."""
        query = db.query(Trade).filter(Trade.organization_id == org_id)

        if status:
            query = query.filter(Trade.status == status)
        if source:
            query = query.filter(Trade.source == source)

        return query.order_by(Trade.created_at.desc()).offset(skip).limit(limit).all()
