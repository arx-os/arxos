# ArxOS Development Issues

This file tracks known issues, technical debt, and improvement areas for the ArxOS project.

## Code Quality Issues

### Minor Issues

1. **TODO in JNI** (`src/mobile_ffi/jni.rs:60`)
   - Intentionally deferred until Android NDK is set up
   - Requires JNI implementation for Android platform
   - Status: Known issue, pending Android NDK setup

2. **Unused Imports**
   - Approximately 10 unused imports across several files
   - Impact: Harmless but should be cleaned up
   - Status: Minor linting issue

3. **unwrap/expect Usage**
   - 86 instances of `unwrap()`/`expect()` in codebase
   - Many instances are in tests (acceptable)
   - Some instances in production code (should be reviewed)
   - Status: Needs review to determine which should be replaced with proper error handling

4. **Clippy Warnings**
   - Minor style improvements suggested:
     - Derive `Default` for `SpatialEngine` and other types where appropriate
     - Remove redundant casts (`f64` -> `f64`)
     - Use `std::io::Error::other()` instead of custom error patterns
     - Replace literal bool comparisons with `assert!()` instead of `assert_eq!()`
   - Status: Low priority linting improvements

## Technical Debt

No major technical debt items at this time.

## Known Limitations

1. **Android NDK Setup**
   - Documented in `ANDROID_NDK_TODO.md`
   - Required for building Rust library for Android
   - Status: Pending

2. **iOS FFI Testing**
   - FFI functions ready but require physical device testing
   - Documented in `docs/IOS_FFI_STATUS.md`
   - Status: Ready for testing on device
