# ArxOS Enhancement Plan
**Version:** 1.0  
**Date:** December 8, 2025  
**Status:** Planning

## Executive Summary

This document outlines the engineering plan for addressing identified enhancement opportunities in ArxOS. The focus is on impact-driven development with clear acceptance criteria and minimal scope creep.

---

## Technical Context

### Architecture Constraints
- **Platform:** WASM PWA only (no native mobile apps)
- **Hardware Strategy:** Vendor integration first (BACnet, Modbus, MQTT)
- **Development Philosophy:** Ship working features, defer speculative work

### Current State Assessment
- ✅ Core terminal-first workflows functional
- ✅ Git-native storage working
- ✅ IFC import/export operational (90%+ geometries supported)
- ✅ Hardware integration via vendor protocols
- ✅ Agent-based remote management functional

---

## Enhancement Categories

### 1. IFC ExtrudedAreaSolid Bounding Box Edge Cases
**Priority:** LOW (P3)  
**Category:** Bug Fix / Quality Enhancement  
**Effort Estimate:** 2-3 days

#### Current State
- Location: `src/ifc/geometry.rs:652` (test marked `#[ignore]`)
- Implementation Status: 90% complete
- Edge Case: Complex profile geometries with rotations/transformations
- Impact: Minimal - spatial queries work for common cases, edge cases rare

#### Technical Analysis
```rust
// Current implementation in collect_points_from_extruded_area_solid()
// Handles: Basic profile extrusion, direction vectors, placement transforms
// Missing: Non-planar profiles, swept surfaces, complex boolean operations
```

The `compute_entity_bounding_box()` method successfully processes:
- ✅ Simple rectangular profiles
- ✅ Polyline-based profiles
- ✅ Basic placement transformations
- ✅ Standard extrusion directions
- ❌ Edge case: Non-orthogonal extrusions with complex profile rotations

#### Implementation Plan
**Phase 1: Reproduce Edge Cases (4 hours)**
1. Create test IFC files with known problematic geometries:
   - Rotated profile with angled extrusion
   - Multi-contour profiles
   - Boolean-modified solids
2. Run through parser, document failures
3. Add test cases to `geometry.rs` test suite

**Phase 2: Fix Core Issue (8 hours)**
1. Enhance `collect_points_from_extruded_area_solid()`:
   - Add profile rotation matrix composition
   - Handle composite transformations correctly
   - Validate extrusion direction normalization
2. Update `compute_bounds()` to handle degenerate cases
3. Add fuzzy comparison for floating-point edge cases

**Phase 3: Validation (4 hours)**
1. Un-ignore test at line 649
2. Add 3-5 new test cases covering edge geometries
3. Run full IFC test suite on `test_data/*.ifc` files
4. Document any remaining unsupported geometries

#### Acceptance Criteria
- [ ] Test `computes_bounding_box_for_extruded_solid` passes
- [ ] All `test_data/*.ifc` files parse without bounding box errors
- [ ] Edge case tests added to suite (min 3 new tests)
- [ ] Performance regression < 5% on benchmark suite

#### Decision Drivers
**Implement IF:**
- Users report spatial query failures in real-world IFC files
- Vendor integration requires accurate bounding boxes
- Required for regulatory compliance (building codes)

**Defer IF:**
- No user reports of geometry failures in 3+ months
- Workarounds exist (manual YAML overrides)
- Higher priority features pending

---

### 2. Interactive Search Browser
**Priority:** MEDIUM (P2)  
**Category:** UI Enhancement  
**Effort Estimate:** 3-5 days

#### Current State
- Location: Terminal-based search via `grep`, `list`, `show` commands
- Works well for CLI power users
- Room for UX improvement for less technical users

#### Proposed Enhancement
**Feature:** TUI-based fuzzy search browser with live filtering

**User Experience:**
```
┌─ ArxOS Search ────────────────────────────────────┐
│ 🔍 Search: hvac                                   │
├───────────────────────────────────────────────────┤
│ ▸ Equipment: HVAC-AHU-01  (Floor 2, Room 201)    │
│   Equipment: HVAC-VAV-12  (Floor 3, Room 305)    │
│   Room: HVAC Room         (Floor B1)             │
│   Tag: #hvac-maintenance                          │
├───────────────────────────────────────────────────┤
│ ↑↓ Navigate │ Enter: Select │ Esc: Cancel        │
└───────────────────────────────────────────────────┘
```

#### Implementation Plan
**Phase 1: Design (4 hours)**
1. Create UX mockups (ASCII art in doc)
2. Define search algorithm (fuzzy vs exact vs hybrid)
3. Identify data sources to search:
   - Rooms (name, tags, attributes)
   - Equipment (name, type, location)
   - Floors, Buildings
   - Git commit messages (optional)

**Phase 2: Core Search (8 hours)**
1. Add dependency: `fuzzy-matcher = "0.3"` to Cargo.toml
2. Create `src/tui/search.rs` module:
   ```rust
   pub struct SearchBrowser {
       query: String,
       results: Vec<SearchResult>,
       selected: usize,
   }
   ```
3. Implement search indexing on BuildingData
4. Add keyboard navigation (↑↓, Enter, Esc, Ctrl+N/P)

**Phase 3: Integration (8 hours)**
1. Add `search` command to CLI: `arx search [query]`
2. Integrate with existing TUI dashboard (Ctrl+F keybinding)
3. Add result actions:
   - Enter: Show detailed view
   - Ctrl+O: Open in editor
   - Ctrl+G: Show in git history

**Phase 4: Polish (4 hours)**
1. Add syntax highlighting for matched characters
2. Implement search history (LRU cache)
3. Add filtering options (--type room, --floor 2)
4. Write user documentation

#### Acceptance Criteria
- [ ] Fuzzy search matches expected results (precision >80%)
- [ ] Handles 1000+ entities without lag (<100ms response)
- [ ] Keyboard-only navigation (no mouse required)
- [ ] Integrates cleanly with existing TUI
- [ ] Documentation in CLI_REFERENCE.md

#### Decision Drivers
**Implement IF:**
- User feedback requests better discovery UX
- Adoption blocked by CLI complexity
- Vendor demo requires polished UI

**Defer IF:**
- Current CLI search adequate for power users
- No user complaints about discoverability
- Higher priority features pending

---

### 3. CRUD Commands (Room/Equipment)
**Priority:** LOW (P3)  
**Category:** Feature Completeness  
**Effort Estimate:** 5-8 days

#### Current State
- Location: `src/cli/commands/data.rs:19-131`
- Status: Intentionally stubbed with helpful error messages
- Current Workflow: Users edit YAML directly or use spreadsheet editor

**Stubbed Commands:**
```rust
arx room create   // "Use spreadsheet editor or YAML file"
arx room update   // "Use spreadsheet editor or YAML file"  
arx room delete   // "Use spreadsheet editor or YAML file"
arx equipment add // "Use spreadsheet editor or YAML file"
// ... etc
```

#### Design Philosophy
**Why Currently Stubbed:**
1. YAML editing is flexible and Git-friendly
2. Spreadsheet editor provides bulk operations
3. CRUD commands add complexity without clear value
4. Few users have requested this functionality

#### Implementation Plan (IF Needed)
**Phase 1: Requirements Gathering (8 hours)**
1. Survey users: "Would you use CLI CRUD commands?"
2. Analyze git logs: How often do users hand-edit YAML?
3. Define scope:
   - Interactive mode (prompts for fields) vs args
   - Validation rules
   - Git integration (auto-commit? confirmation?)

**Phase 2: Room CRUD (16 hours)**
1. `arx room create --name "Conference A" --floor 2 --area 450`
2. Implement `BuildingData::add_room()` with validation
3. Handle duplicates, floor references, auto-generate IDs
4. Add `arx room update --id room-12 --name "New Name"`
5. Add `arx room delete --id room-12 --confirm`
6. Write transaction log to git

**Phase 3: Equipment CRUD (16 hours)**
1. Similar to Room CRUD
2. Add `--location room-12` linking
3. Validate equipment types (HVAC, lighting, etc.)
4. Handle equipment removal (orphan warnings)

**Phase 4: Interactive Mode (8 hours)**
1. `arx room create --interactive`
2. TUI-based form with field validation
3. Preview changes before commit
4. Confirmation dialog

#### Acceptance Criteria
- [ ] All CRUD operations validate input
- [ ] Changes auto-commit to git with descriptive messages
- [ ] Rollback mechanism for failed operations
- [ ] Unit tests cover validation logic
- [ ] Integration tests verify git commits
- [ ] Error messages guide user to fix issues

#### Decision Drivers
**Implement IF:**
- 3+ users request this feature
- Vendor integrations need programmatic CRUD
- Scripting/automation use cases emerge

**Defer IF:**
- Current workflows adequate (YAML + git)
- No user demand after 6+ months
- Higher ROI features available

---

### 4. Reserved Spatial Functions
**Priority:** LOW (P3)  
**Category:** Future API Surface  
**Effort Estimate:** 8-12 days (deferred)

#### Current State
- Location: `src/spatial.rs` (module with basic point/bounds utilities)
- Status: Reserved for future spatial query enhancements
- Current Functionality: Basic bounding box, point-in-box queries

#### Potential Future Enhancements
```rust
// Deferred capabilities (implement only if needed):
pub trait SpatialIndex {
    fn find_nearest(&self, point: Point3D, n: usize) -> Vec<Entity>;
    fn find_within_radius(&self, point: Point3D, radius: f64) -> Vec<Entity>;
    fn intersects_volume(&self, bounds: BoundingBox) -> Vec<Entity>;
    fn path_between(&self, from: Entity, to: Entity) -> Option<Vec<Entity>>;
}
```

#### Decision Drivers
**DO NOT IMPLEMENT unless:**
- Building automation requires zone-based queries
- Pathfinding needed for robotics integration
- Regulatory compliance requires spatial analysis
- 3D visualization needs spatial indexing

**Current Assessment:** Not needed. Core workflows don't require advanced spatial queries.

---

### 5. Additional IFC Geometry Types
**Priority:** LOW (P3)  
**Category:** Format Support Expansion  
**Effort Estimate:** Variable (10-40 hours per geometry type)

#### Current Support Matrix
| Geometry Type               | Status      | Usage Frequency |
|----------------------------|-------------|-----------------|
| IFCEXTRUDEDAREASOLID       | ✅ 90%      | Very Common     |
| IFCPOLYLINE                | ✅ Complete | Very Common     |
| IFCAXIS2PLACEMENT3D        | ✅ Complete | Very Common     |
| IFCCARTESIANPOINT          | ✅ Complete | Very Common     |
| IFCBOOLEANCLIPPINGRESULT   | ❌ Unsupported | Rare         |
| IFCFACETEDBREP             | ❌ Unsupported | Rare         |
| IFCSWEPTDISKSOLID          | ❌ Unsupported | Rare         |
| IFCCSGSOLID                | ❌ Unsupported | Very Rare    |
| IFCTESSELLATEDITEM         | ❌ Unsupported | Uncommon     |

#### Strategy
**Implement on Demand:** Add geometry types only when:
1. Real-world IFC file fails to parse
2. Vendor requires specific geometry support
3. User reports missing building data

**Current Coverage:** ~85% of real-world IFC files parse completely

#### Implementation Template (Per Geometry Type)
1. Add entity type detection in `collect_points_from_shape()`
2. Implement `collect_points_from_<geometry_type>()` method
3. Add transformation logic
4. Create test case with sample IFC snippet
5. Validate against test_data files

**Effort:** 10-40 hours per geometry type depending on complexity

---

## Implementation Prioritization Framework

### Decision Matrix
```
Priority = (User Impact × Frequency) / (Implementation Cost × Maintenance Burden)

P1 (High):    Priority > 5.0  → Implement immediately
P2 (Medium):  Priority 2-5    → Implement if resources available
P3 (Low):     Priority < 2.0  → Defer until user demand confirmed
```

### Current Priorities
1. **P3** - IFC ExtrudedAreaSolid edge cases (Low impact, rare occurrence)
2. **P2** - Interactive search browser (Medium impact, UX enhancement)
3. **P3** - CRUD commands (Low demand, workarounds exist)
4. **P3** - Reserved spatial functions (Speculative, no current need)
5. **P3** - Additional IFC geometries (On-demand only)

---

## Engineering Best Practices

### Development Workflow
1. **Write Tests First**: Add failing test before implementation
2. **Incremental Commits**: Commit working code frequently
3. **Feature Flags**: Use Cargo features for experimental code
4. **Documentation**: Update CLI_REFERENCE.md with new features
5. **Performance**: Benchmark before/after (target: <5% regression)

### Code Quality Gates
- [ ] All tests pass (`cargo test --all-features`)
- [ ] No new warnings (`cargo clippy --all-features`)
- [ ] Benchmarks stable (`cargo bench`)
- [ ] Documentation updated
- [ ] Git commit message follows convention

### Rollback Strategy
All features should be:
- Gated behind feature flags if experimental
- Reversible via git revert
- Disabled via runtime configuration if needed

---

## Architectural Decisions

### AD-001: WASM PWA Only (No Native Mobile)
**Status:** Accepted  
**Date:** December 8, 2025  

**Context:**  
Previously considered native mobile apps (Android/iOS) with FFI layer. This adds significant complexity:
- Platform-specific builds (Android Studio, Xcode)
- FFI bindings maintenance (JNI, Objective-C)
- App store submission process
- Platform-specific UI frameworks

**Decision:**  
Focus exclusively on WASM PWA (Progressive Web App):
- Single codebase (Rust → WASM)
- Works on all platforms via browser
- No app store gatekeeping
- Offline-capable via service workers
- Terminal emulation in browser (xterm.js)

**Consequences:**
- ✅ Faster development cycle
- ✅ Easier maintenance
- ✅ Broader platform support
- ❌ No access to native device APIs (acceptable for our use case)
- ❌ Requires modern browser (2020+)

**Action Items:**
- [ ] Remove FFI test files: `tests/README_ANDROID_AR_TESTS.md`, `tests/README_MOBILE_FFI_TESTS.md`
- [ ] Archive mobile docs: `docs/mobile/` → `docs/archive/mobile/`
- [ ] Update README.md to reflect WASM-first approach
- [ ] Document browser requirements in QUICK_START_GUIDE.md

---

### AD-002: Vendor-First Hardware Integration
**Status:** Accepted  
**Date:** December 8, 2025

**Context:**  
Two approaches to hardware sensor integration:
1. Native development: Build our own sensor drivers, protocols, firmware
2. Vendor integration: Connect to existing BACnet/Modbus/MQTT systems

**Decision:**  
Prioritize vendor integration (BACnet, Modbus, MQTT):
- Leverage existing building automation infrastructure
- Faster time-to-market
- Lower support burden
- Industry-standard protocols

Native development deferred to future (open-source hardware community):
- May develop for specific use cases later
- Focus on reference implementations
- Community-driven, not core product

**Consequences:**
- ✅ Immediate compatibility with 90% of building systems
- ✅ Lower development cost
- ✅ Proven, reliable protocols
- ❌ Dependent on vendor API stability
- ❌ Limited control over hardware features

**Action Items:**
- [ ] Document vendor integration guide: `docs/VENDOR_INTEGRATION.md` (already exists ✓)
- [ ] Create vendor certification checklist
- [ ] Prioritize BACnet/Modbus testing
- [ ] Archive speculative native hardware docs

---

## Maintenance Strategy

### Deferred Work Management
- Tag GitHub issues with `P3-deferred` label
- Document decision rationale in issue comments
- Review deferred items quarterly
- Promote to active if user demand increases

### User Feedback Loop
- Monitor GitHub issues for feature requests
- Track CLI command usage via telemetry (opt-in)
- Survey users quarterly on pain points
- Prioritize based on frequency × impact

### Technical Debt Prevention
- No placeholder implementations without issue tracking
- All `#[ignore]` tests must have linked issue
- Document "why not implemented" in comments
- Review deferred decisions every 6 months

---

## Appendix

### Test Coverage Goals
- Core functionality: >90% coverage
- CLI commands: >80% coverage
- IFC parsing: >85% real-world file support
- Hardware integration: Mock-based unit tests + vendor interop tests

### Performance Targets
- IFC parse time: <5s for 10MB file
- Git operations: <1s for standard building repo
- Search response: <100ms for 1000 entities
- Memory usage: <500MB for typical building

### Documentation Requirements
- All public APIs have rustdoc comments
- CLI commands documented in CLI_REFERENCE.md
- Architecture decisions in this document
- User workflows in QUICK_START_GUIDE.md

---

## Review Schedule

- **Next Review:** March 2026 (3 months)
- **Review Triggers:**
  - 3+ users request same feature
  - Vendor partnership requires new capability
  - Regulatory requirement emerges
  - Performance degradation detected

---

**Document Owner:** Development Team  
**Approval Required:** Technical Lead  
**Last Updated:** December 8, 2025
