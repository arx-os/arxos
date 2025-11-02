# Mobile CI/CD Guide

## Overview

ArxOS uses GitHub Actions for automated building, testing, and distribution of iOS and Android mobile applications.

## Workflows

### iOS Build (`ios-build.yml`)

Builds the iOS XCFramework and optionally creates app archives.

**Triggers:**
- Push to `main` or `develop` branches (when iOS-related files change)
- Pull requests to `main` or `develop`
- Manual workflow dispatch
- Release creation

**Jobs:**

1. **build-xcframework**
   - Builds Rust library for iOS architectures:
     - `aarch64-apple-ios` (devices)
     - `aarch64-apple-ios-sim` (simulator ARM)
     - `x86_64-apple-ios` (simulator x86_64)
   - Creates universal simulator library using `lipo`
   - Packages XCFramework with proper Info.plist
   - Uploads artifacts for 30 days

2. **build-app** (conditional)
   - Only runs on releases or manual dispatch
   - Downloads XCFramework artifact
   - Builds iOS app archive using Xcode
   - Note: IPA export requires code signing certificates (not yet configured)

**Artifacts:**
- `ios-xcframework`: ArxOS.xcframework.zip
- `ios-libraries`: Individual .a library files
- `ios-app-archive`: Xcode archive (if build-app runs)

**Usage:**

```bash
# Trigger manually via GitHub Actions UI
# Or push to main/develop with iOS-related changes
```

### Android Build (`android-build.yml`)

Builds Android native libraries and APK/AAB packages.

**Triggers:**
- Push to `main` or `develop` branches (when Android-related files change)
- Pull requests to `main` or `develop`
- Manual workflow dispatch
- Release creation

**Jobs:**

1. **build-native**
   - Sets up Android NDK (version 26.1.10909125)
   - Builds Rust library for Android architectures:
     - `aarch64-linux-android` (ARM64)
     - `armv7-linux-androideabi` (ARMv7)
     - `i686-linux-android` (x86)
     - `x86_64-linux-android` (x86_64)
   - Configures Cargo for Android cross-compilation
   - Copies .so files to `jniLibs` directory structure
   - Uploads native libraries as artifacts

2. **build-app**
   - Downloads native library artifacts
   - Sets up Java 17 and Android SDK
   - Builds debug APK (always)
   - Builds release AAB (on releases/manual dispatch)
   - Uploads build artifacts and reports

**Artifacts:**
- `android-native-libs`: Native .so files for all architectures
- `android-debug-apk`: Debug APK for testing
- `android-release-aab`: Release AAB for Play Store (if built)
- `android-build-reports`: Build reports and logs

**Usage:**

```bash
# Automatic on push to main/develop
# Manual via GitHub Actions UI
# Release AAB built on release creation
```

### Mobile Tests (`mobile-tests.yml`)

Runs tests for mobile FFI and integration.

**Triggers:**
- Push to `main` or `develop` (when mobile FFI changes)
- Pull requests
- Manual workflow dispatch

**Jobs:**

1. **test-mobile-ffi**
   - Runs Rust mobile FFI unit tests
   - Runs AR integration tests
   - Runs hardware integration tests
   - Always runs on push/PR

2. **test-ios-simulator** (conditional)
   - Only runs on manual dispatch or commits with `[ios]` tag
   - Builds for iOS simulator architectures
   - Placeholder for Xcode test integration

3. **test-android-emulator** (conditional)
   - Only runs on manual dispatch or commits with `[android]` tag
   - Sets up Android emulator (API 29, x86_64)
   - Runs connected Android tests
   - Requires additional Gradle configuration

**Usage:**

```bash
# Automatic on mobile FFI changes
# Manual via GitHub Actions UI
# Use commit message tags: [ios] or [android]
```

## Artifact Retention

- **XCFramework/APK/AAB**: 30 days (production artifacts)
- **Libraries**: 7 days (intermediate builds)
- **Test Results**: 7 days (debugging)

## Downloading Artifacts

### Via GitHub UI

1. Go to **Actions** tab
2. Select the workflow run
3. Scroll to **Artifacts** section
4. Click artifact name to download

### Via GitHub CLI

```bash
gh run list --workflow=ios-build.yml
gh run download <run-id> --artifact ios-xcframework
```

## Build Configuration

### iOS

- **Deployment Target**: iOS 17.0
- **Xcode**: Latest stable (auto-selected)
- **Architectures**: arm64 (device), arm64 + x86_64 (simulator)

### Android

- **NDK Version**: 26.1.10909125
- **Minimum API Level**: 21
- **Target API Level**: Latest (from Android SDK)
- **Java Version**: 17
- **Gradle**: Wrapped version in project

## Code Signing

### iOS

Currently configured for unsigned builds. To enable signed builds:

1. Add signing certificates to GitHub Secrets:
   - `IOS_SIGNING_CERTIFICATE_BASE64`
   - `IOS_SIGNING_KEY_BASE64`
   - `IOS_PROVISIONING_PROFILE_BASE64`

2. Update `build-app` job to use certificates

3. Configure `CODE_SIGN_IDENTITY` and provisioning

### Android

Currently builds debug APK without signing. For release:

1. Add signing keys to GitHub Secrets:
   - `ANDROID_KEYSTORE_BASE64`
   - `ANDROID_KEYSTORE_PASSWORD`
   - `ANDROID_KEY_ALIAS`
   - `ANDROID_KEY_PASSWORD`

2. Update `build-app` job to sign AAB

3. Configure `signingConfig` in `build.gradle`

## Troubleshooting

### Build Failures

1. **iOS: Missing Xcode**
   - Workflow uses `macos-latest` which includes Xcode
   - If issues occur, check Xcode version in logs

2. **Android: NDK Not Found**
   - Workflow automatically sets up NDK
   - Verify NDK version matches `android-build.yml`

3. **Rust Compilation Errors**
   - Check Rust toolchain version
   - Verify target installation
   - Review Cargo.lock for dependency issues

### Test Failures

1. **Mobile FFI Tests**
   - Verify test data files exist
   - Check FFI function signatures

2. **iOS Simulator Tests**
   - Requires Xcode project test configuration
   - May need additional setup

3. **Android Emulator Tests**
   - Requires Gradle test configuration
   - Emulator setup may timeout on slow runners

### Performance

- **Cache Strategy**: Uses Rust dependency cache
- **Parallel Builds**: Jobs run in parallel where possible
- **Timeout**: 30-45 minutes per job

## Best Practices

1. **Trigger Conditions**: Use path filters to avoid unnecessary builds
2. **Artifact Retention**: Download important artifacts before they expire
3. **Manual Testing**: Use `workflow_dispatch` for manual verification
4. **Release Process**: Tag releases to trigger production builds
5. **Monitoring**: Watch workflow runs for regressions

## Future Enhancements

- [ ] Code signing for iOS releases
- [ ] Code signing for Android releases
- [ ] TestFlight distribution
- [ ] Play Store internal testing distribution
- [ ] Automated device testing
- [ ] Performance benchmarking
- [ ] Code coverage reports

## See Also

- [iOS Build Guide](../ios/README.md)
- [Android Build Guide](../android/BUILD_GUIDE.md)
- [Mobile FFI Integration](./MOBILE_FFI_INTEGRATION.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

