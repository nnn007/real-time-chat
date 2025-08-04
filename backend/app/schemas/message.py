"""
Message Pydantic Schemas
Data validation and serialization schemas for message-related operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PaginationParams, SortParams, UserInfo


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Message content"
    )
    
    message_type: str = Field(
        "text",
        pattern="^(text|image|file|system)$",
        description="Type of message"
    )
    
    reply_to_id: Optional[UUID] = Field(
        None,
        description="ID of the message being replied to"
    )
    
    # For encrypted messages
    encrypted_content: Optional[str] = Field(
        None,
        description="Encrypted message content"
    )
    
    # For file/image messages
    file_url: Optional[str] = Field(
        None,
        description="URL of attached file"
    )
    
    file_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Original file name"
    )
    
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="File size in bytes"
    )
    
    file_type: Optional[str] = Field(
        None,
        max_length=100,
        description="MIME type of the file"
    )


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Updated message content"
    )
    
    encrypted_content: Optional[str] = Field(
        None,
        description="Updated encrypted content"
    )


class MessageReaction(BaseModel):
    """Schema for message reactions."""
    
    emoji: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Emoji reaction"
    )
    
    user_id: UUID = Field(..., description="User who reacted")
    username: str = Field(..., description="Username of reactor")
    created_at: datetime = Field(..., description="Reaction timestamp")


class MessageInfo(BaseModel):
    """Schema for message information."""
    
    id: UUID = Field(..., description="Message ID")
    chatroom_id: UUID = Field(..., description="Chatroom ID")
    user_id: UUID = Field(..., description="Sender user ID")
    username: str = Field(..., description="Sender username")
    display_name: str = Field(..., description="Sender display name")
    content: str = Field(..., description="Message content")
    message_type: str = Field(..., description="Message type")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    edited_at: Optional[datetime] = Field(None, description="Last edit timestamp")
    
    # Reply information
    reply_to_id: Optional[UUID] = Field(None, description="Replied message ID")
    reply_to_content: Optional[str] = Field(None, description="Replied message content")
    reply_to_username: Optional[str] = Field(None, description="Replied message sender")
    
    # File information
    file_url: Optional[str] = Field(None, description="File URL")
    file_name: Optional[str] = Field(None, description="File name")
    file_size: Optional[int] = Field(None, description="File size")
    file_type: Optional[str] = Field(None, description="File MIME type")
    
    # Reactions
    reactions: List[MessageReaction] = Field(default_factory=list, description="Message reactions")
    reaction_counts: Dict[str, int] = Field(default_factory=dict, description="Reaction counts")
    
    # Status
    is_edited: bool = Field(False, description="Whether message was edited")
    is_deleted: bool = Field(False, description="Whether message was deleted")
    is_pinned: bool = Field(False, description="Whether message is pinned")
    
    # Encryption
    is_encrypted: bool = Field(False, description="Whether message is encrypted")


class MessageListResponse(BaseModel):
    """Schema for message list response."""
    
    messages: List[MessageInfo] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class MessageSearchParams(BaseModel):
    """Schema for message search parameters."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Search query"
    )
    
    message_type: Optional[str] = Field(
        None,
        pattern="^(text|image|file|system)$",
        description="Filter by message type"
    )
    
    user_id: Optional[UUID] = Field(
        None,
        description="Filter by sender user ID"
    )
    
    date_from: Optional[datetime] = Field(
        None,
        description="Filter messages from this date"
    )
    
    date_to: Optional[datetime] = Field(
        None,
        description="Filter messages until this date"
    )
    
    has_files: Optional[bool] = Field(
        None,
        description="Filter messages with file attachments"
    )


class MessageSearchResponse(BaseModel):
    """Schema for message search results."""
    
    results: List[MessageInfo] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Search query used")
    search_time_ms: float = Field(..., description="Search execution time")
    
    # Search facets
    facets: Dict[str, Any] = Field(
        default_factory=dict,
        description="Search facets and aggregations"
    )


class MessageReactionRequest(BaseModel):
    """Schema for adding/removing message reactions."""
    
    emoji: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Emoji reaction"
    )
    
    action: str = Field(
        ...,
        pattern="^(add|remove)$",
        description="Action to perform"
    )


class MessagePinRequest(BaseModel):
    """Schema for pinning/unpinning messages."""
    
    action: str = Field(
        ...,
        pattern="^(pin|unpin)$",
        description="Pin action"
    )


class MessageBulkAction(BaseModel):
    """Schema for bulk message operations."""
    
    message_ids: List[UUID] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of message IDs"
    )
    
    action: str = Field(
        ...,
        pattern="^(delete|pin|unpin)$",
        description="Action to perform"
    )


class MessageStatsResponse(BaseModel):
    """Schema for message statistics."""
    
    total_messages: int = Field(..., description="Total messages in chatroom")
    messages_today: int = Field(..., description="Messages sent today")
    messages_this_week: int = Field(..., description="Messages sent this week")
    messages_this_month: int = Field(..., description="Messages sent this month")
    
    # User statistics
    top_senders: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top message senders"
    )
    
    # Message type breakdown
    message_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Message count by type"
    )
    
    # Activity timeline
    activity_timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Message activity over time"
    )


class ChatSummaryRequest(BaseModel):
    """Schema for requesting chat summary."""
    
    message_count: int = Field(
        100,
        ge=10,
        le=1000,
        description="Number of recent messages to summarize"
    )
    
    summary_type: str = Field(
        "general",
        pattern="^(general|detailed|bullet_points|key_topics)$",
        description="Type of summary to generate"
    )
    
    include_participants: bool = Field(
        True,
        description="Whether to include participant information"
    )


class ChatSummaryResponse(BaseModel):
    """Schema for chat summary response."""
    
    summary: str = Field(..., description="Generated summary")
    summary_type: str = Field(..., description="Type of summary")
    message_count: int = Field(..., description="Number of messages analyzed")
    participants: List[str] = Field(..., description="Participants in the conversation")
    key_topics: List[str] = Field(..., description="Key topics discussed")
    generated_at: datetime = Field(..., description="Summary generation timestamp")
    
    # Metadata
    model_used: str = Field(..., description="AI model used for summary")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

