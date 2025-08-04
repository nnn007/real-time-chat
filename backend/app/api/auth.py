"""
Authentication API Endpoints
Handles user authentication, registration, and token management.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    hash_password,
    get_current_user,
    get_user_by_username_or_email
)
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterResponse,
    LoginResponse,
    RefreshTokenResponse
)
from app.schemas.common import success_response, error_response

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()
security = HTTPBearer()


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Register new user",
    description="Create a new user account"
)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Register a new user account.
    
    Args:
        register_data: User registration data
        db: Database session
        
    Returns:
        RegisterResponse: User data and tokens
    """
    try:
        # Check if user already exists
        existing_user = await get_user_by_username_or_email(
            register_data.username, db
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(register_data.password)
        
        # TODO: Implement actual user creation
        # For now, return mock response
        user_data = {
            "id": "mock-user-id",
            "username": register_data.username,
            "email": register_data.email,
            "display_name": register_data.display_name,
            "avatar_url": None,
            "public_key": register_data.public_key,
            "is_verified": False,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None
        }
        
        # Create tokens
        access_token = create_access_token(data={"sub": user_data["id"]})
        refresh_token = create_refresh_token(data={"sub": user_data["id"]})
        
        return RegisterResponse(
            user=user_data,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user and return access tokens"
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate user and return access tokens.
    
    Args:
        login_data: Login credentials
        db: Database session
        
    Returns:
        LoginResponse: User data and tokens
    """
    try:
        # Authenticate user
        user = await authenticate_user(login_data.username, login_data.password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Update last login
        user.last_login = datetime.utcnow()
        # TODO: Save to database
        
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "public_key": user.public_key,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        return LoginResponse(
            user=user_data,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token data
        db: Database session
        
    Returns:
        RefreshTokenResponse: New access token
    """
    try:
        # TODO: Implement token refresh logic
        # For now, return mock response
        access_token = create_access_token(data={"sub": "mock-user-id"})
        
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post(
    "/logout",
    summary="User logout",
    description="Logout user and invalidate tokens"
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Logout user and invalidate tokens.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Logout confirmation
    """
    try:
        # TODO: Implement token invalidation logic
        return success_response(
            data={"message": "Logged out successfully"},
            message="Logout successful"
        )
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get(
    "/me",
    summary="Get current user info",
    description="Get information about the currently authenticated user"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Current user information
    """
    return success_response(
        data=current_user.to_private_dict(),
        message="User information retrieved successfully"
    ) 