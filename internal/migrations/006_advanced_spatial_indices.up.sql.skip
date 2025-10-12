-- Advanced Spatial Indices for Query Optimization
-- This migration creates multi-resolution and specialized spatial indices

-- Drop existing basic indices if they exist
DROP INDEX IF EXISTS idx_equipment_position;
DROP INDEX IF EXISTS idx_equipment_positions_spatial;

-- Multi-resolution spatial indices for different query scales
-- Coarse grid (10m resolution) for large area queries
CREATE INDEX IF NOT EXISTS idx_equipment_position_coarse
    ON equipment_positions
    USING GIST (ST_SnapToGrid(position, 10.0))
    WHERE position IS NOT NULL;

-- Medium grid (1m resolution) for building-level queries
CREATE INDEX IF NOT EXISTS idx_equipment_position_medium
    ON equipment_positions
    USING GIST (ST_SnapToGrid(position, 1.0))
    WHERE position IS NOT NULL;

-- Fine grid (10cm resolution) for room-level queries
CREATE INDEX IF NOT EXISTS idx_equipment_position_fine
    ON equipment_positions
    USING GIST (ST_SnapToGrid(position, 0.1))
    WHERE position IS NOT NULL;

-- 3D spatial index for Z-axis queries (floor-based searches)
CREATE INDEX IF NOT EXISTS idx_equipment_position_3d
    ON equipment_positions
    USING GIST (position gist_geometry_ops_nd)
    WHERE position IS NOT NULL;

-- Partial indices for equipment types (common query patterns)
CREATE INDEX IF NOT EXISTS idx_hvac_equipment_spatial
    ON equipment_positions
    USING GIST (position)
    WHERE equipment_id IN (
        SELECT id FROM equipment WHERE type = 'hvac'
    );

CREATE INDEX IF NOT EXISTS idx_electrical_equipment_spatial
    ON equipment_positions
    USING GIST (position)
    WHERE equipment_id IN (
        SELECT id FROM equipment WHERE type = 'electrical'
    );

CREATE INDEX IF NOT EXISTS idx_sensor_equipment_spatial
    ON equipment_positions
    USING GIST (position)
    WHERE equipment_id IN (
        SELECT id FROM equipment WHERE type = 'sensor'
    );

-- Covering index for common query patterns (includes frequently accessed columns)
CREATE INDEX IF NOT EXISTS idx_equipment_covering
    ON equipment_positions
    USING GIST (position)
    INCLUDE (confidence, source, updated_at)
    WHERE position IS NOT NULL;

-- Time-based partial index for recent data (last 7 days)
CREATE INDEX IF NOT EXISTS idx_recent_positions
    ON equipment_positions
    USING GIST (position)
    WHERE updated_at > NOW() - INTERVAL '7 days'
      AND position IS NOT NULL;

-- Index for movement tracking (positions that have changed)
CREATE INDEX IF NOT EXISTS idx_position_changes
    ON equipment_positions (equipment_id, updated_at DESC)
    WHERE updated_at IS NOT NULL;

-- Composite index for floor-based queries
CREATE INDEX IF NOT EXISTS idx_floor_equipment
    ON equipment (floor_id, type, status)
    WHERE floor_id IS NOT NULL;

-- Index for bounding box queries
CREATE INDEX IF NOT EXISTS idx_equipment_bbox
    ON equipment_positions
    USING GIST (ST_Envelope(position))
    WHERE position IS NOT NULL;

-- Create spatial index on floor boundaries
CREATE INDEX IF NOT EXISTS idx_floor_boundaries_spatial
    ON floor_boundaries
    USING GIST (boundary)
    WHERE boundary IS NOT NULL;

-- KNN (K-Nearest Neighbors) optimization index
CREATE INDEX IF NOT EXISTS idx_equipment_knn
    ON equipment_positions
    USING GIST (position gist_geometry_ops)
    WHERE position IS NOT NULL;

-- Create materialized view for floor equipment counts (refresh periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_floor_equipment_stats AS
SELECT
    f.id as floor_id,
    f.name as floor_name,
    COUNT(DISTINCT ep.equipment_id) as equipment_count,
    ST_Extent(ep.position) as floor_extent,
    ST_Centroid(ST_Collect(ep.position)) as floor_centroid
FROM floors f
LEFT JOIN floor_boundaries fb ON f.id = fb.floor_id
LEFT JOIN equipment_positions ep ON ST_Contains(fb.boundary, ep.position)
GROUP BY f.id, f.name
WITH DATA;

-- Index on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_floor_stats_floor_id
    ON mv_floor_equipment_stats (floor_id);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_floor_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_floor_equipment_stats;
END;
$$ LANGUAGE plpgsql;

-- Cluster table for better performance (organize data physically by spatial location)
-- This should be done during maintenance window
-- CLUSTER equipment_positions USING idx_equipment_position_medium;

-- Update table statistics for query planner
ANALYZE equipment_positions;
ANALYZE equipment;
ANALYZE floors;
ANALYZE floor_boundaries;

-- Create notification trigger for real-time spatial updates
CREATE OR REPLACE FUNCTION notify_spatial_change()
RETURNS trigger AS $$
DECLARE
    payload json;
BEGIN
    payload = json_build_object(
        'type', TG_OP,
        'equipment_id', NEW.equipment_id,
        'position', json_build_object(
            'x', ST_X(NEW.position),
            'y', ST_Y(NEW.position),
            'z', ST_Z(NEW.position)
        ),
        'timestamp', NOW(),
        'source', NEW.source
    );

    PERFORM pg_notify('spatial_changes', payload::text);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to equipment_positions table
DROP TRIGGER IF EXISTS spatial_change_trigger ON equipment_positions;
CREATE TRIGGER spatial_change_trigger
    AFTER INSERT OR UPDATE OF position ON equipment_positions
    FOR EACH ROW
    EXECUTE FUNCTION notify_spatial_change();

-- Add table for caching common query results (optional, for extremely frequent queries)
CREATE TABLE IF NOT EXISTS spatial_query_cache (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    query_params JSONB NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_query_cache_hash
    ON spatial_query_cache (query_hash, expires_at);

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_spatial_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM spatial_query_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON INDEX idx_equipment_position_coarse IS 'Coarse spatial index for large area queries (10m grid)';
COMMENT ON INDEX idx_equipment_position_medium IS 'Medium spatial index for building queries (1m grid)';
COMMENT ON INDEX idx_equipment_position_fine IS 'Fine spatial index for room queries (0.1m grid)';
COMMENT ON INDEX idx_equipment_position_3d IS '3D spatial index for floor-based queries';
COMMENT ON INDEX idx_equipment_covering IS 'Covering index with frequently accessed columns';
COMMENT ON MATERIALIZED VIEW mv_floor_equipment_stats IS 'Cached statistics for floor equipment';