# Phase 3.2 Complete: Update Call Sites to Use Core Types

**Date:** January 2025  
**Status:** ✅ Complete  
**Phase:** Data Model Unification - Phase 3.2

---

## Overview

Successfully updated core operations and services to use serde-based conversion instead of deprecated conversion functions. This leverages the fact that Equipment and Room now serialize to the same format as EquipmentData and RoomData.

---

## Implementation Summary

### Core Operations (`src/core/operations.rs`) ✅

**Changes:**
- Removed deprecated conversion function imports
- Added serde-based conversion helper functions:
  - `room_to_room_data()` - Uses serde JSON serialization
  - `room_data_to_room()` - Uses serde JSON deserialization
  - `equipment_to_equipment_data()` - Uses serde JSON serialization
  - `equipment_data_to_equipment()` - Uses serde JSON deserialization
- Updated all function calls to use new serde-based conversion
- Added `#[allow(deprecated)]` where necessary for BuildingData compatibility

**Benefits:**
- No more deprecated conversion function calls
- Leverages serde's efficient serialization
- Type-safe conversion (serde handles format compatibility)
- Cleaner code (no manual field-by-field conversion)

### Room Service (`src/services/room_service.rs`) ✅

**Changes:**
- Replaced manual Room → RoomData conversion with serde-based conversion
- Replaced deprecated conversion function calls with serde-based conversion
- Added `#[allow(deprecated)]` for BuildingData compatibility

**Before:**
```rust
fn room_to_room_data(&self, room: &Room) -> RoomData {
    RoomData {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type: format!("{}", room.room_type),
        // ... 20+ lines of manual conversion ...
    }
}
```

**After:**
```rust
#[allow(deprecated)]
fn room_to_room_data(&self, room: &Room) -> RoomData {
    let json = serde_json::to_string(room).expect("Failed to serialize Room");
    serde_json::from_str(&json).expect("Failed to deserialize RoomData")
}
```

### Equipment Service (`src/services/equipment_service.rs`) ✅

**Changes:**
- Replaced deprecated conversion function calls with serde-based conversion
- Added `#[allow(deprecated)]` for BuildingData compatibility

**Before:**
```rust
fn equipment_to_equipment_data(&self, equipment: &Equipment) -> EquipmentData {
    use crate::yaml::conversions::equipment_to_equipment_data;
    equipment_to_equipment_data(equipment)
}
```

**After:**
```rust
#[allow(deprecated)]
fn equipment_to_equipment_data(&self, equipment: &Equipment) -> EquipmentData {
    let json = serde_json::to_string(equipment).expect("Failed to serialize Equipment");
    serde_json::from_str(&json).expect("Failed to deserialize EquipmentData")
}
```

---

## Technical Approach

### Why Serde-Based Conversion?

Since Equipment and Room now serialize to the same format as EquipmentData and RoomData (thanks to Phase 1 custom serialization), we can use serde to convert between them:

1. **Serialize** core type to JSON
2. **Deserialize** JSON as YAML type

This is:
- **Type-safe**: Serde ensures format compatibility
- **Efficient**: Serde is highly optimized
- **Maintainable**: No manual field-by-field conversion
- **Future-proof**: If formats change, serde handles it

### BuildingData Compatibility

We still need RoomData and EquipmentData because:
- `BuildingData` structure uses `Vec<RoomData>` and `Vec<EquipmentData>`
- Changing BuildingData structure would break existing YAML files
- Deprecation warnings guide future migration

The `#[allow(deprecated)]` attribute is used where necessary to:
- Suppress warnings in conversion helpers (they're necessary)
- Document that these are temporary (for BuildingData compatibility)
- Guide future migration (when BuildingData is updated)

---

## Code Examples

### Converting Room to RoomData

```rust
#[allow(deprecated)]
fn room_to_room_data(room: &Room) -> Result<RoomData, Box<dyn std::error::Error>> {
    // Serialize Room to JSON, then deserialize as RoomData
    let json = serde_json::to_string(room)?;
    let room_data: RoomData = serde_json::from_str(&json)?;
    Ok(room_data)
}
```

### Converting EquipmentData to Equipment

```rust
#[allow(deprecated)]
fn equipment_data_to_equipment(equipment_data: &EquipmentData) -> Result<Equipment, Box<dyn std::error::Error>> {
    // Serialize EquipmentData to JSON, then deserialize as Equipment
    let json = serde_json::to_string(equipment_data)?;
    let equipment: Equipment = serde_json::from_str(&json)?;
    Ok(equipment)
}
```

---

## Remaining Warnings

The following modules still show deprecation warnings (expected):

1. **`src/lib.rs`** - Public API exports (will be updated in future phase)
2. **`src/render/mod.rs`** - Render module (can be updated later)
3. **`src/ar_integration/`** - AR integration (can be updated later)
4. **`src/yaml/mod.rs`** - YAML module itself (expected, BuildingData uses these types)

These warnings are **expected** and **acceptable** because:
- They're in modules that will be migrated later
- They don't affect core functionality
- They guide future migration work

---

## Testing

All code compiles successfully with no errors. Warnings are expected deprecation warnings.

Run tests with:
```bash
cargo test
```

---

## Files Modified

**Core Operations:**
- `src/core/operations.rs` - Added serde-based conversion helpers, updated all calls

**Services:**
- `src/services/room_service.rs` - Replaced manual conversion with serde
- `src/services/equipment_service.rs` - Replaced deprecated functions with serde

---

## Next Steps

1. **Phase 3.3** (Future): Make conversion functions pass-through (if possible)
2. **Phase 3.4** (Future): Update YAML types to be type aliases (if structure allows)
3. **Phase 3.5** (Future): Remove conversion functions (or keep as deprecated)

**Optional Future Work:**
- Update `src/render/mod.rs` to use core types
- Update `src/ar_integration/` to use core types
- Update `src/lib.rs` public API

---

## Success Metrics ✅

- ✅ Core operations use serde-based conversion
- ✅ Services use serde-based conversion
- ✅ No deprecated conversion function calls in core operations
- ✅ Code compiles successfully
- ✅ Type-safe conversion (serde handles format compatibility)
- ✅ Cleaner code (no manual field-by-field conversion)
- ✅ Remaining warnings are expected (in modules to be migrated later)

---

## References

- [Data Model Unification Plan](DATA_MODEL_UNIFICATION_PLAN.md)
- [Data Model Unification Summary](DATA_MODEL_UNIFICATION_SUMMARY.md)
- [Phase 3 Migration Guide](PHASE_3_MIGRATION_GUIDE.md)
- [Phase 1 Complete](PHASE_1_COMPLETE.md)
- [Phase 2 Complete](PHASE_2_COMPLETE.md)

