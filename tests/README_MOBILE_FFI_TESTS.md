# Mobile FFI Tests

## Overview

This directory contains comprehensive tests for the mobile FFI (Foreign Function Interface) bindings that enable iOS and Android applications to interact with the ArxOS Rust core.

## Test Organization

### `mobile_ffi_tests.rs`

Main test file for mobile FFI functions, organized into modules:

1. **Core FFI Tests** (`tests` module)
   - Basic FFI function tests: `arxos_list_rooms`, `arxos_get_room`, `arxos_list_equipment`, `arxos_get_equipment`
   - AR scan parsing: `arxos_parse_ar_scan`, `arxos_extract_equipment`
   - Error handling and memory management
   - JSON serialization/deserialization

2. **FFI Error Tracking Tests** (`ffi_error_tracking_tests` module)
   - Error code mapping and retrieval
   - Error message handling
   - Error isolation between operations
   - Null pointer handling
   - Invalid UTF-8 handling

3. **JNI Implementation Tests** (`jni_tests` module)
   - Tests for underlying mobile_ffi functions (used by JNI)
   - JSON serialization verification
   - Equipment extraction from AR scans

4. **AR Integration Tests** (`ar_integration_tests` module) ⭐ **NEW**
   - `arxos_load_ar_model()` - Model export and loading
   - `arxos_save_ar_scan()` - AR scan data saving and processing
   - `arxos_list_pending_equipment()` - Pending equipment listing
   - `arxos_confirm_pending_equipment()` - Equipment confirmation workflow
   - `arxos_reject_pending_equipment()` - Equipment rejection workflow
   - Complete workflow integration tests

### `ios_ar_workflow_integration_tests.rs` ⭐ **NEW**

End-to-end integration tests for the complete iOS AR workflow:
- Model loading → Scan saving → Pending listing → Confirmation → Verification
- Rejection workflow testing
- Building data persistence verification

## Test Coverage

### FFI Functions Coverage

| Function | Unit Tests | Integration Tests | Status |
|----------|-----------|-------------------|--------|
| `arxos_list_rooms` | ✅ | ✅ | Complete |
| `arxos_get_room` | ✅ | ✅ | Complete |
| `arxos_list_equipment` | ✅ | ✅ | Complete |
| `arxos_get_equipment` | ✅ | ✅ | Complete |
| `arxos_parse_ar_scan` | ✅ | ✅ | Complete |
| `arxos_extract_equipment` | ✅ | ✅ | Complete |
| `arxos_load_ar_model` | ✅ | ✅ | **NEW** |
| `arxos_save_ar_scan` | ✅ | ✅ | **NEW** |
| `arxos_list_pending_equipment` | ✅ | ✅ | **NEW** |
| `arxos_confirm_pending_equipment` | ✅ | ✅ | **NEW** |
| `arxos_reject_pending_equipment` | ✅ | ✅ | **NEW** |

## Running Tests

### Run all mobile FFI tests:
```bash
cargo test --lib mobile_ffi_tests
```

### Run AR integration tests only:
```bash
cargo test --lib mobile_ffi_tests::ar_integration_tests
```

### Run iOS workflow integration tests:
```bash
cargo test --test ios_ar_workflow_integration_tests
```

### Run specific test:
```bash
cargo test --lib test_arxos_load_ar_model_with_temp_file
```

## Test Structure Best Practices

1. **Helper Functions**: Use `to_c_string()` and `free_c_string()` for safe C string handling
2. **Temp Directories**: Use `tempfile::TempDir` for isolated test environments
3. **Directory Management**: Use `DirectoryGuard` pattern for tests that change working directory
4. **Serial Tests**: Use `#[serial]` attribute for tests that modify global state
5. **Error Handling**: Test both success and failure paths
6. **Null Safety**: Always test null pointer handling
7. **Memory Management**: Verify proper cleanup with `arxos_free_string()`

## Test Data

Test buildings are created dynamically using `create_test_building()` helper function. This ensures:
- Isolated test environments
- No pollution of real building data
- Consistent test data across runs

## iOS Swift Tests

Swift unit tests are located in:
- `ios/ArxOSMobile/ArxOSMobileTests/ArxOSCoreFFITests.swift` - FFI wrapper tests
- `ios/ArxOSMobile/ArxOSMobileTests/ARScanDataTests.swift` - Model serialization tests

These tests require:
- Xcode project configuration
- Swift test target setup
- Mock FFI library for isolated testing

## Future Enhancements

- [ ] Mock FFI library for Swift tests
- [ ] Performance benchmarks for FFI calls
- [ ] Memory leak detection tests
- [ ] Thread safety tests
- [ ] Android JNI tests

