# Test Organization

**Last Updated:** January 2025

## Overview

This directory contains all integration tests for ArxOS. Tests are organized by feature category in subdirectories for better organization and scalability.

## Test Organization Strategy

Tests are organized in **subdirectories by category**. Each subdirectory contains related integration tests. Tests in subdirectories are explicitly registered in `Cargo.toml` using `[[test]]` entries to ensure Cargo can discover them.

### Test Categories

#### AR Tests (`tests/ar/`)
AR integration and workflow tests:
- `ar_complete_workflow_test.rs` - Complete AR workflow end-to-end
- `ar_gltf_integration_tests.rs` - glTF export integration tests
- `ar_usdz_integration_tests.rs` - USDZ export integration tests
- `ar_workflow_integration_test.rs` - AR workflow integration
- `ar_ios_workflow_integration_tests.rs` - iOS AR workflow integration
- `ar_json_helpers_tests.rs` - AR JSON parsing helper tests

#### Mobile/FFI Tests (`tests/mobile/`)
Mobile FFI and cross-platform tests:
- `mobile_ffi_tests.rs` - Core FFI function tests (JNI, iOS, error handling)

#### Hardware Tests (`tests/hardware/`)
Hardware sensor integration tests:
- `hardware_integration_tests.rs` - Core hardware integration
- `hardware_http_integration_tests.rs` - HTTP sensor integration
- `hardware_workflow_tests.rs` - Hardware workflow tests

#### Persistence Tests (`tests/persistence/`)
Data persistence and Git integration tests:
- `persistence_tests.rs` - Building data persistence, save/load, Git operations

#### E2E Tests (`tests/e2e/`)
End-to-end workflow tests:
- `e2e_workflow_tests.rs` - Complete end-to-end workflows
- `e2e_command_integration_tests.rs` - Command integration tests

#### IFC Tests (`tests/ifc/`)
IFC file processing tests:
- `ifc_workflow_tests.rs` - IFC processing workflows
- `ifc_sync_integration_tests.rs` - IFC bidirectional sync

#### TUI Tests (`tests/tui/`)
Terminal User Interface integration tests:
- `tui_workflow_integration_tests.rs` - Complete TUI workflows
- `tui_component_interaction_tests.rs` - Component interaction tests
- `tui_event_flow_tests.rs` - Event flow and propagation tests
- `tui_terminal_integration_tests.rs` - Terminal manager integration
- `test_utils.rs` - Shared test utilities and helpers

#### Spreadsheet Tests (`tests/spreadsheet/`) ⭐ NEW
Spreadsheet TUI integration tests:
- `spreadsheet_component_integration_tests.rs` - Component interaction tests (Grid + Editor + Validation)
- `spreadsheet_data_source_integration_tests.rs` - Data source workflow tests (Load → Edit → Save → Reload)
- `spreadsheet_filesystem_integration_tests.rs` - File system operations (YAML persistence, Git, file locking)
- `spreadsheet_command_integration_tests.rs` - CLI command handler integration tests

#### Command Tests (`tests/commands/`)
Unit tests for individual command handlers:
- Located in `tests/commands/` subdirectory
- One test file per command module
- See `tests/commands/README.md` for details

#### Other Tests (Root Level)
Tests that don't fit into specific categories:
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
cargo test --test ar_workflow_integration_test
cargo test --test ar_complete_workflow_test
# etc.

# Mobile/FFI tests
cargo test --test mobile_ffi_tests

# Hardware tests
cargo test --test hardware_integration_tests
cargo test --test hardware_http_integration_tests
cargo test --test hardware_workflow_tests

# Persistence tests
cargo test --test persistence_tests

# E2E tests
cargo test --test e2e_workflow_tests
cargo test --test e2e_command_integration_tests

# IFC tests
cargo test --test ifc_workflow_tests
cargo test --test ifc_sync_integration_tests

# TUI tests
cargo test --test tui_workflow_integration_tests
cargo test --test tui_component_interaction_tests
cargo test --test tui_event_flow_tests
cargo test --test tui_terminal_integration_tests

# Spreadsheet tests
cargo test --test spreadsheet_component_integration_tests
cargo test --test spreadsheet_data_source_integration_tests
cargo test --test spreadsheet_filesystem_integration_tests
cargo test --test spreadsheet_command_integration_tests
```

### Run All Tests in a Category
```bash
# Run all AR tests
cargo test --test ar_

# Run all hardware tests  
cargo test --test hardware_

# Run all TUI tests
cargo test --test tui_

# Run all spreadsheet tests
cargo test --test spreadsheet_
```

### Run Command Tests
```bash
cargo test --test commands/ar_tests
cargo test --test commands/export_tests
# etc.
```

## Test File Naming Convention

Tests use the following naming pattern:
- **Category subdirectory** (e.g., `ar/`, `mobile/`, `hardware/`, `tui/`)
- **Feature name** (e.g., `workflow`, `integration`, `component`)
- **Test type suffix** (e.g., `_tests.rs`, `_test.rs`)

Examples:
- `tests/ar/ar_workflow_integration_test.rs` - AR workflow integration test
- `tests/mobile/mobile_ffi_tests.rs` - Mobile FFI tests
- `tests/hardware/hardware_http_integration_tests.rs` - Hardware HTTP integration tests
- `tests/tui/tui_workflow_integration_tests.rs` - TUI workflow integration tests
- `tests/spreadsheet/spreadsheet_component_integration_tests.rs` - Spreadsheet component integration tests

## Benefits of This Organization

1. **Easy Discovery**: Files grouped in subdirectories make it easy to find related tests
2. **Cargo Compatible**: Tests registered in `Cargo.toml` ensure Cargo can discover them
3. **Scalable**: Easy to add new tests in appropriate subdirectories
4. **Clear Intent**: Directory structure and descriptive names make test purpose obvious
5. **IDE Friendly**: Most IDEs group files by directory automatically
6. **Better Organization**: Subdirectories prevent test directory from becoming cluttered

## Test Statistics

- **Total Test Files**: 45 Rust test files
- **AR Tests**: 6 files in `tests/ar/`
- **Command Tests**: 17 files in `tests/commands/`
- **Mobile Tests**: 1 file in `tests/mobile/`
- **Hardware Tests**: 3 files in `tests/hardware/`
- **E2E Tests**: 2 files in `tests/e2e/`
- **IFC Tests**: 2 files in `tests/ifc/`
- **Persistence Tests**: 1 file in `tests/persistence/`
- **TUI Tests**: 5 files in `tests/tui/` (including `test_utils.rs`)
- **Spreadsheet Tests**: 4 files in `tests/spreadsheet/` ⭐ NEW
- **Other Tests**: 4 files in `tests/` root
- **Test Coverage**: >90% (as per project standards)

## Related Documentation

- `tests/README_PERSISTENCE_TESTS.md` - Persistence test details
- `tests/README_MOBILE_FFI_TESTS.md` - Mobile FFI test details
- `tests/README_ANDROID_AR_TESTS.md` - Android AR test details
- `tests/TEST_COVERAGE_SUMMARY.md` - Overall test coverage summary
- `tests/IMPLEMENTATION_SUMMARY.md` - Implementation details
- `tests/TESTS_DIRECTORY_REVIEW.md` - Structure review and best practices

