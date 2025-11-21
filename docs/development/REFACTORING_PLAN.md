# Large File Refactoring Plan

**Date**: 2024-11-19
**Status**: Documented, ready for execution
**Estimated Effort**: 3-4 hours dedicated session

## Files Requiring Refactoring

### Priority 1: ifc/hierarchy/builder.rs (991 lines) - CRITICAL

**Current Structure**:
- Single large impl block for HierarchyBuilder
- Complex constructor with relationship parsing
- Mixed concerns: building, validation, transformation

**Proposed Split**:

```
ifc/hierarchy/
├── builder.rs (core building logic, ~500 lines)
│   - HierarchyBuilder struct
│   - new() constructor
│   - build() method
│   - Core hierarchy assembly
│
├── validator.rs (validation logic, ~300 lines)
│   - Validation methods extracted from builder
│   - Reference checking
│   - Integrity validation
│   - Error reporting
│
└── transforms.rs (transformations, ~200 lines)
    - Geometry transformations
    - Coordinate conversions
    - Bounding box calculations
```

**Refactoring Steps**:
1. Create validator.rs with validation trait
2. Extract validation methods to validator.rs
3. Create transforms.rs with transformation utilities
4. Extract transformation logic
5. Simplify builder.rs to core logic
6. Update imports throughout codebase
7. Run full test suite after each step
8. Verify no functionality regression

**Risk**: Medium - Complex code with many dependencies
**Benefit**: High - Improved maintainability, clearer separation

### Priority 2: render3d/interactive/mod.rs (810 lines)

**Current Structure**:
- Event handlers mixed with state management
- Keyboard and mouse handling inline

**Proposed Split**:

```
render3d/interactive/
├── mod.rs (state management, ~400 lines)
│   - InteractiveRenderer struct
│   - State management
│   - Rendering coordination
│
└── handlers/
    ├── keyboard.rs (~200 lines)
    │   - Keyboard event handling
    │   - Key bindings
    │
    └── mouse.rs (~200 lines)
        - Mouse event handling
        - Click/drag logic
```

**Refactoring Steps**:
1. Create handlers/ subdirectory
2. Create keyboard.rs with KeyboardHandler trait
3. Extract keyboard logic
4. Create mouse.rs with MouseHandler trait
5. Extract mouse logic
6. Update mod.rs to use handlers
7. Test rendering functionality

**Risk**: Low - Clear handler boundaries
**Benefit**: High - Much cleaner organization

### Priority 3: ifc/enhanced/spatial_index.rs (782 lines)

**Proposed Split**:

```
ifc/enhanced/
├── spatial_index.rs (indexing, ~400 lines)
│   - Index building
│   - Data structure management
│
└── spatial_query.rs (queries, ~400 lines)
    - Query operations
    - Search algorithms
    - Result filtering
```

**Risk**: Low - Natural read/write split
**Benefit**: Medium - Clearer intent

### Priority 4: render3d/renderer.rs (762 lines)

**Proposed Split**:

```
render3d/
├── renderer.rs (coordination, ~300 lines)
│   - Main renderer
│   - Strategy selection
│
└── strategies/
    ├── wireframe.rs (~150 lines)
    ├── solid.rs (~150 lines)
    ├── textured.rs (~150 lines)
    └── hybrid.rs (~150 lines)
```

**Risk**: Medium - Rendering logic may be intertwined
**Benefit**: High - Strategy pattern properly implemented

## Refactoring Best Practices

### Before Starting

1. **Ensure 100% tests passing** ✅ (Already done)
2. **Create feature branch**: `git checkout -b refactor/large-files`
3. **Commit current state**: Clean working directory
4. **Set aside dedicated time**: 3-4 hours uninterrupted

### During Refactoring

1. **One file at a time**: Complete each refactoring fully
2. **Small commits**: Commit after each successful extraction
3. **Test continuously**: Run tests after every change
4. **Update imports**: Fix all references immediately
5. **Document changes**: Update module docs

### Testing Strategy

```bash
# After each extraction
cargo build --lib
cargo test --lib
cargo clippy --lib

# Before committing
cargo test --all
cargo doc --no-deps
```

### Rollback Plan

If issues arise:
```bash
git checkout main
git branch -D refactor/large-files
```

Start over with lessons learned.

## Success Criteria

- [ ] All files <600 lines (target <500)
- [ ] Clear module boundaries
- [ ] 100% tests passing
- [ ] No clippy warnings introduced
- [ ] Documentation updated
- [ ] Import paths resolved

## Estimated Timeline

| File | Effort | Priority |
|------|--------|----------|
| builder.rs | 2 hours | 1 |
| interactive/mod.rs | 1 hour | 2 |
| spatial_index.rs | 1 hour | 3 |
| renderer.rs | 1.5 hours | 4 |

**Total**: 5.5 hours (do in 2 sessions)

## Code Quality Metrics (Post-Refactoring)

**Expected Improvements**:
- Average file size: 215 → ~180 lines
- Files >600 lines: 8 → 0
- Files >800 lines: 4 → 0
- Module cohesion: Improved
- Test maintainability: Improved

## Alternative: Gradual Refactoring

If full refactoring isn't feasible:

1. **Extract one piece at a time** (e.g., just validators from builder.rs)
2. **Ship incrementally** (each extraction is valuable)
3. **Improve over sprints** (Don't block on perfect)

## Conclusion

Large file refactoring is **ready to execute** with:
- ✅ Clear plan documented
- ✅ Files identified and analyzed
- ✅ Proposed structure defined
- ✅ Risk assessment complete
- ✅ Test strategy established

**Recommendation**: Schedule dedicated 4-hour refactoring session when:
- No production urgencies
- Full test suite passing
- Feature development paused
- Team has bandwidth for review

**Defer until**: Dedicated time available (not blocking production)
