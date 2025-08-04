"""
Security and Authentication Module
Handles JWT tokens, password hashing, and authentication utilities.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import bcrypt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User

logger = structlog.get_logger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_random_string(length: int = 32) -> str:
    """
    Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string to generate
        
    Returns:
        str: Random string
    """
    return secrets.token_urlsafe(length)


def generate_invite_code(length: int = 12) -> str:
    """
    Generate a human-friendly invitation code.
    
    Args:
        length: Length of the code
        
    Returns:
        str: Invitation code
    """
    # Use only alphanumeric characters, excluding confusing ones
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_token(token: str) -> str:
    """
    Hash a token for secure storage.
    
    Args:
        token: Token to hash
        
    Returns:
        str: Hashed token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        token_type: Expected token type (access/refresh)
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        AuthenticationException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            raise AuthenticationException("Invalid token type")
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            raise AuthenticationException("Token missing expiration")
        
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            raise AuthenticationException("Token has expired")
        
        return payload
        
    except JWTError as e:
        logger.error("JWT verification failed", error=str(e))
        raise AuthenticationException("Invalid token")


async def get_user_by_id(user_id: str, db: AsyncSession) -> Optional[User]:
    """
    Get user by ID from database.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        User: User object or None if not found
    """
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error("Failed to get user by ID", user_id=user_id, error=str(e))
        return None


async def get_user_by_username_or_email(identifier: str, db: AsyncSession) -> Optional[User]:
    """
    Get user by username or email from database.
    
    Args:
        identifier: Username or email
        db: Database session
        
    Returns:
        User: User object or None if not found
    """
    from sqlalchemy import select, or_
    
    try:
        result = await db.execute(
            select(User).where(
                or_(
                    User.username == identifier,
                    User.email == identifier
                )
            )
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error("Failed to get user by identifier", identifier=identifier, error=str(e))
        return None


async def authenticate_user(identifier: str, password: str, db: AsyncSession) -> Optional[User]:
    """
    Authenticate user with username/email and password.
    
    Args:
        identifier: Username or email
        password: Plain text password
        db: Database session
        
    Returns:
        User: Authenticated user or None if authentication failed
    """
    user = await get_user_by_username_or_email(identifier, db)
    
    if not user:
        logger.warning("Authentication failed - user not found", identifier=identifier)
        return None
    
    if not user.is_active:
        logger.warning("Authentication failed - user inactive", user_id=str(user.id))
        return None
    
    if not verify_password(password, user.password_hash):
        logger.warning("Authentication failed - invalid password", user_id=str(user.id))
        return None
    
    logger.info("User authenticated successfully", user_id=str(user.id), username=user.username)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify the access token
        payload = verify_token(credentials.credentials, "access")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationException("Invalid token payload")
        
        # Get user from database
        user = await get_user_by_id(user_id, db)
        
        if user is None:
            raise AuthenticationException("User not found")
        
        if not user.is_active:
            raise AuthenticationException("User account is inactive")
        
        return user
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get current active user.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return current_user


def create_token_pair(user: User) -> Dict[str, Any]:
    """
    Create access and refresh token pair for user.
    
    Args:
        user: User to create tokens for
        
    Returns:
        dict: Token pair with access_token, refresh_token, and metadata
    """
    # Token payload
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    }
    
    # Create tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_seconds,
        "user": user.to_private_dict(),
    }


class RoleChecker:
    """
    Dependency class for checking user roles in chatrooms.
    """
    
    def __init__(self, required_roles: list):
        self.required_roles = required_roles
    
    async def __call__(
        self,
        chatroom_id: str,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
    ):
        """
        Check if user has required role in chatroom.
        
        Args:
            chatroom_id: ID of the chatroom
            current_user: Current authenticated user
            db: Database session
            
        Raises:
            HTTPException: If user doesn't have required role
        """
        from sqlalchemy import select
        from app.models.chatroom import ChatroomMember
        
        # Get user's membership in the chatroom
        result = await db.execute(
            select(ChatroomMember).where(
                ChatroomMember.chatroom_id == chatroom_id,
                ChatroomMember.user_id == current_user.id
            )
        )
        membership = result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this chatroom"
            )
        
        if membership.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(self.required_roles)}"
            )
        
        return membership


# Common role checkers
require_owner = RoleChecker(["owner"])
require_moderator = RoleChecker(["owner", "moderator"])
require_member = RoleChecker(["owner", "moderator", "member"])


def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        str: Session ID
    """
    return generate_random_string(32)


def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client IP address
    """
    # Check for forwarded headers first (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"


def get_user_agent(request) -> str:
    """
    Get user agent from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: User agent string
    """
    return request.headers.get("User-Agent", "unknown")

