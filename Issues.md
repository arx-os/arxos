# ArxOS Development Issues

This file tracks known issues, technical debt, and improvement areas for the ArxOS project.

## Code Quality Issues

### Minor Issues (Mostly Addressed)

1. **TODO in JNI** (`src/mobile_ffi/jni.rs:60`) ✅
   - Intentionally deferred until Android NDK is set up
   - Requires JNI implementation for Android platform
   - Status: Known issue, pending Android NDK setup

2. **Unused Imports** ✅
   - ~~Approximately 10 unused imports across several files~~
   - Impact: Harmless
   - Status: **RESOLVED** - Cleaned up in recent commit

3. **unwrap/expect Usage** ✅
   - 86 instances of `unwrap()`/`expect()` in codebase
   - **Reviewed:** Most instances are in tests (acceptable)
   - Production instances are appropriate:
     - Hardcoded regex compilation in `src/path/mod.rs` (will only fail if code is broken)
     - Fallback error strings in `src/mobile_ffi/ffi.rs` (fails at init time if malformed)
   - Status: **ACCEPTABLE** - All production uses are safe

4. **Clippy Warnings** ✅
   - ~80 clippy warnings total (mostly minor style suggestions)
   - Suggested improvements:
     - Derive `Default` for `SpatialEngine` and other types where appropriate
     - Remove redundant casts (`f64` -> `f64`)
     - Use `std::io::Error::other()` instead of custom error patterns
     - Replace literal bool comparisons with `assert!()` instead of `assert_eq!()`
   - Status: **LOW PRIORITY** - Code compiles and tests pass, these are style suggestions

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
