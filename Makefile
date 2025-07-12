# Arxos Monorepo Makefile
# Provides unified build, test, and deployment commands for the entire platform

.PHONY: help build test deploy clean install setup

# Default target
help:
	@echo "Arxos Monorepo - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup          - Initial setup of the entire monorepo"
	@echo "  install        - Install all dependencies"
	@echo "  clean          - Clean all build artifacts"
	@echo ""
	@echo "Development:"
	@echo "  build          - Build all components"
	@echo "  build-core     - Build core services only"
	@echo "  build-frontend - Build frontend applications only"
	@echo "  build-services - Build specialized services only"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-core      - Test core services"
	@echo "  test-frontend  - Test frontend applications"
	@echo "  test-services  - Test specialized services"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy         - Deploy all services"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  deploy-prod    - Deploy to production environment"
	@echo ""
	@echo "Development Tools:"
	@echo "  lint           - Run linting on all code"
	@echo "  format         - Format all code"
	@echo "  docs           - Generate documentation"

# Setup and Installation
setup: install
	@echo "Setting up Arxos monorepo..."
	@mkdir -p logs
	@mkdir -p data
	@echo "✅ Setup complete"

install:
	@echo "Installing dependencies..."
	# Core dependencies
	cd core/svg-parser && pip install -r requirements.txt
	cd core/backend && go mod download
	# Frontend dependencies
	cd frontend/web && npm install
	cd frontend/ios && pod install
	# Service dependencies
	cd services/ai && pip install -r requirements.txt
	cd services/iot && pip install -r requirements.txt
	cd services/cmms && pip install -r requirements.txt
	@echo "✅ Dependencies installed"

clean:
	@echo "Cleaning build artifacts..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@find . -name "node_modules" -type d -exec rm -rf {} +
	@find . -name "dist" -type d -exec rm -rf {} +
	@find . -name "build" -type d -exec rm -rf {} +
	@echo "✅ Clean complete"

# Building
build: build-core build-frontend build-services
	@echo "✅ All components built"

build-core:
	@echo "Building core services..."
	cd core/svg-parser && python setup.py build
	cd core/backend && go build -o bin/arx-backend ./cmd/main.go
	@echo "✅ Core services built"

build-frontend:
	@echo "Building frontend applications..."
	cd frontend/web && npm run build
	cd frontend/ios && xcodebuild -workspace Arxos.xcworkspace -scheme Arxos -configuration Release
	cd frontend/android && ./gradlew assembleRelease
	@echo "✅ Frontend applications built"

build-services:
	@echo "Building specialized services..."
	cd services/ai && python setup.py build
	cd services/iot && python setup.py build
	cd services/cmms && python setup.py build
	@echo "✅ Specialized services built"

# Testing
test: test-core test-frontend test-services
	@echo "✅ All tests passed"

test-core:
	@echo "Testing core services..."
	cd core/svg-parser && python -m pytest tests/ -v
	cd core/backend && go test ./...
	@echo "✅ Core tests passed"

test-frontend:
	@echo "Testing frontend applications..."
	cd frontend/web && npm test
	cd frontend/ios && xcodebuild test -workspace Arxos.xcworkspace -scheme Arxos
	cd frontend/android && ./gradlew test
	@echo "✅ Frontend tests passed"

test-services:
	@echo "Testing specialized services..."
	cd services/ai && python -m pytest tests/ -v
	cd services/iot && python -m pytest tests/ -v
	cd services/cmms && python -m pytest tests/ -v
	@echo "✅ Service tests passed"

# Deployment
deploy: deploy-staging
	@echo "✅ Deployment complete"

deploy-staging:
	@echo "Deploying to staging environment..."
	docker-compose -f infrastructure/deploy/docker-compose.staging.yml up -d
	@echo "✅ Staging deployment complete"

deploy-prod:
	@echo "Deploying to production environment..."
	docker-compose -f infrastructure/deploy/docker-compose.prod.yml up -d
	@echo "✅ Production deployment complete"

# Development Tools
lint:
	@echo "Running linting..."
	cd core/svg-parser && flake8 .
	cd core/backend && golangci-lint run
	cd frontend/web && npm run lint
	@echo "✅ Linting complete"

format:
	@echo "Formatting code..."
	cd core/svg-parser && black .
	cd core/backend && go fmt ./...
	cd frontend/web && npm run format
	@echo "✅ Formatting complete"

docs:
	@echo "Generating documentation..."
	cd tools/docs && python generate_docs.py
	@echo "✅ Documentation generated"

# Development shortcuts
dev: install
	@echo "Starting development environment..."
	docker-compose -f infrastructure/deploy/docker-compose.dev.yml up -d
	@echo "✅ Development environment started"

dev-stop:
	@echo "Stopping development environment..."
	docker-compose -f infrastructure/deploy/docker-compose.dev.yml down
	@echo "✅ Development environment stopped"

# Database operations
db-migrate:
	@echo "Running database migrations..."
	cd infrastructure/database && alembic upgrade head
	@echo "✅ Database migrations complete"

db-reset:
	@echo "Resetting database..."
	cd infrastructure/database && alembic downgrade base
	cd infrastructure/database && alembic upgrade head
	@echo "✅ Database reset complete"

# Monitoring and logs
logs:
	@echo "Showing application logs..."
	docker-compose -f infrastructure/deploy/docker-compose.dev.yml logs -f

monitor:
	@echo "Starting monitoring dashboard..."
	cd infrastructure/monitoring && python start_monitoring.py 