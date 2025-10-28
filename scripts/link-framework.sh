#!/bin/bash
# Script to automatically link ArxOS.xcframework in Xcode project
# This creates a backup before modifying the project file

set -e

PROJECT_FILE="ios/ArxOSMobile.xcodeproj/project.pbxproj"
FRAMEWORK_PATH="ios/build/ArxOS.xcframework"
FRAMEWORK_NAME="ArxOS.xcframework"

# Check if framework exists
if [ ! -d "$FRAMEWORK_PATH" ]; then
    echo "❌ Framework not found at: $FRAMEWORK_PATH"
    echo "💡 Run: ./scripts/build-mobile-ios.sh first"
    exit 1
fi

# Check if project file exists
if [ ! -f "$PROJECT_FILE" ]; then
    echo "❌ Xcode project not found at: $PROJECT_FILE"
    exit 1
fi

# Create backup
backup_file="${PROJECT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$PROJECT_FILE" "$backup_file"
echo "✅ Created backup: $backup_file"

# Extract framework UUID (Xcode needs this)
FRAMEWORK_UUID=$(grep -o '"framework".*' "$PROJECT_FILE" | head -1 || echo "")

# Check if framework is already in the project
if grep -q "$FRAMEWORK_NAME" "$PROJECT_FILE"; then
    echo "⚠️  Framework already linked in Xcode project"
    echo "💡 If you're seeing issues, try:"
    echo "   1. Select target in Xcode"
    echo "   2. Build Phases → Link Binary With Libraries"
    echo "   3. Verify ArxOS.xcframework is listed with 'Do Not Embed'"
    exit 0
fi

echo "📝 Framework found but not linked in Xcode project file"
echo ""
echo "⚠️  Manual linking required in Xcode:"
echo ""
echo "Recommended method (Drag & Drop):"
echo "  1. Open ios/ArxOSMobile.xcodeproj in Xcode"
echo "  2. In Project Navigator, find your project structure"
echo "  3. Drag $FRAMEWORK_PATH from Finder"
echo "  4. Drop into the project navigator in Xcode"
echo "  5. UNCHECK 'Copy items if needed'"
echo "  6. CHECK the target 'ArxOSMobile'"
echo "  7. Click 'Finish'"
echo "  8. In Build Phases → Link Binary, set to 'Do Not Embed'"
echo ""
echo "Alternative (direct file edit):"
echo "  Editing project.pbxproj is complex and error-prone."
echo "  Use Xcode's UI instead (drag & drop method above)."
echo ""
echo "See docs/XCODE_LINKING_GUIDE.md for detailed instructions."

