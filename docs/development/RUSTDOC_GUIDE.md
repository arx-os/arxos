# Rustdoc Documentation Guide

## What is rustdoc?

**rustdoc** is Rust's built-in documentation tool that generates HTML documentation directly from your source code. It reads special Markdown comments in your Rust files and produces beautiful, navigable, searchable HTML documentation.

### Purpose

1. **API Documentation**: Auto-generates documentation for all public APIs (functions, structs, enums, traits, modules)
2. **Code Examples**: Executes and tests code examples embedded in documentation
3. **Developer Experience**: Provides IDE integration (hover tooltips, search)
4. **Discoverability**: Makes your crate's API easy to explore and understand

### Key Benefits

- ✅ **Always in sync**: Documentation lives with code
- ✅ **Executable examples**: Code examples in docs are tested
- ✅ **Searchable**: Built-in search functionality
- ✅ **IDE integration**: Hover docs, go-to-definition
- ✅ **Standard format**: Consistent across all Rust projects

---

## How rustdoc Works

### Documentation Comment Syntax

rustdoc uses special comment syntax to extract documentation:

#### Outer Documentation (`///`)

Documents the item that follows:

```rust
/// Represents a building in ArxOS
///
/// The `Building` struct is the root entity in the ArxOS hierarchy:
/// Building → Floor → Wing → Room → Equipment
///
/// # Examples
///
/// ```
/// use arxos::core::Building;
///
/// let building = Building::new("Main Building".to_string(), "main".to_string());
/// assert_eq!(building.name, "Main Building");
/// ```
#[derive(Debug, Clone)]
pub struct Building {
    /// Unique identifier for the building
    pub id: String,
    /// Human-readable building name
    pub name: String,
}
```

#### Inner Documentation (`//!`)

Documents the enclosing item (module or crate):

```rust
//! Core data structures for ArxOS
//!
//! This module provides the foundational data structures and business logic
//! for representing buildings, floors, rooms, equipment, and their spatial relationships.
//!
//! # Overview
//!
//! The core module defines the hierarchy:
//! - `Building` - Root entity
//! - `Floor` - Building floors
//! - `Wing` - Floor wings
//! - `Room` - Rooms in wings
//! - `Equipment` - Equipment in rooms

pub mod building;
pub mod room;
```

---

### Markdown Support

rustdoc comments support full Markdown:

```rust
/// Creates a new room with the specified properties.
///
/// # Arguments
///
/// * `name` - Room name (required)
/// * `room_type` - Type of room (see [`RoomType`])
/// * `dimensions` - Optional dimensions as "width x depth x height"
///
/// # Returns
///
/// Returns the created room ID on success, or an error if:
/// - Room name is invalid
/// - Dimensions cannot be parsed
/// - Parent floor/wing not found
///
/// # Examples
///
/// ## Basic usage
///
/// ```no_run
/// use arxos::core::{Room, RoomType};
///
/// let room = create_room(
///     "Conference Room 201".to_string(),
///     RoomType::Office,
///     None
/// )?;
/// ```
///
/// ## With dimensions
///
/// ```no_run
/// let room = create_room(
///     "Lab 101".to_string(),
///     RoomType::Laboratory,
///     Some("10x8x3".to_string())
/// )?;
/// ```
///
/// # Errors
///
/// This function will return an error if:
/// - The room name is empty
/// - The dimensions string cannot be parsed
/// - The parent floor/wing does not exist
///
/// # See Also
///
/// - [`RoomType`] - Room type enumeration
/// - [`update_room`] - Update existing room
pub fn create_room(...) -> Result<String, Error> {
    // ...
}
```

---

### Code Example Testing

Code examples in documentation are **tested** by default:

```rust
/// Add two numbers
///
/// # Examples
///
/// ```
/// # // Hidden setup code (not shown in docs)
/// let result = add(2, 3);
/// assert_eq!(result, 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

When you run `cargo test`, rustdoc will:
1. Extract code examples from documentation
2. Compile them as separate test binaries
3. Execute them and verify they pass

**Example Attributes:**

- `no_run` - Don't run the example, just compile it
- `ignore` - Skip this example
- `should_panic` - Example should panic
- `compile_fail` - Example should fail to compile

---

## Generating Documentation

### Basic Generation

```bash
# Generate documentation locally
cargo doc

# Generate and open in browser
cargo doc --open

# Generate for all dependencies too
cargo doc --all

# Generate without dependencies (faster)
cargo doc --no-deps
```

**Output Location:**
- Documentation is generated in `target/doc/`
- Main entry point: `target/doc/arxos/index.html`

### Documentation Features

```bash
# Enable all features
cargo doc --all-features

# Enable specific features
cargo doc --features android

# Keep dependency documentation
cargo doc --all

# Only document public APIs
cargo doc --document-private-items
```

---

## Proper Implementation

### 1. Document Public APIs

**All public items should have documentation:**

```rust
/// Error type for configuration operations
#[derive(Debug)]
pub enum ConfigError {
    /// Configuration file not found
    FileNotFound {
        /// Path to the missing file
        path: String,
    },
    /// Invalid configuration format
    InvalidFormat {
        /// Error message describing the issue
        message: String,
    },
}
```

### 2. Use Standard Sections

rustdoc recognizes special sections:

```rust
/// Process AR scan data from mobile devices
///
/// # Arguments
///
/// * `scan_data` - JSON string with AR scan data
///
/// # Returns
///
/// Parsed AR scan data structure
///
/// # Errors
///
/// Returns `InvalidData` error if:
/// - JSON is malformed
/// - Required fields are missing
/// - Data validation fails
///
/// # Examples
///
/// ```
/// use arxos::ar_integration::parse_ar_scan;
///
/// let json = r#"{"roomName": "Room 101", "floorLevel": 2}"#;
/// let scan = parse_ar_scan(json)?;
/// ```
///
/// # Panics
///
/// Never panics - all errors are returned as `Result`
///
/// # Safety
///
/// This function is safe to call with any valid UTF-8 string.
pub fn parse_ar_scan(scan_data: &str) -> Result<WasmArScanData, Error> {
    // ...
}
```

**Standard Sections:**
- `# Arguments` - Function parameters
- `# Returns` - Return value description
- `# Errors` - Error conditions
- `# Examples` - Usage examples
- `# Panics` - Panic conditions
- `# Safety` - Unsafe function requirements

### 3. Link Between Items

Use backticks to create links:

```rust
/// Get room by ID
///
/// Returns a [`Room`] struct with all details.
/// See also [`list_rooms`] to get all rooms.
pub fn get_room(id: &str) -> Option<Room> {
    // ...
}
```

Links work automatically for:
- Types in scope
- Functions in scope
- Modules

### 4. Document Modules

Every module should have documentation:

```rust
//! Mobile FFI interface for ArxOS
//! 
//! This module provides foreign function interface bindings for mobile applications.
//! The functions are designed to be called from iOS (Swift) and Android (Kotlin).
//!
//! # Overview
//!
//! The FFI module exports:
//! - C-compatible functions for iOS
//! - JNI functions for Android
//! - Data structures for cross-platform communication
//!
//! # Usage
//!
//! See [`ffi`] module for C FFI functions and [`jni`] module for JNI bindings.

pub mod ffi;
pub mod jni;
```

---

## Hosting Documentation

### Option 1: docs.rs (Recommended for Published Crates)

**docs.rs** automatically builds and hosts documentation for crates published to crates.io.

**Advantages:**
- ✅ Automatic - Builds on every publish
- ✅ Free hosting
- ✅ Always up-to-date
- ✅ Discoverable (searchable on docs.rs)
- ✅ Standard URL: `https://docs.rs/crate-name/version/`

**Setup:**

1. **Publish to crates.io** (requires account setup)

2. **Add to `Cargo.toml`**:

```toml
[package]
name = "arxos"
version = "0.1.0"

[package.metadata.docs.rs]
# Features to enable when building docs
features = ["android"]

# Additional rustdoc flags
rustdoc-args = ["--cfg", "docsrs"]
```

3. **Automatic**: docs.rs builds docs automatically on publish

**Note:** This only works if you publish to crates.io. If ArxOS is not published, use GitHub Pages instead.

---

### Option 2: GitHub Pages (Recommended for Private/Unpublished Projects)

**GitHub Pages** hosts static HTML files from your repository.

**Advantages:**
- ✅ Works for any repository (public or private with GitHub Pro)
- ✅ Custom domain support
- ✅ Free hosting
- ✅ Easy to set up with GitHub Actions

**Setup:**

1. **Create GitHub Actions Workflow** (`.github/workflows/docs.yml`):

```yaml
name: Build Documentation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      
      - name: Generate documentation
        run: cargo doc --no-deps --all-features
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        if: github.ref == 'refs/heads/main'
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./target/doc
          destination_dir: docs
```

2. **Enable GitHub Pages**:
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` (created by workflow)
   - Path: `/docs`

3. **Documentation URL**:
   - `https://username.github.io/arxos/docs/arxos/index.html`

---

### Option 3: Manual Hosting

You can host the generated HTML anywhere:

```bash
# Generate docs
cargo doc --no-deps

# Upload target/doc/ to your web server
scp -r target/doc/* user@server:/var/www/docs.arxos.com/
```

---

## Best Practices

### 1. Document Public APIs Comprehensively

```rust
// ❌ BAD: No documentation
pub fn process_data(data: String) -> Result<(), Error> {
    // ...
}

// ✅ GOOD: Comprehensive documentation
/// Process building data from YAML format.
///
/// Parses YAML input and validates building structure, converting
/// to internal representation.
///
/// # Arguments
///
/// * `data` - YAML string containing building data
///
/// # Returns
///
/// `Ok(())` if processing succeeds, `Err` if:
/// - YAML parsing fails
/// - Validation errors occur
/// - Required fields are missing
///
/// # Examples
///
/// ```
/// use arxos::yaml::process_building_data;
///
/// let yaml = r#"
/// building:
///   name: Main Building
/// "#;
/// process_building_data(yaml)?;
/// ```
pub fn process_data(data: String) -> Result<(), Error> {
    // ...
}
```

### 2. Include Examples

Always include at least one example:

```rust
/// Create a new equipment item
///
/// # Examples
///
/// ```
/// use arxos::core::{Equipment, EquipmentType};
///
/// let equipment = Equipment::new(
///     "VAV-301".to_string(),
///     "vav-301".to_string(),
///     EquipmentType::HVAC
/// );
/// ```
pub fn new(name: String, path: String, eq_type: EquipmentType) -> Self {
    // ...
}
```

### 3. Document Error Conditions

```rust
/// Load building data from file
///
/// # Errors
///
/// Returns an error if:
/// - File does not exist (`FileNotFound`)
/// - File cannot be read (`IoError`)
/// - YAML parsing fails (`YamlProcessing`)
/// - Validation fails (`Validation`)
pub fn load_building(path: &Path) -> Result<Building, ArxError> {
    // ...
}
```

### 4. Use Module Documentation

Document modules to explain their purpose:

```rust
//! Git integration for ArxOS
//!
//! This module provides Git operations for building data, including:
//! - Commit management
//! - Change staging
//! - History tracking
//!
//! # Usage
//!
//! ```rust,no_run
//! use arxos::git::BuildingGitManager;
//!
//! let git = BuildingGitManager::new("path/to/repo")?;
//! git.commit("Add new equipment")?;
//! ```

pub struct BuildingGitManager { ... }
```

### 5. Link Related Items

```rust
/// Configuration error
///
/// See also [`ConfigManager`] for configuration operations
/// and [`ConfigError`] for other error types.
pub enum ConfigError { ... }
```

---

## Current ArxOS Status

### What's Already Documented

✅ **Core Types**: `Building`, `Room`, `Equipment` have rustdoc comments  
✅ **FFI Functions**: Mobile FFI functions have documentation  
✅ **Module Structure**: Modules have overview documentation  
✅ **Error Types**: Error types are documented

### What Could Be Improved

⚠️ **Some functions lack examples**  
⚠️ **Some modules need better overviews**  
⚠️ **Cross-references could be added**  
⚠️ **Documentation not yet hosted/published**

---

## Recommendation for ArxOS

### Phase 1: Improve Existing Documentation (Current)

1. ✅ Add examples to all public functions
2. ✅ Enhance module-level documentation
3. ✅ Add cross-references between related items
4. ✅ Document error conditions consistently

### Phase 2: Generate and Host (Next)

**Recommendation: Use GitHub Pages**

**Why:**
- ArxOS may not be published to crates.io
- Full control over hosting
- Easy to set up with GitHub Actions
- Free and reliable

**Implementation:**
1. Create `.github/workflows/docs.yml` to build docs on push
2. Deploy to `gh-pages` branch
3. Enable GitHub Pages
4. Link from README.md

### Phase 3: Auto-Generation (Future)

Once hosting is set up, docs will automatically update on every push to main.

---

## Quick Start Guide

### Generate Documentation Now

```bash
# Build documentation
cargo doc --no-deps --open

# View in browser at:
# file:///path/to/arxos/target/doc/arxos/index.html
```

### Check Documentation Coverage

```bash
# Check for undocumented items
cargo doc --no-deps --document-private-items 2>&1 | grep "warning.*undocumented"
```

### Test Documentation Examples

```bash
# Run documentation tests
cargo test --doc

# This compiles and runs all code examples in doc comments
```

---

## Comparison: rustdoc vs Markdown Docs

| Aspect | rustdoc | Markdown Docs |
|--------|---------|---------------|
| **Source** | Code comments | Separate `.md` files |
| **Sync** | Always in sync | Manual updates |
| **Examples** | Tested automatically | Manual verification |
| **Search** | Built-in | External tools |
| **IDE Integration** | Full support | Limited |
| **Maintenance** | Low (auto-extracted) | High (manual) |
| **Coverage** | API-focused | Can include everything |

**Best Approach:** Use both!
- **rustdoc**: For API reference (auto-generated from code)
- **Markdown**: For guides, tutorials, workflows (user-facing docs)

---

## Summary

**rustdoc** is Rust's built-in documentation system that:
1. Extracts documentation from code comments (`///` and `//!`)
2. Generates beautiful HTML documentation
3. Tests code examples automatically
4. Provides IDE integration

**Proper Implementation:**
1. Document all public APIs with `///`
2. Include examples in documentation
3. Use standard sections (# Arguments, # Returns, # Errors, etc.)
4. Host on docs.rs (if published) or GitHub Pages (if private)

**For ArxOS:**
- Current status: Good rustdoc coverage, needs examples
- Recommendation: Set up GitHub Pages hosting
- Next step: Create GitHub Actions workflow for auto-deployment

---

## See Also

- [Official rustdoc Book](https://doc.rust-lang.org/rustdoc/)
- [How to Write Documentation](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html)
- [docs.rs Documentation](https://docs.rs/)
- [GitHub Pages](https://pages.github.com/)

