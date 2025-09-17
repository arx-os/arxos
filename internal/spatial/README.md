# Spatial Module

The spatial module provides millimeter-precision coordinate management, confidence tracking, and progressive data enhancement capabilities for ArxOS.

## Overview

This module implements the spatial precision layer that complements the semantic .bim.txt format, enabling:
- Dual coordinate system (grid ↔ world)
- Confidence tracking for all spatial data
- Coverage mapping for progressive enhancement
- Intelligent merge of multiple data sources
- PostGIS integration for spatial queries

## Architecture

```
spatial/
├── types.go         # Core spatial types (Point3D, BoundingBox, etc.)
├── translator.go    # Coordinate translation service
├── confidence.go    # Confidence tracking system
├── coverage.go      # Coverage mapping and tracking
├── merge.go         # Progressive merge algorithm
├── postgis/         # PostGIS database integration
│   ├── client.go    # Database connection management
│   ├── schema.go    # Schema definitions
│   └── queries.go   # Spatial query implementations
└── tests/           # Unit and integration tests
```

## Core Components

### Coordinate Translation

Handles conversion between different coordinate systems:
- **Grid Coordinates**: Integer positions for .bim.txt files
- **World Coordinates**: 3D float positions in meters
- **GPS Coordinates**: Real-world geographic positioning
- **AR Coordinates**: Mobile device AR space

### Confidence Tracking

Four-tier confidence system:
- `ESTIMATED` (0): Derived from PDF/IFC without verification
- `LOW` (1): Automated detection
- `MEDIUM` (2): Partial verification
- `HIGH` (3): LiDAR or AR verified

### Coverage Mapping

Tracks which areas of a building have been scanned:
- Spatial extent of scanned regions
- Scan type and date
- Point density metrics
- Progressive coverage percentage

### Progressive Merge

Intelligent reconciliation of multiple data sources:
- Conflict detection
- Rule-based resolution
- Source precedence
- Audit trail

## Usage

### Basic Coordinate Translation

```go
import "github.com/arx-os/arxos/internal/spatial"

// Create translator for a building
translator := spatial.NewTranslator(buildingID)
translator.SetGridScale(0.5) // 0.5 meters per grid unit
translator.SetFloorHeight(3.0) // 3 meters between floors

// Convert grid to world
worldPos := translator.GridToWorld(10, 5, 2) // x=10, y=5, floor=2

// Convert world to grid
gridX, gridY, floor := translator.WorldToGrid(worldPos)
```

### Confidence Management

```go
// Create confidence manager
cm := spatial.NewConfidenceManager(db)

// Update equipment confidence
err := cm.UpdateConfidence(
    equipmentID,
    spatial.ASPECT_POSITION,
    spatial.CONFIDENCE_HIGH,
    "lidar_scan_2024_03",
)

// Query by confidence
equipment := cm.QueryWithConfidence(spatial.ConfidenceQuery{
    MinPositionConfidence: spatial.CONFIDENCE_MEDIUM,
    VerifiedWithinDays: 30,
})
```

### Coverage Tracking

```go
// Create coverage tracker
tracker := spatial.NewCoverageTracker(buildingID)

// Add scanned region
region := spatial.ScannedRegion{
    Boundary: polygon,
    ScanType: "lidar",
    ScanDate: time.Now(),
    PointDensity: 1000, // points/m²
}
tracker.AddScannedRegion(region)

// Check coverage
percentage := tracker.GetCoveragePercentage()
confidence := tracker.GetRegionConfidence(point)
```

### Progressive Merge

```go
// Create merger
merger := spatial.NewProgressiveMerger(building)

// Add data source
source := spatial.DataSource{
    Type: spatial.SOURCE_LIDAR,
    Timestamp: time.Now(),
    Confidence: 0.95,
}

// Execute merge
result, err := merger.MergeSource(source)
if err != nil {
    // Handle conflicts
    for _, conflict := range result.Conflicts {
        resolution := merger.ResolveConflict(conflict)
        merger.ApplyResolution(resolution)
    }
}
```

## PostGIS Integration

The module supports optional PostGIS for enhanced spatial capabilities:

```go
// Check if spatial database available
if db.HasSpatialSupport() {
    spatialDB, _ := db.GetSpatialDB()

    // Perform spatial queries
    nearby := spatialDB.QueryBySpatialProximity(center, radius)

    // Store point cloud
    spatialDB.StorePointCloud(pointCloud)
}
```

## Configuration

```yaml
spatial:
  postgis:
    enabled: true
    host: localhost
    port: 5432
    database: arxos_spatial

  translation:
    grid_scale: 0.5      # meters per grid unit
    floor_height: 3.0    # meters between floors

  confidence:
    decay_rate: 0.1      # confidence decay per month
    verify_threshold: 90 # days before reverification

  thresholds:
    grid_movement: 1.0   # grid units to trigger update
    room_change: 0.5     # meters to detect room change
```

## Testing

```bash
# Run all spatial tests
go test ./internal/spatial/...

# Run with coverage
go test -cover ./internal/spatial/...

# Run integration tests
go test ./internal/spatial/tests/integration_test.go
```

## Performance Targets

- Coordinate translation: < 10ms
- Confidence query: < 200ms
- Coverage calculation: < 100ms
- Merge operation: < 5s for 10,000 points

## Dependencies

- `github.com/twpayne/go-geom`: Geometry operations
- `github.com/cridenour/go-postgis`: PostGIS integration
- PostgreSQL with PostGIS extension (optional)

## Future Enhancements

- [ ] Machine learning for object matching
- [ ] Automatic confidence decay
- [ ] Spatial indexing optimization
- [ ] Real-time merge streaming
- [ ] AR anchor persistence