# ArxOS Error Handling Guide

**Version:** 2.0  
**Last Updated:** January 2025

---

## Overview

ArxOS uses a comprehensive error handling system built on `thiserror` and custom error types. This guide documents the standard patterns and best practices for error handling across all modules.

---

## Table of Contents

1. [Error Architecture](#error-architecture)
2. [Standard Error Types](#standard-error-types)
3. [Error Patterns](#error-patterns)
4. [Best Practices](#best-practices)
5. [Migration Guide](#migration-guide)
6. [Examples](#examples)

---

## Error Architecture

### Central Error System

ArxOS has a **two-tier error architecture**:

1. **Central Error Type** (`ArxError` in `src/error/mod.rs`)
   - Rich error context with suggestions and recovery steps
   - User-friendly error messages
   - Debugging information

2. **Module-Specific Error Types**
   - Domain-specific errors (IFC, Hardware, Git, etc.)
   - Can be converted to `ArxError` for consistency
   - Implement `From` trait for automatic conversion

### Error Flow

```
Module Error → Box<dyn Error> → ArxError (with context) → User Display
     ↓              ↓                    ↓                     ↓
  Specific      Generic          Rich Context         Friendly Message
```

---

## Standard Error Types

### 1. Central Error Type: `ArxError`

```rust
pub enum ArxError {
    IfcProcessing { message, context, source },
    Configuration { message, context, field },
    GitOperation { message, context, operation },
    Validation { message, context, file_path },
    IoError { message, context, path },
    YamlProcessing { message, context, file_path },
    SpatialData { message, context, entity_type },
}
```

**Characteristics:**
- ✅ Rich context with suggestions
- ✅ Recovery steps available
- ✅ User-friendly messages
- ✅ Debugging information

### 2. Module Error Types

Each module should define its own error type:

```rust
// In module's error.rs file
#[derive(Debug, Error)]
pub enum ModuleError {
    #[error("Operation failed: {reason}")]
    OperationFailed { reason: String },
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Generic error: {0}")]
    Generic(#[from] anyhow::Error),
}

pub type ModuleResult<T> = Result<T, ModuleError>;
```

**Required Traits:**
- `Debug` (for logging)
- `Error` (from `thiserror`)
- `Send + Sync` (for multi-threading)

---

## Error Patterns

### Pattern 1: Create Error with Context

```rust
use crate::error::ArxError;

// Simple error
let error = ArxError::validation("Invalid input");

// Error with context
let error = ArxError::validation("Invalid equipment type")
    .with_suggestions(vec![
        "Use one of: HVAC, Electrical, Plumbing".to_string(),
        "Check documentation for valid types".to_string(),
    ])
    .with_recovery(vec![
        "Retry with valid equipment type".to_string(),
        "Use 'arx equipment types' to see valid options".to_string(),
    ])
    .with_file_path("building.yaml")
    .with_help_url("https://arxos.io/docs/equipment");
```

### Pattern 2: Module Error to Central Error

```rust
use crate::error::ArxError;
use crate::ifc::error::IFCError;

impl From<IFCError> for ArxError {
    fn from(err: IFCError) -> Self {
        match err {
            IFCError::FileNotFound { path } => {
                ArxError::io_error(format!("IFC file not found: {}", path))
                    .with_file_path(path)
                    .with_suggestions(vec![
                        "Verify the file path is correct".to_string(),
                        "Check that the file exists".to_string(),
                    ])
            }
            IFCError::ParsingError { message } => {
                ArxError::ifc_processing(message)
                    .with_suggestions(vec![
                        "Verify the IFC file is valid".to_string(),
                        "Try re-exporting from your CAD software".to_string(),
                    ])
            }
            _ => ArxError::ifc_processing(err.to_string()),
        }
    }
}
```

### Pattern 3: Error Propagation

```rust
pub fn load_building_data(path: &str) -> Result<BuildingData, ArxError> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| ArxError::io_error(format!("Failed to read file: {}", e))
            .with_file_path(path)
            .with_suggestions(vec![
                "Check file permissions".to_string(),
                "Verify the file path is correct".to_string(),
            ]))?;
    
    serde_yaml::from_str(&content)
        .map_err(|e| ArxError::yaml_processing(format!("Failed to parse YAML: {}", e))
            .with_file_path(path)
            .with_suggestions(vec![
                "Verify the YAML syntax is valid".to_string(),
                "Check for missing or extra quotes".to_string(),
            ]))
}
```

### Pattern 4: Command Handler Error

```rust
pub fn handle_import(ifc_file: PathBuf, repo: Option<PathBuf>) 
    -> Result<(), Box<dyn std::error::Error>> 
{
    let processor = IFCProcessor::new();
    
    // Process IFC file
    let building_data = processor.process(&ifc_file)
        .map_err(|e| {
            // Convert to ArxError with context
            ArxError::ifc_processing(format!("IFC import failed: {}", e))
                .with_file_path(ifc_file.to_string_lossy())
                .with_suggestions(vec![
                    "Verify the IFC file is valid".to_string(),
                    "Check ArxOS documentation for supported formats".to_string(),
                ])
        })?;
    
    // Save building data
    save_building_data(&building_data)
        .map_err(|e| format!("Failed to save building data: {}", e))?;
    
    Ok(())
}
```

---

## Best Practices

### ✅ DO:

1. **Use Result types** for fallible operations
   ```rust
   fn risky_operation() -> Result<Success, Error>
   ```

2. **Provide context** with error messages
   ```rust
   Error::new("Operation failed".to_string())
       .with_file_path(path)
       .with_suggestions(vec!["..."])
   ```

3. **Use ? operator** for error propagation
   ```rust
   let data = read_file(path)?;
   ```

4. **Convert module errors** to central errors
   ```rust
   impl From<ModuleError> for ArxError
   ```

5. **Add suggestions** for user action
   ```rust
   .with_suggestions(vec![
       "Check file permissions".to_string(),
       "Verify the file exists".to_string(),
   ])
   ```

### ❌ DON'T:

1. **Don't use unwrap() in production code**
   ```rust
   // BAD
   let value = input.parse().unwrap();
   
   // GOOD
   let value = input.parse()
       .map_err(|e| ArxError::validation(format!("Invalid number: {}", e)))?;
   ```

2. **Don't ignore errors**
   ```rust
   // BAD
   let _ = risky_operation();
   
   // GOOD
   risky_operation()?;
   ```

3. **Don't use generic error strings**
   ```rust
   // BAD
   return Err("Error".into());
   
   // GOOD
   return Err(ArxError::validation("Invalid input format"));
   ```

4. **Don't lose error context**
   ```rust
   // BAD
   .map_err(|_| "Failed".into())
   
   // GOOD
   .map_err(|e| ArxError::io_error(format!("Failed to read: {}", e)))
   ```

---

## Module Error Types

### Current Module Errors

| Module | Error Type | Location | Status |
|--------|------------|----------|--------|
| Core | `ArxError` | `src/error/mod.rs` | ✅ Central type |
| IFC | `IFCError` | `src/ifc/error.rs` | ✅ Good |
| Git | `GitError` | `src/git/manager.rs` | ✅ Good |
| Hardware | `HardwareError` | `src/hardware/mod.rs` | ✅ Good |
| Persistence | `PersistenceError` | `src/persistence/error.rs` | ✅ Good |
| Config | `ConfigError` | `src/config/mod.rs` | ✅ Good |
| Path Safety | `PathSafetyError` | `src/utils/path_safety.rs` | ✅ Good |
| Mobile FFI | `FFIError` | `src/mobile_ffi/mod.rs` | ✅ Good |

---

## Migration Guide

### Migrating from unwrap() to Result

**Before:**
```rust
pub fn load_config() -> Config {
    let content = std::fs::read_to_string("config.toml").unwrap();
    toml::from_str(&content).unwrap()
}
```

**After:**
```rust
pub fn load_config() -> Result<Config, ArxError> {
    let content = std::fs::read_to_string("config.toml")
        .map_err(|e| ArxError::io_error(format!("Config file not found: {}", e))
            .with_suggestions(vec![
                "Create config.toml in the project root".to_string(),
                "See docs/CONFIG.md for configuration format".to_string(),
            ]))?;
    
    toml::from_str(&content)
        .map_err(|e| ArxError::configuration(format!("Invalid config: {}", e))
            .with_suggestions(vec![
                "Check TOML syntax".to_string(),
                "Verify all required fields are present".to_string(),
            ]))
}
```

### Migrating Command Handlers

**Before:**
```rust
pub fn handle_import(ifc_file: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let building = import_ifc(ifc_file.to_str().unwrap())?;
    save_building(building)?;
    Ok(())
}
```

**After:**
```rust
pub fn handle_import(ifc_file: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    // Convert path with proper error handling
    let path_str = ifc_file.to_str()
        .ok_or_else(|| ArxError::validation("Invalid file path")
            .with_file_path(ifc_file.to_string_lossy()))?;
    
    let building = import_ifc(path_str)?;
    save_building(building)?;
    
    println!("✅ Successfully imported IFC file");
    Ok(())
}
```

---

## Examples

### Example 1: File I/O Error

```rust
use crate::error::ArxError;

pub fn read_building_file(path: &str) -> Result<String, ArxError> {
    std::fs::read_to_string(path)
        .map_err(|e| ArxError::io_error(format!("Failed to read building file: {}", e))
            .with_file_path(path.to_string())
            .with_suggestions(vec![
                format!("Verify the file exists: {}", path),
                "Check file permissions".to_string(),
                "Ensure you have read access".to_string(),
            ])
            .with_recovery(vec![
                "Try running with sudo if permission issue".to_string(),
                "Verify the path is correct".to_string(),
            ])
            .with_help_url("https://arxos.io/docs/file-io"))
}
```

### Example 2: Validation Error

```rust
use crate::error::ArxError;

pub fn validate_equipment_type(equipment_type: &str) -> Result<(), ArxError> {
    const VALID_TYPES: &[&str] = &["HVAC", "Electrical", "Plumbing", "Safety"];
    
    if !VALID_TYPES.contains(&equipment_type) {
        return Err(ArxError::validation(
            format!("Invalid equipment type: {}", equipment_type)
        )
        .with_suggestions(vec![
            format!("Use one of: {}", VALID_TYPES.join(", ")),
            "Check ArxOS documentation for valid types".to_string(),
        ])
        .with_recovery(vec![
            "Run 'arx equipment types' to see all valid types".to_string(),
        ]));
    }
    
    Ok(())
}
```

### Example 3: FFI Error

```rust
use crate::error::ArxError;

pub unsafe extern "C" fn arxos_list_rooms(building_name: *const c_char) 
    -> *mut c_char 
{
    if building_name.is_null() {
        return create_error_json(
            ArxError::validation("building_name cannot be null")
                .with_suggestions(vec![
                    "Provide a valid building name".to_string(),
                    "Check that the pointer is not null".to_string(),
                ])
        );
    }
    
    // Rest of function...
}
```

---

## Summary

**ArxOS Error Handling Philosophy:**
1. ✅ Use `Result<T, E>` for all fallible operations
2. ✅ Provide rich context with suggestions
3. ✅ Use the `?` operator for error propagation
4. ✅ Convert module errors to `ArxError` for consistency
5. ✅ Never use `unwrap()` in production code
6. ✅ Always provide user-friendly error messages

**Key Benefits:**
- 🔍 Better debugging with context
- 👥 User-friendly error messages
- 🛠️ Actionable suggestions
- 📊 Error analytics and tracking
- 🔒 Type-safe error handling

---

**Next Steps:**
- Review existing error usage in modules
- Migrate unwrap() calls to proper error handling
- Add context to existing errors
- Update command handlers to use ArxError

