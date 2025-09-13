# ArxOS Makefile

# Variables
BINARY_DIR := bin
CLI_BINARY := $(BINARY_DIR)/arx
DAEMON_BINARY := $(BINARY_DIR)/arxd
SERVER_BINARY := $(BINARY_DIR)/arxos-server
GO := go
GOFLAGS := -v
LDFLAGS := -s -w

# Version info
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Build flags with version info
BUILD_FLAGS := -ldflags "$(LDFLAGS) -X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME) -X main.Commit=$(COMMIT)"

.PHONY: all build clean test run-cli run-daemon run-server install help dev docker deploy

# Default target
all: build

# Build all binaries
build: build-cli build-daemon build-server
	@echo "✅ Build complete"

# Build CLI
build-cli:
	@echo "🔨 Building CLI..."
	@mkdir -p $(BINARY_DIR)
	$(GO) build $(GOFLAGS) $(BUILD_FLAGS) -o $(CLI_BINARY) ./cmd/arx

# Build daemon
build-daemon:
	@echo "🔨 Building daemon..."
	@mkdir -p $(BINARY_DIR)
	$(GO) build $(GOFLAGS) $(BUILD_FLAGS) -o $(DAEMON_BINARY) ./cmd/arxd

# Build server
build-server:
	@echo "🔨 Building server..."
	@mkdir -p $(BINARY_DIR)
	$(GO) build $(GOFLAGS) $(BUILD_FLAGS) -o $(SERVER_BINARY) ./cmd/arxos-server

# Run CLI
run-cli: build-cli
	@echo "🚀 Running CLI..."
	$(CLI_BINARY)

# Run daemon
run-daemon: build-daemon
	@echo "🚀 Running daemon..."
	$(DAEMON_BINARY) start --config configs/arxd.yaml

# Run server
run-server: build-server
	@echo "🚀 Running server..."
	$(SERVER_BINARY) -db data/arxos.db

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

# Install binaries to GOPATH
install: build
	@echo "📦 Installing..."
	$(GO) install ./cmd/arx
	$(GO) install ./cmd/arxd
	@echo "✅ Installed to GOPATH"

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
	@echo "🐳 Building Docker images..."
	docker build -f Dockerfile.server -t arxos-server:latest .
	@echo "✅ Docker images built"

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

# Database commands
db-backup:
	@echo "💾 Creating database backup..."
	docker-compose exec arxos-server sqlite3 /app/data/arxos.db ".backup /app/data/backup-$(shell date +%Y%m%d-%H%M%S).db"
	@echo "✅ Database backup created"

db-migrate:
	@echo "🔄 Running database migrations..."
	docker-compose exec arxos-server ./arxos-server migrate
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
	@echo "  make build        - Build all binaries (CLI, daemon, and server)"
	@echo "  make build-cli    - Build only the CLI"
	@echo "  make build-daemon - Build only the daemon"
	@echo "  make build-server - Build only the server"
	@echo "  make run-cli      - Build and run the CLI"
	@echo "  make run-daemon   - Build and run the daemon"
	@echo "  make run-server   - Build and run the server"
	@echo "  make test         - Run tests"
	@echo "  make test-coverage- Run tests with coverage report"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make install      - Install binaries to GOPATH"
	@echo "  make fmt          - Format code"
	@echo "  make lint         - Run linter (requires golangci-lint)"
	@echo "  make security     - Run security check (requires gosec)"
	@echo "  make deps         - Update dependencies"
	@echo "  make dev          - Setup development environment"
	@echo "  make help         - Show this help message"