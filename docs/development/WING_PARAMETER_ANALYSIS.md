# Wing Parameter Analysis

**Date:** January 2025  
**Purpose:** Understand the purpose and implementation status of the `wing` parameter

---

## What is a "Wing"?

**Answer:** A **Wing** is a legitimate architectural concept in ArxOS representing an organizational grouping on a floor.

### Building Hierarchy

The intended hierarchy in ArxOS is:
```
Building → Floor → Wing → Room → Equipment
```

**Evidence:**
- `src/core/wing.rs` - `Wing` struct exists
- `src/core/floor.rs` - `Floor` has `wings: Vec<Wing>`
- `src/core/building.rs:11` - Documentation: "Building → Floor → Wing → Room → Equipment"
- `src/core/room.rs:11` - "Rooms are containers for equipment within wings on floors"

---

## The Problem: Wing Parameter is Broken

### Intended Behavior

When creating a room with `arx room create --wing "A"`, the room should:
1. Find or create wing "A" on the specified floor
2. Add the room to that wing
3. Preserve the wing information

### Actual Behavior

**Current Implementation (BROKEN):**
```rust
// src/commands/room_handlers.rs:115-159
// 1. Accepts wing parameter ✓
// 2. Prints wing in output message ✓
// 3. Creates room data ✓
// 4. Adds room directly to floor_data.rooms ✗ (bypasses wing!)
floor_data.rooms.push(room_data);
```

**The wing parameter is accepted but completely ignored!**

---

## Data Model Mismatch

### Core Model (In-Memory)
```rust
// src/core/floor.rs
pub struct Floor {
    pub wings: Vec<Wing>,  // Wings contain rooms
    // ...
}

// src/core/wing.rs
pub struct Wing {
    pub rooms: Vec<Room>,  // Rooms are in wings
    // ...
}
```

### YAML Model (Serialization)
```rust
// src/yaml/mod.rs
pub struct FloorData {
    pub rooms: Vec<RoomData>,  // Rooms stored directly on floor (flattened)
    // ...
}
```

**The YAML structure flattens the hierarchy** - it stores rooms directly on floors, losing wing information during serialization.

**Conversion Logic:**
```rust
// src/yaml/mod.rs:372-404
// When converting FROM core model TO YAML:
for floor in &building.floors {
    for wing in &floor.wings {        // Iterate wings
        for room in &wing.rooms {     // Get rooms from wings
            // Flatten all rooms into single Vec<RoomData>
            rooms.push(room_data);
        }
    }
}
// Result: All rooms from all wings on a floor become one flat list
```

**When converting FROM YAML TO core model:**
- Wings are lost (not restored from YAML)
- Rooms are added to default wing or floor directly

---

## Impact

### What Works
- ✅ Wings exist in core model
- ✅ Wing parameter is accepted by CLI
- ✅ Wing information is displayed in output

### What's Broken
- ❌ Wing parameter is ignored when creating rooms
- ❌ Rooms are added directly to floor, bypassing wing structure
- ❌ Wing information is lost during YAML serialization
- ❌ YAML doesn't preserve wing structure

---

## Evidence from Codebase

### 1. CLI Example Shows Wing Usage
```rust
// src/commands/init.rs:145
println!("   1. Add a room:    arxos room create --building \"{}\" --floor 1 --wing A --name \"Main Hall\" --room-type hallway", building_name);
```
**Shows:** Wing was intended to be used

### 2. Mobile FFI Expects Wing
```swift
// ios/ArxOSMobile/Services/ArxOSCoreFFI.swift:142
wing: roomInfo.properties["wing"] ?? "",
```
**Shows:** Mobile apps expect wing information

### 3. IFC Import Creates Default Wings
```rust
// src/ifc/hierarchy.rs:518-520
// Create a default wing if the floor has no wings
if floor.wings.is_empty() {
    floor.wings.push(Wing { ... });
}
```
**Shows:** IFC import creates wings when needed

### 4. Room Explorer Shows Wing Hierarchy
```rust
// src/commands/room/explorer.rs:4
//! - Building → Floors → Wings → Rooms hierarchy
```
**Shows:** UI expects wing hierarchy

---

## Root Cause

**The issue is a data model inconsistency:**

1. **Core model** supports wings (Building → Floor → Wing → Room)
2. **YAML serialization** flattens wings (Building → Floor → Room)
3. **Room creation** works with YAML structure, ignoring wings
4. **Wing information** is lost when saving to YAML

---

## Solutions

### Option 1: Fix Wing Implementation (Recommended)

**Add wing support to YAML and room creation:**

1. **Add wings to FloorData:**
   ```rust
   pub struct FloorData {
       pub wings: Vec<WingData>,  // Add wings
       pub rooms: Vec<RoomData>,  // Keep for backward compatibility
   }
   ```

2. **Fix room creation to use wings:**
   ```rust
   // Find or create wing
   let wing = floor_data.find_or_create_wing(&config.wing)?;
   wing.rooms.push(room_data);
   ```

3. **Update YAML conversion** to preserve wing structure

**Pros:** Full wing support, preserves hierarchy  
**Cons:** Breaking change, requires migration

### Option 2: Remove Wing Parameter

**Remove wing from CLI and core model:**

1. Remove `wing` parameter from CLI
2. Remove `Wing` struct from core model
3. Simplify hierarchy to Building → Floor → Room

**Pros:** Simpler, matches current YAML structure  
**Cons:** Loses architectural concept, breaks existing code

### Option 3: Document as Unused (Current State)

**Keep wing parameter but document it's ignored:**

1. Add deprecation warning
2. Document that wing is ignored
3. Keep for backward compatibility

**Pros:** No breaking changes  
**Cons:** Confusing, misleading API

---

## Recommendation

**Option 1: Fix Wing Implementation**

**Rationale:**
- Wing is a valid architectural concept
- Core model already supports it
- Mobile apps expect it
- IFC import uses it
- Room explorer shows wing hierarchy

**Implementation Steps:**
1. Add `WingData` to YAML structure
2. Update YAML conversion to preserve wings
3. Fix room creation to use wing parameter
4. Add migration script for existing YAML files

---

## Conclusion

**What wing is:** A legitimate architectural concept for organizing rooms on a floor (e.g., "Wing A", "North Wing", "Administrative Wing")

**Current status:** The `wing` parameter is **broken** - it's accepted but ignored. This is a **bug**, not dead code.

**Fix needed:** The wing functionality needs to be properly implemented to match the core model's intended hierarchy.

