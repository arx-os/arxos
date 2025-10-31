#!/bin/bash
# Build ArxOS for Android on macOS
# This script builds the Rust library for Android using cargo-ndk

set -e

echo "🚀 Building ArxOS for Android on macOS..."

# Set Android NDK path
export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"

if [ ! -d "$ANDROID_NDK_HOME" ]; then
    echo "❌ Android NDK not found at $ANDROID_NDK_HOME"
    echo "📦 Installing via Homebrew..."
    brew install android-ndk
    export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"
fi

echo "✅ Using NDK at: $ANDROID_NDK_HOME"

# Create output directories
mkdir -p android/app/src/main/jniLibs/arm64-v8a
mkdir -p android/app/src/main/jniLibs/armeabi-v7a

# Build for ARM64
echo "📱 Building for ARM64..."
cargo ndk -t arm64-v8a -o android/app/src/main/jniLibs build --release --lib --features android || {
    echo "⚠️  ARM64 build failed, trying without JNI..."
    cargo ndk -t arm64-v8a -o android/app/src/main/jniLibs build --release --lib
}

# Build for ARMv7
echo "📱 Building for ARMv7..."
cargo ndk -t armeabi-v7a -o android/app/src/main/jniLibs build --release --lib --features android || {
    echo "⚠️  ARMv7 build failed, trying without JNI..."
    cargo ndk -t armeabi-v7a -o android/app/src/main/jniLibs build --release --lib
}

echo ""
echo "✅ Android build complete!"
echo "📋 Built libraries:"
find android/app/src/main/jniLibs -name "*.so" 2>/dev/null || echo "   No .so files found"

echo ""
echo "📋 Next steps:"
echo "  1. Build the Android app using: cd android && ./gradlew build"
echo "  2. Or use Android Studio to build and test"

