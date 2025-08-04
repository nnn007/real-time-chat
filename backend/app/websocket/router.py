"""
WebSocket Router
Handles WebSocket endpoint and message routing with full real-time functionality.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session, get_redis_client
from app.core.security import verify_token
from app.models.user import User
from app.models.chatroom import ChatroomMember
from app.websocket.connection_manager import ConnectionManager

logger = structlog.get_logger(__name__)

# Create router
websocket_router = APIRouter()

# Connection manager instance
manager = ConnectionManager()


async def get_user_from_token(token: str, db: AsyncSession) -> User:
    """
    Get user from JWT token.
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        User: Authenticated user
        
    Raises:
        Exception: If token is invalid or user not found
    """
    try:
        payload = verify_token(token, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise Exception("Invalid token payload")
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise Exception("User not found or inactive")
        
        return user
        
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise


async def check_chatroom_membership(user_id: str, chatroom_id: str, db: AsyncSession) -> bool:
    """
    Check if user is a member of the chatroom.
    
    Args:
        user_id: User ID
        chatroom_id: Chatroom ID
        db: Database session
        
    Returns:
        bool: True if user is a member
    """
    try:
        result = await db.execute(
            select(ChatroomMember).where(
                ChatroomMember.user_id == user_id,
                ChatroomMember.chatroom_id == chatroom_id
            )
        )
        return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.error("Failed to check chatroom membership", error=str(e))
        return False


async def store_message_in_mongodb(message_data: Dict[str, Any]):
    """
    Store message in MongoDB.
    
    Args:
        message_data: Message data to store
    """
    try:
        # TODO: Implement MongoDB message storage
        # For now, we'll just log the message
        logger.info("Message stored", message_id=message_data.get("id"))
    except Exception as e:
        logger.error("Failed to store message in MongoDB", error=str(e))


async def publish_to_redis(channel: str, message: Dict[str, Any]):
    """
    Publish message to Redis pub/sub.
    
    Args:
        channel: Redis channel
        message: Message to publish
    """
    try:
        redis_client = get_redis_client()
        await redis_client.publish(channel, json.dumps(message))
    except Exception as e:
        logger.error("Failed to publish to Redis", error=str(e))


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """
    WebSocket endpoint for real-time chat functionality.
    
    Args:
        websocket: WebSocket connection
        token: JWT access token for authentication
        db: Database session
    """
    user = None
    user_id = None
    
    try:
        # Verify token and get user
        user = await get_user_from_token(token, db)
        user_id = str(user.id)
        
        # Accept connection
        await manager.connect(websocket, user_id)
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "event": "connected",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "timestamp": datetime.utcnow().isoformat()
            }
        }))
        
        # Notify other users that this user is online
        await manager.broadcast_user_status(user_id, "online", {
            "user_id": user_id,
            "username": user.username,
            "display_name": user.display_name
        })
        
        logger.info("WebSocket connected", user_id=user_id, username=user.username)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                event_type = message_data.get("event")
                event_data = message_data.get("data", {})
                
                logger.info("WebSocket message received", user_id=user_id, event=event_type)
                
                if event_type == "join_chatroom":
                    await handle_join_chatroom(user_id, user, event_data, db)
                
                elif event_type == "leave_chatroom":
                    await handle_leave_chatroom(user_id, event_data)
                
                elif event_type == "send_message":
                    await handle_send_message(user_id, user, event_data, db)
                
                elif event_type == "typing_start":
                    await handle_typing_indicator(user_id, user, event_data, True)
                
                elif event_type == "typing_stop":
                    await handle_typing_indicator(user_id, user, event_data, False)
                
                elif event_type == "ping":
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({
                        "event": "pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    }))
                
                else:
                    logger.warning("Unknown WebSocket event", event=event_type, user_id=user_id)
                
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected", user_id=user_id)
        
    except Exception as e:
        logger.error("WebSocket error", error=str(e), user_id=user_id)
        try:
            await websocket.close(code=4000, reason=f"Server error: {str(e)}")
        except:
            pass
    
    finally:
        # Clean up connection
        if user_id:
            manager.disconnect(websocket, user_id)
            
            # Notify other users that this user is offline
            await manager.broadcast_user_status(user_id, "offline", {
                "user_id": user_id,
                "username": user.username if user else "unknown"
            })


async def handle_join_chatroom(user_id: str, user: User, event_data: Dict[str, Any], db: AsyncSession):
    """
    Handle user joining a chatroom.
    
    Args:
        user_id: User ID
        user: User object
        event_data: Event data containing chatroom_id
        db: Database session
    """
    try:
        chatroom_id = event_data.get("chatroom_id")
        if not chatroom_id:
            return
        
        # Check if user is a member of the chatroom
        is_member = await check_chatroom_membership(user_id, chatroom_id, db)
        if not is_member:
            logger.warning("User attempted to join chatroom without membership", 
                         user_id=user_id, chatroom_id=chatroom_id)
            return
        
        # Add user to chatroom subscription
        manager.join_chatroom(user_id, chatroom_id)
        
        # Notify other chatroom members
        await manager.broadcast_to_chatroom(
            json.dumps({
                "event": "user_joined",
                "data": {
                    "user": {
                        "id": user_id,
                        "username": user.username,
                        "display_name": user.display_name
                    },
                    "chatroom_id": chatroom_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }),
            chatroom_id,
            exclude_user=user_id
        )
        
        # Publish to Redis for scaling across multiple servers
        await publish_to_redis(f"chatroom:{chatroom_id}", {
            "event": "user_joined",
            "user_id": user_id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("User joined chatroom", user_id=user_id, chatroom_id=chatroom_id)
        
    except Exception as e:
        logger.error("Failed to handle join chatroom", error=str(e), user_id=user_id)


async def handle_leave_chatroom(user_id: str, event_data: Dict[str, Any]):
    """
    Handle user leaving a chatroom.
    
    Args:
        user_id: User ID
        event_data: Event data containing chatroom_id
    """
    try:
        chatroom_id = event_data.get("chatroom_id")
        if not chatroom_id:
            return
        
        # Remove user from chatroom subscription
        manager.leave_chatroom(user_id, chatroom_id)
        
        # Notify other chatroom members
        await manager.broadcast_to_chatroom(
            json.dumps({
                "event": "user_left",
                "data": {
                    "user_id": user_id,
                    "chatroom_id": chatroom_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }),
            chatroom_id,
            exclude_user=user_id
        )
        
        # Publish to Redis
        await publish_to_redis(f"chatroom:{chatroom_id}", {
            "event": "user_left",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("User left chatroom", user_id=user_id, chatroom_id=chatroom_id)
        
    except Exception as e:
        logger.error("Failed to handle leave chatroom", error=str(e), user_id=user_id)


async def handle_send_message(user_id: str, user: User, event_data: Dict[str, Any], db: AsyncSession):
    """
    Handle sending a message.
    
    Args:
        user_id: User ID
        user: User object
        event_data: Event data containing message details
        db: Database session
    """
    try:
        chatroom_id = event_data.get("chatroom_id")
        content = event_data.get("content")
        message_type = event_data.get("message_type", "text")
        client_id = event_data.get("client_id")
        
        if not chatroom_id or not content:
            return
        
        # Check if user is a member of the chatroom
        is_member = await check_chatroom_membership(user_id, chatroom_id, db)
        if not is_member:
            logger.warning("User attempted to send message without membership", 
                         user_id=user_id, chatroom_id=chatroom_id)
            return
        
        # Create message object
        message_id = f"msg_{datetime.utcnow().timestamp()}_{user_id}"
        message = {
            "id": message_id,
            "chatroom_id": chatroom_id,
            "user_id": user_id,
            "username": user.username,
            "display_name": user.display_name,
            "content": content,
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "edited": False,
            "reactions": []
        }
        
        # Store message in MongoDB (async)
        asyncio.create_task(store_message_in_mongodb(message))
        
        # Broadcast message to chatroom members
        await manager.broadcast_to_chatroom(
            json.dumps({
                "event": "message_received",
                "data": {"message": message}
            }),
            chatroom_id
        )
        
        # Publish to Redis for scaling
        await publish_to_redis(f"chatroom:{chatroom_id}", {
            "event": "message_received",
            "message": message
        })
        
        logger.info("Message sent", message_id=message_id, user_id=user_id, chatroom_id=chatroom_id)
        
    except Exception as e:
        logger.error("Failed to handle send message", error=str(e), user_id=user_id)


async def handle_typing_indicator(user_id: str, user: User, event_data: Dict[str, Any], is_typing: bool):
    """
    Handle typing indicator.
    
    Args:
        user_id: User ID
        user: User object
        event_data: Event data containing chatroom_id
        is_typing: Whether user is typing
    """
    try:
        chatroom_id = event_data.get("chatroom_id")
        if not chatroom_id:
            return
        
        # Broadcast typing indicator to other chatroom members
        await manager.broadcast_to_chatroom(
            json.dumps({
                "event": "typing_indicator",
                "data": {
                    "user_id": user_id,
                    "username": user.username,
                    "chatroom_id": chatroom_id,
                    "is_typing": is_typing,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }),
            chatroom_id,
            exclude_user=user_id
        )
        
        logger.debug("Typing indicator sent", user_id=user_id, chatroom_id=chatroom_id, is_typing=is_typing)
        
    except Exception as e:
        logger.error("Failed to handle typing indicator", error=str(e), user_id=user_id)

