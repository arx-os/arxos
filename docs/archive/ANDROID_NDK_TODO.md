# Android NDK TODO

**Status:** ✅ WORKING on macOS  
**Priority:** Low  
**Last Updated:** January 2025

## Issue

Android build requires Android NDK which was previously thought to not be available on macOS.

## What's Ready

- ✅ Android app structure complete
- ✅ ARCore dependencies added
- ✅ Build configuration fixed
- ✅ Rust targets installed (aarch64, armv7)
- ✅ **NDK installed via Homebrew on macOS**
- ✅ **Rust libraries built successfully for Android**

## What's Been Done

- ✅ Android NDK installation via `brew install android-ndk`
- ✅ `cargo-ndk` installed for easy Android builds
- ✅ Built Rust library for both ARM architectures
- ✅ Created .so files in jniLibs directories
- ✅ Created `scripts/build-android-mac.sh` for easy rebuilding

## Current Build Status

**Rust libraries built and ready:**
- ARM64: `android/app/src/main/jniLibs/arm64-v8a/libarxos.so` (1.8MB)
- ARMv7: `android/app/src/main/jniLibs/armeabi-v7a/libarxos.so` (852KB)

## How to Build on macOS

```bash
# Install NDK (one time)
brew install android-ndk

# Install cargo-ndk (one time)
cargo install cargo-ndk

# Build Android libraries
export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"
cargo ndk -t arm64-v8a -t armeabi-v7a -o android/app/src/main/jniLibs build --release --lib

# Or use the build script
./scripts/build-android-mac.sh
```

## What's Still Needed

- [ ] Implement JNI bindings (currently placeholder)
- [ ] Test on physical Android device
- [ ] Verify ARCore integration works
- [ ] Add full JNI implementation for Android

## References

- See `android/BUILD_GUIDE.md` for detailed instructions
- Android NDK: https://developer.android.com/ndk
- Build script: `scripts/build-android-mac.sh`

