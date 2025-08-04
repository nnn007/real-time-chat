"""
Real-Time Chat Application - FastAPI Backend
Main application entry point with FastAPI setup and middleware configuration.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.chatrooms import router as chatrooms_router
from app.api.messages import router as messages_router
from app.api.upload import router as upload_router
from app.api.encryption import router as encryption_router
from app.core.config import get_settings
from app.core.database import close_db_connections, init_db_connections
from app.core.exceptions import (
    ChatApplicationException,
    chat_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.websocket.connection_manager import ConnectionManager
from app.websocket.router import websocket_router

# Configure structured logging
logger = structlog.get_logger(__name__)

# Initialize settings
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize connection manager for WebSocket
connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Handles startup and shutdown events for database connections and other resources.
    """
    logger.info("Starting Real-Time Chat Application")
    
    # Startup
    try:
        await init_db_connections()
        logger.info("Database connections initialized")
        
        # Initialize Prometheus metrics
        if settings.ENABLE_METRICS:
            instrumentator = Instrumentator()
            instrumentator.instrument(app).expose(app)
            logger.info("Prometheus metrics enabled")
            
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    yield
    
    # Shutdown
    try:
        await close_db_connections()
        logger.info("Database connections closed")
        logger.info("Real-Time Chat Application shutdown complete")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Real-Time Chat Application with E2E Encryption",
        docs_url="/docs" if settings.ENABLE_API_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
        lifespan=lifespan,
    )
    
    # Add security middleware
    if settings.ENABLE_SECURITY_HEADERS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"] if settings.ENVIRONMENT == "development" else [settings.HOST]
        )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )
    
    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add custom exception handlers
    app.add_exception_handler(ChatApplicationException, chat_exception_handler)
    app.add_exception_handler(Exception, http_exception_handler)
    
    # Add validation exception handler
    from pydantic import ValidationError
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # Add middleware for request logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests for monitoring and debugging."""
        start_time = time.time()
        
        # Log request
        logger.info(
            "HTTP request started",
            method=request.method,
            url=str(request.url),
            client_ip=get_remote_address(request),
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                "HTTP request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time,
            )
            
            # Add process time header
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "HTTP request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=process_time,
            )
            raise
    
    # Include API routers
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/users", tags=["Users"])
    app.include_router(chatrooms_router, prefix="/chatrooms", tags=["Chatrooms"])
    app.include_router(messages_router, prefix="/chatrooms", tags=["Messages"])
    app.include_router(upload_router, prefix="/upload", tags=["File Upload"])
    app.include_router(encryption_router, prefix="/encryption", tags=["Encryption"])
    
    # Include WebSocket router
    app.include_router(websocket_router)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint for monitoring and load balancers.
        
        Returns:
            dict: Health status and system information
        """
        try:
            # Check database connections
            from app.core.database import check_database_health
            db_health = await check_database_health()
            
            return {
                "success": True,
                "data": {
                    "status": "healthy" if db_health["all_healthy"] else "degraded",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": settings.APP_VERSION,
                    "environment": settings.ENVIRONMENT,
                    "services": db_health["services"],
                }
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": {
                        "code": "HEALTH_CHECK_FAILED",
                        "message": "Service health check failed",
                        "details": {"error": str(e)}
                    }
                }
            )
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """
        Root endpoint with basic application information.
        
        Returns:
            dict: Application information
        """
        return {
            "success": True,
            "data": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "description": "Real-Time Chat Application with E2E Encryption",
                "docs_url": "/docs" if settings.ENABLE_API_DOCS else None,
                "websocket_url": "/ws",
            }
        }
    
    return app


# Create the application instance
app = create_application()

# Make connection manager available globally
app.state.connection_manager = connection_manager


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        access_log=settings.ACCESS_LOG,
        log_level=settings.LOG_LEVEL.lower(),
    )

