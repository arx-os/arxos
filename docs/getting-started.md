# 🚀 Getting Started with Arxos

## 🎯 **Quick Start Guide**

This guide will get you up and running with Arxos in **under 10 minutes**. Arxos is a production-ready, enterprise-grade building intelligence platform that transforms buildings into programmable, navigable systems.

## 📋 **Prerequisites**

### **System Requirements**
- **Operating System**: Linux, macOS, or Windows (WSL2 recommended for Windows)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space
- **Network**: Internet connection for initial setup

### **Required Software**
- **Go**: Version 1.21 or later
- **Python**: Version 3.9 or later
- **PostgreSQL**: Version 13 or later
- **Git**: Version 2.30 or later

## 🚀 **Step 1: Installation**

### **1. Clone the Repository**
```bash
git clone https://github.com/arxos/arxos.git
cd arxos
```

### **2. Install Dependencies**
```bash
# Install Go dependencies
go mod download

# Install Python dependencies
cd ai_services
pip install -r requirements.txt
cd ..

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib postgis
sudo apt-get install -y libgdal-dev libproj-dev libgeos-dev
```

### **3. Build the Core Engine**
```bash
# Build C core components
cd core/c
make clean && make all
cd ../..

# Build Go components
go build ./cmd/arxos
```

## 🗄️ **Step 2: Database Setup**

### **1. Create Database**
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE arxos;
CREATE USER arxos_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE arxos TO arxos_user;
\q
```

### **2. Run Migrations**
```bash
# Run database migrations
go run cmd/arxos/main.go migrate
```

## ⚙️ **Step 3: Configuration**

### **1. Create Config File**
```bash
# Create configuration directory
mkdir -p config/backend

# Create main config file
cat > config/backend/config.yaml << EOF
database:
  host: localhost
  port: 5432
  name: arxos
  user: arxos_user
  password: your_secure_password
  sslmode: disable

server:
  host: 0.0.0.0
  port: 8080
  debug: true

ai_services:
  grpc_host: localhost
  grpc_port: 50051
  enable_gpu: false

security:
  jwt_secret: your_jwt_secret_here
  enable_2fa: false
  session_timeout: 3600
EOF
```

### **2. Set Environment Variables**
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export ARXOS_CONFIG_PATH="$PWD/config/backend"
export ARXOS_DB_URL="postgres://arxos_user:your_secure_password@localhost:5432/arxos"
export ARXOS_AI_SERVICE_URL="localhost:50051"
```

## 🏗️ **Step 4: Start Services**

### **1. Start AI Services**
```bash
# Start Python AI services
cd ai_services
python grpc_server.py &
cd ..
```

### **2. Start Main Service**
```bash
# Start Arxos main service
go run cmd/arxos/main.go serve
```

### **3. Verify Services**
```bash
# Check main service
curl http://localhost:8080/health

# Check AI service
curl http://localhost:50051/health
```

## 🎯 **Step 5: Your First Building**

### **1. Initialize a Building**
```bash
# Create a new building
./arxos init --name "My First Building" --type office --floors 3

# Navigate to the building
./arxos cd "My First Building"

# List building contents
./arxos ls
```

### **2. Upload a Floor Plan**
```bash
# Upload a PDF floor plan
./arxos ingest --file path/to/floor_plan.pdf --type pdf

# Check processing status
./arxos status

# View extracted objects
./arxos ls --type arxobject
```

### **3. Explore the Building**
```bash
# Navigate to first floor
./arxos cd floor_1

# List rooms
./arxos ls --type room

# View building tree
./arxos tree

# Find specific elements
./arxos find --type wall
```

## 🌐 **Step 6: Web Interface**

### **1. Open Web Interface**
Open your browser and navigate to:
```
http://localhost:8080
```

### **2. Login**
- **Username**: `admin`
- **Password**: `admin` (change this in production!)

### **3. Explore Features**
- **3D Visualization**: View your building in 3D
- **ASCII Rendering**: See terminal-based visualization
- **Real-time Updates**: Monitor live building data
- **Asset Management**: Manage building components

## 🧪 **Step 7: Test the System**

### **1. Test CLI Commands**
```bash
# Test navigation
./arxos pwd
./arxos ls
./arxos tree

# Test search
./arxos find --query "wall thickness > 200mm"
./arxos find --type electrical --confidence > 0.8

# Test real-time monitoring
./arxos watch --type arxobject
```

### **2. Test Real-time Features**
```bash
# Start monitoring in another terminal
./arxos watch --dashboard

# Make changes in the web interface
# Watch real-time updates in the terminal
```

### **3. Test AI Services**
```bash
# Test PDF processing
./arxos ai detect --file test_floor_plan.pdf

# Test LiDAR processing
./arxos ai scan --room "conference_room"
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Database Connection Failed**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l

# Verify connection
psql -h localhost -U arxos_user -d arxos
```

#### **2. CGO Build Failed**
```bash
# Install build tools
sudo apt-get install -y build-essential

# Check Go version
go version

# Verify CGO is enabled
go env CGO_ENABLED
```

#### **3. AI Services Not Starting**
```bash
# Check Python dependencies
pip list | grep -E "(opencv|torch|tensorflow)"

# Check gRPC service
netstat -tlnp | grep 50051

# Check logs
tail -f ai_services/grpc_server.log
```

### **Getting Help**

#### **1. Check Logs**
```bash
# Main service logs
tail -f logs/arxos.log

# AI service logs
tail -f ai_services/grpc_server.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### **2. Verify Configuration**
```bash
# Check config loading
./arxos config --validate

# Check environment variables
env | grep ARXOS
```

#### **3. Community Support**
- **GitHub Issues**: [Report bugs and request features](https://github.com/arxos/arxos/issues)
- **Documentation**: [Complete documentation](https://docs.arxos.com)
- **Discord**: [Community chat](https://discord.gg/arxos)

## 🎯 **Next Steps**

### **1. Learn the CLI**
- [Complete Command Reference](cli/commands.md)
- [File Tree Structure](cli/file-tree.md)
- [Interactive Navigation](cli/interactive-navigation.md)

### **2. Understand the Architecture**
- [System Architecture](current-architecture.md)
- [ArxObject Model](architecture/arxobjects.md)
- [ASCII Rendering](architecture/ascii-bim.md)

### **3. Explore Workflows**
- [Field Validation](workflows/field-validation.md)
- [Building IaC](workflows/building-iac.md)
- [PDF to 3D](workflows/pdf-to-3d.md)

### **4. Advanced Features**
- [Real-time Monitoring](development/realtime.md)
- [AI Services](development/ai-services.md)
- [Security & Compliance](security/compliance.md)

## 🏆 **Congratulations!**

You've successfully set up Arxos and created your first building! You now have:

✅ **A complete building intelligence platform**  
✅ **Real-time monitoring and updates**  
✅ **AI-powered data processing**  
✅ **Enterprise-grade security**  
✅ **Professional CLI tools**  
✅ **3D and ASCII visualization**  

**Welcome to the future of building management!** 🏗️✨

---

**Need help?** Check the [troubleshooting section](#-troubleshooting) or [community support](#3-community-support) above.
