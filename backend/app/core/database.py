"""
Database Connection Module
Handles connections to PostgreSQL, MongoDB, and Redis databases.
"""

import asyncio
from typing import Dict, Optional

import redis.asyncio as aioredis
import structlog
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Global database connections
postgres_engine = None
postgres_session_factory = None
mongodb_client = None
mongodb_database = None
redis_client = None


async def init_postgres_connection():
    """
    Initialize PostgreSQL database connection with async SQLAlchemy.
    
    Returns:
        tuple: (engine, session_factory)
    """
    global postgres_engine, postgres_session_factory
    
    try:
        # Create async engine with conditional pool parameters
        engine_kwargs = {
            "url": settings.postgres_url,
            "echo": settings.DEBUG,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections every hour
        }
        
        # Only add pool parameters if not using NullPool
        if settings.ENVIRONMENT != "development":
            engine_kwargs.update({
                "pool_size": 10,  # Default pool size
                "max_overflow": 0,
            })
        else:
            engine_kwargs["poolclass"] = NullPool
            
        postgres_engine = create_async_engine(**engine_kwargs)
        
        # Create session factory
        postgres_session_factory = sessionmaker(
            bind=postgres_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Test connection
        async with postgres_engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("PostgreSQL connection initialized successfully")
        return postgres_engine, postgres_session_factory
        
    except Exception as e:
        logger.error("Failed to initialize PostgreSQL connection", error=str(e))
        raise


async def init_mongodb_connection():
    """
    Initialize MongoDB database connection with Motor.
    
    Returns:
        tuple: (client, database)
    """
    global mongodb_client, mongodb_database
    
    try:
        # Create MongoDB client
        mongodb_client = AsyncIOMotorClient(
            settings.mongodb_url,
            minPoolSize=1,  # Default min pool size
            maxPoolSize=10,  # Default max pool size
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
        )
        
        # Get database
        mongodb_database = mongodb_client[settings.MONGODB_DB]
        
        # Test connection
        await mongodb_client.admin.command("ping")
        
        logger.info("MongoDB connection initialized successfully")
        return mongodb_client, mongodb_database
        
    except Exception as e:
        logger.error("Failed to initialize MongoDB connection", error=str(e))
        raise


async def init_redis_connection():
    """
    Initialize Redis connection with aioredis.
    
    Returns:
        aioredis.Redis: Redis client instance
    """
    global redis_client
    
    try:
        # Create Redis connection pool
        redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,  # Default pool size
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30,
        )
        
        # Test connection
        await redis_client.ping()
        
        logger.info("Redis connection initialized successfully")
        return redis_client
        
    except Exception as e:
        logger.error("Failed to initialize Redis connection", error=str(e))
        raise


async def init_db_connections():
    """
    Initialize all database connections.
    """
    logger.info("Initializing database connections")
    
    try:
        # Initialize connections concurrently
        await asyncio.gather(
            init_postgres_connection(),
            init_mongodb_connection(),
            init_redis_connection(),
        )
        
        logger.info("All database connections initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database connections", error=str(e))
        raise


async def close_db_connections():
    """
    Close all database connections gracefully.
    """
    global postgres_engine, mongodb_client, redis_client
    
    logger.info("Closing database connections")
    
    try:
        # Close PostgreSQL connection
        if postgres_engine:
            await postgres_engine.dispose()
            logger.info("PostgreSQL connection closed")
        
        # Close MongoDB connection
        if mongodb_client:
            mongodb_client.close()
            logger.info("MongoDB connection closed")
        
        # Close Redis connection
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")
            
        logger.info("All database connections closed successfully")
        
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))


async def get_postgres_session() -> AsyncSession:
    """
    Get PostgreSQL database session.
    
    Returns:
        AsyncSession: SQLAlchemy async session
    """
    if not postgres_session_factory:
        raise RuntimeError("PostgreSQL connection not initialized")
    
    return postgres_session_factory()


def get_mongodb_database():
    """
    Get MongoDB database instance.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    if not mongodb_database:
        raise RuntimeError("MongoDB connection not initialized")
    
    return mongodb_database


def get_redis_client():
    """
    Get Redis client instance.
    
    Returns:
        aioredis.Redis: Redis client instance
    """
    if not redis_client:
        raise RuntimeError("Redis connection not initialized")
    
    return redis_client


async def check_database_health() -> Dict[str, any]:
    """
    Check health of all database connections.
    
    Returns:
        dict: Health status of all databases
    """
    health_status = {
        "services": {},
        "all_healthy": True
    }
    
    # Check PostgreSQL
    try:
        if postgres_engine:
            async with postgres_engine.begin() as conn:
                await conn.execute("SELECT 1")
            health_status["services"]["postgresql"] = "healthy"
        else:
            health_status["services"]["postgresql"] = "not_initialized"
            health_status["all_healthy"] = False
    except Exception as e:
        health_status["services"]["postgresql"] = f"unhealthy: {str(e)}"
        health_status["all_healthy"] = False
    
    # Check MongoDB
    try:
        if mongodb_client:
            await mongodb_client.admin.command("ping")
            health_status["services"]["mongodb"] = "healthy"
        else:
            health_status["services"]["mongodb"] = "not_initialized"
            health_status["all_healthy"] = False
    except Exception as e:
        health_status["services"]["mongodb"] = f"unhealthy: {str(e)}"
        health_status["all_healthy"] = False
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "not_initialized"
            health_status["all_healthy"] = False
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["all_healthy"] = False
    
    return health_status


# Database session dependency for FastAPI
async def get_db_session():
    """
    FastAPI dependency for getting database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with get_postgres_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# MongoDB database dependency for FastAPI
async def get_mongodb():
    """
    FastAPI dependency for getting MongoDB database.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    return get_mongodb_database()


# Redis client dependency for FastAPI
async def get_redis():
    """
    FastAPI dependency for getting Redis client.
    
    Returns:
        aioredis.Redis: Redis client instance
    """
    return get_redis_client()


class DatabaseManager:
    """
    Database manager class for handling multiple database operations.
    """
    
    def __init__(self):
        self.postgres_session = None
        self.mongodb = None
        self.redis = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.postgres_session = get_postgres_session()
        self.mongodb = get_mongodb_database()
        self.redis = get_redis_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.postgres_session:
            if exc_type:
                await self.postgres_session.rollback()
            else:
                await self.postgres_session.commit()
            await self.postgres_session.close()
    
    async def commit_postgres(self):
        """Commit PostgreSQL transaction."""
        if self.postgres_session:
            await self.postgres_session.commit()
    
    async def rollback_postgres(self):
        """Rollback PostgreSQL transaction."""
        if self.postgres_session:
            await self.postgres_session.rollback()


# Utility functions for common database operations

async def execute_postgres_query(query: str, params: Optional[dict] = None):
    """
    Execute a raw PostgreSQL query.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        Result of the query execution
    """
    async with get_postgres_session() as session:
        try:
            result = await session.execute(query, params or {})
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise


async def execute_mongodb_operation(collection_name: str, operation: str, *args, **kwargs):
    """
    Execute a MongoDB operation.
    
    Args:
        collection_name: Name of the MongoDB collection
        operation: Operation to perform (find, insert_one, etc.)
        *args: Operation arguments
        **kwargs: Operation keyword arguments
        
    Returns:
        Result of the operation
    """
    db = get_mongodb_database()
    collection = db[collection_name]
    operation_func = getattr(collection, operation)
    return await operation_func(*args, **kwargs)


async def execute_redis_command(command: str, *args, **kwargs):
    """
    Execute a Redis command.
    
    Args:
        command: Redis command to execute
        *args: Command arguments
        **kwargs: Command keyword arguments
        
    Returns:
        Result of the command execution
    """
    redis = get_redis_client()
    command_func = getattr(redis, command)
    return await command_func(*args, **kwargs)

