"""
Authentication Pydantic Schemas
Request/response schemas for authentication endpoints.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.schemas.common import UserInfo


class RegisterRequest(BaseModel):
    """User registration request schema."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_]+$",
        description="Username (3-50 chars, alphanumeric and underscore only)"
    )
    
    email: EmailStr = Field(..., description="Valid email address")
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters)"
    )
    
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name (1-100 characters)"
    )
    
    public_key: Optional[str] = Field(
        None,
        description="RSA public key for end-to-end encryption"
    )
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        
        # Check for reserved usernames
        reserved = ['admin', 'root', 'system', 'api', 'www', 'mail', 'support']
        if v.lower() in reserved:
            raise ValueError('Username is reserved')
        
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepass123",
                "display_name": "John Doe",
                "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
            }
        }


class LoginRequest(BaseModel):
    """User login request schema."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Username or email address"
    )
    
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password"
    )
    
    remember_me: bool = Field(
        False,
        description="Whether to extend session duration"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "securepass123",
                "remember_me": False
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str = Field(..., description="Valid refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenData(BaseModel):
    """Token data schema."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")


class UserProfile(BaseModel):
    """User profile schema for authentication responses."""
    
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    display_name: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    public_key: Optional[str] = Field(None, description="RSA public key")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: str = Field(..., description="Account creation timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")


class RegisterResponse(BaseModel):
    """User registration response schema."""
    
    user: UserProfile = Field(..., description="Created user profile")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "display_name": "John Doe",
                    "avatar_url": None,
                    "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
                    "is_verified": False,
                    "created_at": "2023-01-01T00:00:00Z",
                    "last_login": None
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class LoginResponse(BaseModel):
    """User login response schema."""
    
    user: UserProfile = Field(..., description="User profile")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "display_name": "John Doe",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
                    "is_verified": True,
                    "created_at": "2023-01-01T00:00:00Z",
                    "last_login": "2023-12-01T12:00:00Z"
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class LogoutResponse(BaseModel):
    """Logout response schema."""
    
    message: str = Field("Logged out successfully", description="Logout confirmation message")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Logged out successfully"
            }
        }


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters)"
    )
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword456"
            }
        }


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    
    email: EmailStr = Field(..., description="Email address to verify")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john@example.com"
            }
        }


class EmailVerificationResponse(BaseModel):
    """Email verification response schema."""
    
    message: str = Field(..., description="Verification status message")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Verification email sent successfully"
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    
    email: EmailStr = Field(..., description="Email address for password reset")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john@example.com"
            }
        }


class PasswordResetResponse(BaseModel):
    """Password reset response schema."""
    
    message: str = Field(..., description="Password reset status message")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Password reset email sent successfully"
            }
        }


class SessionInfo(BaseModel):
    """Session information schema."""
    
    id: str = Field(..., description="Session ID")
    device_info: Optional[str] = Field(None, description="Device information")
    ip_address: Optional[str] = Field(None, description="IP address")
    created_at: str = Field(..., description="Session creation timestamp")
    last_used_at: str = Field(..., description="Last usage timestamp")
    expires_at: str = Field(..., description="Session expiry timestamp")
    is_current: bool = Field(..., description="Whether this is the current session")


class SessionListResponse(BaseModel):
    """Session list response schema."""
    
    sessions: list[SessionInfo] = Field(..., description="List of active sessions")
    
    class Config:
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": "session123",
                        "device_info": "Chrome on Windows",
                        "ip_address": "192.168.1.100",
                        "created_at": "2023-12-01T10:00:00Z",
                        "last_used_at": "2023-12-01T12:00:00Z",
                        "expires_at": "2023-12-08T10:00:00Z",
                        "is_current": True
                    }
                ]
            }
        }

