# ArxOS Test Suite

Clean test structure for the ArxOS codebase.

## Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for service interactions
├── e2e/           # End-to-end tests for complete workflows
└── scripts/       # Test helper scripts
```

## Running Tests

### All Tests
```bash
make test
```

### Unit Tests Only
```bash
make test-unit
```

### Integration Tests
```bash
make test-integration
```

### E2E Tests
```bash
make test-e2e
```

## Test Coverage

```bash
make test-coverage
```

## Adding New Tests

1. Unit tests go next to the code they test with `_test.go` suffix
2. Integration tests go in `tests/integration/`
3. E2E tests simulate real user workflows in `tests/e2e/`