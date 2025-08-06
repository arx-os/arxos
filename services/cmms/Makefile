# CMMS Service Makefile

.PHONY: help build test clean run docker-build docker-run docker-stop lint fmt

# Default target
help:
	@echo "Available targets:"
	@echo "  build        - Build the CMMS service"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean build artifacts"
	@echo "  run          - Run the service locally"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker Compose services"
	@echo "  lint         - Run linter"
	@echo "  fmt          - Format code"

# Build the service
build:
	@echo "Building CMMS service..."
	go build -o bin/cmms-service ./cmd/cmms-service

# Run tests
test:
	@echo "Running tests..."
	go test -v ./...

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf bin/
	go clean

# Run the service locally
run: build
	@echo "Running CMMS service..."
	./bin/cmms-service

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t arxos/cmms-service:latest .

# Run with Docker Compose
docker-run:
	@echo "Starting CMMS service with Docker Compose..."
	docker-compose up -d

# Stop Docker Compose services
docker-stop:
	@echo "Stopping Docker Compose services..."
	docker-compose down

# Run linter
lint:
	@echo "Running linter..."
	golangci-lint run

# Format code
fmt:
	@echo "Formatting code..."
	go fmt ./...

# Install dependencies
deps:
	@echo "Installing dependencies..."
	go mod download
	go mod tidy

# Generate mocks (if using mockgen)
mocks:
	@echo "Generating mocks..."
	mockgen -source=internal/connector/connector.go -destination=internal/connector/mocks.go
	mockgen -source=internal/sync/sync.go -destination=internal/sync/mocks.go

# Run with hot reload (requires air)
dev:
	@echo "Running with hot reload..."
	air

# Database migrations
migrate:
	@echo "Running database migrations..."
	# Add migration commands here

# Seed database
seed:
	@echo "Seeding database..."
	# Add seed commands here

# Build for production
build-prod:
	@echo "Building for production..."
	CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o bin/cmms-service ./cmd/cmms-service

# Create release
release: build-prod
	@echo "Creating release..."
	tar -czf cmms-service-$(shell git describe --tags --always).tar.gz bin/

# Show service status
status:
	@echo "Service status:"
	@docker-compose ps

# View logs
logs:
	@echo "Viewing logs..."
	@docker-compose logs -f cmms-service

# Access database
db:
	@echo "Accessing database..."
	@docker-compose exec postgres psql -U arxos -d arxos

# Backup database
backup:
	@echo "Backing up database..."
	@docker-compose exec postgres pg_dump -U arxos arxos > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore:
	@echo "Restoring database..."
	@docker-compose exec -T postgres psql -U arxos -d arxos < $(file)

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8080/health || echo "Service is not healthy"

# Performance test
perf-test:
	@echo "Running performance tests..."
	@ab -n 1000 -c 10 http://localhost:8080/health

# Security scan
security-scan:
	@echo "Running security scan..."
	@gosec ./...

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	go get -u ./...
	go mod tidy 