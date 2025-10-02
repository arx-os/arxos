# ArxOS Makefile
# Provides commands for building, testing, and running the ArxOS platform with IfcOpenShell integration

.PHONY: help build build-all test test-all docker docker-all run run-dev clean lint format

# Default target
help:
	@echo "ArxOS Development Commands:"
	@echo ""
	@echo "Building:"
	@echo "  build          Build ArxOS main application"
	@echo "  build-all      Build all components (ArxOS + IfcOpenShell service)"
	@echo "  docker         Build Docker images for all services"
	@echo "  docker-dev     Build Docker images for development"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run ArxOS Go tests"
	@echo "  test-ifc       Run IfcOpenShell service tests"
	@echo "  test-all       Run all tests"
	@echo "  test-integration Run integration tests"
	@echo ""
	@echo "Running:"
	@echo "  run            Run ArxOS with Docker Compose"
	@echo "  run-dev        Run ArxOS in development mode"
	@echo "  run-ifc        Run only IfcOpenShell service"
	@echo "  stop           Stop all services"
	@echo ""
	@echo "Development:"
	@echo "  lint           Run linters on Go code"
	@echo "  format         Format Go code"
	@echo "  clean          Clean build artifacts"
	@echo "  setup          Setup development environment"

# Building
build:
	@echo "Building ArxOS..."
	go build -o bin/arx cmd/arx/main.go
	@echo "✅ ArxOS built successfully"

build-all: build build-ifc-service
	@echo "✅ All components built successfully"

build-ifc-service:
	@echo "Building IfcOpenShell service..."
	cd services/ifcopenshell-service && pip install -r requirements.txt
	@echo "✅ IfcOpenShell service built successfully"

# Docker builds
docker:
	@echo "Building Docker images..."
	docker build -t arxos:latest .
	docker build -t arxos-ifc-service:latest services/ifcopenshell-service/
	@echo "✅ Docker images built successfully"

docker-dev:
	@echo "Building development Docker images..."
	docker build -t arxos:dev .
	docker build -t arxos-ifc-service:dev services/ifcopenshell-service/
	@echo "✅ Development Docker images built successfully"

# Testing
test:
	@echo "Running ArxOS tests..."
	go test ./internal/infrastructure/ifc/... -v
	@echo "✅ ArxOS tests completed"

test-ifc:
	@echo "Running IfcOpenShell service tests..."
	cd services/ifcopenshell-service && python -m pytest tests/ -v
	@echo "✅ IfcOpenShell service tests completed"

test-all: test test-ifc
	@echo "✅ All tests completed"

test-integration:
	@echo "Running integration tests..."
	@echo "Starting services..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Running integration tests..."
	go test ./test/integration/... -v
	@echo "Stopping services..."
	docker-compose -f docker-compose.dev.yml down
	@echo "✅ Integration tests completed"

# Running services
run:
	@echo "Starting ArxOS with Docker Compose..."
	docker-compose up -d
	@echo "✅ ArxOS started successfully"
	@echo "ArxOS API: http://localhost:8080"
	@echo "IfcOpenShell Service: http://localhost:5000"
	@echo "PostGIS Database: localhost:5432"

run-dev:
	@echo "Starting ArxOS in development mode..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ ArxOS development environment started"
	@echo "ArxOS API: http://localhost:8080"
	@echo "IfcOpenShell Service: http://localhost:5000"
	@echo "PostGIS Database: localhost:5432"

run-ifc:
	@echo "Starting only IfcOpenShell service..."
	docker-compose up -d ifcopenshell-service postgis
	@echo "✅ IfcOpenShell service started"
	@echo "IfcOpenShell Service: http://localhost:5000"
	@echo "PostGIS Database: localhost:5432"

stop:
	@echo "Stopping all services..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down
	@echo "✅ All services stopped"

# Development tools
lint:
	@echo "Running linters..."
	golangci-lint run ./...
	@echo "✅ Linting completed"

format:
	@echo "Formatting Go code..."
	go fmt ./...
	goimports -w .
	@echo "✅ Code formatted"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf bin/
	rm -rf services/ifcopenshell-service/__pycache__/
	rm -rf services/ifcopenshell-service/tests/__pycache__/
	docker system prune -f
	@echo "✅ Cleanup completed"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	@echo "Installing Go dependencies..."
	go mod download
	@echo "Installing Python dependencies..."
	cd services/ifcopenshell-service && pip install -r requirements.txt
	@echo "Creating necessary directories..."
	mkdir -p bin/
	mkdir -p data/
	mkdir -p logs/
	@echo "✅ Development environment setup completed"

# Health checks
health:
	@echo "Checking service health..."
	@echo "ArxOS API:"
	@curl -s http://localhost:8080/health || echo "❌ ArxOS API not responding"
	@echo "IfcOpenShell Service:"
	@curl -s http://localhost:5000/health || echo "❌ IfcOpenShell service not responding"
	@echo "PostGIS Database:"
	@pg_isready -h localhost -p 5432 -U arxos || echo "❌ PostGIS database not responding"

# Logs
logs:
	@echo "Showing service logs..."
	docker-compose logs -f

logs-ifc:
	@echo "Showing IfcOpenShell service logs..."
	docker-compose logs -f ifcopenshell-service

# Database operations
db-migrate:
	@echo "Running database migrations..."
	go run cmd/arx/main.go migrate up
	@echo "✅ Database migrations completed"

db-reset:
	@echo "Resetting database..."
	docker-compose down postgis
	docker volume rm arxos_postgis-data || true
	docker-compose up -d postgis
	sleep 5
	$(MAKE) db-migrate
	@echo "✅ Database reset completed"

# IFC testing
test-ifc-file:
	@echo "Testing IFC file processing..."
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-ifc-file FILE=path/to/file.ifc"; exit 1; fi
	@echo "Testing file: $(FILE)"
	@curl -X POST -H "Content-Type: application/octet-stream" --data-binary @$(FILE) http://localhost:5000/api/parse
	@echo ""

# Performance testing
perf-test:
	@echo "Running performance tests..."
	@echo "Testing IfcOpenShell service performance..."
	@for i in {1..10}; do \
		echo "Request $$i:"; \
		time curl -s -X POST -H "Content-Type: application/octet-stream" --data-binary @test_data/inputs/sample.ifc http://localhost:5000/api/parse > /dev/null; \
	done
	@echo "✅ Performance tests completed"

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "ArxOS API Documentation:"
	@echo "  - Health: GET http://localhost:8080/health"
	@echo "  - IFC Import: POST http://localhost:8080/api/ifc/import"
	@echo ""
	@echo "IfcOpenShell Service Documentation:"
	@echo "  - Health: GET http://localhost:5000/health"
	@echo "  - Parse: POST http://localhost:5000/api/parse"
	@echo "  - Validate: POST http://localhost:5000/api/validate"
	@echo "  - Metrics: GET http://localhost:5000/metrics"
	@echo ""
	@echo "PostGIS Database:"
	@echo "  - Host: localhost"
	@echo "  - Port: 5432"
	@echo "  - Database: arxos"
	@echo "  - User: arxos"
	@echo "  - Password: arxos"
