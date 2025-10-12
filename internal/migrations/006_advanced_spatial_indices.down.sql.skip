-- Rollback Advanced Spatial Indices

-- Drop notification trigger and function
DROP TRIGGER IF EXISTS spatial_change_trigger ON equipment_positions;
DROP FUNCTION IF EXISTS notify_spatial_change();

-- Drop cache table and function
DROP TABLE IF EXISTS spatial_query_cache;
DROP FUNCTION IF EXISTS clean_spatial_cache();

-- Drop materialized view and refresh function
DROP MATERIALIZED VIEW IF EXISTS mv_floor_equipment_stats;
DROP FUNCTION IF EXISTS refresh_floor_stats();

-- Drop all advanced indices
DROP INDEX IF EXISTS idx_equipment_position_coarse;
DROP INDEX IF EXISTS idx_equipment_position_medium;
DROP INDEX IF EXISTS idx_equipment_position_fine;
DROP INDEX IF EXISTS idx_equipment_position_3d;
DROP INDEX IF EXISTS idx_hvac_equipment_spatial;
DROP INDEX IF EXISTS idx_electrical_equipment_spatial;
DROP INDEX IF EXISTS idx_sensor_equipment_spatial;
DROP INDEX IF EXISTS idx_equipment_covering;
DROP INDEX IF EXISTS idx_recent_positions;
DROP INDEX IF EXISTS idx_position_changes;
DROP INDEX IF EXISTS idx_floor_equipment;
DROP INDEX IF EXISTS idx_equipment_bbox;
DROP INDEX IF EXISTS idx_floor_boundaries_spatial;
DROP INDEX IF EXISTS idx_equipment_knn;
DROP INDEX IF EXISTS idx_mv_floor_stats_floor_id;

-- Recreate basic spatial index
CREATE INDEX idx_equipment_position
    ON equipment_positions
    USING GIST (position)
    WHERE position IS NOT NULL;