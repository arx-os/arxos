#!/bin/bash
# Build ArxOS for Android on macOS
# This script builds the Rust library for Android using cargo-ndk

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building ArxOS for Android on macOS...${NC}"

# Check for cargo-ndk
if ! command -v cargo-ndk &> /dev/null; then
    echo -e "${YELLOW}⚠️  cargo-ndk not found${NC}"
    echo "Install with: cargo install cargo-ndk"
    exit 1
fi

# Detect NDK path (supports both Apple Silicon and Intel Mac)
if [ -d "/opt/homebrew/share/android-ndk" ]; then
    export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"
elif [ -d "/usr/local/share/android-ndk" ]; then
    export ANDROID_NDK_HOME="/usr/local/share/android-ndk"
elif [ -n "$ANDROID_NDK_HOME" ]; then
    # Use provided environment variable
    :
else
    echo -e "${YELLOW}⚠️  Android NDK not found at default locations${NC}"
    echo "Checking if Homebrew can install it..."
    if command -v brew &> /dev/null; then
        echo -e "${BLUE}📦 Installing Android NDK via Homebrew...${NC}"
        brew install android-ndk
        # Try to detect where Homebrew installed it
        if [ -d "/opt/homebrew/share/android-ndk" ]; then
            export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"
        elif [ -d "/usr/local/share/android-ndk" ]; then
            export ANDROID_NDK_HOME="/usr/local/share/android-ndk"
        else
            echo -e "${RED}❌ Could not find NDK after installation${NC}"
            echo "Please set ANDROID_NDK_HOME manually"
            exit 1
        fi
    else
        echo -e "${RED}❌ Homebrew not found and ANDROID_NDK_HOME not set${NC}"
        echo "Please install Android NDK or set ANDROID_NDK_HOME"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Using NDK at: $ANDROID_NDK_HOME${NC}"

# Create output directories
mkdir -p android/app/src/main/jniLibs/arm64-v8a
mkdir -p android/app/src/main/jniLibs/armeabi-v7a

# Build for ARM64
echo -e "${BLUE}📱 Building for ARM64...${NC}"
if cargo ndk -t arm64-v8a -o android/app/src/main/jniLibs build --release --lib --features android 2>/dev/null; then
    echo -e "${GREEN}✅ ARM64 build successful${NC}"
elif cargo ndk -t arm64-v8a -o android/app/src/main/jniLibs build --release --lib 2>/dev/null; then
    echo -e "${YELLOW}⚠️  ARM64 build successful (without android feature)${NC}"
else
    echo -e "${RED}❌ ARM64 build failed${NC}"
    exit 1
fi

# Build for ARMv7
echo -e "${BLUE}📱 Building for ARMv7...${NC}"
if cargo ndk -t armeabi-v7a -o android/app/src/main/jniLibs build --release --lib --features android 2>/dev/null; then
    echo -e "${GREEN}✅ ARMv7 build successful${NC}"
elif cargo ndk -t armeabi-v7a -o android/app/src/main/jniLibs build --release --lib 2>/dev/null; then
    echo -e "${YELLOW}⚠️  ARMv7 build successful (without android feature)${NC}"
else
    echo -e "${RED}❌ ARMv7 build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Android build complete!${NC}"
echo ""
echo -e "${BLUE}📋 Built libraries:${NC}"
if find android/app/src/main/jniLibs -name "*.so" 2>/dev/null | grep -q .; then
    find android/app/src/main/jniLibs -name "*.so" 2>/dev/null | while read -r file; do
        echo -e "  ${GREEN}✓${NC} $file"
    done
else
    echo -e "  ${YELLOW}⚠️  No .so files found${NC}"
fi

echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "  1. Build the Android app: cd android && ./gradlew build"
echo "  2. Or use Android Studio to build and test"

