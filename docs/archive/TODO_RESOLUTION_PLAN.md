# TODO Resolution Plan - Remaining 152 Items

## Reality Check

After filtering deprecated code (`internal/infrastructure/container/container.go` is old), here's the REAL breakdown:

### Active TODOs by Layer

| Layer | Count | Priority | Notes |
|-------|-------|----------|-------|
| **Use Cases** | 63 | HIGH | Business logic completions |
| **CLI Commands** | 36 | MEDIUM | Command implementations |
| **Interfaces/Handlers** | 17 | HIGH | API completions |
| **TUI** | 13 | LOW | Terminal UI features |
| **Infrastructure** | 4 | MEDIUM | Service wiring |
| **PKG** | 2 | LOW | Utility functions |
| ~~Deprecated~~ | ~~17~~ | N/A | Old container code |

**Real Total**: ~135 functional TODOs

## Categorization by Feature Area

### Version Control (Git-like) - **42 TODOs**
- Pull requests (merge, review, comments)
- Issues (auto-assignment, labels)
- Commits (actual merge logic)
- Rollback service (semantic versioning)
- **Status**: Foundation exists, workflow incomplete
- **Priority**: Medium (Priority #6 in original plan)

### IFC Import - **7 TODOs**
- Validation result conversion
- Spatial accuracy/coverage calculations
- Full IFC export (building → IFC entities)
- **Status**: Basic import works, enhancements needed
- **Priority**: Low (core features work)

### Design/CADTUI - **12 TODOs**
- Component selection
- Viewport management
- Undo/redo
- Tool implementations
- **Status**: Framework exists, features incomplete
- **Priority**: Low (advanced UI feature)

### BAS Integration - **5 TODOs**
- File processor wiring
- Point mapping
- System detection
- **Status**: Import works, automation needed
- **Priority**: Low (manual import works)

### CLI Commands - **36 TODOs**
- Branch operations (switch, merge, diff)
- Contributor management
- PR/Issue management
- Repository operations (clone, push, pull)
- Service commands
- **Status**: Basic commands work, Git workflow incomplete
- **Priority**: Medium

### TUI - **13 TODOs**
- PostGIS query implementations
- Energy calculations
- Floor count aggregations
- Spatial data conversions
- **Status**: UI works, data integrations incomplete
- **Priority**: Low (not blocking)

### Mobile/Handlers - **17 TODOs**
- AR metadata queries (check spatial_anchors table)
- Building anchor counts
- Equipment filter enhancements
- **Status**: Core features work, optimizations needed
- **Priority**: Low (non-critical enhancements)

## Resolution Strategy

### Batch 1: Critical Infrastructure (1 hour)
**Target**: 5 TODOs
- ✅ Version repository changes deserialization (DONE)
- BAS file processor wiring
- Daemon IFC service configuration

### Batch 2: Use Case Completions (3-4 hours)
**Target**: 20-30 high-value TODOs
- IFC validation conversions
- Version control placeholders (author, change counts)
- Issue/PR auto-assignment rules

### Batch 3: CLI Git Workflow (4-5 hours)
**Target**: 25-30 TODOs
- Branch switching
- Commit operations
- PR/Issue commands
- Contributor commands

### Batch 4: TUI & Polish (2-3 hours)
**Target**: 15-20 TODOs
- PostGIS query implementations
- Data aggregations
- UI enhancements

### Batch 5: Cleanup & Documentation (1 hour)
**Target**: Remaining TODOs
- Delete deprecated code
- Document limitations
- Mark future features

## Recommended Approach

**Option A: Feature-Complete Existing Priorities**
- Focus on TODOs in IFC, Mobile, Multi-user, Equipment
- Skip version control (Priority #6 for later)
- Target: ~40 TODOs (2-3 hours)

**Option B: Git Workflow (Priority #6)**
- Implement version control TODOs
- Complete PR/Issue/Branch commands
- Target: ~42 TODOs (6-8 hours)

**Option C: Mixed Approach**
- Resolve quick wins across all layers
- Skip complex features (CADTUI, undo/redo)
- Target: ~60 TODOs (4-5 hours)

## Next Step

**Which approach do you prefer?**
1. Feature-complete the 4 priorities we've implemented
2. Move to Priority #6 (Git workflow / version control)
3. Mixed approach - quick wins across all modules

**Current focus**: Waiting for your direction to stay on track! 🎯

