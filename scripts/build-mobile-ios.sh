#!/bin/bash
# Build ArxOS for iOS
# This script builds the Rust library for iOS and prepares it for Xcode integration

set -e

echo "🚀 Building ArxOS for iOS..."

# Create output directory
mkdir -p ios/build

# Build for iOS architectures
echo "📱 Building for iOS devices (arm64)..."
cargo build --target aarch64-apple-ios --release

echo "📱 Building for iOS simulator (x86_64)..."
cargo build --target x86_64-apple-ios --release

echo "📱 Building for iOS simulator (arm64)..."
cargo build --target aarch64-apple-ios-sim --release

echo "📦 Creating universal framework..."
# TODO: Create iOS framework from compiled libraries
# This would involve:
# 1. Creating a framework structure
# 2. Combining arm64 and x86_64 libraries
# 3. Creating headers
# 4. Creating module map

echo "✅ iOS build complete!"
echo "📋 Next steps:"
echo "  1. Open ios/ArxOSMobile.xcodeproj in Xcode"
echo "  2. Link the compiled .a library to the project"
echo "  3. Update bridging header"
echo "  4. Test the app"

