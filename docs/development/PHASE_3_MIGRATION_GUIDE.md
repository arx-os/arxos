# Phase 3: Migration Guide

**Date:** January 2025  
**Status:** In Progress  
**Phase:** Data Model Unification - Phase 3

---

## Overview

Phase 3 focuses on migrating from YAML types to core types. Core types (Equipment, Room) now serialize directly to YAML format, so conversion functions are no longer necessary for new code.

---

## Migration Strategy

### Current State

- ✅ Core types (Equipment, Room) serialize directly to YAML format
- ✅ Custom serialization handles format differences
- ⚠️ Conversion functions still exist for backward compatibility
- ⚠️ Some code still uses YAML types (EquipmentData, RoomData)

### Target State

- Core types used directly throughout codebase
- YAML types deprecated (kept for backward compatibility)
- Conversion functions deprecated (kept for backward compatibility)
- Direct serialization/deserialization of core types

---

## Migration Steps

### Step 1: Use Core Types Directly ✅

**Status:** Core types are ready for direct use

Core types now serialize/deserialize directly to YAML format:

```rust
use crate::core::Equipment;
use serde_json;

// Serialize Equipment directly
let equipment = Equipment::new(...);
let json = serde_json::to_string(&equipment)?;

// Deserialize Equipment directly
let equipment: Equipment = serde_json::from_str(&json)?;
```

### Step 2: Update Call Sites

**Status:** In Progress

Update code to use core types directly instead of conversion functions:

**Before:**
```rust
use crate::yaml::conversions::equipment_to_equipment_data;
let equipment_data = equipment_to_equipment_data(&equipment);
```

**After:**
```rust
// Use Equipment directly - it serializes to the same format
let json = serde_json::to_string(&equipment)?;
```

### Step 3: Deprecation Warnings

**Status:** ✅ Complete

Conversion functions and YAML types are now marked as deprecated:

- `equipment_to_equipment_data()` - Deprecated
- `equipment_data_to_equipment()` - Deprecated
- `room_data_to_room()` - Deprecated
- `EquipmentData` - Deprecated
- `RoomData` - Deprecated

### Step 4: Gradual Migration

**Status:** Ongoing

Gradually update call sites:

1. **Services** (`src/services/`)
   - Update `room_service.rs` to use Room directly
   - Update `equipment_service.rs` to use Equipment directly

2. **Operations** (`src/core/operations.rs`)
   - Update to use Equipment directly instead of EquipmentData

3. **YAML Serialization** (`src/yaml/mod.rs`)
   - Update `BuildingYamlSerializer` to work with core types directly

### Step 5: Remove Conversion Functions (Future)

**Status:** Not Started

Once all call sites are updated:
- Remove conversion functions
- Keep YAML types as deprecated type aliases (for backward compatibility)
- Update documentation

---

## Code Examples

### Serializing Equipment

**Old Way (Deprecated):**
```rust
use crate::yaml::conversions::equipment_to_equipment_data;
let equipment_data = equipment_to_equipment_data(&equipment);
let yaml = serde_yaml::to_string(&equipment_data)?;
```

**New Way:**
```rust
use crate::core::Equipment;
let yaml = serde_yaml::to_string(&equipment)?;
```

### Deserializing Equipment

**Old Way (Deprecated):**
```rust
use crate::yaml::conversions::equipment_data_to_equipment;
let equipment_data: EquipmentData = serde_yaml::from_str(&yaml)?;
let equipment = equipment_data_to_equipment(&equipment_data);
```

**New Way:**
```rust
use crate::core::Equipment;
let equipment: Equipment = serde_yaml::from_str(&yaml)?;
```

### Serializing Room

**Old Way (Deprecated):**
```rust
// Room serialization was not fully implemented
```

**New Way:**
```rust
use crate::core::Room;
let yaml = serde_yaml::to_string(&room)?;
```

### Deserializing Room

**Old Way (Deprecated):**
```rust
use crate::yaml::conversions::room_data_to_room;
let room_data: RoomData = serde_yaml::from_str(&yaml)?;
let room = room_data_to_room(&room_data);
```

**New Way:**
```rust
use crate::core::Room;
let room: Room = serde_yaml::from_str(&yaml)?;
```

---

## Backward Compatibility

### Deprecated Types

The following types are deprecated but still available:

- `EquipmentData` - Use `crate::core::Equipment` instead
- `RoomData` - Use `crate::core::Room` instead

### Deprecated Functions

The following functions are deprecated but still available:

- `equipment_to_equipment_data()` - Use `Equipment::serialize` instead
- `equipment_data_to_equipment()` - Use `Equipment::deserialize` instead
- `room_data_to_room()` - Use `Room::deserialize` instead

### Migration Timeline

1. **Phase 3.1** (Current): Add deprecation warnings ✅
2. **Phase 3.2** (In Progress): Update call sites gradually
3. **Phase 3.3** (Future): Remove conversion functions
4. **Phase 3.4** (Future): Make YAML types type aliases (if possible)

---

## Known Limitations

### BuildingData Structure

`BuildingData` has a different structure than `Building`:
- `BuildingData` has `BuildingInfo` and `BuildingMetadata` as separate fields
- `Building` has `metadata` as an optional flattened field

This means `BuildingData` cannot be a simple type alias. It will remain as a separate type for now, but we can simplify the conversion logic.

### EquipmentData vs Equipment

`EquipmentData` has some computed fields:
- `system_type` - Computed from `equipment_type`
- `bounding_box` - Computed from `position`

Since `Equipment` now serializes with these fields (via custom serialization), we could potentially make `EquipmentData` a type alias in the future, but it requires careful handling of the computed fields.

---

## Testing

When migrating code:

1. **Test Serialization**: Ensure core types serialize to the same YAML format
2. **Test Deserialization**: Ensure core types deserialize from existing YAML files
3. **Test Round-Trip**: Serialize → Deserialize → Verify equality

```rust
#[test]
fn test_equipment_round_trip() {
    let equipment = Equipment::new(...);
    let yaml = serde_yaml::to_string(&equipment).unwrap();
    let deserialized: Equipment = serde_yaml::from_str(&yaml).unwrap();
    // Verify fields match
}
```

---

## References

- [Data Model Unification Plan](DATA_MODEL_UNIFICATION_PLAN.md)
- [Data Model Unification Summary](DATA_MODEL_UNIFICATION_SUMMARY.md)
- [Phase 1 Complete](PHASE_1_COMPLETE.md)
- [Phase 2 Complete](PHASE_2_COMPLETE.md)

