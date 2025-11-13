# ArxOS IFC Processing Module

## Overview

The IFC processing module handles Industry Foundation Classes (IFC) files, converting them into ArxOS's Git-based building data format.

## Architecture

### Core Components

- **IFCProcessor**: Main processor for IFC files
- **SpatialEntity**: Represents spatial data extracted from IFC
- **IFCError**: Comprehensive error handling
- **BoundingBox**: 3D bounding box representation

### Error Handling

The module uses `thiserror` for structured error handling:

```rust
#[derive(Error, Debug)]
pub enum IFCError {
    #[error("IFC file not found: {path}")]
    FileNotFound { path: String },
    
    #[error("Invalid IFC file format: {reason}")]
    InvalidFormat { reason: String },
    
    #[error("IFC parsing error: {message}")]
    ParsingError { message: String },
}
```

### Logging

The module uses the `log` crate for structured logging:

- `info!`: General processing information
- `warn!`: Non-critical issues
- `error!`: Critical errors

## Usage

### Basic IFC Processing

```rust
use arxos::ifc::IFCProcessor;

let processor = IFCProcessor::new();
let building = processor.process_file("building.ifc")?;
```

### File Validation

```rust
let is_valid = processor.validate_ifc_file("building.ifc")?;
```

### Spatial Data Extraction

```rust
let spatial_data = processor.extract_spatial_data(&ifc_bytes)?;
```

## Testing

The module includes comprehensive tests:

- Unit tests for individual components
- Integration tests for file processing
- Error handling tests
- Mock data tests

Run tests with:

```bash
cargo test
```

## Current Implementation Status

### Working Features ✅
- Basic STEP file parsing
- Entity extraction (IFCSPACE, IFCFLOWTERMINAL, IFCBUILDINGSTOREY recognized)
- Spatial entity detection
- YAML serialization
- **Hierarchical extraction**: Building → Floor → Room → Equipment structure
- **Floor entities (IFCBUILDINGSTOREY)**: Properly extracted into Floor objects
- **Separate hierarchy extraction command**: `arx ifc extract-hierarchy`
- **PlacementResolver**: Accurate absolute transforms (translation + rotation) based on local placements
- **Canonical paths**: Deterministic `/building/<slug>/floor-*/room-*/equipment-*` paths for Git + ArxAddress workflows

### Recent Updates (December 2024) ✅
- Implemented `HierarchyBuilder` for proper building structure
- Fixed `IFCBUILDINGSTOREY` entity classification
- Added `extract_hierarchy()` method for structured data extraction
- Integrated hierarchy extraction into import workflow
- Added fallback to spatial entity parsing if hierarchy fails

### Recent Updates (March 2025) ✅
- Replaced hash-based coordinate fallbacks with real geometry extraction (profiles, extrusions, bounding boxes)
- Deterministic floor/room/equipment mapping via `IFCRELAGGREGATES` and `IFCRELCONTAINEDINSPATIALSTRUCTURE`
- Canonical slug/path generation wired into CLI imports and exporters
- Golden fixtures (`tests/fixtures/ifc/simple.ifc`) and renderer/export regression tests keep the pipeline honest

### Usage Example

```bash
# Import IFC with automatic hierarchy extraction
arx import building.ifc

# Extract hierarchy separately
arx ifc extract-hierarchy --file building.ifc --output building.yml
```
Equipment and rooms now inherit canonical parent paths; any fixture regressions are caught by the golden tests.

## Planned Enhancements

### Phase 1: Entity Classification Enhancement

**Goal:** Recognize and categorize all IFC entity types

**New Entity Type Recognition:**
- `IFCBUILDINGSTOREY` → Floor extraction
- `IFCSPACE` → Room extraction (with room type classification)
- `IFCFLOWTERMINAL` → HVAC Equipment
- `IFCLIGHTFIXTURE` → Electrical Equipment
- `IFCFLOWFITTING` → Plumbing Equipment

**Implementation:**
```rust
// Add to src/ifc/enhanced.rs
fn is_storey_entity(&self, entity_type: &str) -> bool {
    matches!(entity_type.to_uppercase().as_str(),
        "IFCBUILDINGSTOREY" | "IFCBUILDINGFLOOR" | "IFCLEVEL"
    )
}
```

### Phase 2: Hierarchy Building

**Goal:** Reconstruct complete building hierarchy

**New Components:**
- `EntityClassifier` - Classify entities by type
- `HierarchyBuilder` - Build Building → Floor → Room → Equipment tree
- `ReferenceResolver` - Resolve entity references and placement

**Architecture:**
```
IFC File
  ↓
EnhancedIFCParser (existing)
  ↓
Entity Classification Layer (NEW)
  ↓
Hierarchy Builder (NEW)
  ↓
Building Data Structure
```

### Phase 3: Reference Resolution

**Goal:** Handle entity references and spatial placement

- Resolve IFC reference syntax (#14 = placement reference)
- Infer spatial relationships from coordinates
- Map equipment to rooms based on Z-coordinate (floor level)

**Success Criteria:**
1. ✅ IFCBUILDINGSTOREY entities extracted as Floor objects
2. ✅ IFCSPACE entities extracted as Room objects with room types
3. ✅ IFCFLOWTERMINAL entities extracted as Equipment
4. ✅ Full hierarchy: Building → Floor → Room → Equipment
5. ✅ Spatial relationships preserved

### Testing Strategy

- Test with `test_data/sample_building.ifc` and `tests/fixtures/ifc/simple.ifc`
- Verify floor/room/equipment extraction
- Test with real-world IFC files
- Handle edge cases (no floors, no rooms, malformed files)
