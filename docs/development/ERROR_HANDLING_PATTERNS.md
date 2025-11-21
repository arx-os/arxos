# Error Handling Patterns in ArxOS

This document describes the error handling patterns used throughout the ArxOS codebase to ensure robustness and prevent panics.

## Core Principles

1. **No unwrap() in production code** - All production code uses proper error handling
2. **Descriptive error messages** - Errors include context, suggestions, and recovery steps
3. **Graceful degradation** - Systems recover from errors when possible
4. **Test code flexibility** - Test code may use unwrap() for clarity

## Enforced Lints

The following clippy lints are enabled in `src/lib.rs`:

```rust
#![warn(clippy::unwrap_used)]
#![warn(clippy::expect_used)]
```

These lints will warn about any new unwrap() or expect() calls in production code.

## Common Patterns

### 1. Mutex Poison Recovery

**Problem**: `lock().unwrap()` can panic if a thread panicked while holding the lock.

**Solution**: Use `unwrap_or_else` with poison recovery:

```rust
// ❌ Bad - will panic
let data = mutex.lock().unwrap();

// ✅ Good - recovers from poison
let data = mutex.lock().unwrap_or_else(|poisoned| {
    log::warn!("Mutex poisoned, recovering");
    poisoned.into_inner()
});
```

**Examples**:
- `src/ifc/geometry.rs:143-147` - Transform cache recovery
- `src/ifc/geometry.rs:177-181` - Transform cache recovery

### 2. Option/Result Chaining

**Problem**: `option.unwrap()` panics on None, `result.unwrap()` panics on Err.

**Solution**: Use `ok_or_else`, `?` operator, or pattern matching:

```rust
// ❌ Bad - will panic
let value = hashmap.get(&key).unwrap();

// ✅ Good - descriptive error
let value = hashmap.get(&key)
    .ok_or_else(|| format!("Key {} not found in structure", key))?;

// ✅ Good - early return with ?
let error = modal.error.as_ref()?;

// ✅ Good - if-let pattern
if let Some(ch) = string.chars().next() {
    // Use ch safely
} else {
    return Err("Empty string".into());
}
```

**Examples**:
- `src/ifc/hierarchy/builder.rs:795-796` - Floor bounds checking
- `src/tui/error_modal.rs:170` - Error modal rendering
- `src/core/spatial/grid.rs:53-57` - Grid coordinate validation

### 3. System Resource Fallbacks

**Problem**: System resources (time, entropy) can fail in edge cases.

**Solution**: Provide fallback behavior:

```rust
// ❌ Bad - will panic if system clock is wrong
let timestamp = SystemTime::now()
    .duration_since(UNIX_EPOCH)
    .expect("System time error")
    .as_millis();

// ✅ Good - fallback to hash-based ID
let timestamp = SystemTime::now()
    .duration_since(UNIX_EPOCH)
    .unwrap_or_else(|_| {
        // System clock is before UNIX epoch - use random fallback
        use std::collections::hash_map::RandomState;
        use std::hash::{BuildHasher, Hash, Hasher};
        let mut hasher = RandomState::new().build_hasher();
        prefix.hash(&mut hasher);
        std::time::Duration::from_millis(hasher.finish())
    })
    .as_millis();
```

**Examples**:
- `src/utils.rs:311-321` - ID generation with fallback

### 4. Array/Vec Bounds Checking

**Problem**: Index access can panic if out of bounds.

**Solution**: Use `.get()` with `ok_or_else`:

```rust
// ❌ Bad - will panic if index out of bounds
let item = vec[index];

// ✅ Good - descriptive error
let item = vec.get(index)
    .ok_or_else(|| format!("Index {} out of bounds (len: {})", index, vec.len()))?;
```

**Examples**:
- `src/ifc/hierarchy/builder.rs:795` - Floor index validation
- `src/ifc/hierarchy/builder.rs:870` - Room index validation
- `src/ifc/hierarchy/builder.rs:901` - Space index validation

### 5. String/Character Operations

**Problem**: String operations can fail on empty strings or invalid UTF-8.

**Solution**: Use safe iterators and validation:

```rust
// ❌ Bad - will panic if empty
let ch = string.chars().next().unwrap();

// ✅ Good - validated extraction
let ch = string.chars().next()
    .ok_or_else(|| format!("Expected non-empty string, got: '{}'", string))?;

// ✅ Good - safe uppercase conversion
if let Some(ch) = char.to_uppercase().next() {
    // Use uppercase char
} else {
    // Fallback behavior
}
```

**Examples**:
- `src/core/spatial/grid.rs:53-57` - Column character validation
- `src/core/spatial/grid.rs:75-77` - Uppercase conversion

## ArxError Integration

Use the `ArxError` type for rich error context:

```rust
use crate::error::{ArxError, ErrorCategory, ErrorSeverity};

// Create error with full context
return Err(ArxError {
    message: "Failed to parse IFC structure".to_string(),
    category: ErrorCategory::Parsing,
    severity: ErrorSeverity::High,
    context: vec![
        format!("File: {}", filepath),
        format!("Line: {}", line_num),
    ],
    suggestions: vec![
        "Check IFC file format version".to_string(),
        "Validate with IFC schema checker".to_string(),
    ],
    recovery_steps: vec![
        "Skip this element and continue parsing".to_string(),
    ],
});
```

## When unwrap() IS Acceptable

### Test Code

Test code may use `unwrap()` for clarity:

```rust
#[cfg(test)]
mod tests {
    #[test]
    fn test_parsing() {
        let coord = GridCoordinate::parse("D-4").unwrap();
        assert_eq!(coord.column, "D");
    }
}
```

### Infallible Operations

Some operations are guaranteed to succeed by invariants:

```rust
// After checking len() != 0
if !vec.is_empty() {
    let first = vec.first(); // This is Some, but still use safe pattern
}
```

Even for infallible operations, prefer safe patterns to maintain consistency.

## Code Review Checklist

When reviewing code, check for:

- [ ] No `.unwrap()` in production code paths
- [ ] No `.expect()` in production code paths
- [ ] Mutex locks use poison recovery
- [ ] Array/HashMap access uses `.get()` with error handling
- [ ] System resource access has fallbacks
- [ ] Error messages include context and suggestions
- [ ] Test code is properly marked with `#[cfg(test)]`

## Migration History

### Phase 2.1-2.2: Critical IFC Processing (Nov 2024)
- Fixed `lock().unwrap()` in geometry.rs (2 instances)
- Fixed array access in builder.rs (4 instances)

### Phase 2.3: Domain-Based Cleanup (Nov 2024)
- Spatial domain: grid.rs (2 instances)
- Utils: generate_id fallback (1 instance)
- TUI: error_modal.rs (1 instance)

### Phase 2.4: Enforcement (Nov 2024)
- Enabled clippy::unwrap_used and clippy::expect_used lints
- Verified 0 production unwraps across 222 source files
- Documented patterns for future development

## Statistics

- **Total source files**: 222
- **Production unwraps**: 0 ✅
- **Test unwraps**: 293 (acceptable)
- **Unwraps fixed in Phase 2**: 10
- **Error recovery patterns**: 5

## Future Improvements

1. Consider using `anyhow` or `thiserror` for error type ergonomics
2. Add telemetry for poison recovery events
3. Benchmark error path performance
4. Create error handling examples for common scenarios
