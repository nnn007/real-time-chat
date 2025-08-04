# Real-Time Chat Application Architecture

## System Overview

This document outlines the architecture for a comprehensive real-time chat application featuring end-to-end encryption, full-text search, AI-powered summaries, and secure private chatrooms. The system is designed with scalability, security, and performance in mind.

## Architecture Components

### Frontend Layer
- **Technology**: React 18 with TypeScript
- **State Management**: Redux Toolkit with RTK Query
- **Real-time Communication**: WebSocket client with automatic reconnection
- **Encryption**: Client-side E2E encryption using Web Crypto API
- **UI Framework**: Material-UI (MUI) for consistent design
- **Routing**: React Router for navigation

### Backend Layer
- **API Framework**: FastAPI with Python 3.11
- **WebSocket Server**: FastAPI WebSocket support with connection management
- **Authentication**: JWT tokens with refresh mechanism
- **Rate Limiting**: Redis-based rate limiting for API endpoints
- **Background Tasks**: Celery for async processing (summaries, indexing)

### Database Layer

#### PostgreSQL (Primary Database)
- **Purpose**: User accounts, chatroom metadata, permissions
- **Tables**:
  - `users`: User profiles and authentication data
  - `chatrooms`: Chatroom information and settings
  - `chatroom_members`: User-chatroom relationships
  - `invitations`: Chatroom invitation links and permissions

#### MongoDB (Message Storage)
- **Purpose**: Message history and metadata
- **Collections**:
  - `messages`: Encrypted message content and metadata
  - `message_search_index`: Full-text search index
  - `chat_summaries`: AI-generated conversation summaries

#### Redis (Caching & Real-time)
- **Purpose**: Session management, pub/sub, caching, rate limiting
- **Key Patterns**:
  - `session:{user_id}`: User session data
  - `chatroom:{room_id}:members`: Active chatroom members
  - `search_cache:{query_hash}`: Cached search results
  - `rate_limit:{user_id}:{endpoint}`: Rate limiting counters

## Security Architecture

### End-to-End Encryption
The application implements client-side encryption to ensure messages remain private even from the server operators.

#### Key Management
- **Key Generation**: Each chatroom generates a unique AES-256 encryption key
- **Key Exchange**: Secure key distribution using RSA public key cryptography
- **Key Rotation**: Automatic key rotation for enhanced security
- **Key Storage**: Keys stored locally in browser's IndexedDB, never on server

#### Encryption Flow
1. **Message Sending**:
   - Client encrypts message with chatroom's AES key
   - Encrypted payload sent to server via WebSocket
   - Server stores encrypted message without decryption capability

2. **Message Receiving**:
   - Server broadcasts encrypted message to chatroom members
   - Clients decrypt message locally using stored key
   - Decrypted content displayed in chat interface

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication with access/refresh token pairs
- **Role-Based Access**: Chatroom owners, moderators, and members with different permissions
- **Invitation System**: Secure, time-limited invitation links for private chatrooms
- **Session Management**: Redis-based session tracking with automatic cleanup

## Real-Time Communication

### WebSocket Implementation
- **Connection Management**: Automatic reconnection with exponential backoff
- **Message Broadcasting**: Redis pub/sub for scalable message distribution
- **Presence System**: Real-time user online/offline status
- **Typing Indicators**: Live typing status updates

### Message Flow
1. User sends message through WebSocket connection
2. Server validates user permissions and rate limits
3. Message encrypted on client, sent to server
4. Server publishes message to Redis pub/sub channel
5. All connected clients in chatroom receive message
6. Clients decrypt and display message

## Search & AI Features

### Full-Text Search
- **Search Index**: MongoDB text indexes on decrypted message content
- **Caching Strategy**: Redis caching for frequent search queries
- **Search Scope**: Per-chatroom search with permission enforcement
- **Performance**: Optimized queries with pagination and relevance scoring

### AI-Powered Summaries
- **LLM Integration**: OpenAI GPT-4 API for conversation summarization
- **Trigger Conditions**: Automatic summaries after configurable message thresholds
- **Privacy Preservation**: Messages decrypted client-side before summarization
- **Caching**: Summary results cached in MongoDB for quick retrieval

## Scalability Considerations

### Horizontal Scaling
- **Stateless Backend**: FastAPI servers can be load-balanced
- **Database Sharding**: MongoDB collections can be sharded by chatroom_id
- **Redis Clustering**: Redis cluster for high-availability caching
- **CDN Integration**: Static assets served via CDN

### Performance Optimizations
- **Connection Pooling**: Database connection pools for efficient resource usage
- **Message Batching**: WebSocket message batching for reduced network overhead
- **Lazy Loading**: Progressive message loading in chat interface
- **Compression**: WebSocket message compression for bandwidth efficiency

## Deployment Architecture

### Development Environment
- **Docker Compose**: Local development with all services containerized
- **Hot Reloading**: Frontend and backend development servers with live reload
- **Database Seeding**: Automated test data generation for development

### Production Environment
- **Backend Deployment**: Railway/Render for FastAPI application hosting
- **Frontend Deployment**: Vercel/Netlify for React application hosting
- **Database Hosting**: 
  - PostgreSQL: Railway/Supabase managed database
  - MongoDB: MongoDB Atlas cluster
  - Redis: Redis Cloud or Railway Redis addon

### Configuration Management
- **Environment Variables**: Secure configuration via environment variables
- **Secrets Management**: API keys and sensitive data in secure vaults
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **SSL/TLS**: HTTPS enforcement for all communications

## API Specification

### Authentication Endpoints
```
POST /auth/register - User registration
POST /auth/login - User authentication
POST /auth/refresh - Token refresh
POST /auth/logout - User logout
```

### Chatroom Management
```
GET /chatrooms - List user's chatrooms
POST /chatrooms - Create new chatroom
GET /chatrooms/{id} - Get chatroom details
PUT /chatrooms/{id} - Update chatroom settings
DELETE /chatrooms/{id} - Delete chatroom
POST /chatrooms/{id}/invite - Generate invitation link
POST /chatrooms/join/{invite_code} - Join via invitation
```

### Message Operations
```
GET /chatrooms/{id}/messages - Retrieve message history
POST /chatrooms/{id}/search - Search messages
GET /chatrooms/{id}/summary - Get AI summary
```

### WebSocket Events
```
message_send - Send new message
message_receive - Receive new message
typing_start - User starts typing
typing_stop - User stops typing
user_join - User joins chatroom
user_leave - User leaves chatroom
```

## Security Measures

### Data Protection
- **Encryption at Rest**: Database encryption for sensitive data
- **Encryption in Transit**: TLS 1.3 for all network communications
- **Key Management**: Secure key generation and storage practices
- **Data Minimization**: Collect only necessary user information

### Access Control
- **Permission System**: Granular permissions for chatroom operations
- **Rate Limiting**: API endpoint rate limiting to prevent abuse
- **Input Validation**: Comprehensive input sanitization and validation
- **CSRF Protection**: Cross-site request forgery prevention

### Monitoring & Logging
- **Audit Logs**: Comprehensive logging of user actions
- **Error Tracking**: Automated error reporting and alerting
- **Performance Monitoring**: Real-time performance metrics
- **Security Monitoring**: Intrusion detection and prevention

This architecture provides a solid foundation for building a secure, scalable, and feature-rich real-time chat application that meets all specified requirements while maintaining high performance and security standards.

