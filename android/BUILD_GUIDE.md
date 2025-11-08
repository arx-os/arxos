# Android Build Guide

**Status:** Configured - Ready for Rust Library Integration

## Current State

The Android app is configured and ready for Rust FFI integration:

✅ **Completed:**
- JNI library loading enabled with error handling
- ARCore dependencies added
- Android targets installed (aarch64, armv7)
- Proper directory structure created
- Gradle configuration fixed

## Building the Rust Library

To build the Rust library for Android, you'll need:

1. **Android NDK** installed and configured
2. **Rust Android targets** (already installed)

### Build Steps

```bash
# Set Android NDK path (adjust for your system)
export ANDROID_NDK_HOME=$HOME/Android/Sdk/ndk-bundle

# Build for all architectures
cd /path/to/arxos
cargo build -p arxos --target aarch64-linux-android --release --lib
cargo build -p arxos --target armv7-linux-androideabi --release --lib

# Copy libraries to Android project
cp target/aarch64-linux-android/release/libarxos.so android/app/src/main/jniLibs/arm64-v8a/
cp target/armv7-linux-androideabi/release/libarxos.so android/app/src/main/jniLibs/armeabi-v7a/
```

### Alternative: Use the Build Script

```bash
# From project root
./scripts/build-mobile-android.sh

# Then copy .so files to jniLibs directories
```

## Testing

1. Open `android/` in Android Studio
2. Sync Gradle files
3. Build APK
4. Install on device with ARCore support
5. Run and test

## Current Limitations

- Native library not yet built (requires NDK setup)
- JSON parsing in JNI wrapper commented out until library is linked
- Requires physical device for AR testing

## Next Steps

1. Set up Android NDK on development machine
2. Build Rust library for Android
3. Copy .so files to jniLibs directories
4. Implement JSON parsing in JNI wrappers
5. Test on physical Android device

## Architecture

The app follows a clean MVVM pattern:

```
Kotlin UI Layer (Jetpack Compose)
    ↕
JNI Wrapper (ArxOSCoreJNI.kt)
    ↕
Rust FFI Layer (libarxos.so)
    ↕
Rust Core (ArxOS functionality)
```

## Resources

- [Android NDK Setup](https://developer.android.com/ndk/guides)
- [Rust Android Targets](https://rust-lang.github.io/rustup-components-history/)
- [ARCore Documentation](https://developers.google.com/ar)

---

**Note:** Android development requires Windows/Linux with Android NDK installed. Current setup is ready for building when NDK is available.

