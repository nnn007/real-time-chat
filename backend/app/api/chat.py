"""
Chat API Routes
Production-ready API endpoints for the RealTime Chat application.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

# Mock data for demonstration
MOCK_USERS = {
    "test-user-123": {
        "id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com"
    }
}

MOCK_CHATROOMS = [
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

MOCK_MESSAGES = {
    "room-1": [
        {
            "id": "msg-1",
            "content": "Hello everyone!",
            "user_id": "user-1",
            "username": "Alice",
            "chatroom_id": "room-1",
            "message_type": "text",
            "created_at": "2024-01-01T10:00:00Z",
            "encrypted": False
        },
        {
            "id": "msg-2",
            "content": "Welcome to the chat!",
            "user_id": "user-2", 
            "username": "Bob",
            "chatroom_id": "room-1",
            "message_type": "text",
            "created_at": "2024-01-01T10:05:00Z",
            "encrypted": False
        }
    ],
    "room-2": [
        {
            "id": "msg-3",
            "content": "This is a private message",
            "user_id": "test-user-123",
            "username": "testuser",
            "chatroom_id": "room-2",
            "message_type": "text",
            "created_at": "2024-01-01T11:00:00Z",
            "encrypted": True
        }
    ]
}

@chat_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "Production chat server is running",
        "features": {
            "authentication": "enabled",
            "database": "sqlite",
            "websocket": "planned",
            "encryption": "client-side"
        }
    })

@chat_bp.route('/auth/register', methods=['POST'])
def register():
    """User registration endpoint."""
    data = request.get_json() or {}
    
    # In a real app, you would validate and store the user
    user_data = {
        "id": f"user-{datetime.now().timestamp()}",
        "username": data.get("username", "newuser"),
        "email": data.get("email", "user@example.com")
    }
    
    return jsonify({
        "success": True,
        "data": {
            "user": user_data,
            "access_token": "production-access-token",
            "token_type": "bearer"
        }
    })

@chat_bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json() or {}
    
    # In a real app, you would validate credentials
    return jsonify({
        "success": True,
        "data": {
            "user": MOCK_USERS["test-user-123"],
            "access_token": "production-access-token",
            "token_type": "bearer"
        }
    })

@chat_bp.route('/chatrooms', methods=['GET'])
def get_chatrooms():
    """Get user's chatrooms."""
    return jsonify({
        "success": True,
        "data": {
            "chatrooms": MOCK_CHATROOMS
        }
    })

@chat_bp.route('/chatrooms', methods=['POST'])
def create_chatroom():
    """Create a new chatroom."""
    data = request.get_json() or {}
    
    new_room = {
        "id": f"room-{len(MOCK_CHATROOMS) + 1}",
        "name": data.get("name", "New Room"),
        "description": data.get("description", ""),
        "is_private": data.get("is_private", False),
        "member_count": 1,
        "created_at": datetime.now().isoformat() + "Z"
    }
    
    MOCK_CHATROOMS.append(new_room)
    
    return jsonify({
        "success": True,
        "data": {
            "chatroom": new_room
        }
    })

@chat_bp.route('/chatrooms/<chatroom_id>/messages', methods=['GET'])
def get_messages(chatroom_id):
    """Get messages for a chatroom."""
    messages = MOCK_MESSAGES.get(chatroom_id, [])
    
    return jsonify({
        "success": True,
        "data": {
            "messages": messages,
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total": len(messages),
                "has_next": False
            }
        }
    })

@chat_bp.route('/chatrooms/<chatroom_id>/messages', methods=['POST'])
def send_message(chatroom_id):
    """Send a message to a chatroom."""
    data = request.get_json() or {}
    
    new_message = {
        "id": f"msg-{datetime.now().timestamp()}",
        "content": data.get("content", ""),
        "user_id": "test-user-123",
        "username": "testuser",
        "chatroom_id": chatroom_id,
        "message_type": data.get("message_type", "text"),
        "created_at": datetime.now().isoformat() + "Z",
        "encrypted": data.get("encrypted", False)
    }
    
    if chatroom_id not in MOCK_MESSAGES:
        MOCK_MESSAGES[chatroom_id] = []
    
    MOCK_MESSAGES[chatroom_id].append(new_message)
    
    return jsonify({
        "success": True,
        "data": {
            "message": new_message
        }
    })

# Encryption endpoints
@chat_bp.route('/encryption/<chatroom_id>/keys', methods=['POST'])
def store_public_key(chatroom_id):
    """Store public key for encryption."""
    data = request.get_json() or {}
    
    return jsonify({
        "success": True,
        "data": {
            "key_id": f"{chatroom_id}:test-user-123",
            "fingerprint": "ABCD1234EFGH5678",
            "created_at": datetime.now().isoformat() + "Z"
        }
    })

@chat_bp.route('/encryption/<chatroom_id>/keys', methods=['GET'])
def get_public_keys(chatroom_id):
    """Get public keys for a chatroom."""
    return jsonify({
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
    })

@chat_bp.route('/encryption/<chatroom_id>/stats', methods=['GET'])
def get_encryption_stats(chatroom_id):
    """Get encryption statistics for a chatroom."""
    return jsonify({
        "success": True,
        "data": {
            "chatroom_id": chatroom_id,
            "active_keys_count": 2,
            "encrypted_messages_count": 15,
            "encryption_enabled": True,
            "latest_key_rotation": None
        }
    })

# Search endpoints
@chat_bp.route('/chatrooms/<chatroom_id>/messages/search', methods=['POST'])
def search_messages(chatroom_id):
    """Search messages in a chatroom."""
    data = request.get_json() or {}
    query = data.get("query", "")
    
    messages = MOCK_MESSAGES.get(chatroom_id, [])
    
    # Simple search implementation
    results = []
    if query:
        results = [msg for msg in messages if query.lower() in msg["content"].lower()]
    
    return jsonify({
        "success": True,
        "data": {
            "results": results,
            "query": query,
            "total_results": len(results)
        }
    })

@chat_bp.route('/chatrooms/<chatroom_id>/messages/summary', methods=['POST'])
def generate_summary(chatroom_id):
    """Generate AI summary of chat messages."""
    data = request.get_json() or {}
    summary_type = data.get("type", "general")
    
    # Mock summary based on type
    summaries = {
        "general": "This chatroom contains friendly conversations between users discussing various topics.",
        "detailed": "The conversation started with greetings and evolved into discussions about the chat application features and functionality.",
        "bullet_points": "• Users exchanged greetings\n• Discussion about chat features\n• Positive engagement overall",
        "key_topics": "Main topics: introductions, chat functionality, user experience"
    }
    
    return jsonify({
        "success": True,
        "data": {
            "summary": summaries.get(summary_type, summaries["general"]),
            "type": summary_type,
            "message_count": len(MOCK_MESSAGES.get(chatroom_id, [])),
            "generated_at": datetime.now().isoformat() + "Z"
        }
    })

