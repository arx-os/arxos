#!/bin/bash

# Arxos Build Script
# Quick commands to build various components

set -e

echo "🏗️  Arxos Build System"
echo "====================="

case "$1" in
    "all")
        echo "Building all components..."
        cargo build --release
        echo "✅ Rust build complete"
        ;;
    
    "terminal")
        echo "Building terminal client..."
        cargo build --release --bin arxos
        echo "✅ Terminal client ready at target/release/arxos"
        ;;
    
    "embedded")
        echo "Building embedded library..."
        cargo build --release -p arxos-embedded --target thumbv7em-none-eabi
        echo "✅ Embedded library built"
        ;;
    
    "firmware")
        echo "Building ESP32 firmware..."
        cd firmware/esp32
        pio run
        echo "✅ Firmware ready for upload"
        ;;
    
    "test")
        echo "Running tests..."
        cargo test --all
        echo "✅ All tests passed"
        ;;
    
    "clean")
        echo "Cleaning build artifacts..."
        cargo clean
        rm -rf firmware/esp32/.pio
        echo "✅ Clean complete"
        ;;
    
    *)
        echo "Usage: ./build.sh [command]"
        echo ""
        echo "Commands:"
        echo "  all       - Build everything"
        echo "  terminal  - Build terminal client"
        echo "  embedded  - Build embedded library"
        echo "  firmware  - Build ESP32 firmware"
        echo "  test      - Run all tests"
        echo "  clean     - Clean build artifacts"
        echo ""
        echo "Example: ./build.sh terminal"
        ;;
esac