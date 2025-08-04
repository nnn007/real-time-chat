"""
AI Service
Handles OpenAI integration for chat summaries and other AI-powered features.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

import structlog
from openai import AsyncOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.database import get_mongodb_database, get_redis_client
from app.schemas.message import ChatSummaryRequest, ChatSummaryResponse

logger = structlog.get_logger(__name__)
settings = get_settings()


class AIService:
    """
    Service for handling AI-powered features using OpenAI.
    """
    
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.redis = None
        self.cache_ttl = 3600  # 1 hour cache TTL for summaries
    
    async def initialize(self):
        """Initialize the AI service with OpenAI client and database connections."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured, AI features will be disabled")
            return
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.db = get_mongodb_database()
        self.redis = get_redis_client()
        
        logger.info("AI service initialized successfully")
    
    async def generate_chat_summary(
        self,
        chatroom_id: UUID,
        request: ChatSummaryRequest,
        user_id: UUID
    ) -> ChatSummaryResponse:
        """
        Generate a summary of recent chat messages using OpenAI.
        
        Args:
            chatroom_id: ID of the chatroom to summarize
            request: Summary request parameters
            user_id: ID of the user requesting the summary
            
        Returns:
            ChatSummaryResponse: Generated summary with metadata
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized - check API key configuration")
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_summary_cache_key(chatroom_id, request)
            cached_summary = await self._get_cached_summary(cache_key)
            if cached_summary:
                logger.info("Returning cached chat summary", cache_key=cache_key)
                return cached_summary
            
            # Get recent messages from the chatroom
            messages = await self._get_recent_messages(chatroom_id, request.message_count)
            
            if not messages:
                raise ValueError("No messages found in the chatroom")
            
            # Prepare messages for OpenAI
            formatted_messages = await self._format_messages_for_ai(messages)
            
            # Generate summary using OpenAI
            summary_text = await self._generate_summary_with_openai(
                formatted_messages,
                request.summary_type,
                request.include_participants
            )
            
            # Extract participants and key topics
            participants = list(set(msg.get("username", "Unknown") for msg in messages))
            key_topics = await self._extract_key_topics(formatted_messages)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Create response
            summary_response = ChatSummaryResponse(
                summary=summary_text,
                summary_type=request.summary_type,
                message_count=len(messages),
                participants=participants,
                key_topics=key_topics,
                generated_at=datetime.utcnow(),
                model_used=settings.OPENAI_MODEL,
                processing_time_ms=processing_time_ms
            )
            
            # Cache the summary
            await self._cache_summary(cache_key, summary_response)
            
            # Store summary in database for future reference
            await self._store_summary_in_db(chatroom_id, user_id, summary_response)
            
            logger.info(
                "Chat summary generated successfully",
                chatroom_id=str(chatroom_id),
                user_id=str(user_id),
                message_count=len(messages),
                processing_time_ms=processing_time_ms
            )
            
            return summary_response
            
        except Exception as e:
            logger.error(
                "Failed to generate chat summary",
                chatroom_id=str(chatroom_id),
                user_id=str(user_id),
                error=str(e)
            )
            raise
    
    async def _get_recent_messages(
        self,
        chatroom_id: UUID,
        message_count: int
    ) -> List[Dict[str, Any]]:
        """Get recent messages from the chatroom."""
        try:
            messages_collection = self.db.messages
            
            # Query recent messages
            cursor = messages_collection.find(
                {"chatroom_id": str(chatroom_id)},
                sort=[("timestamp", -1)],
                limit=message_count
            )
            
            messages = await cursor.to_list(length=message_count)
            
            # Reverse to get chronological order
            messages.reverse()
            
            return messages
            
        except Exception as e:
            logger.error("Failed to get recent messages", error=str(e))
            raise
    
    async def _format_messages_for_ai(
        self,
        messages: List[Dict[str, Any]]
    ) -> str:
        """Format messages for OpenAI processing."""
        formatted_lines = []
        
        for msg in messages:
            timestamp = msg.get("timestamp", datetime.utcnow())
            username = msg.get("username", "Unknown")
            content = msg.get("content", "")
            message_type = msg.get("message_type", "text")
            
            # Format timestamp
            time_str = timestamp.strftime("%H:%M") if isinstance(timestamp, datetime) else str(timestamp)
            
            # Handle different message types
            if message_type == "text":
                formatted_lines.append(f"[{time_str}] {username}: {content}")
            elif message_type == "image":
                formatted_lines.append(f"[{time_str}] {username}: [shared an image]")
            elif message_type == "file":
                file_name = msg.get("file_name", "file")
                formatted_lines.append(f"[{time_str}] {username}: [shared file: {file_name}]")
            elif message_type == "system":
                formatted_lines.append(f"[{time_str}] System: {content}")
        
        return "\n".join(formatted_lines)
    
    async def _generate_summary_with_openai(
        self,
        formatted_messages: str,
        summary_type: str,
        include_participants: bool
    ) -> str:
        """Generate summary using OpenAI."""
        try:
            # Build system prompt based on summary type
            system_prompts = {
                "general": "You are a helpful assistant that summarizes chat conversations. Provide a concise, informative summary of the main topics and key points discussed.",
                "detailed": "You are a helpful assistant that creates detailed summaries of chat conversations. Include important details, decisions made, and action items discussed.",
                "bullet_points": "You are a helpful assistant that summarizes chat conversations in bullet point format. Create clear, organized bullet points covering the main topics.",
                "key_topics": "You are a helpful assistant that identifies and summarizes the key topics discussed in chat conversations. Focus on the main themes and subjects."
            }
            
            system_prompt = system_prompts.get(summary_type, system_prompts["general"])
            
            if include_participants:
                system_prompt += " Also mention the key participants and their contributions to the discussion."
            
            # Create user prompt
            user_prompt = f"""Please summarize the following chat conversation:

{formatted_messages}

Please provide a {summary_type} summary of this conversation."""
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            summary = response.choices[0].message.content.strip()
            
            return summary
            
        except Exception as e:
            logger.error("Failed to generate summary with OpenAI", error=str(e))
            raise
    
    async def _extract_key_topics(self, formatted_messages: str) -> List[str]:
        """Extract key topics from the conversation."""
        try:
            if not self.client:
                return []
            
            # Use a simple prompt to extract key topics
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts key topics from chat conversations. Return only a comma-separated list of 3-5 main topics discussed, without explanations."
                    },
                    {
                        "role": "user",
                        "content": f"Extract the key topics from this conversation:\n\n{formatted_messages}"
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            topics_text = response.choices[0].message.content.strip()
            topics = [topic.strip() for topic in topics_text.split(",") if topic.strip()]
            
            return topics[:5]  # Limit to 5 topics
            
        except Exception as e:
            logger.warning("Failed to extract key topics", error=str(e))
            return []
    
    async def _store_summary_in_db(
        self,
        chatroom_id: UUID,
        user_id: UUID,
        summary_response: ChatSummaryResponse
    ):
        """Store the generated summary in the database."""
        try:
            summaries_collection = self.db.chat_summaries
            
            summary_doc = {
                "_id": str(UUID()),  # Generate new UUID for summary
                "chatroom_id": str(chatroom_id),
                "requested_by": str(user_id),
                "summary": summary_response.summary,
                "summary_type": summary_response.summary_type,
                "message_count": summary_response.message_count,
                "participants": summary_response.participants,
                "key_topics": summary_response.key_topics,
                "model_used": summary_response.model_used,
                "processing_time_ms": summary_response.processing_time_ms,
                "created_at": summary_response.generated_at,
                "updated_at": summary_response.generated_at
            }
            
            await summaries_collection.insert_one(summary_doc)
            
            logger.info("Summary stored in database", chatroom_id=str(chatroom_id))
            
        except Exception as e:
            logger.error("Failed to store summary in database", error=str(e))
            # Don't raise - this is not critical for the user experience
    
    async def get_stored_summaries(
        self,
        chatroom_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get previously generated summaries for a chatroom."""
        try:
            summaries_collection = self.db.chat_summaries
            
            cursor = summaries_collection.find(
                {"chatroom_id": str(chatroom_id)},
                sort=[("created_at", -1)],
                limit=limit
            )
            
            summaries = await cursor.to_list(length=limit)
            
            return summaries
            
        except Exception as e:
            logger.error("Failed to get stored summaries", error=str(e))
            return []
    
    def _get_summary_cache_key(
        self,
        chatroom_id: UUID,
        request: ChatSummaryRequest
    ) -> str:
        """Generate cache key for summary."""
        key_parts = [
            "summary",
            str(chatroom_id),
            str(request.message_count),
            request.summary_type,
            str(request.include_participants)
        ]
        return ":".join(key_parts)
    
    async def _get_cached_summary(self, cache_key: str) -> Optional[ChatSummaryResponse]:
        """Get cached summary."""
        try:
            if self.redis:
                # In a real implementation, you'd deserialize the cached data
                # For now, we'll skip caching to keep it simple
                pass
        except Exception as e:
            logger.warning("Failed to get cached summary", cache_key=cache_key, error=str(e))
        
        return None
    
    async def _cache_summary(self, cache_key: str, summary: ChatSummaryResponse):
        """Cache summary."""
        try:
            if self.redis:
                # In a real implementation, you'd serialize the summary
                # For now, we'll skip caching to keep it simple
                pass
        except Exception as e:
            logger.warning("Failed to cache summary", cache_key=cache_key, error=str(e))
    
    async def is_available(self) -> bool:
        """Check if AI service is available."""
        return self.client is not None


# Global AI service instance
ai_service = AIService()

