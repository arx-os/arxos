# Changelog

All notable changes to ArxOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-pilot.5] - 2026-07-17

**Tag:** `v2.0.0-pilot.5` @ `latest`  
**Install:** `git checkout v2.0.0-pilot.5 && cargo install --path . --locked`  
**Default features:** compiler spine + TUI.

### Changed
- Address Validation: Downgraded reserved system prefix mismatches from hard errors to warnings by default to support pragmatic field naming schemas. Added `--strict-addresses` flag to validation and IFC import commands to enforce strict validations (R10/R5).
- LossReport Honesty: Expanded the static `unmapped_products` list into a dynamic registry-driven scan to ensure all unmapped physical IFC entities (including MEP elements like `IFCPIPESEGMENT` and `IFCDUCTSEGMENT`) are correctly captured in the LossReport instead of silently ignored (R2).
- Key Determinism: Sorted all `properties` HashMap fields on serialization using a custom Serde helper to guarantee deterministic JSON and YAML output formats (G3).

## [2.0.0-pilot.4] - 2026-07-13

**Tag:** `v2.0.0-pilot.4` @ `659bbd9f`  
**Install:** `git checkout v2.0.0-pilot.4 && cargo install --path . --locked`  
**Default features:** compiler spine + **TUI** (primary UI).

### Added
- LossReport `unmapped_products` — class counts for walls/slabs/doors/windows/etc. present in IFC but not mapped into the Arx domain (R2 eng honesty)
- buildingSMART ISO RV fixtures + `buildingsmart_ifc_test` (non-panic + unmapped warning)
- Assessment report: `tests/ifc_buildingsmart_report.md`
- Resource limits (`docs/resource-limits.md`) and hard refuse on oversize import (R6 eng defaults)
- L1 pilot packet docs (charter, field-handoff, second-person checklist, pilot-release)

### Changed
- Default feature set: **TUI on**; hardware BACnet/Modbus/MQTT and Bevy/LiDAR 3D viz **removed** from product surface
- CLI: compiler-first help order; `export --path` for project root; `--delta` removed
- Manifest **R2** → Partial (lab battery + LossReport; district IFC evidence still open)
- Preferred R9 pin supersedes pilot.3 for new field installs

### Not claimed
- Full BIM / CoordinationView certification
- District L1 exit (R1, R5, R7, R10, field R2 still open)
- Production chain / mainnet $AXD

---

## [2.0.0] - 2025-12-09

### 🎉 Major Release: ArxAddress System

This release introduces the new **ArxOS Address** system, replacing the deprecated `UniversalPath` system. This is a breaking change that significantly improves address management, IFC sync, and query capabilities.

### Added

#### ArxAddress System
- **New 7-part hierarchical addressing**: `/country/state/city/building/floor/room/fixture`
- **14 reserved system names** for standardized engineering components (hvac, plumbing, electrical, fire, lighting, security, elevators, roof, windows, doors, structure, envelope, it, furniture)
- **Arbitrary custom items** support (e.g., `/usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge/pbj-sandwich`)
- **Path validation** with reserved-system prefix rules
- **SHA-256 GUID generation** for stable IFC entity IDs
- **Query engine** with glob pattern support (`/usa/ny/*/floor-*/mech/boiler-*`)

#### Configuration & Persistence
- **Persistent counter storage** (`.arxos/counters.toml`) for auto-generated fixture IDs
- **Counter persistence** survives restarts and works across concurrent users
- **Migration script** (`arx migrate`) to add addresses to existing fixtures

#### CLI Enhancements
- **`--at` flag** for `equipment add` command to specify ArxAddress
- **`arx query` command** with glob pattern matching
- **`arx migrate` command** for one-shot migration of existing fixtures
- **Enhanced help documentation** with examples and glob syntax

#### Error Handling
- **Structured error types** (`ArxError::AddressValidation`, `ArxError::CounterOverflow`, `ArxError::PathInvalid`)
- **Better CLI/mobile UX** with actionable error messages and recovery steps
- **Error context** with suggestions and help URLs

#### Mobile FFI
- **`address_path` field** added to `EquipmentInfo` (returns `.path` as String)
- **Simplified mobile API** - address returned as simple string instead of struct

#### Git Integration
- **Address-based directory layout**: Equipment files organized as `country/state/city/building/floor/room/fixture.yml`
- **Automatic directory creation** when new address segments appear
- **Backward compatibility** with old format for equipment without addresses

#### Testing & Quality
- **Comprehensive test coverage** for address validation, reserved systems, GUID stability, glob matching
- **IFC GUID collision guard** with verification tests
- **CI pipeline** with `cargo fmt`, `clippy`, `test`, and `tarpaulin` (≥85% coverage requirement)

#### Documentation
- **`ArxAddress.md`** specification document
- **Example YAML** with full 7-part addresses (`examples/ps-118/`)
- **CLI help updates** with usage examples

### Changed

#### Breaking Changes
- **`UniversalPath` completely removed** - Use `ArxAddress` instead (migration required)
- **`GitClient` completely removed** - Use `BuildingGitManager` instead (migration required)
- **`PathGenerator` completely removed** - Address generation now uses `ArxAddress::new()` and `spatial::grid::to_address::generate_address_from_context()`
- **`src/path/mod.rs` deleted** - All path-related functionality moved to `domain::ArxAddress`
- **`Equipment.address` field added** (optional for migration compatibility)
- **`EquipmentData.address` field added** (optional for migration compatibility)

#### API Changes
- **`ArxAddress`** replaces `UniversalPath` in public API
- **Search engine** now prioritizes `address.path` over `universal_path`
- **IFC export** uses `ArxAddress::guid()` for entity ID generation (SHA-256 hash)

#### Internal Improvements
- **Address validation** called everywhere paths are created (CLI, auto-gen, YAML load, mobile FFI)
- **Reserved system prefix validation** for all 14 systems
- **Error messages** use structured `ArxError` instead of generic `anyhow!`

### Removed

- **`UniversalPath`** - Completely removed from codebase (replaced by `ArxAddress`)
- **`GitClient`** - Completely removed from codebase (replaced by `BuildingGitManager`)
- **`PathGenerator`** - Module deleted (functionality moved to `ArxAddress` and `spatial::grid::to_address`)
- **`src/path/mod.rs`** - Deprecated path module removed

### Migration Guide

#### For Existing Data

1. **Run migration script**:
   ```bash
   arx migrate --dry-run  # Preview changes
   arx migrate            # Apply migration
   ```

2. **Manual migration** (if needed):
   - Old `universal_path` fields are preserved
   - New `address` fields are auto-generated from existing data
   - Both formats supported during migration period

#### For Code

1. **Replace `UniversalPath` with `ArxAddress`**:
   ```rust
   // Old
   use arxos::path::UniversalPath;
   let path = UniversalPath::new(...);
   
   // New
   use arxos::domain::ArxAddress;
   let addr = ArxAddress::new("usa", "ny", "brooklyn", "ps-118", "floor-02", "mech", "boiler-01");
   ```

2. **Update path access**:
   ```rust
   // Old
   let path_str = universal_path.to_string();
   
   // New
   let path_str = address.path;
   ```

3. **Use `BuildingGitManager` instead of `GitClient`**:
   ```rust
   // Old
   use arxos::git::GitClient;
   
   // New
   use arxos::git::BuildingGitManager;
   ```

### Security

- **Path validation** prevents malformed addresses from entering the system
- **SHA-256 hashing** for GUID generation (previously BLAKE3, now standardized)

### Performance

- **Counter persistence** improves auto-ID generation performance
- **Query engine** optimized for glob pattern matching
- **Address validation** cached where possible

---

## [1.0.0] - Previous Release

See [docs/CHANGELOG_NOVEMBER_2025.md](docs/CHANGELOG_NOVEMBER_2025.md) for previous changelog entries.

