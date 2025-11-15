"""
Logistics Service - Business logic for delivery management.

Handles delivery order creation, transporter assignment,
status tracking, and event logging.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import (
    DeliveryOrder, DeliveryEvent, Transporter,
    SalesContract, Invoice, AuditLog, User
)
from schemas import (
    DeliveryOrderCreate, DeliveryOrderUpdate,
    DeliveryEventCreate, TransporterCreate, TransporterUpdate
)


class LogisticsService:
    """Service for managing delivery orders and logistics."""

    @staticmethod
    def generate_do_number(db: Session, org_id: int, fy: str) -> str:
        """Generate unique delivery order number."""
        prefix = f"DO-{fy[-2:]}-{org_id}"
        count = db.query(DeliveryOrder).filter(
            and_(
                DeliveryOrder.organization_id == org_id,
                DeliveryOrder.financial_year == fy,
                DeliveryOrder.do_number.like(f"{prefix}%")
            )
        ).count()
        return f"{prefix}-{(count + 1):05d}"

    @staticmethod
    def generate_transporter_code(db: Session, org_id: int) -> str:
        """Generate unique transporter code."""
        prefix = f"TP-{org_id}"
        count = db.query(Transporter).filter(
            and_(
                Transporter.organization_id == org_id,
                Transporter.transporter_code.like(f"{prefix}%")
            )
        ).count()
        return f"{prefix}-{(count + 1):04d}"

    @staticmethod
    def create_transporter(
        db: Session,
        transporter_data: TransporterCreate,
        user_id: int
    ) -> Transporter:
        """Create new transporter."""
        # Generate transporter code
        transporter_code = LogisticsService.generate_transporter_code(
            db,
            transporter_data.organization_id
        )

        transporter = Transporter(
            id=str(uuid4()),
            transporter_code=transporter_code,
            organization_id=transporter_data.organization_id,
            name=transporter_data.name,
            contact_person=transporter_data.contact_person,
            contact_phone=transporter_data.contact_phone,
            contact_email=transporter_data.contact_email,
            address=transporter_data.address,
            city=transporter_data.city,
            state=transporter_data.state,
            pincode=transporter_data.pincode,
            pan=transporter_data.pan,
            gstin=transporter_data.gstin,
            status='ACTIVE'
        )

        db.add(transporter)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Admin",
            module="Logistics",
            action="CREATE",
            details=f"Created transporter {transporter_code}"
        )
        db.add(audit)

        db.commit()
        db.refresh(transporter)

        return transporter

    @staticmethod
    def create_delivery_order(
        db: Session,
        do_data: DeliveryOrderCreate,
        user_id: int
    ) -> DeliveryOrder:
        """Create new delivery order."""
        # Validate contract
        contract = db.query(SalesContract).filter(
            SalesContract.id == do_data.contract_id
        ).first()
        if not contract:
            raise ValueError(f"Contract {do_data.contract_id} not found")

        # Validate transporter if provided
        if do_data.transporter_id:
            transporter = db.query(Transporter).filter(
                and_(
                    Transporter.id == do_data.transporter_id,
                    Transporter.status == 'ACTIVE'
                )
            ).first()
            if not transporter:
                raise ValueError(f"Invalid or inactive transporter {do_data.transporter_id}")

        # Generate DO number
        do_number = LogisticsService.generate_do_number(
            db,
            do_data.organization_id,
            do_data.financial_year
        )

        # Create delivery order
        delivery_order = DeliveryOrder(
            id=str(uuid4()),
            do_number=do_number,
            organization_id=do_data.organization_id,
            financial_year=do_data.financial_year,
            contract_id=do_data.contract_id,
            invoice_id=do_data.invoice_id,
            delivery_date=do_data.delivery_date,
            planned_delivery_date=do_data.delivery_date,
            quantity_bales=do_data.quantity_bales,
            quantity_kg=do_data.quantity_kg,
            transporter_id=do_data.transporter_id,
            vehicle_number=do_data.vehicle_number,
            driver_name=do_data.driver_name,
            driver_phone=do_data.driver_phone,
            pickup_location=do_data.pickup_location,
            delivery_location=do_data.delivery_location,
            status='DRAFT'
        )

        db.add(delivery_order)

        # Create initial event
        event = DeliveryEvent(
            id=str(uuid4()),
            delivery_order_id=delivery_order.id,
            event_type='CREATED',
            performed_by=user_id,
            event_data={"created_by": user_id},
            notes=f"Delivery order created",
            event_timestamp=datetime.utcnow()
        )
        db.add(event)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Logistics Manager",
            module="Logistics",
            action="CREATE",
            details=f"Created delivery order {do_number} for contract {contract.sc_no}"
        )
        db.add(audit)

        db.commit()
        db.refresh(delivery_order)

        return delivery_order

    @staticmethod
    def assign_transporter(
        db: Session,
        do_id: str,
        transporter_id: str,
        vehicle_number: str,
        driver_name: str,
        driver_phone: str,
        user_id: int
    ) -> DeliveryOrder:
        """Assign or reassign transporter to delivery order."""
        delivery_order = db.query(DeliveryOrder).filter(
            DeliveryOrder.id == do_id
        ).first()
        if not delivery_order:
            raise ValueError(f"Delivery order {do_id} not found")

        if delivery_order.status in ['DELIVERED', 'CANCELLED']:
            raise ValueError(f"Cannot assign transporter to {delivery_order.status} delivery")

        # Validate transporter
        transporter = db.query(Transporter).filter(
            and_(
                Transporter.id == transporter_id,
                Transporter.status == 'ACTIVE'
            )
        ).first()
        if not transporter:
            raise ValueError(f"Invalid or inactive transporter {transporter_id}")

        old_transporter = delivery_order.transporter_id

        # Update delivery order
        delivery_order.transporter_id = transporter_id
        delivery_order.vehicle_number = vehicle_number
        delivery_order.driver_name = driver_name
        delivery_order.driver_phone = driver_phone

        if delivery_order.status == 'DRAFT':
            delivery_order.status = 'SCHEDULED'

        # Create event
        event = DeliveryEvent(
            id=str(uuid4()),
            delivery_order_id=delivery_order.id,
            event_type='TRANSPORTER_ASSIGNED',
            performed_by=user_id,
            event_data={
                "old_transporter_id": old_transporter,
                "new_transporter_id": transporter_id,
                "transporter_name": transporter.name,
                "vehicle_number": vehicle_number,
                "driver_name": driver_name
            },
            notes=f"Transporter {transporter.name} assigned with vehicle {vehicle_number}",
            event_timestamp=datetime.utcnow()
        )
        db.add(event)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Logistics Manager",
            module="Logistics",
            action="ASSIGN_TRANSPORTER",
            details=f"Assigned transporter {transporter.name} to DO {delivery_order.do_number}"
        )
        db.add(audit)

        db.commit()
        db.refresh(delivery_order)

        return delivery_order

    @staticmethod
    def update_delivery_status(
        db: Session,
        do_id: str,
        new_status: str,
        user_id: int,
        notes: Optional[str] = None,
        location: Optional[str] = None,
        event_data: Optional[Dict] = None
    ) -> DeliveryOrder:
        """Update delivery order status with event tracking."""
        delivery_order = db.query(DeliveryOrder).filter(
            DeliveryOrder.id == do_id
        ).first()
        if not delivery_order:
            raise ValueError(f"Delivery order {do_id} not found")

        # Validate status transition
        valid_transitions = {
            'DRAFT': ['SCHEDULED', 'CANCELLED'],
            'SCHEDULED': ['IN_TRANSIT', 'CANCELLED'],
            'IN_TRANSIT': ['DELIVERED', 'CANCELLED'],
            'PARTIALLY_DELIVERED': ['DELIVERED', 'CANCELLED'],
            'DELIVERED': [],  # Final state
            'CANCELLED': []   # Final state
        }

        if new_status not in valid_transitions.get(delivery_order.status, []):
            raise ValueError(
                f"Invalid status transition from {delivery_order.status} to {new_status}"
            )

        old_status = delivery_order.status
        delivery_order.status = new_status

        # Update timestamps
        if new_status == 'IN_TRANSIT':
            # Record actual dispatch time
            pass
        elif new_status == 'DELIVERED':
            delivery_order.actual_delivery_date = datetime.utcnow()

        # Map status to event type
        status_to_event = {
            'SCHEDULED': 'SCHEDULED',
            'IN_TRANSIT': 'DISPATCHED',
            'DELIVERED': 'DELIVERED',
            'CANCELLED': 'CANCELLED'
        }

        event_type = status_to_event.get(new_status, 'IN_TRANSIT')

        # Create status change event
        event = DeliveryEvent(
            id=str(uuid4()),
            delivery_order_id=delivery_order.id,
            event_type=event_type,
            performed_by=user_id,
            event_data=event_data or {},
            notes=notes or f"Status changed from {old_status} to {new_status}",
            location=location,
            event_timestamp=datetime.utcnow()
        )
        db.add(event)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Logistics Manager",
            module="Logistics",
            action="STATUS_CHANGE",
            details=f"Changed DO {delivery_order.do_number} status to {new_status}"
        )
        db.add(audit)

        db.commit()
        db.refresh(delivery_order)

        return delivery_order

    @staticmethod
    def cancel_delivery(
        db: Session,
        do_id: str,
        reason: str,
        user_id: int
    ) -> DeliveryOrder:
        """Cancel delivery order."""
        delivery_order = db.query(DeliveryOrder).filter(
            DeliveryOrder.id == do_id
        ).first()
        if not delivery_order:
            raise ValueError(f"Delivery order {do_id} not found")

        if delivery_order.status in ['DELIVERED', 'CANCELLED']:
            raise ValueError(f"Cannot cancel {delivery_order.status} delivery")

        delivery_order.status = 'CANCELLED'
        delivery_order.cancellation_reason = reason

        # Create cancellation event
        event = DeliveryEvent(
            id=str(uuid4()),
            delivery_order_id=delivery_order.id,
            event_type='CANCELLED',
            performed_by=user_id,
            event_data={"reason": reason},
            notes=f"Delivery cancelled: {reason}",
            event_timestamp=datetime.utcnow()
        )
        db.add(event)

        # Audit log
        audit = AuditLog(
            user=str(user_id),
            role="Logistics Manager",
            module="Logistics",
            action="CANCEL",
            details=f"Cancelled DO {delivery_order.do_number}",
            reason=reason
        )
        db.add(audit)

        db.commit()
        db.refresh(delivery_order)

        return delivery_order

    @staticmethod
    def get_delivery_events(
        db: Session,
        do_id: str
    ) -> List[DeliveryEvent]:
        """Get all events for a delivery order."""
        return db.query(DeliveryEvent).filter(
            DeliveryEvent.delivery_order_id == do_id
        ).order_by(DeliveryEvent.event_timestamp.asc()).all()

    @staticmethod
    def get_deliveries_by_contract(
        db: Session,
        contract_id: str
    ) -> List[DeliveryOrder]:
        """Get all deliveries for a contract."""
        return db.query(DeliveryOrder).filter(
            DeliveryOrder.contract_id == contract_id
        ).order_by(DeliveryOrder.delivery_date.desc()).all()
