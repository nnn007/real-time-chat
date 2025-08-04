# GitHub Repository Setup Guide

This guide helps you set up the GitHub repository for your RealTime Chat application with proper CI/CD pipeline.

## 🚀 Repository Setup

### 1. Initialize Git Repository

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: RealTime Chat Application"

# Add remote repository (replace with your GitHub repo URL)
git remote add origin https://github.com/yourusername/realtime-chat-app.git

# Push to GitHub
git push -u origin main
```

### 2. Repository Structure

Your repository should have the following structure:

```
realtime-chat-app/
├── .github/
│   └── workflows/
│       └── azure-deploy.yml
├── src/                    # React frontend
│   ├── components/
│   ├── contexts/
│   ├── pages/
│   ├── services/
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── websocket/
│   │   └── main.py
│   └── requirements.txt
├── database/              # Database schemas
├── docs/                  # Documentation
├── .gitignore
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── docker-compose.yml
├── Dockerfile
├── README.md
├── AZURE_DEPLOYMENT.md
└── GITHUB_SETUP.md
```

### 3. Create .gitignore

Create a `.gitignore` file:

```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# Build outputs
dist/
build/
*.egg-info/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Stores VSCode versions used for testing VSCode extensions
.vscode-test

# Python
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# Database
*.db
*.sqlite3

# Uploads
uploads/
```

## 🔧 GitHub Actions CI/CD

### 1. Create GitHub Actions Workflow

Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install frontend dependencies
      run: npm ci
    
    - name: Run frontend tests
      run: npm test --if-present
    
    - name: Build frontend
      run: npm run build
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run backend tests
      run: |
        cd backend
        python -m pytest tests/ --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        name: backend-coverage

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
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
    
    - name: Deploy to Azure Static Web Apps (Staging)
      uses: Azure/static-web-apps-deploy@v1
      with:
        azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN_STAGING }}
        repo_token: ${{ secrets.GITHUB_TOKEN }}
        app_location: "/"
        api_location: "/api"
        output_location: "dist"
        deployment_environment: staging
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Deploy to Azure App Service (Staging)
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'chat-backend-api-staging'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_STAGING }}
        package: ./backend

  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
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
    
    - name: Deploy to Azure Static Web Apps (Production)
      uses: Azure/static-web-apps-deploy@v1
      with:
        azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
        repo_token: ${{ secrets.GITHUB_TOKEN }}
        app_location: "/"
        api_location: "/api"
        output_location: "dist"
        deployment_environment: production
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Deploy to Azure App Service (Production)
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'chat-backend-api'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        package: ./backend

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'
```

### 2. Create Security Workflow

Create `.github/workflows/security.yml`:

```yaml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Bandit security scan
      uses: python-security/bandit-action@v1
      with:
        path: ./backend
        level: low
        format: json
        output-file: bandit-report.json
    
    - name: Run npm audit
      run: npm audit --audit-level moderate
    
    - name: Run safety check for Python
      run: |
        pip install safety
        safety check --json --output safety-report.json
```

### 3. Create Dependency Update Workflow

Create `.github/workflows/dependabot.yml`:

```yaml
name: Dependabot

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  update-deps:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Update npm dependencies
      run: |
        npm update
        npm audit fix
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Update Python dependencies
      run: |
        cd backend
        pip install --upgrade pip
        pip install --upgrade -r requirements.txt
        pip freeze > requirements.txt
```

## 🔐 GitHub Secrets Setup

### Required Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

#### Azure Deployment Secrets
- `AZURE_STATIC_WEB_APPS_API_TOKEN` - Production Static Web Apps token
- `AZURE_STATIC_WEB_APPS_API_TOKEN_STAGING` - Staging Static Web Apps token
- `AZURE_WEBAPP_PUBLISH_PROFILE` - Production App Service publish profile
- `AZURE_WEBAPP_PUBLISH_PROFILE_STAGING` - Staging App Service publish profile

#### Application Secrets
- `OPENAI_API_KEY` - OpenAI API key
- `JWT_SECRET_KEY` - JWT signing secret
- `DATABASE_URL` - Production database URL
- `MONGODB_URL` - Production MongoDB URL
- `REDIS_URL` - Production Redis URL

### How to Get Azure Secrets

1. **Static Web Apps Token**:
   ```bash
   az staticwebapp secrets set \
     --name chat-frontend \
     --secret-names AZURE_STATIC_WEB_APPS_API_TOKEN \
     --secret-value "your-token"
   ```

2. **App Service Publish Profile**:
   ```bash
   az webapp deployment list-publishing-profiles \
     --resource-group chat-app-rg \
     --name chat-backend-api \
     --xml
   ```

## 📋 Branch Protection Rules

### Main Branch Protection

1. Go to Settings > Branches
2. Add rule for `main` branch:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Include administrators
   - Restrict pushes that create files that match a specified pattern

### Required Status Checks

- `test` - Frontend and backend tests
- `security-scan` - Security vulnerability scan
- `deploy-staging` - Staging deployment (for develop branch)
- `deploy-production` - Production deployment (for main branch)

## 🔍 Code Quality

### 1. ESLint Configuration

Create `.eslintrc.js`:

```javascript
module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 12,
    sourceType: 'module',
  },
  plugins: ['react'],
  rules: {
    'react/react-in-jsx-scope': 'off',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
```

### 2. Prettier Configuration

Create `.prettierrc`:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

### 3. Python Code Quality

Add to `backend/requirements.txt`:

```
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
```

Create `backend/pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## 📊 GitHub Insights

### 1. Enable GitHub Insights

- Go to Settings > Options
- Enable "Issues" and "Wikis"
- Enable "Discussions" for community engagement

### 2. Set up Project Board

Create a project board with columns:
- Backlog
- To Do
- In Progress
- Review
- Done

### 3. Issue Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug report
about: Create a report to help us improve
title: ''
labels: 'bug'
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. iOS]
 - Browser: [e.g. chrome, safari]
 - Version: [e.g. 22]

**Additional context**
Add any other context about the problem here.
```

## 🚀 Release Management

### 1. Semantic Versioning

Use semantic versioning for releases:
- MAJOR.MINOR.PATCH (e.g., 1.0.0)
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### 2. Release Workflow

Create `.github/workflows/release.yml`:

```yaml
name: Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
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
    
    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
```

### 3. Automated Release Notes

Use GitHub's automatic release notes generation or create custom templates.

## 📈 Monitoring and Analytics

### 1. GitHub Analytics

- Monitor repository traffic
- Track issue and PR metrics
- Analyze contributor activity

### 2. Integration with Azure

- Connect GitHub repository to Azure DevOps
- Set up Azure Pipelines for advanced CI/CD
- Configure Azure Monitor for application insights

## 🎯 Next Steps

1. **Set up branch protection rules**
2. **Configure required status checks**
3. **Add issue templates**
4. **Set up project boards**
5. **Configure automated releases**
6. **Set up monitoring and alerts**

---

**This setup provides a robust CI/CD pipeline with security scanning, automated testing, and deployment to Azure.** 