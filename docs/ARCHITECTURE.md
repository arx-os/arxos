# ArxOS Architecture Documentation

## Overview

ArxOS is a "Git for Buildings" system that enables version control and collaboration for building information models (BIM) using Git repositories and YAML data structures.

## Core Architecture

### 1. Universal Path System

The Universal Path System provides hierarchical addressing for building components:

```
/BUILDING/{building-name}/FLOOR/{floor-level}/{system-type}/{equipment-name}
```

**Examples:**
- `/BUILDING/Office-Building/FLOOR/2/HVAC/VAV-301`
- `/BUILDING/Office-Building/FLOOR/2/ROOM/Room-101/HVAC/VAV-301`

**Key Features:**
- **Git-Safe Paths**: Automatic sanitization of special characters
- **Conflict Resolution**: Numeric suffixes for duplicate paths
- **Validation**: Comprehensive path format validation
- **File System Mapping**: Automatic conversion to directory structures

### 2. Spatial Data Model

ArxOS uses a comprehensive 3D spatial data model:

```rust
pub struct SpatialEntity {
    pub id: String,
    pub name: String,
    pub entity_type: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub coordinate_system: Option<CoordinateSystem>,
}
```

**Components:**
- **Point3D**: 3D coordinates with x, y, z values
- **BoundingBox3D**: 3D bounding boxes for spatial entities
- **CoordinateSystem**: Support for multiple coordinate systems
- **SpatialEntity**: Unified entity with spatial properties

### 3. YAML Data Structure

Building data is serialized to hierarchical YAML:

```yaml
building:
  id: building-uuid
  name: Building Name
  description: Building description
  created_at: 2025-10-22T18:36:48Z
  updated_at: 2025-10-22T18:36:48Z
  version: 1.0.0
  global_bounding_box:
    min: {x: 0, y: 0, z: 0}
    max: {x: 100, y: 100, z: 30}

metadata:
  source_file: building.ifc
  parser_version: ArxOS v2.0
  total_entities: 150
  spatial_entities: 150
  coordinate_system: World
  units: meters
  tags: [ifc, building]

floors:
  - id: floor-1
    name: Floor 1
    level: 1
    elevation: 0.0
    rooms: [...]
    equipment: [...]
    bounding_box: {...}

coordinate_systems:
  - name: World
    origin: {x: 0, y: 0, z: 0}
    x_axis: {x: 1, y: 0, z: 0}
    y_axis: {x: 0, y: 1, z: 0}
    z_axis: {x: 0, y: 0, z: 1}
```

### 4. Git Repository Structure

ArxOS creates organized Git repositories with the following structure:

```
building-repo/
├── building.yml              # Main building data
├── index.yml                 # Navigation index
├── floors/
│   ├── floor-1.yml           # Floor data
│   ├── floor-2.yml
│   └── floor-1/
│       ├── rooms/
│       │   ├── room-101.yml
│       │   └── room-102.yml
│       └── equipment/
│           ├── HVAC/
│           │   ├── vav-301.yml
│           │   └── vav-302.yml
│           └── ELECTRICAL/
│               └── panel-301.yml
```

## Implementation Details

### 1. IFC Processing

ArxOS uses a custom STEP parser for IFC files:

**Features:**
- **Entity Detection**: Identifies IFCSPACE, IFCFLOWTERMINAL, IFCWALL, etc.
- **Spatial Extraction**: Extracts 3D coordinates and bounding boxes
- **Mock Data Generation**: Creates realistic spatial data for testing
- **Error Handling**: Comprehensive error handling with fallback mechanisms

**Process:**
1. Parse STEP file content
2. Extract building information
3. Identify spatial entities
4. Generate spatial data
5. Create building data structure

### 2. Path Generation Strategy

**Decision: Hybrid Path System**
- **Descriptive Paths**: Include building names and room information
- **Git-Safe Formatting**: Automatic sanitization of special characters
- **Conflict Resolution**: Numeric suffixes for duplicate paths
- **Validation**: Comprehensive path format validation

**Examples:**
- Equipment in room: `/BUILDING/Office-Building/FLOOR/2/ROOM/Room-101/HVAC/VAV-301`
- Equipment without room: `/BUILDING/Office-Building/FLOOR/2/HVAC/VAV-301`
- Room: `/BUILDING/Office-Building/FLOOR/2/ROOM/Room-101`

### 3. Git Operations Strategy

**Decision: Local Git First**
- **Local Repositories**: Start with local Git for simplicity
- **Structured Commits**: Grouped commits by entity type
- **File Organization**: Granular files for better Git diff tracking
- **Version Control**: Full Git history for building changes

**Commit Strategy:**
- **Building Updates**: Single commit per import
- **Entity Changes**: Separate commits for different entity types
- **Metadata**: Automatic commit messages with entity counts

### 4. Data Organization Philosophy

**Decision: Granular File Structure**
- **Individual Files**: Separate files for each entity
- **Hierarchical Organization**: Directory structure matching building hierarchy
- **Performance**: Fast operations with Git's efficient storage
- **Usability**: Human-readable file structure

**Benefits:**
- **Better Diffs**: Git can track individual entity changes
- **Collaboration**: Multiple people can edit different entities
- **Performance**: Only changed files need to be processed
- **Scalability**: Handles large buildings with thousands of entities

## API Design

### 1. CLI Commands

```bash
# Import IFC file and generate YAML
arx import building.ifc

# Export to Git repository
arx export --repo ./building-repo

# Render building in terminal
arx render --building "Building Name"

# Validate building data
arx validate --path ./building-repo
```

### 2. Library API

```rust
// IFC Processing
let processor = IFCProcessor::new();
let (building, spatial_entities) = processor.process_file("building.ifc")?;

// YAML Serialization
let serializer = BuildingYamlSerializer::new();
let building_data = serializer.serialize_building(&building, &spatial_entities, Some("building.ifc"))?;

// Path Generation
let mut path_generator = PathGenerator::new("Building Name");
let path = path_generator.generate_equipment_path("VAV-301", 2, "HVAC", Some("Room-101"))?;

// Git Operations
let config = GitConfigManager::default_config();
let mut git_manager = BuildingGitManager::new("./repo", "Building Name", config)?;
let result = git_manager.export_building(&building_data, Some("Update building data"))?;
```

## Error Handling

ArxOS uses comprehensive error handling with custom error types:

```rust
#[derive(Debug, thiserror::Error)]
pub enum IFCError {
    #[error("IFC file not found: {path}")]
    FileNotFound { path: String },
    
    #[error("Parsing error: {message}")]
    ParsingError { message: String },
    
    #[error("Invalid format: {reason}")]
    InvalidFormat { reason: String },
}

#[derive(Debug, thiserror::Error)]
pub enum PathError {
    #[error("Path conflict: too many conflicts for base path {base_path}")]
    TooManyConflicts { base_path: String },
    
    #[error("Invalid path format: {path}")]
    InvalidFormat { path: String },
}

#[derive(Debug, thiserror::Error)]
pub enum GitError {
    #[error("Git repository error: {0}")]
    GitError(#[from] git2::Error),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}
```

## Testing Strategy

### 1. Unit Tests
- **Path Generation**: Test path creation, sanitization, and conflict resolution
- **Spatial Data**: Test coordinate calculations and bounding box operations
- **YAML Serialization**: Test data structure serialization
- **Git Operations**: Test repository creation and commit operations

### 2. Integration Tests
- **IFC Processing**: Test with real IFC files
- **End-to-End**: Test complete import → YAML → Git workflow
- **Error Handling**: Test error conditions and recovery

### 3. Performance Tests
- **Large Buildings**: Test with buildings containing thousands of entities
- **Git Operations**: Test performance with large repositories
- **Memory Usage**: Monitor memory consumption during processing

## Future Enhancements

### 1. Remote Git Integration
- **GitHub/GitLab**: Support for remote repositories
- **Authentication**: Token-based authentication
- **Webhooks**: Automatic updates on repository changes

### 2. Advanced Spatial Operations
- **Coordinate Transformations**: Support for multiple coordinate systems
- **Spatial Queries**: Find equipment within radius, collision detection
- **3D Visualization**: Enhanced terminal rendering

### 3. Collaboration Features
- **Merge Conflicts**: Intelligent conflict resolution for building data
- **Branching**: Support for building variants and versions
- **Permissions**: Role-based access control

### 4. Performance Optimizations
- **Incremental Updates**: Only process changed entities
- **Caching**: Cache parsed IFC data and spatial calculations
- **Parallel Processing**: Multi-threaded IFC parsing

## Conclusion

ArxOS provides a robust foundation for "Git for Buildings" with:

- **Comprehensive Spatial Data Model**: Full 3D coordinate support
- **Universal Path System**: Hierarchical addressing with conflict resolution
- **Structured YAML Format**: Human-readable building data
- **Real Git Integration**: Full version control capabilities
- **Extensible Architecture**: Designed for future enhancements

The system successfully bridges the gap between traditional BIM workflows and modern version control practices, enabling collaboration and change tracking for building information models.
