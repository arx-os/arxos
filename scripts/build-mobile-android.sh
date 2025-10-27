#!/bin/bash
# Build ArxOS for Android
# This script builds the Rust library for Android using NDK

set -e

echo "🚀 Building ArxOS for Android..."

# Android NDK path (update this for your system)
NDK_PATH="${ANDROID_NDK_HOME:-$HOME/Android/Sdk/ndk-bundle}"

if [ ! -d "$NDK_PATH" ]; then
    echo "❌ Android NDK not found at $NDK_PATH"
    echo "Please set ANDROID_NDK_HOME environment variable"
    exit 1
fi

echo "📱 Building for Android (armv7)..."
cargo build --target armv7-linux-androideabi --release

echo "📱 Building for Android (aarch64)..."
cargo build --target aarch64-linux-android --release

echo "📱 Building for Android (x86)..."
cargo build --target i686-linux-android --release

echo "📱 Building for Android (x86_64)..."
cargo build --target x86_64-linux-android --release

echo "✅ Android build complete!"
echo "📋 Next steps:"
echo "  1. Copy .so files to android/app/src/main/jniLibs/"
echo "  2. Update android/app/build.gradle"
echo "  3. Rebuild the Android app"
echo "  4. Test the app"

