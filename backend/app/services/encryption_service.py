"""
Encryption Service
Handles server-side encryption operations, key exchange, and encrypted message storage.
"""

import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import structlog
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_mongodb_database, get_redis_client
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class EncryptionService:
    """
    Service for handling server-side encryption operations.
    Manages key exchange, encrypted message storage, and key rotation.
    """
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.redis = None
        self.key_cache_ttl = 3600  # 1 hour cache TTL for keys
    
    async def initialize(self):
        """Initialize the encryption service with database connections."""
        self.db = get_mongodb_database()
        self.redis = get_redis_client()
        
        # Ensure encryption collections exist
        await self._ensure_encryption_collections()
        
        logger.info("Encryption service initialized successfully")
    
    async def _ensure_encryption_collections(self):
        """Ensure that encryption-related collections exist with proper indexes."""
        try:
            # Create indexes for key exchange collection
            key_exchange_collection = self.db.key_exchange
            await key_exchange_collection.create_index([
                ("chatroom_id", 1),
                ("user_id", 1)
            ], unique=True, name="chatroom_user_key")
            
            await key_exchange_collection.create_index([
                ("chatroom_id", 1),
                ("created_at", -1)
            ], name="chatroom_keys_by_date")
            
            # Create indexes for encrypted messages collection
            encrypted_messages_collection = self.db.encrypted_messages
            await encrypted_messages_collection.create_index([
                ("message_id", 1)
            ], unique=True, name="message_id_unique")
            
            await encrypted_messages_collection.create_index([
                ("chatroom_id", 1),
                ("created_at", -1)
            ], name="chatroom_encrypted_messages")
            
            logger.info("Encryption collections and indexes ensured successfully")
            
        except Exception as e:
            logger.error("Failed to create encryption indexes", error=str(e))
            raise
    
    async def store_public_key(
        self,
        user_id: UUID,
        chatroom_id: UUID,
        public_key_data: str,
        key_fingerprint: str
    ) -> Dict[str, Any]:
        """
        Store a user's public key for a chatroom.
        
        Args:
            user_id: ID of the user
            chatroom_id: ID of the chatroom
            public_key_data: Base64 encoded public key data
            key_fingerprint: Key fingerprint for verification
            
        Returns:
            Dict[str, Any]: Stored key information
        """
        try:
            key_exchange_collection = self.db.key_exchange
            
            key_doc = {
                "user_id": str(user_id),
                "chatroom_id": str(chatroom_id),
                "public_key_data": public_key_data,
                "key_fingerprint": key_fingerprint,
                "key_type": "ECDH-P256",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            
            # Upsert the key (replace if exists)
            result = await key_exchange_collection.replace_one(
                {
                    "user_id": str(user_id),
                    "chatroom_id": str(chatroom_id)
                },
                key_doc,
                upsert=True
            )
            
            # Cache the key
            cache_key = f"public_key:{chatroom_id}:{user_id}"
            if self.redis:
                await self.redis.setex(
                    cache_key,
                    self.key_cache_ttl,
                    json.dumps(key_doc, default=str)
                )
            
            logger.info(
                "Public key stored successfully",
                user_id=str(user_id),
                chatroom_id=str(chatroom_id),
                fingerprint=key_fingerprint
            )
            
            return {
                "success": True,
                "key_id": f"{chatroom_id}:{user_id}",
                "fingerprint": key_fingerprint,
                "created_at": key_doc["created_at"]
            }
            
        except Exception as e:
            logger.error(
                "Failed to store public key",
                user_id=str(user_id),
                chatroom_id=str(chatroom_id),
                error=str(e)
            )
            raise
    
    async def get_public_keys(
        self,
        chatroom_id: UUID,
        exclude_user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all public keys for a chatroom.
        
        Args:
            chatroom_id: ID of the chatroom
            exclude_user_id: Optional user ID to exclude from results
            
        Returns:
            List[Dict[str, Any]]: List of public keys
        """
        try:
            key_exchange_collection = self.db.key_exchange
            
            # Build query
            query = {
                "chatroom_id": str(chatroom_id),
                "is_active": True
            }
            
            if exclude_user_id:
                query["user_id"] = {"$ne": str(exclude_user_id)}
            
            # Get keys from database
            cursor = key_exchange_collection.find(query)
            keys = await cursor.to_list(length=None)
            
            # Convert to response format
            public_keys = []
            for key_doc in keys:
                public_keys.append({
                    "user_id": key_doc["user_id"],
                    "public_key_data": key_doc["public_key_data"],
                    "key_fingerprint": key_doc["key_fingerprint"],
                    "created_at": key_doc["created_at"]
                })
            
            logger.info(
                "Retrieved public keys for chatroom",
                chatroom_id=str(chatroom_id),
                key_count=len(public_keys)
            )
            
            return public_keys
            
        except Exception as e:
            logger.error(
                "Failed to get public keys",
                chatroom_id=str(chatroom_id),
                error=str(e)
            )
            raise
    
    async def get_user_public_key(
        self,
        user_id: UUID,
        chatroom_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific user's public key for a chatroom.
        
        Args:
            user_id: ID of the user
            chatroom_id: ID of the chatroom
            
        Returns:
            Optional[Dict[str, Any]]: Public key data or None if not found
        """
        try:
            # Check cache first
            cache_key = f"public_key:{chatroom_id}:{user_id}"
            if self.redis:
                cached_key = await self.redis.get(cache_key)
                if cached_key:
                    key_doc = json.loads(cached_key)
                    return {
                        "user_id": key_doc["user_id"],
                        "public_key_data": key_doc["public_key_data"],
                        "key_fingerprint": key_doc["key_fingerprint"],
                        "created_at": datetime.fromisoformat(key_doc["created_at"])
                    }
            
            # Get from database
            key_exchange_collection = self.db.key_exchange
            key_doc = await key_exchange_collection.find_one({
                "user_id": str(user_id),
                "chatroom_id": str(chatroom_id),
                "is_active": True
            })
            
            if not key_doc:
                return None
            
            # Cache the result
            if self.redis:
                await self.redis.setex(
                    cache_key,
                    self.key_cache_ttl,
                    json.dumps(key_doc, default=str)
                )
            
            return {
                "user_id": key_doc["user_id"],
                "public_key_data": key_doc["public_key_data"],
                "key_fingerprint": key_doc["key_fingerprint"],
                "created_at": key_doc["created_at"]
            }
            
        except Exception as e:
            logger.error(
                "Failed to get user public key",
                user_id=str(user_id),
                chatroom_id=str(chatroom_id),
                error=str(e)
            )
            raise
    
    async def store_encrypted_message(
        self,
        message_id: UUID,
        chatroom_id: UUID,
        user_id: UUID,
        encrypted_content: str,
        encryption_metadata: Dict[str, Any]
    ) -> bool:
        """
        Store encrypted message content.
        
        Args:
            message_id: ID of the message
            chatroom_id: ID of the chatroom
            user_id: ID of the sender
            encrypted_content: Encrypted message content
            encryption_metadata: Encryption metadata (IV, algorithm, etc.)
            
        Returns:
            bool: Success status
        """
        try:
            encrypted_messages_collection = self.db.encrypted_messages
            
            encrypted_doc = {
                "message_id": str(message_id),
                "chatroom_id": str(chatroom_id),
                "user_id": str(user_id),
                "encrypted_content": encrypted_content,
                "encryption_metadata": encryption_metadata,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await encrypted_messages_collection.insert_one(encrypted_doc)
            
            logger.info(
                "Encrypted message stored successfully",
                message_id=str(message_id),
                chatroom_id=str(chatroom_id)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to store encrypted message",
                message_id=str(message_id),
                error=str(e)
            )
            return False
    
    async def get_encrypted_message(
        self,
        message_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get encrypted message content.
        
        Args:
            message_id: ID of the message
            
        Returns:
            Optional[Dict[str, Any]]: Encrypted message data or None if not found
        """
        try:
            encrypted_messages_collection = self.db.encrypted_messages
            
            encrypted_doc = await encrypted_messages_collection.find_one({
                "message_id": str(message_id)
            })
            
            if not encrypted_doc:
                return None
            
            return {
                "message_id": encrypted_doc["message_id"],
                "chatroom_id": encrypted_doc["chatroom_id"],
                "user_id": encrypted_doc["user_id"],
                "encrypted_content": encrypted_doc["encrypted_content"],
                "encryption_metadata": encrypted_doc["encryption_metadata"],
                "created_at": encrypted_doc["created_at"]
            }
            
        except Exception as e:
            logger.error(
                "Failed to get encrypted message",
                message_id=str(message_id),
                error=str(e)
            )
            return None
    
    async def rotate_chatroom_keys(
        self,
        chatroom_id: UUID,
        initiated_by: UUID
    ) -> Dict[str, Any]:
        """
        Rotate encryption keys for a chatroom.
        
        Args:
            chatroom_id: ID of the chatroom
            initiated_by: ID of the user who initiated key rotation
            
        Returns:
            Dict[str, Any]: Key rotation result
        """
        try:
            key_exchange_collection = self.db.key_exchange
            
            # Mark all current keys as inactive
            await key_exchange_collection.update_many(
                {
                    "chatroom_id": str(chatroom_id),
                    "is_active": True
                },
                {
                    "$set": {
                        "is_active": False,
                        "rotated_at": datetime.utcnow(),
                        "rotated_by": str(initiated_by)
                    }
                }
            )
            
            # Clear cached keys
            if self.redis:
                # Get all cached keys for this chatroom
                pattern = f"public_key:{chatroom_id}:*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            
            logger.info(
                "Chatroom keys rotated successfully",
                chatroom_id=str(chatroom_id),
                initiated_by=str(initiated_by)
            )
            
            return {
                "success": True,
                "chatroom_id": str(chatroom_id),
                "rotated_at": datetime.utcnow(),
                "initiated_by": str(initiated_by)
            }
            
        except Exception as e:
            logger.error(
                "Failed to rotate chatroom keys",
                chatroom_id=str(chatroom_id),
                error=str(e)
            )
            raise
    
    async def get_encryption_stats(
        self,
        chatroom_id: UUID
    ) -> Dict[str, Any]:
        """
        Get encryption statistics for a chatroom.
        
        Args:
            chatroom_id: ID of the chatroom
            
        Returns:
            Dict[str, Any]: Encryption statistics
        """
        try:
            key_exchange_collection = self.db.key_exchange
            encrypted_messages_collection = self.db.encrypted_messages
            
            # Get active keys count
            active_keys_count = await key_exchange_collection.count_documents({
                "chatroom_id": str(chatroom_id),
                "is_active": True
            })
            
            # Get total encrypted messages count
            encrypted_messages_count = await encrypted_messages_collection.count_documents({
                "chatroom_id": str(chatroom_id)
            })
            
            # Get latest key rotation
            latest_rotation = await key_exchange_collection.find_one(
                {
                    "chatroom_id": str(chatroom_id),
                    "rotated_at": {"$exists": True}
                },
                sort=[("rotated_at", -1)]
            )
            
            return {
                "chatroom_id": str(chatroom_id),
                "active_keys_count": active_keys_count,
                "encrypted_messages_count": encrypted_messages_count,
                "encryption_enabled": active_keys_count > 0,
                "latest_key_rotation": latest_rotation.get("rotated_at") if latest_rotation else None
            }
            
        except Exception as e:
            logger.error(
                "Failed to get encryption stats",
                chatroom_id=str(chatroom_id),
                error=str(e)
            )
            return {
                "chatroom_id": str(chatroom_id),
                "active_keys_count": 0,
                "encrypted_messages_count": 0,
                "encryption_enabled": False,
                "latest_key_rotation": None
            }
    
    async def cleanup_old_keys(self, days_old: int = 30) -> int:
        """
        Clean up old inactive keys.
        
        Args:
            days_old: Number of days old to consider for cleanup
            
        Returns:
            int: Number of keys cleaned up
        """
        try:
            key_exchange_collection = self.db.key_exchange
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = await key_exchange_collection.delete_many({
                "is_active": False,
                "rotated_at": {"$lt": cutoff_date}
            })
            
            logger.info(
                "Cleaned up old encryption keys",
                deleted_count=result.deleted_count,
                cutoff_date=cutoff_date
            )
            
            return result.deleted_count
            
        except Exception as e:
            logger.error("Failed to cleanup old keys", error=str(e))
            return 0


# Global encryption service instance
encryption_service = EncryptionService()

