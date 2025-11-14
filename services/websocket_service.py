"""
WebSocket Service Layer
Real-time communication for notifications, updates, and live data
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Optional
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connections by room/channel
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Store user metadata
        self.connection_metadata: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, metadata: Optional[dict] = None):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        # Add to user connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        logger.info(f"WebSocket connected: user={user_id}")
        
        # Send connection confirmation
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "message": "WebSocket connection established",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        # Get user_id from metadata
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata.get("user_id")
            
            # Remove from user connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from all rooms
            for room_connections in self.rooms.values():
                room_connections.discard(websocket)
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def send_to_user(self, message: dict, user_id: str):
        """Send a message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def join_room(self, websocket: WebSocket, room: str):
        """Add a WebSocket connection to a room/channel."""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)
        
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id", "unknown")
        logger.info(f"User {user_id} joined room: {room}")
        
        await self.send_personal_message(
            {
                "type": "room_joined",
                "room": room,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
    
    async def leave_room(self, websocket: WebSocket, room: str):
        """Remove a WebSocket connection from a room/channel."""
        if room in self.rooms:
            self.rooms[room].discard(websocket)
            if not self.rooms[room]:
                del self.rooms[room]
        
        await self.send_personal_message(
            {
                "type": "room_left",
                "room": room,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
    
    async def send_to_room(self, message: dict, room: str):
        """Send a message to all connections in a room/channel."""
        if room in self.rooms:
            disconnected = []
            for connection in self.rooms[room]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to room {room}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    def get_active_users(self) -> List[str]:
        """Get list of currently connected user IDs."""
        return list(self.active_connections.keys())
    
    def get_room_members(self, room: str) -> List[str]:
        """Get list of user IDs in a specific room."""
        if room not in self.rooms:
            return []
        
        members = []
        for connection in self.rooms[room]:
            metadata = self.connection_metadata.get(connection)
            if metadata:
                members.append(metadata.get("user_id"))
        
        return members
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """Get count of active connections."""
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


class NotificationService:
    """Service for sending real-time notifications via WebSocket."""
    
    @staticmethod
    async def send_notification(
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
        priority: str = "normal"
    ):
        """Send a notification to a specific user."""
        notification = {
            "type": "notification",
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_to_user(notification, user_id)
    
    @staticmethod
    async def send_trade_update(trade_id: str, update_type: str, data: dict):
        """Send trade-related updates to subscribed users."""
        message = {
            "type": "trade_update",
            "trade_id": trade_id,
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Send to trade room
        await manager.send_to_room(message, f"trade:{trade_id}")
    
    @staticmethod
    async def send_offer_update(offer_id: str, update_type: str, data: dict):
        """Send offer-related updates."""
        message = {
            "type": "offer_update",
            "offer_id": offer_id,
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_to_room(message, f"offer:{offer_id}")
    
    @staticmethod
    async def send_approval_notification(user_id: str, approval_type: str, data: dict):
        """Send approval workflow notifications."""
        await NotificationService.send_notification(
            user_id,
            "approval",
            f"{approval_type} Requires Approval",
            f"A new {approval_type} request is pending your approval",
            data,
            priority="high"
        )
    
    @staticmethod
    async def send_kyc_reminder(user_id: str, partner_name: str, days_remaining: int):
        """Send KYC expiry reminders."""
        await NotificationService.send_notification(
            user_id,
            "kyc_reminder",
            "KYC Renewal Required",
            f"KYC for {partner_name} expires in {days_remaining} days",
            {"partner_name": partner_name, "days_remaining": days_remaining},
            priority="high" if days_remaining <= 7 else "normal"
        )
    
    @staticmethod
    async def send_session_expiry_warning(user_id: str, minutes_remaining: int):
        """Send session expiry warnings."""
        await NotificationService.send_notification(
            user_id,
            "session_warning",
            "Session Expiring Soon",
            f"Your session will expire in {minutes_remaining} minutes",
            {"minutes_remaining": minutes_remaining},
            priority="normal"
        )
    
    @staticmethod
    async def broadcast_system_announcement(title: str, message: str, data: Optional[dict] = None):
        """Broadcast system-wide announcements."""
        announcement = {
            "type": "system_announcement",
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(announcement)


# Background task for heartbeat/keepalive
async def heartbeat_task():
    """Send periodic heartbeat to all connections."""
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        heartbeat = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(heartbeat)
