# Enable FFI Calls - After Build Succeeds

Once the build succeeds, we need to enable the actual Rust FFI calls.

## Step 1: Edit ArxOSCoreFFI.swift

Open: `ios/ArxOSMobile/ArxOSMobile/Services/ArxOSCoreFFI.swift`

### In `listEquipment()` function (around line 114):

**Change FROM:**
```swift
let result: Result<[Equipment], Error> = .success([])
```

**Change TO:**
```swift
let result = self.callFFI(function: arxos_list_equipment, 
                         input: buildingName, 
                         errorMessage: "Failed to list equipment")
```

### In `listRooms()` function (around line 88):

**Change FROM:**
```swift
let result: Result<[Room], Error> = .success([])
```

**Change TO:**
```swift
let result = self.callFFI(function: arxos_list_rooms, 
                         input: buildingName, 
                         errorMessage: "Failed to list rooms")
```

## Step 2: Rebuild

Press **Cmd+B** again to rebuild with the new FFI calls enabled.

## Step 3: Create Test Data

The app needs building data to display. Create a test building:

```bash
mkdir -p test_ios_building
cd test_ios_building
git init

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

## Step 4: Run the App

1. Select a simulator (e.g., iPhone 15)
2. Press **Cmd+R** (or Product → Run)
3. Navigate to Equipment List view
4. You should see your test equipment!

## Expected Result

When you open the Equipment List:
- ✅ Equipment list loads (may be empty if no data)
- ✅ No crashes
- ✅ Console shows FFI calls being made

## Troubleshooting

### App runs but shows empty list
→ Expected! The app doesn't have building data yet. The FFI calls are working, just no data to show.

### App crashes on launch
→ Check console for error messages. Common issues:
- JSON parsing errors
- Memory management issues
- Missing building data

Let me know what happens!

