# ArxOS Makefile

# Variables
BINARY_DIR := bin
BINARY := $(BINARY_DIR)/arx
GO := go
GOFLAGS := -v
LDFLAGS := -s -w

# Version info
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Build flags with version info
BUILD_FLAGS := -ldflags "$(LDFLAGS) -X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME) -X main.Commit=$(COMMIT)"

.PHONY: all build clean test run install help dev docker deploy test-integration docker-test-up docker-test-down

# Default target
all: build

# Build single binary
build:
	@echo "🔨 Building ArxOS..."
	@mkdir -p $(BINARY_DIR)
	$(GO) build $(GOFLAGS) $(BUILD_FLAGS) -o $(BINARY) ./cmd/arx
	@echo "✅ Build complete: $(BINARY)"

# Run the CLI
run: build
	@echo "🚀 Running ArxOS..."
	$(BINARY)

# Run server mode
run-server: build
	@echo "🚀 Running ArxOS server..."
	$(BINARY) serve

# Run tests
test:
	@echo "🧪 Running tests..."
	$(GO) test -v ./...

# Run tests with coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	$(GO) test -v -cover -coverprofile=coverage.out ./...
	$(GO) tool cover -html=coverage.out -o coverage.html
	@echo "📊 Coverage report generated: coverage.html"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning..."
	rm -rf $(BINARY_DIR)
	rm -f coverage.out coverage.html
	rm -f *.test
	rm -rf testdata/output testdata/temp
	@echo "✨ Clean complete"

# Install binary to system
install: build
	@echo "📦 Installing ArxOS..."
	@cp $(BINARY) /usr/local/bin/arx
	@echo "✅ Installed to /usr/local/bin/arx"

# Format code
fmt:
	@echo "🎨 Formatting code..."
	$(GO) fmt ./...
	@echo "✅ Code formatted"

# Run linter
lint:
	@echo "🔍 Running linter..."
	@which golangci-lint > /dev/null || (echo "❌ golangci-lint not installed. Run: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest" && exit 1)
	golangci-lint run
	@echo "✅ Linting complete"

# Check for security issues
security:
	@echo "🔒 Checking security..."
	@which gosec > /dev/null || (echo "❌ gosec not installed. Run: go install github.com/securego/gosec/v2/cmd/gosec@latest" && exit 1)
	gosec ./...
	@echo "✅ Security check complete"

# Update dependencies
deps:
	@echo "📦 Updating dependencies..."
	$(GO) mod download
	$(GO) mod tidy
	@echo "✅ Dependencies updated"

# Development setup
dev: deps build
	@echo "🛠️  Development environment ready"

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t arxos:latest .
	@echo "✅ Docker image built"

docker-run:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Docker services started"

docker-stop:
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✅ Docker services stopped"

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# Deployment commands
deploy-dev: docker-build docker-run
	@echo "🚀 Development deployment complete"
	@echo "📡 API Server: http://localhost:8080"
	@echo "📊 Traefik Dashboard: http://localhost:8888"

deploy-prod:
	@echo "🚀 Production deployment..."
	@echo "⚠️  Make sure to configure .env file first"
	docker-compose -f docker-compose.yml up -d
	@echo "✅ Production deployment complete"

# PostGIS test commands
docker-test-up:
	@echo "🐳 Starting PostGIS test container..."
	@docker-compose -f docker-compose.test.yml up -d postgis
	@sleep 5
	@echo "✅ PostGIS test container ready"

docker-test-down:
	@echo "🛑 Stopping PostGIS test container..."
	@docker-compose -f docker-compose.test.yml down -v
	@echo "✅ PostGIS test container stopped"

test-integration: docker-test-up
	@echo "🧪 Running integration tests..."
	@ARXOS_DB_TYPE=postgis \
	 ARXOS_POSTGIS_URL=postgres://arxos:testpass@localhost:5432/arxos_test?sslmode=disable \
	 $(GO) test -tags=integration $(GOFLAGS) ./internal/database/...
	@$(MAKE) docker-test-down
	@echo "✅ Integration tests complete"

# Database commands
db-backup:
	@echo "💾 Creating database backup..."
	docker-compose exec arxos sqlite3 /app/data/arxos.db ".backup /app/data/backup-$(shell date +%Y%m%d-%H%M%S).db"
	@echo "✅ Database backup created"

db-migrate:
	@echo "🔄 Running database migrations..."
	docker-compose exec arxos ./arx migrate
	@echo "✅ Database migrations complete"

# Release commands
release-prepare:
	@echo "📦 Preparing release..."
	@which goreleaser > /dev/null || (echo "❌ goreleaser not installed. Visit: https://goreleaser.com/install/" && exit 1)
	goreleaser check
	@echo "✅ Release preparation complete"

release-snapshot:
	@echo "📦 Creating snapshot release..."
	goreleaser release --snapshot --rm-dist
	@echo "✅ Snapshot release created"

# Help target
help:
	@echo "ArxOS Makefile Commands:"
	@echo ""
	@echo "  make build        - Build the arx binary"
	@echo "  make run          - Build and run arx CLI"
	@echo "  make run-server   - Build and run arx in server mode"
	@echo "  make test         - Run tests"
	@echo "  make test-coverage- Run tests with coverage report"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make install      - Install arx to /usr/local/bin"
	@echo "  make fmt          - Format code"
	@echo "  make lint         - Run linter (requires golangci-lint)"
	@echo "  make security     - Run security check (requires gosec)"
	@echo "  make deps         - Update dependencies"
	@echo "  make dev          - Setup development environment"
	@echo "  make help         - Show this help message"