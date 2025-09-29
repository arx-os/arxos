# ArxOS Storage Coordinator

## Overview

The `StorageCoordinator` replaces the complex multi-backend storage system with a clean, purpose-built coordinator that implements ArxOS's multi-level data architecture.

## Architecture

### Before (Complex Multi-Backend)
```
┌─────────────────────────────────────────┐
│          Storage Manager                │
├─────────────────────────────────────────┤
│  Primary Backend │ Fallback │ Cache     │
│  (S3/GCS/Azure) │ Backend  │ Backend   │
│  Complex retry  │ Sync     │ Metadata  │
│  Streaming ops  │ Logic    │ Operations│
└─────────────────────────────────────────┘
```

### After (Multi-Level Coordinator)
```
┌─────────────────────────────────────────┐
│        Storage Coordinator             │
├─────────────────────────────────────────┤
│  BIM Files     │  PostGIS    │ Cache   │
│  (.bim.txt)    │  (Spatial)  │ (Cache) │
│  Schematic     │  Precision  │ Queries │
└─────────────────────────────────────────┘
```

## Multi-Level Data Strategy

### 1. Schematic Level (BIM Files)
- **Storage**: `.bim.txt` files in filesystem
- **Purpose**: Human-readable building schematics
- **Users**: Building managers, Git version control
- **Precision**: Grid-based coordinates (0.5m resolution)

### 2. Spatial Level (PostGIS Database)
- **Storage**: PostGIS spatial database
- **Purpose**: Millimeter-precision 3D coordinates
- **Users**: AR mobile app, field technicians
- **Precision**: Real-world coordinates (mm level)

### 3. Query Level (Cache)
- **Storage**: In-memory cache
- **Purpose**: Fast queries and system tracing
- **Users**: Terminal operations, systems engineers
- **Precision**: Optimized for relationships and performance

## Usage Examples

### Building Manager (Overview)
```go
// Load schematic view from .bim.txt
building, err := coordinator.GetBuilding(ctx, buildingID, QueryOverview)
// Returns: BIM file data with grid coordinates
```

### Field Technician (Spatial)
```go
// Load precise coordinates for AR
building, err := coordinator.GetBuilding(ctx, buildingID, QuerySpatial)
// Returns: PostGIS spatial anchors with mm precision
```

### Systems Engineer (Detail)
```go
// Load for system tracing and analysis
building, err := coordinator.GetBuilding(ctx, buildingID, QueryDetail)
// Returns: Cached data optimized for queries
```

## Coordinate Translation

The coordinator automatically handles coordinate translation between:

- **Grid Coordinates**: `LOCATION: (45, 30)` in .bim.txt
- **World Coordinates**: `(12.547, 8.291, 1.127)` in PostGIS
- **Significant Change Detection**: Only updates .bim.txt for major moves

## Data Flow

### AR Edit Flow
```
AR App Edit (3D) → PostGIS Update → Coordinate Translation → 
Significant Change? → Yes: Update .bim.txt → Git Commit
                   → No: Cache in memory only
```

### Terminal Edit Flow
```
Terminal Edit → Memory Cache → Auto-sync → .bim.txt Update → Git Commit
```

### BIM File Edit Flow
```
.bim.txt Edit → File Watcher → Coordinate Translation → PostGIS Update
```

## Migration from Old System

```go
// Migrate existing data
config := DefaultCoordinatorConfig()
coordinator, _ := NewStorageCoordinator(config)

// Migrate from old complex storage
MigrateFromOldStorage("/old/storage/path", coordinator)

// Clean up old system
CleanupOldStorage("/old/storage/path")
```

## Benefits

1. **Simplified Architecture**: No more complex multi-backend abstraction
2. **Purpose-Built**: Each storage layer serves specific user needs
3. **Coordinate Translation**: Automatic bridging between precision levels
4. **Performance**: Right tool for each job (files, spatial DB, query cache)
5. **Maintainable**: Clear separation of concerns

## Configuration

```go
config := &CoordinatorConfig{
    BIMFilesPath:   "~/.arxos/buildings",     // .bim.txt files
    DatabasePath:   "postgres://localhost/arxos",     // PostGIS
    AutoSync:       true,                     // Auto-sync between layers
    SyncInterval:   30 * time.Second,        // Sync frequency
    ValidateOnSave: true,                     // Validate .bim.txt files
}
```

## Future Enhancements

- **PostGIS Integration**: Use PostGIS for all spatial operations
- **Real-time Sync**: WebSocket updates between storage layers
- **Conflict Resolution**: Handle concurrent edits from multiple sources
- **Backup Strategy**: Automated backups of all storage layers
