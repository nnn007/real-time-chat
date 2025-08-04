"""
Application Configuration
Centralized configuration management using Pydantic settings.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Configuration
    APP_NAME: str = Field(default="RealTime Chat App", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/staging/production)")
    ENABLE_API_DOCS: bool = Field(default=True, description="Enable API documentation")
    ENABLE_SECURITY_HEADERS: bool = Field(default=True, description="Enable security headers")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    
    # Security Configuration
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")
    
    # Database Configuration - PostgreSQL
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="realtime_chat", description="PostgreSQL database name")
    
    # Database Configuration - MongoDB
    MONGODB_HOST: str = Field(default="localhost", description="MongoDB host")
    MONGODB_PORT: int = Field(default=27017, description="MongoDB port")
    MONGODB_USER: Optional[str] = Field(default=None, description="MongoDB username")
    MONGODB_PASSWORD: Optional[str] = Field(default=None, description="MongoDB password")
    MONGODB_DB: str = Field(default="realtime_chat", description="MongoDB database name")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    CORS_CREDENTIALS: bool = Field(default=True, description="Allow CORS credentials")
    CORS_METHODS: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods"
    )
    CORS_HEADERS: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS headers"
    )
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_STORAGE_URI: Optional[str] = Field(default=None, description="Rate limit storage URI")
    
    # Session Configuration
    SESSION_EXPIRE_SECONDS: int = Field(default=86400, description="Session expiry in seconds")
    REDIS_SESSION_PREFIX: str = Field(default="session:", description="Redis session key prefix")
    REDIS_RATE_LIMIT_PREFIX: str = Field(default="rate_limit:", description="Redis rate limit key prefix")
    
    # WebSocket Configuration
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, description="WebSocket heartbeat interval")
    WEBSOCKET_MAX_CONNECTIONS_PER_USER: int = Field(default=5, description="Max WebSocket connections per user")
    WEBSOCKET_MESSAGE_QUEUE_SIZE: int = Field(default=1000, description="WebSocket message queue size")
    
    # File Upload Configuration
    UPLOAD_DIR: str = Field(default="uploads", description="File upload directory")
    FILE_STORAGE_TYPE: str = Field(default="local", description="File storage type (local/s3)")
    MAX_FILE_SIZE: int = Field(10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default_factory=lambda: [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf", "text/plain", "application/json"
        ],
        description="Allowed file MIME types"
    )
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS secret access key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    S3_BUCKET_NAME: Optional[str] = Field(default=None, description="S3 bucket name")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key for AI features")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    OPENAI_MAX_TOKENS: int = Field(default=500, description="Maximum tokens for OpenAI responses")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="Temperature for OpenAI responses")
    
    # Search Configuration
    SEARCH_RESULTS_PER_PAGE: int = Field(default=20, description="Default search results per page")
    SEARCH_MAX_RESULTS: int = Field(default=1000, description="Maximum search results to return")
    
    # Cache Configuration
    CACHE_TTL_SEARCH: int = Field(default=300, description="Search results cache TTL in seconds")
    CACHE_TTL_SUMMARY: int = Field(default=3600, description="Summary cache TTL in seconds")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    
    # Server Configuration
    WORKERS: int = Field(default=1, description="Number of worker processes")
    ACCESS_LOG: bool = Field(default=True, description="Enable access logging")
    
    # Encryption Configuration
    ENCRYPTION_KEY: Optional[str] = Field(default=None, description="Encryption key for E2E encryption")
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def mongodb_url(self) -> str:
        """Get MongoDB connection URL."""
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return (
                f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
                f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}?authSource=admin"
            )
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings

