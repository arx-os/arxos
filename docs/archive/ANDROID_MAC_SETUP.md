# Building Android on macOS - Complete Guide

**Status:** ✅ Working as of January 2025

## Overview

ArxOS Android libraries can now be built on macOS using Homebrew-installed Android NDK and `cargo-ndk`. No Android Studio required!

## Prerequisites

1. **Homebrew** installed
2. **Rust** installed (with Cargo)
3. Android Rust targets installed

## Quick Start

### 1. Install Dependencies

```bash
# Install Android NDK via Homebrew
brew install android-ndk

# Install cargo-ndk tool
cargo install cargo-ndk

# Install Android Rust targets (if not already installed)
rustup target install aarch64-linux-android armv7-linux-androideabi
```

### 2. Build Android Libraries

```bash
# Set NDK path
export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"

# Build for both architectures
cargo ndk -t arm64-v8a -t armeabi-v7a -o android/app/src/main/jniLibs build --release --lib
```

Or use the automated script:

```bash
chmod +x scripts/build-android-mac.sh
./scripts/build-android-mac.sh
```

### 3. Verify Build

```bash
# Check that .so files were created
find android/app/src/main/jniLibs -name "*.so" -exec ls -lh {} \;
```

You should see:
- `libarxos.so` in `android/app/src/main/jniLibs/arm64-v8a/` (~1.8MB)
- `libarxos.so` in `android/app/src/main/jniLibs/armeabi-v7a/` (~852KB)

## Architecture

The build process:
1. Compiles Rust code to Android-compatible libraries using `cargo-ndk`
2. Automatically creates `.so` files in the correct `jniLibs` subdirectories
3. Works with Android app's existing Gradle configuration

## Troubleshooting

### "Could not find any NDK"

```bash
# Set the environment variable in your shell profile
echo 'export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"' >> ~/.zshrc
source ~/.zshrc
```

### Build Errors

If you see JNI-related errors:
- The JNI module is currently disabled
- Use `--lib` flag only (no `--features android`)
- JNI bindings will be implemented in a future update

### Missing Rust Targets

```bash
rustup target list  # See installed targets
rustup target add aarch64-linux-android armv7-linux-androideabi
```

## Next Steps

1. **Build the Android App**: Use Android Studio or Gradle to compile the full app
2. **Test on Device**: Connect an Android device and run the app
3. **Implement JNI**: Add Java/Kotlin bindings when needed

## References

- Android NDK: https://developer.android.com/ndk
- cargo-ndk: https://crates.io/crates/cargo-ndk
- Android Build Guide: `android/BUILD_GUIDE.md`
- Android NDK TODO: `ANDROID_NDK_TODO.md`

## Key Files

- `scripts/build-android-mac.sh` - Automated build script
- `android/app/src/main/jniLibs/` - Where compiled .so files live
- `src/mobile_ffi/ffi.rs` - C FFI bindings (currently used)
- `android/app/build.gradle` - Gradle configuration

---

**Success!** You can now build ArxOS for Android entirely from your Mac terminal. 🎉

