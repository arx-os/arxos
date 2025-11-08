# Technical Debt Register

**Last Updated:** January 2025  
**Purpose:** Track known architectural improvements for future releases

---

## Operations Module Coupling

**Priority:** Low  
**Status:** Documented for Future Enhancement  
**Impact:** Architectural improvement, not blocking

### Current State

The `src/core/operations.rs` module has dependencies on:
- `crate::yaml::conversions` - For data conversion
- `crate::persistence::PersistenceManager` - For data access

### Issue

While not a critical problem, the operations module is tightly coupled to persistence and YAML layers. This makes it harder to:
- Test operations in isolation
- Swap out persistence implementations
- Reuse operations in different contexts

### Proposed Solution

**Option 1: Service Layer (Recommended)**
- Create `crates/arxos/crates/arxos/src/services/spatial_service.rs`
- Move spatial operations to service layer
- Use dependency injection for persistence
- Operations module becomes thin wrapper

**Option 2: Move to Commands**
- Move operations closer to where they're used
- Commands module already has access to persistence
- Reduces indirection

**Option 3: Dependency Injection**
- Pass persistence manager as parameter
- Operations become pure functions
- Better testability

### Recommendation

**For v1.0:** ✅ Acceptable as-is  
**For v1.1+:** Consider Option 1 (Service Layer)

**Rationale:**
- No circular dependencies (already resolved)
- Clear separation of concerns
- Works correctly for current use cases
- Architectural improvement, not bug fix

---

## Data Model Duplication

**Priority:** Low  
**Status:** Acceptable for v1.0  
**Impact:** Maintenance overhead

### Current State

- Core types: `Room`, `Equipment`, `Building` (in `src/core/`)
- YAML types: `RoomData`, `EquipmentData`, `BuildingData` (in `src/yaml/`)
- Conversion functions: `src/yaml/conversions.rs`

### Issue

Two separate data models require:
- Conversion functions between types
- Maintenance of both models
- Potential for inconsistencies

### Proposed Solution

**Option 1: Derive Serialization from Core**
- Add `Serialize`/`Deserialize` to core types
- Use core types directly for YAML
- Remove YAML types

**Option 2: Auto-Generate Conversions**
- Use macros to generate conversions
- Single source of truth
- Automatic sync

**Option 3: Keep Current Approach**
- Maintain explicit conversions
- Clear separation of concerns
- Better control over serialization

### Recommendation

**For v1.0:** ✅ Current approach is acceptable  
**For v2.0:** Consider Option 1 if maintenance becomes burdensome

---

## Performance Optimizations

**Priority:** Low  
**Status:** Future Enhancement  
**Impact:** Performance improvements

### Areas for Optimization

1. **Spatial Query Indexing**
   - Current: O(n) linear search
   - Future: R-tree or spatial index for O(log n) queries

2. **Validation Caching**
   - Cache validation results
   - Invalidate on changes
   - Reduce redundant checks

3. **Batch Operations**
   - Batch file I/O operations
   - Reduce filesystem calls
   - Improve performance

### Recommendation

**For v1.0:** ✅ Current performance is acceptable  
**For v1.1+:** Add spatial indexing if needed

---

## Documentation

**Priority:** Low  
**Status:** Ongoing  
**Impact:** Developer experience

### Areas for Improvement

1. **API Documentation**
   - More examples in doc comments
   - Better error message documentation
   - Usage patterns

2. **Architecture Diagrams**
   - Visual representation of module structure
   - Data flow diagrams
   - Component interactions

3. **Migration Guides**
   - Guide for upgrading between versions
   - Breaking change documentation
   - Deprecation notices

### Recommendation

**For v1.0:** ✅ Current documentation is good  
**For v1.1+:** Enhance as needed

---

## Summary

**Total Technical Debt Items:** 4  
**Blocking v1.0:** 0  
**Recommended for v1.1+:** 2  
**Nice to Have:** 2

**V1.0 Recommendation:** ✅ **PROCEED** - All technical debt is non-blocking and can be addressed in future releases.

