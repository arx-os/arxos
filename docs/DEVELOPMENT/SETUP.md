# Development Environment Setup

## 🎯 **Overview**

This guide provides complete instructions for setting up the Arxos development environment. Follow these steps to get your development environment ready for Arxos development.

## 📋 **Prerequisites**

### **Required Software**
- **Node.js**: 18.0.0 or higher
- **Go**: 1.21.0 or higher
- **Python**: 3.11.0 or higher
- **Docker**: 20.10.0 or higher
- **Git**: 2.30.0 or higher
- **PostgreSQL**: 17.0 or higher (or use Docker)
- **PostGIS**: 3.5.3 or higher
- **Redis**: 7.0 or higher (or use Docker)

### **System Requirements**
- **Operating System**: Windows 10/11, macOS 12+, or Ubuntu 20.04+
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space minimum
- **Network**: Internet connection for package downloads

## 🚀 **Quick Setup**

### **1. Clone the Repository**
```bash
git clone https://github.com/arxos/arxos.git
cd arxos
```

### **2. Start Development Environment**
```bash
# Start all services with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
```

### **3. Install Dependencies**
```bash
# Install Node.js dependencies
cd frontend && npm install
cd ../arxide/desktop && npm install

# Install Go dependencies
cd ../../core/backend && go mod download

# Install Python dependencies
cd ../../services && pip install -r requirements.txt
```

### **4. Verify Setup**
```bash
# Run tests to verify everything is working
npm test
go test ./...
python -m pytest
```

## 🔧 **Detailed Setup Instructions**

### **Frontend Development Setup**

#### **ArxIDE Desktop Application**
```bash
cd arxide/desktop

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

#### **Web Application**
```bash
cd frontend/web

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### **Backend Development Setup**

#### **Go Services**
```bash
cd core/backend

# Install dependencies
go mod download

# Run the application
go run main.go

# Run tests
go test ./...

# Build for production
go build -o arxos-backend
```

#### **Python Services**
```bash
cd services

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Run tests
python -m pytest
```

### **Database Setup**

#### **Using Docker (Recommended)**
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run database migrations
cd infrastructure/database
alembic upgrade head

# Verify database connection
python -c "from database.connection import get_db; print('Database connected successfully')"
```

#### **Local Installation**
```bash
# Install PostgreSQL
# On Ubuntu:
sudo apt-get install postgresql postgresql-contrib

# On macOS:
brew install postgresql

# On Windows:
# Download from https://www.postgresql.org/download/windows/

# Install Redis
# On Ubuntu:
sudo apt-get install redis-server

# On macOS:
brew install redis

# On Windows:
# Download from https://redis.io/download
```

### **Development Tools Setup**

#### **Code Quality Tools**
```bash
# Install ESLint for JavaScript/TypeScript
npm install -g eslint

# Install Prettier for code formatting
npm install -g prettier

# Install Black for Python formatting
pip install black

# Install Go formatting tools
go install golang.org/x/tools/cmd/goimports@latest
```

#### **IDE Configuration**
```bash
# VS Code extensions
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension ms-python.python
code --install-extension golang.go
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-eslint
```

## 🧪 **Testing Setup**

### **Unit Tests**
```bash
# JavaScript/TypeScript tests
npm test

# Go tests
go test ./...

# Python tests
python -m pytest
```

### **Integration Tests**
```bash
# Run all integration tests
npm run test:integration

# Run specific service tests
cd services && python -m pytest tests/integration/
```

### **End-to-End Tests**
```bash
# Install Playwright
npm install -g playwright

# Install browser dependencies
npx playwright install

# Run E2E tests
npm run test:e2e
```

## 🔍 **Verification Steps**

### **1. Service Health Checks**
```bash
# Check all services are running
curl http://localhost:8000/health
curl http://localhost:8080/health
curl http://localhost:5432/health
```

### **2. Database Connection**
```bash
# Test database connection
python -c "
from database.connection import get_db
db = get_db()
print('Database connection successful')
"
```

### **3. API Endpoints**
```bash
# Test API endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:8080/api/v1/health
```

### **4. Development Tools**
```bash
# Test code formatting
npm run format
black --check .
go fmt ./...

# Test linting
npm run lint
flake8 .
golangci-lint run
```

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Port Conflicts**
```bash
# Check what's using a port
lsof -i :8000
lsof -i :8080
lsof -i :5432

# Kill process using port
kill -9 <PID>
```

#### **Docker Issues**
```bash
# Restart Docker services
docker-compose down
docker-compose up -d

# Clean up Docker
docker system prune -a
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check Redis status
sudo systemctl status redis

# Restart Redis
sudo systemctl restart redis
```

#### **Node.js Issues**
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### **Python Issues**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Performance Issues**

#### **Memory Usage**
```bash
# Monitor memory usage
htop
free -h

# Increase Docker memory limit
# In Docker Desktop settings
```

#### **Disk Space**
```bash
# Check disk usage
df -h

# Clean up Docker images
docker system prune -a
```

## 📊 **Environment Configuration**

### **Environment Variables**
```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

### **Configuration Files**
```bash
# Database configuration
cp config/database.example.yml config/database.yml

# API configuration
cp config/api.example.yml config/api.yml

# Development configuration
cp config/dev.example.yml config/dev.yml
```

## 🔒 **Security Setup**

### **SSL Certificates**
```bash
# Generate development SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### **API Keys**
```bash
# Generate API keys for development
python scripts/generate_api_keys.py
```

### **Database Security**
```bash
# Set up database users and permissions
psql -U postgres -c "CREATE USER arxos_dev WITH PASSWORD 'dev_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE arxos_dev TO arxos_dev;"
```

## 📚 **Additional Resources**

### **Documentation**
- [Architecture Overview](../ARCHITECTURE/OVERVIEW.md)
- [API Reference](../API/)
- [Component Documentation](../COMPONENTS/)

### **Development Guides**
- [Development Workflow](WORKFLOW.md)
- [Testing Strategy](TESTING.md)
- [Code Quality](CODE_QUALITY.md)

### **Troubleshooting**
- [Common Issues](TROUBLESHOOTING.md)
- [Performance Tuning](PERFORMANCE.md)
- [Security Hardening](SECURITY.md)

---

## 📊 **Setup Status Checklist**

### **✅ Core Setup**
- [ ] Repository cloned
- [ ] Dependencies installed
- [ ] Database running
- [ ] Services starting
- [ ] Tests passing

### **✅ Development Tools**
- [ ] IDE configured
- [ ] Code formatting working
- [ ] Linting configured
- [ ] Git hooks installed

### **✅ Verification**
- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Database connected
- [ ] Development environment ready

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Status**: Active Development