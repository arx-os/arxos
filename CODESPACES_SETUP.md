# GitHub Codespaces Setup Guide

## 🚀 Quick Start

### Step 1: Create Codespace
1. Go to your GitHub repository: `https://github.com/[your-username]/arxos`
2. Click the green **"Code"** button
3. Select the **"Codespaces"** tab
4. Click **"Create codespace on main"**
5. Wait for the environment to build (2-3 minutes)

### Step 2: Start Development
Once the codespace opens:

```bash
# Install all dependencies
make install

# Start all services
make dev
```

## 🔧 What's Included

The codespace comes with:

- ✅ **Go 1.24** - Backend development
- ✅ **Python 3.11** - GUS Agent and SVGX Engine
- ✅ **Node.js 20** - Frontend development
- ✅ **Rust 1.75** - Tauri desktop app
- ✅ **Docker & Docker Compose** - Containerized services
- ✅ **PostgreSQL** - Database
- ✅ **Redis** - Caching
- ✅ **VS Code Extensions** - Development tools

## 🌐 Accessing Services

Once running, services are available at:

- **Browser CAD**: http://localhost:3000
- **ArxIDE**: http://localhost:3001
- **Backend API**: http://localhost:8080
- **GUS Agent**: http://localhost:8000

## 📋 Common Commands

```bash
# Development
make dev          # Start all services
make build        # Build all services
make test         # Run all tests

# Individual services
make dev-backend  # Start Go backend only
make dev-gus      # Start GUS agent only
make dev-cad      # Start Browser CAD only
make dev-arxide   # Start ArxIDE only

# Code quality
make lint         # Run linting
make format       # Format code

# Database
make db-migrate   # Run migrations
make db-seed      # Seed database

# Health check
make health       # Check all services
```

## 🛠️ Development Workflow

### 1. Backend Development (Go)
```bash
cd arx-backend
go run main.go
```

### 2. GUS Agent Development (Python)
```bash
cd services/gus
python -m uvicorn main:app --reload
```

### 3. Browser CAD Development (Node.js)
```bash
cd frontend/web
npm run dev
```

### 4. ArxIDE Development (Rust/Tauri)
```bash
cd arxide
npm run dev
```

## 🔍 Troubleshooting

### Port Forwarding
If services aren't accessible:
1. Check the "Ports" tab in VS Code
2. Ensure ports are forwarded automatically
3. Click "Open in Browser" for each service

### Database Issues
```bash
# Reset database
make docker-down
make docker-up
make db-migrate
make db-seed
```

### Service Health
```bash
# Check all services
make health

# Check individual services
curl http://localhost:8080/health  # Backend
curl http://localhost:8000/health  # GUS
curl http://localhost:3000/health  # CAD
curl http://localhost:3001/health  # ArxIDE
```

## 📁 File Structure

```
arxos/
├── .devcontainer/          # Codespace configuration
├── arx-backend/           # Go backend (Chi framework)
├── services/gus/          # Python GUS agent
├── frontend/web/          # Browser CAD (HTMX + Canvas)
├── arxide/               # ArxIDE desktop (Tauri)
├── dev/                  # Docker development setup
├── docs/                 # Documentation
└── Makefile              # Development commands
```

## 🎯 Next Steps

1. **Start with Backend**: Focus on Go API development
2. **Add GUS Agent**: Implement AI assistance features
3. **Build Browser CAD**: Create web-based CAD interface
4. **Develop ArxIDE**: Build desktop CAD application

## 💡 Tips

- Use `Ctrl+Shift+P` to access VS Code commands
- Use the integrated terminal for development
- Check the "Problems" tab for linting issues
- Use the "Extensions" tab to manage VS Code extensions
- Use the "Ports" tab to manage port forwarding

## 🆘 Support

If you encounter issues:

1. Check the terminal output for error messages
2. Run `make health` to check service status
3. Restart the codespace if needed
4. Check the [GitHub Issues](https://github.com/[your-username]/arxos/issues) for known problems

---

**Ready to start developing!** 🚀 