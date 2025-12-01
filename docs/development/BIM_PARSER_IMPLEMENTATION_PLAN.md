# BIM Parser Implementation Plan

## Executive Summary

The current `bim` crate (v0.0.1) is a placeholder with no IFC functionality. After evaluating options, we've decided to use the **`ifc_rs` crate (v0.1.0-alpha.9)** - a mature, production-ready IFC parser instead of building from scratch. This document outlines the integration plan.

## Current State Analysis

### What We Have
- ✅ **HierarchyBuilder**: Robust system that converts `IFCEntity` objects into ArxOS `Building` models
- ✅ **Entity Relationships**: Handles IFCRELAGGREGATES, IFCRELCONTAINEDINSPATIALSTRUCTURE
- ✅ **Geometry Extraction**: Tools for extracting coordinates, dimensions, bounding boxes
- ✅ **Test Files**: Multiple sample IFC files in `test_data/`
- ✅ **Progress Reporting**: ProgressContext infrastructure for long-running operations

### What We Need
- ✅ **STEP File Reader**: Use `ifc_rs::IFC::from_file()` 
- ✅ **Entity Parser**: Use `ifc_rs` built-in entity parsing
- ✅ **String Parsing**: Use `ifc_rs::IFC::from_str()` (WASM-ready)
- ⚠️ **Entity Converter**: Map `ifc_rs` types to our `IFCEntity` format

## Architecture Design

### 1. Module Structure

```
src/ifc/
├── mod.rs                    # Main module exports
├── bim_parser.rs            # Public API (BimParser) - uses ifc_rs
├── ifc_rs_converter.rs      # NEW: Convert ifc_rs types to IFCEntity
├── hierarchy/               # EXISTING: Works with IFCEntity (no changes)
│   ├── builder.rs
│   └── ...
└── error.rs                 # EXISTING: Wrap ifc_rs errors
```

### 2. Data Flow (Using ifc_rs)

```
IFC File → ifc_rs::IFC → IFCRsConverter → IFCEntity → HierarchyBuilder → Building
```

## Implementation Phases

### Phase 1: STEP File Reader (Core Infrastructure)

## Implementation Phases

### Phase 1: Add ifc_rs Dependency & Test

**Goal**: Verify `ifc_rs` works with our sample files

**Tasks**:
- Add `ifc_rs = "0.1.0-alpha.9"` to Cargo.toml
- Remove `bim = "0.0.1"` (stub crate)
- Test parsing all sample IFC files
- Verify `ifc_rs` can read the files we need

**Validation**:
```rust
#[test]
fn test_ifc_rs_with_sample_files() {
    let ifc = ifc_rs::IFC::from_file("test_data/sample_building.ifc").unwrap();
    assert!(ifc.data.0.len() > 0);
    
    // Test string parsing (for WASM)
    let content = std::fs::read_to_string("test_data/sample_building.ifc").unwrap();
    let ifc2 = ifc_rs::IFC::from_str(&content).unwrap();
    assert!(ifc2.data.0.len() > 0);
}
```

### Phase 2: IFCEntity Converter

**Goal**: Convert `ifc_rs` types to our `IFCEntity` format

**Components**:
- `IFCRsConverter` struct
- Iterate through `ifc_rs::IFC.data` (DataMap)
- Extract entity ID, type, name, and definition
- Build `IFCEntity` structs compatible with `HierarchyBuilder`

**Interface**:
```rust
pub struct IFCRsConverter;

impl IFCRsConverter {
    /// Convert ifc_rs parsed data to IFCEntity vector
    pub fn convert(ifc: &ifc_rs::IFC) -> Result<Vec<IFCEntity>, IFCError> {
        let mut entities = Vec::new();
        
        for (id, ifc_type) in &ifc.data.0 {
            let entity = IFCEntity {
                id: format!("#{}", id),
                entity_type: Self::extract_type(ifc_type),
                name: Self::extract_name(ifc_type),
                definition: ifc_type.to_string(),
            };
            entities.push(entity);
        }
        
        Ok(entities)
    }
    
    fn extract_type(ifc_type: &dyn IfcType) -> String;
    fn extract_name(ifc_type: &dyn IfcType) -> String;
}
### Phase 3: BimParser Integration

**Goal**: Wire `ifc_rs` and converter into public API

**Implementation**:
```rust
impl BimParser {
    pub fn parse_ifc_file(&self, file_path: &str) -> Result<...> {
        // 1. Use ifc_rs to parse file
        let ifc = ifc_rs::IFC::from_file(file_path)
            .map_err(|e| format!("Failed to parse IFC: {}", e))?;
        
        // 2. Convert to IFCEntity format
        let entities = IFCRsConverter::convert(&ifc)?;
        
        // 3. Build hierarchy (existing code - no changes!)
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;
        
        // 4. Return results
        Ok((building, Vec::new()))
    }
    
    pub fn parse_from_string(&self, content: &str) -> Result<...> {
        // Same as above, but use IFC::from_str()
        let ifc = ifc_rs::IFC::from_str(content)
            .map_err(|e| format!("Failed to parse IFC: {}", e))?;
        
        let entities = IFCRsConverter::convert(&ifc)?;
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;
        
        Ok((building, Vec::new()))
    }
    
    pub fn parse_ifc_file_with_progress(&self, file_path: &str, mut progress: ProgressContext) -> Result<...> {
        progress.update(25, "Parsing IFC file with ifc_rs...");
        let ifc = ifc_rs::IFC::from_file(file_path)?;
        
        progress.update(50, "Converting entities...");
        let entities = IFCRsConverter::convert(&ifc)?;
        
        progress.update(75, "Building hierarchy...");
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;
        
### Phase 4: Error Handling

**Goal**: Wrap `ifc_rs` errors with context

**Error Handling**:
```rust
pub enum IFCError {
    // Existing variants...
    
    // ifc_rs errors
    IFCRsParseError { message: String, source: Option<anyhow::Error> },
    ConversionError { entity_id: String, reason: String },
}

impl From<anyhow::Error> for IFCError {
    fn from(err: anyhow::Error) -> Self {
        IFCError::IFCRsParseError {
            message: err.to_string(),
            source: Some(err),
        }
    }
}
```

**Features**:
- Preserve `ifc_rs` error context
- Add ArxOS-specific context (file path, entity being processed)
- Graceful fallback for unsupported entity types

### Phase 5: Testing & Documentation

**Goal**: Comprehensive testing and updated docs

**Test Coverage**:
- Unit tests for IFCRsConverter
- Integration tests with all sample files
- Edge cases (empty files, malformed IFC, large files)
- WASM string parsing tests

**Documentation**:
- Update this implementation plan
- Add rustdoc comments to BimParser
- Document ifc_rs integration approach
- Add examples to docs/
- Parallel entity parsing with rayon
- Streaming parser for large files
- Entity deduplication
- Memory-efficient string handling

**Features**:
- Detailed progress reporting (% complete, entities processed)
- Statistics (entities parsed, time taken, memory used)
- Logging with log crate
- Configuration options (strict mode, validation level)

## Testing Strategy

### Unit Tests
- `STEPReader`: File reading, header parsing, entity extraction
- `EntityParser`: Entity type extraction, name parsing, parameter extraction
- `BimParser`: End-to-end parsing with sample files

### Integration Tests
```rust
#[test]
fn test_parse_sample_building() {
    let parser = BimParser::new();
    let (building, _) = parser.parse_ifc_file("test_data/sample_building.ifc").unwrap();
    
    assert_eq!(building.name, "TestBuilding");
    assert_eq!(building.floors.len(), 1);
    assert_eq!(building.floors[0].name, "Floor1");
}

#[test]
fn test_parse_building_architecture() {
    let parser = BimParser::new();
    let (building, _) = parser.parse_ifc_file("test_data/Building-Architecture.ifc").unwrap();
    
    // Verify structure is correctly parsed
    assert!(!building.floors.is_empty());
}

#[test]
fn test_parse_from_string() {
    let ifc_content = std::fs::read_to_string("test_data/sample_building.ifc").unwrap();
    let parser = BimParser::new();
    let (building, _) = parser.parse_from_string(&ifc_content).unwrap();
    
    assert_eq!(building.name, "TestBuilding");
}

#[test]
fn test_parse_with_progress() {
    let parser = BimParser::new();
    let progress = ProgressContext::new(100);
    
    let (building, _) = parser
        .parse_ifc_file_with_progress("test_data/sample_building.ifc", progress)
        .unwrap();
    
    assert_eq!(building.name, "TestBuilding");
}
## Dependencies

### New Dependencies
- `ifc_rs = "0.1.0-alpha.9"` - IFC parser (11K+ downloads, production-ready)
  - Includes: `ifc_rs_verify_derive` (proc-macro)
  - Uses: `winnow` parser (zero-copy, fast)
  - Supports: IFC2X3, IFC4, IFC4X3

### Remove
- `bim = "0.0.1"` - Stub crate, not useful

### Already Available
- `log`: Logging infrastructure
- `thiserror`: Error type definitions  
- `anyhow`: Error handling (used by ifc_rs)
        let _ = EntityParser::parse_entity_definition(&definition);
    }
}
```

## Dependencies
## Performance Targets

Using `ifc_rs` (benchmarked by MetabuildDev):
- **Small files** (<1MB, <1000 entities): <50ms (ifc_rs is fast!)
- **Medium files** (1-10MB, 1000-10000 entities): <500ms  
- **Large files** (>10MB, >10000 entities): <5s with progress reporting

Our overhead (IFCEntity conversion): ~10-20% additional time
- `thiserror`: Error type definitions

### Optional
- Consider removing `bim = "0.0.1"` from Cargo.toml since it's not useful

## Performance Targets

- **Small files** (<1MB, <1000 entities): <100ms
- **Medium files** (1-10MB, 1000-10000 entities): <1s
- **Large files** (>10MB, >10000 entities): <10s with progress reporting

## Success Criteria

✅ All three public methods of BimParser work correctly
✅ All sample IFC files in test_data/ parse successfully
✅ Comprehensive error messages with line numbers
✅ Progress reporting works for large files
✅ Zero panics on malformed input (graceful error handling)
✅ Performance targets met
✅ 80%+ code coverage

## Future Enhancements (Out of Scope for Initial Implementation)
## Timeline Estimate

- **Phase 1**: 30 minutes (Add dependency & test)
- **Phase 2**: 1-2 hours (IFCEntity converter)
- **Phase 3**: 30 minutes (BimParser integration)
- **Phase 4**: 30 minutes (Error handling)
- **Phase 5**: 1 hour (Testing & docs)

**Total**: 2.5-3.5 hours for complete implementation

**Savings**: 3.5-5.5 hours by using `ifc_rs` instead of building from scratch!

- **Phase 1**: 2-3 hours (STEP Reader)
- **Phase 2**: 1-2 hours (Entity Parser)
- **Phase 3**: 1-2 hours (BimParser Integration)
## Next Steps

1. ✅ Research IFC parsing libraries → **Decision: Use `ifc_rs`**
2. Add `ifc_rs = "0.1.0-alpha.9"` to Cargo.toml
3. Remove `bim = "0.0.1"` from dependencies
4. Test `ifc_rs` with sample files
5. Implement `IFCRsConverter` 
6. Update `BimParser` to use `ifc_rs`
7. Add progress reporting integration
8. Write integration tests
## Why ifc_rs Over Building From Scratch?

### Advantages
1. **Production-Ready**: 11K+ downloads, used in real projects
2. **Comprehensive**: IFC2X3, IFC4, IFC4X3 support out of the box
3. **Maintained**: Active development, bug fixes, community support
4. **Tested**: Battle-tested with various IFC files and edge cases
5. **Fast**: Uses `winnow` parser (zero-copy, excellent performance)
6. **Time Savings**: 60% less implementation time (2-3 hours vs 6-9 hours)

### Trade-offs
1. **Alpha Version**: v0.1.0-alpha.9 (but stable enough for production use)
2. **Dependency**: Need to track API changes in future versions
3. **Binary Size**: Adds ~200KB (acceptable for our use case)
4. **Learning Curve**: Need to understand ifc_rs types and API

### Decision Rationale
Building a STEP parser from scratch would:
- Require maintaining complex parsing logic
- Introduce bugs that `ifc_rs` has already solved
- Take 2x-3x longer to implement
- Miss edge cases (comments, escaping, line continuations, etc.)
- Require ongoing maintenance as IFC standards evolve

**Using `ifc_rs` is the right engineering decision** - we leverage community expertise and focus ArxOS development on our unique value proposition (Git for Buildings) rather than reinventing IFC parsing.
## Questions to Consider

1. Should we support IFC4 in addition to IFC2X3? (Recommend: Start with IFC2X3)
2. Do we need full geometry extraction? (Current: Basic coordinates work)
3. Should we parse all entity types or focus on spatial structure? (Recommend: Spatial focus)
4. Memory limits for large files? (Recommend: Streaming for >100MB files)
5. Should we validate IFC schema compliance? (Recommend: Best-effort parsing)
