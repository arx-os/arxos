# Test Organization

**Last Updated:** January 2025

## Overview

This directory contains all integration tests for ArxOS. Tests are organized by feature category using descriptive prefixes for easy identification and navigation.

## Test Organization Strategy

Since Rust's `cargo test` only discovers tests directly in the `tests/` directory (not subdirectories), we use **descriptive prefixes** to organize tests by category while maintaining a flat structure that Cargo can discover.

### Test Categories

#### AR Tests (`ar_*`)
AR integration and workflow tests:
- `ar_complete_workflow_test.rs` - Complete AR workflow end-to-end
- `ar_gltf_integration_tests.rs` - glTF export integration tests
- `ar_usdz_integration_tests.rs` - USDZ export integration tests
- `ar_workflow_integration_test.rs` - AR workflow integration
- `ar_ios_workflow_integration_tests.rs` - iOS AR workflow integration
- `ar_json_helpers_tests.rs` - AR JSON parsing helper tests

#### Mobile/FFI Tests (`mobile_*`)
Mobile FFI and cross-platform tests:
- `mobile_ffi_tests.rs` - Core FFI function tests (JNI, iOS, error handling)

#### Hardware Tests (`hardware_*`)
Hardware sensor integration tests:
- `hardware_integration_tests.rs` - Core hardware integration
- `hardware_http_integration_tests.rs` - HTTP sensor integration
- `hardware_workflow_tests.rs` - Hardware workflow tests

#### Persistence Tests (`persistence_*`)
Data persistence and Git integration tests:
- `persistence_tests.rs` - Building data persistence, save/load, Git operations

#### E2E Tests (`e2e_*`)
End-to-end workflow tests:
- `e2e_workflow_tests.rs` - Complete end-to-end workflows
- `e2e_command_integration_tests.rs` - Command integration tests

#### IFC Tests (`ifc_*`)
IFC file processing tests:
- `ifc_workflow_tests.rs` - IFC processing workflows
- `ifc_sync_integration_tests.rs` - IFC bidirectional sync

#### Command Tests (`commands/`)
Unit tests for individual command handlers:
- Located in `tests/commands/` subdirectory
- One test file per command module
- See `tests/commands/README.md` for details

#### Other Tests
- `docs_integration_tests.rs` - Documentation generation tests
- `game_integration_tests.rs` - Gamified PR review tests
- `integration_tests.rs` - General integration tests
- `security_tests.rs` - Security and validation tests

## Running Tests

### Run All Tests
```bash
cargo test
```

### Run Tests by Category
```bash
# AR tests
cargo test --test ar_

# Mobile/FFI tests
cargo test --test mobile_

# Hardware tests
cargo test --test hardware_

# Persistence tests
cargo test --test persistence_

# E2E tests
cargo test --test e2e_

# IFC tests
cargo test --test ifc_
```

### Run Specific Test File
```bash
cargo test --test ar_workflow_integration_test
cargo test --test mobile_ffi_tests
cargo test --test hardware_integration_tests
```

### Run Command Tests
```bash
cargo test --test commands/ar_tests
cargo test --test commands/export_tests
# etc.
```

## Test File Naming Convention

Tests use the following naming pattern:
- **Category prefix** (e.g., `ar_`, `mobile_`, `hardware_`)
- **Feature name** (e.g., `workflow`, `integration`, `gltf`)
- **Test type suffix** (e.g., `_tests.rs`, `_test.rs`)

Examples:
- `ar_workflow_integration_test.rs` - AR workflow integration test
- `mobile_ffi_tests.rs` - Mobile FFI tests
- `hardware_http_integration_tests.rs` - Hardware HTTP integration tests

## Benefits of This Organization

1. **Easy Discovery**: Files grouped by prefix make it easy to find related tests
2. **Cargo Compatible**: Flat structure works with Cargo's test discovery
3. **Scalable**: Easy to add new tests in appropriate categories
4. **Clear Intent**: Descriptive names make test purpose obvious
5. **IDE Friendly**: Most IDEs group files by prefix automatically

## Test Statistics

- **Total Test Files**: ~36
- **Command Tests**: 17 files in `tests/commands/`
- **Integration Tests**: 19 files in `tests/` root
- **Test Coverage**: >90% (as per project standards)

## Related Documentation

- `tests/README_PERSISTENCE_TESTS.md` - Persistence test details
- `tests/README_MOBILE_FFI_TESTS.md` - Mobile FFI test details
- `tests/README_ANDROID_AR_TESTS.md` - Android AR test details
- `tests/TEST_COVERAGE_SUMMARY.md` - Overall test coverage summary
- `tests/IMPLEMENTATION_SUMMARY.md` - Implementation details

