#!/bin/bash
# ArxOS Mobile Build Script
# Note: FFI bindings (arxos_mobile.udl) need to be created before this script can build mobile libraries

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if arxos_mobile.udl file exists
if [ ! -f "src/arxos_mobile.udl" ]; then
    print_error "FFI bindings not found!"
    echo ""
    echo "To enable mobile builds:"
    echo "  1. Create arxos_mobile.udl file with UniFFI definitions"
    echo "  2. Add UniFFI build configuration to Cargo.toml"
    echo "  3. Run this script again"
    echo ""
    echo "For now, mobile apps run in standalone mode with graceful fallbacks."
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_status "Mobile FFI bindings detected"
print_status "Building Rust library for iOS and Android..."

# iOS Targets
IOS_TARGETS=(
    "aarch64-apple-ios"
    "aarch64-apple-ios-sim"
    "x86_64-apple-ios"
)

# Android Targets
ANDROID_TARGETS=(
    "aarch64-linux-android"
    "armv7-linux-androideabi"
    "i686-linux-android"
    "x86_64-linux-android"
)

# Function to install targets
install_targets() {
    local targets=("$@")
    for target in "${targets[@]}"; do
        if rustup target list --installed | grep -q "$target"; then
            print_status "Target $target already installed"
        else
            print_status "Installing target $target"
            rustup target add "$target"
        fi
    done
}

# Main build logic
main() {
    case "${1:-all}" in
        ios)
            print_status "Building iOS..."
            install_targets "${IOS_TARGETS[@]}"
            print_warning "iOS build not yet implemented (requires FFI bindings)"
            ;;
        android)
            print_status "Building Android..."
            install_targets "${ANDROID_TARGETS[@]}"
            print_warning "Android build not yet implemented (requires FFI bindings)"
            ;;
        install)
            print_status "Installing all targets..."
            install_targets "${IOS_TARGETS[@]}"
            install_targets "${ANDROID_TARGETS[@]}"
            print_success "All targets installed"
            ;;
        *)
            echo "Mobile build script for ArxOS"
            echo ""
            echo "Usage: $0 [ios|android|install|help]"
            echo ""
            echo "Commands:"
            echo "  ios      - Build for iOS"
            echo "  android  - Build for Android"
            echo "  install  - Install Rust targets"
            echo "  help     - Show this help"
            echo ""
            echo "Note: FFI bindings (arxos_mobile.udl) must be created first"
            ;;
    esac
}

main "$@"
