# ArxOS Makefile for Windows PowerShell
# Provides easy commands for testing, building, and development

.PHONY: help test test-coverage test-race test-benchmark test-integration test-unit clean build run lint fmt vet mod-tidy security staticcheck install-tools

# Default target
help:
	@echo "ArxOS Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Testing Commands:"
	@echo "  test              Run all tests"
	@echo "  test-coverage     Run tests with coverage report"
	@echo "  test-race         Run tests with race detection"
	@echo "  test-benchmark    Run benchmarks"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-unit         Run unit tests only"
	@echo ""
	@echo "Development Commands:"
	@echo "  build             Build the application"
	@echo "  run               Run the application"
	@echo "  clean             Clean build artifacts"
	@echo "  fmt               Format code"
	@echo "  vet               Run go vet"
	@echo "  mod-tidy          Tidy go.mod"
	@echo "  lint              Run linter"
	@echo "  security          Run security scan"
	@echo "  staticcheck       Run static analysis"
	@echo ""
	@echo "Tool Installation:"
	@echo "  install-tools     Install development tools"
	@echo ""

# Test commands
test:
	@echo "Running all tests..."
	@powershell -ExecutionPolicy Bypass -File scripts/run_tests.ps1

test-coverage:
	@echo "Running tests with coverage..."
	@powershell -ExecutionPolicy Bypass -File scripts/run_tests.ps1 -CoverageThreshold 80

test-race:
	@echo "Running tests with race detection..."
	@powershell -ExecutionPolicy Bypass -File scripts/run_tests.ps1 -Race

test-benchmark:
	@echo "Running benchmarks..."
	@powershell -ExecutionPolicy Bypass -File scripts/run_tests.ps1 -Benchmark

test-integration:
	@echo "Running integration tests..."
	@go test -v -timeout=10m ./internal/app/...

test-unit:
	@echo "Running unit tests..."
	@go test -v -timeout=10m ./internal/app/di/... ./internal/infra/messaging/... ./internal/domain/...

# Development commands
build:
	@echo "Building ArxOS..."
	@go build -o bin/arx.exe ./cmd/arx

run:
	@echo "Running ArxOS..."
	@go run ./cmd/arx

clean:
	@echo "Cleaning build artifacts..."
	@if exist bin rmdir /s /q bin
	@if exist coverage rmdir /s /q coverage
	@if exist coverage_*.out del coverage_*.out
	@go clean

fmt:
	@echo "Formatting code..."
	@go fmt ./...

vet:
	@echo "Running go vet..."
	@go vet ./...

mod-tidy:
	@echo "Tidying go.mod..."
	@go mod tidy

lint:
	@echo "Running linter..."
	@if exist $(GOPATH)\bin\golangci-lint.exe (
		$(GOPATH)\bin\golangci-lint.exe run
	) else (
		echo "golangci-lint not found. Run 'make install-tools' to install it."
	)

security:
	@echo "Running security scan..."
	@if exist $(GOPATH)\bin\gosec.exe (
		$(GOPATH)\bin\gosec.exe ./...
	) else (
		echo "gosec not found. Run 'make install-tools' to install it."
	)

staticcheck:
	@echo "Running static analysis..."
	@if exist $(GOPATH)\bin\staticcheck.exe (
		$(GOPATH)\bin\staticcheck.exe ./...
	) else (
		echo "staticcheck not found. Run 'make install-tools' to install it."
	)

# Tool installation
install-tools:
	@echo "Installing development tools..."
	@go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	@go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
	@go install honnef.co/go/tools/cmd/staticcheck@latest
	@echo "Tools installed successfully!"

# Quick test for specific packages
test-di:
	@echo "Running DI tests..."
	@go test -v ./internal/app/di/...

test-websocket:
	@echo "Running WebSocket tests..."
	@go test -v ./internal/infra/messaging/...

test-domain:
	@echo "Running domain tests..."
	@go test -v ./internal/domain/...

test-app:
	@echo "Running application tests..."
	@go test -v ./internal/app/...

# Docker commands
docker-build:
	@echo "Building Docker image..."
	@docker build -t arxos .

docker-run:
	@echo "Running Docker container..."
	@docker run -p 8080:8080 arxos

docker-test:
	@echo "Running tests in Docker..."
	@docker run --rm -v ${PWD}:/app -w /app golang:1.21 go test ./...

# Database commands
db-migrate:
	@echo "Running database migrations..."
	@go run ./cmd/arx migrate

db-seed:
	@echo "Seeding database..."
	@go run ./scripts/seed_test_data.go

# Development server
dev:
	@echo "Starting development server..."
	@go run ./cmd/arx serve --port 8080 --config configs/development.yml

# Production build
prod-build:
	@echo "Building for production..."
	@go build -ldflags="-s -w" -o bin/arx.exe ./cmd/arx

# Test specific functionality
test-health:
	@echo "Testing health endpoint..."
	@go run ./cmd/arx health

test-config:
	@echo "Testing configuration..."
	@go test -v ./internal/config/...

test-validation:
	@echo "Testing validation..."
	@go test -v ./internal/validation/...

# Coverage report
coverage-report:
	@echo "Generating coverage report..."
	@go test -coverprofile=coverage.out ./...
	@go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Performance tests
perf-test:
	@echo "Running performance tests..."
	@go test -bench=. -benchmem ./...

# Memory profiling
mem-profile:
	@echo "Running memory profiling..."
	@go test -memprofile=mem.prof ./...
	@go tool pprof mem.prof

# CPU profiling
cpu-profile:
	@echo "Running CPU profiling..."
	@go test -cpuprofile=cpu.prof ./...
	@go tool pprof cpu.prof

# All-in-one development setup
setup:
	@echo "Setting up development environment..."
	@make install-tools
	@make mod-tidy
	@make fmt
	@make vet
	@echo "Development environment ready!"

# CI/CD pipeline
ci:
	@echo "Running CI pipeline..."
	@make fmt
	@make vet
	@make mod-tidy
	@make test-coverage
	@make security
	@make staticcheck
	@echo "CI pipeline completed!"

# Release preparation
release-prep:
	@echo "Preparing for release..."
	@make clean
	@make fmt
	@make vet
	@make mod-tidy
	@make test-coverage
	@make security
	@make staticcheck
	@make prod-build
	@echo "Release preparation completed!"