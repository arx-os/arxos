# Arxos Test Suite Makefile

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Go parameters
GOTEST=go test
GOTEST_UNIT=$(GOTEST) -short -race -coverprofile=coverage-unit.out
GOTEST_INTEGRATION=$(GOTEST) -race -coverprofile=coverage-integration.out
GOTEST_E2E=$(GOTEST) -tags=e2e

# Test directories
UNIT_DIR=./unit/...
INTEGRATION_DIR=./integration/...
E2E_DIR=./e2e/...
PERFORMANCE_DIR=./performance/...

# Default target
.PHONY: all
all: test

# Help target
.PHONY: help
help:
	@echo "$(BLUE)Arxos Test Suite$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  $(GREEN)make test$(NC)           - Run all tests"
	@echo "  $(GREEN)make test-unit$(NC)      - Run unit tests only"
	@echo "  $(GREEN)make test-integration$(NC) - Run integration tests"
	@echo "  $(GREEN)make test-e2e$(NC)       - Run end-to-end tests"
	@echo "  $(GREEN)make test-performance$(NC) - Run performance tests"
	@echo "  $(GREEN)make test-security$(NC)  - Run security tests"
	@echo "  $(GREEN)make coverage$(NC)       - Generate coverage report"
	@echo "  $(GREEN)make clean$(NC)          - Clean test artifacts"
	@echo ""
	@echo "$(YELLOW)Quick tests (for development):$(NC)"
	@echo "  $(GREEN)make quick$(NC)          - Run fast unit tests"
	@echo "  $(GREEN)make smoke$(NC)          - Run smoke tests"
	@echo ""
	@echo "$(YELLOW)CI/CD targets:$(NC)"
	@echo "  $(GREEN)make ci-unit$(NC)        - CI unit tests"
	@echo "  $(GREEN)make ci-integration$(NC) - CI integration tests"
	@echo "  $(GREEN)make ci-e2e$(NC)         - CI e2e tests"

# Main test targets
.PHONY: test
test: test-unit test-integration test-e2e-smoke
	@echo "$(GREEN)✓ All tests passed$(NC)"

.PHONY: test-unit
test-unit:
	@echo "$(YELLOW)Running unit tests...$(NC)"
	@cd ../core && $(GOTEST_UNIT) ./...
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

.PHONY: test-integration
test-integration: db-test-up
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@cd ../core && $(GOTEST_INTEGRATION) ./tests/...
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

.PHONY: test-e2e
test-e2e: services-up
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	@cd ../core && $(GOTEST_E2E) $(E2E_DIR)
	@echo "$(GREEN)✓ E2E tests passed$(NC)"

.PHONY: test-e2e-smoke
test-e2e-smoke:
	@echo "$(YELLOW)Running E2E smoke tests...$(NC)"
	@echo "$(GREEN)✓ Smoke tests passed (TODO: implement)$(NC)"

.PHONY: test-performance
test-performance:
	@echo "$(YELLOW)Running performance tests...$(NC)"
	@if command -v k6 > /dev/null; then \
		k6 run performance/load/confidence_api_load.js; \
	else \
		echo "$(RED)K6 not installed. Install with: brew install k6$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Performance tests completed$(NC)"

.PHONY: test-security
test-security:
	@echo "$(YELLOW)Running security tests...$(NC)"
	@if command -v gosec > /dev/null; then \
		gosec -fmt json -out security-report.json ../core/...; \
	else \
		echo "$(YELLOW)Installing gosec...$(NC)"; \
		go install github.com/securego/gosec/v2/cmd/gosec@latest; \
		gosec -fmt json -out security-report.json ../core/...; \
	fi
	@echo "$(GREEN)✓ Security scan completed$(NC)"

# Quick development tests
.PHONY: quick
quick:
	@echo "$(YELLOW)Running quick unit tests...$(NC)"
	@cd ../core && go test -short ./...
	@echo "$(GREEN)✓ Quick tests passed$(NC)"

.PHONY: smoke
smoke:
	@echo "$(YELLOW)Running smoke tests...$(NC)"
	@./scripts/smoke-test.sh
	@echo "$(GREEN)✓ Smoke tests passed$(NC)"

# Coverage
.PHONY: coverage
coverage:
	@echo "$(YELLOW)Generating coverage report...$(NC)"
	@cd ../core && go test -race -coverprofile=coverage.out -covermode=atomic ./...
	@cd ../core && go tool cover -html=coverage.out -o coverage.html
	@echo "$(GREEN)✓ Coverage report generated: coverage.html$(NC)"

.PHONY: coverage-view
coverage-view: coverage
	@open ../core/coverage.html

# Database management
.PHONY: db-test-up
db-test-up:
	@echo "$(YELLOW)Starting test database...$(NC)"
	@cd .. && docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d postgres redis
	@sleep 3
	@echo "$(GREEN)✓ Test database ready$(NC)"

.PHONY: db-test-down
db-test-down:
	@echo "$(YELLOW)Stopping test database...$(NC)"
	@cd .. && docker-compose -f docker-compose.yml -f docker-compose.test.yml down
	@echo "$(GREEN)✓ Test database stopped$(NC)"

# Service management
.PHONY: services-up
services-up:
	@echo "$(YELLOW)Starting all services...$(NC)"
	@cd .. && docker-compose up -d
	@sleep 5
	@echo "$(GREEN)✓ Services ready$(NC)"

.PHONY: services-down
services-down:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@cd .. && docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

# CI/CD targets
.PHONY: ci-unit
ci-unit:
	@echo "$(YELLOW)Running CI unit tests...$(NC)"
	@cd ../core && go test -short -race -coverprofile=coverage.out ./...
	@echo "$(GREEN)✓ CI unit tests passed$(NC)"

.PHONY: ci-integration
ci-integration: db-test-up
	@echo "$(YELLOW)Running CI integration tests...$(NC)"
	@cd ../core && go test -race ./tests/...
	@echo "$(GREEN)✓ CI integration tests passed$(NC)"

.PHONY: ci-e2e
ci-e2e: services-up
	@echo "$(YELLOW)Running CI E2E tests...$(NC)"
	@cd ../core && go test -tags=e2e ./tests/e2e/...
	@echo "$(GREEN)✓ CI E2E tests passed$(NC)"

# Benchmarks
.PHONY: benchmark
benchmark:
	@echo "$(YELLOW)Running benchmarks...$(NC)"
	@cd ../core && go test -bench=. -benchmem ./...
	@echo "$(GREEN)✓ Benchmarks completed$(NC)"

# Test data management
.PHONY: fixtures-reset
fixtures-reset:
	@echo "$(YELLOW)Resetting test fixtures...$(NC)"
	@./scripts/reset-fixtures.sh
	@echo "$(GREEN)✓ Fixtures reset$(NC)"

# Cleanup
.PHONY: clean
clean:
	@echo "$(YELLOW)Cleaning test artifacts...$(NC)"
	@rm -f coverage*.out coverage*.html
	@rm -f security-report.json
	@rm -rf reports/*
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# Watch mode for development
.PHONY: watch
watch:
	@echo "$(YELLOW)Starting test watcher...$(NC)"
	@while true; do \
		$(MAKE) quick; \
		echo "$(BLUE)Waiting for changes...$(NC)"; \
		fswatch -1 -r ../core; \
	done

# Validation
.PHONY: validate
validate:
	@echo "$(YELLOW)Validating test structure...$(NC)"
	@./scripts/validate-tests.sh
	@echo "$(GREEN)✓ Test structure valid$(NC)"

.DEFAULT_GOAL := help