#!/bin/bash
set -e

echo "🚀 Setting up Arxos Development Environment..."

# Update package lists
sudo apt-get update

# Install additional system dependencies
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
    yq

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Go tools
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install github.com/go-delve/delve/cmd/dlv@latest

# Install Python tools
pip install --upgrade pip
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
    pydantic

# Install Node.js tools
npm install -g \
    @types/node \
    typescript \
    ts-node \
    nodemon \
    eslint \
    prettier \
    tailwindcss \
    @tailwindcss/forms \
    @tailwindcss/typography

# Install Rust tools
rustup component add rustfmt clippy
cargo install cargo-watch

# Create development directories
mkdir -p /workspaces/data/postgres
mkdir -p /workspaces/data/redis
mkdir -p /workspaces/data/logs

# Set up Git configuration
git config --global user.name "Arxos Developer"
git config --global user.email "developer@arxos.dev"

# Create environment files
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

# Set up pre-commit hooks
pre-commit install

echo "✅ Arxos Development Environment setup complete!"
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