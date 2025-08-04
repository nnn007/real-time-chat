"""
Exception Handling Module
Custom exceptions and exception handlers for the chat application.
"""

from typing import Any, Dict, Optional

import structlog
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = structlog.get_logger(__name__)


class ChatApplicationException(Exception):
    """
    Base exception class for chat application specific errors.
    """
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationException(ChatApplicationException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTH_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationException(ChatApplicationException):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ACCESS_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ResourceNotFoundException(ChatApplicationException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource: str, resource_id: str = None, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ResourceConflictException(ChatApplicationException):
    """Exception raised when a resource conflict occurs."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RESOURCE_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class ValidationException(ChatApplicationException):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        if field:
            message = f"Validation error for field '{field}': {message}"
        
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class RateLimitException(ChatApplicationException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class ChatroomException(ChatApplicationException):
    """Exception raised for chatroom-related errors."""
    
    def __init__(self, message: str, code: str = "CHATROOM_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ChatroomFullException(ChatroomException):
    """Exception raised when chatroom is at maximum capacity."""
    
    def __init__(self, chatroom_name: str = None, details: Optional[Dict[str, Any]] = None):
        message = "Chatroom is full"
        if chatroom_name:
            message += f" ({chatroom_name})"
        
        super().__init__(
            message=message,
            code="CHATROOM_FULL",
            details=details
        )


class InvalidInvitationException(ChatroomException):
    """Exception raised for invalid chatroom invitations."""
    
    def __init__(self, message: str = "Invalid or expired invitation", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_INVITATION",
            details=details
        )


class MessageException(ChatApplicationException):
    """Exception raised for message-related errors."""
    
    def __init__(self, message: str, code: str = "MESSAGE_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class EncryptionException(ChatApplicationException):
    """Exception raised for encryption-related errors."""
    
    def __init__(self, message: str = "Encryption operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ENCRYPTION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class FileUploadException(ChatApplicationException):
    """Exception raised for file upload errors."""
    
    def __init__(self, message: str, code: str = "FILE_UPLOAD_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class FileSizeException(FileUploadException):
    """Exception raised when file size exceeds limit."""
    
    def __init__(self, max_size_mb: int, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"File size exceeds maximum limit of {max_size_mb}MB",
            code="FILE_TOO_LARGE",
            details=details
        )


class FileTypeException(FileUploadException):
    """Exception raised for unsupported file types."""
    
    def __init__(self, file_type: str, allowed_types: list, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"File type '{file_type}' not allowed. Allowed types: {', '.join(allowed_types)}",
            code="FILE_TYPE_NOT_ALLOWED",
            details=details
        )


class DatabaseException(ChatApplicationException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ExternalServiceException(ChatApplicationException):
    """Exception raised for external service errors."""
    
    def __init__(self, service: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        if not message:
            message = f"{service} service unavailable"
        
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


# Exception handlers

async def chat_exception_handler(request: Request, exc: ChatApplicationException) -> JSONResponse:
    """
    Handle chat application specific exceptions.
    
    Args:
        request: FastAPI request object
        exc: Chat application exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.error(
        "Chat application exception",
        exception_type=type(exc).__name__,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.error(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail,
                "details": {}
            }
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic validation exceptions.
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.error(
        "Validation exception",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method,
    )
    
    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": formatted_errors
                }
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions that aren't caught by other handlers.
    
    Args:
        request: FastAPI request object
        exc: General exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.error(
        "Unhandled exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        }
    )


# Utility functions for raising common exceptions

def raise_not_found(resource: str, resource_id: str = None):
    """Raise a resource not found exception."""
    raise ResourceNotFoundException(resource, resource_id)


def raise_access_denied(message: str = "Access denied"):
    """Raise an access denied exception."""
    raise AuthorizationException(message)


def raise_validation_error(message: str, field: str = None):
    """Raise a validation error exception."""
    raise ValidationException(message, field)


def raise_conflict(message: str):
    """Raise a resource conflict exception."""
    raise ResourceConflictException(message)


def raise_rate_limit_exceeded(message: str = "Rate limit exceeded"):
    """Raise a rate limit exceeded exception."""
    raise RateLimitException(message)

