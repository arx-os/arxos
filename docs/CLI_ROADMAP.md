# ArxOS CLI Roadmap

This document tracks planned CLI features that have not yet been implemented. These were previously stub implementations with TODO comments.

---

## Git Operations (15 features)

### Stage Command
**File:** `cli/mod.rs`
**Features:**
- [x] Implement `git add -A` (stage all files) - **IMPLEMENTED**
- [x] Implement `git add <file>` (stage specific file) - **IMPLEMENTED**

### Commit Command
**File:** `cli/mod.rs`
**Features:**
- [x] Implement `git commit -m <message>` - **IMPLEMENTED**

### Unstage Command
**File:** `cli/mod.rs`
**Features:**
- [x] Implement `git reset` (unstage all) - **IMPLEMENTED**
- [x] Implement `git reset <file>` (unstage specific file) - **IMPLEMENTED**

### Diff Command
**File:** `cli/mod.rs`
**Features:**
- [x] Implement `git diff --stat` (summary) - **IMPLEMENTED**
- [ ] Interactive diff viewer (TUI)
- [x] Standard `git diff` output - **IMPLEMENTED**

### History Command
**File:** `cli/mod.rs`
**Features:**
- [x] Implement `git log --verbose` - **IMPLEMENTED**
- [x] Standard `git log` output - **IMPLEMENTED**

### Status Command
**File:** `cli/mod.rs`
**Features:**
- [ ] Interactive status dashboard (TUI)
- [ ] Implement `git status -v`
- [x] Basic `git status` output - **IMPLEMENTED**

---

## Maintenance Operations (28 features)

### Validate Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Load and validate building.yaml schema
- [ ] Check referential integrity
- [ ] Validate spatial relationships

### Config Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Load and display configuration
- [ ] Parse `section.key=value` and update config
- [ ] Reset configuration to defaults
- [ ] Open config file in $EDITOR
- [ ] Launch TUI configuration wizard

### Watch Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Implement watch mode daemon
- [ ] Launch TUI watch dashboard
- [ ] Monitor file changes and auto-process

### Health Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Launch TUI health dashboard
- [ ] Component-specific health checks
- [ ] Verbose diagnostic information

### Info Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Filter by component/tags
- [ ] Show verbose results
- [ ] Show compact results

### Docs Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Generate API documentation
- [ ] Generate user documentation
- [ ] Generate architecture documentation

### Sensor Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Implement watch mode daemon for sensor data
- [ ] Loop and process new sensor files as they appear
- [ ] Process all sensor data files in directory
- [ ] Commit changes after processing sensor data

### Server Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Implement HTTP server for ArxOS API
- [ ] Run server request/response loop

### Subscribe Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Implement MQTT subscriber
- [ ] Run subscriber event loop
- [ ] Process real-time spatial updates

### Migrate Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Analyze and show what would be migrated (dry-run)
- [ ] Perform actual data migration

### Sign Command
**File:** `cli/commands/maintenance.rs`
**Features:**
- [ ] Verify all commits with GPG
- [ ] Verify specific commit with GPG
- [ ] Implement GPG signature verification

---

## Data Operations (14 features)

### Room Subcommand
**File:** `cli/commands/data.rs`
**Features:**
- [ ] Launch TUI room explorer
- [ ] Show detailed room information
- [ ] Show room list
- [ ] Fetch room details from building data
- [ ] Show equipment in room

### Equipment Subcommand
**File:** `cli/commands/data.rs`
**Features:**
- [ ] Launch TUI equipment browser
- [ ] Show detailed equipment info
- [ ] Show equipment list

### Spatial Subcommand
**File:** `cli/commands/data.rs`
**Features:**
- [ ] Implement grid to real coordinate conversion
- [ ] Implement real to grid coordinate conversion
- [ ] Implement spatial queries (nearby, contains, etc.)
- [ ] Implement spatial relationship setting
- [ ] Implement coordinate system transformation
- [ ] Implement spatial validation

---

## Query Operations (8 features)

### Search Command
**File:** `cli/mod.rs`
**Features:**
- [ ] Launch TUI search result browser (interactive mode)
- [x] Implement search logic - **IMPLEMENTED**
- [x] Show verbose results with full details - **IMPLEMENTED**
- [x] Show compact results - **IMPLEMENTED**
- [x] Search equipment by name - **IMPLEMENTED**
- [x] Search rooms by name - **IMPLEMENTED**
- [x] Search buildings by name - **IMPLEMENTED**
- [x] Regex pattern matching - **IMPLEMENTED**
- [x] Case-sensitive/insensitive search - **IMPLEMENTED**
- [x] Configurable result limit - **IMPLEMENTED**

### Query Command
**File:** `cli/mod.rs`
**Features:**
- [x] Implement ArxAddress glob pattern matching - **IMPLEMENTED**
- [x] Format output as JSON - **IMPLEMENTED**
- [x] Format output as YAML - **IMPLEMENTED**
- [x] Format output as table - **IMPLEMENTED**
- [x] Verbose mode with properties - **IMPLEMENTED**

### Address Command
**File:** `cli/commands/query.rs`
**Features:**
- [ ] Advanced ArxAddress operations (not yet implemented)

---

## Building Operations (7 features)

### Init Command
**File:** `cli/commands/building.rs`
**Features:**
- [ ] Implement Git initialization for building repo
- [ ] Create initial commit with building structure

### Export Command
**File:** `cli/commands/building.rs`
**Features:**
- [ ] Implement building data export logic
- [ ] Support multiple export formats

### Watch Command
**File:** `cli/commands/building.rs`
**Features:**
- [ ] Implement watch mode daemon for building changes

### Sync Command
**File:** `cli/commands/building.rs`
**Features:**
- [ ] Implement building data synchronization

### Import Command
**File:** `cli/commands/building.rs`
**Features:**
- [ ] Implement dry run analysis (show what would be imported)
- [ ] Implement actual IFC import logic

---

## Rendering Operations (3 features)

### Render Command
**File:** `cli/commands/rendering.rs`
**Features:**
- [ ] Launch interactive 3D renderer
- [ ] Implement static rendering to file

### View3D Command
**File:** `cli/commands/rendering.rs`
**Features:**
- [ ] Launch interactive 3D renderer with specified settings

---

## Core Rendering (1 feature)

### Interactive Renderer
**File:** `render3d/mod.rs:634`
**Feature:**
- [ ] Implement interactive renderer entry point
- [ ] Connect existing 3D renderer to TUI/interactive mode

---

## Implementation Priority

### High Priority (Core Workflows)
1. Git operations (stage, commit, status) - Most used CLI features
2. Building import/export - Essential for data management
3. Query operations - User needs to access building data

### Medium Priority (Developer Tools)
4. Health/info/validate - Debugging and diagnostics
5. Room/equipment queries - Data exploration
6. Static rendering - Export functionality

### Low Priority (Advanced Features)
7. Watch modes - Convenience features
8. Server/subscribe - Real-time integration
9. TUI dashboards - Enhanced UX
10. Migration/signing - Advanced workflows

---

## Notes

- All core functionality exists in the ArxOS library
- CLI commands are thin wrappers around core APIs
- Many features just need CLI arg parsing + core function calls
- TUI features require ratatui integration
- Server features require web framework (axum/actix)

---

**Status:** All features are planned, none implemented
**Created:** 2025-11-20
**Purpose:** Track CLI feature development, removed from inline TODOs
