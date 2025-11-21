# Data Model Unification Plan

**Goal:** Unify core domain types and YAML serialization types by deriving serialization directly from core types, eliminating the need for separate YAML types and conversion functions.

**Status:** Planning Phase  
**Date:** January 2025

---

## Current State Analysis

### Key Differences

#### 1. **EquipmentStatus Enum Mismatch** ⚠️ **CRITICAL**
- **Core**: `Active`, `Inactive`, `Maintenance`, `OutOfOrder`, `Unknown` (operational status)
- **YAML**: `Healthy`, `Warning`, `Critical`, `Unknown` (health status)
- **Issue**: These represent different concepts! Operational status ≠ Health status
- **Solution**: Create unified enum with both concepts, or use serde attributes to map between them

#### 2. **EquipmentType**
- **Core**: `EquipmentType` enum (HVAC, Electrical, etc.)
- **YAML**: `String` + derived `system_type: String`
- **Solution**: Use serde to serialize enum as string, derive `system_type` via computed field

#### 3. **Position Types** ⚠️ **COMPLEX**
- **Core**: `core::Position` struct with `coordinate_system: String`
- **Spatial**: `spatial::Point3D` (simple x, y, z) - used by YAML
- **Issue**: These are **different types** in different modules!
- **Solution Options**:
  - **Option A**: Make core types use `spatial::Point3D` directly, store coordinate system separately
  - **Option B**: Use serde custom serialization to convert `Position` → `Point3D` for YAML
  - **Option C**: Unify types - merge `Position` and `Point3D` into single type
- **Recommendation**: Option B - Keep types separate, use custom serialization

#### 4. **BoundingBox Types** ⚠️ **COMPLEX**
- **Core**: `core::BoundingBox` with `core::Position` (includes coordinate system)
- **Spatial**: `spatial::BoundingBox3D` with `spatial::Point3D` (no coordinate system)
- **Issue**: Different types, different modules
- **Solution**: Similar to Position - use custom serialization or unify types

#### 5. **Room Equipment**
- **Core**: `Vec<Equipment>` (full objects)
- **YAML**: `Vec<String>` (IDs only)
- **Solution**: Use serde `serialize_with` to serialize as IDs, deserialize by resolving IDs

#### 6. **Timestamps**
- **Core**: `created_at`, `updated_at` (DateTime<Utc>)
- **YAML**: None
- **Solution**: Use `#[serde(skip_serializing_if = "...")]` or make optional

#### 7. **YAML-Only Features**
- Sensor mappings, metadata, coordinate system info
- **Solution**: Add optional fields to core types, or use serde `flatten` for metadata

---

## Proposed Solution: Hybrid Approach with Type Unification

### Phase 0: Unify Spatial Types (Prerequisite)

**Decision Point:** Should we unify `core::Position` and `spatial::Point3D`?

**Option A: Keep Separate (Recommended)**
- Keep `core::Position` for domain logic (with coordinate system)
- Keep `spatial::Point3D` for spatial operations (simple, fast)
- Use conversion functions between them
- Use serde custom serialization for YAML

**Option B: Unify Types**
- Merge `Position` and `Point3D` into single type
- Add optional coordinate system field
- Simpler, but loses type safety distinction

**Recommendation:** Option A - Keep types separate for now, add conversion helpers.

### Phase 1: Enhance Core Types with Serialization Attributes

**Strategy:** Add serde attributes to core types to customize serialization behavior, making them serialize directly to YAML format.

#### 1.1 EquipmentStatus Unification

**Option A: Unified Enum (Recommended)**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EquipmentStatus {
    // Operational status
    Active,
    Inactive,
    Maintenance,
    OutOfOrder,
    
    // Health status (for YAML compatibility)
    Healthy,
    Warning,
    Critical,
    
    Unknown,
}
```

**Option B: Separate Enums with Mapping**
```rust
// Core enum (operational)
pub enum EquipmentStatus {
    Active,
    Inactive,
    Maintenance,
    OutOfOrder,
    Unknown,
}

// YAML enum (health)
pub enum EquipmentHealthStatus {
    Healthy,
    Warning,
    Critical,
    Unknown,
}

// Use serde attributes to map between them
```

**Option C: Single Enum with Serde Rename (Simplest)**
- Keep core enum as-is
- Use `#[serde(rename = "...")]` to map to YAML values
- Add conversion logic in serde custom serializer

**Recommendation:** Option C - Keep existing enums, use custom serialization

#### 1.2 EquipmentType Serialization

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EquipmentType {
    HVAC,
    Electrical,
    AV,
    Furniture,
    Safety,
    Plumbing,
    Network,
    Other(String),
}

// Add computed field for system_type
impl Equipment {
    #[serde(skip)]
    pub fn system_type(&self) -> String {
        match self.equipment_type {
            EquipmentType::HVAC => "HVAC",
            EquipmentType::Electrical => "ELECTRICAL",
            // ... etc
        }.to_string()
    }
}
```

**Better approach:** Use serde `serialize_with` to add `system_type` during serialization.

#### 1.3 Position Serialization

**Challenge:** `core::Position` needs to serialize as `spatial::Point3D` for YAML.

**Solution:** Use custom serialization to convert between types:

```rust
use crate::spatial::Point3D;

#[derive(Debug, Clone)]
pub struct Position {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub coordinate_system: String,
}

// Custom serialization to Point3D format
impl Serialize for Position {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        // Serialize as Point3D (x, y, z only)
        Point3D {
            x: self.x,
            y: self.y,
            z: self.z,
        }.serialize(serializer)
    }
}

// Custom deserialization from Point3D
impl<'de> Deserialize<'de> for Position {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let point: Point3D = Point3D::deserialize(deserializer)?;
        Ok(Position {
            x: point.x,
            y: point.y,
            z: point.z,
            coordinate_system: "building_local".to_string(), // Default
        })
    }
}
```

**Alternative:** Use `#[serde(with = "position_serde")]` module for cleaner code.

#### 1.4 BoundingBox Serialization

**Challenge:** `core::BoundingBox` needs to serialize as `spatial::BoundingBox3D`.

**Solution:** Similar custom serialization:

```rust
use crate::spatial::{Point3D, BoundingBox3D};

impl Serialize for BoundingBox {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        BoundingBox3D {
            min: Point3D {
                x: self.min.x,
                y: self.min.y,
                z: self.min.z,
            },
            max: Point3D {
                x: self.max.x,
                y: self.max.y,
                z: self.max.z,
            },
        }.serialize(serializer)
    }
}
```

#### 1.5 Room Equipment Serialization

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Room {
    // ... other fields ...
    
    #[serde(serialize_with = "serialize_equipment_ids")]
    #[serde(deserialize_with = "deserialize_equipment_ids")]
    pub equipment: Vec<Equipment>,
}

fn serialize_equipment_ids<S>(equipment: &Vec<Equipment>, serializer: S) -> Result<S::Ok, S::Error>
where
    S: serde::Serializer,
{
    let ids: Vec<String> = equipment.iter().map(|e| e.id.clone()).collect();
    ids.serialize(serializer)
}
```

**Challenge:** Deserialization requires resolving IDs to Equipment objects. This might require a two-pass approach or storing equipment separately.

#### 1.6 Timestamps

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Room {
    // ... other fields ...
    
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub created_at: Option<DateTime<Utc>>,
    
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub updated_at: Option<DateTime<Utc>>,
}
```

Make timestamps optional so they're omitted from YAML but preserved in core.

---

### Phase 2: Add YAML-Only Fields to Core Types

#### 2.1 Sensor Mappings

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Equipment {
    // ... existing fields ...
    
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub sensor_mappings: Option<Vec<SensorMapping>>,
}
```

#### 2.2 Metadata

Add metadata fields to Building type:
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Building {
    // ... existing fields ...
    
    #[serde(flatten, skip_serializing_if = "Option::is_none", default)]
    pub metadata: Option<BuildingMetadata>,
}
```

---

### Phase 3: Migration Strategy

#### 3.1 Backward Compatibility

1. **Keep YAML types as type aliases** (temporary)
   ```rust
   // Deprecated: Use core::Equipment instead
   pub type EquipmentData = crate::core::Equipment;
   ```

2. **Update conversion functions** to be identity functions (temporary)
   ```rust
   pub fn equipment_to_equipment_data(equipment: &Equipment) -> Equipment {
       equipment.clone() // Just clone, no conversion needed
   }
   ```

3. **Gradually update call sites** to use core types directly

#### 3.2 Migration Steps

1. **Step 1**: Add serde attributes to core types
2. **Step 2**: Test serialization/deserialization with existing YAML files
3. **Step 3**: Update conversion functions to be pass-through
4. **Step 4**: Update all call sites to use core types
5. **Step 5**: Remove YAML types (or keep as type aliases)
6. **Step 6**: Remove conversion functions

---

## Implementation Plan

### Step 0: Create Serde Helper Modules

**Files to create:**
- `src/core/serde_helpers.rs` - Custom serialization for Position, BoundingBox
- `src/core/serde_helpers/position.rs` - Position ↔ Point3D conversion
- `src/core/serde_helpers/bounding_box.rs` - BoundingBox ↔ BoundingBox3D conversion
- `src/core/serde_helpers/equipment_status.rs` - EquipmentStatus mapping

### Step 1: Equipment Type Unification

**Files to modify:**
- `src/core/equipment.rs` - Add serde attributes
- `src/core/types.rs` - Update Position/BoundingBox serialization
- `src/yaml/conversions.rs` - Update to use core types directly

**Changes:**
1. Add custom serialization for `EquipmentStatus` to map to YAML values
2. Add `system_type` as computed field during serialization
3. Update `Position` to serialize as `Point3D` when coordinate_system is default
4. Update `BoundingBox` similarly

### Step 2: Room Type Unification

**Files to modify:**
- `src/core/room.rs` - Add serde attributes
- `src/yaml/conversions.rs` - Update room conversions

**Changes:**
1. Add custom serialization for equipment (IDs only in YAML)
2. Make timestamps optional
3. Update spatial properties serialization

### Step 3: Building Type Unification

**Files to modify:**
- `src/core/building.rs` - Add metadata support
- `src/yaml/mod.rs` - Update BuildingData to use core::Building

**Changes:**
1. Add metadata fields to Building
2. Update BuildingData to be type alias or wrapper

### Step 4: Update All Usage Sites

**Files to update:**
- All files using `EquipmentData`, `RoomData`, `BuildingData`
- Service layer (already uses core types - good!)
- Command handlers
- Persistence layer
- Export/import modules

### Step 5: Remove YAML Types

**Files to remove/modify:**
- `src/yaml/mod.rs` - Remove type definitions, keep only serializer
- `src/yaml/conversions.rs` - Remove conversion functions

---

## Challenges & Solutions

### Challenge 1: EquipmentStatus Semantic Mismatch

**Problem:** Core uses operational status, YAML uses health status.

**Solution Options:**
1. **Keep both enums**, use custom serializer to map
2. **Unify into single enum** with both concepts
3. **Add health_status field** to Equipment, keep status as operational

**Recommendation:** Option 1 - Keep enums separate, use custom serialization. This preserves semantic clarity.

### Challenge 2: Room Equipment (Vec<Equipment> vs Vec<String>)

**Problem:** Core has full objects, YAML has IDs only.

**Solution:**
- Serialize as IDs in YAML
- Deserialize by resolving IDs from building data
- Requires two-pass deserialization or storing equipment separately

**Alternative:** Keep equipment at building/floor level, rooms reference by ID. This matches YAML structure better.

### Challenge 3: Backward Compatibility

**Problem:** Existing YAML files use current format.

**Solution:**
- Use serde attributes to support both formats
- Add `#[serde(alias = "...")]` for field name variations
- Use versioned serialization if needed

### Challenge 4: Performance

**Problem:** Custom serialization might be slower.

**Solution:**
- Benchmark before/after
- Use serde's built-in optimizations
- Cache serialized forms if needed

---

## Testing Strategy

### Unit Tests
1. Test core type serialization to YAML
2. Test YAML deserialization to core types
3. Test backward compatibility with existing YAML files
4. Test conversion functions (should be identity)

### Integration Tests
1. Test full save/load cycle with core types
2. Test IFC import/export
3. Test mobile FFI compatibility
4. Test service layer (already uses core types)

### Migration Tests
1. Test loading old YAML files
2. Test saving new format
3. Test round-trip conversion

---

## Success Criteria

1. ✅ Core types serialize directly to YAML format
2. ✅ No conversion functions needed
3. ✅ Backward compatible with existing YAML files
4. ✅ All tests pass
5. ✅ Performance is acceptable (within 10% of current)
6. ✅ Code is simpler (fewer types, less conversion logic)

---

## Risks & Mitigation

### Risk 1: Breaking Changes
- **Mitigation**: Gradual migration, keep YAML types as aliases initially

### Risk 2: Performance Regression
- **Mitigation**: Benchmark early, optimize custom serializers

### Risk 3: Backward Compatibility Issues
- **Mitigation**: Extensive testing with existing YAML files

### Risk 4: Complex Custom Serialization
- **Mitigation**: Start simple, add complexity only if needed

---

## Timeline Estimate

- **Phase 1**: 2-3 days (Equipment + Room types)
- **Phase 2**: 1-2 days (Building + metadata)
- **Phase 3**: 2-3 days (Update all usage sites)
- **Phase 4**: 1 day (Testing + fixes)
- **Phase 5**: 1 day (Cleanup + documentation)

**Total**: ~7-10 days

---

## Next Steps

1. Review and approve this plan
2. Start with Phase 1 (Equipment type)
3. Test thoroughly before proceeding
4. Iterate based on findings

