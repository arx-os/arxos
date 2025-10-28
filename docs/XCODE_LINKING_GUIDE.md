# Linking ArxOS.xcframework in Xcode

## Method 1: Target Settings (Recommended)

### Step 1: Select the Target
1. Open `ios/ArxOSMobile.xcodeproj` in Xcode
2. In the **Project Navigator** (left sidebar), click on the **project name** at the top (not the folder, but the blue icon)
3. In the main editor area, you'll see your project and targets
4. Under **TARGETS**, select **ArxOSMobile** (the iOS app target)

### Step 2: Navigate to Framework Settings
**Option A - Tab at the top:**
- Click the **"General"** tab at the top of the target settings
- Scroll down to find **"Frameworks, Libraries, and Embedded Content"**

**Option B - If "General" tab is not visible:**
- Look for **"Build Settings"** or **"Build Phases"** tabs
- We'll add the framework in **"Build Phases"** instead (see Method 2)

### Step 3: Add the Framework
1. Under **"Frameworks, Libraries, and Embedded Content"**
2. Click the **"+"** button (plus icon)
3. Choose **"Add Other..."** → **"Add Files..."**
4. Navigate to: `ios/build/ArxOS.xcframework`
5. Click **"Add"**
6. Set the status to **"Do Not Embed"** (important!)

---

## Method 2: Build Phases (Alternative)

If you can't find the "General" tab, use Build Phases:

### Step 1: Select Target
- Select **ArxOSMobile** target in the project navigator

### Step 2: Add to "Link Binary With Libraries"
1. Click **"Build Phases"** tab
2. Expand **"Link Binary With Libraries"**
3. Click the **"+"** button
4. Click **"Add Other..."** → **"Add Files..."**
5. Navigate to: `ios/build/ArxOS.xcframework`
6. Click **"Add"**

### Step 3: Add Framework Search Path
1. Still in **"Build Phases"**, look for the **"+"** button at the top
2. Click it and select **"New Copy Files Phase"** (if needed)
3. Or go to **"Build Settings"** tab
4. Search for **"Framework Search Paths"**
5. Click the **"+"** to add a new path
6. Enter: `$(PROJECT_DIR)/../ios/build`
7. Make sure it's marked as **Recursive**

---

## Method 3: Build Settings (Manual Configuration)

If the above methods don't work, configure manually:

### Step 1: Select Target
- Select **ArxOSMobile** target

### Step 2: Go to Build Settings
- Click **"Build Settings"** tab

### Step 3: Add Framework Search Path
1. Search for **"Framework Search Paths"** in the search box
2. Double-click the value field (next to "Debug" and "Release")
3. Click **"+"** to add: `$(PROJECT_DIR)/../ios/build`
4. Make sure **"Recursive"** is checked

### Step 4: Add Other Linker Flags (if needed)
1. Search for **"Other Linker Flags"**
2. Add: `-framework ArxOS` or `-L$(PROJECT_DIR)/../ios/build -larxos`

### Step 5: Configure Bridging Header
1. Search for **"Objective-C Bridging Header"**
2. Set to: `$(PROJECT_DIR)/ArxOSMobile/include/arxos_bridge.h`

---

## Method 4: Drag and Drop (Easiest)

### Step 1: Show Project Navigator
- Make sure the left sidebar is visible (File Navigator)

### Step 2: Find the Framework
- In Finder, navigate to `ios/build/ArxOS.xcframework`

### Step 3: Drag to Xcode
1. Drag the `ArxOS.xcframework` folder from Finder
2. Drop it into the Xcode project navigator, anywhere in your project structure
3. When prompted, make sure:
   - **"Copy items if needed"** is **UNCHECKED** (we want to reference it)
   - **"Create groups"** is selected
   - **Target "ArxOSMobile"** is **CHECKED**
4. Click **"Finish"**

### Step 4: Verify in Build Phases
1. Select your target
2. Go to **"Build Phases"**
3. Expand **"Link Binary With Libraries"**
4. You should see `ArxOS.xcframework` listed
5. If it shows "Embed & Sign", change it to **"Do Not Embed"**

---

## Method 5: Directly Edit project.pbxproj (Advanced)

If none of the above work, we can edit the Xcode project file directly using a script.

See `scripts/link-framework.sh` for an automated script to do this.

---

## Verification

After adding the framework, verify it's linked:

1. **Build the project**: Press `Cmd+B` or Product → Build
2. **Check for errors**: You should see no linker errors
3. **Verify framework appears**:
   - Select target → Build Phases → Link Binary With Libraries
   - You should see `ArxOS.xcframework`
   - Status should be **"Do Not Embed"**

## Common Issues

### Issue: "No such module 'ArxOS'"
**Solution**: The framework isn't in the framework search path. Use Method 3 to add the path.

### Issue: "Undefined symbols" errors
**Solution**: Check that the framework is added to "Link Binary With Libraries" in Build Phases.

### Issue: Can't find "General" tab
**Solution**: Use Method 2 (Build Phases) or Method 4 (Drag and Drop).

### Issue: Framework not found
**Solution**: Make sure you're using the absolute path or `$(PROJECT_DIR)` variable.

---

## Quick Reference

**Framework Location**: `ios/build/ArxOS.xcframework`  
**Framework Size**: ~141 MB total (device + simulators)  
**Embed Setting**: **"Do Not Embed"** (static library, not dynamic)  
**Bridging Header**: `$(PROJECT_DIR)/ArxOSMobile/include/arxos_bridge.h`

---

## Still Having Issues?

Try these commands in Terminal to verify the framework exists:

```bash
# Check framework exists
ls -la ios/build/ArxOS.xcframework/

# Check library files
ls -la ios/build/ArxOS.xcframework/ios-arm64/
ls -la ios/build/ArxOS.xcframework/ios-arm64_x86_64-simulator/

# Verify structure
tree ios/build/ArxOS.xcframework/ -L 2
```

If the framework is missing, rebuild it:
```bash
./scripts/build-mobile-ios.sh
```

