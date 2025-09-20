-- Migration 005: Rollback spatial indices and optimizations
-- Description: Removes spatial indices and optimization structures

BEGIN;

-- Drop materialized views
DROP MATERIALIZED VIEW IF EXISTS mv_equipment_spatial_summary;

-- Drop helper functions
DROP FUNCTION IF EXISTS find_equipment_within_radius(GEOMETRY, FLOAT);
DROP FUNCTION IF EXISTS calculate_building_coverage(UUID);

-- Drop indices on point_clouds
DROP INDEX IF EXISTS idx_point_clouds_scan_id;
DROP INDEX IF EXISTS idx_point_clouds_points;

-- Drop point_clouds table
DROP TABLE IF EXISTS point_clouds;

-- Drop indices on spatial_anchors
DROP INDEX IF EXISTS idx_spatial_anchors_confidence;
DROP INDEX IF EXISTS idx_spatial_anchors_position;

-- Drop spatial_anchors table
DROP TABLE IF EXISTS spatial_anchors;

-- Drop indices on scanned_regions
DROP INDEX IF EXISTS idx_scanned_regions_building_floor;
DROP INDEX IF EXISTS idx_scanned_regions_region;

-- Drop scanned_regions table
DROP TABLE IF EXISTS scanned_regions;

-- Drop indices on building_transforms
DROP INDEX IF EXISTS idx_building_transforms_origin;

-- Drop building_transforms table
DROP TABLE IF EXISTS building_transforms;

-- Drop indices on equipment_positions
DROP INDEX IF EXISTS idx_equipment_positions_confidence;
DROP INDEX IF EXISTS idx_equipment_positions_position;

-- Drop equipment_positions table
DROP TABLE IF EXISTS equipment_positions;

-- Drop indices on buildings
DROP INDEX IF EXISTS idx_buildings_arxos_id;
DROP INDEX IF EXISTS idx_buildings_origin;

-- Drop indices on equipment
DROP INDEX IF EXISTS idx_equipment_status;
DROP INDEX IF EXISTS idx_equipment_type;
DROP INDEX IF EXISTS idx_equipment_building_floor;
DROP INDEX IF EXISTS idx_equipment_building_position;
DROP INDEX IF EXISTS idx_equipment_position;

COMMIT;

-- Update comment
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 005 rolled back';