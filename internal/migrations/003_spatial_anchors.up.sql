-- Migration: Add spatial anchor support for AR
-- This starts with simple 2D+floor, can migrate to PostGIS later

-- Table for AR spatial anchors
CREATE TABLE IF NOT EXISTS spatial_anchors (
    id TEXT PRIMARY KEY,
    building_uuid TEXT NOT NULL,
    equipment_path TEXT NOT NULL,

    -- Simple spatial data (upgrade to PostGIS geometry later)
    x_meters REAL NOT NULL,
    y_meters REAL NOT NULL,
    z_meters REAL DEFAULT 0,
    floor INTEGER NOT NULL,

    -- Rotation as quaternion
    rotation_x REAL DEFAULT 0,
    rotation_y REAL DEFAULT 0,
    rotation_z REAL DEFAULT 0,
    rotation_w REAL DEFAULT 1,

    -- Platform-specific AR anchor data
    platform TEXT CHECK(platform IN ('ARKit', 'ARCore', 'Other')),
    anchor_data bytea, -- Raw anchor data from AR platform (PostgreSQL uses bytea instead of BLOB)

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,

    -- Constraints
    UNIQUE(building_uuid, equipment_path),
    FOREIGN KEY (building_uuid) REFERENCES buildings(id)
);

-- Index for spatial queries (PostGIS)
CREATE INDEX IF NOT EXISTS idx_spatial_anchors_location
    ON spatial_anchors(building_uuid, floor, x_meters, y_meters);

-- Index for equipment lookups
CREATE INDEX IF NOT EXISTS idx_spatial_anchors_equipment
    ON spatial_anchors(building_uuid, equipment_path);

-- Table for spatial zones/regions
CREATE TABLE IF NOT EXISTS spatial_zones (
    id TEXT PRIMARY KEY,
    building_uuid TEXT NOT NULL,
    name TEXT NOT NULL,
    zone_type TEXT CHECK(zone_type IN ('room', 'floor', 'area', 'zone')),

    -- Bounding box (simple rectangle for now)
    min_x REAL NOT NULL,
    min_y REAL NOT NULL,
    max_x REAL NOT NULL,
    max_y REAL NOT NULL,
    floor INTEGER NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (building_uuid) REFERENCES buildings(id)
);

-- View for equipment with spatial data
CREATE OR REPLACE VIEW equipment_spatial AS
SELECT
    e.id as equipment_id,
    e.equipment_type,
    e.status,
    sa.building_uuid,
    sa.equipment_path,
    sa.x_meters,
    sa.y_meters,
    sa.floor,
    sa.platform,
    sa.updated_at
FROM equipment e
LEFT JOIN spatial_anchors sa ON sa.equipment_path LIKE '%' || e.id || '%';
