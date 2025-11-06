# Data Model Unification - Executive Summary

## The Problem

Currently, ArxOS has **two separate type systems**:

1. **Core Types** (`src/core/`) - Rich domain models with enums, timestamps, full objects
2. **YAML Types** (`src/yaml/`) - Serialization-friendly types with strings, IDs, simple types

This requires:
- Conversion functions between types (`src/yaml/conversions.rs`)
- Maintaining two sets of types
- Potential for inconsistencies
- Extra code complexity

## The Goal

**Unify to a single type system** where core types serialize directly to YAML format using serde attributes.

## Key Challenges

### 1. EquipmentStatus Semantic Mismatch ⚠️ **CRITICAL**

**Core:** Operational status (Active, Inactive, Maintenance, OutOfOrder)  
**YAML:** Health status (Healthy, Warning, Critical)

**These are different concepts!** A piece of equipment can be:
- Operationally Active but Health Warning (e.g., running but needs maintenance)
- Operationally Inactive but Health Healthy (e.g., turned off, working fine)

**Solution Options:**
- **Option A**: Keep both enums, use custom serializer to map
- **Option B**: Add `health_status` field to Equipment, keep `status` as operational
- **Option C**: Unify into single enum with both concepts

**Recommendation:** Option B - Add separate `health_status` field. This preserves semantic clarity.

### 2. Spatial Type Differences

**Core:** `core::Position` (with coordinate system)  
**YAML:** `spatial::Point3D` (simple x, y, z)

**These are different types in different modules!**

**Solution:** Use serde custom serialization to convert between them during serialization.

### 3. Room Equipment Structure

**Core:** `Vec<Equipment>` (full objects)  
**YAML:** `Vec<String>` (IDs only)

**Challenge:** YAML format stores equipment at floor level, rooms reference by ID. Core stores equipment in rooms.

**Solution:** 
- Serialize equipment as IDs in YAML
- Deserialize by resolving IDs from building data
- Requires two-pass deserialization or storing equipment separately

**Alternative:** Restructure core to match YAML (equipment at floor level, rooms reference by ID). This might be a better long-term solution.

### 4. Timestamps

**Core:** `created_at`, `updated_at` (DateTime<Utc>)  
**YAML:** None

**Solution:** Make timestamps optional, skip serialization if None.

---

## Recommended Approach

### Phase 1: Equipment Status (Most Critical)

**Decision:** Add `health_status` field to Equipment, keep `status` as operational.

```rust
pub struct Equipment {
    // ... existing fields ...
    pub status: EquipmentStatus,  // Operational: Active, Inactive, Maintenance, OutOfOrder
    pub health_status: Option<EquipmentHealthStatus>,  // Health: Healthy, Warning, Critical
}
```

**Benefits:**
- Preserves semantic clarity
- Backward compatible (health_status is optional)
- Can migrate gradually

### Phase 2: Spatial Types

**Decision:** Use serde custom serialization to convert `Position` ↔ `Point3D`.

**Implementation:**
- Create `src/core/serde_helpers/` module
- Implement custom Serialize/Deserialize for Position and BoundingBox
- Use `#[serde(with = "...")]` attribute

### Phase 3: Equipment Structure

**Decision:** Keep current structure for now, use custom serialization.

**Future consideration:** Restructure to match YAML (equipment at floor level) for better alignment.

### Phase 4: Add YAML-Only Features

**Decision:** Add optional fields to core types.

- Sensor mappings → `Option<Vec<SensorMapping>>` on Equipment
- Metadata → `Option<BuildingMetadata>` on Building
- Timestamps → `Option<DateTime<Utc>>` on Room/Equipment

---

## Implementation Strategy

### Incremental Approach

1. **Start with Equipment** (most used, most complex)
2. **Then Room** (depends on Equipment)
3. **Then Building** (depends on Room/Equipment)
4. **Finally cleanup** (remove YAML types, conversion functions)

### Backward Compatibility

- Keep YAML types as type aliases initially
- Update conversion functions to be pass-through
- Test with existing YAML files
- Gradual migration of call sites

### Testing Strategy

1. **Unit tests** for serialization/deserialization
2. **Integration tests** for save/load cycles
3. **Migration tests** with existing YAML files
4. **Performance tests** to ensure no regression

---

## Decision Points

### Decision 1: EquipmentStatus
- [ ] Option A: Keep both enums, use custom serializer
- [x] Option B: Add health_status field (RECOMMENDED)
- [ ] Option C: Unify into single enum

### Decision 2: Spatial Types
- [x] Option A: Keep separate, use custom serialization (RECOMMENDED)
- [ ] Option B: Unify into single type

### Decision 3: Room Equipment
- [x] Option A: Keep current structure, use custom serialization (RECOMMENDED)
- [ ] Option B: Restructure to match YAML (future consideration)

### Decision 4: Migration Strategy
- [x] Option A: Incremental, keep YAML types as aliases (RECOMMENDED)
- [ ] Option B: Big bang, replace all at once

---

## Success Metrics

1. ✅ Core types serialize directly to YAML
2. ✅ No conversion functions needed
3. ✅ Backward compatible with existing YAML files
4. ✅ All tests pass
5. ✅ Performance within 10% of current
6. ✅ Code is simpler (fewer types, less conversion)

---

## Next Steps

1. **Review this plan** and make decisions on key points
2. **Start with Phase 1** (Equipment status)
3. **Test thoroughly** before proceeding
4. **Iterate** based on findings

---

## Current vs Proposed Architecture

### Current Architecture (Before)

```
YAML File
  ↓
BuildingData (YAML type)
  ↓
[Conversion Functions]
  ↓
Building (Core type)
  ↓
Domain Logic
  ↓
[Conversion Functions]
  ↓
BuildingData (YAML type)
  ↓
YAML File
```

**Issues:**
- Two type systems to maintain
- Conversion functions required
- Potential for inconsistencies
- Extra complexity

### Proposed Architecture (After)

```
YAML File
  ↓
Building (Core type) - Direct deserialization
  ↓
Domain Logic
  ↓
Building (Core type) - Direct serialization
  ↓
YAML File
```

**Benefits:**
- Single type system
- No conversion functions
- Type safety
- Simpler code

---

## Visual Comparison

### Equipment Type (Current)

```
Core::Equipment {
  status: EquipmentStatus::Active  // Operational
  equipment_type: EquipmentType::HVAC
  position: Position { x, y, z, coordinate_system }
}
  ↓ [conversion]
YAML::EquipmentData {
  status: EquipmentStatus::Healthy  // Health (different!)
  equipment_type: "HVAC"  // String
  system_type: "HVAC"  // Derived
  position: Point3D { x, y, z }  // No coordinate system
}
```

### Equipment Type (Proposed)

```
Core::Equipment {
  status: EquipmentStatus::Active  // Operational
  health_status: Some(EquipmentHealthStatus::Healthy)  // Health
  equipment_type: EquipmentType::HVAC  // Enum
  position: Position { x, y, z, coordinate_system }
}
  ↓ [direct serialization with custom serde]
YAML {
  status: "Healthy"  // Serialized from health_status
  equipment_type: "HVAC"  // Serialized from enum
  system_type: "HVAC"  // Computed during serialization
  position: { x, y, z }  // Serialized from Position (coordinate_system omitted)
}
```

---

## Questions to Answer

1. **EquipmentStatus**: Should we add `health_status` field or unify enums?
2. **Spatial Types**: Should we unify `Position` and `Point3D` or keep separate?
3. **Room Equipment**: Should we restructure to match YAML (equipment at floor level)?
4. **Migration Timeline**: How aggressive should we be? Incremental or big bang?

