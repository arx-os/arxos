# Deprecation Strategy for RoomData and EquipmentData

**Date:** January 2025  
**Status:** Active  
**Version:** 2.0.0

---

## Overview

This document outlines the deprecation strategy for `RoomData` and `EquipmentData` types in favor of using core types (`Room` and `Equipment`) directly. The strategy prioritizes backward compatibility while providing a clear migration path.

---

## Current State

### Deprecated Types

The following types are marked as deprecated but remain functional:

1. **`yaml::RoomData`** - Deprecated in favor of `core::Room`
2. **`yaml::EquipmentData`** - Deprecated in favor of `core::Equipment`
3. **`yaml::conversions::*`** - Conversion functions marked as deprecated

### Deprecation Warnings

All deprecated types and functions include deprecation warnings:

```rust
#[deprecated(note = "Use crate::core::Room directly with serde serialization")]
pub struct RoomData { ... }

#[deprecated(note = "Use Equipment::deserialize directly from YAML instead")]
pub fn equipment_data_to_equipment(...) { ... }
```

---

## Rationale

### Why Keep Deprecated Types?

1. **Backward Compatibility:** Existing code and YAML files continue to work
2. **Gradual Migration:** Allows incremental migration of remaining modules
3. **External Dependencies:** External code may depend on these types
4. **Conversion Functions:** Needed for delta calculations and legacy code paths

### Why Deprecate?

1. **Code Simplification:** Single type system reduces complexity
2. **Type Safety:** Core types provide better type safety (enums vs strings)
3. **Maintainability:** Fewer types to maintain
4. **Consistency:** All modules use the same types

---

## Migration Path

### For New Code

**Always use core types:**

```rust
// ✅ CORRECT - Use core types
use crate::core::{Room, Equipment, Floor, Wing};

let room = Room::new("Office 101".to_string(), RoomType::Office);
let equipment = Equipment::new("HVAC-1".to_string(), "/path".to_string(), EquipmentType::HVAC);
```

### For Existing Code

**Option 1: Direct Migration (Recommended)**

```rust
// ❌ OLD - Using deprecated types
use crate::yaml::{RoomData, EquipmentData};
let room_data: RoomData = ...;
let equipment_data: EquipmentData = ...;

// ✅ NEW - Using core types
use crate::core::{Room, Equipment};
let room: Room = ...;
let equipment: Equipment = ...;
```

**Option 2: Gradual Migration (Temporary)**

If immediate migration is not possible, use conversion functions (with deprecation warnings):

```rust
#[allow(deprecated)]
use crate::yaml::conversions::{room_data_to_room, equipment_data_to_equipment};

let room = room_data_to_room(&room_data);
let equipment = equipment_data_to_equipment(&equipment_data);
```

---

## Deprecation Timeline

### Phase 1: Deprecation (v2.0.0) ✅ **COMPLETE**

- ✅ Types marked as deprecated
- ✅ Conversion functions marked as deprecated
- ✅ Deprecation warnings added
- ✅ Migration guide created
- ✅ Core modules migrated to use core types

**Status:** Complete

### Phase 2: Migration (v2.x) ✅ **COMPLETE**

- ✅ BuildingData restructured to use core types
- ✅ All command handlers migrated
- ✅ All services migrated
- ✅ All export modules migrated
- ✅ All render/AR modules migrated
- ✅ All tests updated

**Status:** Complete

### Phase 3: Cleanup (v3.0.0) ⏳ **FUTURE**

**Considerations:**
- Remove deprecated types entirely
- Remove conversion functions
- Update public API (`src/lib.rs`)
- Breaking change - requires major version bump

**Timeline:** TBD (likely v3.0.0 or later)

---

## Remaining Deprecated Usage

### Acceptable Usage

The following usage is **expected and acceptable**:

1. **`src/lib.rs`** - Public API exports
   - **Reason:** Backward compatibility for external users
   - **Action:** Keep until v3.0.0

2. **`src/export/ifc/delta.rs`** - Delta calculations
   - **Reason:** Delta format uses deprecated types for compatibility
   - **Action:** Keep until delta format is updated

3. **Test Files** - Conversion function tests
   - **Reason:** Tests need to verify conversion functions
   - **Action:** Keep as long as conversion functions exist

### Unacceptable Usage

The following usage should be **migrated**:

1. New code using deprecated types
2. Code that can easily be migrated
3. Internal modules (non-public API)

---

## Migration Checklist

### For Developers

When working with building data:

- [ ] Use `core::Room` instead of `yaml::RoomData`
- [ ] Use `core::Equipment` instead of `yaml::EquipmentData`
- [ ] Use `core::Floor` instead of `yaml::FloorData`
- [ ] Use `core::Wing` instead of `yaml::WingData`
- [ ] Access rooms via `floor.wings[].rooms[]` (not `floor.rooms[]`)
- [ ] Use `room.spatial_properties.position` (not `room.position`)
- [ ] Use `equipment.position` (core::Position, not Point3D)
- [ ] Use `equipment.equipment_type` (enum, not string)
- [ ] Use `equipment.health_status` (if present) or `equipment.status`

### For Code Reviewers

When reviewing code:

- [ ] Check for deprecated type usage
- [ ] Ensure new code uses core types
- [ ] Verify migration is complete
- [ ] Check for `#[allow(deprecated)]` usage (should be minimal)

---

## Breaking Changes

### v2.0.0 (Current)

**No breaking changes:**
- Deprecated types still work
- Conversion functions still available
- Existing code continues to function

### v3.0.0 (Future)

**Potential breaking changes:**
- Remove `RoomData` and `EquipmentData` types
- Remove conversion functions
- Update public API exports
- Require migration of all external code

**Migration Guide:** Will be provided before v3.0.0 release

---

## Examples

### Creating a Room

```rust
// ✅ CORRECT - Using core types
use crate::core::{Room, RoomType, SpatialProperties, Position, Dimensions, BoundingBox};

let spatial_properties = SpatialProperties::new(
    Position {
        x: 10.0,
        y: 20.0,
        z: 3.0,
        coordinate_system: "building_local".to_string(),
    },
    Dimensions {
        width: 10.0,
        height: 3.0,
        depth: 10.0,
    },
    "building_local".to_string(),
);

let room = Room {
    id: "room-101".to_string(),
    name: "Office 101".to_string(),
    room_type: RoomType::Office,
    equipment: vec![],
    spatial_properties,
    properties: HashMap::new(),
    created_at: None,
    updated_at: None,
};
```

### Creating Equipment

```rust
// ✅ CORRECT - Using core types
use crate::core::{Equipment, EquipmentType, EquipmentStatus, Position};

let equipment = Equipment {
    id: "equipment-1".to_string(),
    name: "HVAC Unit 1".to_string(),
    path: "/building/floor1/equipment-1".to_string(),
    address: None,
    equipment_type: EquipmentType::HVAC,
    position: Position {
        x: 5.0,
        y: 5.0,
        z: 2.0,
        coordinate_system: "building_local".to_string(),
    },
    properties: HashMap::new(),
    status: EquipmentStatus::Active,
    health_status: None,
    room_id: None,
    sensor_mappings: None,
};
```

### Accessing Building Data

```rust
// ✅ CORRECT - Using core types
let building_data: BuildingData = ...;

// Access floors
for floor in &building_data.floors {
    // Access wings
    for wing in &floor.wings {
        // Access rooms
        for room in &wing.rooms {
            // Access room properties
            let position = &room.spatial_properties.position;
            let dimensions = &room.spatial_properties.dimensions;
            
            // Access equipment in room
            for equipment in &room.equipment {
                let eq_type = equipment.equipment_type;  // Enum
                let status = equipment.status;  // Operational status
                let health = equipment.health_status;  // Health status (optional)
            }
        }
    }
    
    // Access floor-level equipment
    for equipment in &floor.equipment {
        // ...
    }
}
```

---

## References

- [Data Model Unification Plan](DATA_MODEL_UNIFICATION_PLAN.md)
- [Data Model Unification Summary](DATA_MODEL_UNIFICATION_SUMMARY.md)
- [Data Model Unification Complete](DATA_MODEL_UNIFICATION_COMPLETE.md)
- [Phase 3 Migration Guide](PHASE_3_MIGRATION_GUIDE.md)
- [Phase 8 & 9 Complete](PHASE_8_9_COMPLETE.md)

---

## Questions?

If you have questions about the deprecation strategy or need help migrating code:

1. Check the migration guide: `PHASE_3_MIGRATION_GUIDE.md`
2. Review examples in this document
3. Check existing migrated code for patterns
4. Ask the team for assistance

---

**Last Updated:** January 2025  
**Maintained By:** ArxOS Engineering Team

