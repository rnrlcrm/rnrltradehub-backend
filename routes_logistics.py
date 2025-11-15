"""
Logistics API Routes - Delivery Orders and Transporter Management.

Provides endpoints for:
- Transporter CRUD
- Delivery order management
- Transporter assignment
- Status tracking
- Event logging
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    TransporterCreate, TransporterUpdate, TransporterResponse,
    DeliveryOrderCreate, DeliveryOrderUpdate, DeliveryOrderResponse,
    DeliveryEventCreate, DeliveryEventResponse
)
from services.logistics_service import LogisticsService
from models import Transporter, DeliveryOrder

router = APIRouter(prefix="/api/logistics", tags=["Logistics"])


# ============================================================================
# TRANSPORTER ENDPOINTS
# ============================================================================

@router.post("/transporters", response_model=TransporterResponse)
def create_transporter(
    transporter: TransporterCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create new transporter/logistics provider."""
    try:
        new_transporter = LogisticsService.create_transporter(
            db=db,
            transporter_data=transporter,
            user_id=user_id
        )
        return new_transporter
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transporters", response_model=List[TransporterResponse])
def list_transporters(
    org_id: int,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all transporters."""
    query = db.query(Transporter).filter(Transporter.organization_id == org_id)
    
    if status:
        query = query.filter(Transporter.status == status)
    
    transporters = query.order_by(Transporter.name).offset(skip).limit(limit).all()
    return transporters


@router.get("/transporters/{transporter_id}", response_model=TransporterResponse)
def get_transporter(
    transporter_id: str,
    db: Session = Depends(get_db)
):
    """Get transporter by ID."""
    transporter = db.query(Transporter).filter(Transporter.id == transporter_id).first()
    if not transporter:
        raise HTTPException(status_code=404, detail="Transporter not found")
    return transporter


# ============================================================================
# DELIVERY ORDER ENDPOINTS
# ============================================================================

@router.post("/delivery-orders", response_model=DeliveryOrderResponse)
def create_delivery_order(
    delivery_order: DeliveryOrderCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create new delivery order."""
    try:
        new_do = LogisticsService.create_delivery_order(
            db=db,
            do_data=delivery_order,
            user_id=user_id
        )
        return new_do
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/delivery-orders", response_model=List[DeliveryOrderResponse])
def list_delivery_orders(
    org_id: int,
    status: Optional[str] = Query(None),
    contract_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List delivery orders with filters."""
    query = db.query(DeliveryOrder).filter(DeliveryOrder.organization_id == org_id)
    
    if status:
        query = query.filter(DeliveryOrder.status == status)
    if contract_id:
        query = query.filter(DeliveryOrder.contract_id == contract_id)
    
    orders = query.order_by(DeliveryOrder.delivery_date.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/delivery-orders/{do_id}", response_model=DeliveryOrderResponse)
def get_delivery_order(
    do_id: str,
    db: Session = Depends(get_db)
):
    """Get delivery order by ID."""
    do = db.query(DeliveryOrder).filter(DeliveryOrder.id == do_id).first()
    if not do:
        raise HTTPException(status_code=404, detail="Delivery order not found")
    return do


@router.post("/delivery-orders/{do_id}/assign-transporter")
def assign_transporter(
    do_id: str,
    transporter_id: str,
    vehicle_number: str,
    driver_name: str,
    driver_phone: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Assign or reassign transporter to delivery order."""
    try:
        do = LogisticsService.assign_transporter(
            db=db,
            do_id=do_id,
            transporter_id=transporter_id,
            vehicle_number=vehicle_number,
            driver_name=driver_name,
            driver_phone=driver_phone,
            user_id=user_id
        )
        return {
            "message": "Transporter assigned",
            "do_number": do.do_number,
            "transporter_id": transporter_id,
            "vehicle_number": vehicle_number
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delivery-orders/{do_id}/dispatch")
def dispatch_delivery(
    do_id: str,
    user_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Mark delivery as dispatched (SCHEDULED → IN_TRANSIT)."""
    try:
        do = LogisticsService.update_delivery_status(
            db=db,
            do_id=do_id,
            new_status='IN_TRANSIT',
            user_id=user_id,
            notes=notes
        )
        return {"message": "Delivery dispatched", "do_number": do.do_number, "status": do.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delivery-orders/{do_id}/complete")
def complete_delivery(
    do_id: str,
    user_id: int,
    notes: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Mark delivery as completed (IN_TRANSIT → DELIVERED)."""
    try:
        do = LogisticsService.update_delivery_status(
            db=db,
            do_id=do_id,
            new_status='DELIVERED',
            user_id=user_id,
            notes=notes,
            location=location
        )
        return {"message": "Delivery completed", "do_number": do.do_number, "status": do.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delivery-orders/{do_id}/cancel")
def cancel_delivery(
    do_id: str,
    reason: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Cancel delivery order."""
    try:
        do = LogisticsService.cancel_delivery(
            db=db,
            do_id=do_id,
            reason=reason,
            user_id=user_id
        )
        return {"message": "Delivery cancelled", "do_number": do.do_number, "reason": reason}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/delivery-orders/{do_id}/events", response_model=List[DeliveryEventResponse])
def get_delivery_events(
    do_id: str,
    db: Session = Depends(get_db)
):
    """Get all events for a delivery order."""
    events = LogisticsService.get_delivery_events(db=db, do_id=do_id)
    return events


@router.get("/delivery-orders/by-contract/{contract_id}", response_model=List[DeliveryOrderResponse])
def get_deliveries_by_contract(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Get all deliveries for a contract."""
    deliveries = LogisticsService.get_deliveries_by_contract(db=db, contract_id=contract_id)
    return deliveries
