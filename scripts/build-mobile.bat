@echo off
REM ArxOS Mobile Build Script (Windows)
REM Note: FFI bindings (arxos_mobile.udl) need to be created before this script can build mobile libraries

if not exist "src\arxos_mobile.udl" (
    echo [ERROR] FFI bindings not found!
    echo.
    echo To enable mobile builds:
    echo   1. Create arxos_mobile.udl file with UniFFI definitions
    echo   2. Add UniFFI build configuration to Cargo.toml
    echo   3. Run this script again
    echo.
    echo For now, mobile apps run in standalone mode with graceful fallbacks.
    exit /b 1
)

echo [INFO] Mobile FFI bindings detected
echo [INFO] Building Rust library for Android...

REM Android Targets
set ANDROID_TARGETS=aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android

if "%1"=="install" (
    echo [INFO] Installing Android targets...
    for %%t in (%ANDROID_TARGETS%) do (
        rustup target add %%t
    )
    echo [SUCCESS] All targets installed
    exit /b 0
)

if "%1"=="android" (
    echo [INFO] Building for Android...
    echo [WARNING] Android build not yet implemented (requires FFI bindings)
    exit /b 0
)

echo ArxOS Mobile Build Script
echo.
echo Usage: %0 [android|install|help]
echo.
echo Commands:
echo   android  - Build for Android
echo   install  - Install Rust targets
echo   help     - Show this help
echo.
echo Note: FFI bindings (arxos_mobile.udl) must be created first
echo       iOS builds are not supported on Windows
