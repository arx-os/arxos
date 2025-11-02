# Persistence Tests

These tests verify building data persistence operations including save, load, and Git integration.

## Running Tests

### Individual Tests
All tests pass when run individually:
```bash
cargo test --test persistence_tests test_name
```

### Full Test Suite
Tests are configured to run serially automatically:
```bash
cargo test --test persistence_tests
```

## Test Isolation

Tests use:
- **DirectoryGuard**: RAII guard that automatically restores the original directory
- **TempDir**: Each test uses its own temporary directory
- **Cleanup**: Automatic cleanup of YAML files on test completion
- **Serial execution**: Tests automatically run serially using `#[serial]` attribute to prevent directory conflicts

## Test Structure

Each test:
1. Creates a unique temp directory
2. Changes to that directory using `DirectoryGuard`
3. Performs test operations
4. Automatically cleans up and restores directory on completion

This ensures complete isolation between tests.

