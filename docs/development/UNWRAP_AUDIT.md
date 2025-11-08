# Unwrap/Expect Usage Audit

**Date:** January 2025  
**Total Instances:** 492 in `src/` directory (excluding tests)  
**Priority:** Critical - Must fix before v1.0

---

## Summary

This audit categorizes all `unwrap()` and `expect()` calls in production code (excluding test files). The goal is to eliminate panic risks in production code paths.

### Risk Categories

- **CRITICAL**: User-facing code, command handlers, FFI functions
- **HIGH**: Core operations, data integrity paths
- **MEDIUM**: UI code, hardware processing
- **LOW**: Internal utilities, well-guarded contexts
- **TEST**: Test code (lower priority)

---

## Production Code Audit

### Critical Priority Files

#### 1. `crates/arxui/crates/arxui/src/commands/sync.rs`

**Line 31:**
```rust
let yaml_file = yaml_files.first().unwrap();
```

- **Risk Level:** CRITICAL
- **Context:** Command handler - user-facing
- **Issue:** Panics if no YAML files found
- **Fix:** Use `ok_or_else()` to return proper error

---

#### 2. `crates/arxui/crates/arxui/src/commands/spreadsheet.rs`

**Line 234:**
```rust
editor.as_mut().unwrap().reset_cursor();
```

- **Risk Level:** CRITICAL
- **Context:** UI editor - user interaction
- **Issue:** Panics if editor is None
- **Fix:** Check `editor.is_some()` before unwrap

**Line 456:**
```rust
.unwrap()
.as_secs();
```

- **Risk Level:** MEDIUM
- **Context:** Timestamp generation - should never fail in practice
- **Issue:** Panics if system time is before UNIX_EPOCH
- **Fix:** Use `expect()` with descriptive message or handle error

**Line 628:**
```rust
editor.as_mut().unwrap().reset_cursor();
```

- **Risk Level:** CRITICAL
- **Context:** UI editor - user interaction
- **Issue:** Same as line 234
- **Fix:** Same as line 234

---

#### 3. `crates/arxui/crates/arxui/src/commands/room_handlers.rs`

**Lines 367, 378, 406, 417:**
```rust
let (width, depth, height) = result.unwrap();
```

- **Risk Level:** TEST (in test functions)
- **Context:** Test code
- **Issue:** Tests should use `expect()` for better error messages
- **Fix:** Replace with `expect("test should parse dimensions correctly")`

**Note:** These are in test functions, lower priority but should still be fixed.

---

#### 4. `crates/arxui/crates/arxui/src/commands/init.rs`

**Lines 238, 261, 278:**
```rust
let building_data = create_minimal_building(&config).unwrap();
```

- **Risk Level:** TEST (in test functions)
- **Context:** Test code
- **Issue:** Tests should use `expect()` for better error messages
- **Fix:** Replace with `expect("test should create building successfully")`

---

### High Priority Files

#### 5. `src/core/operations.rs`

**Lines with unwrap/expect:** Multiple instances throughout

**Analysis needed:** Review each instance individually for:
- Context (production vs internal)
- Risk level
- Appropriate fix

**Status:** Requires detailed review (see Phase 1.2)

---

#### 6. `crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs`

**Line 67:**
```rust
.expect("Fallback error string must be valid")
```

- **Risk Level:** MEDIUM
- **Context:** FFI error handling - fallback string
- **Issue:** Should never fail, but if it does, panic is acceptable
- **Fix:** Keep expect with message (acceptable in FFI context)

**Line 464:**
```rust
.expect("Empty string must always be valid for CString")
```

- **Risk Level:** MEDIUM
- **Context:** FFI error handling - empty string creation
- **Issue:** Should never fail
- **Fix:** Keep expect with message (acceptable in FFI context)

**Status:** These are acceptable - well-documented fallback cases

---

### Medium Priority Files

#### 7. `src/persistence/mod.rs`

**Lines 349, 350, 379, 380, 383, 384:**
```rust
let temp_dir = TempDir::new().unwrap();
std::env::set_current_dir(temp_dir.path()).unwrap();
let yaml_content = serializer.to_yaml(&building_data).unwrap();
std::fs::write(&test_file, yaml_content).unwrap();
let persistence = PersistenceManager::new("Test Building").unwrap();
let loaded_data = persistence.load_building_data().unwrap();
```

- **Risk Level:** TEST (in test functions)
- **Context:** Test setup code
- **Issue:** Tests should handle errors gracefully
- **Fix:** Use `expect()` with descriptive messages

---

#### 8. `src/ui/*.rs` files

**Multiple instances in:**
- `src/ui/theme_manager.rs` - Test code
- `src/ui/spreadsheet/data_source.rs` - Test code
- `src/ui/spreadsheet/import.rs` - Test code
- `src/ui/error_modal.rs` - Test code
- `src/ui/error_integration.rs` - Test code

**Status:** Mostly test code - lower priority but should use `expect()` for better messages

---

#### 9. `src/identity/registry.rs`

**Lines:** 204, 205, 213, 214, 217, 221, 230, 231, 234, 237, 241, 244, 251, 252, 255, 266, 267, 279, 280, 283, 294, 295, 299, 301, 309, 310, 313, 316, 318, 321, 323, 331, 332, 341, 342, 345, 347, 350, 352, 359, 360, 369, 370, 373, 376, 386, 387, 390, 392, 398, 407, 408, 411, 414, 417, 424, 433, 448, 451, 454, 460, 461, 469, 470, 474, 476, 484, 485, 489, 493, 495, 511, 512, 521, 522, 526, 530, 533

**Risk Level:** TEST (all in test functions)
- **Context:** Test code
- **Issue:** Tests should use `expect()` for better error messages
- **Fix:** Replace with `expect()` with descriptive messages

---

#### 10. `src/identity/pending.rs`

**Line 197:**
```rust
info!("Added pending user request: {}", self.requests.last().unwrap().email);
```

- **Risk Level:** MEDIUM
- **Context:** Production code - logging after adding request
- **Issue:** Panics if requests vector is empty (shouldn't happen, but unsafe)
- **Fix:** Use `if let Some(last) = self.requests.last()` or check length

**Lines 355, 356, 363, 364, 367, 375, 376, 381, 382:**
- **Risk Level:** TEST (in test functions)
- **Fix:** Use `expect()` with descriptive messages

---

#### 11. `src/identity/gpg.rs`

**Lines:** Multiple test instances
- **Risk Level:** TEST
- **Fix:** Use `expect()` with descriptive messages

---

#### 12. `src/ifc/fallback.rs`

**Line 125:**
```rust
self.validate_file_size(validated_path.to_str().unwrap())?;
```

- **Risk Level:** HIGH
- **Context:** IFC file processing - path conversion
- **Issue:** Panics if path contains invalid UTF-8
- **Fix:** Use `to_string_lossy()` or handle error properly

---

### Low Priority Files

#### 13. `src/utils/path_safety.rs`

**Lines:** Multiple test instances
- **Risk Level:** TEST
- **Fix:** Use `expect()` with descriptive messages

---

## Test Code Summary

Most unwrap/expect calls in the codebase are in test files. While lower priority, they should still be fixed to:
- Use `expect()` for better error messages
- Make tests more maintainable
- Follow best practices

---

## Action Plan

### Phase 1: Critical Fixes (Week 1)

1. **`crates/arxui/crates/arxui/src/commands/sync.rs`** - Line 31 (CRITICAL)
2. **`crates/arxui/crates/arxui/src/commands/spreadsheet.rs`** - Lines 234, 628 (CRITICAL)
3. **`src/ifc/fallback.rs`** - Line 125 (HIGH)
4. **`src/identity/pending.rs`** - Line 197 (MEDIUM)

### Phase 2: Core Operations (Week 1-2)

1. **`src/core/operations.rs`** - Full audit and fix
2. Review all production paths

### Phase 3: Test Code (Week 2)

1. Replace unwrap with expect in all test files
2. Add descriptive messages

### Phase 4: UI and Hardware (Week 2)

1. Review UI code for production unwraps
2. Review hardware code for production unwraps

---

## Fix Pattern

### Before (❌)
```rust
let x = coords[0].parse().unwrap_or(0.0);
let file = files.first().unwrap();
```

### After (✅)
```rust
let x = coords[0].parse()
    .map_err(|e| ArxError::validation(format!("Invalid coordinate '{}': {}", coords[0], e)))?;

let file = files.first()
    .ok_or_else(|| ArxError::validation("No files found in directory".to_string()))?;
```

### For Tests (✅)
```rust
// Before
let result = function().unwrap();

// After
let result = function().expect("test should succeed");
```

---

## Success Criteria

- [ ] Zero unwrap/expect in production command handlers
- [ ] Zero unwrap/expect in FFI functions (except documented fallbacks)
- [ ] Zero unwrap/expect in core operations
- [ ] All test code uses expect() with descriptive messages
- [ ] All error paths properly handled with Result types

---

## Notes

- FFI functions with `expect()` for fallback strings are acceptable (documented)
- Test code should use `expect()` instead of `unwrap()` for better error messages
- All user-facing code must eliminate panic risks
- Maintain backward compatibility where possible

