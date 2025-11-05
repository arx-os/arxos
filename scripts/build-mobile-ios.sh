#!/bin/bash
# Build ArxOS for iOS
# This script builds the Rust library for iOS and creates an XCFramework

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building ArxOS for iOS...${NC}"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${YELLOW}⚠️  iOS builds require macOS. Skipping...${NC}"
    exit 0
fi

# Set up iOS build environment
if [ -z "$DEVELOPER_DIR" ]; then
    if [ -d "/Applications/Xcode.app/Contents/Developer" ]; then
        export DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"
        echo -e "${BLUE}📦 Set DEVELOPER_DIR to default Xcode location${NC}"
    else
        echo -e "${YELLOW}⚠️  Xcode not found at default location. Please set DEVELOPER_DIR environment variable.${NC}"
    fi
fi

# Set iOS deployment target
export IPHONEOS_DEPLOYMENT_TARGET=${IPHONEOS_DEPLOYMENT_TARGET:-17.0}

# Create output directories
mkdir -p ios/build
mkdir -p ios/build/lib

# Check for rustup
if ! command -v rustup &> /dev/null; then
    echo -e "${RED}❌ rustup not found. Please install Rust toolchain.${NC}"
    exit 1
fi

# Install iOS targets if not already installed
echo -e "${BLUE}📦 Checking iOS targets...${NC}"
IOS_TARGETS=("aarch64-apple-ios" "aarch64-apple-ios-sim" "x86_64-apple-ios")
for target in "${IOS_TARGETS[@]}"; do
    if ! rustup target list --installed | grep -q "$target"; then
        echo -e "${BLUE}Installing target: $target${NC}"
        rustup target add "$target"
    fi
done

# Build for iOS architectures
echo -e "${BLUE}📱 Building for iOS devices (arm64)...${NC}"
cargo build --target aarch64-apple-ios --release --lib

echo -e "${BLUE}📱 Building for iOS simulator (x86_64)...${NC}"
cargo build --target x86_64-apple-ios --release --lib

echo -e "${BLUE}📱 Building for iOS simulator (arm64)...${NC}"
cargo build --target aarch64-apple-ios-sim --release --lib

# Copy libraries to build directory
echo -e "${BLUE}📦 Copying libraries...${NC}"
cp target/aarch64-apple-ios/release/libarxos.a ios/build/lib/libarxos-device.a
cp target/x86_64-apple-ios/release/libarxos.a ios/build/lib/libarxos-simulator-x86_64.a
cp target/aarch64-apple-ios-sim/release/libarxos.a ios/build/lib/libarxos-simulator-aarch64.a

# Create universal library for simulator by combining architectures
echo -e "${BLUE}📦 Creating universal simulator library...${NC}"
if ! command -v lipo &> /dev/null; then
    echo -e "${YELLOW}❌ lipo not found. Xcode Command Line Tools required.${NC}"
    echo "Install with: xcode-select --install"
    exit 1
fi
lipo -create ios/build/lib/libarxos-simulator-x86_64.a ios/build/lib/libarxos-simulator-aarch64.a -output ios/build/lib/libarxos-simulator.a

# Create XCFramework structure
echo -e "${BLUE}📦 Creating XCFramework...${NC}"
XCFRAMEWORK_DIR="ios/build/ArxOS.xcframework"
rm -rf "$XCFRAMEWORK_DIR"
mkdir -p "$XCFRAMEWORK_DIR"

# Create headers directory
mkdir -p "$XCFRAMEWORK_DIR/Headers"
cp include/arxos_mobile.h "$XCFRAMEWORK_DIR/Headers/"

# Copy device library
mkdir -p "$XCFRAMEWORK_DIR/ios-arm64"
cp ios/build/lib/libarxos-device.a "$XCFRAMEWORK_DIR/ios-arm64/libarxos.a"

# Copy simulator library
mkdir -p "$XCFRAMEWORK_DIR/ios-arm64_x86_64-simulator"
cp ios/build/lib/libarxos-simulator.a "$XCFRAMEWORK_DIR/ios-arm64_x86_64-simulator/libarxos.a"

# Create Info.plist for XCFramework
cat > "$XCFRAMEWORK_DIR/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AvailableLibraries</key>
    <array>
        <dict>
            <key>LibraryIdentifier</key>
            <string>ios-arm64</string>
            <key>LibraryPath</key>
            <string>libarxos.a</string>
            <key>SupportedArchitectures</key>
            <array>
                <string>arm64</string>
            </array>
            <key>SupportedPlatform</key>
            <string>ios</string>
        </dict>
        <dict>
            <key>LibraryIdentifier</key>
            <string>ios-arm64_x86_64-simulator</string>
            <key>LibraryPath</key>
            <string>libarxos.a</string>
            <key>SupportedArchitectures</key>
            <array>
                <string>arm64</string>
                <string>x86_64</string>
            </array>
            <key>SupportedPlatform</key>
            <string>ios</string>
            <key>SupportedPlatformVariant</key>
            <string>simulator</string>
        </dict>
    </array>
    <key>CFBundlePackageType</key>
    <string>XFW</string>
    <key>XCFrameworkFormatVersion</key>
    <string>1.0</string>
</dict>
</plist>
EOF

echo -e "${GREEN}✅ iOS build complete!${NC}"
echo ""
echo "📦 Output: $XCFRAMEWORK_DIR"
echo ""
echo "📋 Next steps:"
echo "  1. Open ios/ArxOSMobile.xcodeproj in Xcode"
echo "  2. Add $XCFRAMEWORK_DIR as a framework dependency"
echo "  3. Update bridging header: ios/ArxOSMobile/include/arxos_bridge.h"
echo "  4. Build and test the app"
echo ""
echo "To link the framework in Xcode:"
echo "  1. Select your target in Xcode"
echo "  2. Go to 'General' → 'Frameworks, Libraries, and Embedded Content'"
echo "  3. Click '+' and 'Add Files...'"
echo "  4. Navigate to ios/build/ and select ArxOS.xcframework"

