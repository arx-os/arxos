# Development Setup Guide

## 🚀 **Local Development Environment**

This guide will get your local ARXOS development environment up and running for both Go backend and Python AI service development.

---

## 📋 **Prerequisites**

### **Required Software**
- **Go 1.21+** - [Download from golang.org](https://golang.org/dl/)
- **Python 3.9+** - [Download from python.org](https://python.org/downloads/)
- **PostgreSQL 13+** with PostGIS extension
- **Redis 6+** server
- **Git** - [Download from git-scm.com](https://git-scm.com/downloads)

### **System Requirements**
- **RAM**: Minimum 8GB, recommended 16GB+
- **Storage**: 10GB+ free space
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)

---

## 🔧 **Environment Setup**

### **1. Clone Repository**
```bash
git clone https://github.com/your-org/arxos.git
cd arxos
```

### **2. Go Environment Setup**
```bash
# Navigate to Go backend
cd core/backend

# Install Go dependencies
go mod download

# Verify Go installation
go version
# Should show: go version go1.21.x

# Check Go environment
go env GOPATH
go env GOROOT
```

### **3. Python Environment Setup**
```bash
# Navigate to AI service
cd ../../ai_service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Verify Python installation
python --version
# Should show: Python 3.9.x or higher
```

---

## 🗄️ **Database Setup**

### **PostgreSQL Installation**

#### **Windows**
1. Download from [postgresql.org](https://postgresql.org/download/windows/)
2. Install with PostGIS extension enabled
3. Set password for `postgres` user
4. Add PostgreSQL bin directory to PATH

#### **macOS**
```bash
# Using Homebrew
brew install postgresql postgis

# Start PostgreSQL service
brew services start postgresql
```

#### **Linux (Ubuntu)**
```bash
# Install PostgreSQL and PostGIS
sudo apt update
sudo apt install postgresql postgresql-contrib postgis

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### **Create Database**
```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql

# Create database with PostGIS extension
CREATE DATABASE arxos_dev;
\c arxos_dev
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

# Create application user (optional)
CREATE USER arxos_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE arxos_dev TO arxos_user;

# Exit PostgreSQL
\q
```

### **Redis Installation**

#### **Windows**
1. Download from [redis.io](https://redis.io/download)
2. Install Redis server
3. Start Redis service

#### **macOS**
```bash
# Using Homebrew
brew install redis

# Start Redis service
brew services start redis
```

#### **Linux (Ubuntu)**
```bash
# Install Redis
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

---

## ⚙️ **Configuration Setup**

### **1. Environment Variables**

Create `.env` files in both backend and AI service directories:

#### **Backend (.env)**
```bash
# core/backend/.env
DB_URL=postgres://postgres:your_password@localhost:5432/arxos_dev?sslmode=disable
REDIS_URL=redis://localhost:6379
AI_SERVICE_URL=http://localhost:5000
PORT=8080
LOG_LEVEL=debug
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
JWT_SECRET=your_jwt_secret_key_here
```

#### **AI Service (.env)**
```bash
# ai_service/.env
OPENAI_API_KEY=your_openai_api_key_here
BACKEND_URL=http://localhost:8080
PORT=5000
LOG_LEVEL=debug
```

### **2. Database Migrations**
```bash
# Navigate to backend directory
cd core/backend

# Run database migrations
go run main.go migrate

# Verify tables created
psql -U postgres -d arxos_dev -c "\dt"
```

---

## 🚀 **Starting Development Services**

### **1. Start Go Backend**
```bash
# Terminal 1 - Backend
cd core/backend

# Run with hot reload (using air for development)
go install github.com/cosmtrek/air@latest
air

# Or run directly
go run main.go
```

**Expected Output:**
```
[INFO] Starting ARXOS backend server...
[INFO] Database connected successfully
[INFO] Redis connected successfully
[INFO] Server listening on :8080
[INFO] Health check endpoint: /api/health
```

### **2. Start Python AI Service**
```bash
# Terminal 2 - AI Service
cd ai_service

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start AI service
python main.py
```

**Expected Output:**
```
[INFO] Starting ARXOS AI service...
[INFO] OpenAI API connected successfully
[INFO] Server listening on :5000
[INFO] Health check endpoint: /health
```

### **3. Verify Services**
```bash
# Test backend health
curl http://localhost:8080/api/health
# Expected: {"status":"healthy","timestamp":"..."}

# Test AI service health
curl http://localhost:5000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

---

## 🧪 **Testing Your Setup**

### **1. Upload Test PDF**
1. Open browser to `http://localhost:8080`
2. Navigate to upload interface
3. Select a PDF building plan
4. Watch processing in AI service logs
5. View extracted ArxObjects in database

### **2. Database Verification**
```bash
# Connect to database
psql -U postgres -d arxos_dev

# Check ArxObjects table
SELECT COUNT(*) FROM arxobjects;

# View sample data
SELECT id, type, system, confidence FROM arxobjects LIMIT 5;

# Exit
\q
```

### **3. API Testing**
```bash
# Test ArxObjects endpoint
curl http://localhost:8080/api/v1/arxobjects

# Test with authentication (if implemented)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8080/api/v1/arxobjects
```

---

## 🔧 **Development Tools**

### **Recommended IDEs**
- **VS Code** with Go and Python extensions
- **GoLand** for Go development
- **PyCharm** for Python development

### **VS Code Extensions**
```json
// .vscode/extensions.json
{
  "recommendations": [
    "golang.go",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-json"
  ]
}
```

### **VS Code Settings**
```json
// .vscode/settings.json
{
  "go.useLanguageServer": true,
  "go.gopath": "/path/to/your/gopath",
  "python.defaultInterpreter": "./ai_service/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black"
}
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Go Module Issues**
```bash
# Clear Go module cache
go clean -modcache

# Verify module dependencies
go mod verify

# Update dependencies
go get -u ./...
```

#### **Python Virtual Environment Issues**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify database exists
psql -U postgres -l | grep arxos

# Check PostGIS extension
psql -U postgres -d arxos_dev -c "SELECT PostGIS_Version();"
```

#### **Redis Connection Issues**
```bash
# Check Redis status
redis-cli ping
# Should return: PONG

# Check Redis configuration
redis-cli config get bind
redis-cli config get port
```

---

## 📚 **Next Steps**

1. **Explore the Codebase**: Read [Architecture Overview](../architecture/overview.md)
2. **Understand ArxObjects**: Review [ArxObject System](../architecture/arxobjects.md)
3. **Learn Development**: Follow [Development Guide](guide.md)
4. **API Reference**: Check [API Documentation](../api/README.md)

---

## 🆘 **Need Help?**

- **Development issues**: Check [Development Guide](guide.md)
- **Architecture questions**: Review [Architecture Overview](../architecture/overview.md)
- **API problems**: See [API Reference](../api/README.md)
- **Setup issues**: Verify prerequisites and configuration

**Happy coding! 🚀**
