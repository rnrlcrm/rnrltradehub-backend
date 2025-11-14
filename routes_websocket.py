"""
WebSocket Routes
Real-time communication endpoints
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from services.websocket_service import manager, NotificationService
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str = Query(...),
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notifications.
    
    Connection: ws://localhost:8000/ws/notifications?user_id=123&token=xyz
    """
    # TODO: Verify token in production
    # For now, accept connection with user_id
    
    await manager.connect(websocket, user_id, {"type": "notifications"})
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                # Handle different message types
                if message_type == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": message.get("timestamp")},
                        websocket
                    )
                
                elif message_type == "subscribe_trade":
                    trade_id = message.get("trade_id")
                    if trade_id:
                        await manager.join_room(websocket, f"trade:{trade_id}")
                
                elif message_type == "unsubscribe_trade":
                    trade_id = message.get("trade_id")
                    if trade_id:
                        await manager.leave_room(websocket, f"trade:{trade_id}")
                
                elif message_type == "subscribe_offers":
                    await manager.join_room(websocket, "offers")
                
                elif message_type == "get_active_users":
                    active_users = manager.get_active_users()
                    await manager.send_personal_message(
                        {
                            "type": "active_users",
                            "users": active_users,
                            "count": len(active_users)
                        },
                        websocket
                    )
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        },
                        websocket
                    )
            
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"},
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: user={user_id}")


@router.websocket("/trade/{trade_id}")
async def websocket_trade_updates(
    websocket: WebSocket,
    trade_id: str,
    user_id: str = Query(...),
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time trade updates.
    
    Connection: ws://localhost:8000/ws/trade/123?user_id=456&token=xyz
    """
    await manager.connect(websocket, user_id, {"type": "trade", "trade_id": trade_id})
    await manager.join_room(websocket, f"trade:{trade_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle trade-specific messages
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        {"type": "pong"},
                        websocket
                    )
            
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        await manager.leave_room(websocket, f"trade:{trade_id}")
        manager.disconnect(websocket)


@router.websocket("/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    user_id: str = Query(...),
    token: str = Query(...)
):
    """
    WebSocket endpoint for dashboard real-time updates.
    
    Connection: ws://localhost:8000/ws/dashboard?user_id=123&token=xyz
    """
    await manager.connect(websocket, user_id, {"type": "dashboard"})
    await manager.join_room(websocket, "dashboard")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "refresh_stats":
                    # TODO: Fetch latest dashboard stats and send
                    await manager.send_personal_message(
                        {
                            "type": "stats_update",
                            "data": {
                                "total_trades": 0,
                                "active_offers": 0
                                # Add more stats
                            }
                        },
                        websocket
                    )
            
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        await manager.leave_room(websocket, "dashboard")
        manager.disconnect(websocket)
