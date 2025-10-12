# ArxOS Development Action Plan
## Resolution Strategy for 197 TODO Items

**Last Updated:** October 11, 2025
**Status:** Planning Phase
**Goal:** Complete full-featured ArxOS with all interfaces working

---

## Executive Summary

This plan addresses all 197 TODO items organized by Joel's priorities. **We're building the full vision** - CLI, Mobile, Web API, IFC import, multi-user support, and all equipment systems (electrical, HVAC, AV, networking, BAS, etc.).

### Joel's Priority Order
1. **IFC Import** - Primary data source for building geometry
2. **Mobile App** - Field tech data collection interface
3. **Multi-user Support** - Team collaboration
4. **Equipment Systems** - All types (electrical, HVAC, AV, networking, BAS, etc.)

### Realistic Timeline

**Total Effort:** 284 hours (7 full-time weeks or 41 weeks at 7 hours/week)

| Phase | Focus | TODO Count | Timeline | Hours |
|-------|-------|-----------|----------|-------|
| **Phase 1: Foundation** | Infrastructure + Database | 28 | Weeks 1-6 | 40h |
| **Phase 2: IFC Import** | Geometry + Building Data | 23 | Weeks 7-10 | 32h |
| **Phase 3: Mobile API** | HTTP Handlers + Spatial | 36 | Weeks 11-16 | 48h |
| **Phase 4: Multi-user** | Auth + Permissions | 12 | Weeks 17-19 | 16h |
| **Phase 5: Equipment Systems** | All system types | 15 | Weeks 20-23 | 20h |
| **Phase 6: Version Control** | Git-like workflow | 42 | Weeks 24-32 | 64h |
| **Phase 7: Advanced UI** | TUI + Design tools | 30 | Weeks 33-40 | 48h |
| **Phase 8: Polish** | Testing + Optimization | 11 | Weeks 41-44 | 16h |
| **TOTAL** | **All Features** | **197** | **44 weeks** | **284h** |

**At 7 hours/week:** ~10 months
**At 10 hours/week:** ~7 months
**At 20 hours/week (sprints):** ~3.5 months

---

## Phase 1: Foundation (Weeks 1-6, 40 hours)

**Goal:** Get database, repositories, and basic CLI working

### Critical Infrastructure TODOs (28 items)

#### 1. Database & Container Setup (4 items - 4 hours)

```
File: internal/app/container.go
Lines: 280, 636

Tasks:
- [ ] Week 1: Parse timeout from config (1h)
- [ ] Week 1: Add Close method to cache interface (1h)

File: internal/infrastructure/logger.go
Lines: 132, 140

Tasks:
- [ ] Week 1: Add proper timestamp to logs (1h)
- [ ] Week 1: Implement JSON marshaling for structured logs (1h)

Complexity: Low
Dependencies: None
Priority: P0 - Must work for everything else
```

#### 2. PostGIS Spatial Queries (7 items - 16 hours)

```
File: internal/infrastructure/database.go
Lines: 191, 197

File: internal/infrastructure/postgis/spatial_repo.go
Lines: 358, 363, 368, 373

Tasks:
- [ ] Week 2: Implement basic PostGIS spatial queries (ST_X, ST_Y, ST_Z) (4h)
- [ ] Week 2: Implement PostGIS nearest neighbor queries (ST_Distance) (3h)
- [ ] Week 3: Implement spatial update functionality (2h)
- [ ] Week 3: Implement spatial delete functionality (2h)
- [ ] Week 3: Implement equipment position updates (3h)
- [ ] Week 4: Implement spatial analytics (ST_Area, ST_Union, etc.) (2h)

Complexity: Medium-High (requires PostGIS knowledge)
Dependencies: Database setup
Priority: P0 - Core spatial functionality
Testing: Create test building, query by location
```

#### 3. Repository Deserialization (10 items - 12 hours)

```
File: internal/infrastructure/repository/postgis_repository_repo.go
Lines: 90, 96, 138

File: internal/infrastructure/repository/postgis_version_repo.go
Lines: 92, 134, 181, 228

File: internal/infrastructure/postgis/bas_point_repo.go
Line: 193

File: internal/infrastructure/postgis/branch_repo.go
Line: 659

Tasks:
- [ ] Week 3: Implement structure JSON deserialization (3h)
- [ ] Week 3: Load actual version objects from JSON (2h)
- [ ] Week 4: Implement changes JSON deserialization (3h)
- [ ] Week 4: Get version ID from context (1h)
- [ ] Week 4: Implement branch graph traversal (3h)

Complexity: Medium
Dependencies: Database schema in place
Priority: P0 - Required for data persistence
Testing: Roundtrip serialize/deserialize tests
```

#### 4. CLI Context & Basic Commands (7 items - 8 hours)

```
File: internal/cli/context.go
Line: 176

File: internal/cli/commands/system.go
Line: 74

File: internal/cli/commands/services.go
Line: 42

File: internal/cli/commands/init.go
Line: 57

Tasks:
- [ ] Week 4: Implement io.Reader to []byte conversion (1h)
- [ ] Week 5: Implement actual installation logic (2h)
- [ ] Week 5: Implement daemon service integration (2h)
- [ ] Week 5: Implement initialization logic (create dirs, config) (3h)

Complexity: Low-Medium
Dependencies: None
Priority: P0 - Foundation for CLI
Testing: Run init, verify directories created
```

### Phase 1 Exit Criteria

✅ Database setup with PostGIS working
✅ Can create building via CLI and retrieve it
✅ Spatial queries working (can query equipment by location)
✅ Repository layer persisting/loading data correctly
✅ Basic CLI commands functional

---

## Phase 2: IFC Import - Priority #1 (Weeks 7-10, 32 hours)

**Goal:** Import IFC files and populate building geometry/structure

### IFC Processing TODOs (13 items - 24 hours)

```
File: internal/usecase/ifc_usecase.go
Lines: 63, 77, 78, 79, 80, 123, 140, 151, 152, 153

File: internal/infrastructure/services/daemon.go
Line: 241

File: internal/infrastructure/services/file_processor.go
Lines: 223, 236

Tasks:
- [ ] Week 7: Get IFC service from daemon configuration (1h)
- [ ] Week 7: Implement discipline detection from IFC data (3h)
      - Detect architectural, structural, MEP, etc. from IFC schema
- [ ] Week 7: Extract properties from IFC parse result (3h)
      - Material properties, dimensions, manufacturer info
- [ ] Week 8: Extract materials from IFC data (2h)
- [ ] Week 8: Extract IFC classifications (IfcClassification) (2h)
- [ ] Week 8: Extract warnings from parse results (2h)
      - Invalid geometry, missing references, etc.
- [ ] Week 9: Implement actual file reading from repository (3h)
      - Read IFC files from building repository
- [ ] Week 9: Convert validation results to test results (2h)
- [ ] Week 9: Calculate accuracy from validation results (2h)
      - Compare parsed vs. expected element counts
- [ ] Week 10: Calculate coverage from validation (2h)
      - Percentage of IFC elements successfully parsed
- [ ] Week 10: Extract spatial errors (dimension mismatches, etc.) (2h)

Complexity: High (requires IFC schema knowledge)
Dependencies: IfcOpenShell service working, Repository layer working
Priority: P1 - #1 priority per Joel
Testing: Import real IFC file from school, verify building structure
```

### IFC HTTP Handlers (10 items - 8 hours)

```
File: internal/interfaces/http/handlers/ifc_handler.go
Lines: 147, 166, 185, 198, 211, 230, 249, 268, 287

File: internal/interfaces/http/handlers/building_handler.go
Lines: 239, 258

Tasks:
- [ ] Week 10: Implement ExportIFC in use case (1h)
- [ ] Week 10: Implement GetImportJob status tracking (1h)
- [ ] Week 10: Implement GetExportJob status tracking (1h)
- [ ] Week 10: Implement ListImportJobs (1h)
- [ ] Week 10: Implement ListExportJobs (1h)
- [ ] Week 10: Implement CancelImportJob (1h)
- [ ] Week 10: Implement CancelExportJob (1h)
- [ ] Week 10: Implement GetImportJobLogs (0.5h)
- [ ] Week 10: Implement GetExportJobLogs (0.5h)

Complexity: Medium
Dependencies: IFC use case working
Priority: P1 - Needed for mobile/web interface to IFC
Testing: Import IFC via HTTP POST, check job status
```

### Phase 2 Exit Criteria

✅ Can import IFC file via CLI
✅ IFC parser extracts all properties, materials, classifications
✅ Building structure auto-created from IFC geometry
✅ Can query imported building data
✅ HTTP endpoints for IFC import/export working

---

## Phase 3: Mobile API - Priority #2 (Weeks 11-16, 48 hours)

**Goal:** Complete HTTP API for mobile app data collection

### Spatial HTTP Handlers (10 items - 12 hours)

```
File: internal/interfaces/http/handlers/spatial_handler.go
Lines: 87, 138, 233, 305, 374

Tasks:
- [ ] Week 11: Implement spatial anchor creation (2h)
      - Create AR anchors with GPS + local coordinates
- [ ] Week 11: Implement spatial anchor query using PostGIS (2h)
      - Query anchors by building, floor, or proximity
- [ ] Week 12: Implement PostGIS query for nearby equipment (3h)
      - ST_DWithin for radius-based search
- [ ] Week 12: Implement spatial mapping storage (2h)
      - Store AR spatial maps uploaded from mobile
- [ ] Week 12: Add Description field to Building domain model (1h)
- [ ] Week 12: Update building handlers to use description (2h)

Complexity: Medium-High
Dependencies: PostGIS spatial queries working
Priority: P1 - #2 priority per Joel, required for mobile AR
Testing: Create anchor via API, query nearby equipment
```

### Mobile-Specific Handlers (7 items - 10 hours)

```
File: internal/interfaces/http/handlers/mobile_handler.go
Lines: 101, 146, 148, 215, 217

File: internal/interfaces/http/handlers/component_handler.go
Line: 397

Tasks:
- [ ] Week 13: Enhance EquipmentFilter domain model (2h)
      - Add mobile-specific filters (hasPhoto, needsInspection, etc.)
- [ ] Week 13: Check spatial_anchors table for AR anchor status (2h)
      - Query if equipment has AR anchor
- [ ] Week 13: Determine AR status (not_mapped/pending/mapped) (2h)
- [ ] Week 14: Implement GetComponentHistory in use case (3h)
      - Return change history for equipment
- [ ] Week 14: Update mobile equipment responses with AR data (1h)

Complexity: Medium
Dependencies: Spatial handlers working
Priority: P1 - Mobile app requires these
Testing: Mobile app can fetch equipment with AR status
```

### User Management Handlers (5 items - 8 hours)

```
File: internal/interfaces/http/handlers/user_handler.go
Lines: 287, 361, 380

File: internal/interfaces/http/handlers/auth_handler.go
Line: 382

Tasks:
- [ ] Week 14: Implement GetUserByEmail in use case (2h)
- [ ] Week 15: Implement ActivateUser in use case (2h)
- [ ] Week 15: Implement DeactivateUser in use case (2h)
- [ ] Week 15: Implement token blacklisting/revocation (2h)
      - Store revoked tokens in Redis or database

Complexity: Medium
Dependencies: User use case working
Priority: P1 - Multi-user support (#3 priority)
Testing: Create user, activate, deactivate, revoke token
```

### TUI PostGIS Integration (14 items - 18 hours)

```
File: internal/tui/services/postgis_client.go
Lines: 114, 139, 201, 247, 286, 312, 328

File: internal/tui/models/spatial_query.go
Line: 483

File: internal/tui/models/dashboard.go
Line: 222

File: internal/tui/services/data_service.go
Lines: 282, 283

File: internal/interfaces/tui/cadtui.go
Lines: 240, 241, 309, 314

Tasks:
- [ ] Week 15: Implement real PostGIS query for TUI (3h)
- [ ] Week 15: Implement PostGIS spatial queries (ST_X, ST_Y, ST_Z) for TUI (2h)
- [ ] Week 16: Implement PostGIS ST_Area, ST_Union for TUI (2h)
- [ ] Week 16: Implement comprehensive spatial query functions (3h)
- [ ] Week 16: Implement floor-specific equipment queries (2h)
- [ ] Week 16: Implement ST_DWithin spatial query (2h)
- [ ] Week 16: Implement ST_Within spatial query (2h)
- [ ] Week 16: Convert spatialData to TUI display format (1h)
- [ ] Week 16: Get actual floor count from building data (0.5h)
- [ ] Week 16: Implement energy calculation (defer or placeholder) (0.5h)

Complexity: Medium
Dependencies: PostGIS queries working
Priority: P2 - Nice to have working TUI
Testing: Open TUI, verify it shows real building data
```

### Phase 3 Exit Criteria

✅ Mobile app can fetch equipment lists
✅ Mobile app can create AR anchors
✅ Mobile app can query nearby equipment
✅ Mobile app can upload photos/data
✅ User management API working
✅ TUI displays real database data

---

## Phase 4: Multi-user Support - Priority #3 (Weeks 17-19, 16 hours)

**Goal:** Secure multi-user authentication and authorization

### Authentication & User Management (6 items - 12 hours)

```
File: internal/usecase/user_usecase.go
Line: 294

File: internal/usecase/auth_usecase.go
Line: 100

Tasks:
- [ ] Week 17: Implement proper password verification (3h)
      - bcrypt hash comparison
      - Rate limiting on failed attempts
- [ ] Week 17: Implement proper password verification with stored hash (3h)
      - Load user from database
      - Compare hashed passwords
      - Return JWT token on success
- [ ] Week 18: Add password complexity requirements (2h)
      - Min length, special chars, etc.
- [ ] Week 18: Implement password reset flow (2h)
      - Email token, reset link
- [ ] Week 19: Add audit logging for auth events (2h)
      - Log logins, logouts, failed attempts

Complexity: Medium (security-critical)
Dependencies: User repository working
Priority: P1 - #3 priority per Joel
Testing: Create user, login, logout, verify tokens
```

### Container Wiring for Missing Repos (6 items - 4 hours)

```
File: internal/infrastructure/container/container.go
Lines: 70, 73, 74, 75, 76, 77, 78, 90, 91, 97, 101, 106, 107, 118

Tasks:
- [ ] Week 19: Wire CommitRepository (already implemented, just needs wiring) (1h)
- [ ] Week 19: Wire ContributorRepository (already implemented) (1h)
- [ ] Week 19: Wire TeamRepository (already implemented) (1h)
- [ ] Week 19: Wire RoomRepository (already implemented) (0.5h)
- [ ] Week 19: Wire EquipmentRepository (already implemented) (0.5h)

Complexity: Low
Dependencies: Repositories exist, just need container wiring
Priority: P1 - Required for full functionality
Testing: Verify getters work, repositories accessible
```

### Phase 4 Exit Criteria

✅ Multiple users can log in with separate credentials
✅ Password hashing and verification working
✅ Token refresh and revocation working
✅ All repositories wired in container
✅ Audit logging for security events

---

## Phase 5: Equipment Systems (Weeks 20-23, 20 hours)

**Goal:** Support all equipment system types, not just BAS

### Equipment System Import & Management (15 items - 20 hours)

**Note:** BAS is just one of many equipment system types (electrical, HVAC, AV, networking, fire safety, security, etc.). The import mechanism should work for ANY system CSV.

```
File: internal/cli/commands/bas.go
Lines: 211, 310, 361, 393

File: internal/usecase/bas_import_usecase.go
Lines: 133, 139, 156, 298

File: internal/infrastructure/services/file_processor.go
Lines: 223, 236

Tasks:
- [ ] Week 20: Rename "BAS Import" to "Equipment Import" (generic) (1h)
      - Make it work for any equipment type CSV
      - BAS, electrical panels, HVAC units, AV equipment, network gear, etc.

- [ ] Week 20: Check if system already exists and reuse it (2h)
      - Avoid creating duplicate systems

- [ ] Week 21: Implement unmapped equipment listing (2h)
      - Show equipment not yet assigned to rooms/locations

- [ ] Week 21: Implement smart equipment mapping (4h)
      - Auto-map equipment to rooms based on naming conventions
      - "RM-301-HVAC-01" → Room 301

- [ ] Week 22: Implement equipment point updates (3h)
      - Update existing equipment when re-importing CSV

- [ ] Week 22: Implement soft delete for removed equipment (2h)
      - Mark as inactive instead of deleting

- [ ] Week 23: Integrate with version control system (3h)
      - Track equipment changes as commits

- [ ] Week 23: Wire equipment import to file processor daemon (2h)
      - Auto-import when CSV dropped in watched folder

- [ ] Week 23: Test with multiple system types (1h)
      - Import HVAC CSV, electrical panel CSV, AV equipment CSV

Complexity: Medium
Dependencies: Repository layer working
Priority: P1 - Core functionality, #4 priority per Joel
Testing: Import CSV with equipment, verify auto-mapping, update equipment, verify changes tracked
```

### Phase 5 Exit Criteria

✅ Can import any equipment system type via CSV
✅ Smart room mapping working (auto-assigns equipment to rooms)
✅ Equipment updates tracked in version control
✅ Can handle electrical, HVAC, AV, networking, BAS, etc.
✅ File watcher daemon auto-imports new CSVs

---

## Phase 6: Version Control - Git Workflow (Weeks 24-32, 64 hours)

**Goal:** Complete Git-like version control for building changes

### Branch Operations (6 items - 12 hours)

```
File: internal/cli/commands/branch.go
Lines: 269, 303, 351, 402, 466, 554

File: internal/usecase/branch_usecase.go
Lines: 161, 162, 163, 181, 182

Tasks:
- [ ] Week 24: Wire branch use case to service context (2h)
- [ ] Week 24: Implement get branch details from use case (2h)
- [ ] Week 25: Implement get commits from use case (2h)
- [ ] Week 25: Implement get diff from use case (3h)
- [ ] Week 26: Update working directory on checkout (1h)
- [ ] Week 26: Load branch state on checkout (1h)
- [ ] Week 26: Check for uncommitted changes (warn if not force) (1h)

Complexity: High
Dependencies: Repository layer working
Priority: P2 - Advanced feature
Testing: Create branch, checkout, see changes isolated
```

### Pull Request/Work Order System (14 items - 24 hours)

```
File: internal/cli/commands/pr.go
Lines: 118, 283, 336, 370, 426, 456, 547, 603, 638, 690, 733, 768

File: internal/usecase/pull_request_usecase.go
Lines: 129, 130, 197, 198, 199, 254

Tasks:
- [ ] Week 27: Get actual current branch (1h)
- [ ] Week 27: Wire PR use case to service context (1h)
- [ ] Week 27: Implement get PR details from use case (2h)
- [ ] Week 28: Add reviewers to PR (2h)
- [ ] Week 28: Log PR activity (1h)
- [ ] Week 28: Implement PR approval via use case (2h)
- [ ] Week 29: Implement PR merge via use case (3h)
- [ ] Week 29: Perform actual branch merge (4h)
- [ ] Week 29: Create merge commit (2h)
- [ ] Week 30: Update building state on merge (3h)
- [ ] Week 30: Implement PR close via use case (1h)
- [ ] Week 30: Implement add comment via use case (1h)
- [ ] Week 30: Implement rule-based PR auto-assignment (1h)

Complexity: High
Dependencies: Branch operations working
Priority: P2 - Work order system
Testing: Create PR, approve, merge, verify building updated
```

### Issue/Work Order Tracking (12 items - 16 hours)

```
File: internal/cli/commands/pr.go
Lines: 603, 638, 690, 733, 768

File: internal/usecase/issue_usecase.go
Lines: 99, 100, 144, 256

Tasks:
- [ ] Week 31: Implement get issues from use case (2h)
- [ ] Week 31: Implement get issue details from use case (2h)
- [ ] Week 31: Auto-apply labels to issues (2h)
- [ ] Week 31: Log issue activity (1h)
- [ ] Week 31: Get default branch for issue (1h)
- [ ] Week 32: Implement start work via use case (2h)
- [ ] Week 32: Implement resolve via use case (2h)
- [ ] Week 32: Implement close via use case (2h)
- [ ] Week 32: Implement rule-based issue auto-assignment (2h)

Complexity: Medium
Dependencies: Branch and PR working
Priority: P2 - Work order tracking
Testing: Create issue, start work, resolve, close
```

### Contributor Management (8 items - 8 hours)

```
File: internal/cli/commands/contributor.go
Lines: 56, 114, 150, 182, 245, 277, 310, 335

Tasks:
- [ ] Week 32: Implement add contributor via use case (1h)
- [ ] Week 32: Implement list contributors via use case (1h)
- [ ] Week 32: Implement remove contributor via use case (1h)
- [ ] Week 32: Implement update contributor via use case (1h)
- [ ] Week 32: Implement create team via use case (1h)
- [ ] Week 32: Implement list teams via use case (1h)
- [ ] Week 32: Implement add team member via use case (1h)
- [ ] Week 32: Implement remove team member via use case (1h)

Complexity: Low-Medium
Dependencies: User management working
Priority: P2 - Team collaboration
Testing: Add contributor, create team, manage members
```

### Version/Commit Management (12 items - 16 hours)

```
File: internal/usecase/version_usecase.go
Lines: 59, 60, 61, 67, 70, 80, 151, 162, 196, 224, 230, 235

File: internal/usecase/commit_usecase.go
Lines: 51, 71, 87

File: internal/usecase/snapshot_service.go
Lines: 314, 332, 350

File: internal/usecase/rollback_service.go
Line: 606

File: internal/usecase/repository_usecase.go
Lines: 80, 81, 90, 184, 263

Tasks:
- [ ] Week 32: Get user info from context/auth (Name, Email, ID) (2h)
- [ ] Week 32: Calculate actual changes for commit (3h)
- [ ] Week 32: Get system version from build info (1h)
- [ ] Week 32: Calculate changes between versions (3h)
- [ ] Week 32: Implement actual version comparison (3h)
- [ ] Week 32: Implement actual rollback logic (3h)
- [ ] Week 32: Implement proper semantic versioning (1h)

Complexity: High
Dependencies: Repository layer working
Priority: P2 - Version tracking
Testing: Make changes, commit, view diff, rollback
```

### Phase 6 Exit Criteria

✅ Can create branches for isolated work
✅ Can create PRs for review
✅ Can merge PRs to update main branch
✅ Issues track work orders
✅ Contributors and teams managed
✅ Version history tracked
✅ Can rollback to previous versions

---

## Phase 7: Advanced UI (Weeks 33-40, 48 hours)

**Goal:** Complete TUI and design tools

### TUI Improvements (6 items - 12 hours)

```
File: internal/tui/main.go
Lines: 178, 188

File: internal/tui/models/dashboard.go
Line: 222

Tasks:
- [ ] Week 33: Implement energy visualization model (4h)
      - Display energy usage charts in TUI
- [ ] Week 34: Implement repository manager model (4h)
      - TUI interface to manage Git-like operations
- [ ] Week 34: Get actual floor count from building data (1h)
- [ ] Week 35: Polish TUI navigation and display (3h)

Complexity: Medium
Dependencies: PostGIS queries working, Version control working
Priority: P3 - Nice to have
Testing: Open TUI, navigate, verify displays
```

### Design/CADTUI Tools (15 items - 36 hours)

```
File: internal/usecase/design_usecase.go
Lines: 15, 174, 274, 280, 294, 300, 306, 312, 397, 402, 407, 412

File: internal/interfaces/tui/cadtui.go
Lines: 240, 241, 309, 314

Tasks:
- [ ] Week 35: Add visual renderer for CADTUI (6h)
- [ ] Week 36: Add animation engine (4h)
- [ ] Week 36: Implement component selection logic (3h)
- [ ] Week 37: Implement viewport management (get/set) (4h)
- [ ] Week 37: Implement zoom to component (3h)
- [ ] Week 38: Implement undo functionality (4h)
- [ ] Week 38: Implement redo functionality (2h)
- [ ] Week 39: Implement history tracking (3h)
- [ ] Week 39: Implement create component tool (2h)
- [ ] Week 39: Implement move component tool (2h)
- [ ] Week 40: Implement connect components tool (2h)
- [ ] Week 40: Implement zoom to fit tool (1h)

Complexity: Very High (building a CAD tool)
Dependencies: Component management working
Priority: P3 - Advanced feature
Testing: Open CADTUI, create components, move, connect, undo
```

### Utility Commands (9 items - 12 hours)

```
File: internal/cli/commands/utility.go
Lines: 21, 46, 72, 97

File: internal/cli/commands/import_export.go
Lines: 133, 163

File: internal/cli/commands/repository.go
Lines: 123, 151, 172

File: internal/usecase/building_usecase.go
Line: 242

Tasks:
- [ ] Week 40: Implement query execution (2h)
- [ ] Week 40: Implement connection tracing (3h)
- [ ] Week 40: Implement visualization generation (3h)
- [ ] Week 40: Implement report generation (2h)
- [ ] Week 40: Implement building export logic (1h)
- [ ] Week 40: Implement format conversion (1h)

Complexity: Medium
Dependencies: Repository layer working
Priority: P2-P3
Testing: Run queries, generate visualizations, export reports
```

### Phase 7 Exit Criteria

✅ TUI shows energy visualization
✅ TUI repository manager working
✅ CADTUI design tools functional
✅ Can visualize building geometry
✅ Advanced utility commands working

---

## Phase 8: Polish & Optimization (Weeks 41-44, 16 hours)

**Goal:** Test, optimize, and deploy

### Remaining TODOs & Cleanup (11 items - 16 hours)

```
File: internal/infrastructure/postgis/bas_point_repo_test.go
Lines: 18, 168, 265

File: internal/interfaces/http/router.go
Line: 187

Tasks:
- [ ] Week 41: Set up proper test database connection (2h)
- [ ] Week 41: Implement repository tests when database available (4h)
- [ ] Week 42: Move all handlers to Container for Clean Architecture (3h)
- [ ] Week 43: Performance optimization (4h)
      - Add database indexes
      - Optimize slow queries
      - Cache frequently accessed data
- [ ] Week 44: End-to-end testing (3h)
      - Test complete workflows
      - Fix any remaining bugs

Complexity: Low-Medium
Dependencies: Everything else working
Priority: P1 - Production readiness
Testing: Full regression test suite
```

### Documentation & Deployment (No TODOs, but critical)

```
Tasks:
- [ ] Week 44: Write deployment guide (4h)
- [ ] Week 44: Write user documentation (4h)
- [ ] Week 44: Create video tutorials (4h)
- [ ] Week 44: Set up production environment (4h)
- [ ] Week 44: Deploy to school district servers (2h)
- [ ] Week 44: Train first users (4h)

Complexity: Low
Dependencies: Everything working
Priority: P0 - Can't use it if not deployed
```

### Phase 8 Exit Criteria

✅ All 197 TODOs resolved
✅ Full test suite passing
✅ Performance optimized
✅ Documentation complete
✅ Deployed to production
✅ First users trained

---

## Realistic Timeline Scenarios

### Scenario 1: Steady Pace (7 hours/week)
- **Duration:** 41 weeks (~10 months)
- **Schedule:** 1 hour/day or 3.5 hours twice a week
- **Pros:** Sustainable alongside full-time job
- **Cons:** Longer to completion
- **Recommended:** Yes, if maintaining work-life balance

### Scenario 2: Sprint Mode (10 hours/week)
- **Duration:** 28 weeks (~7 months)
- **Schedule:** 2 hours/day or 5 hours twice a week
- **Pros:** Faster progress
- **Cons:** Requires discipline
- **Recommended:** Yes, if motivated

### Scenario 3: Aggressive (20 hours/week)
- **Duration:** 14 weeks (~3.5 months)
- **Schedule:** 4 hours/day or full weekends
- **Pros:** Fastest to completion
- **Cons:** Risk of burnout
- **Recommended:** Only for short bursts (1-2 month sprints)

### Scenario 4: Variable Pace
- **Weeks 1-10:** 10 hours/week (Foundation + IFC)
- **Weeks 11-20:** 7 hours/week (Mobile API + Multi-user)
- **Weeks 21-30:** 5 hours/week (Equipment + Version Control)
- **Weeks 31-40:** 7 hours/week (Advanced UI)
- **Weeks 41-44:** 10 hours/week (Polish + Deploy)
- **Total Duration:** 10 months
- **Recommended:** Yes, most realistic

---

## Progress Tracking

### Milestone Markers

**Month 1 (Weeks 1-4):** Foundation Complete
- [ ] Database + PostGIS working
- [ ] Repository layer functional
- [ ] Basic CLI CRUD working
- **Progress:** 14% (28/197 TODOs)

**Month 2 (Weeks 5-8):** IFC Import Alpha
- [ ] Can import IFC files
- [ ] Building structure auto-created
- [ ] HTTP endpoints for IFC working
- **Progress:** 26% (51/197 TODOs)

**Month 3 (Weeks 9-12):** Mobile API Beta
- [ ] Spatial anchors working
- [ ] Mobile endpoints functional
- [ ] AR integration ready
- **Progress:** 44% (87/197 TODOs)

**Month 4 (Weeks 13-16):** Multi-user Ready
- [ ] Authentication working
- [ ] User management functional
- [ ] TUI showing real data
- **Progress:** 56% (110/197 TODOs)

**Month 5 (Weeks 17-20):** Equipment Systems Complete
- [ ] Generic equipment import
- [ ] Smart room mapping
- [ ] Version control integration
- **Progress:** 63% (125/197 TODOs)

**Month 6 (Weeks 21-24):** Version Control Alpha
- [ ] Branch operations working
- [ ] Basic PR functionality
- **Progress:** 71% (140/197 TODOs)

**Month 7 (Weeks 25-28):** Version Control Beta
- [ ] Full PR workflow
- [ ] Issue tracking
- **Progress:** 79% (155/197 TODOs)

**Month 8 (Weeks 29-32):** Git Workflow Complete
- [ ] Contributors and teams
- [ ] Version comparison
- [ ] Rollback functionality
- **Progress:** 86% (170/197 TODOs)

**Month 9 (Weeks 33-36):** Advanced UI Alpha
- [ ] Energy visualization
- [ ] Repository manager TUI
- [ ] CADTUI basic tools
- **Progress:** 91% (180/197 TODOs)

**Month 10 (Weeks 37-40):** Advanced UI Beta
- [ ] CADTUI design tools complete
- [ ] Utility commands working
- **Progress:** 95% (187/197 TODOs)

**Month 11 (Weeks 41-44):** Production Release
- [ ] All TODOs resolved
- [ ] Tests passing
- [ ] Deployed
- **Progress:** 100% (197/197 TODOs)

---

## Risk Management

### Technical Risks

**Risk 1: PostGIS Learning Curve**
- **Impact:** High (blocks spatial features)
- **Probability:** Medium
- **Mitigation:**
  - Start with simple queries
  - Use AI assistance for complex PostGIS syntax
  - Test incrementally
  - Reference PostGIS documentation extensively

**Risk 2: IFC Parsing Complexity**
- **Impact:** High (Priority #1 feature)
- **Probability:** Medium
- **Mitigation:**
  - IfcOpenShell service already exists
  - Focus on extraction, not parsing
  - Start with simple IFC files
  - Add complexity incrementally

**Risk 3: Mobile API Breaking Changes**
- **Impact:** Medium (affects mobile app)
- **Probability:** Low
- **Mitigation:**
  - Version API endpoints
  - Mobile app and backend in same repo
  - Test mobile frequently

**Risk 4: Version Control Complexity**
- **Impact:** Medium (advanced feature)
- **Probability:** High
- **Mitigation:**
  - This is the most complex phase
  - Reference Git source code
  - Consider using libgit2 bindings
  - Implement incrementally

**Risk 5: Time Constraints**
- **Impact:** High (solo developer, full-time job)
- **Probability:** High
- **Mitigation:**
  - Be realistic about hours per week
  - Track time spent vs. estimated
  - Adjust timeline as needed
  - Focus on quality over speed

### Scope Risks

**Risk 6: Feature Creep**
- **Impact:** High (derails timeline)
- **Probability:** Medium
- **Mitigation:**
  - Stick to the plan
  - No new features until 197 TODOs done
  - Track "future ideas" separately
  - Review plan monthly, not weekly

**Risk 7: Perfectionism**
- **Impact:** Medium (slows progress)
- **Probability:** High
- **Mitigation:**
  - "Done" beats "perfect"
  - Ship working code, refactor later
  - 80/20 rule: 80% quality in 20% time
  - Get feedback early and often

---

## Success Metrics

### Technical Metrics

**Code Quality:**
- [ ] All 197 TODOs resolved
- [ ] Test coverage > 70%
- [ ] No critical linter errors
- [ ] Build time < 2 minutes

**Performance:**
- [ ] API response time < 200ms (p95)
- [ ] IFC import < 30 seconds for typical file
- [ ] Database queries < 50ms (p95)
- [ ] Mobile app loads < 2 seconds

**Reliability:**
- [ ] Uptime > 99.9%
- [ ] Zero data loss
- [ ] Automatic backups working
- [ ] Error recovery implemented

### Business Metrics

**Adoption:**
- [ ] Documented 10+ buildings in school district
- [ ] 5+ active users (colleagues)
- [ ] 100+ equipment items tracked
- [ ] 50+ work orders created

**Value:**
- [ ] Supervisor approval to continue
- [ ] Time savings demonstrated (before/after)
- [ ] Data accuracy improved
- [ ] Audit compliance easier

**Validation:**
- [ ] Can answer: "Where is equipment X?"
- [ ] Can answer: "What work was done last month?"
- [ ] Can answer: "When was this inspected?"
- [ ] Can generate compliance reports

---

## Weekly Routine

### Sustainable Development Pattern

**Weekday Pattern (5-7 hours/week):**
```
Monday:    1 hour  - Review plan, pick 2-3 TODOs for week
Tuesday:   1 hour  - Work on TODO #1
Wednesday: 1 hour  - Work on TODO #2
Thursday:  1 hour  - Work on TODO #3
Friday:    1 hour  - Test changes, commit, document
Saturday:  0-2 hours - Optional catch-up
Sunday:    0-2 hours - Optional sprint
```

**Weekend Sprint Pattern (10-15 hours/week):**
```
Monday-Friday: 1 hour/day - Quick progress (5h total)
Saturday:      4-6 hours  - Deep work session
Sunday:        2-4 hours  - Testing and cleanup
```

### Productivity Tips

1. **Time Boxing:**
   - Set timer for 1-hour blocks
   - Take 10-minute breaks
   - Avoid multi-hour marathons (diminishing returns)

2. **Context Preservation:**
   - End each session with TODO.md update
   - Write "NEXT:" comment in code
   - Commit WIP to feature branch

3. **Focus:**
   - One TODO at a time
   - Finish before starting next
   - Resist urge to refactor everything

4. **Testing:**
   - Write test for each TODO
   - Run tests before committing
   - Keep CI/CD green

---

## Tools & Resources

### Development Tools

**Required:**
- PostgreSQL 15+ with PostGIS extension
- Go 1.24+
- Docker (for services)
- Git

**Recommended:**
- VSCode with Go extension
- TablePlus or pgAdmin (database GUI)
- Postman (API testing)
- Redis (for caching)

### Learning Resources

**PostGIS:**
- PostGIS documentation: https://postgis.net/docs/
- PostGIS in Action book
- AI assistance for complex queries

**IFC:**
- IFC4 specification
- IfcOpenShell documentation
- BuildingSMART resources

**Go Best Practices:**
- Effective Go
- Go Code Review Comments
- Clean Architecture in Go

### AI Assistance

**When to use AI:**
- PostGIS query syntax
- Complex algorithm implementation
- Test case generation
- Documentation writing

**When NOT to use AI:**
- Architecture decisions (you know your domain)
- Business logic (domain expert needed)
- Security-critical code (requires review)

---

## Phase Completion Checklists

### Phase 1: Foundation ✓
```
Infrastructure:
- [ ] Database schema migrated
- [ ] PostGIS extension enabled
- [ ] Spatial queries working
- [ ] Repository deserialization working
- [ ] Container properly wired

CLI:
- [ ] arx building create → works
- [ ] arx building list → shows data
- [ ] arx equipment create → works
- [ ] arx equipment list → shows data

Tests:
- [ ] Repository tests passing
- [ ] Use case tests passing
- [ ] Integration tests passing
```

### Phase 2: IFC Import ✓
```
IFC Processing:
- [ ] Can parse IFC file
- [ ] Extracts properties correctly
- [ ] Extracts materials
- [ ] Extracts classifications
- [ ] Validates geometry
- [ ] Creates building structure

CLI:
- [ ] arx ifc import <file> → works
- [ ] arx ifc validate <file> → shows results
- [ ] arx building list → shows IFC building

API:
- [ ] POST /api/v1/ifc/import → works
- [ ] GET /api/v1/ifc/jobs/{id} → shows status
- [ ] Import job completes successfully

Tests:
- [ ] Test with real IFC file
- [ ] Verify building structure
- [ ] Check equipment mapping
```

### Phase 3: Mobile API ✓
```
Spatial:
- [ ] Create AR anchor → works
- [ ] Query nearby equipment → works
- [ ] Store spatial mapping → works

Mobile:
- [ ] GET /api/v1/mobile/equipment → works
- [ ] POST /api/v1/equipment/photo → uploads
- [ ] Equipment has AR status field
- [ ] Filters working

Auth:
- [ ] User login → returns token
- [ ] Token refresh → works
- [ ] Token revocation → works
- [ ] User activation → works

TUI:
- [ ] TUI shows real building data
- [ ] TUI spatial queries working
- [ ] TUI updates in real-time

Tests:
- [ ] Mobile app can connect
- [ ] Mobile app can fetch equipment
- [ ] Mobile app can create anchors
```

### Phase 4: Multi-user ✓
```
Authentication:
- [ ] Password hashing working
- [ ] Password verification working
- [ ] JWT token generation working
- [ ] Token refresh working
- [ ] Token revocation working

Users:
- [ ] Create user → works
- [ ] Activate user → works
- [ ] Deactivate user → works
- [ ] Get user by email → works

Container:
- [ ] All repositories wired
- [ ] All use cases accessible
- [ ] Dependency injection working

Tests:
- [ ] Multiple users can log in
- [ ] Users isolated from each other
- [ ] Permissions enforced
```

### Phase 5: Equipment Systems ✓
```
Import:
- [ ] Import HVAC equipment CSV → works
- [ ] Import electrical panel CSV → works
- [ ] Import AV equipment CSV → works
- [ ] Import network gear CSV → works
- [ ] Import BAS points CSV → works

Mapping:
- [ ] Smart room mapping working
- [ ] Can list unmapped equipment
- [ ] Can manually map equipment

Version Control:
- [ ] Equipment changes tracked
- [ ] Can view change history
- [ ] Changes associated with user

File Watcher:
- [ ] Daemon watches folder
- [ ] Auto-imports new CSVs
- [ ] Sends notifications on import

Tests:
- [ ] Import 100+ equipment items
- [ ] Verify auto-mapping accuracy
- [ ] Update equipment, verify tracking
```

### Phase 6: Version Control ✓
```
Branches:
- [ ] Create branch → works
- [ ] List branches → shows all
- [ ] Checkout branch → switches context
- [ ] Delete branch → works

Pull Requests:
- [ ] Create PR → works
- [ ] List PRs → shows all
- [ ] Review PR → works
- [ ] Approve PR → works
- [ ] Merge PR → updates main branch

Issues:
- [ ] Create issue → works
- [ ] List issues → shows all
- [ ] Start work → creates branch
- [ ] Resolve issue → closes
- [ ] Link issue to PR → works

Contributors:
- [ ] Add contributor → works
- [ ] List contributors → shows all
- [ ] Create team → works
- [ ] Add team member → works

Versions:
- [ ] Create version → works
- [ ] Compare versions → shows diff
- [ ] Rollback to version → works
- [ ] Version history → shows all changes

Tests:
- [ ] Create branch, make changes, merge
- [ ] Create PR, approve, merge
- [ ] Create issue, start work, resolve
- [ ] Rollback to previous version
```

### Phase 7: Advanced UI ✓
```
TUI:
- [ ] Energy visualization showing
- [ ] Repository manager working
- [ ] TUI responsive and fast

CADTUI:
- [ ] Visual renderer working
- [ ] Can create components
- [ ] Can move components
- [ ] Can connect components
- [ ] Undo/redo working
- [ ] Viewport navigation working

Utilities:
- [ ] Query execution working
- [ ] Connection tracing working
- [ ] Visualization generation working
- [ ] Report generation working

Tests:
- [ ] TUI usable for daily work
- [ ] CADTUI can design simple system
- [ ] Reports accurate and useful
```

### Phase 8: Polish ✓
```
Testing:
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] End-to-end tests passing
- [ ] Performance tests passing

Optimization:
- [ ] Database indexed properly
- [ ] Slow queries optimized
- [ ] Caching implemented
- [ ] API response times good

Documentation:
- [ ] User documentation complete
- [ ] API documentation complete
- [ ] Deployment guide written
- [ ] Video tutorials created

Deployment:
- [ ] Production environment set up
- [ ] Database migrated
- [ ] Application deployed
- [ ] Users trained
- [ ] Monitoring configured

Validation:
- [ ] 10+ buildings documented
- [ ] 5+ active users
- [ ] Positive feedback received
- [ ] Time savings demonstrated
```

---

## Appendix: Quick Reference

### TODO Count by Priority

```
P0 - Critical (Foundation):        28 TODOs
P1 - High (IFC + Mobile + Auth):   83 TODOs
P2 - Medium (Version Control):     56 TODOs
P3 - Low (Advanced UI):            30 TODOs

Total:                             197 TODOs
```

### TODO Count by System

```
Infrastructure:                    28 TODOs
IFC Processing:                    23 TODOs
Mobile API:                        36 TODOs
Authentication:                    12 TODOs
Equipment Systems:                 15 TODOs
Version Control:                   42 TODOs
Advanced UI:                       30 TODOs
Polish & Testing:                  11 TODOs

Total:                            197 TODOs
```

### Hours by Phase

```
Phase 1: Foundation              40 hours
Phase 2: IFC Import              32 hours
Phase 3: Mobile API              48 hours
Phase 4: Multi-user              16 hours
Phase 5: Equipment Systems       20 hours
Phase 6: Version Control         64 hours
Phase 7: Advanced UI             48 hours
Phase 8: Polish                  16 hours

Total:                          284 hours
```

### Critical Path (Must Complete First)

```
Week 1:  Database setup
Week 2:  PostGIS spatial queries
Week 3:  Repository deserialization
Week 4:  Basic CLI commands
Week 5:  CLI context handling
Week 6:  Phase 1 testing
```

Everything else depends on Phase 1 completion.

---

## Final Notes

**This is a big project.** 284 hours is roughly:
- 7 full-time work weeks
- 41 weeks at 7 hours/week
- 28 weeks at 10 hours/week
- 14 weeks at 20 hours/week

**But you've already done the hard part:** The architecture is sound, the vision is clear, the domain knowledge is there.

**The remaining work is:**
- Filling in TODOs (mostly straightforward implementation)
- Testing (verify it works)
- Polish (make it nice)
- Deploy (make it real)

**You're not building from scratch.** You're completing a well-architected system.

**Recommendation:**
- Start with Phase 1 (6 weeks)
- Get IFC import working (Phase 2, 4 weeks)
- Reassess timeline with actual experience
- Adjust pace as needed

**You'll know if this is working when:**
- Week 6: You can create a building in CLI and see it in database
- Week 10: You can import an IFC file and see building structure
- Week 16: Your mobile app can fetch real equipment data
- Week 24: You're using it daily at work

**The goal isn't to finish in 44 weeks.** The goal is to have a working system you're using at your job. If that happens in Week 20, great. If it takes 60 weeks, that's fine too.

**Progress > Perfection.**

---

**Next Step:** Start Phase 1, Week 1 tasks (Database setup). Report back when database is running and migrations are applied.

**Created:** October 11, 2025
**Author:** Development Planning Assistant
**Status:** Ready for Implementation
**Priority Order:** IFC → Mobile → Multi-user → Equipment Systems

