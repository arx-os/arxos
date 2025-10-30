# Android NDK TODO

**Status:** Blocked on NDK Setup  
**Priority:** Low  
**Last Updated:** January 2025

## Issue

Android build requires Android NDK which is not available on macOS without Android Studio.

## What's Ready

- ✅ Android app structure complete
- ✅ JNI integration prepared
- ✅ ARCore dependencies added
- ✅ Build configuration fixed
- ✅ Rust targets installed (aarch64, armv7)

## What's Needed

- [ ] Android NDK installation (Windows/Linux only)
- [ ] Build Rust library for Android
- [ ] Copy .so files to jniLibs
- [ ] Test on physical Android device

## When to Address

- When working on Windows/Linux development machine
- When Android development becomes priority
- When ready to test AR functionality on Android

## References

- See `android/BUILD_GUIDE.md` for detailed instructions
- Android NDK: https://developer.android.com/ndk

