# Quick Start: Link Framework in Xcode

## Easiest Method: Drag & Drop ⭐ (Recommended)

### Step 1: Open Xcode Project
```bash
open ios/ArxOSMobile.xcodeproj
```

### Step 2: Show the Framework in Finder
```bash
open ios/build/
```
This opens Finder showing the `ArxOS.xcframework` folder.

### Step 3: Drag Into Xcode
1. Drag the `ArxOS.xcframework` folder from Finder
2. Drop it anywhere in your Xcode project navigator (left sidebar)
3. When the dialog appears:
   - ☐ **UNCHECK** "Copy items if needed"
   - ☑ Make sure "Create groups" is selected
   - ☑ Make sure "ArxOSMobile" target is **CHECKED**
4. Click **"Finish"**

### Step 4: Set to "Do Not Embed"
1. In Xcode project navigator, select the **project** (blue icon at top)
2. Select your **target** "ArxOSMobile" (under TARGETS)
3. Click **"Build Phases"** tab
4. Find **"Link Binary With Libraries"**
5. Find `ArxOS.xcframework` in the list
6. Click the **"Change"** button (or right-click)
7. Change from "Embed & Sign" to **"Do Not Embed"** ✅

### Step 5: Build
- Press **Cmd+B** (or Product → Build)
- Check for errors
- If you see "No such module" errors, see troubleshooting below

---

## Alternative: If "Build Phases" Tab is Hidden

Different Xcode versions have different layouts. Try:

1. Click the project in the navigator
2. Click your target "ArxOSMobile" 
3. Look for tabs: **"Info"**, **"Build Settings"**, **"Build Phases"**, or **"Signing & Capabilities"**
4. OR click anywhere in the main editor and look at top tabs

---

## What to Do After Linking

### 1. Enable FFI Calls
Edit `ios/ArxOSMobile/ArxOSMobile/Services/ArxOSCoreFFI.swift`:

Find this line (around line 114):
```swift
let result: Result<[Equipment], Error> = .success([])
```

Change to:
```swift
let result = self.callFFI(function: arxos_list_equipment, 
                         input: buildingName, 
                         errorMessage: "Failed to list equipment")
```

Do the same for other functions (listRooms, getRoom, etc.)

### 2. Create Test Data
```bash
# Create a test building with some equipment
mkdir -p test_ios_building
cd test_ios_building
git init

# Create a simple building YAML file
cat > building.yaml << 'EOF'
building:
  id: test-ios-1
  name: Test Building
  description: Test building for iOS
  version: 1.0

floors:
  - level: 1
    rooms:
      - name: Room 101
        id: room-101
        equipment: [equip-1, equip-2]
    equipment:
      - id: equip-1
        name: VAV-101
        equipment_type: HVAC
        status: Active
        position: {x: 10, y: 10, z: 0}
      - id: equip-2
        name: Light-101
        equipment_type: Electrical
        status: Active
        position: {x: 15, y: 15, z: 0}
EOF

cd ..
```

### 3. Build and Run
1. In Xcode, select a simulator (e.g., iPhone 15)
2. Press **Cmd+R** (or Product → Run)
3. The app should launch
4. Navigate to Equipment List view
5. You should see test equipment!

---

## Troubleshooting

### "No such module 'ArxOS'"
**Solution**: The framework isn't in the search path. Add this to Build Settings:

1. Select target → Build Settings
2. Search for "Framework Search Paths"
3. Click the "+" button
4. Add: `$(PROJECT_DIR)/../ios/build`
5. Make sure "Recursive" is checked

### "Undefined symbols"
**Solution**: The framework isn't being linked. Go to:
- Build Phases → Link Binary With Libraries
- Make sure `ArxOS.xcframework` is in the list

### "Could not find 'arxos_bridge.h'"
**Solution**: Add bridging header to Build Settings:

1. Build Settings → "Objective-C Bridging Header"
2. Set to: `ArxOSMobile/include/arxos_bridge.h`

### Still stuck?
See `docs/XCODE_LINKING_GUIDE.md` for all methods, or run:
```bash
./scripts/link-framework.sh
```

---

## Expected Result

After successfully linking and building:
- ✅ App builds without errors
- ✅ Equipment list view loads (may be empty initially)
- ✅ No linker errors in console
- ✅ Framework appears in build products

The app is now ready to call Rust FFI functions!

