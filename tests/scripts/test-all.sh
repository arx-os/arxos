#!/bin/bash

# Run all ArxOS tests
set -e

echo "=== ArxOS Test Suite ==="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Track results
FAILED=0

# Run unit tests
echo "Running unit tests..."
if go test -v ./cmd/... ./core/... -short; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    FAILED=1
fi
echo

# Run integration tests (if services are running)
echo "Running integration tests..."
if go test -v ./tests/integration/...; then
    echo -e "${GREEN}✓ Integration tests passed${NC}"
else
    echo -e "${RED}✗ Integration tests failed${NC}"
    FAILED=1
fi
echo

# Check if E2E should run
if [ "$RUN_E2E" = "true" ]; then
    echo "Running E2E tests..."
    if go test -v ./tests/e2e/...; then
        echo -e "${GREEN}✓ E2E tests passed${NC}"
    else
        echo -e "${RED}✗ E2E tests failed${NC}"
        FAILED=1
    fi
    echo
fi

# Coverage report
if [ "$COVERAGE" = "true" ]; then
    echo "Generating coverage report..."
    go test -coverprofile=coverage.out ./...
    go tool cover -html=coverage.out -o coverage.html
    echo "Coverage report saved to coverage.html"
    echo
fi

# Summary
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}=== All tests passed! ===${NC}"
    exit 0
else
    echo -e "${RED}=== Some tests failed ===${NC}"
    exit 1
fi