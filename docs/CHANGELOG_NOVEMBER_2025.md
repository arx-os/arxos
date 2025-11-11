# ArxOS Changelog - November 2025

## 📱 Mobile Pivot to WASM PWA

- Archived the native app directories (`ios/`, `android/`) and their build assets (`Dockerfile.android`, mobile build scripts, UniFFI headers).
- Removed the `mobile_ffi` Rust module and replaced it with `ar_integration::wasm` helpers designed for the browser-based PWA.
- Added WASM-friendly parsing helpers so the upcoming PWA can reuse AR scan datasets (`parse_ar_scan`, `extract_equipment_from_ar_scan`).
- Introduced `crates/arxos-wasm`, React/Zustand PWA shell (`pwa/`), and the `crates/arxos-agent` loopback service secured by DID:key tokens.
- Updated docs and scripts to point contributors to the Web PWA roadmap (`WEB_PWA_PLAN.md`) and the archived mobile bundle (`docs/mobile/STATUS.md`).
- Simplified the `arxos` build script—no more cbindgen/cross-platform header generation.

## 🎮 Gamified PR Review & Planning System

### New Features

#### Game System
- **PR Review Mode**: Interactive review of contractor PRs with constraint validation
  - Load PRs with `arx game review`
  - Real-time 3D visualization of equipment placements
  - Constraint violation detection and reporting
  - Approve/Reject/RequestChanges workflow
  - Export validated PRs to IFC format

- **Planning Mode**: Interactive equipment placement with real-time feedback
  - Plan equipment placement in 3D space
  - Real-time constraint validation as you place equipment
  - Export planning sessions as PRs for review
  - Direct IFC export from planning sessions

- **Learning Mode**: Educational scenarios from historical PRs
  - Load approved PRs as learning scenarios
  - Expert commentary system (YAML-based or auto-generated)
  - Tutorial step system with completion tracking
  - Best practices and common mistakes highlighted

#### Constraint System
- **Spatial Constraints**: Clearance requirements, proximity rules
- **Structural Constraints**: Wall support areas, load capacity validation
- **Code Constraints**: Building code compliance (ADA, fire safety)
- **Budget Constraints**: Cost limits and per-item tracking
- **User Preference Constraints**: Teacher/occupant location requests

#### IFC Integration
- **IFC Metadata Preservation**: Complete round-trip compatibility
  - Original IFC entity IDs maintained
  - Placement chains preserved
  - IFC properties tracked and restored
- **Type Mapping**: Automatic EquipmentType ↔ IFC entity type conversion
- **Game-to-IFC Export**: Export game sessions with full metadata

#### Mobile Integration
- **New FFI Functions**:
  - `arxos_load_pr` - Load PRs for review from mobile apps
  - `arxos_validate_constraints` - Validate equipment placement
  - `arxos_get_game_plan` - Retrieve planning session data

### Documentation

#### New Documentation Files
- `docs/features/GAME_SYSTEM.md` - Complete game system guide
- `docs/features/CONSTRAINTS.md` - Constraint validation reference
- `docs/features/IFC_COMPATIBILITY.md` - IFC round-trip guide
- `docs/mobile/MOBILE_GAME_INTEGRATION.md` - Mobile game integration

#### Updated Documentation
- `docs/DOCUMENTATION_INDEX.md` - Added game system and mobile integration
- `docs/core/USER_GUIDE.md` - Added game commands section
- `docs/core/CODEBASE_OVERVIEW.md` - Added game module documentation
- `README.md` - Added game system to features and quick start
- `docs/features/README.md` - Added game documentation links

### Code Organization

#### New Modules
- `crates/arxos/crates/arxos/src/game/` - Complete game system implementation
  - `types.rs` - Core game types
  - `scenario.rs` - Scenario loading
  - `state.rs` - Game state management
  - `constraints.rs` - Constraint validation
  - `pr_game.rs` - PR review mode
  - `planning.rs` - Planning mode
  - `learning.rs` - Learning mode
  - `ifc_sync.rs` - IFC metadata preservation
  - `ifc_mapping.rs` - Type mapping
  - `export.rs` - IFC export

#### Enhanced Modules
- `src/render3d/interactive.rs` - Added game overlay support
- `src/render3d/events.rs` - Added game action events
- `crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs` - Added game-related FFI functions
- `crates/arxui/crates/arxui/src/commands/game.rs` - New game command handlers
- `src/cli/mod.rs` - Added game command definitions

### Testing

#### New Test Suites
- `tests/commands/game_tests.rs` - Unit tests for game module
- `tests/game_integration_tests.rs` - Integration tests for workflows

#### Test Coverage
- Game state management
- Constraint validation
- PR review workflow
- Planning workflow
- IFC round-trip compatibility
- Scenario loading

### Breaking Changes

None - All new features are additive.

### Deprecations

None.

### Known Limitations

1. **Session Persistence**: `