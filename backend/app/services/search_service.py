"""
Search Service
Handles full-text search across messages and chatrooms using MongoDB text indexes.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_mongodb_database, get_redis_client
from app.schemas.message import MessageSearchParams, MessageSearchResponse, MessageInfo

logger = structlog.get_logger(__name__)


class SearchService:
    """
    Service for handling search operations across messages and chatrooms.
    """
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.redis = None
        self.cache_ttl = 300  # 5 minutes cache TTL
    
    async def initialize(self):
        """Initialize the search service with database connections."""
        self.db = get_mongodb_database()
        self.redis = get_redis_client()
        
        # Ensure search indexes exist
        await self._ensure_search_indexes()
    
    async def _ensure_search_indexes(self):
        """Ensure that text search indexes exist on the messages collection."""
        try:
            messages_collection = self.db.messages
            
            # Create text index for full-text search
            await messages_collection.create_index([
                ("content", "text"),
                ("user_id", 1),
                ("chatroom_id", 1)
            ], name="message_text_search")
            
            # Create compound indexes for efficient filtering
            await messages_collection.create_index([
                ("chatroom_id", 1),
                ("timestamp", -1)
            ], name="chatroom_timestamp")
            
            await messages_collection.create_index([
                ("user_id", 1),
                ("timestamp", -1)
            ], name="user_timestamp")
            
            await messages_collection.create_index([
                ("message_type", 1),
                ("timestamp", -1)
            ], name="type_timestamp")
            
            logger.info("Search indexes ensured successfully")
            
        except Exception as e:
            logger.error("Failed to create search indexes", error=str(e))
            raise
    
    async def search_messages(
        self,
        chatroom_id: UUID,
        search_params: MessageSearchParams,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> MessageSearchResponse:
        """
        Search messages in a chatroom using full-text search.
        
        Args:
            chatroom_id: ID of the chatroom to search in
            search_params: Search parameters
            user_id: ID of the user performing the search
            page: Page number (1-based)
            per_page: Number of results per page
            
        Returns:
            MessageSearchResponse: Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(chatroom_id, search_params, page, per_page)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info("Returning cached search results", cache_key=cache_key)
                return cached_result
            
            # Build MongoDB query
            query = await self._build_search_query(chatroom_id, search_params)
            
            # Get messages collection
            messages_collection = self.db.messages
            
            # Execute search with pagination
            skip = (page - 1) * per_page
            
            # Use aggregation pipeline for complex search
            pipeline = [
                {"$match": query},
                {"$sort": {"score": {"$meta": "textScore"}, "timestamp": -1}},
                {"$skip": skip},
                {"$limit": per_page},
                {
                    "$lookup": {
                        "from": "users",  # Assuming we have user data in MongoDB too
                        "localField": "user_id",
                        "foreignField": "_id",
                        "as": "user_info"
                    }
                }
            ]
            
            # Execute search
            cursor = messages_collection.aggregate(pipeline)
            results = await cursor.to_list(length=per_page)
            
            # Get total count
            total_results = await messages_collection.count_documents(query)
            
            # Convert results to MessageInfo objects
            message_results = []
            for result in results:
                message_info = await self._convert_to_message_info(result)
                message_results.append(message_info)
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Build response
            search_response = MessageSearchResponse(
                results=message_results,
                total_results=total_results,
                query=search_params.query,
                search_time_ms=search_time_ms,
                facets=await self._get_search_facets(chatroom_id, search_params)
            )
            
            # Cache the result
            await self._cache_result(cache_key, search_response)
            
            logger.info(
                "Message search completed",
                chatroom_id=str(chatroom_id),
                query=search_params.query,
                total_results=total_results,
                search_time_ms=search_time_ms
            )
            
            return search_response
            
        except Exception as e:
            logger.error(
                "Message search failed",
                chatroom_id=str(chatroom_id),
                query=search_params.query,
                error=str(e)
            )
            raise
    
    async def search_global_messages(
        self,
        search_params: MessageSearchParams,
        user_id: UUID,
        accessible_chatrooms: List[UUID],
        page: int = 1,
        per_page: int = 20
    ) -> MessageSearchResponse:
        """
        Search messages across all accessible chatrooms for a user.
        
        Args:
            search_params: Search parameters
            user_id: ID of the user performing the search
            accessible_chatrooms: List of chatroom IDs the user can access
            page: Page number (1-based)
            per_page: Number of results per page
            
        Returns:
            MessageSearchResponse: Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Build query for multiple chatrooms
            query = await self._build_global_search_query(search_params, accessible_chatrooms)
            
            # Get messages collection
            messages_collection = self.db.messages
            
            # Execute search with pagination
            skip = (page - 1) * per_page
            
            # Aggregation pipeline with chatroom info
            pipeline = [
                {"$match": query},
                {"$sort": {"score": {"$meta": "textScore"}, "timestamp": -1}},
                {"$skip": skip},
                {"$limit": per_page},
                {
                    "$lookup": {
                        "from": "chatrooms",
                        "localField": "chatroom_id",
                        "foreignField": "_id",
                        "as": "chatroom_info"
                    }
                }
            ]
            
            # Execute search
            cursor = messages_collection.aggregate(pipeline)
            results = await cursor.to_list(length=per_page)
            
            # Get total count
            total_results = await messages_collection.count_documents(query)
            
            # Convert results
            message_results = []
            for result in results:
                message_info = await self._convert_to_message_info(result)
                message_results.append(message_info)
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Build response
            search_response = MessageSearchResponse(
                results=message_results,
                total_results=total_results,
                query=search_params.query,
                search_time_ms=search_time_ms,
                facets=await self._get_global_search_facets(search_params, accessible_chatrooms)
            )
            
            logger.info(
                "Global message search completed",
                user_id=str(user_id),
                query=search_params.query,
                total_results=total_results,
                search_time_ms=search_time_ms
            )
            
            return search_response
            
        except Exception as e:
            logger.error(
                "Global message search failed",
                user_id=str(user_id),
                query=search_params.query,
                error=str(e)
            )
            raise
    
    async def _build_search_query(
        self,
        chatroom_id: UUID,
        search_params: MessageSearchParams
    ) -> Dict[str, Any]:
        """Build MongoDB query for message search."""
        query = {
            "chatroom_id": str(chatroom_id),
            "$text": {"$search": search_params.query}
        }
        
        # Add optional filters
        if search_params.message_type:
            query["message_type"] = search_params.message_type
        
        if search_params.user_id:
            query["user_id"] = str(search_params.user_id)
        
        if search_params.date_from or search_params.date_to:
            date_filter = {}
            if search_params.date_from:
                date_filter["$gte"] = search_params.date_from
            if search_params.date_to:
                date_filter["$lte"] = search_params.date_to
            query["timestamp"] = date_filter
        
        if search_params.has_files is not None:
            if search_params.has_files:
                query["file_url"] = {"$exists": True, "$ne": None}
            else:
                query["file_url"] = {"$exists": False}
        
        return query
    
    async def _build_global_search_query(
        self,
        search_params: MessageSearchParams,
        accessible_chatrooms: List[UUID]
    ) -> Dict[str, Any]:
        """Build MongoDB query for global message search."""
        query = {
            "chatroom_id": {"$in": [str(cid) for cid in accessible_chatrooms]},
            "$text": {"$search": search_params.query}
        }
        
        # Add the same filters as regular search
        if search_params.message_type:
            query["message_type"] = search_params.message_type
        
        if search_params.user_id:
            query["user_id"] = str(search_params.user_id)
        
        if search_params.date_from or search_params.date_to:
            date_filter = {}
            if search_params.date_from:
                date_filter["$gte"] = search_params.date_from
            if search_params.date_to:
                date_filter["$lte"] = search_params.date_to
            query["timestamp"] = date_filter
        
        if search_params.has_files is not None:
            if search_params.has_files:
                query["file_url"] = {"$exists": True, "$ne": None}
            else:
                query["file_url"] = {"$exists": False}
        
        return query
    
    async def _convert_to_message_info(self, result: Dict[str, Any]) -> MessageInfo:
        """Convert MongoDB result to MessageInfo object."""
        # This is a simplified conversion - in a real implementation,
        # you'd want to properly map all fields and handle user info
        return MessageInfo(
            id=UUID(result["_id"]),
            chatroom_id=UUID(result["chatroom_id"]),
            user_id=UUID(result["user_id"]),
            username=result.get("username", "Unknown"),
            display_name=result.get("display_name", "Unknown"),
            content=result["content"],
            message_type=result.get("message_type", "text"),
            created_at=result["timestamp"],
            updated_at=result.get("updated_at"),
            edited_at=result.get("edited_at"),
            reply_to_id=UUID(result["reply_to_id"]) if result.get("reply_to_id") else None,
            file_url=result.get("file_url"),
            file_name=result.get("file_name"),
            file_size=result.get("file_size"),
            file_type=result.get("file_type"),
            reactions=[],  # Would need to populate from actual data
            reaction_counts={},
            is_edited=result.get("is_edited", False),
            is_deleted=result.get("is_deleted", False),
            is_pinned=result.get("is_pinned", False),
            is_encrypted=result.get("is_encrypted", False)
        )
    
    async def _get_search_facets(
        self,
        chatroom_id: UUID,
        search_params: MessageSearchParams
    ) -> Dict[str, Any]:
        """Get search facets for filtering."""
        try:
            messages_collection = self.db.messages
            
            # Build base query without text search for facets
            base_query = {"chatroom_id": str(chatroom_id)}
            
            # Get message type facets
            type_facets = await messages_collection.aggregate([
                {"$match": base_query},
                {"$group": {"_id": "$message_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]).to_list(length=None)
            
            # Get user facets
            user_facets = await messages_collection.aggregate([
                {"$match": base_query},
                {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]).to_list(length=None)
            
            return {
                "message_types": [{"type": f["_id"], "count": f["count"]} for f in type_facets],
                "top_users": [{"user_id": f["_id"], "count": f["count"]} for f in user_facets]
            }
            
        except Exception as e:
            logger.error("Failed to get search facets", error=str(e))
            return {}
    
    async def _get_global_search_facets(
        self,
        search_params: MessageSearchParams,
        accessible_chatrooms: List[UUID]
    ) -> Dict[str, Any]:
        """Get search facets for global search."""
        try:
            messages_collection = self.db.messages
            
            # Build base query
            base_query = {"chatroom_id": {"$in": [str(cid) for cid in accessible_chatrooms]}}
            
            # Get chatroom facets
            chatroom_facets = await messages_collection.aggregate([
                {"$match": base_query},
                {"$group": {"_id": "$chatroom_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]).to_list(length=None)
            
            return {
                "chatrooms": [{"chatroom_id": f["_id"], "count": f["count"]} for f in chatroom_facets]
            }
            
        except Exception as e:
            logger.error("Failed to get global search facets", error=str(e))
            return {}
    
    def _get_cache_key(
        self,
        chatroom_id: UUID,
        search_params: MessageSearchParams,
        page: int,
        per_page: int
    ) -> str:
        """Generate cache key for search results."""
        key_parts = [
            "search",
            str(chatroom_id),
            search_params.query,
            search_params.message_type or "all",
            str(search_params.user_id) if search_params.user_id else "all",
            str(page),
            str(per_page)
        ]
        return ":".join(key_parts)
    
    async def _get_cached_result(self, cache_key: str) -> Optional[MessageSearchResponse]:
        """Get cached search result."""
        try:
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    # In a real implementation, you'd deserialize the cached data
                    # For now, we'll skip caching to keep it simple
                    pass
        except Exception as e:
            logger.warning("Failed to get cached result", cache_key=cache_key, error=str(e))
        
        return None
    
    async def _cache_result(self, cache_key: str, result: MessageSearchResponse):
        """Cache search result."""
        try:
            if self.redis:
                # In a real implementation, you'd serialize the result
                # For now, we'll skip caching to keep it simple
                pass
        except Exception as e:
            logger.warning("Failed to cache result", cache_key=cache_key, error=str(e))


# Global search service instance
search_service = SearchService()

