#!/bin/bash
# ArxOS Mobile Build Script
# Builds Rust library for iOS and Android targets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOBILE_CRATE="$PROJECT_ROOT/crates/arxos-mobile"
TARGET_DIR="$PROJECT_ROOT/target"

# iOS Configuration
IOS_TARGETS=(
    "aarch64-apple-ios"
    "aarch64-apple-ios-sim"
    "x86_64-apple-ios"
)

# Android Configuration
ANDROID_TARGETS=(
    "aarch64-linux-android"
    "armv7-linux-androideabi"
    "i686-linux-android"
    "x86_64-linux-android"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install iOS targets
install_ios_targets() {
    print_status "Installing iOS targets..."
    
    for target in "${IOS_TARGETS[@]}"; do
        if rustup target list --installed | grep -q "$target"; then
            print_status "Target $target already installed"
        else
            print_status "Installing target $target"
            rustup target add "$target"
        fi
    done
}

# Function to install Android targets
install_android_targets() {
    print_status "Installing Android targets..."
    
    for target in "${ANDROID_TARGETS[@]}"; do
        if rustup target list --installed | grep -q "$target"; then
            print_status "Target $target already installed"
        else
            print_status "Installing target $target"
            rustup target add "$target"
        fi
    done
}

# Function to build iOS library
build_ios() {
    print_status "Building iOS library..."
    
    cd "$MOBILE_CRATE"
    
    # Build for iOS device
    print_status "Building for iOS device (aarch64-apple-ios)..."
    cargo build --release --target aarch64-apple-ios --features ios
    
    # Build for iOS simulator
    print_status "Building for iOS simulator (aarch64-apple-ios-sim)..."
    cargo build --release --target aarch64-apple-ios-sim --features ios
    
    # Build for iOS simulator (x86_64)
    print_status "Building for iOS simulator x86_64..."
    cargo build --release --target x86_64-apple-ios --features ios
    
    # Create universal library for iOS
    print_status "Creating universal iOS library..."
    mkdir -p "$TARGET_DIR/universal/ios"
    
    lipo -create \
        "$TARGET_DIR/aarch64-apple-ios/release/libarxos_mobile.a" \
        "$TARGET_DIR/aarch64-apple-ios-sim/release/libarxos_mobile.a" \
        "$TARGET_DIR/x86_64-apple-ios/release/libarxos_mobile.a" \
        -output "$TARGET_DIR/universal/ios/libarxos_mobile.a"
    
    print_success "iOS library built successfully"
}

# Function to build Android library
build_android() {
    print_status "Building Android library..."
    
    cd "$MOBILE_CRATE"
    
    # Build for Android targets
    for target in "${ANDROID_TARGETS[@]}"; do
        print_status "Building for Android target: $target"
        cargo build --release --target "$target" --features android
    done
    
    # Create Android AAR structure
    print_status "Creating Android AAR structure..."
    mkdir -p "$TARGET_DIR/universal/android/jni"
    
    # Copy libraries for different architectures
    mkdir -p "$TARGET_DIR/universal/android/jni/arm64-v8a"
    mkdir -p "$TARGET_DIR/universal/android/jni/armeabi-v7a"
    mkdir -p "$TARGET_DIR/universal/android/jni/x86"
    mkdir -p "$TARGET_DIR/universal/android/jni/x86_64"
    
    cp "$TARGET_DIR/aarch64-linux-android/release/libarxos_mobile.so" "$TARGET_DIR/universal/android/jni/arm64-v8a/"
    cp "$TARGET_DIR/armv7-linux-androideabi/release/libarxos_mobile.so" "$TARGET_DIR/universal/android/jni/armeabi-v7a/"
    cp "$TARGET_DIR/i686-linux-android/release/libarxos_mobile.so" "$TARGET_DIR/universal/android/jni/x86/"
    cp "$TARGET_DIR/x86_64-linux-android/release/libarxos_mobile.so" "$TARGET_DIR/universal/android/jni/x86_64/"
    
    print_success "Android library built successfully"
}

# Function to generate UniFFI bindings
generate_bindings() {
    print_status "Generating UniFFI bindings..."
    
    cd "$MOBILE_CRATE"
    
    # Generate Swift bindings
    print_status "Generating Swift bindings..."
    uniffi-bindgen generate --library "$TARGET_DIR/debug/libarxos_mobile.dylib" --language swift --out-dir "$TARGET_DIR/bindings/swift"
    
    # Generate Kotlin bindings
    print_status "Generating Kotlin bindings..."
    uniffi-bindgen generate --library "$TARGET_DIR/debug/libarxos_mobile.so" --language kotlin --out-dir "$TARGET_DIR/bindings/kotlin"
    
    print_success "UniFFI bindings generated successfully"
}

# Function to clean build artifacts
clean() {
    print_status "Cleaning build artifacts..."
    
    cd "$MOBILE_CRATE"
    cargo clean
    
    rm -rf "$TARGET_DIR/universal"
    rm -rf "$TARGET_DIR/bindings"
    
    print_success "Build artifacts cleaned"
}

# Function to show help
show_help() {
    echo "ArxOS Mobile Build Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  ios          Build iOS library"
    echo "  android      Build Android library"
    echo "  all          Build both iOS and Android libraries"
    echo "  bindings     Generate UniFFI bindings"
    echo "  install      Install required Rust targets"
    echo "  clean        Clean build artifacts"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 ios       # Build iOS library only"
    echo "  $0 all       # Build both iOS and Android libraries"
    echo "  $0 clean     # Clean all build artifacts"
}

# Main script logic
main() {
    # Check if we're in the right directory
    if [[ ! -f "$MOBILE_CRATE/Cargo.toml" ]]; then
        print_error "Mobile crate not found at $MOBILE_CRATE"
        exit 1
    fi
    
    # Check if Rust is installed
    if ! command_exists rustup; then
        print_error "rustup is not installed. Please install Rust first."
        exit 1
    fi
    
    # Check if cargo is installed
    if ! command_exists cargo; then
        print_error "cargo is not installed. Please install Rust first."
        exit 1
    fi
    
    # Parse command line arguments
    case "${1:-help}" in
        "ios")
            install_ios_targets
            build_ios
            ;;
        "android")
            install_android_targets
            build_android
            ;;
        "all")
            install_ios_targets
            install_android_targets
            build_ios
            build_android
            ;;
        "bindings")
            generate_bindings
            ;;
        "install")
            install_ios_targets
            install_android_targets
            ;;
        "clean")
            clean
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
