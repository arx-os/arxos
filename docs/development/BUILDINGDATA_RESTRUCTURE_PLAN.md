# BuildingData Restructure Plan

**Date:** January 2025  
**Status:** In Progress  
**Goal:** Restructure BuildingData to use core types directly

---

## Overview

Restructure `BuildingData` to use core types (`Room`, `Equipment`, `Floor`, `Wing`) instead of YAML types (`RoomData`, `EquipmentData`, `FloorData`, `WingData`). This will complete the data model unification by eliminating the need for conversion functions in BuildingData operations.

---

## Current State

### BuildingData Structure
```rust
pub struct BuildingData {
    pub building: BuildingInfo,        // Nested building info
    pub metadata: BuildingMetadata,     // Parser metadata
    pub floors: Vec<FloorData>,         // Uses RoomData, EquipmentData
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
}
```

### Building (Core) Structure
```rust
pub struct Building {
    pub id: String,
    pub name: String,
    pub path: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub floors: Vec<Floor>,             // Uses Room, Equipment
    pub metadata: Option<BuildingMetadata>,
}
```

### Key Differences

| Field | BuildingData | Building (Core) |
|-------|--------------|-----------------|
| Building Info | `BuildingInfo` (nested) | Flat fields |
| Description | `BuildingInfo.description` | None |
| Version | `BuildingInfo.version` | None |
| Global Bounding Box | `BuildingInfo.global_bounding_box` | None |
| Coordinate Systems | `coordinate_systems: Vec<CoordinateSystemInfo>` | None |
| Floors | `Vec<FloorData>` | `Vec<Floor>` |

---

## Proposed Solution

### Step 1: Enhance Building (Core) with Missing Fields

Add missing fields to `Building` to match `BuildingData` capabilities:

```rust
pub struct Building {
    pub id: String,
    pub name: String,
    pub path: String,
    pub description: Option<String>,              // NEW
    pub version: String,                          // NEW
    pub global_bounding_box: Option<BoundingBox3D>, // NEW
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub floors: Vec<Floor>,
    pub metadata: Option<BuildingMetadata>,
    pub coordinate_systems: Vec<CoordinateSystemInfo>, // NEW
}
```

### Step 2: Update BuildingData to Use Core Types

Change `BuildingData` to use core types:

```rust
pub struct BuildingData {
    // Use Building directly (or flatten its fields)
    pub building: Building,  // OR flatten Building fields
    pub metadata: BuildingMetadata,  // Keep separate for backward compatibility
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
}
```

**OR** (Better approach - flatten Building):

```rust
pub struct BuildingData {
    // Flatten Building fields
    pub id: String,
    pub name: String,
    pub path: String,
    pub description: Option<String>,
    pub version: String,
    pub global_bounding_box: Option<BoundingBox3D>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub floors: Vec<Floor>,  // Core type!
    pub metadata: BuildingMetadata,
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
}
```

### Step 3: Update All BuildingData Usage

Update all code that uses BuildingData:
- Persistence layer
- Operations
- Services
- Render module
- AR integration
- BuildingYamlSerializer

---

## Implementation Steps

### Phase 1: Enhance Building (Core) ✅
- [x] Add `description: Option<String>`
- [x] Add `version: String`
- [x] Add `global_bounding_box: Option<BoundingBox3D>`
- [x] Add `coordinate_systems: Vec<CoordinateSystemInfo>`

### Phase 2: Update BuildingData Structure
- [ ] Change `floors: Vec<FloorData>` → `floors: Vec<Floor>`
- [ ] Update `WingData` to use `Room` and `Equipment`
- [ ] Update `FloorData` to use `Wing` (core type)
- [ ] Remove or deprecate `RoomData` and `EquipmentData` from BuildingData

### Phase 3: Update BuildingData Methods
- [ ] Update `build_index()` to work with core types
- [ ] Update `get_floor_mut()` to work with core types
- [ ] Update `get_wing_mut()` to work with core types
- [ ] Update `get_or_create_floor_mut()` to work with core types
- [ ] Update `get_or_create_wing_mut()` to work with core types

### Phase 4: Update Persistence Layer
- [ ] Update `PersistenceManager` to work with new BuildingData
- [ ] Update serialization/deserialization
- [ ] Ensure backward compatibility with existing YAML files

### Phase 5: Update Operations & Services
- [ ] Update `core::operations` to work with new BuildingData
- [ ] Update services to work with new BuildingData
- [ ] Remove conversion functions from operations

### Phase 6: Update Render Module
- [ ] Update `BuildingRenderer` to use core types
- [ ] Remove RoomData/EquipmentData usage

### Phase 7: Update AR Integration
- [ ] Update AR integration modules to use core types
- [ ] Remove RoomData/EquipmentData usage

### Phase 8: Cleanup
- [ ] Remove or deprecate `RoomData` and `EquipmentData` types
- [ ] Remove conversion functions (or keep as deprecated)
- [ ] Update tests
- [ ] Update documentation

---

## Backward Compatibility

### YAML File Compatibility

**Challenge:** Existing YAML files use RoomData and EquipmentData structure.

**Solution:** Use custom deserialization to handle both formats:
1. Try to deserialize as new format (core types)
2. Fall back to old format (RoomData/EquipmentData) if needed
3. Convert old format to new format during deserialization

**OR** simpler approach:
- Since Room and RoomData serialize to the same format (thanks to custom serialization), we can deserialize directly as Room/Equipment
- Use serde's `#[serde(alias = "...")]` or custom deserialization if needed

---

## Risks

1. **Breaking Change:** This changes the YAML format structure
2. **Migration Required:** Existing YAML files may need conversion
3. **Large Scope:** Many files need updating
4. **Testing:** Need comprehensive testing to ensure backward compatibility

---

## Success Criteria

- ✅ BuildingData uses core types (Room, Equipment, Floor, Wing)
- ✅ All code compiles successfully
- ✅ Existing YAML files can be loaded (backward compatible)
- ✅ New YAML files use core types
- ✅ No conversion functions needed in BuildingData operations
- ✅ Render module uses core types
- ✅ AR integration uses core types

---

## References

- [Data Model Unification Plan](DATA_MODEL_UNIFICATION_PLAN.md)
- [Data Model Unification Summary](DATA_MODEL_UNIFICATION_SUMMARY.md)

