# Real-Time Chat Application API Specification

## Overview

This document defines the REST API endpoints and WebSocket events for the Real-Time Chat Application. The API follows RESTful principles and uses JSON for data exchange.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication with a dual-token approach:
- **Access Token**: Short-lived (30 minutes) for API requests
- **Refresh Token**: Long-lived (7 days) for token renewal

### Authentication Headers
```
Authorization: Bearer <access_token>
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details
    }
  }
}
```

## HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Default: 60 requests per minute per user
- WebSocket connections: 5 concurrent connections per user
- File uploads: 10 uploads per hour per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string (3-50 chars, unique)",
  "email": "string (valid email, unique)",
  "password": "string (min 8 chars)",
  "display_name": "string (1-100 chars)",
  "public_key": "string (RSA public key, optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "display_name": "string",
      "avatar_url": "string|null",
      "is_verified": false,
      "created_at": "datetime"
    },
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 1800
  }
}
```

#### POST /auth/login
Authenticate user and receive tokens.

**Request Body:**
```json
{
  "username": "string (username or email)",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "string",
      "display_name": "string",
      "avatar_url": "string|null",
      "last_login": "datetime"
    },
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 1800
  }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "expires_in": 1800
  }
}
```

#### POST /auth/logout
Logout user and invalidate tokens.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### User Management Endpoints

#### GET /users/me
Get current user profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "display_name": "string",
    "avatar_url": "string|null",
    "public_key": "string|null",
    "is_verified": boolean,
    "created_at": "datetime",
    "last_login": "datetime"
  }
}
```

#### PUT /users/me
Update current user profile.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "display_name": "string (optional)",
  "avatar_url": "string (optional)",
  "public_key": "string (optional)"
}
```

#### POST /users/me/avatar
Upload user avatar image.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body:**
```
file: image file (max 5MB, JPEG/PNG/GIF)
```

### Chatroom Management Endpoints

#### GET /chatrooms
List user's chatrooms.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `page`: integer (default: 1)
- `limit`: integer (default: 20, max: 100)
- `search`: string (optional, search by name)

**Response:**
```json
{
  "success": true,
  "data": {
    "chatrooms": [
      {
        "id": "uuid",
        "name": "string",
        "description": "string|null",
        "is_private": boolean,
        "member_count": integer,
        "last_message": {
          "id": "string",
          "content": "string (encrypted)",
          "user_id": "uuid",
          "username": "string",
          "created_at": "datetime"
        },
        "unread_count": integer,
        "role": "owner|moderator|member",
        "joined_at": "datetime"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 50,
      "pages": 3
    }
  }
}
```

#### POST /chatrooms
Create a new chatroom.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "name": "string (1-100 chars)",
  "description": "string (optional, max 500 chars)",
  "is_private": boolean,
  "max_members": integer (optional, default: 100),
  "auto_summary_enabled": boolean (optional, default: true),
  "summary_threshold": integer (optional, default: 50)
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "chatroom": {
      "id": "uuid",
      "name": "string",
      "description": "string|null",
      "owner_id": "uuid",
      "is_private": boolean,
      "max_members": integer,
      "encryption_enabled": true,
      "auto_summary_enabled": boolean,
      "summary_threshold": integer,
      "created_at": "datetime"
    }
  }
}
```

#### GET /chatrooms/{chatroom_id}
Get chatroom details.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "success": true,
  "data": {
    "chatroom": {
      "id": "uuid",
      "name": "string",
      "description": "string|null",
      "owner_id": "uuid",
      "is_private": boolean,
      "max_members": integer,
      "member_count": integer,
      "encryption_enabled": boolean,
      "auto_summary_enabled": boolean,
      "summary_threshold": integer,
      "created_at": "datetime",
      "updated_at": "datetime"
    },
    "members": [
      {
        "user_id": "uuid",
        "username": "string",
        "display_name": "string",
        "avatar_url": "string|null",
        "role": "owner|moderator|member",
        "joined_at": "datetime",
        "last_read_at": "datetime",
        "is_online": boolean
      }
    ],
    "user_role": "owner|moderator|member"
  }
}
```

#### PUT /chatrooms/{chatroom_id}
Update chatroom settings (owner/moderator only).

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "max_members": integer (optional),
  "auto_summary_enabled": boolean (optional),
  "summary_threshold": integer (optional)
}
```

#### DELETE /chatrooms/{chatroom_id}
Delete chatroom (owner only).

**Headers:** `Authorization: Bearer <access_token>`

#### POST /chatrooms/{chatroom_id}/invite
Generate invitation link for chatroom.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "max_uses": integer (optional, default: 1),
  "expires_in_hours": integer (optional, default: 24)
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "invitation": {
      "id": "uuid",
      "invite_code": "string",
      "invite_url": "string",
      "max_uses": integer,
      "current_uses": 0,
      "expires_at": "datetime",
      "created_at": "datetime"
    }
  }
}
```

#### POST /chatrooms/join/{invite_code}
Join chatroom using invitation code.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "success": true,
  "data": {
    "chatroom": {
      "id": "uuid",
      "name": "string",
      "description": "string|null",
      "member_count": integer,
      "role": "member"
    }
  }
}
```

#### POST /chatrooms/{chatroom_id}/leave
Leave chatroom.

**Headers:** `Authorization: Bearer <access_token>`

### Message Endpoints

#### GET /chatrooms/{chatroom_id}/messages
Retrieve message history.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `page`: integer (default: 1)
- `limit`: integer (default: 50, max: 100)
- `before`: datetime (optional, messages before this timestamp)
- `after`: datetime (optional, messages after this timestamp)

**Response:**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "string",
        "chatroom_id": "uuid",
        "user_id": "uuid",
        "username": "string",
        "display_name": "string",
        "avatar_url": "string|null",
        "content": {
          "encrypted_data": "string",
          "iv": "string",
          "key_version": integer
        },
        "message_type": "text|image|file|system",
        "reply_to": "string|null",
        "attachments": [
          {
            "filename": "string",
            "file_type": "string",
            "file_size": integer,
            "encrypted_url": "string",
            "thumbnail_url": "string|null"
          }
        ],
        "reactions": [
          {
            "user_id": "uuid",
            "username": "string",
            "emoji": "string",
            "created_at": "datetime"
          }
        ],
        "edited_at": "datetime|null",
        "created_at": "datetime"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 500,
      "has_more": true
    }
  }
}
```

#### POST /chatrooms/{chatroom_id}/search
Search messages in chatroom.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "query": "string (search terms)",
  "message_type": "text|image|file (optional)",
  "user_id": "uuid (optional)",
  "date_from": "datetime (optional)",
  "date_to": "datetime (optional)",
  "limit": integer (optional, default: 20, max: 100)
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "message": {
          // Message object (same as above)
        },
        "relevance_score": float,
        "matched_terms": ["string"],
        "context": {
          "before": "string",
          "match": "string",
          "after": "string"
        }
      }
    ],
    "total_results": integer,
    "search_time_ms": integer
  }
}
```

#### GET /chatrooms/{chatroom_id}/summary
Get AI-generated chat summary.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `date_from`: datetime (optional)
- `date_to`: datetime (optional)
- `summary_type`: "automatic|manual" (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "id": "string",
      "chatroom_id": "uuid",
      "summary_text": "string",
      "summary_type": "automatic|manual",
      "message_count": integer,
      "start_date": "datetime",
      "end_date": "datetime",
      "participants": ["uuid"],
      "keywords": ["string"],
      "sentiment_score": float,
      "language": "string",
      "created_at": "datetime"
    }
  }
}
```

#### POST /chatrooms/{chatroom_id}/summary
Generate new chat summary.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "date_from": "datetime (optional)",
  "date_to": "datetime (optional)",
  "custom_prompt": "string (optional)"
}
```

### File Upload Endpoints

#### POST /upload/file
Upload file for sharing in chat.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body:**
```
file: file (max 10MB)
chatroom_id: uuid
```

**Response:**
```json
{
  "success": true,
  "data": {
    "file": {
      "id": "string",
      "filename": "string",
      "file_type": "string",
      "file_size": integer,
      "encrypted_url": "string",
      "thumbnail_url": "string|null",
      "upload_date": "datetime"
    }
  }
}
```

### Health and Monitoring Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "datetime",
    "version": "1.0.0",
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "mongodb": "healthy"
    }
  }
}
```

#### GET /metrics
Prometheus metrics endpoint (if monitoring enabled).

## WebSocket Events

The application uses WebSocket for real-time communication on the `/ws` endpoint.

### Connection
```
ws://localhost:8000/ws?token=<access_token>
```

### Client to Server Events

#### join_chatroom
Join a chatroom for real-time updates.

```json
{
  "event": "join_chatroom",
  "data": {
    "chatroom_id": "uuid"
  }
}
```

#### leave_chatroom
Leave a chatroom.

```json
{
  "event": "leave_chatroom",
  "data": {
    "chatroom_id": "uuid"
  }
}
```

#### send_message
Send a new message.

```json
{
  "event": "send_message",
  "data": {
    "chatroom_id": "uuid",
    "content": {
      "encrypted_data": "string",
      "iv": "string",
      "key_version": integer
    },
    "message_type": "text|image|file",
    "reply_to": "string|null",
    "client_id": "string"
  }
}
```

#### typing_start
Indicate user started typing.

```json
{
  "event": "typing_start",
  "data": {
    "chatroom_id": "uuid"
  }
}
```

#### typing_stop
Indicate user stopped typing.

```json
{
  "event": "typing_stop",
  "data": {
    "chatroom_id": "uuid"
  }
}
```

#### message_read
Mark messages as read.

```json
{
  "event": "message_read",
  "data": {
    "chatroom_id": "uuid",
    "message_id": "string"
  }
}
```

### Server to Client Events

#### message_received
New message received.

```json
{
  "event": "message_received",
  "data": {
    "message": {
      // Full message object
    }
  }
}
```

#### user_joined
User joined chatroom.

```json
{
  "event": "user_joined",
  "data": {
    "chatroom_id": "uuid",
    "user": {
      "id": "uuid",
      "username": "string",
      "display_name": "string",
      "avatar_url": "string|null"
    }
  }
}
```

#### user_left
User left chatroom.

```json
{
  "event": "user_left",
  "data": {
    "chatroom_id": "uuid",
    "user_id": "uuid"
  }
}
```

#### typing_indicator
User typing status update.

```json
{
  "event": "typing_indicator",
  "data": {
    "chatroom_id": "uuid",
    "user_id": "uuid",
    "username": "string",
    "is_typing": boolean
  }
}
```

#### user_online
User came online.

```json
{
  "event": "user_online",
  "data": {
    "user_id": "uuid",
    "username": "string"
  }
}
```

#### user_offline
User went offline.

```json
{
  "event": "user_offline",
  "data": {
    "user_id": "uuid",
    "username": "string"
  }
}
```

#### error
Error occurred.

```json
{
  "event": "error",
  "data": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  }
}
```

## Error Codes

### Authentication Errors
- `AUTH_INVALID_CREDENTIALS`: Invalid username/password
- `AUTH_TOKEN_EXPIRED`: Access token expired
- `AUTH_TOKEN_INVALID`: Invalid or malformed token
- `AUTH_REFRESH_TOKEN_INVALID`: Invalid refresh token
- `AUTH_USER_NOT_FOUND`: User account not found
- `AUTH_USER_INACTIVE`: User account deactivated

### Validation Errors
- `VALIDATION_REQUIRED_FIELD`: Required field missing
- `VALIDATION_INVALID_FORMAT`: Invalid field format
- `VALIDATION_LENGTH_EXCEEDED`: Field length limit exceeded
- `VALIDATION_INVALID_VALUE`: Invalid field value

### Resource Errors
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `RESOURCE_ACCESS_DENIED`: Insufficient permissions
- `RESOURCE_ALREADY_EXISTS`: Resource already exists
- `RESOURCE_LIMIT_EXCEEDED`: Resource limit reached

### Chatroom Errors
- `CHATROOM_NOT_FOUND`: Chatroom not found
- `CHATROOM_ACCESS_DENIED`: Not a member of chatroom
- `CHATROOM_FULL`: Chatroom at maximum capacity
- `CHATROOM_INVITE_INVALID`: Invalid or expired invitation
- `CHATROOM_OWNER_REQUIRED`: Owner permissions required

### Message Errors
- `MESSAGE_NOT_FOUND`: Message not found
- `MESSAGE_EDIT_DENIED`: Cannot edit this message
- `MESSAGE_DELETE_DENIED`: Cannot delete this message
- `MESSAGE_TOO_LONG`: Message exceeds length limit
- `MESSAGE_ENCRYPTION_FAILED`: Message encryption failed

### File Upload Errors
- `FILE_TOO_LARGE`: File exceeds size limit
- `FILE_TYPE_NOT_ALLOWED`: File type not permitted
- `FILE_UPLOAD_FAILED`: File upload failed
- `FILE_NOT_FOUND`: File not found

### Rate Limiting Errors
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `CONNECTION_LIMIT_EXCEEDED`: Too many WebSocket connections

This API specification provides a comprehensive foundation for building the real-time chat application with all the requested features including end-to-end encryption, search functionality, and AI-powered summaries.

