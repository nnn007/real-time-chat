# Deployment Guide

This guide provides detailed instructions for deploying the RealTime Chat application in various environments.

## 🌐 Production Deployment

### Current Live Deployments

The application is currently deployed and accessible at:

- **Frontend Only**: https://matzkpcj.manus.space
- **Full-Stack Application**: https://77h9ikcw5198.manus.space
- **API Health Check**: https://77h9ikcw5198.manus.space/health

### Deployment Architecture

The production deployment uses a Flask backend that serves both the API and the React frontend from a single domain, eliminating CORS issues and simplifying deployment.

## 🚀 Quick Deploy (Recommended)

### Option 1: Full-Stack Flask Deployment

This is the recommended approach for production as it serves both frontend and backend from a single URL.

1. **Prepare the Flask Backend**
   ```bash
   # Navigate to the production backend directory
   cd realtime-chat-app/backend-prod
   
   # Activate virtual environment
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Build and Copy Frontend**
   ```bash
   # Build the React frontend
   cd ../frontend
   npm run build
   
   # Copy built files to Flask static directory
   cd ../backend-prod
   cp -r ../frontend/dist/* src/static/
   ```

3. **Test Locally**
   ```bash
   # Start the Flask server
   python src/main.py
   
   # Visit http://localhost:5000 to test
   ```

4. **Deploy to Production**
   - Use your preferred hosting platform (Heroku, DigitalOcean, AWS, etc.)
   - Or use the Manus deployment service as shown in the project

### Option 2: Separate Frontend/Backend Deployment

If you prefer to deploy frontend and backend separately:

1. **Deploy Frontend**
   ```bash
   cd frontend
   npm run build
   # Deploy the 'dist' folder to your static hosting service
   ```

2. **Deploy Backend**
   ```bash
   cd backend
   # Configure environment variables
   # Deploy using your preferred Python hosting service
   ```

3. **Update API URLs**
   - Update the `VITE_API_URL` in the frontend to point to your backend URL
   - Ensure CORS is properly configured in the backend

## 🔧 Environment Configuration

### Production Environment Variables

Create appropriate environment files for production:

**For Flask Backend (backend-prod/.env)**
```env
FLASK_ENV=production
SECRET_KEY=your_production_secret_key_here
DATABASE_URL=sqlite:///production.db
DEBUG=False
```

**For FastAPI Backend (backend/.env)**
```env
ENVIRONMENT=production
DEBUG=false
POSTGRES_URL=postgresql+asyncpg://user:pass@host:5432/dbname
MONGODB_URL=mongodb://user:pass@host:27017/dbname
REDIS_URL=redis://user:pass@host:6379/0
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret_key
```

**For Frontend (.env.production)**
```env
VITE_API_URL=https://your-backend-domain.com
VITE_WS_URL=wss://your-backend-domain.com
```

## 🐳 Docker Deployment

### Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_URL=postgresql+asyncpg://postgres:password@db:5432/chatdb
      - MONGODB_URL=mongodb://mongo:27017/chatdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - mongo
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=chatdb
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  mongo_data:
  redis_data:
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## ☁️ Cloud Platform Deployment

### Heroku Deployment

1. **Prepare for Heroku**
   ```bash
   # Create Procfile for Flask
   echo "web: python src/main.py" > Procfile
   
   # Create runtime.txt
   echo "python-3.11.0" > runtime.txt
   ```

2. **Deploy to Heroku**
   ```bash
   heroku create your-app-name
   heroku config:set FLASK_ENV=production
   git push heroku main
   ```

### Vercel Deployment (Frontend Only)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy Frontend**
   ```bash
   cd frontend
   vercel --prod
   ```

### Netlify Deployment (Frontend Only)

1. **Build the frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to Netlify**
   - Drag and drop the `dist` folder to Netlify
   - Or connect your GitHub repository for automatic deployments

### AWS Deployment

#### Using AWS Amplify (Frontend)
1. Connect your GitHub repository to AWS Amplify
2. Configure build settings:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd frontend
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: frontend/dist
       files:
         - '**/*'
   ```

#### Using AWS ECS (Backend)
1. Create a Docker image and push to ECR
2. Create an ECS service with the image
3. Configure load balancer and security groups

## 🗄️ Database Setup

### PostgreSQL Setup
```sql
-- Create database
CREATE DATABASE chatdb;

-- Create user
CREATE USER chatuser WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE chatdb TO chatuser;
```

### MongoDB Setup
```javascript
// Create database and collections
use chatdb;

// Create indexes for better performance
db.messages.createIndex({ "chatroom_id": 1, "created_at": -1 });
db.messages.createIndex({ "$**": "text" }); // Full-text search
db.encryption_keys.createIndex({ "chatroom_id": 1, "user_id": 1 });
```

### Redis Setup
```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis (optional)
sudo nano /etc/redis/redis.conf

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## 🔒 Security Configuration

### SSL/TLS Setup

1. **Obtain SSL Certificate**
   - Use Let's Encrypt for free certificates
   - Or use your cloud provider's certificate service

2. **Configure HTTPS**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Environment Security

1. **Use Environment Variables**
   - Never commit secrets to version control
   - Use your platform's secret management

2. **Configure CORS Properly**
   ```python
   # In production, specify exact origins
   CORS(app, origins=["https://your-frontend-domain.com"])
   ```

3. **Set Secure Headers**
   ```python
   @app.after_request
   def after_request(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       return response
   ```

## 📊 Monitoring and Logging

### Application Monitoring

1. **Health Check Endpoint**
   - Use `/health` endpoint for monitoring
   - Set up uptime monitoring services

2. **Logging Configuration**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

3. **Error Tracking**
   - Integrate with Sentry or similar service
   - Monitor application errors and performance

### Database Monitoring

1. **Connection Pooling**
   - Monitor database connection usage
   - Set appropriate pool sizes

2. **Query Performance**
   - Monitor slow queries
   - Optimize database indexes

## 🚀 Performance Optimization

### Frontend Optimization

1. **Bundle Analysis**
   ```bash
   npm run build -- --analyze
   ```

2. **Code Splitting**
   - Implement lazy loading for routes
   - Split vendor bundles

3. **Caching Strategy**
   - Configure proper cache headers
   - Use CDN for static assets

### Backend Optimization

1. **Database Optimization**
   - Use connection pooling
   - Implement query caching
   - Add appropriate indexes

2. **Redis Caching**
   - Cache frequently accessed data
   - Implement cache invalidation strategies

3. **WebSocket Optimization**
   - Use Redis pub/sub for scaling
   - Implement connection cleanup

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    
    - name: Build Frontend
      run: |
        cd frontend
        npm ci
        npm run build
    
    - name: Deploy to Production
      run: |
        # Your deployment commands here
        echo "Deploying to production..."
```

## 🆘 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure backend CORS is configured correctly
   - Check that frontend API URL matches backend URL

2. **WebSocket Connection Issues**
   - Verify WebSocket URL is correct (ws:// or wss://)
   - Check firewall and proxy settings

3. **Database Connection Errors**
   - Verify database credentials and connection strings
   - Check network connectivity and firewall rules

4. **Build Failures**
   - Clear node_modules and reinstall dependencies
   - Check for version compatibility issues

### Debug Commands

```bash
# Check application logs
tail -f /var/log/your-app.log

# Test database connection
psql -h localhost -U chatuser -d chatdb -c "SELECT 1;"

# Test Redis connection
redis-cli ping

# Check port availability
netstat -tulpn | grep :5000
```

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review application logs
3. Verify environment configuration
4. Test individual components separately

---

**This deployment guide covers the most common deployment scenarios. Choose the approach that best fits your infrastructure and requirements.**

