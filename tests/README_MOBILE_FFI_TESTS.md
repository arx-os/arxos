# Archived: Mobile FFI Tests

All mobile FFI tests were retired alongside the iOS/Android clients (November 2025). They are preserved only in the mobile archive bundle referenced from `docs/mobile/STATUS.md`.

If you need to revisit the legacy flows:

1. Check out the `mobile-apps-final` tag.
2. Restore `tests/mobile/mobile_ffi_tests.rs` and `tests/ar/ar_ios_workflow_integration_tests.rs`.
3. Re-enable the `mobile_ffi` module and related dependencies (UniFFI, JNI).

For ongoing development, use the WASM helpers in `ar_integration::wasm` and the upcoming PWA integration tests.

