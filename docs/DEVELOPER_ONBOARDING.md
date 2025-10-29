# Developer Onboarding Guide

**ArxOS - Git for Buildings**  
**Version:** 2.0  
**Last Updated:** January 2025

---

## Welcome to ArxOS Development

This guide will help you get started developing ArxOS, a terminal-first building management system built in Rust with Git-native data storage.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting Started](#getting-started)
3. [Code Structure](#code-structure)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Common Patterns](#common-patterns)
7. [Module Documentation](#module-documentation)
8. [Best Practices](#best-practices)

---

## Prerequisites

### Required Software

- **Rust**: Latest stable version (1.70+)
  - Install from: https://rustup.rs/
  - Verify: `rustc --version`

- **Git**: Version control
  - Verify: `git --version`

- **Development Tools**:
  - `cargo` (comes with Rust)
  - `clippy` (rust linter): `rustup component add clippy`
  - `rustfmt` (code formatter): `rustup component add rustfmt`

### Optional Tools

- **Rust IDE**: VSCode with rust-analyzer extension (recommended)
- **Git GUI**: For Git operations and history viewing
- **Terminal**: Modern terminal (iTerm2 on macOS, Windows Terminal)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
```

### 2. Build the Project

```bash
# Build in debug mode (faster iteration)
cargo build

# Build in release mode (optimized)
cargo build --release
```

### 3. Run Tests

```bash
# Run all tests
cargo test

# Run specific test suite
cargo test ar_workflow

# Run with output
cargo test -- --nocapture
```

### 4. Run the CLI

```bash
# Help
cargo run -- --help

# Example: List commands
cargo run -- import --help
```

---

## Code Structure

### High-Level Architecture

```
arxos/
├── src/                          # Main Rust source code
│   ├── main.rs                   # CLI entry point
│   ├── lib.rs                    # Library API (for tests/FFI)
│   ├── commands/                 # Command handlers (16 modules)
│   │   ├── mod.rs               # Command router
│   │   ├── import.rs            # IFC import
│   │   ├── equipment.rs         # Equipment CRUD
│   │   └── [other commands]     # Additional handlers
│   ├── core/                     # Core business logic
│   │   ├── building.rs          # Building data structure
│   │   ├── equipment.rs         # Equipment types
│   │   └── room.rs              # Room types
│   ├── ifc/                      # IFC file processing
│   ├── render3d/                 # 3D rendering engine
│   ├── mobile_ffi/               # FFI bindings for iOS/Android
│   ├── git/                      # Git integration
│   ├── persistence/              # Data persistence layer
│   └── [other modules]/          # Additional functionality
├── tests/                        # Integration tests
├── docs/                         # Documentation
├── ios/                          # iOS mobile app
├── android/                      # Android mobile app
└── Cargo.toml                    # Rust dependencies
```

### Key Module Responsibilities

| Module | Purpose | Key Types |
|--------|---------|-----------|
| `commands/` | CLI command handlers | Command handlers |
| `core/` | Business logic | `Building`, `Equipment`, `Room` |
| `ifc/` | IFC file parsing | `IFCProcessor`, `EnhancedIFCParser` |
| `render3d/` | 3D visualization | `Building3DRenderer`, `InteractiveRenderer` |
| `mobile_ffi/` | Mobile app integration | FFI functions, Swift/Kotlin wrappers |
| `git/` | Git operations | `BuildingGitManager` |
| `persistence/` | Data storage | `PersistenceManager` |
| `ar_integration/` | AR scan processing | `PendingEquipmentManager` |

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-feature-name
```

### 2. Make Changes

Follow ArxOS conventions:
- **Command handlers**: Place in `src/commands/`
- **Core types**: Add to `src/core/`
- **New module**: Create in `src/` with proper `mod.rs`
- **Tests**: Add integration tests in `tests/`

### 3. Run Tests

```bash
# Before committing, ensure all tests pass
cargo test

# Format code
cargo fmt

# Lint code
cargo clippy
```

### 4. Commit Changes

ArxOS follows conventional commits:

```bash
# Format: <type>(<scope>): <description>

# Examples:
git commit -m "feat(equipment): add status filter command"
git commit -m "fix(ar): fix pending equipment storage path"
git commit -m "docs(ar_integration): add module documentation"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/config changes

### 5. Push and Create PR

```bash
git push origin feature/my-feature-name
```

Create a pull request on GitHub with:
- Clear description of changes
- Reference to related issues
- Screenshots/demo if applicable

---

## Testing

### Test Structure

ArxOS uses a comprehensive test strategy:

1. **Unit Tests**: Within each module (`#[cfg(test)]`)
2. **Integration Tests**: In `tests/` directory
3. **Command Tests**: Test CLI commands end-to-end
4. **Workflow Tests**: Test complete workflows

### Running Tests

```bash
# All tests
cargo test

# Specific test file
cargo test ar_workflow_integration_test

# Specific test function
cargo test test_ar_workflow_complete

# Tests in a module
cargo test --lib core

# With output
cargo test -- --nocapture
```

### Writing Tests

Example integration test:

```rust
use arxos::core::{Building, Equipment};
use arxos::persistence::PersistenceManager;

#[test]
fn test_equipment_persistence() {
    // Arrange
    let mut building = create_test_building();
    
    // Act
    building.add_equipment(Equipment::new("HVAC-001", "VAV"))?;
    
    // Assert
    assert_eq!(building.equipment.len(), 1);
}
```

---

## Common Patterns

### 1. Command Handler Pattern

```rust
// src/commands/my_command.rs
use crate::cli::MyCommand;
use crate::persistence::PersistenceManager;

pub fn handle_my_command(cmd: MyCommand) -> Result<(), Box<dyn std::error::Error>> {
    // Load building data
    let persistence = PersistenceManager::new(&cmd.building)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Perform operation
    // ... your logic ...
    
    // Save changes
    persistence.save_building_data(&building_data)?;
    
    Ok(())
}
```

### 2. Error Handling Pattern

```rust
// Use ? operator for error propagation
let result = risky_operation()?;

// Return Box<dyn std::error::Error> from handlers
pub fn my_function() -> Result<(), Box<dyn std::error::Error>> {
    let data = std::fs::read_to_string("file.txt")?;
    Ok(())
}

// Never use unwrap() in production code
// Bad: let value = input.parse().unwrap();
// Good: let value = input.parse()
//         .map_err(|e| format!("Failed to parse: {}", e))?;
```

### 3. Git Integration Pattern

```rust
use crate::git::BuildingGitManager;

let git_manager = BuildingGitManager::new(&path)?;

// Stage changes
git_manager.stage_file(&file_path)?;

// Commit changes
git_manager.commit("Add equipment", "user@example.com")?;
```

### 4. Path Safety Pattern

```rust
use crate::utils::path_safety::PathSafety;

let base_dir = std::env::current_dir()?;
let validated_path = PathSafety::canonicalize_and_validate(
    &Path::new(user_input),
    &base_dir
)?;

// Use validated_path for file operations
```

---

## Module Documentation

### Documenting Modules

All modules should have:
1. **Module doc comment**: Overview and purpose
2. **Usage examples**: Example code snippets
3. **Public API docs**: Document exported types and functions

Example:

```rust
//! AR/LiDAR Data Integration for ArxOS
//!
//! This module handles the integration of AR and LiDAR scan data from mobile applications
//! into the building data structure, enabling real-time updates to the 3D renderer.
//!
//! # Usage Examples
//!
//! ```rust,no_run
//! use arxos::ar_integration::PendingEquipmentManager;
//!
//! let mut manager = PendingEquipmentManager::new("my_building".to_string());
//! // ... use manager ...
//! ```
```

### Generating Documentation

```bash
# Build docs
cargo doc --open

# Build docs for all features
cargo doc --all-features --open
```

---

## Best Practices

### 1. Rust Best Practices

- ✅ Use `Result<T>` for error handling
- ✅ Use `?` operator for error propagation
- ✅ Avoid `unwrap()` in production code
- ✅ Use `Option<T>` for nullable values
- ✅ Use references instead of cloning when possible
- ✅ Use `cargo clippy` before committing

### 2. ArxOS-Specific Practices

- ✅ All data changes must go through Git
- ✅ Use `PersistenceManager` for file operations
- ✅ Use path safety utilities for user input
- ✅ Return `Box<dyn std::error::Error>` from command handlers
- ✅ Add integration tests for new commands
- ✅ Follow existing code structure and patterns

### 3. Git Best Practices

- ✅ Use conventional commit messages
- ✅ Create feature branches for new work
- ✅ Keep commits focused and atomic
- ✅ Reference issues in commit messages
- ✅ Write clear PR descriptions

### 4. Testing Best Practices

- ✅ Write tests before implementing features (TDD)
- ✅ Test both happy path and error cases
- ✅ Use meaningful test names
- ✅ Keep tests focused and independent
- ✅ Clean up test data (use `TempDir`)

---

## Getting Help

### Resources

- **Documentation**: `docs/` directory
- **Architecture**: `docs/ARCHITECTURE.md`
- **User Guide**: `docs/USER_GUIDE.md`
- **Code Examples**: Look at existing command handlers

### Community

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions
- **Code Review**: Submit PRs for review

### Common Questions

**Q: How do I add a new command?**  
A: Create a handler in `src/commands/`, add CLI definition in `src/cli/mod.rs`, and route in `src/commands/mod.rs`.

**Q: How do I integrate with mobile apps?**  
A: Add FFI functions in `src/mobile_ffi/ffi.rs` and update Swift/Kotlin wrappers.

**Q: How do I add a new module?**  
A: Create directory in `src/` with `mod.rs`, add module declaration in parent `mod.rs`.

**Q: How do I test Git operations?**  
A: Use `tempfile::TempDir` to create temporary repos for testing.

---

## Next Steps

1. Explore the codebase: Read existing command handlers
2. Run the app: Try different commands
3. Pick an issue: Start with "good first issue" labeled tasks
4. Join the community: Participate in discussions and PRs

---

**Welcome to ArxOS! Happy coding! 🚀**

