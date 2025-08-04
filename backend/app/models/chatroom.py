"""
Chatroom Models
SQLAlchemy models for chatroom management, members, settings, and invitations.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Chatroom(Base):
    """
    Chatroom model for storing chat room information.
    """
    
    __tablename__ = "chatrooms"
    __allow_unmapped__ = True
    
    # Basic chatroom information
    name = Column(
        String(100),
        nullable=False,
        doc="Name of the chatroom"
    )
    
    description = Column(
        Text,
        nullable=True,
        doc="Description of the chatroom"
    )
    
    # Owner relationship
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the user who owns this chatroom"
    )
    
    # Chatroom settings
    is_private = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the chatroom is private (invite-only)"
    )
    
    max_members = Column(
        Integer,
        default=100,
        nullable=False,
        doc="Maximum number of members allowed"
    )
    
    encryption_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether end-to-end encryption is enabled"
    )
    
    auto_summary_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether automatic chat summaries are enabled"
    )
    
    summary_threshold = Column(
        Integer,
        default=50,
        nullable=False,
        doc="Number of messages before triggering auto-summary"
    )
    
    # Relationships
    owner = relationship(
        "User",
        back_populates="owned_chatrooms",
        doc="User who owns this chatroom"
    )
    
    members = relationship(
        "ChatroomMember",
        back_populates="chatroom",
        cascade="all, delete-orphan",
        doc="Members of this chatroom"
    )
    
    settings = relationship(
        "ChatroomSettings",
        back_populates="chatroom",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Additional settings for this chatroom"
    )
    
    invitations = relationship(
        "Invitation",
        back_populates="chatroom",
        cascade="all, delete-orphan",
        doc="Invitations for this chatroom"
    )
    
    def __repr__(self) -> str:
        return f"<Chatroom(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
    
    def to_dict(self, include_members: bool = False) -> dict:
        """
        Convert chatroom to dictionary.
        
        Args:
            include_members: Whether to include member information
            
        Returns:
            dict: Chatroom information
        """
        data = {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "owner_id": str(self.owner_id),
            "is_private": self.is_private,
            "max_members": self.max_members,
            "encryption_enabled": self.encryption_enabled,
            "auto_summary_enabled": self.auto_summary_enabled,
            "summary_threshold": self.summary_threshold,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_members and self.members:
            data["members"] = [member.to_dict() for member in self.members]
            data["member_count"] = len(self.members)
        
        return data


class ChatroomMember(Base):
    """
    Chatroom member model for storing user-chatroom relationships.
    """
    
    __tablename__ = "chatroom_members"
    __allow_unmapped__ = True
    
    # Foreign keys
    chatroom_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the chatroom"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the user"
    )
    
    # Member information
    role = Column(
        String(20),
        default="member",
        nullable=False,
        doc="Role of the user in the chatroom (owner, moderator, member)"
    )
    
    joined_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        doc="When the user joined the chatroom"
    )
    
    last_read_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        doc="When the user last read messages"
    )
    
    is_muted = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user has muted this chatroom"
    )
    
    # Relationships
    chatroom = relationship(
        "Chatroom",
        back_populates="members",
        doc="Chatroom this membership belongs to"
    )
    
    user = relationship(
        "User",
        back_populates="chatroom_memberships",
        doc="User this membership belongs to"
    )
    
    def __repr__(self) -> str:
        return f"<ChatroomMember(id={self.id}, chatroom_id={self.chatroom_id}, user_id={self.user_id}, role='{self.role}')>"
    
    def to_dict(self, include_user_info: bool = True) -> dict:
        """
        Convert membership to dictionary.
        
        Args:
            include_user_info: Whether to include user information
            
        Returns:
            dict: Membership information
        """
        data = {
            "id": str(self.id),
            "chatroom_id": str(self.chatroom_id),
            "user_id": str(self.user_id),
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_read_at": self.last_read_at.isoformat() if self.last_read_at else None,
            "is_muted": self.is_muted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_user_info and self.user:
            data["user"] = self.user.to_public_dict()
        
        return data
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if the member has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            bool: True if member has permission
        """
        role_permissions = {
            "owner": [
                "manage_chatroom", "delete_chatroom", "manage_members",
                "send_messages", "delete_any_message", "create_invitations"
            ],
            "moderator": [
                "manage_members", "send_messages", "delete_messages",
                "create_invitations"
            ],
            "member": ["send_messages"]
        }
        
        return permission in role_permissions.get(self.role, [])


class ChatroomSettings(Base):
    """
    Chatroom settings model for additional chatroom configuration.
    """
    
    __tablename__ = "chatroom_settings"
    __allow_unmapped__ = True
    
    # Foreign key to chatroom (one-to-one relationship)
    chatroom_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatrooms.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="ID of the chatroom these settings belong to"
    )
    
    # File upload settings
    allow_file_uploads = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether file uploads are allowed"
    )
    
    max_file_size_mb = Column(
        Integer,
        default=10,
        nullable=False,
        doc="Maximum file size in MB"
    )
    
    allowed_file_types = Column(
        ARRAY(String),
        default=["image/jpeg", "image/png", "image/gif", "application/pdf"],
        nullable=False,
        doc="Allowed file MIME types"
    )
    
    # Message settings
    message_retention_days = Column(
        Integer,
        default=365,
        nullable=False,
        doc="Number of days to retain messages"
    )
    
    # Feature toggles
    enable_typing_indicators = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether typing indicators are enabled"
    )
    
    enable_read_receipts = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether read receipts are enabled"
    )
    
    enable_message_reactions = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether message reactions are enabled"
    )
    
    # Customization
    custom_theme = Column(
        JSONB,
        nullable=True,
        doc="Custom theme settings as JSON"
    )
    
    # Relationships
    chatroom = relationship(
        "Chatroom",
        back_populates="settings",
        doc="Chatroom these settings belong to"
    )
    
    def __repr__(self) -> str:
        return f"<ChatroomSettings(id={self.id}, chatroom_id={self.chatroom_id})>"
    
    def to_dict(self) -> dict:
        """
        Convert settings to dictionary.
        
        Returns:
            dict: Settings information
        """
        return {
            "id": str(self.id),
            "chatroom_id": str(self.chatroom_id),
            "allow_file_uploads": self.allow_file_uploads,
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_file_types": self.allowed_file_types,
            "message_retention_days": self.message_retention_days,
            "enable_typing_indicators": self.enable_typing_indicators,
            "enable_read_receipts": self.enable_read_receipts,
            "enable_message_reactions": self.enable_message_reactions,
            "custom_theme": self.custom_theme,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Invitation(Base):
    """
    Invitation model for managing chatroom invitations.
    """
    
    __tablename__ = "invitations"
    __allow_unmapped__ = True
    
    # Foreign keys
    chatroom_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the chatroom this invitation is for"
    )
    
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the user who created this invitation"
    )
    
    # Invitation details
    invite_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique invitation code"
    )
    
    max_uses = Column(
        Integer,
        default=1,
        nullable=False,
        doc="Maximum number of times this invitation can be used"
    )
    
    current_uses = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Current number of times this invitation has been used"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When this invitation expires (null for no expiration)"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether this invitation is active"
    )
    
    # Relationships
    chatroom = relationship(
        "Chatroom",
        back_populates="invitations",
        doc="Chatroom this invitation is for"
    )
    
    created_by_user = relationship(
        "User",
        back_populates="created_invitations",
        doc="User who created this invitation"
    )
    
    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, invite_code='{self.invite_code}', chatroom_id={self.chatroom_id})>"
    
    def is_valid(self) -> bool:
        """
        Check if the invitation is valid and can be used.
        
        Returns:
            bool: True if invitation is valid
        """
        if not self.is_active:
            return False
        
        if self.current_uses >= self.max_uses:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def can_be_used(self) -> bool:
        """
        Check if the invitation can be used (alias for is_valid).
        
        Returns:
            bool: True if invitation can be used
        """
        return self.is_valid()
    
    def use_invitation(self) -> bool:
        """
        Use the invitation (increment usage count).
        
        Returns:
            bool: True if invitation was successfully used
        """
        if not self.is_valid():
            return False
        
        self.current_uses += 1
        
        # Deactivate if max uses reached
        if self.current_uses >= self.max_uses:
            self.is_active = False
        
        return True
    
    def to_dict(self, include_chatroom_info: bool = False) -> dict:
        """
        Convert invitation to dictionary.
        
        Args:
            include_chatroom_info: Whether to include chatroom information
            
        Returns:
            dict: Invitation information
        """
        data = {
            "id": str(self.id),
            "chatroom_id": str(self.chatroom_id),
            "created_by": str(self.created_by),
            "invite_code": self.invite_code,
            "max_uses": self.max_uses,
            "current_uses": self.current_uses,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_valid": self.is_valid(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_chatroom_info and self.chatroom:
            data["chatroom"] = {
                "id": str(self.chatroom.id),
                "name": self.chatroom.name,
                "description": self.chatroom.description,
                "is_private": self.chatroom.is_private,
            }
        
        return data

