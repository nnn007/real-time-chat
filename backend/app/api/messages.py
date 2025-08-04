"""
Messages API Endpoints
Handles message-related operations including CRUD, search, and AI summaries.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.message import (
    MessageCreate,
    MessageInfo,
    MessageUpdate,
    MessageSearchParams,
    MessageSearchResponse,
    ChatSummaryRequest,
    ChatSummaryResponse,
    MessageListResponse,
    MessageReactionRequest,
    MessagePinRequest,
    MessageBulkAction,
    MessageStatsResponse
)
from app.schemas.common import SuccessResponse, ErrorResponse
from app.services.search_service import search_service
from app.services.ai_service import ai_service

logger = structlog.get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create router
router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await search_service.initialize()
    await ai_service.initialize()


@router.post(
    "/{chatroom_id}/messages",
    response_model=Dict[str, Any],
    summary="Create a new message",
    description="Create a new message in a chatroom"
)
@limiter.limit("100/minute")
async def create_message(
    request: Request,
    chatroom_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new message in a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        message_data: Message creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success response with message ID
    """
    try:
        # TODO: Implement message creation logic
        # This would involve:
        # 1. Validate user has permission to send messages in the chatroom
        # 2. Create message in MongoDB
        # 3. Broadcast message via WebSocket
        # 4. Update chatroom last activity
        
        logger.info(
            "Message creation requested",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            message_type=message_data.message_type
        )
        
        # Placeholder response
        return {
            "success": True,
            "data": {
                "message_id": "placeholder-message-id",
                "chatroom_id": str(chatroom_id),
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
        
    except Exception as e:
        logger.error(
            "Failed to create message",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to create message")


@router.get(
    "/{chatroom_id}/messages",
    response_model=MessageListResponse,
    summary="Get messages from a chatroom",
    description="Retrieve messages from a chatroom with pagination"
)
@limiter.limit("200/minute")
async def get_messages(
    request: Request,
    chatroom_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Messages per page"),
    before: Optional[str] = Query(None, description="Get messages before this timestamp"),
    after: Optional[str] = Query(None, description="Get messages after this timestamp"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get messages from a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        page: Page number
        per_page: Messages per page
        before: Get messages before this timestamp
        after: Get messages after this timestamp
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        MessageListResponse: List of messages with pagination info
    """
    try:
        # TODO: Implement message retrieval logic
        logger.info(
            "Messages retrieval requested",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            page=page,
            per_page=per_page
        )
        
        # Placeholder response
        return MessageListResponse(
            messages=[],
            total=0,
            page=page,
            per_page=per_page,
            has_next=False,
            has_previous=False
        )
        
    except Exception as e:
        logger.error(
            "Failed to get messages",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.get(
    "/{chatroom_id}/messages/search",
    response_model=MessageSearchResponse,
    summary="Search messages in a chatroom",
    description="Search for messages in a chatroom using full-text search"
)
@limiter.limit("50/minute")
async def search_messages(
    request: Request,
    chatroom_id: UUID,
    query: str = Query(..., min_length=1, max_length=100, description="Search query"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    has_files: Optional[bool] = Query(None, description="Filter messages with files"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Results per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Search for messages in a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom to search in
        query: Search query
        message_type: Optional message type filter
        user_id: Optional user ID filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        has_files: Optional file attachment filter
        page: Page number
        per_page: Results per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        MessageSearchResponse: Search results with metadata
    """
    try:
        # TODO: Validate user has access to the chatroom
        
        # Build search parameters
        search_params = MessageSearchParams(
            query=query,
            message_type=message_type,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            has_files=has_files
        )
        
        # Perform search
        search_results = await search_service.search_messages(
            chatroom_id=chatroom_id,
            search_params=search_params,
            user_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
        logger.info(
            "Message search completed",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            query=query,
            total_results=search_results.total_results
        )
        
        return search_results
        
    except Exception as e:
        logger.error(
            "Message search failed",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            query=query,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Search failed")


@router.get(
    "/search",
    response_model=MessageSearchResponse,
    summary="Global message search",
    description="Search for messages across all accessible chatrooms"
)
@limiter.limit("30/minute")
async def search_global_messages(
    request: Request,
    query: str = Query(..., min_length=1, max_length=100, description="Search query"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    has_files: Optional[bool] = Query(None, description="Filter messages with files"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Results per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Search for messages across all accessible chatrooms.
    
    Args:
        request: FastAPI request object
        query: Search query
        message_type: Optional message type filter
        user_id: Optional user ID filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        has_files: Optional file attachment filter
        page: Page number
        per_page: Results per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        MessageSearchResponse: Search results with metadata
    """
    try:
        # TODO: Get list of chatrooms the user has access to
        accessible_chatrooms = []  # Placeholder
        
        # Build search parameters
        search_params = MessageSearchParams(
            query=query,
            message_type=message_type,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            has_files=has_files
        )
        
        # Perform global search
        search_results = await search_service.search_global_messages(
            search_params=search_params,
            user_id=current_user.id,
            accessible_chatrooms=accessible_chatrooms,
            page=page,
            per_page=per_page
        )
        
        logger.info(
            "Global message search completed",
            user_id=str(current_user.id),
            query=query,
            total_results=search_results.total_results
        )
        
        return search_results
        
    except Exception as e:
        logger.error(
            "Global message search failed",
            user_id=str(current_user.id),
            query=query,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Global search failed")


@router.post(
    "/{chatroom_id}/messages/summary",
    response_model=ChatSummaryResponse,
    summary="Generate chat summary",
    description="Generate an AI-powered summary of recent chat messages"
)
@limiter.limit("10/hour")
async def generate_chat_summary(
    request: Request,
    chatroom_id: UUID,
    summary_request: ChatSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate an AI-powered summary of recent chat messages.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom to summarize
        summary_request: Summary generation parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ChatSummaryResponse: Generated summary with metadata
    """
    try:
        # Check if AI service is available
        if not await ai_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI service is not available. Please check OpenAI API configuration."
            )
        
        # TODO: Validate user has access to the chatroom
        
        # Generate summary
        summary_response = await ai_service.generate_chat_summary(
            chatroom_id=chatroom_id,
            request=summary_request,
            user_id=current_user.id
        )
        
        logger.info(
            "Chat summary generated",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            summary_type=summary_request.summary_type,
            message_count=summary_request.message_count
        )
        
        return summary_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to generate chat summary",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@router.get(
    "/{chatroom_id}/messages/summaries",
    response_model=List[Dict[str, Any]],
    summary="Get stored summaries",
    description="Get previously generated summaries for a chatroom"
)
@limiter.limit("60/minute")
async def get_stored_summaries(
    request: Request,
    chatroom_id: UUID,
    limit: int = Query(10, ge=1, le=50, description="Number of summaries to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get previously generated summaries for a chatroom.
    
    Args:
        request: FastAPI request object
        chatroom_id: ID of the chatroom
        limit: Number of summaries to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of stored summaries
    """
    try:
        # TODO: Validate user has access to the chatroom
        
        # Get stored summaries
        summaries = await ai_service.get_stored_summaries(
            chatroom_id=chatroom_id,
            limit=limit
        )
        
        logger.info(
            "Retrieved stored summaries",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            count=len(summaries)
        )
        
        return summaries
        
    except Exception as e:
        logger.error(
            "Failed to get stored summaries",
            chatroom_id=str(chatroom_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve summaries")


# Export router
__all__ = ["router"]

