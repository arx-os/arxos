@echo off
REM ArxOS Mobile Build Script for Windows
REM Builds Rust library for iOS and Android targets

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_ROOT=%~dp0..
set MOBILE_CRATE=%PROJECT_ROOT%\crates\arxos-mobile
set TARGET_DIR=%PROJECT_ROOT%\target

REM iOS Configuration
set IOS_TARGETS=aarch64-apple-ios aarch64-apple-ios-sim x86_64-apple-ios

REM Android Configuration  
set ANDROID_TARGETS=aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android

REM Function to print status
:print_status
echo [INFO] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

REM Function to check if command exists
:command_exists
where %1 >nul 2>&1
if %errorlevel% equ 0 (
    exit /b 0
) else (
    exit /b 1
)

REM Function to install targets
:install_targets
call :print_status "Installing Rust targets..."
for %%t in (%IOS_TARGETS%) do (
    rustup target add %%t
    if !errorlevel! neq 0 (
        call :print_error "Failed to install target %%t"
        exit /b 1
    )
)
for %%t in (%ANDROID_TARGETS%) do (
    rustup target add %%t
    if !errorlevel! neq 0 (
        call :print_error "Failed to install target %%t"
        exit /b 1
    )
)
call :print_success "All targets installed successfully"
goto :eof

REM Function to build iOS library
:build_ios
call :print_status "Building iOS library..."
cd /d "%MOBILE_CRATE%"

REM Build for iOS device
call :print_status "Building for iOS device (aarch64-apple-ios)..."
cargo build --release --target aarch64-apple-ios --features ios
if !errorlevel! neq 0 (
    call :print_error "Failed to build for iOS device"
    exit /b 1
)

REM Build for iOS simulator
call :print_status "Building for iOS simulator (aarch64-apple-ios-sim)..."
cargo build --release --target aarch64-apple-ios-sim --features ios
if !errorlevel! neq 0 (
    call :print_error "Failed to build for iOS simulator"
    exit /b 1
)

REM Build for iOS simulator x86_64
call :print_status "Building for iOS simulator x86_64..."
cargo build --release --target x86_64-apple-ios --features ios
if !errorlevel! neq 0 (
    call :print_error "Failed to build for iOS simulator x86_64"
    exit /b 1
)

REM Create universal library directory
if not exist "%TARGET_DIR%\universal\ios" mkdir "%TARGET_DIR%\universal\ios"

REM Note: lipo command is macOS only, so we'll skip universal library creation on Windows
call :print_success "iOS library built successfully (universal library creation skipped on Windows)"
goto :eof

REM Function to build Android library
:build_android
call :print_status "Building Android library..."
cd /d "%MOBILE_CRATE%"

REM Build for Android targets
for %%t in (%ANDROID_TARGETS%) do (
    call :print_status "Building for Android target: %%t"
    cargo build --release --target %%t --features android
    if !errorlevel! neq 0 (
        call :print_error "Failed to build for Android target %%t"
        exit /b 1
    )
)

REM Create Android AAR structure
call :print_status "Creating Android AAR structure..."
if not exist "%TARGET_DIR%\universal\android\jni" mkdir "%TARGET_DIR%\universal\android\jni"
if not exist "%TARGET_DIR%\universal\android\jni\arm64-v8a" mkdir "%TARGET_DIR%\universal\android\jni\arm64-v8a"
if not exist "%TARGET_DIR%\universal\android\jni\armeabi-v7a" mkdir "%TARGET_DIR%\universal\android\jni\armeabi-v7a"
if not exist "%TARGET_DIR%\universal\android\jni\x86" mkdir "%TARGET_DIR%\universal\android\jni\x86"
if not exist "%TARGET_DIR%\universal\android\jni\x86_64" mkdir "%TARGET_DIR%\universal\android\jni\x86_64"

REM Copy libraries for different architectures
copy "%TARGET_DIR%\aarch64-linux-android\release\libarxos_mobile.so" "%TARGET_DIR%\universal\android\jni\arm64-v8a\"
copy "%TARGET_DIR%\armv7-linux-androideabi\release\libarxos_mobile.so" "%TARGET_DIR%\universal\android\jni\armeabi-v7a\"
copy "%TARGET_DIR%\i686-linux-android\release\libarxos_mobile.so" "%TARGET_DIR%\universal\android\jni\x86\"
copy "%TARGET_DIR%\x86_64-linux-android\release\libarxos_mobile.so" "%TARGET_DIR%\universal\android\jni\x86_64\"

call :print_success "Android library built successfully"
goto :eof

REM Function to generate UniFFI bindings
:generate_bindings
call :print_status "Generating UniFFI bindings..."
cd /d "%MOBILE_CRATE%"

REM Generate Swift bindings
call :print_status "Generating Swift bindings..."
if not exist "%TARGET_DIR%\bindings\swift" mkdir "%TARGET_DIR%\bindings\swift"
uniffi-bindgen generate --library "%TARGET_DIR%\debug\libarxos_mobile.dll" --language swift --out-dir "%TARGET_DIR%\bindings\swift"
if !errorlevel! neq 0 (
    call :print_error "Failed to generate Swift bindings"
    exit /b 1
)

REM Generate Kotlin bindings
call :print_status "Generating Kotlin bindings..."
if not exist "%TARGET_DIR%\bindings\kotlin" mkdir "%TARGET_DIR%\bindings\kotlin"
uniffi-bindgen generate --library "%TARGET_DIR%\debug\libarxos_mobile.dll" --language kotlin --out-dir "%TARGET_DIR%\bindings\kotlin"
if !errorlevel! neq 0 (
    call :print_error "Failed to generate Kotlin bindings"
    exit /b 1
)

call :print_success "UniFFI bindings generated successfully"
goto :eof

REM Function to clean build artifacts
:clean
call :print_status "Cleaning build artifacts..."
cd /d "%MOBILE_CRATE%"
cargo clean

if exist "%TARGET_DIR%\universal" rmdir /s /q "%TARGET_DIR%\universal"
if exist "%TARGET_DIR%\bindings" rmdir /s /q "%TARGET_DIR%\bindings"

call :print_success "Build artifacts cleaned"
goto :eof

REM Function to show help
:show_help
echo ArxOS Mobile Build Script for Windows
echo.
echo Usage: %~nx0 [COMMAND]
echo.
echo Commands:
echo   ios          Build iOS library
echo   android      Build Android library  
echo   all          Build both iOS and Android libraries
echo   bindings     Generate UniFFI bindings
echo   install      Install required Rust targets
echo   clean        Clean build artifacts
echo   help         Show this help message
echo.
echo Examples:
echo   %~nx0 ios       # Build iOS library only
echo   %~nx0 all       # Build both iOS and Android libraries
echo   %~nx0 clean     # Clean all build artifacts
goto :eof

REM Main script logic
:main
REM Check if we're in the right directory
if not exist "%MOBILE_CRATE%\Cargo.toml" (
    call :print_error "Mobile crate not found at %MOBILE_CRATE%"
    exit /b 1
)

REM Check if Rust is installed
call :command_exists rustup
if !errorlevel! neq 0 (
    call :print_error "rustup is not installed. Please install Rust first."
    exit /b 1
)

REM Check if cargo is installed
call :command_exists cargo
if !errorlevel! neq 0 (
    call :print_error "cargo is not installed. Please install Rust first."
    exit /b 1
)

REM Parse command line arguments
if "%1"=="ios" (
    call :install_targets
    call :build_ios
) else if "%1"=="android" (
    call :install_targets
    call :build_android
) else if "%1"=="all" (
    call :install_targets
    call :build_ios
    call :build_android
) else if "%1"=="bindings" (
    call :generate_bindings
) else if "%1"=="install" (
    call :install_targets
) else if "%1"=="clean" (
    call :clean
) else if "%1"=="help" (
    call :show_help
) else if "%1"=="-h" (
    call :show_help
) else if "%1"=="--help" (
    call :show_help
) else if "%1"=="" (
    call :show_help
) else (
    call :print_error "Unknown command: %1"
    call :show_help
    exit /b 1
)

REM Run main function
call :main %*
