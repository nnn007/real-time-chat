"""
Common Pydantic Schemas
Shared schemas used across multiple modules.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Generic type for pagination data
T = TypeVar('T')


class SuccessResponse(BaseModel):
    """Standard success response format."""
    
    success: bool = Field(True, description="Indicates successful operation")
    data: Dict[str, Any] = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    success: bool = Field(False, description="Indicates failed operation")
    error: Dict[str, Any] = Field(..., description="Error information")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {
                        "field": "email",
                        "issue": "Invalid email format"
                    }
                }
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    
    page: int = Field(1, ge=1, description="Page number (1-based)")
    limit: int = Field(20, ge=1, le=100, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.limit


class PaginationResponse(BaseModel, Generic[T]):
    """Paginated response format."""
    
    items: List[T] = Field(..., description="List of items for current page")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        limit: int,
        total: int
    ) -> "PaginationResponse[T]":
        """
        Create paginated response.
        
        Args:
            items: List of items for current page
            page: Current page number
            limit: Items per page
            total: Total number of items
            
        Returns:
            PaginationResponse: Formatted paginated response
        """
        total_pages = (total + limit - 1) // limit  # Ceiling division
        
        return cls(
            items=items,
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        )


class SearchParams(BaseModel):
    """Search parameters for search endpoints."""
    
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Results per page")


class DateRangeFilter(BaseModel):
    """Date range filter for queries."""
    
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")


class SortParams(BaseModel):
    """Sorting parameters."""
    
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class FileInfo(BaseModel):
    """File information schema."""
    
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    url: str = Field(..., description="File URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")


class EncryptedContent(BaseModel):
    """Encrypted content schema for E2E encryption."""
    
    encrypted_data: str = Field(..., description="AES encrypted content")
    iv: str = Field(..., description="Initialization vector")
    key_version: int = Field(1, ge=1, description="Encryption key version")


class MessageReaction(BaseModel):
    """Message reaction schema."""
    
    user_id: str = Field(..., description="ID of user who reacted")
    username: str = Field(..., description="Username of user who reacted")
    emoji: str = Field(..., description="Emoji reaction")
    created_at: str = Field(..., description="When reaction was added")


class UserInfo(BaseModel):
    """Basic user information schema."""
    
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    is_online: Optional[bool] = Field(None, description="Online status")


class ChatroomInfo(BaseModel):
    """Basic chatroom information schema."""
    
    id: str = Field(..., description="Chatroom ID")
    name: str = Field(..., description="Chatroom name")
    description: Optional[str] = Field(None, description="Chatroom description")
    is_private: bool = Field(..., description="Whether chatroom is private")
    member_count: int = Field(..., ge=0, description="Number of members")


class HealthStatus(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    services: Dict[str, str] = Field(..., description="Service health statuses")


class WebSocketMessage(BaseModel):
    """WebSocket message schema."""
    
    event: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ValidationError(BaseModel):
    """Validation error detail schema."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    type: str = Field(..., description="Error type")
    input: Any = Field(None, description="Input value that failed")


class RateLimitInfo(BaseModel):
    """Rate limit information schema."""
    
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: int = Field(..., description="Reset timestamp")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")


class ActivityInfo(BaseModel):
    """User activity information schema."""
    
    user_id: str = Field(..., description="User ID")
    activity_type: str = Field(..., description="Type of activity")
    timestamp: str = Field(..., description="Activity timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationInfo(BaseModel):
    """Notification information schema."""
    
    id: str = Field(..., description="Notification ID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    created_at: str = Field(..., description="Creation timestamp")
    read: bool = Field(False, description="Whether notification is read")


class SystemInfo(BaseModel):
    """System information schema."""
    
    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    description: str = Field(..., description="Application description")
    docs_url: Optional[str] = Field(None, description="API documentation URL")
    websocket_url: str = Field(..., description="WebSocket endpoint URL")


# Response wrapper functions

def success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        dict: Formatted success response
    """
    response = {
        "success": True,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response


def error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an error response.
    
    Args:
        code: Error code
        message: Error message
        details: Optional error details
        
    Returns:
        dict: Formatted error response
    """
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }


def paginated_response(
    items: List[Any],
    page: int,
    limit: int,
    total: int,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a paginated response.
    
    Args:
        items: List of items
        page: Current page
        limit: Items per page
        total: Total items
        message: Optional message
        
    Returns:
        dict: Formatted paginated response
    """
    total_pages = (total + limit - 1) // limit
    
    data = {
        "items": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }
    
    response = {
        "success": True,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response

