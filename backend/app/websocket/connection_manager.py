"""
WebSocket Connection Manager
Manages WebSocket connections and message broadcasting with advanced features.
"""

import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time chat functionality.
    Supports multiple connections per user, chatroom subscriptions, and broadcasting.
    """
    
    def __init__(self):
        # Active connections: {user_id: [websocket_connections]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Chatroom subscriptions: {chatroom_id: {user_ids}}
        self.chatroom_subscriptions: Dict[str, Set[str]] = {}
        
        # User presence: {user_id: last_seen_timestamp}
        self.user_presence: Dict[str, datetime] = {}
        
        # Connection metadata: {websocket_id: {user_id, connected_at, ...}}
        self.connection_metadata: Dict[int, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept WebSocket connection and add to active connections.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        try:
            await websocket.accept()
            
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            
            self.active_connections[user_id].append(websocket)
            
            # Store connection metadata
            websocket_id = id(websocket)
            self.connection_metadata[websocket_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
            
            # Update user presence
            self.user_presence[user_id] = datetime.utcnow()
            
            logger.info("WebSocket connected", 
                       user_id=user_id, 
                       connection_count=len(self.active_connections[user_id]))
            
        except Exception as e:
            logger.error("Failed to connect WebSocket", user_id=user_id, error=str(e))
            raise
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove WebSocket connection and clean up.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        try:
            # Remove from active connections
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                
                # Remove user from active connections if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    
                    # Remove from all chatroom subscriptions
                    for chatroom_id in list(self.chatroom_subscriptions.keys()):
                        self.chatroom_subscriptions[chatroom_id].discard(user_id)
                        if not self.chatroom_subscriptions[chatroom_id]:
                            del self.chatroom_subscriptions[chatroom_id]
            
            # Clean up connection metadata
            websocket_id = id(websocket)
            if websocket_id in self.connection_metadata:
                del self.connection_metadata[websocket_id]
            
            # Update user presence if no more connections
            if user_id not in self.active_connections:
                self.user_presence[user_id] = datetime.utcnow()
            
            logger.info("WebSocket disconnected", 
                       user_id=user_id, 
                       remaining_connections=len(self.active_connections.get(user_id, [])))
            
        except Exception as e:
            logger.error("Failed to disconnect WebSocket", user_id=user_id, error=str(e))
    
    async def send_personal_message(self, message: str, user_id: str):
        """
        Send message to specific user across all their connections.
        
        Args:
            message: Message to send
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                    
                    # Update last activity
                    websocket_id = id(connection)
                    if websocket_id in self.connection_metadata:
                        self.connection_metadata[websocket_id]["last_activity"] = datetime.utcnow()
                        
                except Exception as e:
                    logger.error("Failed to send personal message", 
                               user_id=user_id, error=str(e))
                    disconnected_connections.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected_connections:
                self.disconnect(connection, user_id)
    
    async def broadcast_to_chatroom(self, message: str, chatroom_id: str, exclude_user: Optional[str] = None):
        """
        Broadcast message to all users in a chatroom.
        
        Args:
            message: Message to broadcast
            chatroom_id: Target chatroom ID
            exclude_user: User ID to exclude from broadcast
        """
        if chatroom_id in self.chatroom_subscriptions:
            tasks = []
            
            for user_id in self.chatroom_subscriptions[chatroom_id]:
                if exclude_user and user_id == exclude_user:
                    continue
                
                if user_id in self.active_connections:
                    tasks.append(self.send_personal_message(message, user_id))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: str, exclude_user: Optional[str] = None):
        """
        Broadcast message to all connected users.
        
        Args:
            message: Message to broadcast
            exclude_user: User ID to exclude from broadcast
        """
        tasks = []
        
        for user_id in self.active_connections:
            if exclude_user and user_id == exclude_user:
                continue
            
            tasks.append(self.send_personal_message(message, user_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_user_status(self, user_id: str, status: str, user_data: Dict[str, Any]):
        """
        Broadcast user status change to relevant users.
        
        Args:
            user_id: User ID
            status: Status (online/offline)
            user_data: User information
        """
        try:
            # Find all chatrooms this user is subscribed to
            relevant_users = set()
            
            for chatroom_id, subscribers in self.chatroom_subscriptions.items():
                if user_id in subscribers:
                    relevant_users.update(subscribers)
            
            # Remove the user themselves from the broadcast
            relevant_users.discard(user_id)
            
            # Broadcast status to relevant users
            status_message = json.dumps({
                "event": f"user_{status}",
                "data": {
                    **user_data,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            tasks = []
            for target_user_id in relevant_users:
                if target_user_id in self.active_connections:
                    tasks.append(self.send_personal_message(status_message, target_user_id))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error("Failed to broadcast user status", user_id=user_id, error=str(e))
    
    def join_chatroom(self, user_id: str, chatroom_id: str):
        """
        Subscribe user to chatroom updates.
        
        Args:
            user_id: User ID
            chatroom_id: Chatroom ID
        """
        try:
            if chatroom_id not in self.chatroom_subscriptions:
                self.chatroom_subscriptions[chatroom_id] = set()
            
            self.chatroom_subscriptions[chatroom_id].add(user_id)
            
            logger.info("User joined chatroom subscription", 
                       user_id=user_id, 
                       chatroom_id=chatroom_id,
                       member_count=len(self.chatroom_subscriptions[chatroom_id]))
            
        except Exception as e:
            logger.error("Failed to join chatroom", user_id=user_id, chatroom_id=chatroom_id, error=str(e))
    
    def leave_chatroom(self, user_id: str, chatroom_id: str):
        """
        Unsubscribe user from chatroom updates.
        
        Args:
            user_id: User ID
            chatroom_id: Chatroom ID
        """
        try:
            if chatroom_id in self.chatroom_subscriptions:
                self.chatroom_subscriptions[chatroom_id].discard(user_id)
                
                # Remove empty chatroom subscriptions
                if not self.chatroom_subscriptions[chatroom_id]:
                    del self.chatroom_subscriptions[chatroom_id]
            
            logger.info("User left chatroom subscription", 
                       user_id=user_id, 
                       chatroom_id=chatroom_id)
            
        except Exception as e:
            logger.error("Failed to leave chatroom", user_id=user_id, chatroom_id=chatroom_id, error=str(e))
    
    def get_online_users(self) -> List[str]:
        """
        Get list of currently online users.
        
        Returns:
            List[str]: List of online user IDs
        """
        return list(self.active_connections.keys())
    
    def get_chatroom_members(self, chatroom_id: str) -> Set[str]:
        """
        Get set of users subscribed to a chatroom.
        
        Args:
            chatroom_id: Chatroom ID
            
        Returns:
            Set[str]: Set of user IDs
        """
        return self.chatroom_subscriptions.get(chatroom_id, set())
    
    def is_user_online(self, user_id: str) -> bool:
        """
        Check if user is currently online.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if user is online
        """
        return user_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections.
        
        Returns:
            int: Total connection count
        """
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get number of connections for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            int: Connection count for user
        """
        return len(self.active_connections.get(user_id, []))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection manager statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        return {
            "total_connections": self.get_connection_count(),
            "online_users": len(self.active_connections),
            "active_chatrooms": len(self.chatroom_subscriptions),
            "total_subscriptions": sum(len(subscribers) for subscribers in self.chatroom_subscriptions.values()),
            "user_presence_tracked": len(self.user_presence)
        }
    
    async def cleanup_stale_connections(self, max_idle_minutes: int = 30):
        """
        Clean up stale connections that haven't been active.
        
        Args:
            max_idle_minutes: Maximum idle time in minutes
        """
        try:
            current_time = datetime.utcnow()
            stale_connections = []
            
            for websocket_id, metadata in self.connection_metadata.items():
                last_activity = metadata.get("last_activity", metadata.get("connected_at"))
                if last_activity:
                    idle_minutes = (current_time - last_activity).total_seconds() / 60
                    if idle_minutes > max_idle_minutes:
                        stale_connections.append((websocket_id, metadata["user_id"]))
            
            # Close stale connections
            for websocket_id, user_id in stale_connections:
                # Find the websocket by ID (this is a simplified approach)
                for connections in self.active_connections.values():
                    for websocket in connections:
                        if id(websocket) == websocket_id:
                            try:
                                await websocket.close(code=4001, reason="Connection timeout")
                            except:
                                pass
                            self.disconnect(websocket, user_id)
                            break
            
            if stale_connections:
                logger.info("Cleaned up stale connections", count=len(stale_connections))
                
        except Exception as e:
            logger.error("Failed to cleanup stale connections", error=str(e))

