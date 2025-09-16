# ArxOS Spatial Development Plan
## Spatial Precision & Progressive Enhancement Implementation

### Executive Summary

This document outlines the comprehensive development plan for implementing spatial precision and progressive enhancement capabilities in ArxOS. The plan introduces a dual-core architecture combining semantic data (.bim.txt) with millimeter-precision spatial data (PostGIS), enabling progressive refinement from multiple data sources.

## 📋 Technical Requirements

### Core Requirements

1. **Dual Storage System**
   - SQLite for semantic data and queries (existing)
   - PostGIS for spatial precision (new)
   - Bidirectional sync with configurable thresholds

2. **Coordinate Systems**
   - Grid coordinates: Integer-based for .bim.txt (existing)
   - World coordinates: Float64 3D positions in meters (new)
   - GPS anchoring for real-world alignment (new)

3. **Data Confidence Levels**
   - 4-tier system: ESTIMATED → LOW → MEDIUM → HIGH
   - Separate tracking for position vs semantic confidence
   - Source attribution for audit trail

4. **Performance Targets**
   - Coordinate translation: < 10ms per point
   - Partial scan merge: < 5 seconds for 10,000 points
   - Coverage calculation: < 100ms for building
   - Query with confidence: < 200ms for filtered results

## 🗄️ PostGIS Integration Architecture

### Database Schema

```sql
-- Spatial extension setup
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Building spatial reference
CREATE TABLE building_spatial_refs (
    building_id VARCHAR(255) PRIMARY KEY,
    origin_gps GEOGRAPHY(POINT, 4326),
    origin_local GEOMETRY(POINT, 0),
    rotation_degrees FLOAT,
    grid_scale FLOAT, -- meters per grid unit
    floor_height FLOAT, -- meters between floors
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Equipment precise positions
CREATE TABLE equipment_positions (
    equipment_id VARCHAR(255) PRIMARY KEY,
    building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id),
    position_3d GEOMETRY(POINTZ, 0), -- local coordinates
    position_confidence INTEGER, -- 0=ESTIMATED, 1=LOW, 2=MEDIUM, 3=HIGH
    position_source VARCHAR(50), -- 'pdf', 'ifc', 'lidar', 'ar_verified'
    position_updated TIMESTAMP,
    bounding_box GEOMETRY(POLYGON, 0),
    orientation FLOAT[3] -- rotation in degrees [x,y,z]
);

-- Scanned regions tracking
CREATE TABLE scanned_regions (
    id SERIAL PRIMARY KEY,
    building_id VARCHAR(255),
    scan_id VARCHAR(255),
    region_boundary GEOMETRY(POLYGON, 0),
    scan_date TIMESTAMP,
    scan_type VARCHAR(50), -- 'lidar', 'photogrammetry', 'ar_verify'
    point_density FLOAT, -- points per sq meter
    confidence_score FLOAT,
    raw_data_url TEXT -- reference to point cloud storage
);

-- Point cloud storage
CREATE TABLE point_clouds (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(255),
    building_id VARCHAR(255),
    points GEOMETRY(MULTIPOINTZ, 0),
    metadata JSONB,
    processed BOOLEAN DEFAULT FALSE
);
```

### Hybrid Database Strategy

The system will implement a hybrid approach where PostGIS is optional but provides enhanced capabilities when available:

- **Online Mode**: Full PostGIS functionality with spatial queries
- **Offline Mode**: SQLite cache with queued updates for later sync
- **Fallback**: Automatic degradation to SQLite if PostGIS unavailable

## 🔄 Coordinate Translation Service

### Core Functionality

The coordinate translation service bridges grid coordinates (.bim.txt) and world coordinates (PostGIS):

- **Grid to World**: Convert integer grid positions to 3D world coordinates
- **World to Grid**: Map precise positions back to grid representation
- **GPS Integration**: Handle real-world GPS anchoring
- **AR Coordination**: Support AR-specific coordinate systems

### Movement Thresholds

- **Grid Unit Threshold**: 1.0 units (triggers .bim.txt update)
- **Room Change Threshold**: 0.5 meters
- **Floor Change Margin**: 0.1 meters
- **Rotation Threshold**: 5.0 degrees

## 📡 LiDAR Processing Pipeline

### Processing Stages

1. **Preprocessing**
   - Load point cloud (PLY, LAS, LAZ, E57 formats)
   - Filter noise
   - Downsample for performance

2. **Alignment**
   - Detect ground plane
   - Align to building coordinate system
   - Register with existing coverage

3. **Object Detection**
   - Segment point clusters
   - Classify objects
   - Extract features

4. **Equipment Matching**
   - Find candidate matches
   - Calculate confidence scores
   - Resolve ambiguities

## 📊 Confidence Tracking System

### Confidence Levels

- **ESTIMATED** (0): PDF/IFC without verification
- **LOW** (1): Automated detection
- **MEDIUM** (2): Partial verification
- **HIGH** (3): LiDAR or AR verified

### Tracking Dimensions

Each equipment item tracks:
- Position confidence and source
- Semantic confidence and source
- Last verification timestamp
- Verification history

## 🔀 Progressive Merge Algorithm

### Conflict Resolution Rules

1. **LiDAR Position Override**: LiDAR always wins for position data
2. **IFC Semantic Preference**: IFC preferred for metadata
3. **Recent AR Verification**: Recent field verification takes precedence
4. **Timestamp Priority**: Newer data preferred within same source type

### Merge Strategies

- **Position Conflicts**: Higher confidence source wins
- **Semantic Conflicts**: Merge metadata, preserve position
- **Existence Conflicts**: Require human review
- **Coverage Updates**: Automatic tracking of scanned regions

## 📈 Implementation Phases

### Phase 1: Spatial Foundation (Weeks 1-4)
- PostGIS setup and schema implementation
- Basic coordinate translator service
- Hybrid DB with offline fallback
- Update equipment model with spatial fields

### Phase 2: Confidence System (Weeks 5-6)
- Confidence data model implementation
- Update all importers to set confidence
- Confidence-based query API
- Confidence decay over time

### Phase 3: LiDAR Pipeline (Weeks 7-10)
- Point cloud format readers
- Alignment algorithms
- Object detection
- Equipment matching logic

### Phase 4: Progressive Merge (Weeks 11-13)
- Conflict detection engine
- Rule-based resolution system
- Merge strategies per source type
- User review queue

### Phase 5: AR Integration Prep (Weeks 14-16)
- AR coordinate system support
- Spatial anchor management
- Real-time position updates API
- Threshold-based BIM sync

## 🧪 Testing Strategy

### Unit Tests
- Coordinate translation accuracy
- Confidence calculations
- Conflict resolution rules
- Point cloud processing algorithms

### Integration Tests
- PostGIS ↔ SQLite sync
- Import → Merge → Export pipeline
- Coverage calculation with partial scans
- AR edit → BIM update flow

### Performance Tests
- 10M point cloud processing
- 10,000 equipment spatial queries
- Concurrent AR client updates
- Coverage calculation at scale

## 🚦 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| PostGIS availability | Hybrid DB with SQLite fallback |
| LiDAR processing performance | Downsampling, progressive loading |
| Merge conflicts causing data loss | Full audit trail, rollback capability |
| AR coordinate drift | Periodic recalibration, spatial anchors |

## 📚 Dependencies

New Go dependencies required:
- `github.com/twpayne/go-geom` - Geometry operations
- `github.com/cridenour/go-postgis` - PostGIS integration
- `github.com/fogleman/gg` - 2D graphics for coverage
- `github.com/g3n/engine` - 3D operations
- `gonum.org/v1/gonum` - Numerical computing

## Success Criteria

- All existing tests pass
- Translation accuracy < 1cm
- Query performance < 200ms
- 70% object detection accuracy
- 80% conflicts resolved automatically
- No data loss during merge
- Full audit trail maintained