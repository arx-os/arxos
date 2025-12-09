# ArxOS Test Suite

## Overview

The test suite contains **52 integration and unit test files** organized by feature category. Tests are written in Rust and use the standard `cargo test` framework.

## Directory Structure

```
tests/
├── bin/                   # Binary-specific tests (1 file)
├── commands/              # CLI command tests (27 files)
├── downstream/            # Downstream validation tests (1 file)
├── e2e/                   # End-to-end workflow tests (2 files)
├── examples/              # Example validation tests (1 file)
├── fixtures/              # Test data and golden files
│   ├── golden/           # Expected output samples
│   └── ifc/              # Sample IFC files
├── git/                   # Git workflow tests (1 file)
├── hardware/              # Hardware sensor tests (3 files)
├── ifc/                   # IFC processing tests (4 files)
├── persistence/           # Data persistence tests (1 file)
├── render3d/              # 3D rendering tests (1 file)
├── spreadsheet/           # Spreadsheet TUI tests (5 files)
├── tui/                   # Terminal UI tests (6 files)
├── ui/                    # UI component tests (1 file)
└── Root level             # Core integration tests (4 files)
```

## Test Categories

### Command Tests (`commands/`)
Unit tests for CLI commands (27 files):
- `address_integration_tests.rs` - ArxAddress system
- `config_tests.rs` - Configuration management
- `doc_tests.rs` - Documentation generation
- `equipment_tests.rs` - Equipment CRUD operations
- `export_tests.rs` - Export functionality
- `git_ops_tests.rs` - Git operations
- `ifc_tests.rs` - IFC import/export
- `import_tests.rs` - Data import
- `interactive_tests.rs` - Interactive mode
- `migrate_tests.rs` - Data migration
- `query_tests.rs` - Query engine
- `render_tests.rs` - 3D rendering
- `room_tests.rs` - Room management
- `search_tests.rs` - Search functionality
- `sensors_tests.rs` - Sensor data handling
- `spatial_tests.rs` - Spatial operations
- `validate_tests.rs` - Validation
- `watch_tests.rs` - File watching
- `wing_tests.rs` - Building wing management
- And more...

### E2E Tests (`e2e/`)
End-to-end workflow tests:
- `e2e_workflow_tests.rs` - Complete workflows
- `e2e_command_integration_tests.rs` - Command integration

### Hardware Tests (`hardware/`)
Hardware sensor integration:
- `hardware_integration_tests.rs` - Core hardware integration
- `hardware_http_integration_tests.rs` - HTTP sensor endpoints
- `hardware_workflow_tests.rs` - Hardware workflows

### IFC Tests (`ifc/`)
IFC file processing:
- `ifc_golden_tests.rs` - Golden file validation
- `ifc_rs_integration_tests.rs` - ifc-rs library integration
- `ifc_sync_integration_tests.rs` - Bidirectional IFC sync
- `ifc_workflow_tests.rs` - IFC workflows

### Persistence Tests (`persistence/`)
Data persistence and Git integration:
- `persistence_tests.rs` - Save/load operations, Git workflows

### Spreadsheet Tests (`spreadsheet/`)
Spreadsheet TUI component tests:
- `spreadsheet_component_integration_tests.rs` - Component interactions
- `spreadsheet_data_source_integration_tests.rs` - Data source workflows
- `spreadsheet_filesystem_integration_tests.rs` - File operations
- `spreadsheet_command_integration_tests.rs` - CLI command handlers
- `spreadsheet_ar_integration_tests.rs` - AR integration

### TUI Tests (`tui/`)
Terminal user interface tests:
- `tui_workflow_integration_tests.rs` - TUI workflows
- `tui_component_interaction_tests.rs` - Component interactions
- `tui_event_flow_tests.rs` - Event handling
- `tui_terminal_integration_tests.rs` - Terminal manager
- `users_browser_integration_tests.rs` - User browser UI
- `test_utils.rs` - Shared test utilities

### Root Level Tests
Core integration tests:
- `config_validation_tests.rs` - Configuration validation
- `ifc_extruded_solid_test.rs` - IFC geometry processing
- `ifc_integration_test.rs` - IFC integration
- `property_based_tests.rs` - Property-based testing
- `security_tests.rs` - Security validation

## Running Tests

### Run All Tests
```bash
cargo test
```

### Run Tests by Category
```bash
# Command tests
cargo test --test equipment_tests
cargo test --test ifc_tests

# E2E tests
cargo test --test e2e_workflow_tests

# Hardware tests
cargo test --test hardware_integration_tests

# IFC tests
cargo test --test ifc_workflow_tests

# Persistence tests
cargo test --test persistence_tests

# Spreadsheet tests
cargo test --test spreadsheet_component_integration_tests

# TUI tests
cargo test --test tui_workflow_integration_tests

# Security tests
cargo test --test security_tests
```

### Run Specific Test Function
```bash
cargo test --test <test_file> <test_function_name>

# Example:
cargo test --test equipment_tests test_equipment_add
```

### Run Tests with Output
```bash
cargo test -- --nocapture
```

### Run Tests in Parallel/Serial
Most tests run in parallel. Tests that modify shared state use `#[serial]` attribute to run sequentially.

## Test Patterns

### Test Isolation
Tests use several patterns for isolation:

**DirectoryGuard Pattern**
```rust
struct DirectoryGuard {
    original_dir: PathBuf,
}

impl DirectoryGuard {
    fn new(test_dir: &Path) -> Result<Self> {
        let original_dir = std::env::current_dir()?;
        std::env::set_current_dir(test_dir)?;
        Ok(Self { original_dir })
    }
}

impl Drop for DirectoryGuard {
    fn drop(&mut self) {
        let _ = std::env::set_current_dir(&self.original_dir);
    }
}
```

**Temporary Directories**
```rust
use tempfile::TempDir;

let temp_dir = TempDir::new()?;
let _guard = DirectoryGuard::new(temp_dir.path())?;
// Test code here - directory automatically cleaned up
```

**Serial Execution**
```rust
use serial_test::serial;

#[test]
#[serial]
fn test_modifies_global_state() {
    // This test runs serially with other #[serial] tests
}
```

### Test Fixtures
Test data is stored in `tests/fixtures/`:
- `fixtures/golden/` - Expected output samples (YAML, JSON)
- `fixtures/ifc/` - Sample IFC files for testing

### Shared Utilities
- `tests/tui/test_utils.rs` - Helper functions for TUI testing

## Adding New Tests

### Integration Test
Create a new file in the appropriate category directory:

```rust
// tests/commands/mynewcommand_tests.rs

use arxos::cli::commands::mynewcommand;

#[test]
fn test_mynewcommand_basic() {
    // Test code
}
```

### Command Test
For new CLI commands, add tests in `tests/commands/`:
1. Create `<command>_tests.rs`
2. Test command parsing, validation, execution
3. Test error handling

### Category Test
For new feature categories, create a new subdirectory:
1. Create `tests/mynewfeature/`
2. Add test files following naming pattern: `<feature>_<type>_tests.rs`
3. Register in `Cargo.toml` if needed

## Test Coverage

Tests cover:
- ✅ CLI command parsing and execution
- ✅ Data persistence (YAML, Git)
- ✅ IFC import/export
- ✅ ArxAddress system and query engine
- ✅ Hardware sensor integration
- ✅ Spreadsheet TUI components
- ✅ Terminal UI workflows
- ✅ Security validation
- ✅ Configuration management

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Release builds

## Troubleshooting

### Test Fails with Directory Errors
Ensure test uses `DirectoryGuard` and `TempDir` for isolation.

### Test Hangs
Check for missing `#[serial]` attribute if test modifies global state.

### Test Fixtures Missing
Ensure `tests/fixtures/` directory is present with required files.

## Notes

- **Removed outdated tests**: AR integration tests and disabled tests were removed as they referenced non-existent modules (`arxos::ar_integration`, `arxos::game` not exposed in lib)
- **Crate name**: All tests use `arxos::` (the library crate name), not `arxui`
- **Test count**: 52 test files (down from 63 after removing tests for unimplemented features)
