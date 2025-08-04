# Real-Time Chat Application - Backend

This is the FastAPI backend for the Real-Time Chat Application with E2E encryption support.

## 🏗️ Architecture

The backend uses a multi-database architecture:

- **PostgreSQL**: User accounts, chatroom metadata, and permissions
- **MongoDB**: Message storage and search indexing
- **Redis**: Caching, sessions, and real-time features
- **FastAPI**: REST API and WebSocket support

## 📋 Prerequisites

- Python 3.8 or higher
- Docker (optional, for easy database setup)
- PostgreSQL, MongoDB, and Redis (if not using Docker)

## 🚀 Quick Start

### Option 1: Using Docker (Recommended)

1. **Clone and navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```

3. **Start the databases with Docker:**
   ```bash
   docker-compose up -d postgres mongodb redis
   ```

4. **Initialize the databases:**
   ```bash
   python init_db.py
   ```

5. **Start the backend server:**
   ```bash
   python start_server.py
   ```

### Option 2: Manual Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

3. **Install and configure databases:**
   - PostgreSQL: Install and create database `realtime_chat`
   - MongoDB: Install and create database `realtime_chat`
   - Redis: Install and start Redis server

4. **Initialize databases:**
   ```bash
   python init_db.py
   ```

5. **Start the server:**
   ```bash
   python start_server.py
   ```

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Application
APP_NAME=RealTime Chat App
DEBUG=true
ENVIRONMENT=development

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=chat_user
POSTGRES_PASSWORD=chat_password_dev
POSTGRES_DB=realtime_chat

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PASSWORD=admin_password_dev
MONGODB_DB=realtime_chat

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### Database Setup

#### PostgreSQL Schema
The PostgreSQL schema includes:
- Users table for authentication
- Chatrooms table for room metadata
- Chatroom members for user relationships
- Invitations for room access
- User sessions for JWT management

#### MongoDB Schema
The MongoDB schema includes:
- Messages collection for encrypted chat messages
- Chat summaries for AI-generated summaries
- Message search index for full-text search
- User activity for analytics

#### Redis Configuration
Redis is used for:
- Session management
- Rate limiting
- Real-time caching
- WebSocket connection management

## 📚 API Documentation

Once the server is running, access the API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 Testing

### Test Server
For development without databases, use the test server:

```bash
python test_server.py
```

This provides mock endpoints for testing the frontend.

### Health Check
Test the server health:

```bash
curl http://localhost:8000/health
```

## 🔍 Monitoring

### Health Endpoints
- `GET /health` - Overall system health
- `GET /` - Basic application info

### Metrics (if enabled)
- Prometheus metrics at `/metrics`
- Grafana dashboards (with monitoring profile)

## 🛠️ Development

### Project Structure
```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core configuration
│   ├── models/        # Database models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── websocket/     # WebSocket handling
├── database/          # Database schemas
├── uploads/           # File uploads
├── logs/              # Application logs
├── requirements.txt   # Python dependencies
├── docker-compose.yml # Docker setup
├── setup.py          # Setup script
├── init_db.py        # Database initialization
└── start_server.py   # Server startup
```

### Adding New Features

1. **API Routes**: Add to `app/api/`
2. **Models**: Add to `app/models/`
3. **Schemas**: Add to `app/schemas/`
4. **Services**: Add to `app/services/`

### Database Migrations

For PostgreSQL schema changes:
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## 🐳 Docker

### Development
```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres mongodb redis

# View logs
docker-compose logs -f backend
```

### Production
```bash
# Start with production profile
docker-compose --profile production up -d

# Start with monitoring
docker-compose --profile monitoring up -d
```

## 🔒 Security

### Environment Variables
- Never commit `.env` files
- Use strong secret keys in production
- Rotate keys regularly

### Database Security
- Use strong passwords
- Enable SSL in production
- Restrict network access

### API Security
- Rate limiting enabled
- CORS configured
- JWT token authentication
- Input validation with Pydantic

## 📊 Performance

### Optimization Tips
- Use connection pooling
- Enable Redis caching
- Optimize database queries
- Use async/await patterns

### Monitoring
- Prometheus metrics
- Structured logging
- Health checks
- Performance profiling

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database credentials in `.env`
   - Ensure databases are running
   - Verify network connectivity

2. **Import Errors**
   - Install dependencies: `pip install -r requirements.txt`
   - Check Python version (3.8+)

3. **Port Already in Use**
   - Change port in `.env`
   - Kill existing process

4. **Permission Errors**
   - Check file permissions
   - Run with appropriate user

### Debug Mode
Enable debug mode in `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check the logs in `logs/` directory
4. Test with the test server first

## 📄 License

This project is licensed under the MIT License. 