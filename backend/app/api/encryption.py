"""
Encryption API Endpoints
Handles key exchange, encrypted message storage, and encryption management.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import get_current_user
from app.models.user import User
from app.services.encryption_service import encryption_service
from app.schemas.common import SuccessResponse, ErrorResponse

logger = structlog.get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create router
router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Initialize encryption service on startup."""
    await encryption_service.initialize()


@router.post(
    "/{chatroom_id}/keys",
    response_model=Dict[str, Any],
    summary="Store public key",
    description="Store a user's public key for a chatroom"
)
@limiter.limit("10/minute")
async def store_public_key(
    request: Request,
    chatroom_id: UUID,
    key_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Store a user's public key for a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        key_data: Public key data and fingerprint
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success response with key information
    """
    try:
        # Validate input
        if "public_key_data" not in key_data or "key_fingerprint" not in key_data:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: public_key_data, key_fingerprint"
            )
        
        # TODO: Validate user has access to the chatroom
        
        # Store the public key
        result = await encryption_service.store_public_key(
            user_id=current_user.id,
            chatroom_id=chatroom_id,
            public_key_data=key_data["public_key_data"],
            key_fingerprint=key_data["key_fingerprint"]
        )
        
        logger.info(
            "Public key stored successfully",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id),
            fingerprint=key_data["key_fingerprint"]
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to store public key",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to store public key")


@router.get(
    "/{chatroom_id}/keys",
    response_model=Dict[str, Any],
    summary="Get public keys",
    description="Get all public keys for a chatroom"
)
@limiter.limit("60/minute")
async def get_public_keys(
    request: Request,
    chatroom_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all public keys for a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Public keys for the chatroom
    """
    try:
        # TODO: Validate user has access to the chatroom
        
        # Get public keys (excluding current user's key)
        public_keys = await encryption_service.get_public_keys(
            chatroom_id=chatroom_id,
            exclude_user_id=current_user.id
        )
        
        logger.info(
            "Retrieved public keys for chatroom",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id),
            key_count=len(public_keys)
        )
        
        return {
            "success": True,
            "data": {
                "chatroom_id": str(chatroom_id),
                "public_keys": public_keys
            }
        }
        
    except Exception as e:
        logger.error(
            "Failed to get public keys",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve public keys")


@router.get(
    "/{chatroom_id}/keys/{user_id}",
    response_model=Dict[str, Any],
    summary="Get user's public key",
    description="Get a specific user's public key for a chatroom"
)
@limiter.limit("100/minute")
async def get_user_public_key(
    request: Request,
    chatroom_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific user's public key for a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        user_id: ID of the user whose key to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: User's public key data
    """
    try:
        # TODO: Validate user has access to the chatroom
        
        # Get the user's public key
        public_key = await encryption_service.get_user_public_key(
            user_id=user_id,
            chatroom_id=chatroom_id
        )
        
        if not public_key:
            raise HTTPException(
                status_code=404,
                detail="Public key not found for this user in this chatroom"
            )
        
        logger.info(
            "Retrieved user public key",
            current_user_id=str(current_user.id),
            target_user_id=str(user_id),
            chatroom_id=str(chatroom_id)
        )
        
        return {
            "success": True,
            "data": public_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get user public key",
            current_user_id=str(current_user.id),
            target_user_id=str(user_id),
            chatroom_id=str(chatroom_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve public key")


@router.post(
    "/{chatroom_id}/rotate-keys",
    response_model=Dict[str, Any],
    summary="Rotate chatroom keys",
    description="Rotate encryption keys for a chatroom"
)
@limiter.limit("5/hour")
async def rotate_chatroom_keys(
    request: Request,
    chatroom_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Rotate encryption keys for a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Key rotation result
    """
    try:
        # TODO: Validate user has permission to rotate keys (owner/moderator)
        
        # Rotate the keys
        result = await encryption_service.rotate_chatroom_keys(
            chatroom_id=chatroom_id,
            initiated_by=current_user.id
        )
        
        logger.info(
            "Chatroom keys rotated successfully",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id)
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Encryption keys have been rotated. All users will need to exchange new keys."
        }
        
    except Exception as e:
        logger.error(
            "Failed to rotate chatroom keys",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to rotate encryption keys")


@router.get(
    "/{chatroom_id}/stats",
    response_model=Dict[str, Any],
    summary="Get encryption statistics",
    description="Get encryption statistics for a chatroom"
)
@limiter.limit("30/minute")
async def get_encryption_stats(
    request: Request,
    chatroom_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get encryption statistics for a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Encryption statistics
    """
    try:
        # TODO: Validate user has access to the chatroom
        
        # Get encryption stats
        stats = await encryption_service.get_encryption_stats(chatroom_id=chatroom_id)
        
        logger.info(
            "Retrieved encryption stats",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id)
        )
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(
            "Failed to get encryption stats",
            user_id=str(current_user.id),
            chatroom_id=str(chatroom_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve encryption statistics")


@router.post(
    "/messages/{message_id}/encrypt",
    response_model=Dict[str, Any],
    summary="Store encrypted message",
    description="Store encrypted message content"
)
@limiter.limit("200/minute")
async def store_encrypted_message(
    request: Request,
    message_id: UUID,
    encryption_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Store encrypted message content.
    
    Args:
        request: FastAPI request object
        message_id: ID of the message
        encryption_data: Encrypted message data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success response
    """
    try:
        # Validate input
        required_fields = ["chatroom_id", "encrypted_content", "encryption_metadata"]
        for field in required_fields:
            if field not in encryption_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Store encrypted message
        success = await encryption_service.store_encrypted_message(
            message_id=message_id,
            chatroom_id=UUID(encryption_data["chatroom_id"]),
            user_id=current_user.id,
            encrypted_content=encryption_data["encrypted_content"],
            encryption_metadata=encryption_data["encryption_metadata"]
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store encrypted message")
        
        logger.info(
            "Encrypted message stored successfully",
            user_id=str(current_user.id),
            message_id=str(message_id)
        )
        
        return {
            "success": True,
            "data": {
                "message_id": str(message_id),
                "encrypted": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to store encrypted message",
            user_id=str(current_user.id),
            message_id=str(message_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to store encrypted message")


@router.get(
    "/messages/{message_id}/decrypt",
    response_model=Dict[str, Any],
    summary="Get encrypted message",
    description="Get encrypted message content for decryption"
)
@limiter.limit("200/minute")
async def get_encrypted_message(
    request: Request,
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get encrypted message content for decryption.
    
    Args:
        request: FastAPI request object
        message_id: ID of the message
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Encrypted message data
    """
    try:
        # Get encrypted message
        encrypted_message = await encryption_service.get_encrypted_message(message_id=message_id)
        
        if not encrypted_message:
            raise HTTPException(
                status_code=404,
                detail="Encrypted message not found"
            )
        
        # TODO: Validate user has access to this message
        
        logger.info(
            "Retrieved encrypted message",
            user_id=str(current_user.id),
            message_id=str(message_id)
        )
        
        return {
            "success": True,
            "data": encrypted_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get encrypted message",
            user_id=str(current_user.id),
            message_id=str(message_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve encrypted message")


# Export router
__all__ = ["router"]

