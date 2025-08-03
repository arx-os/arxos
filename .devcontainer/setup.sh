#!/bin/bash
set -e

# Function to log messages with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors
handle_error() {
    log "❌ Error occurred in setup script at line $1"
    log "Command that failed: $2"
    exit 1
}

# Set up error handling
trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

log "🚀 Setting up Arxos Development Environment..."

# Check if we're running as the correct user
if [ "$(whoami)" != "vscode" ]; then
    log "⚠️  Warning: Not running as vscode user, some operations may fail"
fi

# Update package lists with retry logic
log "📦 Updating package lists..."
for i in {1..3}; do
    if sudo apt-get update; then
        break
    else
        log "⚠️  Package update attempt $i failed, retrying..."
        sleep 2
    fi
done

# Install additional system dependencies
log "🔧 Installing system dependencies..."
sudo apt-get install -y \
    postgresql-client \
    postgresql-server-dev-all \
    libpq-dev \
    build-essential \
    curl \
    wget \
    unzip \
    git \
    vim \
    nano \
    tree \
    htop \
    jq \
    yq || {
    log "❌ Failed to install system dependencies"
    exit 1
}

# Install Docker Compose with error handling
log "🐳 Installing Docker Compose..."
if ! sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose; then
    log "❌ Failed to download Docker Compose"
    exit 1
fi
sudo chmod +x /usr/local/bin/docker-compose

# Install Go tools with error handling
log "🐹 Installing Go tools..."
if command -v go &> /dev/null; then
    go install golang.org/x/tools/cmd/goimports@latest || log "⚠️  Failed to install goimports"
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest || log "⚠️  Failed to install golangci-lint"
    go install github.com/go-delve/delve/cmd/dlv@latest || log "⚠️  Failed to install delve"
else
    log "⚠️  Go not found, skipping Go tool installation"
fi

# Install Python tools with error handling
log "🐍 Installing Python tools..."
if command -v pip &> /dev/null; then
    pip install --upgrade pip setuptools wheel || log "⚠️  Failed to upgrade pip"
    pip install \
        black \
        flake8 \
        mypy \
        pytest \
        pytest-asyncio \
        pre-commit \
        structlog \
        fastapi \
        uvicorn[standard] \
        sqlalchemy \
        psycopg2-binary \
        redis \
        httpx \
        click \
        pydantic || log "⚠️  Some Python packages failed to install"
else
    log "⚠️  pip not found, skipping Python tool installation"
fi

# Install Node.js tools with error handling
log "📦 Installing Node.js tools..."
if command -v npm &> /dev/null; then
    npm install -g \
        @types/node \
        typescript \
        ts-node \
        nodemon \
        eslint \
        prettier \
        tailwindcss \
        @tailwindcss/forms \
        @tailwindcss/typography || log "⚠️  Some Node.js packages failed to install"
else
    log "⚠️  npm not found, skipping Node.js tool installation"
fi

# Install Rust tools with error handling
log "🦀 Installing Rust tools..."
if command -v rustup &> /dev/null; then
    rustup component add rustfmt clippy || log "⚠️  Failed to install Rust components"
    cargo install cargo-watch || log "⚠️  Failed to install cargo-watch"
else
    log "⚠️  rustup not found, skipping Rust tool installation"
fi

# Create development directories
log "📁 Creating development directories..."
mkdir -p /workspaces/data/postgres
mkdir -p /workspaces/data/redis
mkdir -p /workspaces/data/logs

# Set up Git configuration
log "🔧 Configuring Git..."
git config --global user.name "Arxos Developer" || log "⚠️  Failed to set Git user name"
git config --global user.email "developer@arxos.dev" || log "⚠️  Failed to set Git user email"

# Create environment files
log "📝 Creating environment files..."
cat > /workspaces/.env << EOF
# Development Environment
NODE_ENV=development
GO_ENV=development
PYTHONPATH=/workspaces/arxos

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=arxos_dev
POSTGRES_USER=arxos_user
POSTGRES_PASSWORD=arxos_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Services
BACKEND_PORT=8080
GUS_PORT=8000
CAD_PORT=3000
ARXIDE_PORT=3001
EOF

# Set up pre-commit hooks (only if pre-commit is available)
log "🔧 Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install || log "⚠️  Failed to install pre-commit hooks"
else
    log "⚠️  pre-commit not found, skipping hook installation"
fi

# Verify Docker is working
log "🐳 Verifying Docker installation..."
if command -v docker &> /dev/null; then
    if docker --version; then
        log "✅ Docker is working"
    else
        log "⚠️  Docker command failed"
    fi
else
    log "⚠️  Docker not found"
fi

log "✅ Arxos Development Environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  - make dev          # Start all services"
echo "  - make test         # Run all tests"
echo "  - make build        # Build all services"
echo "  - make clean        # Clean build artifacts"
echo ""
echo "🌐 Services will be available at:"
echo "  - Browser CAD:      http://localhost:3000"
echo "  - ArxIDE:           http://localhost:3001"
echo "  - Backend API:      http://localhost:8080"
echo "  - GUS Agent:        http://localhost:8000"
echo "  - PostgreSQL:       localhost:5432"
echo "  - Redis:            localhost:6379" 