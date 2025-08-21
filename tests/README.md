# Test Suite

Comprehensive testing framework for the ARXOS platform.

## Purpose

This directory contains integration tests, load tests, and test utilities for validating ARXOS functionality across all components.

## Structure

```
tests/
├── load/                 # Load testing and performance tests
├── test_integration.sh   # Integration test runner
├── test_local_server.sh  # Local server test script
└── test_server.go        # Test HTTP server
```

## Test Types

- **Integration Tests**: End-to-end system validation
- **Load Tests**: Performance and scalability testing
- **Local Tests**: Development environment validation

## Running Tests

```bash
# Run integration tests
./test_integration.sh

# Run local server tests
./test_local_server.sh

# Start test server
go run test_server.go
```

## Documentation

For testing details, see [Development Guide](../../docs/development/guide.md#testing-strategy).

## Unit Tests

Unit tests are located within their respective component directories:
- Backend tests: `core/backend/tests/`
- AI service tests: `ai_service/tests/`
