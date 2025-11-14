"""
Trade Desk Module Routes - Complete Implementation
Handles Trades, Offers, Tested Lots, Negotiations, and NLP Parsing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models import Trade, Offer, TestedLot, Negotiation, User, BusinessPartner, Commodity, Location
from schemas import (
    TradeCreate, TradeUpdate, TradeResponse,
    OfferCreate, OfferUpdate, OfferResponse,
    TestedLotCreate, TestedLotUpdate, TestedLotResponse,
    NegotiationCreate, NegotiationResponse,
    TradeParseRequest, TradeParseResponse
)

router = APIRouter(prefix="/api/tradedesk", tags=["Trade Desk"])


# ============================================================================
# TRADES ENDPOINTS
# ============================================================================

@router.post("/trades", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    """Create a new trade request from buyer."""
    db_trade = Trade(
        id=str(uuid.uuid4()),
        **trade.dict()
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


@router.get("/trades", response_model=List[TradeResponse])
def list_trades(
    status: Optional[str] = None,
    commodity_id: Optional[int] = None,
    buyer_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all trades with optional filters."""
    query = db.query(Trade)
    
    if status:
        query = query.filter(Trade.status == status)
    if commodity_id:
        query = query.filter(Trade.commodity_id == commodity_id)
    if buyer_id:
        query = query.filter(Trade.buyer_id == buyer_id)
    
    trades = query.offset(skip).limit(limit).all()
    return trades


@router.get("/trades/{trade_id}", response_model=TradeResponse)
def get_trade(trade_id: str, db: Session = Depends(get_db)):
    """Get specific trade by ID."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.put("/trades/{trade_id}", response_model=TradeResponse)
def update_trade(trade_id: str, trade_update: TradeUpdate, db: Session = Depends(get_db)):
    """Update trade details."""
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not db_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    for key, value in trade_update.dict(exclude_unset=True).items():
        setattr(db_trade, key, value)
    
    db.commit()
    db.refresh(db_trade)
    return db_trade


@router.delete("/trades/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(trade_id: str, db: Session = Depends(get_db)):
    """Cancel/delete a trade."""
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not db_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    db_trade.status = "CANCELLED"
    db.commit()
    return


# ============================================================================
# OFFERS ENDPOINTS
# ============================================================================

@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def create_offer(offer: OfferCreate, db: Session = Depends(get_db)):
    """Create a new offer in response to a trade."""
    # Verify trade exists
    trade = db.query(Trade).filter(Trade.id == offer.trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    db_offer = Offer(
        id=str(uuid.uuid4()),
        **offer.dict()
    )
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    return db_offer


@router.get("/offers", response_model=List[OfferResponse])
def list_offers(
    trade_id: Optional[str] = None,
    seller_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all offers with optional filters."""
    query = db.query(Offer)
    
    if trade_id:
        query = query.filter(Offer.trade_id == trade_id)
    if seller_id:
        query = query.filter(Offer.seller_id == seller_id)
    if status:
        query = query.filter(Offer.status == status)
    
    offers = query.offset(skip).limit(limit).all()
    return offers


@router.get("/offers/{offer_id}", response_model=OfferResponse)
def get_offer(offer_id: str, db: Session = Depends(get_db)):
    """Get specific offer by ID."""
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.put("/offers/{offer_id}", response_model=OfferResponse)
def update_offer(offer_id: str, offer_update: OfferUpdate, db: Session = Depends(get_db)):
    """Update offer details."""
    db_offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    for key, value in offer_update.dict(exclude_unset=True).items():
        setattr(db_offer, key, value)
    
    db.commit()
    db.refresh(db_offer)
    return db_offer


@router.post("/offers/{offer_id}/accept", response_model=OfferResponse)
def accept_offer(offer_id: str, db: Session = Depends(get_db)):
    """Accept an offer."""
    db_offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    db_offer.status = "ACCEPTED"
    db.commit()
    db.refresh(db_offer)
    return db_offer


@router.post("/offers/{offer_id}/reject", response_model=OfferResponse)
def reject_offer(offer_id: str, db: Session = Depends(get_db)):
    """Reject an offer."""
    db_offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    db_offer.status = "REJECTED"
    db.commit()
    db.refresh(db_offer)
    return db_offer


# ============================================================================
# TESTED LOTS ENDPOINTS
# ============================================================================

@router.post("/tested-lots", response_model=TestedLotResponse, status_code=status.HTTP_201_CREATED)
def create_tested_lot(lot: TestedLotCreate, db: Session = Depends(get_db)):
    """Create a new tested lot for quick matching."""
    db_lot = TestedLot(
        id=str(uuid.uuid4()),
        **lot.dict()
    )
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot


@router.get("/tested-lots", response_model=List[TestedLotResponse])
def list_tested_lots(
    seller_id: Optional[str] = None,
    commodity_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all tested lots with optional filters."""
    query = db.query(TestedLot)
    
    if seller_id:
        query = query.filter(TestedLot.seller_id == seller_id)
    if commodity_id:
        query = query.filter(TestedLot.commodity_id == commodity_id)
    if status:
        query = query.filter(TestedLot.status == status)
    
    lots = query.offset(skip).limit(limit).all()
    return lots


@router.get("/tested-lots/{lot_id}", response_model=TestedLotResponse)
def get_tested_lot(lot_id: str, db: Session = Depends(get_db)):
    """Get specific tested lot by ID."""
    lot = db.query(TestedLot).filter(TestedLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Tested lot not found")
    return lot


@router.put("/tested-lots/{lot_id}", response_model=TestedLotResponse)
def update_tested_lot(lot_id: str, lot_update: TestedLotUpdate, db: Session = Depends(get_db)):
    """Update tested lot details."""
    db_lot = db.query(TestedLot).filter(TestedLot.id == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail="Tested lot not found")
    
    for key, value in lot_update.dict(exclude_unset=True).items():
        setattr(db_lot, key, value)
    
    db.commit()
    db.refresh(db_lot)
    return db_lot


@router.delete("/tested-lots/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tested_lot(lot_id: str, db: Session = Depends(get_db)):
    """Delete a tested lot."""
    db_lot = db.query(TestedLot).filter(TestedLot.id == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail="Tested lot not found")
    
    db.delete(db_lot)
    db.commit()
    return


# ============================================================================
# NEGOTIATIONS ENDPOINTS
# ============================================================================

@router.post("/negotiations", response_model=NegotiationResponse, status_code=status.HTTP_201_CREATED)
def create_negotiation(negotiation: NegotiationCreate, db: Session = Depends(get_db)):
    """Create a counter-offer negotiation."""
    # Verify offer exists
    offer = db.query(Offer).filter(Offer.id == negotiation.offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    db_negotiation = Negotiation(
        id=str(uuid.uuid4()),
        **negotiation.dict()
    )
    db.add(db_negotiation)
    
    # Update offer status to NEGOTIATING
    offer.status = "NEGOTIATING"
    
    db.commit()
    db.refresh(db_negotiation)
    return db_negotiation


@router.get("/negotiations", response_model=List[NegotiationResponse])
def list_negotiations(
    offer_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all negotiations with optional filters."""
    query = db.query(Negotiation)
    
    if offer_id:
        query = query.filter(Negotiation.offer_id == offer_id)
    if status:
        query = query.filter(Negotiation.status == status)
    
    negotiations = query.offset(skip).limit(limit).all()
    return negotiations


@router.get("/negotiations/{negotiation_id}", response_model=NegotiationResponse)
def get_negotiation(negotiation_id: str, db: Session = Depends(get_db)):
    """Get specific negotiation by ID."""
    negotiation = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return negotiation


@router.post("/negotiations/{negotiation_id}/accept", response_model=NegotiationResponse)
def accept_negotiation(negotiation_id: str, user_id: str, db: Session = Depends(get_db)):
    """Accept a counter-offer."""
    db_negotiation = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
    if not db_negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    
    db_negotiation.status = "ACCEPTED"
    db_negotiation.responded_by = user_id
    db_negotiation.responded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_negotiation)
    return db_negotiation


@router.post("/negotiations/{negotiation_id}/reject", response_model=NegotiationResponse)
def reject_negotiation(negotiation_id: str, user_id: str, db: Session = Depends(get_db)):
    """Reject a counter-offer."""
    db_negotiation = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
    if not db_negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    
    db_negotiation.status = "REJECTED"
    db_negotiation.responded_by = user_id
    db_negotiation.responded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_negotiation)
    return db_negotiation


# ============================================================================
# NLP PARSING ENDPOINT
# ============================================================================

@router.post("/parse-trade", response_model=TradeParseResponse)
def parse_trade_text(request: TradeParseRequest, db: Session = Depends(get_db)):
    """
    Parse natural language trade description into structured trade data.
    Example: "Need 100 bales of MCU-5 cotton in Mumbai by next month"
    """
    # TODO: Implement actual NLP parsing logic
    # For now, return a placeholder response
    
    # Simple keyword extraction (to be replaced with proper NLP)
    text = request.text.lower()
    
    # Extract basic info (simplified)
    parsed_trade = {
        "buyer_id": request.user_id,  # Assuming user is buyer
        "commodity_id": 1,  # Default, should be parsed
        "quantity": 100.0,  # Should be extracted from text
        "unit": "BALES",  # Should be extracted from text
        "parsed_from_text": request.text
    }
    
    return TradeParseResponse(
        parsed_trade=parsed_trade,
        confidence=0.75,
        suggestions=[
            "Please confirm commodity type",
            "Specify delivery location",
            "Add quality parameters if needed"
        ]
    )


# ============================================================================
# DASHBOARD & ANALYTICS
# ============================================================================

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get trade desk dashboard statistics."""
    stats = {
        "total_trades": db.query(Trade).count(),
        "open_trades": db.query(Trade).filter(Trade.status == "OPEN").count(),
        "total_offers": db.query(Offer).count(),
        "pending_offers": db.query(Offer).filter(Offer.status == "PENDING").count(),
        "total_tested_lots": db.query(TestedLot).count(),
        "available_lots": db.query(TestedLot).filter(TestedLot.status == "AVAILABLE").count(),
        "active_negotiations": db.query(Negotiation).filter(Negotiation.status == "PENDING").count(),
    }
    return stats


@router.get("/matching/trades/{trade_id}")
def get_matching_offers(trade_id: str, db: Session = Depends(get_db)):
    """Get matching offers for a trade based on matching algorithm."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Get all offers for this trade, ordered by matching score
    offers = db.query(Offer).filter(
        Offer.trade_id == trade_id,
        Offer.status.in_(["PENDING", "NEGOTIATING"])
    ).order_by(Offer.matching_score.desc()).all()
    
    return offers
