# Testing

Running tests and benchmarks for ArxOS.

---

## Overview

ArxOS uses Rust's built-in testing framework with:

- **Unit tests** – Test individual functions and modules
- **Integration tests** – Test complete workflows
- **Benchmarks** – Performance measurements
- **Test fixtures** – Sample data in `test_data/`

---

## Running Tests

### All Tests

```bash
# Run all tests
cargo test

# With all features
cargo test --all-features

# Release mode (faster)
cargo test --release
```

### Specific Tests

```bash
# Test a specific module
cargo test git::

# Test a specific function
cargo test test_building_creation

# Test with pattern
cargo test ifc_*
```

### Integration Tests

```bash
# Run only integration tests
cargo test --test '*'

# Specific integration test
cargo test --test ifc_integration_test
```

---

## Test Structure

### Unit Tests

Located in the same file as the code:

```rust
// src/core/building.rs

pub fn create_building(name: &str) -> Building {
    Building::new(name)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_building_creation() {
        let building = create_building("Test");
        assert_eq!(building.name, "Test");
    }

    #[test]
    fn test_building_has_id() {
        let building = create_building("Test");
        assert!(!building.id.is_empty());
    }
}
```

### Integration Tests

Located in `tests/` directory:

```rust
// tests/ifc_integration_test.rs

use arxos::ifc::IfcParser;

#[test]
fn test_import_complete_building() {
    let parser = IfcParser::new("test_data/sample_building.ifc")
        .expect("Failed to create parser");
    
    let building = parser.parse()
        .expect("Failed to parse IFC");
    
    assert!(building.floors.len() > 0);
    assert!(building.name.len() > 0);
}
```

---

## Test Data

### Test Fixtures

Located in `test_data/`:

```
test_data/
├── sample_building.ifc        # Sample IFC file
├── Building-Architecture.ifc  # Architecture model
├── Building-Hvac.ifc          # HVAC model
├── test_building.yaml         # Sample YAML data
├── sample-ar-scan.json        # AR scan data
└── sensor-data/
    └── sample-sensor.json     # Sensor data
```

### Using Test Fixtures

```rust
#[test]
fn test_with_fixture() {
    let ifc_path = "test_data/sample_building.ifc";
    let parser = IfcParser::new(ifc_path).unwrap();
    let building = parser.parse().unwrap();
    
    // Assertions
    assert!(building.floors.len() > 0);
}
```

---

## Feature-Gated Tests

### TUI Tests

```bash
# Run TUI tests
cargo test --features tui

# Specific TUI test
cargo test --features tui test_dashboard
```

### Render3D Tests

```bash
# Run render3d tests
cargo test --features render3d

# Specific render test
cargo test --features render3d test_point_cloud
```

### All Features

```bash
# Test with all features enabled
cargo test --all-features
```

---

## Test Output

### Verbose Output

```bash
# Show println! output
cargo test -- --nocapture

# Show test names
cargo test -- --show-output

# Both
cargo test -- --nocapture --show-output
```

### Parallel Execution

```bash
# Run tests in parallel (default)
cargo test

# Run tests serially
cargo test -- --test-threads=1
```

---

## Benchmarks

### Running Benchmarks

```bash
# Run all benchmarks
cargo bench

# Specific benchmark
cargo bench bench_ifc_parsing

# Save baseline
cargo bench --bench core_benchmarks -- --save-baseline main
```

### Benchmark Structure

Located in `benches/`:

```rust
// benches/core_benchmarks.rs

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use arxos::ifc::IfcParser;

fn bench_ifc_parsing(c: &mut Criterion) {
    c.bench_function("parse_ifc", |b| {
        b.iter(|| {
            let parser = IfcParser::new("test_data/sample_building.ifc")
                .unwrap();
            black_box(parser.parse().unwrap())
        });
    });
}

criterion_group!(benches, bench_ifc_parsing);
criterion_main!(benches);
```

### Compare Baselines

```bash
# Save baseline before changes
cargo bench -- --save-baseline before

# Make changes to code

# Compare with baseline
cargo bench -- --baseline before
```

---

## Code Coverage

### Install Tarpaulin

```bash
cargo install cargo-tarpaulin
```

### Generate Coverage

```bash
# Generate coverage report
cargo tarpaulin --all-features --out Html

# Opens tarpaulin-report.html in browser
```

### CI Coverage

```bash
# Generate coverage for CI
cargo tarpaulin --all-features --out Xml

# Uploads to codecov/coveralls
```

---

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
      
      - name: Run tests
        run: cargo test --all-features
      
      - name: Run benchmarks (check only)
        run: cargo bench --no-run
```

---

## Test Best Practices

### Use Descriptive Names

```rust
#[test]
fn test_import_creates_valid_building_structure() {
    // Test implementation
}

#[test]
fn test_equipment_validation_rejects_invalid_types() {
    // Test implementation
}
```

### Test Edge Cases

```rust
#[test]
fn test_empty_building() {
    let building = Building::new("Empty");
    assert_eq!(building.floors.len(), 0);
}

#[test]
fn test_building_with_negative_floor_numbers() {
    let mut building = Building::new("Test");
    building.add_floor(-1, "Basement");
    assert_eq!(building.floors[0].number, -1);
}
```

### Use Assertions Effectively

```rust
#[test]
fn test_building_properties() {
    let building = create_test_building();
    
    // Specific assertions
    assert_eq!(building.name, "Test Building");
    assert!(building.id.len() > 0);
    assert!(building.floors.len() >= 1);
    
    // Pattern matching
    assert!(matches!(building.status, BuildingStatus::Active));
}
```

---

## Property-Based Testing

### Install PropTest

```toml
[dev-dependencies]
proptest = "1.0"
```

### Property Tests

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_building_name_roundtrip(name in "\\PC+") {
        let building = Building::new(&name);
        prop_assert_eq!(building.name, name);
    }
    
    #[test]
    fn test_floor_number_valid(num in -100i32..100i32) {
        let floor = Floor::new(num);
        prop_assert_eq!(floor.number, num);
    }
}
```

---

## Mock Objects

### Using Test Doubles

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    struct MockGitManager {
        commits: Vec<String>,
    }
    
    impl GitOperations for MockGitManager {
        fn commit(&mut self, msg: &str) -> Result<(), Error> {
            self.commits.push(msg.to_string());
            Ok(())
        }
    }
    
    #[test]
    fn test_with_mock() {
        let mut mock = MockGitManager { commits: vec![] };
        mock.commit("Test commit").unwrap();
        assert_eq!(mock.commits.len(), 1);
    }
}
```

---

## Test Utilities

### Temporary Directories

```rust
use tempfile::TempDir;

#[test]
fn test_with_temp_dir() {
    let temp_dir = TempDir::new().unwrap();
    let building_path = temp_dir.path().join("building.yaml");
    
    // Test code that writes files
    
    // temp_dir automatically cleaned up
}
```

### Test Helpers

```rust
// tests/common/mod.rs

pub fn create_test_building() -> Building {
    let mut building = Building::new("Test Building");
    building.add_floor(1, "Ground Floor");
    building
}

pub fn create_test_equipment() -> Equipment {
    Equipment::new("TEST-001", "HVAC")
}
```

**Usage:**
```rust
mod common;

#[test]
fn test_something() {
    let building = common::create_test_building();
    // Use building
}
```

---

## Debugging Tests

### Run Single Test with Debug Info

```bash
# Enable debug logging
RUST_LOG=debug cargo test test_name -- --nocapture

# With backtraces
RUST_BACKTRACE=1 cargo test test_name
```

### Use dbg! Macro

```rust
#[test]
fn test_debug() {
    let building = create_building();
    dbg!(&building.name);     // Prints to stderr
    dbg!(&building.floors);
    
    assert!(building.floors.len() > 0);
}
```

---

## Performance Testing

### Measure Test Duration

```bash
# Time each test
cargo test -- --show-output --test-threads=1

# Shows:
# test test_ifc_parsing ... ok (15.2s)
# test test_git_commit ... ok (0.5s)
```

### Identify Slow Tests

```bash
# Run with time limit
cargo test -- --test-threads=1 | grep "ok (" | sort -k3 -n
```

---

## Test Documentation

### Document Test Intent

```rust
/// Tests that IFC import correctly handles multi-floor buildings
/// with complex equipment hierarchies.
#[test]
fn test_ifc_import_multi_floor_complex() {
    // Test implementation
}

/// Verifies that equipment validation rejects invalid equipment types
/// according to the schema defined in src/core/equipment.rs.
#[test]
fn test_equipment_validation_rejects_invalid_types() {
    // Test implementation
}
```

---

## Troubleshooting

### Test Failures

**Failed assertion:**
```bash
# Run with backtrace
RUST_BACKTRACE=1 cargo test failing_test

# Run with verbose output
cargo test failing_test -- --nocapture
```

**Timeout:**
```bash
# Increase timeout
cargo test -- --test-threads=1 --nocapture
```

**Flaky tests:**
```bash
# Run multiple times
for i in {1..10}; do cargo test flaky_test || break; done
```

---

## Quick Reference

```bash
# All tests
cargo test

# With features
cargo test --all-features

# Integration tests
cargo test --test '*'

# Benchmarks
cargo bench

# Coverage
cargo tarpaulin --all-features

# Single test
cargo test test_name -- --nocapture

# Documentation tests
cargo test --doc
```

---

**See Also:**
- [Building Guide](./building.md) – Build instructions
- [Contributing Guide](./contributing.md) – Contribution workflow
- [Architecture](../architecture.md) – System design
