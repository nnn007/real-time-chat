# Azure Deployment Guide

This guide provides step-by-step instructions for deploying the RealTime Chat application to Azure.

## 🎯 Deployment Architecture

### Azure Services Used
1. **Azure Static Web Apps** - Frontend hosting
2. **Azure App Service** - Backend API hosting
3. **Azure Database for PostgreSQL** - User and chatroom data
4. **Azure Cosmos DB (MongoDB API)** - Message storage and search
5. **Azure Cache for Redis** - Caching and pub/sub
6. **Azure OpenAI Service** - AI-powered features
7. **Azure Key Vault** - Secret management

## 📋 Prerequisites

### Azure Account Setup
1. Create an Azure account (free tier available)
2. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
3. Install Azure Functions Core Tools
4. Install Node.js and Python

### Required Azure Resources
- Azure subscription
- Resource group
- Application Insights (for monitoring)

## 🚀 Step-by-Step Deployment

### 1. Azure CLI Setup

```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "your-subscription-id"

# Create resource group
az group create --name "chat-app-rg" --location "East US"
```

### 2. Create Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group chat-app-rg \
  --name chat-postgres-server \
  --admin-user postgres \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --version 15 \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group chat-app-rg \
  --server-name chat-postgres-server \
  --database-name realtime_chat

# Get connection string
az postgres flexible-server show-connection-string \
  --server-name chat-postgres-server \
  --admin-user postgres \
  --admin-password "YourSecurePassword123!" \
  --database-name realtime_chat
```

### 3. Create Azure Cosmos DB (MongoDB API)

```bash
# Create Cosmos DB account
az cosmosdb create \
  --resource-group chat-app-rg \
  --name chat-cosmos-db \
  --kind MongoDB

# Create database
az cosmosdb mongodb database create \
  --resource-group chat-app-rg \
  --account-name chat-cosmos-db \
  --name realtime_chat

# Create collections
az cosmosdb mongodb collection create \
  --resource-group chat-app-rg \
  --account-name chat-cosmos-db \
  --database-name realtime_chat \
  --name messages

az cosmosdb mongodb collection create \
  --resource-group chat-app-rg \
  --account-name chat-cosmos-db \
  --database-name realtime_chat \
  --name encryption_keys

# Get connection string
az cosmosdb keys list \
  --resource-group chat-app-rg \
  --name chat-cosmos-db \
  --type connection-strings
```

### 4. Create Azure Cache for Redis

```bash
# Create Redis cache
az redis create \
  --resource-group chat-app-rg \
  --name chat-redis-cache \
  --location "East US" \
  --sku Basic \
  --vm-size C0

# Get connection string
az redis show-connection-string \
  --resource-group chat-app-rg \
  --name chat-redis-cache
```

### 5. Create Azure OpenAI Service

```bash
# Create OpenAI service
az cognitiveservices account create \
  --resource-group chat-app-rg \
  --name chat-openai \
  --location "East US" \
  --kind OpenAI \
  --sku S0

# Get API key
az cognitiveservices account keys list \
  --resource-group chat-app-rg \
  --name chat-openai
```

### 6. Create Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --resource-group chat-app-rg \
  --name chat-key-vault \
  --location "East US"

# Store secrets
az keyvault secret set \
  --vault-name chat-key-vault \
  --name "JWT-SECRET-KEY" \
  --value "your-super-secret-jwt-key"

az keyvault secret set \
  --vault-name chat-key-vault \
  --name "OPENAI-API-KEY" \
  --value "your-openai-api-key"
```

### 7. Deploy Backend to Azure App Service

```bash
# Create App Service plan
az appservice plan create \
  --resource-group chat-app-rg \
  --name chat-app-plan \
  --sku B1 \
  --is-linux

# Create App Service
az webapp create \
  --resource-group chat-app-rg \
  --plan chat-app-plan \
  --name chat-backend-api \
  --runtime "PYTHON:3.11"

# Configure environment variables
az webapp config appsettings set \
  --resource-group chat-app-rg \
  --name chat-backend-api \
  --settings \
    POSTGRES_URL="your-postgres-connection-string" \
    MONGODB_URL="your-cosmos-db-connection-string" \
    REDIS_URL="your-redis-connection-string" \
    OPENAI_API_KEY="@Microsoft.KeyVault(SecretUri=https://chat-key-vault.vault.azure.net/secrets/OPENAI-API-KEY/)" \
    JWT_SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://chat-key-vault.vault.azure.net/secrets/JWT-SECRET-KEY/)" \
    ENVIRONMENT="production" \
    DEBUG="false"

# Deploy backend code
cd backend
az webapp deployment source config-local-git \
  --resource-group chat-app-rg \
  --name chat-backend-api

git add .
git commit -m "Deploy backend to Azure"
git push azure master
```

### 8. Deploy Frontend to Azure Static Web Apps

```bash
# Build frontend
npm run build

# Create Static Web App
az staticwebapp create \
  --resource-group chat-app-rg \
  --name chat-frontend \
  --source . \
  --location "East US" \
  --branch main \
  --app-location "/" \
  --api-location "/api" \
  --output-location "dist"

# Configure environment variables
az staticwebapp appsettings set \
  --resource-group chat-app-rg \
  --name chat-frontend \
  --setting-names \
    VITE_API_URL="https://chat-backend-api.azurewebsites.net" \
    VITE_WS_URL="wss://chat-backend-api.azurewebsites.net"
```

### 9. Configure CORS and Networking

```bash
# Configure CORS for backend
az webapp cors add \
  --resource-group chat-app-rg \
  --name chat-backend-api \
  --allowed-origins "https://chat-frontend.azurestaticapps.net"

# Configure WebSocket support
az webapp config set \
  --resource-group chat-app-rg \
  --name chat-backend-api \
  --web-sockets-enabled true
```

### 10. Set up Custom Domain (Optional)

```bash
# Add custom domain to Static Web App
az staticwebapp hostname add \
  --resource-group chat-app-rg \
  --name chat-frontend \
  --hostname "chat.yourdomain.com"

# Add custom domain to App Service
az webapp config hostname add \
  --resource-group chat-app-rg \
  --webapp-name chat-backend-api \
  --hostname "api.chat.yourdomain.com"
```

## 🔧 Configuration Files

### Azure Static Web Apps Configuration

Create `staticwebapp.config.json` in the root:

```json
{
  "routes": [
    {
      "route": "/api/*",
      "serve": "/api/index.html",
      "statusCode": 200
    },
    {
      "route": "/*",
      "serve": "/index.html",
      "statusCode": 200
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html"
  },
  "globalHeaders": {
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff"
  }
}
```

### Azure App Service Configuration

Create `.deployment` file in backend directory:

```ini
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

Create `startup.txt` in backend directory:

```bash
gunicorn --bind=0.0.0.0 --timeout 600 app.main:app
```

## 📊 Monitoring and Logging

### Application Insights Setup

```bash
# Create Application Insights
az monitor app-insights component create \
  --resource-group chat-app-rg \
  --app chat-app-insights \
  --location "East US" \
  --kind web

# Get instrumentation key
az monitor app-insights component show \
  --resource-group chat-app-rg \
  --app chat-app-insights \
  --query "InstrumentationKey"
```

### Log Analytics Workspace

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group chat-app-rg \
  --workspace-name chat-logs
```

## 🔐 Security Configuration

### SSL/TLS Configuration

```bash
# Enable HTTPS for App Service
az webapp update \
  --resource-group chat-app-rg \
  --name chat-backend-api \
  --https-only true

# Configure SSL binding
az webapp config ssl bind \
  --resource-group chat-app-rg \
  --name chat-backend-api \
  --certificate-thumbprint "your-certificate-thumbprint" \
  --ssl-type SNI
```

### Network Security

```bash
# Configure IP restrictions
az webapp config access-restriction add \
  --resource-group chat-app-rg \
  --name chat-backend-api \
  --rule-name "Allow Static Web App" \
  --action Allow \
  --ip-address "your-static-web-app-ip"
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build frontend
      run: npm run build
    
    - name: Deploy to Azure Static Web Apps
      uses: Azure/static-web-apps-deploy@v1
      with:
        azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
        repo_token: ${{ secrets.GITHUB_TOKEN }}
        app_location: "/"
        api_location: "/api"
        output_location: "dist"
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Deploy to Azure App Service
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'chat-backend-api'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        package: ./backend
```

## 📈 Scaling Configuration

### Auto-scaling Rules

```bash
# Configure auto-scaling for App Service
az monitor autoscale create \
  --resource-group chat-app-rg \
  --resource chat-backend-api \
  --resource-type Microsoft.Web/sites \
  --name chat-backend-autoscale \
  --min-count 1 \
  --max-count 10 \
  --count 2

# Add scaling rule
az monitor autoscale rule create \
  --resource-group chat-app-rg \
  --autoscale-name chat-backend-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

## 🔍 Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure CORS is properly configured
2. **Database Connection**: Check connection strings and firewall rules
3. **WebSocket Issues**: Verify WebSocket support is enabled
4. **Memory Issues**: Monitor and adjust App Service plan

### Debug Commands

```bash
# Check App Service logs
az webapp log tail --resource-group chat-app-rg --name chat-backend-api

# Check Static Web App logs
az staticwebapp logs show --resource-group chat-app-rg --name chat-frontend

# Test database connectivity
az webapp ssh --resource-group chat-app-rg --name chat-backend-api
```

## 💰 Cost Optimization

### Azure Cost Management

1. **Use Free Tier**: Start with free tier services
2. **Reserved Instances**: Consider reserved instances for production
3. **Auto-scaling**: Configure proper auto-scaling rules
4. **Monitoring**: Set up cost alerts

### Estimated Monthly Costs (Basic Setup)

- Azure Static Web Apps: $0 (Free tier)
- Azure App Service (B1): ~$13/month
- Azure Database for PostgreSQL (Basic): ~$25/month
- Azure Cosmos DB (Serverless): ~$25/month
- Azure Cache for Redis (Basic): ~$13/month
- Azure OpenAI Service: Pay-per-use
- **Total**: ~$76/month

## 🎯 Next Steps

1. **Set up monitoring and alerts**
2. **Configure backup strategies**
3. **Implement CI/CD pipeline**
4. **Set up custom domain and SSL**
5. **Configure CDN for static assets**
6. **Set up disaster recovery plan**

---

**This deployment guide provides a production-ready setup for your RealTime Chat application on Azure.** 