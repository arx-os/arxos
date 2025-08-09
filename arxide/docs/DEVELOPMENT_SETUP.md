# ArxIDE Development Setup Guide

## 🎯 Overview

This document provides comprehensive setup instructions for the ArxIDE development environment, including all necessary configurations, tools, and infrastructure needed before development begins.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: 16GB RAM minimum (32GB recommended)
- **Storage**: 10GB available disk space
- **Graphics**: OpenGL 3.3 compatible graphics card
- **Network**: Internet connection for dependencies and updates

### Required Software
- **Node.js**: 18.0.0 or higher
- **Go**: 1.21.0 or higher
- **Python**: 3.11.0 or higher
- **Git**: 2.30.0 or higher
- **Docker**: 20.10.0 or higher (for containerized development)
- **VS Code**: 1.80.0 or higher (for development)

## 🏗️ Project Structure Setup

### 1. Directory Structure
```bash
arxide/
├── desktop/                     # Electron application
│   ├── src/
│   │   ├── main/               # Main process
│   │   ├── renderer/           # Renderer process
│   │   └── shared/             # Shared code
│   ├── public/                 # Static assets
│   ├── dist/                   # Build output
│   └── package.json            # Desktop dependencies
├── backend/                    # Go backend services
│   ├── cmd/                    # Application entry points
│   ├── internal/               # Private application code
│   ├── pkg/                    # Public libraries
│   ├── api/                    # API definitions
│   ├── database/               # Database schemas and migrations
│   └── go.mod                  # Go module file
├── services/                   # Python AI/CAD services
│   ├── arxos_agent/           # Natural language processing
│   ├── svgx_engine/           # SVGX processing engine
│   ├── cad_processing/         # CAD operations
│   ├── simulation/             # Building simulation
│   └── requirements.txt        # Python dependencies
├── shared/                     # Shared utilities and types
│   ├── types/                  # TypeScript type definitions
│   ├── api/                    # API schemas and contracts
│   └── utils/                  # Shared utilities
├── config/                     # Configuration files
│   ├── development/            # Development environment configs
│   ├── staging/                # Staging environment configs
│   ├── production/             # Production environment configs
│   └── docker/                 # Docker configurations
├── scripts/                    # Build and deployment scripts
│   ├── build/                  # Build scripts
│   ├── deploy/                 # Deployment scripts
│   ├── test/                   # Test scripts
│   └── dev/                    # Development scripts
├── tests/                      # Test suites
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── e2e/                    # End-to-end tests
│   └── fixtures/               # Test data and fixtures
├── docs/                       # Documentation
├── .github/                    # GitHub Actions workflows
├── .vscode/                    # VS Code workspace settings
└── docker-compose.yml          # Development environment
```

### 2. Configuration Files

#### package.json (Desktop)
```json
{
  "name": "arxide-desktop",
  "version": "1.0.0",
  "description": "ArxIDE Desktop Application",
  "main": "dist/main/main.js",
  "scripts": {
    "dev": "concurrently \"npm run dev:main\" \"npm run dev:renderer\"",
    "dev:main": "tsc -w -p tsconfig.main.json",
    "dev:renderer": "vite",
    "build": "npm run build:main && npm run build:renderer",
    "build:main": "tsc -p tsconfig.main.json",
    "build:renderer": "vite build",
    "package": "electron-builder",
    "test": "jest",
    "test:e2e": "playwright test",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "electron": "^28.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "monaco-editor": "^0.45.0",
    "three": "^0.158.0",
    "@types/three": "^0.158.0",
    "axios": "^1.6.0",
    "socket.io-client": "^4.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/node": "^20.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "concurrently": "^8.0.0",
    "electron-builder": "^24.0.0",
    "eslint": "^8.0.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-react": "^7.0.0",
    "jest": "^29.0.0",
    "playwright": "^1.40.0",
    "prettier": "^3.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0"
  },
  "build": {
    "appId": "com.arxos.arxide",
    "productName": "ArxIDE",
    "directories": {
      "output": "dist"
    },
    "files": [
      "dist/**/*",
      "node_modules/**/*"
    ],
    "mac": {
      "category": "public.app-category.developer-tools"
    },
    "win": {
      "target": "nsis"
    },
    "linux": {
      "target": "AppImage"
    }
  }
}
```

#### go.mod (Backend)
```go
module arxos/arxide/backend

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/gorilla/websocket v1.5.1
    github.com/lib/pq v1.10.9
    github.com/redis/go-redis/v9 v9.3.0
    github.com/golang-jwt/jwt/v5 v5.2.0
    github.com/google/uuid v1.5.0
    github.com/spf13/viper v1.17.0
    github.com/stretchr/testify v1.8.4
    golang.org/x/crypto v0.17.0
)

require (
    github.com/bytedance/sonic v1.9.1 // indirect
    github.com/chenzhuoyu/base64x v0.0.0-20221115062448-fe3a3abad311 // indirect
    github.com/davecgh/go-spew v1.1.1 // indirect
    github.com/gabriel-vasile/mimetype v1.4.2 // indirect
    github.com/gin-contrib/sse v0.1.0 // indirect
    github.com/go-playground/locales v0.14.1 // indirect
    github.com/go-playground/universal-translator v0.18.1 // indirect
    github.com/go-playground/validator/v10 v10.14.0 // indirect
    github.com/goccy/go-json v0.10.2 // indirect
    github.com/json-iterator/go v1.1.12 // indirect
    github.com/klauspost/cpuid/v2 v2.2.4 // indirect
    github.com/leodido/go-urn v1.2.4 // indirect
    github.com/mattn/go-isatty v0.0.19 // indirect
    github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
    github.com/modern-go/reflect2 v1.0.2 // indirect
    github.com/pelletier/go-toml/v2 v2.1.0 // indirect
    github.com/pmezard/go-difflib v1.0.0 // indirect
    github.com/twitchyliquid64/golang-asm v0.15.1 // indirect
    github.com/ugorji/go/codec v1.2.11 // indirect
    golang.org/x/arch v0.3.0 // indirect
    golang.org/x/net v0.10.0 // indirect
    golang.org/x/sys v0.15.0 // indirect
    golang.org/x/text v0.14.0 // indirect
    google.golang.org/protobuf v1.30.0 // indirect
    gopkg.in/yaml.v3 v3.0.1 // indirect
)
```

#### requirements.txt (Services)
```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# AI/ML Libraries
torch==2.1.1
transformers==4.36.0
numpy==1.24.3
scipy==1.11.4
scikit-learn==1.3.2

# CAD Processing
svgpathtools==1.6.1
shapely==2.0.2
numpy==1.24.3

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1

# WebSocket
websockets==12.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Development
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1

# Security
cryptography==41.0.8
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Monitoring
prometheus-client==0.19.0
structlog==23.2.0
```

### 3. Development Environment Configuration

#### .env.development
```bash
# Application
NODE_ENV=development
ARXIDE_VERSION=1.0.0-dev

# Backend Services
BACKEND_HOST=localhost
BACKEND_PORT=8080
BACKEND_URL=http://localhost:8080

# Database
DATABASE_URL=postgresql://arxide:password@localhost:5432/arxide_dev
REDIS_URL=redis://localhost:6379

# AI Services
AI_SERVICE_HOST=localhost
AI_SERVICE_PORT=8000
AI_SERVICE_URL=http://localhost:8000

# Authentication
JWT_SECRET=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION=24h

# File Storage
STORAGE_PATH=./storage
UPLOAD_MAX_SIZE=100MB

# Logging
LOG_LEVEL=debug
LOG_FORMAT=json

# Development
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_MODE=true
ENABLE_MOCK_SERVICES=false
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: arxide_dev
      POSTGRES_USER: arxide
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U arxide"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://arxide:password@postgres:5432/arxide_dev
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - /app/tmp

  # AI Services
  ai-services:
    build:
      context: ./services
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://arxide:password@postgres:5432/arxide_dev
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./services:/app
      - /app/tmp

volumes:
  postgres_data:
  redis_data:
```

### 4. Testing Configuration

#### jest.config.js
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
```

#### playwright.config.ts
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 5. Code Quality Configuration

#### .eslintrc.js
```javascript
module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 12,
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint', 'react'],
  rules: {
    'react/react-in-jsx-scope': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-explicit-any': 'warn',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
```

#### .prettierrc
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
```

### 6. CI/CD Configuration

#### .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: arxide_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'

    - name: Setup Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        npm ci
        go mod download
        pip install -r services/requirements.txt

    - name: Run linting
      run: |
        npm run lint
        npm run type-check

    - name: Run tests
      run: |
        npm run test
        npm run test:e2e

    - name: Build
      run: npm run build

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info
```

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/arxos/arxide.git
cd arxide
```

### 2. Install Dependencies
```bash
# Desktop dependencies
cd desktop
npm install

# Backend dependencies
cd ../backend
go mod download

# Service dependencies
cd ../services
pip install -r requirements.txt
```

### 3. Start Development Environment
```bash
# Start all services with Docker
docker-compose up -d

# Start desktop application
cd desktop
npm run dev
```

### 4. Verify Setup
```bash
# Check backend health
curl http://localhost:8080/health

# Check AI services health
curl http://localhost:8000/health

# Run tests
npm run test
```

## 🔧 Development Workflow

### Daily Development
1. **Start services**: `docker-compose up -d`
2. **Start desktop**: `npm run dev`
3. **Make changes**: Edit code in your preferred editor
4. **Run tests**: `npm run test`
5. **Commit changes**: Follow conventional commits

### Code Quality
- **Linting**: `npm run lint`
- **Formatting**: `npm run format`
- **Type checking**: `npm run type-check`
- **Testing**: `npm run test`

### Debugging
- **Desktop**: Use Chrome DevTools for renderer process
- **Backend**: Use Delve for Go debugging
- **Services**: Use Python debugger or logging
- **Database**: Use pgAdmin or similar for PostgreSQL

This setup provides a complete development environment with all necessary tools, configurations, and workflows for ArxIDE development.
