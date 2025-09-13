# AR Database Schema Changes

## Overview

This document outlines the database schema modifications required to support the Mobile AR application features.

## Schema Version

**Current Version**: 2 (existing)  
**Target Version**: 3 (with AR support)

## New Tables

### 1. ar_anchors
Stores spatial anchor data for equipment placement in AR.

```sql
CREATE TABLE ar_anchors (
    id TEXT PRIMARY KEY,
    equipment_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    floor_id TEXT,
    room_id TEXT,
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    anchor_data BLOB NOT NULL,  -- Platform-specific anchor data
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,
    rotation_x REAL DEFAULT 0,
    rotation_y REAL DEFAULT 0,
    rotation_z REAL DEFAULT 0,
    scale_x REAL DEFAULT 1.0,
    scale_y REAL DEFAULT 1.0,
    scale_z REAL DEFAULT 1.0,
    confidence REAL DEFAULT 0.0,  -- Anchor confidence score (0-1)
    tracking_state TEXT DEFAULT 'normal',
    metadata TEXT,  -- JSON string for additional metadata
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (building_id) REFERENCES floor_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_ar_anchors_equipment ON ar_anchors(equipment_id);
CREATE INDEX idx_ar_anchors_building ON ar_anchors(building_id);
CREATE INDEX idx_ar_anchors_platform ON ar_anchors(platform);
CREATE INDEX idx_ar_anchors_created_by ON ar_anchors(created_by);
```

### 2. ar_worldmaps
Stores AR world mapping data for persistent cloud anchors.

```sql
CREATE TABLE ar_worldmaps (
    id TEXT PRIMARY KEY,
    building_id TEXT NOT NULL,
    floor_id TEXT,
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    worldmap_data BLOB NOT NULL,  -- Serialized world map data
    thumbnail BLOB,  -- Preview image
    map_extent_x REAL,  -- Physical extent in meters
    map_extent_y REAL,
    map_extent_z REAL,
    anchor_count INTEGER DEFAULT 0,
    size_bytes INTEGER NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- Optional expiration for cleanup
    FOREIGN KEY (building_id) REFERENCES floor_plans(id) ON DELETE CASCADE
);

CREATE INDEX idx_ar_worldmaps_building ON ar_worldmaps(building_id);
CREATE INDEX idx_ar_worldmaps_created_at ON ar_worldmaps(created_at);
```

### 3. ar_sessions
Tracks AR session analytics and multi-user coordination.

```sql
CREATE TABLE ar_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    floor_id TEXT,
    platform TEXT NOT NULL,
    device_model TEXT,
    os_version TEXT,
    app_version TEXT,
    ar_capabilities TEXT,  -- JSON array of device capabilities
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    equipment_viewed INTEGER DEFAULT 0,
    equipment_added INTEGER DEFAULT 0,
    equipment_updated INTEGER DEFAULT 0,
    anchors_created INTEGER DEFAULT 0,
    anchors_updated INTEGER DEFAULT 0,
    FOREIGN KEY (building_id) REFERENCES floor_plans(id) ON DELETE CASCADE
);

CREATE INDEX idx_ar_sessions_user ON ar_sessions(user_id);
CREATE INDEX idx_ar_sessions_building ON ar_sessions(building_id);
CREATE INDEX idx_ar_sessions_started ON ar_sessions(started_at);
```

## Modified Tables

### 1. equipment
Add AR-specific fields to existing equipment table.

```sql
-- Add new columns to equipment table
ALTER TABLE equipment ADD COLUMN manufacturer TEXT;
ALTER TABLE equipment ADD COLUMN model TEXT;
ALTER TABLE equipment ADD COLUMN serial_number TEXT;
ALTER TABLE equipment ADD COLUMN install_date DATE;
ALTER TABLE equipment ADD COLUMN last_service_date DATE;
ALTER TABLE equipment ADD COLUMN warranty_expiry DATE;
ALTER TABLE equipment ADD COLUMN ar_anchor_id TEXT;
ALTER TABLE equipment ADD COLUMN specifications TEXT;  -- JSON string

-- Add foreign key for AR anchor
ALTER TABLE equipment 
ADD CONSTRAINT fk_equipment_ar_anchor 
FOREIGN KEY (ar_anchor_id) REFERENCES ar_anchors(id) ON DELETE SET NULL;

-- Add indexes for new fields
CREATE INDEX idx_equipment_manufacturer ON equipment(manufacturer);
CREATE INDEX idx_equipment_serial ON equipment(serial_number);
CREATE INDEX idx_equipment_ar_anchor ON equipment(ar_anchor_id);
```

### 2. users (if exists) or sessions
Add AR-related user preferences and permissions.

```sql
-- Add AR preferences to users/sessions
ALTER TABLE users ADD COLUMN ar_preferences TEXT;  -- JSON preferences
ALTER TABLE users ADD COLUMN ar_tutorial_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN total_ar_sessions INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN total_ar_contributions INTEGER DEFAULT 0;
```

## Migration Script

```sql
-- Migration from version 2 to version 3
BEGIN TRANSACTION;

-- Check current version
SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;

-- Create AR tables
CREATE TABLE ar_anchors (...);  -- Full definition from above
CREATE TABLE ar_worldmaps (...);  -- Full definition from above
CREATE TABLE ar_sessions (...);  -- Full definition from above

-- Modify existing tables
ALTER TABLE equipment ADD COLUMN manufacturer TEXT;
-- ... other ALTER statements ...

-- Update schema version
INSERT INTO schema_version (version, description, applied_at) 
VALUES (3, 'Add AR support tables and fields', CURRENT_TIMESTAMP);

COMMIT;
```

## Go Migration Code

```go
// migrations.go - Add to existing migrations array

{
    Version:     3,
    Description: "Add AR support",
    Up: `
        -- AR Anchors table
        CREATE TABLE IF NOT EXISTS ar_anchors (
            id TEXT PRIMARY KEY,
            equipment_id TEXT NOT NULL,
            building_id TEXT NOT NULL,
            floor_id TEXT,
            room_id TEXT,
            platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
            anchor_data BLOB NOT NULL,
            position_x REAL NOT NULL,
            position_y REAL NOT NULL,
            position_z REAL NOT NULL,
            rotation_x REAL DEFAULT 0,
            rotation_y REAL DEFAULT 0,
            rotation_z REAL DEFAULT 0,
            scale_x REAL DEFAULT 1.0,
            scale_y REAL DEFAULT 1.0,
            scale_z REAL DEFAULT 1.0,
            confidence REAL DEFAULT 0.0,
            tracking_state TEXT DEFAULT 'normal',
            metadata TEXT,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
            FOREIGN KEY (building_id) REFERENCES floor_plans(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
        );

        -- AR Worldmaps table
        CREATE TABLE IF NOT EXISTS ar_worldmaps (
            id TEXT PRIMARY KEY,
            building_id TEXT NOT NULL,
            floor_id TEXT,
            platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
            worldmap_data BLOB NOT NULL,
            thumbnail BLOB,
            map_extent_x REAL,
            map_extent_y REAL,
            map_extent_z REAL,
            anchor_count INTEGER DEFAULT 0,
            size_bytes INTEGER NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (building_id) REFERENCES floor_plans(id) ON DELETE CASCADE
        );

        -- AR Sessions table
        CREATE TABLE IF NOT EXISTS ar_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            building_id TEXT NOT NULL,
            floor_id TEXT,
            platform TEXT NOT NULL,
            device_model TEXT,
            os_version TEXT,
            app_version TEXT,
            ar_capabilities TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            duration_seconds INTEGER,
            equipment_viewed INTEGER DEFAULT 0,
            equipment_added INTEGER DEFAULT 0,
            equipment_updated INTEGER DEFAULT 0,
            anchors_created INTEGER DEFAULT 0,
            anchors_updated INTEGER DEFAULT 0,
            FOREIGN KEY (building_id) REFERENCES floor_plans(id) ON DELETE CASCADE
        );

        -- Add AR fields to equipment
        ALTER TABLE equipment ADD COLUMN manufacturer TEXT;
        ALTER TABLE equipment ADD COLUMN model TEXT;
        ALTER TABLE equipment ADD COLUMN serial_number TEXT;
        ALTER TABLE equipment ADD COLUMN install_date DATE;
        ALTER TABLE equipment ADD COLUMN last_service_date DATE;
        ALTER TABLE equipment ADD COLUMN warranty_expiry DATE;
        ALTER TABLE equipment ADD COLUMN ar_anchor_id TEXT;
        ALTER TABLE equipment ADD COLUMN specifications TEXT;

        -- Create indexes
        CREATE INDEX idx_ar_anchors_equipment ON ar_anchors(equipment_id);
        CREATE INDEX idx_ar_anchors_building ON ar_anchors(building_id);
        CREATE INDEX idx_ar_anchors_platform ON ar_anchors(platform);
        CREATE INDEX idx_ar_worldmaps_building ON ar_worldmaps(building_id);
        CREATE INDEX idx_ar_sessions_user ON ar_sessions(user_id);
        CREATE INDEX idx_ar_sessions_building ON ar_sessions(building_id);
        CREATE INDEX idx_equipment_ar_anchor ON equipment(ar_anchor_id);
    `,
    Down: `
        DROP TABLE IF EXISTS ar_sessions;
        DROP TABLE IF EXISTS ar_worldmaps;
        DROP TABLE IF EXISTS ar_anchors;
        
        -- Note: Removing columns from equipment would lose data
        -- Consider keeping them or backing up first
    `,
}
```

## Data Models (Go)

```go
// models/ar.go

package models

import (
    "time"
    "database/sql/driver"
)

// ARAnchor represents a spatial anchor for equipment
type ARAnchor struct {
    ID            string    `json:"id" db:"id"`
    EquipmentID   string    `json:"equipment_id" db:"equipment_id"`
    BuildingID    string    `json:"building_id" db:"building_id"`
    FloorID       *string   `json:"floor_id,omitempty" db:"floor_id"`
    RoomID        *string   `json:"room_id,omitempty" db:"room_id"`
    Platform      string    `json:"platform" db:"platform"`
    AnchorData    []byte    `json:"anchor_data" db:"anchor_data"`
    Position      Position  `json:"position"`
    Rotation      Rotation  `json:"rotation"`
    Scale         Scale     `json:"scale"`
    Confidence    float64   `json:"confidence" db:"confidence"`
    TrackingState string    `json:"tracking_state" db:"tracking_state"`
    Metadata      *string   `json:"metadata,omitempty" db:"metadata"`
    CreatedBy     string    `json:"created_by" db:"created_by"`
    CreatedAt     time.Time `json:"created_at" db:"created_at"`
    UpdatedAt     time.Time `json:"updated_at" db:"updated_at"`
}

// Position represents 3D coordinates
type Position struct {
    X float64 `json:"x" db:"position_x"`
    Y float64 `json:"y" db:"position_y"`
    Z float64 `json:"z" db:"position_z"`
}

// Rotation represents 3D rotation in degrees
type Rotation struct {
    X float64 `json:"x" db:"rotation_x"`
    Y float64 `json:"y" db:"rotation_y"`
    Z float64 `json:"z" db:"rotation_z"`
}

// Scale represents 3D scale factors
type Scale struct {
    X float64 `json:"x" db:"scale_x"`
    Y float64 `json:"y" db:"scale_y"`
    Z float64 `json:"z" db:"scale_z"`
}

// ARWorldMap represents saved AR world mapping data
type ARWorldMap struct {
    ID           string     `json:"id" db:"id"`
    BuildingID   string     `json:"building_id" db:"building_id"`
    FloorID      *string    `json:"floor_id,omitempty" db:"floor_id"`
    Platform     string     `json:"platform" db:"platform"`
    WorldMapData []byte     `json:"-" db:"worldmap_data"`
    Thumbnail    []byte     `json:"-" db:"thumbnail"`
    MapExtent    *MapExtent `json:"map_extent,omitempty"`
    AnchorCount  int        `json:"anchor_count" db:"anchor_count"`
    SizeBytes    int        `json:"size_bytes" db:"size_bytes"`
    CreatedBy    string     `json:"created_by" db:"created_by"`
    CreatedAt    time.Time  `json:"created_at" db:"created_at"`
    ExpiresAt    *time.Time `json:"expires_at,omitempty" db:"expires_at"`
}

// MapExtent represents the physical extent of a world map
type MapExtent struct {
    X float64 `json:"x" db:"map_extent_x"`
    Y float64 `json:"y" db:"map_extent_y"`
    Z float64 `json:"z" db:"map_extent_z"`
}

// ARSession represents an AR session for analytics
type ARSession struct {
    ID               string    `json:"id" db:"id"`
    UserID           string    `json:"user_id" db:"user_id"`
    BuildingID       string    `json:"building_id" db:"building_id"`
    FloorID          *string   `json:"floor_id,omitempty" db:"floor_id"`
    Platform         string    `json:"platform" db:"platform"`
    DeviceModel      *string   `json:"device_model,omitempty" db:"device_model"`
    OSVersion        *string   `json:"os_version,omitempty" db:"os_version"`
    AppVersion       *string   `json:"app_version,omitempty" db:"app_version"`
    ARCapabilities   *string   `json:"ar_capabilities,omitempty" db:"ar_capabilities"`
    StartedAt        time.Time `json:"started_at" db:"started_at"`
    EndedAt          *time.Time `json:"ended_at,omitempty" db:"ended_at"`
    DurationSeconds  *int      `json:"duration_seconds,omitempty" db:"duration_seconds"`
    EquipmentViewed  int       `json:"equipment_viewed" db:"equipment_viewed"`
    EquipmentAdded   int       `json:"equipment_added" db:"equipment_added"`
    EquipmentUpdated int       `json:"equipment_updated" db:"equipment_updated"`
    AnchorsCreated   int       `json:"anchors_created" db:"anchors_created"`
    AnchorsUpdated   int       `json:"anchors_updated" db:"anchors_updated"`
}
```

## Query Examples

### Get all anchors for a building
```sql
SELECT 
    a.*,
    e.name as equipment_name,
    e.type as equipment_type
FROM ar_anchors a
JOIN equipment e ON a.equipment_id = e.id
WHERE a.building_id = ?
ORDER BY a.created_at DESC;
```

### Get AR session analytics
```sql
SELECT 
    COUNT(*) as total_sessions,
    AVG(duration_seconds) as avg_duration,
    SUM(equipment_added) as total_equipment_added,
    SUM(equipment_updated) as total_equipment_updated
FROM ar_sessions
WHERE building_id = ?
    AND started_at >= datetime('now', '-30 days');
```

### Find equipment with AR anchors
```sql
SELECT 
    e.*,
    a.platform,
    a.confidence,
    a.tracking_state
FROM equipment e
LEFT JOIN ar_anchors a ON e.ar_anchor_id = a.id
WHERE e.floor_plan_id = ?
    AND a.id IS NOT NULL;
```

## Performance Considerations

1. **BLOB Storage**: AR anchor data and world maps can be large. Consider:
   - Implementing compression before storage
   - Setting size limits (e.g., 10MB for world maps)
   - Regular cleanup of expired data

2. **Indexing**: Critical indexes included for:
   - Foreign key lookups
   - Platform-specific queries
   - Time-based queries for analytics

3. **Data Retention**: Consider implementing:
   - Automatic cleanup of old AR sessions
   - World map expiration
   - Anchor consolidation for duplicate equipment

## Backup Considerations

Due to the addition of BLOB data:
1. Database size will increase significantly
2. Implement separate backup strategy for AR data
3. Consider excluding world map BLOBs from frequent backups
4. Store world maps in external object storage for production