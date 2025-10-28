<!-- 390ce086-7a48-481a-977c-f648c6e340a4 c2b26070-e89a-4381-9484-cec2e9d18f2a -->
# ArxOS Complete Implementation Plan

## Overview

This plan addresses all critical gaps identified in the project review, focusing on wiring up existing infrastructure to enable end-to-end workflows. The work is organized into three phases following the recommended priority order.

## Current Status (Updated)

**Completed:**
- ✅ Equipment persistence with Git staging (Phase 1.1)
- ✅ Git staging commands (stage/commit/unstage) (Phase 1.2)
- ✅ Room persistence (already existed)

**In Progress:**
- ⚠️ iOS FFI integration structure created (Phase 2.1)
- ⚠️ EquipmentListView wired to FFI (but returns empty until library is built)

**Next Steps:**
- Build Rust FFI library for iOS targets
- Complete IFC import workflow
- Implement sensor data pipeline

## Phase 1: Core Functionality (Priority: Critical)

### 1.1 Equipment Persistence to Git

**Problem**: Equipment commands print output but don't persist changes or commit to Git.

**Files to modify**:

- `src/commands/equipment.rs` (lines 50, 110, 129)
- `src/commands/room.rs` (similar pattern)

**Implementation**:

```rust
// In handle_add_equipment() at line 50
use crate::persistence::PersistenceManager;

// Load existing building data
let persistence = PersistenceManager::new(&room)?;
let mut building_data = persistence.load_building_data()?;

// Add equipment to appropriate floor/room
let equipment = Equipment::new(name, "", parsed_equipment_type);
// Find and update the target room
// ... add equipment to room

// Save changes (staged, not committed yet)
persistence.save_building_data(&building_data)?;

if commit {
    let commit_msg = format!("Add equipment: {}", equipment.name);
    persistence.save_and_commit(&building_data, Some(&commit_msg))?;
}
```

**Apply same pattern to**:

- `handle_update_equipment()`
- `handle_remove_equipment()`
- All room commands in `src/commands/room.rs`

### 1.2 Git Staging Commands

**Problem**: User wants to stage changes before committing, but no staging workflow exists.

**New commands to add** in `src/cli/mod.rs`:

- `git stage` - Stage current changes
- `git commit` - Commit staged changes with message
- `git unstage` - Remove files from staging

**Files to create/modify**:

- `src/commands/git_ops.rs` - Add staging handlers
- `src/git/manager.rs` - Add staging methods to BuildingGitManager

**Implementation**: Use git2 staging area APIs to track changes before committing.

### 1.3 Spatial Commands Integration

**Problem**: Spatial commands exist but don't persist spatial data updates.

**Files to modify**:

- `src/commands/spatial.rs` - Wire up persistence for coordinate system changes

## Phase 2: Mobile Integration (Priority: High)

### 2.1 iOS FFI Wiring

**Problem**: iOS UI is complete but doesn't call Rust FFI functions. Mock data is hardcoded.

**Files to modify**:

- `ios/ArxOSMobile/ArxOSMobile/Services/ArxOSService.swift` - Create Swift wrapper for FFI
- `ios/ArxOSMobile/ArxOSMobile/Views/EquipmentListView.swift` (line 83-124) - Replace mock data

**Implementation**:

```swift
// Create ArxOSService.swift
import Foundation

class ArxOSService {
    func listEquipment(buildingName: String) -> [Equipment] {
        let cString = buildingName.cString(using: .utf8)
        let resultPtr = arxos_list_equipment(cString)
        
        // Parse JSON response
        guard let resultPtr = resultPtr else { return [] }
        let resultString = String(cString: resultPtr)
        arxos_free_string(resultPtr)
        
        // Deserialize JSON to Equipment array
        // ... return parsed equipment
    }
}

// In EquipmentListView.swift, replace loadEquipment():
private func loadEquipment() {
    isLoading = true
    let service = ArxOSService()
    equipmentList = service.listEquipment(buildingName: "test_building")
    isLoading = false
}
```

**Additional wiring needed**:

- `arxos_list_rooms()` → `EquipmentListView` room filter
- `arxos_parse_ar_scan()` → `ARScanView`
- `arxos_extract_equipment()` → AR equipment detection

### 2.2 Build Rust FFI Library for iOS

**Problem**: FFI functions exist but library isn't built for iOS targets.

**Tasks**:

1. Build for `aarch64-apple-ios` (devices)
2. Build for `aarch64-apple-ios-sim` (M1/M2 simulators)
3. Create XCFramework with both architectures
4. Link in Xcode project

**Script updates needed**: `scripts/build-mobile-ios.sh`

### 2.3 Android FFI Wiring (Lower priority than iOS)

**Files to modify**:

- `android/app/src/main/java/com/arxos/mobile/data/ArxOSRepository.kt` - Create Kotlin wrapper
- Wire up to existing Compose UI components

## Phase 3: IFC Import and Sensor Integration

### 3.1 Complete IFC Import Workflow

**Problem**: IFC parser works but CLI import command doesn't complete the workflow.

**Files to modify**:

- `src/commands/import.rs` - Complete import handler

**Current code** (line 25-30):

```rust
pub fn handle_import(ifc_file: PathBuf, repo: Option<PathBuf>) -> Result<(), Box<dyn std::error::Error>> {
    println!("Importing IFC file: {:?}", ifc_file);
    // TODO: Complete implementation
}
```

**Complete implementation**:

```rust
pub fn handle_import(ifc_file: PathBuf, repo: Option<PathBuf>) -> Result<(), Box<dyn std::error::Error>> {
    let processor = IFCProcessor::new();
    
    // Extract hierarchy from IFC
    let (building, floors) = processor.extract_hierarchy(ifc_file.to_str().unwrap())?;
    
    // Convert to BuildingData format
    let building_data = convert_to_building_data(building, floors)?;
    
    // Serialize to YAML
    let serializer = BuildingYamlSerializer::new();
    let yaml_output = serializer.to_yaml(&building_data)?;
    
    // Write to file
    let output_file = PathBuf::from(format!("{}.yaml", building_data.building.name));
    std::fs::write(&output_file, yaml_output)?;
    
    // Initialize Git repo if requested
    if let Some(repo_path) = repo {
        // Initialize Git and commit initial import
    }
    
    println!("✅ Imported successfully: {}", output_file.display());
    Ok(())
}
```

**Helper function needed**: `convert_to_building_data()` to transform IFC hierarchy to YAML format.

### 3.2 Sensor Data Ingestion Pipeline

**Problem**: Hardware examples work, sensor data formats defined, but no integration with equipment status.

**Files to modify**:

- `src/commands/sensors.rs` - Complete sensor processing command
- `src/hardware/status_updater.rs` - Implement status update logic

**Implementation**:

```rust
// In handle_process_sensors_command()
pub fn handle_process_sensors_command(
    sensor_dir: &PathBuf,
    building: &str,
    commit: bool,
    watch: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let config = SensorIngestionConfig {
        data_directory: sensor_dir.clone(),
        ..Default::default()
    };
    let ingestion = SensorIngestionService::new(config);
    
    // Scan for sensor files
    let sensor_files = ingestion.scan_directory(sensor_dir)?;
    
    // Load building data
    let persistence = PersistenceManager::new(building)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Process each sensor file
    for file in sensor_files {
        let sensor_data = ingestion.read_sensor_data_file(&file)?;
        
        // Update equipment status based on sensor data
        update_equipment_from_sensor(&mut building_data, &sensor_data)?;
    }
    
    // Save and optionally commit
    persistence.save_building_data(&building_data)?;
    if commit {
        persistence.save_and_commit(&building_data, Some("Update from sensor data"))?;
    }
    
    Ok(())
}
```

**New function needed**: `update_equipment_from_sensor()` to map sensor readings to equipment status updates.

### 3.3 Equipment Status Mapping

**Problem**: Need to map sensor readings to equipment status fields.

**Implementation in** `src/hardware/status_updater.rs`:

- Match sensor `device_id` or `equipment_id` to equipment in building data
- Update equipment properties based on sensor type (temperature, humidity, CO2, etc.)
- Set equipment status based on threshold rules
- Add timestamp to track when status was last updated

## Phase 4: Polish and Integration

### 4.1 3D Rendering Data Integration

**Problem**: 3D rendering system exists but doesn't load real building data.

**Files to modify**:

- `src/commands/render.rs` - Load building data from persistence
- `src/commands/interactive.rs` - Wire up interactive renderer

### 4.2 AR Workflow Integration

**Problem**: AR scanning UI exists but doesn't integrate with pending equipment workflow.

**Implementation**:

- Wire AR scan results to `PendingEquipmentManager`
- Enable review and confirmation workflow
- Commit approved equipment to building data

### 4.3 Testing and Documentation

**Tasks**:

- Add integration tests for persistence workflows
- Test mobile FFI on real iOS device
- Update user guide with complete workflows
- Add examples for common operations

## Implementation Order

1. Equipment persistence (Phase 1.1) - Unblocks all CRUD operations
2. Git staging (Phase 1.2) - Enables proper version control workflow
3. iOS FFI wiring (Phase 2.1) - Mobile app becomes functional
4. IFC import (Phase 3.1) - Can import real building data
5. Sensor integration (Phase 3.2-3.3) - Hardware integration complete
6. Polish items (Phase 4) - Enhanced user experience

## Success Criteria

- Equipment add/update/remove operations persist to YAML and Git
- iOS app displays real building data via FFI
- IFC import generates valid YAML files
- Sensor data updates equipment status automatically
- All workflows are end-to-end functional
- Test coverage maintained above 90%

### To-dos

- [x] Implement equipment CRUD persistence with Git staging support in src/commands/equipment.rs ✅ **COMPLETED**
  - Added equipment persistence to YAML files
  - Git staging support (--commit flag)
  - Full CRUD operations (add, update, remove)
  
- [x] Implement room CRUD persistence with Git staging support in src/commands/room.rs ✅ **COMPLETED**
  - Already implemented in existing code

- [x] Add Git staging commands (stage, commit, unstage) to CLI and git manager ✅ **COMPLETED**
  - Added `Stage`, `Commit`, `Unstage` commands to CLI
  - Implemented handlers in git_ops.rs
  - Added methods to BuildingGitManager: stage_file, stage_all, unstage_file, unstage_all, commit_staged

- [x] Create ArxOSService.swift wrapper for FFI functions ✅ **COMPLETED**
  - FFI wrapper structure created with proper C bindings
  - Models created in Models/ArxOSModels.swift
  - Swift FFI wrapper updated with full implementation
  - Generic callFFI helper for JSON parsing and error handling
  - Memory management properly implemented (arxos_free_string)
  - TODO markers added for enabling when library is linked

- [⚠️] Replace mock data in EquipmentListView with real FFI calls ⚠️ **READY FOR LINKING**
  - Updated to call FFI service with complete error handling
  - All Swift wrappers implement proper FFI call patterns
  - **REMAINING**: Uncomment FFI calls once library is built and linked in Xcode
  - See: docs/PHASE2_IMPLEMENTATION_STATUS.md for details

- [✅] Build Rust library for iOS targets and create XCFramework ✅ **COMPLETED**
  - ✅ Cargo.toml updated with staticlib crate type
  - ✅ build.rs created for build configuration
  - ✅ Build script enhanced with complete XCFramework creation
  - ✅ Build script installs iOS targets automatically
  - ✅ Environment variables automatically configured (DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET)
  - ✅ Successfully built for all iOS architectures (aarch64-apple-ios, x86_64-apple-ios, aarch64-apple-ios-sim)
  - ✅ XCFramework created at ios/build/ArxOS.xcframework
  - ✅ Universal libraries created (device + simulator)
  - ✅ Headers and Info.plist properly configured
  - ✅ Framework linked in Xcode project (absolute path configured)
  - ✅ Fixed duplicate model definitions
  - ✅ Fixed file paths in Xcode project
  - ✅ Added missing files (ArxOSCoreFFI.swift, ArxOSModels.swift, Models group, ARViewContainer.swift)
  - ✅ Fixed Codable conformance issues (DetectedEquipment, Position3D)
  - ✅ Fixed TerminalError enum to include all required cases
  - ✅ Added system library linker flags (-lz, -liconv)
  - ✅ **BUILD SUCCEEDED** - iOS app now builds successfully!

- [✅] Complete IFC import workflow with hierarchy extraction and YAML generation ✅ **COMPLETED**
  - ✅ IFC import command fully functional
  - ✅ Extracts building hierarchy from IFC files
  - ✅ Generates YAML output with building data
  - ✅ Git repository initialization on import
  - ✅ Commits generated building data to Git
  - ✅ Tested with minimal IFC file
  - ⚠️ **TESTING**: Need to test with larger IFC file for realistic data

- [ ] Implement sensor data ingestion pipeline with equipment status updates ❌ **NOT STARTED**

- [ ] Create sensor-to-equipment mapping and threshold-based status updates ❌ **NOT STARTED**

- [ ] Wire 3D rendering commands to load real building data from persistence ❌ **NOT STARTED**

- [ ] Integrate AR scanning with pending equipment workflow and confirmation ❌ **NOT STARTED**

- [ ] Add integration tests for complete persistence and FFI workflows ❌ **NOT STARTED**

## Progress Summary

**Completed (6/12):**
- ✅ Equipment persistence to Git
- ✅ Git staging commands
- ✅ iOS FFI Swift wrapper with full implementation
- ✅ iOS build script with XCFramework creation
- ✅ Built Rust library for all iOS targets
- ✅ Created XCFramework (ios/build/ArxOS.xcframework)

**In Progress (1/12):**
- ⏳ iOS Xcode project integration
  - Framework ready to link
  - Build script enhanced with auto-configuration
  - See docs/PHASE2_BUILD_SUCCESS.md for Xcode integration steps

**Remaining (5/12):**
- ⏳ Link framework in Xcode project
- ❌ IFC import workflow
- ❌ Sensor data pipeline
- ❌ Sensor-to-equipment mapping
- ❌ AR workflow integration
- ❌ Integration tests

**Overall Progress: 58% (7/12 items complete, 5/12 remaining)**