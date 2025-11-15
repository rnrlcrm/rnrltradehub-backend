"""
Trade Desk API Routes - AI Chatbot and Manual Trade Entry.

Provides endpoints for:
- Chat session management
- Trade capture (AI and manual)
- Trade approval workflow
- Trade-to-contract conversion
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    TradeCreate, TradeUpdate, TradeResponse,
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse
)
from services.trade_service import TradeService
from models import Trade, ChatSession

router = APIRouter(prefix="/api/trade-desk", tags=["Trade Desk"])


# ============================================================================
# CHATBOT SESSION ENDPOINTS
# ============================================================================

@router.post("/chat/sessions", response_model=ChatSessionResponse)
def create_chat_session(
    user_id: int,
    org_id: int,
    session_type: str = "TRADE_CAPTURE",
    db: Session = Depends(get_db)
):
    """
    Create new AI chatbot session for trade capture.
    
    Session types:
    - TRADE_CAPTURE: For capturing trades
    - PAYMENT_QUERY: For payment queries
    - DISPUTE: For dispute management
    - STATEMENT: For account statements
    """
    try:
        session = TradeService.create_chat_session(
            db=db,
            user_id=user_id,
            org_id=org_id,
            session_type=session_type
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def add_chat_message(
    session_id: str,
    message_type: str,
    content: str,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """
    Add message to chatbot session.
    
    Message types:
    - USER_INPUT: User's message
    - BOT_RESPONSE: Bot's response
    - BOT_QUESTION: Bot asking for information
    - VALIDATION_ERROR: Validation error message
    - SYSTEM: System message
    """
    try:
        message = TradeService.add_chat_message(
            db=db,
            session_id=session_id,
            message_type=message_type,
            content=content,
            metadata=metadata
        )
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get chat session details."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get all messages in a chat session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages


# ============================================================================
# TRADE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/trades", response_model=TradeResponse)
def create_trade(
    trade: TradeCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Create new trade (manual or from chatbot).
    
    Validates:
    - Commodity exists and is active
    - Business partners exist and are active
    - No duplicate trades
    - Quantity and rate are valid
    - All business rules
    """
    try:
        new_trade = TradeService.create_trade(
            db=db,
            trade_data=trade,
            user_id=user_id
        )
        return new_trade
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades", response_model=List[TradeResponse])
def list_trades(
    org_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source (AI_CHATBOT, MANUAL_ENTRY)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List all trades with filters.
    
    Filters:
    - status: DRAFT, PENDING_APPROVAL, CONFIRMED, CONTRACT_GENERATED, CANCELLED, AMENDED
    - source: AI_CHATBOT, MANUAL_ENTRY, API_IMPORT
    """
    trades = TradeService.get_trades(
        db=db,
        org_id=org_id,
        status=status,
        source=source,
        skip=skip,
        limit=limit
    )
    return trades


@router.get("/trades/{trade_id}", response_model=TradeResponse)
def get_trade(
    trade_id: str,
    db: Session = Depends(get_db)
):
    """Get trade by ID."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.put("/trades/{trade_id}", response_model=TradeResponse)
def update_trade(
    trade_id: str,
    trade_update: TradeUpdate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Update trade with version tracking.
    
    Cannot update trades in CANCELLED or CONTRACT_GENERATED status.
    Increments version number on each update.
    """
    try:
        updated_trade = TradeService.update_trade(
            db=db,
            trade_id=trade_id,
            trade_data=trade_update,
            user_id=user_id
        )
        return updated_trade
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trades/{trade_id}/approve")
def approve_trade(
    trade_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Approve trade (change status to CONFIRMED).
    
    Only PENDING_APPROVAL trades can be approved.
    """
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != 'PENDING_APPROVAL':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve trade in {trade.status} status"
        )
    
    trade.status = 'CONFIRMED'
    db.commit()
    db.refresh(trade)
    
    return {"message": "Trade approved", "trade_id": trade_id, "status": trade.status}


@router.post("/trades/{trade_id}/submit-for-approval")
def submit_for_approval(
    trade_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Submit trade for approval (change status to PENDING_APPROVAL).
    
    Only DRAFT trades can be submitted.
    """
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != 'DRAFT':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit {trade.status} trade for approval"
        )
    
    trade.status = 'PENDING_APPROVAL'
    db.commit()
    db.refresh(trade)
    
    return {"message": "Trade submitted for approval", "trade_id": trade_id, "status": trade.status}


@router.post("/trades/{trade_id}/convert-to-contract")
def convert_to_contract(
    trade_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Convert approved trade to sales contract.
    
    Only CONFIRMED trades can be converted.
    Creates sales contract and links it to the trade.
    """
    try:
        contract = TradeService.convert_to_contract(
            db=db,
            trade_id=trade_id,
            user_id=user_id
        )
        return {
            "message": "Trade converted to contract",
            "trade_id": trade_id,
            "contract_id": contract.id,
            "contract_number": contract.sc_no
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trades/{trade_id}/cancel")
def cancel_trade(
    trade_id: str,
    reason: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel trade with reason.
    
    Cannot cancel trades in CANCELLED or CONTRACT_GENERATED status.
    """
    try:
        cancelled_trade = TradeService.cancel_trade(
            db=db,
            trade_id=trade_id,
            reason=reason,
            user_id=user_id
        )
        return {
            "message": "Trade cancelled",
            "trade_id": trade_id,
            "status": cancelled_trade.status,
            "reason": reason
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================

@router.post("/trades/validate")
def validate_trade(
    trade: TradeCreate,
    db: Session = Depends(get_db)
):
    """
    Validate trade data without creating it.
    
    Returns validation result with errors and warnings.
    """
    try:
        validation = TradeService.validate_trade_data(db=db, trade_data=trade)
        return validation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/by-source")
def get_trade_stats_by_source(
    org_id: int,
    db: Session = Depends(get_db)
):
    """Get trade statistics by source (AI vs Manual)."""
    from sqlalchemy import func
    
    stats = db.query(
        Trade.source,
        func.count(Trade.id).label('count'),
        func.sum(Trade.quantity_bales).label('total_bales')
    ).filter(
        Trade.organization_id == org_id
    ).group_by(Trade.source).all()
    
    return [
        {
            "source": stat.source,
            "trade_count": stat.count,
            "total_bales": stat.total_bales or 0
        }
        for stat in stats
    ]


@router.get("/stats/by-status")
def get_trade_stats_by_status(
    org_id: int,
    db: Session = Depends(get_db)
):
    """Get trade statistics by status."""
    from sqlalchemy import func
    
    stats = db.query(
        Trade.status,
        func.count(Trade.id).label('count'),
        func.sum(Trade.quantity_bales).label('total_bales')
    ).filter(
        Trade.organization_id == org_id
    ).group_by(Trade.status).all()
    
    return [
        {
            "status": stat.status,
            "trade_count": stat.count,
            "total_bales": stat.total_bales or 0
        }
        for stat in stats
    ]
