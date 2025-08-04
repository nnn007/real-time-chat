# RealTime Chat Application

A modern, secure real-time chat application with end-to-end encryption, AI-powered summaries, and full-text search capabilities. Built with React, FastAPI, and multiple database technologies.

## 🚀 Project Status

This project is currently being organized and prepared for Azure deployment. The codebase includes:

### ✅ Completed Features
- **Backend**: FastAPI with comprehensive API endpoints
- **Frontend**: React components with authentication and chat functionality
- **Database**: PostgreSQL, MongoDB, and Redis configurations
- **Security**: End-to-end encryption, JWT authentication
- **AI Features**: OpenAI-powered chat summaries and search
- **Real-time**: WebSocket communication

### 🔧 Current Organization
- Frontend files are being organized into proper React structure
- Backend files are being moved to FastAPI structure
- Dependencies and build configurations are being set up

## 🛠️ Technology Stack

### Frontend
- **React 18**: Modern React with hooks and context
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

### Backend
- **FastAPI**: High-performance async Python framework
- **WebSocket**: Real-time bidirectional communication
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization

### Databases
- **PostgreSQL**: User accounts and chatroom metadata
- **MongoDB**: Message storage and full-text search
- **Redis**: Caching, pub/sub, and rate limiting

### Security & Encryption
- **Web Crypto API**: Browser-native cryptographic operations
- **ECDH P-256**: Elliptic curve key exchange
- **AES-GCM**: Authenticated encryption
- **JWT**: Secure authentication tokens

### AI & Search
- **OpenAI API**: GPT-powered chat summaries
- **MongoDB Text Search**: Full-text indexing and search
- **Redis Caching**: Performance optimization

## 📁 Project Structure

```
realtime-chat-app/
├── src/                    # React frontend
│   ├── components/         # Reusable UI components
│   ├── contexts/          # React contexts (Auth, Chat, Theme)
│   ├── pages/             # Page components
│   ├── services/          # API and WebSocket services
│   └── App.jsx            # Main application component
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration and database
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic services
│   │   └── websocket/    # WebSocket handling
│   └── requirements.txt  # Backend dependencies
├── database/              # Database schemas and configs
├── docker-compose.yml     # Development environment
├── Dockerfile            # Production container
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose (for development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd realtime-chat-app
   ```

2. **Frontend Setup**
   ```bash
   npm install
   npm run dev
   ```

3. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your database URLs and API keys
   
   # Start the development server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Database Setup (Docker)**
   ```bash
   docker-compose up -d postgres mongodb redis
   ```

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database URLs
POSTGRES_URL=postgresql+asyncpg://user:password@localhost/chatdb
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# OpenAI API (for chat summaries)
OPENAI_API_KEY=your_openai_api_key

# JWT Secret
JWT_SECRET_KEY=your_jwt_secret_key

# Application Settings
ENVIRONMENT=development
DEBUG=true
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token

### Chatrooms
- `GET /chatrooms` - Get user's chatrooms
- `POST /chatrooms` - Create new chatroom
- `GET /chatrooms/{id}` - Get chatroom details

### Messages
- `GET /chatrooms/{id}/messages` - Get messages
- `POST /chatrooms/{id}/messages` - Send message
- `POST /chatrooms/{id}/messages/search` - Search messages
- `POST /chatrooms/{id}/messages/summary` - Generate AI summary

### Encryption
- `POST /encryption/{chatroom_id}/keys` - Store public key
- `GET /encryption/{chatroom_id}/keys` - Get public keys
- `GET /encryption/{chatroom_id}/stats` - Get encryption statistics

## 🚀 Deployment

### Azure Deployment (Coming Soon)

The application will be deployed to Azure with the following architecture:

1. **Frontend**: Azure Static Web Apps
2. **Backend**: Azure App Service
3. **Databases**: Azure Database for PostgreSQL, Azure Cosmos DB (MongoDB), Azure Cache for Redis
4. **AI Services**: Azure OpenAI Service

### Local Production Build

```bash
# Build frontend
npm run build

# Start backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔐 Security Features

### End-to-End Encryption
- Client-side encryption using Web Crypto API
- ECDH key exchange for secure key sharing
- AES-GCM encryption for messages
- Automatic key rotation

### Security Best Practices
- JWT tokens for authentication
- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS configuration
- HTTPS enforcement

## 🤖 AI Integration

### OpenAI Chat Summaries
- General conversation summaries
- Detailed analysis with key points
- Bullet point summaries
- Key topic extraction

### Search Capabilities
- Full-text search across messages
- MongoDB text indexing
- Real-time search suggestions

## 📝 Development Notes

### Architecture Decisions
- Multi-database approach for optimal performance
- Client-side encryption for true E2E security
- WebSocket for real-time communication
- React context for state management

### Performance Optimizations
- Message pagination
- Redis caching
- Database indexing
- Lazy loading

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ using modern web technologies and best practices for security, performance, and user experience.**

