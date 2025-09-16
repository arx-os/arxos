-- Migration 001: Initial spatial schema
-- Creates the foundational PostGIS tables for ArxOS spatial features

-- Enable PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Building spatial reference system
CREATE TABLE IF NOT EXISTS building_spatial_refs (
    building_id VARCHAR(255) PRIMARY KEY,
    origin_gps GEOGRAPHY(POINT, 4326),
    origin_local GEOMETRY(POINT, 0),
    rotation_degrees FLOAT,
    grid_scale FLOAT DEFAULT 0.5, -- meters per grid unit
    floor_height FLOAT DEFAULT 3.0, -- meters between floors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Equipment precise positions
CREATE TABLE IF NOT EXISTS equipment_positions (
    equipment_id VARCHAR(255) PRIMARY KEY,
    building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id) ON DELETE CASCADE,
    position_3d GEOMETRY(POINTZ, 0), -- 3D position in local coordinates
    position_confidence INTEGER DEFAULT 0, -- 0=ESTIMATED, 1=LOW, 2=MEDIUM, 3=HIGH
    position_source VARCHAR(50), -- 'pdf', 'ifc', 'lidar', 'ar_verified'
    position_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bounding_box GEOMETRY(POLYGON, 0),
    orientation FLOAT[3], -- Euler angles in degrees [x,y,z]
    -- Grid coordinates for .bim.txt compatibility
    grid_x INTEGER,
    grid_y INTEGER,
    floor INTEGER
);

-- Scanned regions tracking
CREATE TABLE IF NOT EXISTS scanned_regions (
    id SERIAL PRIMARY KEY,
    building_id VARCHAR(255) REFERENCES building_spatial_refs(building_id) ON DELETE CASCADE,
    scan_id VARCHAR(255) UNIQUE NOT NULL,
    region_boundary GEOMETRY(POLYGON, 0),
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_type VARCHAR(50), -- 'lidar', 'photogrammetry', 'ar_verify'
    point_density FLOAT, -- points per square meter
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    raw_data_url TEXT,
    metadata JSONB
);

-- Create spatial indexes
CREATE INDEX idx_equipment_position_3d ON equipment_positions USING GIST(position_3d);
CREATE INDEX idx_equipment_bbox ON equipment_positions USING GIST(bounding_box);
CREATE INDEX idx_scanned_regions_boundary ON scanned_regions USING GIST(region_boundary);

-- Create regular indexes for performance
CREATE INDEX idx_equipment_building ON equipment_positions(building_id);
CREATE INDEX idx_equipment_confidence ON equipment_positions(position_confidence);
CREATE INDEX idx_equipment_grid ON equipment_positions(grid_x, grid_y, floor);
CREATE INDEX idx_scanned_regions_building ON scanned_regions(building_id);
CREATE INDEX idx_scanned_regions_date ON scanned_regions(scan_date DESC);

-- Add update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_building_spatial_refs_updated_at
    BEFORE UPDATE ON building_spatial_refs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_positions_updated_at
    BEFORE UPDATE ON equipment_positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();