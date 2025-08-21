# Quick Start Guide

## 🚀 **Get ARXOS Running in 5 Minutes**

This guide will get you up and running with ARXOS quickly, regardless of your role.

---

## 🎯 **I'm a Developer - I Want to Run ARXOS Locally**

### **Prerequisites**
- **Go 1.21+** installed
- **Python 3.9+** installed  
- **PostgreSQL 13+** with PostGIS extension
- **Redis 6+** server running

### **Step 1: Clone & Setup (2 minutes)**
```bash
git clone https://github.com/your-org/arxos.git
cd arxos

# Install Go dependencies
cd core/backend
go mod download

# Install Python dependencies  
cd ../../ai_service
pip install -r requirements.txt
```

### **Step 2: Database Setup (1 minute)**
```bash
# Create database
createdb arxos_dev

# Run migrations
cd core/backend
go run main.go migrate
```

### **Step 3: Start Services (2 minutes)**
```bash
# Terminal 1: Start Go backend
cd core/backend
go run main.go

# Terminal 2: Start Python AI service
cd ai_service
python main.py
```

**🎉 ARXOS is now running!**
- Backend: http://localhost:8080
- AI Service: http://localhost:5000
- API Health: http://localhost:8080/api/health

---

## 🎯 **I'm a User - I Want to Try ARXOS Features**

### **Access the System**
1. Open your browser to `http://localhost:8080`
2. Upload a PDF floor plan to test ingestion
3. View the extracted building data
4. Explore 3D visualization features

### **Test PDF Ingestion**
1. Navigate to the upload interface
2. Select a PDF building plan
3. Watch the AI service process it
4. View extracted ArxObjects in the BIM viewer

---

## 🎯 **I'm a System Admin - I Want to Deploy ARXOS**

### **Production Deployment**
```bash
# Build Go binary
cd core/backend
go build -o arxos-server

# Run with environment variables
export DB_URL="postgres://user:pass@localhost/arxos"
export REDIS_URL="redis://localhost:6379"
export AI_SERVICE_URL="http://localhost:5000"

./arxos-server
```

### **Environment Variables**
```bash
# Required
DB_URL=postgres://user:pass@localhost/arxos
REDIS_URL=redis://localhost:6379
AI_SERVICE_URL=http://localhost:5000

# Optional
PORT=8080
LOG_LEVEL=info
CORS_ORIGINS=http://localhost:3000
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

**Database Connection Failed**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify database exists
psql -l | grep arxos
```

**Redis Connection Failed**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

**AI Service Not Responding**
```bash
# Check Python service
curl http://localhost:5000/health
# Should return: {"status": "healthy"}
```

### **Get Help**
- **Development issues**: Check [Development Guide](development/guide.md)
- **Architecture questions**: Review [Architecture Overview](architecture/overview.md)
- **API problems**: See [API Reference](api/README.md)

---

## 🎯 **What's Next?**

1. **Explore the system**: Upload a PDF and see ArxObjects in action
2. **Understand the code**: Read [Architecture Overview](architecture/overview.md)
3. **Start developing**: Follow [Development Guide](development/guide.md)
4. **Build features**: Check [API Reference](api/README.md)

**Welcome to ARXOS! 🏗️✨**
