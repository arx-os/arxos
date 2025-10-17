# Makefile for ArxOS
# Provides targets for development, testing, and linting

.PHONY: help build test lint lint-fix clean install-tools check-interface

# Default target
help: ## Show this help message
	@echo "ArxOS Development Makefile"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Build targets
build: ## Build the project
	@echo "Building ArxOS..."
	go build -v ./...

build-race: ## Build with race detection
	@echo "Building ArxOS with race detection..."
	go build -race -v ./...

# Test targets
test: ## Run all tests
	@echo "Running tests..."
	go test -v ./...

test-race: ## Run tests with race detection
	@echo "Running tests with race detection..."
	go test -race -v ./...

test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

test-bench: ## Run benchmark tests
	@echo "Running benchmark tests..."
	go test -bench=. -benchmem ./...

test-integration: ## Run integration tests (requires test database)
	@echo "Running integration tests..."
	@echo "Ensure test database is running: docker-compose -f docker-compose.test.yml up -d"
	go test ./test/integration/... -v -count=1

test-integration-coverage: ## Run integration tests with coverage
	@echo "Running integration tests with coverage..."
	go test ./test/integration/... -v -count=1 -coverprofile=coverage-integration.out
	go tool cover -html=coverage-integration.out -o coverage-integration.html
	@echo "Integration coverage report: coverage-integration.html"

test-short: ## Run only unit tests (skip integration)
	@echo "Running unit tests only..."
	go test -short ./... -v

test-db-start: ## Start test database
	@echo "Starting test database..."
	docker-compose -f docker-compose.test.yml up -d postgres-test
	@echo "Waiting for database to be ready..."
	@sleep 3
	@docker-compose -f docker-compose.test.yml ps

test-db-stop: ## Stop test database
	@echo "Stopping test database..."
	docker-compose -f docker-compose.test.yml down

test-db-clean: ## Clean test database and volumes
	@echo "Cleaning test database..."
	docker-compose -f docker-compose.test.yml down -v

migrate-test: ## Run migrations on test database
	@echo "Running migrations on test database..."
	@export TEST_DB_HOST=localhost TEST_DB_PORT=5433 TEST_DB_NAME=arxos_test && \
	psql -h $$TEST_DB_HOST -p $$TEST_DB_PORT -U postgres -d $$TEST_DB_NAME -f internal/migrations/*.up.sql || \
	echo "Note: Run 'make migrate-up' with TEST_DB_* env vars set"

# Linting targets
lint: ## Run all linters
	@echo "Running linters..."
	@$(MAKE) check-interface
	@$(MAKE) golangci-lint

lint-fix: ## Run linters and fix issues where possible
	@echo "Running linters with auto-fix..."
	@$(MAKE) check-interface
	golangci-lint run --fix

check-interface: ## Check for interface{} usage
	@echo "Checking for interface{} usage..."
	@./scripts/lint-interface.sh

golangci-lint: ## Run golangci-lint
	@echo "Running golangci-lint..."
	golangci-lint run --config=.golangci.yml

# Formatting targets
fmt: ## Format Go code
	@echo "Formatting Go code..."
	go fmt ./...
	goimports -w .

fmt-check: ## Check if code is formatted
	@echo "Checking code formatting..."
	@if [ $$(gofmt -l . | wc -l) -ne 0 ]; then \
		echo "Code is not formatted. Run 'make fmt' to fix."; \
		gofmt -l .; \
		exit 1; \
	fi
	@if [ $$(goimports -l . | wc -l) -ne 0 ]; then \
		echo "Imports are not organized. Run 'make fmt' to fix."; \
		goimports -l .; \
		exit 1; \
	fi

# Code generation targets
generate: ## Generate code
	@echo "Generating code..."
	go generate ./...

# Clean targets
clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	go clean -cache
	rm -f coverage.out coverage.html
	rm -rf dist/

clean-mod: ## Clean module cache
	@echo "Cleaning module cache..."
	go clean -modcache

# Installation targets
install-tools: ## Install development tools
	@echo "Installing development tools..."
	@if ! command -v golangci-lint >/dev/null 2>&1; then \
		echo "Installing golangci-lint..."; \
		curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $$(go env GOPATH)/bin v1.54.2; \
	fi
	@if ! command -v goimports >/dev/null 2>&1; then \
		echo "Installing goimports..."; \
		go install golang.org/x/tools/cmd/goimports@latest; \
	fi
	@if ! command -v pre-commit >/dev/null 2>&1; then \
		echo "Installing pre-commit..."; \
		pip install pre-commit; \
	fi

install-pre-commit: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	pre-commit install

# Development targets
dev-setup: install-tools install-pre-commit ## Set up development environment
	@echo "Development environment setup complete!"

# CI/CD targets
ci-test: test-race test-coverage ## Run CI tests
	@echo "CI tests completed!"

ci-lint: lint ## Run CI linting
	@echo "CI linting completed!"

ci-build: build-race ## Run CI build
	@echo "CI build completed!"

# Security targets
security: ## Run security checks
	@echo "Running security checks..."
	gosec ./...

# Documentation targets
docs: ## Generate documentation
	@echo "Generating documentation..."
	godoc -http=:6060 &
	@echo "Documentation server started at http://localhost:6060"
	@echo "Press Ctrl+C to stop"

# Release targets
release-check: ## Check if ready for release
	@echo "Checking release readiness..."
	@$(MAKE) fmt-check
	@$(MAKE) lint
	@$(MAKE) test
	@$(MAKE) build
	@echo "Release check completed!"

# Docker targets
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t arxos:latest .

docker-run: ## Run Docker container
	@echo "Running Docker container..."
	docker run -p 8080:8080 arxos:latest

# Database targets
db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	go run cmd/migrate/main.go

db-seed: ## Seed database with test data
	@echo "Seeding database..."
	go run cmd/seed/main.go

# Monitoring targets
monitor: ## Start monitoring
	@echo "Starting monitoring..."
	go run cmd/monitor/main.go

# Backup targets
backup: ## Create backup
	@echo "Creating backup..."
	go run cmd/backup/main.go

# Restore targets
restore: ## Restore from backup
	@echo "Restoring from backup..."
	go run cmd/restore/main.go

# Health check targets
health: ## Check system health
	@echo "Checking system health..."
	go run cmd/health/main.go

# Performance targets
perf-test: ## Run performance tests
	@echo "Running performance tests..."
	go test -bench=. -benchmem -cpuprofile=cpu.prof -memprofile=mem.prof ./...

perf-analyze: ## Analyze performance profiles
	@echo "Analyzing performance profiles..."
	go tool pprof cpu.prof
	go tool pprof mem.prof

# Dependencies
deps: ## Download dependencies
	@echo "Downloading dependencies..."
	go mod download
	go mod tidy

deps-update: ## Update dependencies
	@echo "Updating dependencies..."
	go get -u ./...
	go mod tidy

# Version targets
version: ## Show version information
	@echo "ArxOS Version Information:"
	@echo "Go version: $$(go version)"
	@echo "Git commit: $$(git rev-parse HEAD)"
	@echo "Git branch: $$(git rev-parse --abbrev-ref HEAD)"
	@echo "Build time: $$(date)"

# Environment targets
env: ## Show environment information
	@echo "Environment Information:"
	@echo "GOOS: $$(go env GOOS)"
	@echo "GOARCH: $$(go env GOARCH)"
	@echo "GOPATH: $$(go env GOPATH)"
	@echo "GOROOT: $$(go env GOROOT)"
	@echo "GOMOD: $$(go env GOMOD)"

# Quick development workflow
dev: fmt lint test ## Quick development workflow (format, lint, test)
	@echo "Development workflow completed!"

# Full development workflow
full: clean deps fmt lint test build ## Full development workflow
	@echo "Full development workflow completed!"
