#!/bin/bash
# Build ArxOS for Android
# This script builds the Rust library for Android using NDK and copies .so files

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building ArxOS for Android...${NC}"

# Check for Rust toolchain
if ! command -v rustup &> /dev/null; then
    echo -e "${RED}❌ rustup not found. Please install Rust toolchain.${NC}"
    exit 1
fi

# Android NDK path (update this for your system)
NDK_PATH="${ANDROID_NDK_HOME:-$HOME/Android/Sdk/ndk-bundle}"

if [ ! -d "$NDK_PATH" ]; then
    echo -e "${RED}❌ Android NDK not found at $NDK_PATH${NC}"
    echo "Please set ANDROID_NDK_HOME environment variable"
    echo "Example: export ANDROID_NDK_HOME=/path/to/android-ndk"
    exit 1
fi

echo -e "${BLUE}✅ Using NDK at: $NDK_PATH${NC}"

# Check if Cargo is configured for Android
if [ ! -f "$HOME/.cargo/config.toml" ] || ! grep -q "aarch64-linux-android" "$HOME/.cargo/config.toml" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Cargo not configured for Android cross-compilation${NC}"
    echo "Run: ./scripts/setup-android-cargo.sh"
    echo "Or configure manually in ~/.cargo/config.toml"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Android targets
TARGETS=(
    "armv7-linux-androideabi:armeabi-v7a"
    "aarch64-linux-android:arm64-v8a"
    "i686-linux-android:x86"
    "x86_64-linux-android:x86_64"
)

# Install Android targets if not already installed
echo -e "${BLUE}📦 Checking Android targets...${NC}"
for target_pair in "${TARGETS[@]}"; do
    target=$(echo "$target_pair" | cut -d: -f1)
    if ! rustup target list --installed | grep -q "$target"; then
        echo -e "${BLUE}Installing target: $target${NC}"
        rustup target add "$target"
    fi
done

# Create output directories
echo -e "${BLUE}📦 Creating output directories...${NC}"
mkdir -p android/app/src/main/jniLibs/armeabi-v7a
mkdir -p android/app/src/main/jniLibs/arm64-v8a
mkdir -p android/app/src/main/jniLibs/x86
mkdir -p android/app/src/main/jniLibs/x86_64

# Build for each architecture
for target_pair in "${TARGETS[@]}"; do
    target=$(echo "$target_pair" | cut -d: -f1)
    arch=$(echo "$target_pair" | cut -d: -f2)
    
    echo -e "${BLUE}📱 Building for Android ($arch)...${NC}"
    cargo build --target "$target" --release --lib
    
    # Copy .so file to jniLibs directory
    SO_FILE="target/$target/release/libarxos.so"
    if [ -f "$SO_FILE" ]; then
        cp "$SO_FILE" "android/app/src/main/jniLibs/$arch/"
        echo -e "${GREEN}✅ Copied to jniLibs/$arch/${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: $SO_FILE not found${NC}"
    fi
done

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

