"""
User Models
SQLAlchemy models for user management and authentication.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    """
    User model for storing user account information.
    """
    
    __tablename__ = "users"
    __allow_unmapped__ = True
    
    # Basic user information
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for the user"
    )
    
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User's email address"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        doc="Hashed password"
    )
    
    display_name = Column(
        String(100),
        nullable=False,
        doc="Display name shown to other users"
    )
    
    avatar_url = Column(
        Text,
        nullable=True,
        doc="URL to user's avatar image"
    )
    
    # Encryption keys for E2E encryption
    public_key = Column(
        Text,
        nullable=True,
        doc="RSA public key for end-to-end encryption"
    )
    
    # Account status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the user account is active"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user's email is verified"
    )
    
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of user's last login"
    )
    
    # Relationships
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's active sessions"
    )
    
    chatroom_memberships = relationship(
        "ChatroomMember",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's chatroom memberships"
    )
    
    owned_chatrooms = relationship(
        "Chatroom",
        back_populates="owner",
        doc="Chatrooms owned by this user"
    )
    
    created_invitations = relationship(
        "Invitation",
        back_populates="created_by_user",
        doc="Invitations created by this user"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_public_dict(self) -> dict:
        """
        Convert user to dictionary with public information only.
        
        Returns:
            dict: Public user information
        """
        return {
            "id": str(self.id),
            "username": self.username,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
    
    def to_private_dict(self) -> dict:
        """
        Convert user to dictionary with private information (for the user themselves).
        
        Returns:
            dict: Private user information
        """
        public_data = self.to_public_dict()
        public_data.update({
            "email": self.email,
            "public_key": self.public_key,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        })
        return public_data


class UserSession(Base):
    """
    User session model for managing JWT refresh tokens and active sessions.
    """
    
    __tablename__ = "user_sessions"
    __allow_unmapped__ = True
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the user this session belongs to"
    )
    
    # Session information
    refresh_token_hash = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Hashed refresh token"
    )
    
    device_info = Column(
        Text,
        nullable=True,
        doc="Information about the device/client"
    )
    
    ip_address = Column(
        INET,
        nullable=True,
        doc="IP address of the client"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When the session expires"
    )
    
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When the session was last used"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the session is active"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="sessions",
        doc="User this session belongs to"
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
    
    def is_expired(self) -> bool:
        """
        Check if the session is expired.
        
        Returns:
            bool: True if session is expired
        """
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> dict:
        """
        Convert session to dictionary.
        
        Returns:
            dict: Session information
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "device_info": self.device_info,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

