# Local Development Setup Guide

This guide will help you set up the Real-Time Chat Application for local development.

## Prerequisites

Before starting, make sure you have the following installed:

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Docker** - [Download here](https://www.docker.com/products/docker-desktop/)
- **Docker Compose** - Usually comes with Docker Desktop

## Quick Setup

The easiest way to get started is to run the automated setup script:

```bash
cd backend
python setup_local.py
```

This script will:
1. Check prerequisites
2. Install Python dependencies
3. Create the `.env` file
4. Start the databases (PostgreSQL, MongoDB, Redis)
5. Initialize database schemas
6. Test the server startup

## Manual Setup

If you prefer to set up manually or the automated script fails, follow these steps:

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Create Environment File

Copy the example environment file:

```bash
cp env.example .env
```

The `.env` file contains all the necessary configuration for local development.

### 3. Start Databases

Start the required databases using Docker Compose:

```bash
python start_databases.py
```

This will start:
- **PostgreSQL** (port 5432) - Main relational database
- **MongoDB** (port 27017) - Document database for messages
- **Redis** (port 6379) - Cache and session storage

### 4. Initialize Database Schemas

Initialize the database schemas:

```bash
python init_db.py
```

This will create all necessary tables, indexes, and initial data.

### 5. Start the Backend Server

Start the FastAPI backend server:

```bash
python start_server.py
```

The server will be available at `http://localhost:8000`

### 6. Start the Frontend

In a new terminal, navigate to the project root and start the frontend:

```bash
cd ..
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Database Management

### Start Databases
```bash
python start_databases.py
```

### Stop Databases
```bash
python stop_databases.py
```

### View Database Logs
```bash
docker-compose logs postgres
docker-compose logs mongodb
docker-compose logs redis
```

### Reset Databases
```bash
# Stop databases
python stop_databases.py

# Remove volumes (this will delete all data)
docker-compose down -v

# Start databases
python start_databases.py

# Initialize schemas
python init_db.py
```

## Troubleshooting

### Common Issues

#### 1. Docker Not Running
**Error**: `Docker is not available`
**Solution**: Make sure Docker Desktop is running

#### 2. Port Already in Use
**Error**: `Address already in use`
**Solution**: 
- Check if another service is using the port
- Stop the conflicting service
- Or change the port in `.env` file

#### 3. Database Connection Failed
**Error**: `connection refused`
**Solution**:
- Make sure databases are running: `python start_databases.py`
- Check Docker containers: `docker-compose ps`
- View logs: `docker-compose logs`

#### 4. Permission Denied
**Error**: `Permission denied`
**Solution**:
- On Windows: Run PowerShell as Administrator
- On Linux/Mac: Use `sudo` if needed

#### 5. Python Dependencies Issues
**Error**: `ModuleNotFoundError`
**Solution**:
```bash
pip install -r requirements.txt
```

### Database Connection Details

#### PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **User**: chat_user
- **Password**: chat_password_dev
- **Database**: realtime_chat

#### MongoDB
- **Host**: localhost
- **Port**: 27017
- **User**: admin
- **Password**: admin_password_dev
- **Database**: realtime_chat

#### Redis
- **Host**: localhost
- **Port**: 6379
- **Password**: (none)
- **Database**: 0

## Development Workflow

1. **Start Development Environment**:
   ```bash
   python setup_local.py
   ```

2. **Start Backend Server**:
   ```bash
   python start_server.py
   ```

3. **Start Frontend** (in new terminal):
   ```bash
   cd ..
   npm run dev
   ```

4. **Make Changes**: Edit files in `backend/app/` or `src/`

5. **Test Changes**: The server will auto-reload on changes

6. **Stop Development**:
   ```bash
   # Stop backend (Ctrl+C)
   # Stop frontend (Ctrl+C)
   # Stop databases
   python stop_databases.py
   ```

## Useful Commands

```bash
# Check database status
docker-compose ps

# View all logs
docker-compose logs

# View specific service logs
docker-compose logs postgres

# Restart a specific service
docker-compose restart postgres

# Access PostgreSQL directly
docker-compose exec postgres psql -U chat_user -d realtime_chat

# Access MongoDB directly
docker-compose exec mongodb mongosh -u admin -p admin_password_dev

# Access Redis directly
docker-compose exec redis redis-cli
```

## API Documentation

Once the server is running, you can access:
- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Next Steps

After setting up the local environment:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Test the Frontend**: Visit http://localhost:5173
3. **Read the Code**: Start with `backend/app/main.py`
4. **Check Documentation**: See `docs/` folder for more details

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. View the logs: `docker-compose logs`
3. Check the documentation in `docs/`
4. Create an issue in the project repository

Happy coding! 🚀 