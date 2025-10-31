# ArxOS Codebase Overview

**Version:** 2.0  
**Date:** January 2025  
**Language:** Rust (2021 Edition)  
**Size:** ~34,000 lines  
**Architecture:** Terminal-First Layered Monolith with Git-Native Storage

---

## Purpose

**ArxOS** brings version control to building management. It's a **Decentralized Physical Infrastructure Network (DePIN)** platform that enables:

- **Building Data Management**: Import IFC files, manage equipment and rooms, track changes with Git
- **3D Visualization**: Interactive terminal-based 3D building visualization with real-time rendering
- **Mobile Integration**: Native iOS/Android apps with AR capabilities for field verification
- **Hardware Integration**: Deploy ESP32, RP2040, or Arduino sensors to monitor buildings
- **Distributed Contributions**: Crowd-sourced building data with USD-based rewards (no blockchain complexity)

### Key Differentiators

- 🌐 **Git-Native**: Building data IS your version control—no databases needed
- 🏗️ **IFC Import**: Automatic hierarchy extraction from Building Information Modeling files
- 🔍 **Smart Search**: Advanced search with regex, fuzzy matching, and filtering
- 📱 **Mobile AR**: Native mobile apps for on-site equipment verification
- ⚡ **Terminal-First**: Designed for efficiency, automation, and developer workflows

---

## Architecture

### High-Level Overview

ArxOS follows a **layered monolith** architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                      │
│  Commands: search, filter, render, interactive, config     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Application Layer                           │
│  Search Engine, 3D Renderer, Interactive Controller       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Core Services Layer                       │
│  Git Integration, IFC Processing, Spatial Operations       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Data Layer                               │
│  YAML/JSON Data, Building Models, Equipment Data          │
└─────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Terminal-First**: All functionality works in terminal environment
2. **Git-Native**: All data changes go through Git workflow
3. **Modular Design**: Clean separation of concerns with focused modules
4. **Performance-Focused**: Optimized for large buildings (1000+ equipment)
5. **Extensible**: Easy to add new features and integrations

### System Components

**Rust Core**: Single unified crate compiled to static library  
**Native UI Shells**: iOS (Swift/SwiftUI) and Android (Jetpack Compose)  
**Git-First DePIN**: No database required, uses Git for distributed data storage  
**FFI Integration**: Mobile apps call Rust via C FFI bindings

---

## Key Modules

### Core Business Logic (`src/core/`)

Foundation data structures and operations:

- **`building.rs`**: Building entity with hierarchy (Floors → Wings → Rooms → Equipment)
- **`room.rs`**: Room types and spatial properties
- **`equipment.rs`**: Equipment types, status, and positioning
- **`types.rs`**: Spatial properties, positions, dimensions, bounding boxes
- **`operations.rs`**: CRUD operations for building components

**Key Types**: `Building`, `Floor`, `Wing`, `Room`, `Equipment`, `Position`, `SpatialProperties`

### Command Handlers (`src/commands/`)

Central routing layer mapping CLI commands to business logic:

- **`mod.rs`**: Command router with 18+ command handlers
- **`import.rs`**: IFC file import and Git initialization
- **`export.rs`**: Git export with validation
- **`render.rs`**: 2D/3D building visualization
- **`interactive.rs`**: Live interactive 3D rendering with controls
- **`search.rs`**: Search and filtering operations
- **`git_ops.rs`**: Git status, diff, history, stage, commit
- **`equipment.rs`**: Equipment CRUD operations
- **`room.rs`**: Room CRUD operations
- **`ar.rs`**: AR scan integration and pending equipment management
- **`sensors.rs`**: Sensor data processing
- **`watch.rs`**: Live monitoring dashboard

### IFC Processing (`src/ifc/`)

Custom STEP parser for Building Information Modeling:

- **`mod.rs`**: IFC processor coordination
- **`fallback.rs`**: Custom STEP parser with parallel processing
- **`enhanced/`**: Enhanced parsing with error recovery and spatial indexing
- **`hierarchy.rs`**: Building hierarchy extraction (Building → Floor → Room → Equipment)

**Key Types**: `IFCProcessor`, `FallbackIFCParser`, `EnhancedIFCParser`, `HierarchyBuilder`

### 3D Rendering (`src/render3d/`)

Advanced terminal-based 3D visualization:

- **`renderer.rs`**: 3D building renderer with camera and projection systems
- **`interactive.rs`**: Interactive 3D renderer with real-time updates
- **`camera.rs`**: 3D camera positioning and navigation
- **`projection.rs`**: Multiple projection types (isometric, orthographic, perspective)
- **`particles.rs`**: Particle effect system for visual feedback
- **`animation.rs`**: Animation framework for smooth transitions
- **`effects.rs`**: Visual effects engine
- **`events.rs`**: Event handling for user interactions
- **`state.rs`**: Interactive session state management

**Key Types**: `Building3DRenderer`, `InteractiveRenderer`, `Camera3D`, `Projection3D`, `ParticleSystem`

### Data Persistence (`src/persistence/`)

Unified persistence layer for Git and YAML:

- **`mod.rs`**: `PersistenceManager` coordinates Git and YAML operations
- **`error.rs`**: Persistence-specific error types

**Key Operations**: `load_building_data()`, `save_building_data()`, `save_and_commit()`

### Git Integration (`src/git/`)

Version control operations for building data:

- **`manager.rs`**: `BuildingGitManager` for repository operations
- **`mod.rs`**: Git configuration and operation result types

**Key Operations**: `export_building()`, `get_status()`, `get_diff()`, `list_commits()`, `commit_staged()`

### Search Engine (`src/search/`)

Advanced search and filtering capabilities:

- **`engine.rs`**: Multi-field search with regex and fuzzy matching
- **`formatter.rs`**: Result formatting for various output types
- **`types.rs`**: Search configurations and result structures

**Key Types**: `SearchEngine`, `SearchConfig`, `FilterConfig`, `SearchResult`

### YAML Serialization (`src/yaml/`)

Building data serialization for storage:

- **`mod.rs`**: `BuildingYamlSerializer` and data structures
- Separate data structures (`BuildingInfo`, `FloorData`, `RoomData`, `EquipmentData`) for serialization

### AR Integration (`src/ar_integration/`)

Mobile AR scan processing:

- **`pending.rs`**: `PendingEquipmentManager` for pending equipment verification
- **`processing.rs`**: AR scan data processing and validation
- **`mod.rs`**: AR integration workflow coordination

### Mobile FFI (`src/mobile_ffi/`)

Foreign function interface for mobile apps:

- **`ffi.rs`**: C FFI bindings with JSON serialization
- **`jni.rs`**: Android JNI bindings
- **`mod.rs`**: Mobile-specific data structures

### Spatial Operations (`src/spatial/`)

3D spatial data structures and queries:

- **`types.rs`**: Spatial entities and coordinate systems
- **`mod.rs`**: Spatial operations and queries

### Error Management (`src/error/`)

Rich error context and recovery:

- **`mod.rs`**: `ArxError` enum with context and suggestions
- **`display.rs`**: User-friendly error formatting
- **`analytics.rs`**: Error tracking and analytics

### Configuration (`src/config/`)

Configuration management with environment overrides:

- **`manager.rs`**: `ConfigManager` with hot reload
- **`mod.rs`**: Configuration structure
- **`validation.rs`**: Configuration validation

### Hardware Integration (`src/hardware/`)

Sensor data ingestion and status updates:

- **`ingestion.rs`**: Sensor data ingestion from IoT devices
- **`status_updater.rs`**: Equipment status updates from sensor data
- **`data_types.rs`**: Sensor data structures

---

## Main Data Flow

### IFC Building Import Workflow

**Entry Point** → **CLI Command Parsing** → **IFC Processing** → **Hierarchy Mapping** → **Serialization** → **Git Persistence** → **User Feedback**

#### Detailed Flow:

1. **CLI Argument Parsing** (`src/cli/mod.rs`)
   - User runs `arx import building.ifc --repo ./repo`
   - `Cli::parse()` extracts `Import` command with IFC path and repo options

2. **Command Routing** (`src/commands/mod.rs`)
   - `execute_command()` matches `Import` to `import::handle_import()`

3. **Import Handler** (`src/commands/import.rs`)
   - Validates IFC file path with `PathSafety`
   - Creates progress context for user feedback
   - Calls `IFCProcessor::extract_hierarchy()`

4. **IFC Processing** (`src/ifc/mod.rs`)
   - Reads IFC file with `PathSafety::read_file_safely()`
   - Returns raw STEP file content

5. **Entity Extraction** (`src/ifc/fallback.rs`)
   - `FallbackIFCParser` extracts STEP entities
   - Produces `IFCEntity` instances with type, name, and definition

6. **Hierarchy Building** (`src/ifc/hierarchy.rs`)
   - `HierarchyBuilder` maps IFC types to domain types:
     - `IFCBUILDING` → `Building`
     - `IFCBUILDINGSTOREY` → `Floor`
     - `IFCSPACE` → `Room`
     - Equipment entities → `Equipment`
   - Creates relationships (equipment → rooms → floors → building)
   - Returns `(Building, Vec<Floor>)`

7. **YAML Serialization** (`src/yaml/mod.rs`)
   - `BuildingYamlSerializer` converts domain types to `BuildingData`
   - Maps to YAML-compatible structures
   - Generates `building.yaml`

8. **Git Persistence** (if `--repo` specified) (`src/git/manager.rs`)
   - `BuildingGitManager::new()` opens or creates repo
   - `export_building()` writes files and commits
   - Returns commit ID

9. **Progress Reporting** (`src/progress/mod.rs`)
   - Reports parsing, success/errors, summary statistics

10. **Success Output**
    - Prints building stats, YAML filename, Git commit info

**Performance**: The flow supports parallel processing via `rayon` and progress reporting throughout. Error recovery attempts fallback parsing when primary extraction fails.

---

## Design Patterns & Architecture Decisions

### Established Patterns

#### 1. Manager Pattern
Centralizes resource lifecycle and operations:
- **`BuildingGitManager`**: Git operations
- **`PersistenceManager`**: Data persistence coordination
- **`ConfigManager`**: Configuration management
- **`PendingEquipmentManager`**: AR verification workflow

Each provides a focused API with clear responsibilities.

#### 2. Error Wrapper Pattern
Rich error context with suggestions and recovery:
- `ArxError` wraps errors with context, suggestions, recovery steps
- Uses `thiserror` for composability
- Supports user-friendly display and debugging

```rust
pub struct ErrorContext {
    pub suggestions: Vec<String>,
    pub recovery_steps: Vec<String>,
    pub debug_info: Option<String>,
    pub help_url: Option<String>,
    // ...
}
```

#### 3. Factory/Constructor Pattern
Consistent initialization:
- `new()` with defaults
- `with_config()` variants
- `Default` trait for configs

Promotes predictable construction and testing.

### Significant Anti-Patterns / Areas of Complexity

#### 1. Data Model Duplication
**Problem**: Separate structures for core (`src/core/`) and YAML (`src/yaml/`).

**Impact**:
- Maintenance overhead (keep in sync)
- Duplicate field definitions
- Manual conversions (`src/core/conversions.rs`)
- Divergence risk

**Recommended**: Derive serialization from core types or use a single source of truth.

#### 2. Legacy Data Organization
**Problem**: Incomplete migration evidenced by comments and dual fields.

```rust
pub struct Building {
    pub floors: Vec<Floor>,
    pub equipment: Vec<Equipment>, // Legacy - will be moved to floors
}
```

**Impact**:
- Unclear which field is authoritative
- Duplicate data, inconsistent state
- Technical debt

**Recommended**: Complete migration or document the current model.

#### 3. Command Module Coupling
**Problem**: `src/commands/` modules depend on many layers.

**Impact**:
- Changes ripple across command handlers
- Testing is harder
- Tight coupling to business logic

**Note**: Reduced from a 2,132-line `main.rs`; boundaries could be clearer.

---

## Testing Architecture

### Test Organization

**Tests Directory** (`tests/`):
- **`commands/`**: Unit tests per handler (15+ files)
- **Integration tests**: Workflow tests (`ifc_workflow_tests.rs`, `ar_workflow_integration_test.rs`, `hardware_workflow_tests.rs`)
- **Specialized tests**: FFI (`mobile_ffi_tests.rs`), security (`security_tests.rs`)

**Coverage**: >90% target, 150+ tests

### Test Philosophy

**Unit Tests**: Validate individual components  
**Integration Tests**: Validate end-to-end workflows  
**Performance Tests**: `benches/` with Criterion

---

## Mobile Platform Integration

### iOS (`ios/`)

**Architecture**: SwiftUI with ARKit  
**Integration**: C FFI bindings via `ArxOSMobile.xcodeproj`  
**FFI Module**: `ios/ArxOSMobile/Services/ArxOSCoreFFI.swift`  
**Build**: `scripts/build-mobile-ios.sh`

### Android (`android/`)

**Architecture**: Jetpack Compose with ARCore  
**Integration**: JNI bindings  
**FFI Module**: `android/app/src/main/java/com/arxos/mobile/`  
**Build**: `scripts/build-mobile-android.sh`

### FFI Protocol

- Rust: `#[no_mangle]` with JSON serialization  
- Memory: `arxos_free_string`  
- Errors: JSON error payloads

---

## Hardware Integration

### Supported Platforms

- **ESP32**: Temperature, motion, air quality
- **RP2040**: General-purpose sensors
- **Arduino**: Motion, proximity

### Integration Flow

1. **Sensor Data Ingestion** (`src/hardware/ingestion.rs`)
   - Read JSON from devices
   - Validate and map to internal types

2. **Status Updates** (`src/hardware/status_updater.rs`)
   - Update equipment status
   - Persist with Git
   - Trigger notifications

3. **DePIN Network**
   - Distributed verification
   - USD-based rewards

---

## Documentation Structure

**Core Docs** (`docs/`):
- **`ARCHITECTURE.md`**: System design
- **`USER_GUIDE.md`**: Usage
- **`DEVELOPER_ONBOARDING.md`**: Dev setup
- **`MOBILE_FFI_INTEGRATION.md`**: Mobile integration
- **`hardware_integration.md`**: Hardware setup
- **`PERFORMANCE_GUIDE.md`**: Optimization

**Archive** (`docs/archive/`):
- Historical planning and progress
- Migration notes

---

## Configuration & Build

### Build System

**Rust**: Cargo, 2021 Edition  
**Targets**: `cdylib`, `rlib`, `staticlib`  
**Mobile**: Separate iOS/Android builds

### Dependencies

- **Core**: serde, chrono, uuid
- **Git**: git2 (libgit2)
- **Spatial**: nalgebra, geo, rstar
- **Terminal**: crossterm, ratatui
- **Parallelism**: rayon
- **Mobile**: uniffi

### Configuration

- **File**: `arx.toml`
- **Environment**: Variable overrides
- **Defaults**: Sane defaults

---

## What's Missing (Key Context Gaps)

### 1. Deployment & DevOps
- Production deployment
- CI/CD (covers development CI)
- Scaling/redundancy for DePIN

### 2. API Documentation
- Module/crate docs
- Function-level docs
- Example snippets
- Missing: comprehensive API reference

### 3. Data Migration Strategy
- Legacy equipment migration
- Core vs. YAML model transition
- Breaking change/backward compatibility plans

### 4. Security Documentation
- Mobile security
- Sensor authentication
- Data privacy and anonymization

### 5. Performance Benchmarks
- `benches/` present, no published results
- No metrics for typical loads

### 6. Business Logic Documentation
- DePIN rewards
- Verification process
- Network economics

### 7. Integration Examples
- Non-trivial workflows
- Real-world scenarios
- Troubleshooting

---

## Quick Reference

### Start Development

```bash
# Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Build
cargo build --release

# Run tests
cargo test

# Build mobile
./scripts/build-mobile-ios.sh    # iOS
./scripts/build-mobile-android.sh # Android
```

### Key Commands

```bash
# Import IFC building file
arx import building.ifc --repo ./repo

# Search equipment
arx search "VAV"

# Render 3D visualization
arx render --building "Building Name" --three-d --show-status

# Interactive 3D session
arx interactive --building "Building Name" --projection isometric
```

### Architecture Diagram

```
User Input → CLI Parser → Command Router → Business Logic → Services → Persistence
                                                                    ↓
                                                        Git + YAML Storage
```

---

**End of Codebase Overview**

*This document provides a high-level understanding of the ArxOS codebase. For detailed implementation guidance, refer to the specific documentation in the `docs/` directory.*

