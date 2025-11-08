<!-- 6ca2c8e2-b46b-4527-bdd1-5236b37cf48b bf64286b-a167-46e6-bb27-fe3b3bc22f50 -->
# Complete Core Type Migration Plan

## Overview

Now that BuildingData uses core types (Floor, Wing, Room, Equipment) directly, we need to update all remaining modules that still use deprecated RoomData/EquipmentData types. This completes the data model unification project.

## Current State

- BuildingData now uses `Vec<Floor>` (core type) instead of `Vec<FloorData>`
- Floor uses `Vec<Wing>`, `Vec<Room>`, `Vec<Equipment>` (all core types)
- Render and AR integration modules have been migrated
- Remaining modules still use deprecated types with conversion helpers

## Phase 1: Core Operations Layer (HIGH PRIORITY)

### 1.1 Update `src/core/operations.rs`

**Goal**: Remove conversion helpers since BuildingData now uses core types directly

**Changes**:

- Remove `room_to_room_data()`, `room_data_to_room()`, `equipment_to_equipment_data()`, `equipment_data_to_equipment()` helper functions
- Update `create_room()` to work directly with `Room` (BuildingData.floors[].wings[].rooms is now `Vec<Room>`)
- Update `add_equipment()` to work directly with `Equipment`
- Update `list_rooms()`, `get_room()`, `update_room_impl()` to return/work with `Room` directly
- Update `list_equipment()`, `update_equipment_impl()` to return/work with `Equipment` directly
- Remove `#[allow(deprecated)]` imports of `RoomData` and `EquipmentData`

**Files**: `src/core/operations.rs`

## Phase 2: Service Layer (HIGH PRIORITY)

### 2.1 Update `crates/arxos/crates/arxos/src/services/room_service.rs`

**Goal**: Remove RoomData conversions, work directly with Room

**Changes**:

- Remove `room_to_room_data()` and `room_data_to_room()` internal helpers
- Update `create_room()` to add `Room` directly to `building_data.floors[].wings[].rooms`
- Update `get_room()`, `update_room()` to work with `Room` directly
- Remove `#[allow(deprecated)]` import of `RoomData`

**Files**: `crates/arxos/crates/arxos/src/services/room_service.rs`

### 2.2 Update `crates/arxos/crates/arxos/src/services/equipment_service.rs`

**Goal**: Remove EquipmentData conversions, work directly with Equipment

**Changes**:

- Remove `equipment_to_equipment_data()` and `equipment_data_to_equipment()` internal helpers
- Update `add_equipment()` to add `Equipment` directly to `building_data.floors[].equipment` or `floor.wings[].rooms[].equipment`
- Update `get_equipment()`, `update_equipment()` to work with `Equipment` directly
- Remove `#[allow(deprecated)]` import of `EquipmentData`

**Files**: `crates/arxos/crates/arxos/src/services/equipment_service.rs`

## Phase 3: Command Handlers (MEDIUM PRIORITY)

### 3.1 Update `crates/arxui/crates/arxui/src/commands/room_handlers.rs`

**Goal**: Use core Room type instead of RoomData

**Changes**:

- Replace `RoomData` with `Room` (core type)
- Update room creation to use `Room::new()` or construct `Room` directly
- Update room listing/display to work with `Room` fields (e.g., `room.spatial_properties.position` instead of `room.position`)
- Update room updates to modify `Room` fields directly

**Files**: `crates/arxui/crates/arxui/src/commands/room_handlers.rs`

### 3.2 Update `crates/arxui/crates/arxui/src/commands/equipment_handlers.rs`

**Goal**: Use core Equipment type instead of EquipmentData

**Changes**:

- Replace `EquipmentData` with `Equipment` (core type)
- Update equipment creation to use `Equipment` directly
- Update equipment listing/display to work with `Equipment` fields
- Update equipment status handling to use `EquipmentStatus` and `EquipmentHealthStatus` enums

**Files**: `crates/arxui/crates/arxui/src/commands/equipment_handlers.rs`

## Phase 4: Search Engine (MEDIUM PRIORITY)

### 4.1 Update `crates/arxos/crates/arxos/src/search/engine.rs`

**Goal**: Extract Room/Equipment from core types instead of RoomData/EquipmentData

**Changes**:

- Update `SearchEngine` struct: change `equipment: Vec<EquipmentData>` to `equipment: Vec<Equipment>`
- Update `SearchEngine` struct: change `rooms: Vec<RoomData>` to `rooms: Vec<Room>`
- Update `new()` method to extract `Room` and `Equipment` from `building_data.floors[].wings[].rooms` and `building_data.floors[].equipment`
- Update search methods to work with core type fields (e.g., `room.spatial_properties.position` instead of `room.position`)
- Update equipment status matching to use `EquipmentStatus` and `EquipmentHealthStatus` enums

**Files**: `crates/arxos/crates/arxos/src/search/engine.rs`

## Phase 5: AR Integration Pending (MEDIUM PRIORITY)

### 5.1 Update `crates/arxos/crates/arxos/src/ar_integration/pending.rs`

**Goal**: Use core types for pending equipment operations

**Changes**:

- Replace `RoomData` with `Room` (core type)
- Replace `EquipmentData` with `Equipment` (core type)
- Update pending equipment creation to use `Equipment` directly
- Update room creation to use `Room` directly with proper `SpatialProperties`

**Files**: `crates/arxos/crates/arxos/src/ar_integration/pending.rs`

## Phase 6: Export Modules (LOWER PRIORITY)

### 6.1 Update `crates/arxos/crates/arxos/src/export/ar/gltf.rs`

**Goal**: Use core Equipment type for GLTF export

**Changes**:

- Replace `EquipmentData` with `Equipment` (core type)
- Update equipment position access: `equipment.position.x` (already correct for core type)
- Update equipment type handling to use `EquipmentType` enum

**Files**: `crates/arxos/crates/arxos/src/export/ar/gltf.rs`

### 6.2 Update `crates/arxos/crates/arxos/src/export/ifc/exporter.rs`

**Goal**: Use core types for IFC export

**Changes**:

- Replace `RoomData` with `Room` (core type)
- Replace `EquipmentData` with `Equipment` (core type)
- Update room/equipment field access to use core type structure

**Files**: `crates/arxos/crates/arxos/src/export/ifc/exporter.rs`

### 6.3 Update `crates/arxos/crates/arxos/src/export/ifc/delta.rs`

**Goal**: Use core types for IFC delta calculations

**Changes**:

- Replace `RoomData` with `Room` (core type)
- Replace `EquipmentData` with `Equipment` (core type)
- Update comparison logic to work with core type fields

**Files**: `crates/arxos/crates/arxos/src/export/ifc/delta.rs`

## Phase 7: Other Modules (LOWER PRIORITY)

### 7.1 Update `crates/arxos/crates/arxos/src/game/scenario.rs`

**Goal**: Use core types in game scenarios

**Changes**:

- Replace `RoomData`/`EquipmentData` with `Room`/`Equipment`
- Update scenario loading to work with core types

**Files**: `crates/arxos/crates/arxos/src/game/scenario.rs`

### 7.2 Update `src/lib.rs`

**Goal**: Update public API exports

**Changes**:

- Remove or update deprecated type exports
- Ensure core types are properly exported

**Files**: `src/lib.rs`

### 7.3 Update remaining modules

**Goal**: Clean up any remaining deprecated type usage

**Files to check**:

- `crates/arxos/crates/arxos/src/mobile_ffi/` modules
- `src/ui/spreadsheet/data_source.rs`
- `src/render3d/` modules
- `crates/arxos/crates/arxos/src/query/mod.rs`
- `arx/src/bin/convert_3d_scanner_scan.rs`

## Phase 8: Testing & Verification

### 8.1 Update tests

**Goal**: Ensure all tests work with core types

**Changes**:

- Update test fixtures to use core types
- Update test assertions to check core type fields
- Verify backward compatibility tests still pass

**Files**: `tests/` directory

### 8.2 Verify persistence

**Goal**: Ensure YAML serialization/deserialization works correctly

**Actions**:

- Test loading existing YAML files (should deserialize to core types)
- Test saving new YAML files (should serialize from core types)
- Verify backward compatibility with old YAML format

## Phase 9: Documentation & Cleanup

### 9.1 Update documentation

**Goal**: Document the migration and new patterns

**Changes**:

- Update API documentation
- Update migration guides
- Mark deprecated types clearly in docs

**Files**: `docs/` directory

### 9.2 Final cleanup

**Goal**: Remove or finalize deprecated types

**Decision Point**: Keep `RoomData`/`EquipmentData` as deprecated for backward compatibility, or remove after deprecation period

**Actions**:

- Document deprecation timeline
- Consider removing deprecated types in future major version

## Implementation Order

1. **Phase 1** (Core Operations) - Foundation, must be done first
2. **Phase 2** (Services) - Depends on Phase 1
3. **Phase 3** (Commands) - Depends on Phase 2
4. **Phase 4** (Search) - Can be done in parallel with Phase 3
5. **Phase 5** (AR Pending) - Can be done in parallel
6. **Phase 6** (Export) - Lower priority, can be done later
7. **Phase 7** (Other) - Lowest priority
8. **Phase 8** (Testing) - Should be done incrementally with each phase
9. **Phase 9** (Documentation) - Final step

## Success Criteria

- All modules use core types (Room, Equipment) directly
- No conversion helpers remain in operations/services
- All tests pass
- YAML serialization/deserialization works correctly
- Backward compatibility maintained for existing YAML files
- Code compiles without errors (warnings for deprecated types are acceptable)

### To-dos

- [x] Phase 1: Remove conversion helpers from core::operations.rs and update all functions to work directly with Room/Equipment ✅
- [x] Phase 2.1: Update room_service.rs to remove RoomData conversions and work directly with Room ✅
- [x] Phase 2.2: Update equipment_service.rs to remove EquipmentData conversions and work directly with Equipment ✅
- [x] Phase 3.1: Update room_handlers.rs to use core Room type instead of RoomData ✅
- [x] Phase 3.2: Update equipment_handlers.rs to use core Equipment type instead of EquipmentData ✅
- [x] Phase 4: Update search/engine.rs to extract and use Room/Equipment from core types ✅
- [x] Phase 5: Update ar_integration/pending.rs to use core Room/Equipment types ✅
- [x] Phase 6: Update export modules (gltf.rs, ifc/exporter.rs, ifc/delta.rs) to use core types ✅
- [x] Phase 7: Update remaining modules (game, mobile_ffi, ui, render3d, query, bin) to use core types ✅
- [x] Phase 8: Update tests and verify persistence layer works correctly with core types ✅
- [x] Phase 9: Update documentation and finalize deprecation strategy ✅