# Arxos Test Suite

This directory contains test files and utilities for the Arxos system.

## Test Files

### HTML Test Pages
- `test_pdf_simple.html` - Simple PDF processing test
- `test_pdf_batch.html` - Batch PDF processing test

### Test Server
- `test_server.go` - Simple Go HTTP server for testing
  - Serves static files
  - Provides health check endpoint
  - Lists available demos

### Shell Scripts
- `test_integration.sh` - Integration test runner
- `test_local_server.sh` - Local server test script

## Running Tests

### Start Test Server
```bash
go run test_server.go
# Server runs on http://localhost:8080
```

### Run Integration Tests
```bash
./test_integration.sh
```

### Run Local Server Tests
```bash
./test_local_server.sh
```

## Test Coverage

The test suite covers:
- PDF wall extraction accuracy
- Batch processing capabilities
- Server endpoints
- File upload functionality
- BIM conversion pipeline

For unit tests, see `core/backend/tests/` directory.