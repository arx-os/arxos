# Arxos Monorepo Makefile
# Provides unified build, test, and deployment commands for the entire platform

.PHONY: help dev build test clean install deps docker-up docker-down lint format

# Default target
help:
	@echo "🚀 Arxos Development Commands"
	@echo ""
	@echo "📋 Available commands:"
	@echo "  make dev          # Start all services in development mode"
	@echo "  make build        # Build all services"
	@echo "  make test         # Run all tests"
	@echo "  make clean        # Clean build artifacts"
	@echo "  make install      # Install all dependencies"
	@echo "  make deps         # Install development dependencies"
	@echo "  make docker-up    # Start Docker services"
	@echo "  make docker-down  # Stop Docker services"
	@echo "  make lint         # Run linting on all code"
	@echo "  make format       # Format all code"
	@echo "  make help         # Show this help message"

# Development environment
dev: docker-up
	@echo "🚀 Starting Arxos development environment..."
	@echo "📊 Services starting on:"
	@echo "  - Browser CAD:      http://localhost:3000"
	@echo "  - ArxIDE:           http://localhost:3001"
	@echo "  - Backend API:      http://localhost:8080"
	@echo "  - GUS Agent:        http://localhost:8000"
	@echo "  - PostgreSQL:       localhost:5432"
	@echo "  - Redis:            localhost:6379"
	@echo ""
	@echo "⏳ Starting services in parallel..."
	@make -j4 dev-backend dev-gus dev-cad dev-arxide

# Start individual services
dev-backend:
	@echo "🔧 Starting Go Backend..."
	cd arx-backend && go run main.go

dev-gus:
	@echo "🤖 Starting GUS Agent..."
	cd services/gus && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-cad:
	@echo "🎨 Starting Browser CAD..."
	cd frontend/web && npm run dev

dev-arxide:
	@echo "🖥️  Starting ArxIDE..."
	cd arxide && npm run dev

# Build all services
build: build-backend build-gus build-cad build-arxide
	@echo "✅ All services built successfully!"

build-backend:
	@echo "🔧 Building Go Backend..."
	cd arx-backend && go build -o bin/arx-backend .

build-gus:
	@echo "🤖 Building GUS Agent..."
	cd services/gus && python setup.py build

build-cad:
	@echo "🎨 Building Browser CAD..."
	cd frontend/web && npm run build

build-arxide:
	@echo "🖥️  Building ArxIDE..."
	cd arxide && npm run build

# Testing
test: test-backend test-gus test-cad test-arxide
	@echo "✅ All tests passed!"

test-backend:
	@echo "🧪 Testing Go Backend..."
	cd arx-backend && go test ./...

test-gus:
	@echo "🧪 Testing GUS Agent..."
	cd services/gus && python -m pytest

test-cad:
	@echo "🧪 Testing Browser CAD..."
	cd frontend/web && npm test

test-arxide:
	@echo "🧪 Testing ArxIDE..."
	cd arxide && npm test

# Code quality
lint: lint-backend lint-gus lint-cad lint-arxide
	@echo "✅ All linting passed!"

lint-backend:
	@echo "🔍 Linting Go Backend..."
	cd arx-backend && golangci-lint run

lint-gus:
	@echo "🔍 Linting GUS Agent..."
	cd services/gus && flake8 . && mypy .

lint-cad:
	@echo "🔍 Linting Browser CAD..."
	cd frontend/web && npm run lint

lint-arxide:
	@echo "🔍 Linting ArxIDE..."
	cd arxide && npm run lint

# Code formatting
format: format-backend format-gus format-cad format-arxide
	@echo "✅ All code formatted!"

format-backend:
	@echo "🎨 Formatting Go Backend..."
	cd arx-backend && goimports -w .

format-gus:
	@echo "🎨 Formatting GUS Agent..."
	cd services/gus && black . && isort .

format-cad:
	@echo "🎨 Formatting Browser CAD..."
	cd frontend/web && npm run format

format-arxide:
	@echo "🎨 Formatting ArxIDE..."
	cd arxide && npm run format

# Dependencies
install: install-backend install-gus install-cad install-arxide install-svgx
	@echo "✅ All dependencies installed!"

install-backend:
	@echo "📦 Installing Go Backend dependencies..."
	cd arx-backend && go mod download

install-gus:
	@echo "📦 Installing GUS Agent dependencies..."
	cd services/gus && pip install -r requirements.txt

install-cad:
	@echo "📦 Installing Browser CAD dependencies..."
	cd frontend/web && npm install

install-arxide:
	@echo "📦 Installing ArxIDE dependencies..."
	cd arxide && npm install

install-svgx:
	@echo "📦 Installing SVGX Engine dependencies..."
	cd svgx_engine && pip install -e .


# Development dependencies
deps: deps-backend deps-gus deps-cad deps-arxide
	@echo "✅ All development dependencies installed!"

deps-backend:
	@echo "📦 Installing Go development tools..."
	go install golang.org/x/tools/cmd/goimports@latest
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

deps-gus:
	@echo "📦 Installing Python development tools..."
	pip install black flake8 mypy pytest pre-commit

deps-cad:
	@echo "📦 Installing Node.js development tools..."
	npm install -g eslint prettier typescript

deps-arxide:
	@echo "📦 Installing Rust development tools..."
	rustup component add rustfmt clippy

# Docker commands
docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose -f dev/docker-compose.yml up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose -f dev/docker-compose.yml down

# Cleanup
clean: clean-backend clean-gus clean-cad clean-arxide
	@echo "🧹 Cleaned all build artifacts!"

clean-backend:
	@echo "🧹 Cleaning Go Backend..."
	cd arx-backend && rm -rf bin/ && go clean

clean-gus:
	@echo "🧹 Cleaning GUS Agent..."
	cd services/gus && rm -rf build/ dist/ *.egg-info/

clean-cad:
	@echo "🧹 Cleaning Browser CAD..."
	cd frontend/web && rm -rf dist/ node_modules/

clean-arxide:
	@echo "🧹 Cleaning ArxIDE..."
	cd arxide && rm -rf dist/ node_modules/

# Database
db-migrate:
	@echo "🗄️  Running database migrations..."
	cd arx-backend && go run cmd/migrate/main.go

db-seed:
	@echo "🌱 Seeding database..."
	cd arx-backend && go run cmd/seed/main.go

# Health checks
health:
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8080/health || echo "❌ Backend not responding"
	@curl -f http://localhost:8000/health || echo "❌ GUS not responding"
	@curl -f http://localhost:3000/health || echo "❌ CAD not responding"
	@curl -f http://localhost:3001/health || echo "❌ ArxIDE not responding" 