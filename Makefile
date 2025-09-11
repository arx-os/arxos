# ArxOS Makefile

# Variables
BINARY_DIR := bin
CLI_BINARY := $(BINARY_DIR)/arx
DAEMON_BINARY := $(BINARY_DIR)/arxd
GO := go
GOFLAGS := -v
LDFLAGS := -s -w

# Version info
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Build flags with version info
BUILD_FLAGS := -ldflags "$(LDFLAGS) -X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME) -X main.Commit=$(COMMIT)"

.PHONY: all build clean test run-cli run-daemon install help

# Default target
all: build

# Build both binaries
build: build-cli build-daemon
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

# Run CLI
run-cli: build-cli
	@echo "🚀 Running CLI..."
	$(CLI_BINARY)

# Run daemon
run-daemon: build-daemon
	@echo "🚀 Running daemon..."
	$(DAEMON_BINARY) start --config configs/arxd.yaml

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

# Help target
help:
	@echo "ArxOS Makefile Commands:"
	@echo ""
	@echo "  make build        - Build both CLI and daemon"
	@echo "  make build-cli    - Build only the CLI"
	@echo "  make build-daemon - Build only the daemon"
	@echo "  make run-cli      - Build and run the CLI"
	@echo "  make run-daemon   - Build and run the daemon"
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