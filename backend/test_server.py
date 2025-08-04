"""
Test Server
Simple FastAPI server for testing without database dependencies.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create FastAPI app
app = FastAPI(
    title="RealTime Chat API - Test Mode",
    version="1.0.0",
    description="Test version of the Real-Time Chat Application API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "RealTime Chat API - Test Mode", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Test server is running",
        "features": {
            "authentication": "mock",
            "database": "disabled",
            "websocket": "disabled",
            "encryption": "client-side only"
        }
    }

# Mock authentication endpoints
@app.post("/auth/register")
async def mock_register():
    """Mock registration endpoint."""
    return {
        "success": True,
        "data": {
            "user": {
                "id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com"
            },
            "access_token": "mock-access-token",
            "token_type": "bearer"
        }
    }

@app.post("/auth/login")
async def mock_login():
    """Mock login endpoint."""
    return {
        "success": True,
        "data": {
            "user": {
                "id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com"
            },
            "access_token": "mock-access-token",
            "token_type": "bearer"
        }
    }

@app.get("/chatrooms")
async def mock_chatrooms():
    """Mock chatrooms endpoint."""
    return {
        "success": True,
        "data": {
            "chatrooms": [
                {
                    "id": "room-1",
                    "name": "General Chat",
                    "description": "General discussion room",
                    "is_private": False,
                    "member_count": 5,
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "room-2", 
                    "name": "Private Room",
                    "description": "Private encrypted chat",
                    "is_private": True,
                    "member_count": 2,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
    }

@app.get("/chatrooms/{chatroom_id}/messages")
async def mock_messages(chatroom_id: str):
    """Mock messages endpoint."""
    return {
        "success": True,
        "data": {
            "messages": [
                {
                    "id": "msg-1",
                    "content": "Hello everyone!",
                    "user_id": "user-1",
                    "username": "Alice",
                    "chatroom_id": chatroom_id,
                    "message_type": "text",
                    "created_at": "2024-01-01T10:00:00Z",
                    "encrypted": False
                },
                {
                    "id": "msg-2",
                    "content": "This is an encrypted message",
                    "user_id": "user-2", 
                    "username": "Bob",
                    "chatroom_id": chatroom_id,
                    "message_type": "text",
                    "created_at": "2024-01-01T10:05:00Z",
                    "encrypted": True
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total": 2,
                "has_next": False
            }
        }
    }

# Mock encryption endpoints
@app.post("/encryption/{chatroom_id}/keys")
async def mock_store_public_key(chatroom_id: str):
    """Mock store public key endpoint."""
    return {
        "success": True,
        "data": {
            "key_id": f"{chatroom_id}:test-user-123",
            "fingerprint": "ABCD1234EFGH5678",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }

@app.get("/encryption/{chatroom_id}/keys")
async def mock_get_public_keys(chatroom_id: str):
    """Mock get public keys endpoint."""
    return {
        "success": True,
        "data": {
            "chatroom_id": chatroom_id,
            "public_keys": [
                {
                    "user_id": "user-1",
                    "public_key_data": "mock-public-key-data-1",
                    "key_fingerprint": "ABCD1234EFGH5678",
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "user_id": "user-2",
                    "public_key_data": "mock-public-key-data-2", 
                    "key_fingerprint": "IJKL9012MNOP3456",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
    }

@app.get("/encryption/{chatroom_id}/stats")
async def mock_encryption_stats(chatroom_id: str):
    """Mock encryption stats endpoint."""
    return {
        "success": True,
        "data": {
            "chatroom_id": chatroom_id,
            "active_keys_count": 2,
            "encrypted_messages_count": 15,
            "encryption_enabled": True,
            "latest_key_rotation": None
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

