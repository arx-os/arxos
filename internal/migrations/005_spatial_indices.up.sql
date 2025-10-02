-- Migration 005: Add comprehensive spatial indices for performance
-- Description: Creates spatial indices and optimizes PostGIS queries

BEGIN;

-- ============================================================================
-- SPATIAL INDICES FOR EQUIPMENT
-- ============================================================================

-- Create spatial index on equipment positions (if not exists)
CREATE INDEX IF NOT EXISTS idx_equipment_position
ON equipment USING GIST(position);

-- Create compound index for building-specific queries
CREATE INDEX IF NOT EXISTS idx_equipment_building_position
ON equipment(building_id, position);

-- Create index for floor-specific queries
CREATE INDEX IF NOT EXISTS idx_equipment_building_floor
ON equipment(building_id, floor);

-- Create index for equipment type searches
CREATE INDEX IF NOT EXISTS idx_equipment_type
ON equipment(type);

-- Create index for status filtering
CREATE INDEX IF NOT EXISTS idx_equipment_status
ON equipment(status);

-- ============================================================================
-- SPATIAL INDICES FOR BUILDINGS
-- ============================================================================

-- Create spatial index on building origins
CREATE INDEX IF NOT EXISTS idx_buildings_origin
ON buildings USING GIST(origin);

-- Create index for arxos_id lookups
CREATE INDEX IF NOT EXISTS idx_buildings_arxos_id
ON buildings(arxos_id);

-- ============================================================================
-- EQUIPMENT POSITIONS TABLE (for tracking position history)
-- ============================================================================

CREATE TABLE IF NOT EXISTS equipment_positions (
    equipment_id UUID PRIMARY KEY REFERENCES equipment(id) ON DELETE CASCADE,
    position GEOMETRY(PointZ, 4326) NOT NULL,
    confidence SMALLINT DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 3),
    source TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create spatial index on positions
CREATE INDEX IF NOT EXISTS idx_equipment_positions_position
ON equipment_positions USING GIST(position);

-- Create index for confidence queries
CREATE INDEX IF NOT EXISTS idx_equipment_positions_confidence
ON equipment_positions(confidence);

-- ============================================================================
-- BUILDING TRANSFORMS TABLE (for coordinate system transformations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS building_transforms (
    building_id UUID PRIMARY KEY REFERENCES buildings(id) ON DELETE CASCADE,
    origin GEOMETRY(PointZ, 4326) NOT NULL,
    rotation FLOAT DEFAULT 0,
    grid_scale FLOAT DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create spatial index on origins
CREATE INDEX IF NOT EXISTS idx_building_transforms_origin
ON building_transforms USING GIST(origin);

-- ============================================================================
-- SCANNED REGIONS TABLE (for coverage tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS scanned_regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    floor INTEGER,
    region GEOMETRY(Polygon, 4326) NOT NULL,
    confidence SMALLINT DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 3),
    scan_type TEXT,
    scanner_id TEXT,
    scanned_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create spatial index on regions
CREATE INDEX IF NOT EXISTS idx_scanned_regions_region
ON scanned_regions USING GIST(region);

-- Create compound index for building/floor queries
CREATE INDEX IF NOT EXISTS idx_scanned_regions_building_floor
ON scanned_regions(building_id, floor);

-- ============================================================================
-- SPATIAL ANCHORS TABLE (for AR anchoring)
-- ============================================================================

CREATE TABLE IF NOT EXISTS spatial_anchors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    position GEOMETRY(PointZ, 4326) NOT NULL,
    anchor_data JSONB,
    confidence FLOAT DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create spatial index on anchor positions
CREATE INDEX IF NOT EXISTS idx_spatial_anchors_position
ON spatial_anchors USING GIST(position);

-- Create index for confidence filtering
CREATE INDEX IF NOT EXISTS idx_spatial_anchors_confidence
ON spatial_anchors(confidence);

-- ============================================================================
-- POINT CLOUDS TABLE (for LiDAR data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS point_clouds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id TEXT UNIQUE NOT NULL,
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    points GEOMETRY(MultiPointZ, 4326),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create spatial index on point clouds
CREATE INDEX IF NOT EXISTS idx_point_clouds_points
ON point_clouds USING GIST(points);

-- Create index for scan_id lookups
CREATE INDEX IF NOT EXISTS idx_point_clouds_scan_id
ON point_clouds(scan_id);

-- ============================================================================
-- HELPER FUNCTIONS FOR SPATIAL QUERIES
-- ============================================================================

-- Function to find equipment within a radius (in meters)
CREATE OR REPLACE FUNCTION find_equipment_within_radius(
    center_point GEOMETRY,
    radius_meters FLOAT
)
RETURNS TABLE(
    equipment_id UUID,
    distance_meters FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        ST_Distance(e.position::geography, center_point::geography) as dist
    FROM equipment e
    WHERE ST_DWithin(e.position::geography, center_point::geography, radius_meters)
    ORDER BY dist;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate coverage percentage for a building
CREATE OR REPLACE FUNCTION calculate_building_coverage(
    p_building_id UUID
)
RETURNS FLOAT AS $$
DECLARE
    total_area FLOAT;
    covered_area FLOAT;
BEGIN
    -- Calculate total building area (convex hull of all equipment)
    SELECT ST_Area(ST_ConvexHull(ST_Collect(position))::geography)
    INTO total_area
    FROM equipment
    WHERE building_id = p_building_id;

    -- Calculate covered area (union of all scanned regions)
    SELECT ST_Area(ST_Union(region)::geography)
    INTO covered_area
    FROM scanned_regions
    WHERE building_id = p_building_id;

    IF total_area IS NULL OR total_area = 0 THEN
        RETURN 0;
    END IF;

    RETURN COALESCE((covered_area / total_area) * 100, 0);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================================================

-- Materialized view for equipment spatial summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_equipment_spatial_summary AS
SELECT
    e.building_id,
    e.floor,
    COUNT(*) as equipment_count,
    ST_Extent(e.position) as spatial_extent,
    ST_Centroid(ST_Collect(e.position)) as centroid
FROM equipment e
WHERE e.position IS NOT NULL
GROUP BY e.building_id, e.floor;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_equipment_spatial_building
ON mv_equipment_spatial_summary(building_id);

-- ============================================================================
-- VACUUM AND ANALYZE FOR OPTIMIZATION
-- ============================================================================

-- Analyze all spatial tables for query optimization
ANALYZE equipment;
ANALYZE buildings;
ANALYZE equipment_positions;
ANALYZE building_transforms;
ANALYZE scanned_regions;
ANALYZE spatial_anchors;
ANALYZE point_clouds;

COMMIT;

-- Add comment to track migration
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 005 applied';