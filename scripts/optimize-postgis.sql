-- PostGIS Performance Optimization for ArxOS
-- This script creates optimal indices, partitions, and query optimizations
-- Runs after init-postgis.sql during container initialization

-- ============================================================================
-- PERFORMANCE CONFIGURATION
-- ============================================================================

-- Optimize PostGIS settings for building data workloads
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;  -- SSD optimization
ALTER SYSTEM SET cpu_tuple_cost = 0.01;
ALTER SYSTEM SET cpu_index_tuple_cost = 0.005;
ALTER SYSTEM SET cpu_operator_cost = 0.0025;

-- PostGIS specific optimizations
ALTER SYSTEM SET postgis.gdal_datapath = '/usr/share/gdal';
ALTER SYSTEM SET postgis.enable_outdb_rasters = true;
ALTER SYSTEM SET postgis.gdal_enabled_drivers = 'ENABLE_ALL';

-- ============================================================================
-- SPATIAL INDICES
-- ============================================================================

-- Create spatial indices for all geometry columns
CREATE INDEX IF NOT EXISTS idx_buildings_geometry ON buildings USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_buildings_bbox ON buildings USING GIST (st_envelope(geometry));

CREATE INDEX IF NOT EXISTS idx_floors_geometry ON floors USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_floors_building_level ON floors (building_id, level);
CREATE INDEX IF NOT EXISTS idx_floors_elevation ON floors USING BTREE (elevation_mm);

CREATE INDEX IF NOT EXISTS idx_rooms_geometry ON rooms USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms (floor_id);
CREATE INDEX IF NOT EXISTS idx_rooms_number ON rooms (room_number);
CREATE INDEX IF NOT EXISTS idx_rooms_type ON rooms (room_type) WHERE room_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_equipment_room ON equipment (room_id);
CREATE INDEX IF NOT EXISTS idx_equipment_type_status ON equipment (equipment_type, status);
CREATE INDEX IF NOT EXISTS idx_equipment_tag ON equipment (equipment_tag) WHERE equipment_tag IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_equipment_maintained ON equipment (last_maintained)
    WHERE last_maintained IS NOT NULL;

-- Spatial relationship indices for common queries
CREATE INDEX IF NOT EXISTS idx_spatial_contains_rooms ON rooms USING GIST (geometry)
    WHERE geometry IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_spatial_within_equipment ON equipment USING GIST (location)
    WHERE location IS NOT NULL;

-- ============================================================================
-- BTREE INDICES FOR LOOKUPS
-- ============================================================================

-- UUID lookups (primary keys are already indexed)
CREATE INDEX IF NOT EXISTS idx_buildings_arxos_id ON buildings (arxos_id) WHERE arxos_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_floors_uuid ON floors (uuid);
CREATE INDEX IF NOT EXISTS idx_rooms_uuid ON rooms (uuid);
CREATE INDEX IF NOT EXISTS idx_equipment_uuid ON equipment (uuid);

-- Name searches
CREATE INDEX IF NOT EXISTS idx_buildings_name ON buildings USING GIN (to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_rooms_name ON rooms USING GIN (to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_equipment_name ON equipment USING GIN (to_tsvector('english', name));

-- Status and type filtering
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment (status);
CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment (equipment_type);

-- Temporal indices for history tracking
CREATE INDEX IF NOT EXISTS idx_import_history_timestamp ON import_history (imported_at DESC);
CREATE INDEX IF NOT EXISTS idx_export_history_timestamp ON export_history (exported_at DESC);
CREATE INDEX IF NOT EXISTS idx_equipment_installed ON equipment (installed_date)
    WHERE installed_date IS NOT NULL;

-- ============================================================================
-- MATERIALIZED VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Equipment summary by floor
CREATE MATERIALIZED VIEW IF NOT EXISTS equipment_floor_summary AS
SELECT
    f.id as floor_id,
    f.name as floor_name,
    f.level,
    COUNT(e.id) as equipment_count,
    COUNT(DISTINCT e.equipment_type) as equipment_types,
    COUNT(CASE WHEN e.status = 'operational' THEN 1 END) as operational_count,
    COUNT(CASE WHEN e.status = 'maintenance' THEN 1 END) as maintenance_count,
    COUNT(CASE WHEN e.status = 'fault' THEN 1 END) as fault_count,
    MAX(e.last_maintained) as last_maintenance,
    ST_Extent(e.location) as equipment_bbox
FROM floors f
LEFT JOIN rooms r ON r.floor_id = f.id
LEFT JOIN equipment e ON e.room_id = r.id
GROUP BY f.id, f.name, f.level;

CREATE UNIQUE INDEX IF NOT EXISTS idx_equipment_floor_summary_id ON equipment_floor_summary (floor_id);
CREATE INDEX IF NOT EXISTS idx_equipment_floor_summary_level ON equipment_floor_summary (level);

-- Spatial proximity view for equipment relationships
CREATE MATERIALIZED VIEW IF NOT EXISTS equipment_proximity AS
SELECT
    e1.id as equipment1_id,
    e2.id as equipment2_id,
    e1.equipment_type as type1,
    e2.equipment_type as type2,
    ST_Distance(e1.location, e2.location) as distance_mm,
    e1.room_id = e2.room_id as same_room,
    r.floor_id as floor_id
FROM equipment e1
CROSS JOIN equipment e2
JOIN rooms r ON e1.room_id = r.id
WHERE e1.id < e2.id  -- Avoid duplicates
    AND ST_DWithin(e1.location, e2.location, 10000)  -- Within 10 meters
    AND e1.location IS NOT NULL
    AND e2.location IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_equipment_proximity_distance
    ON equipment_proximity (distance_mm);
CREATE INDEX IF NOT EXISTS idx_equipment_proximity_types
    ON equipment_proximity (type1, type2);

-- ============================================================================
-- PARTITIONING STRATEGY
-- ============================================================================

-- Partition import/export history by month for better performance
CREATE TABLE IF NOT EXISTS import_history_y2024m01 PARTITION OF import_history
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE IF NOT EXISTS import_history_y2024m02 PARTITION OF import_history
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- Add more partitions as needed

CREATE TABLE IF NOT EXISTS export_history_y2024m01 PARTITION OF export_history
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE IF NOT EXISTS export_history_y2024m02 PARTITION OF export_history
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- Add more partitions as needed

-- ============================================================================
-- QUERY OPTIMIZATION FUNCTIONS
-- ============================================================================

-- Function to find equipment within a bounding box (optimized)
CREATE OR REPLACE FUNCTION find_equipment_in_bbox(
    min_x DOUBLE PRECISION,
    min_y DOUBLE PRECISION,
    max_x DOUBLE PRECISION,
    max_y DOUBLE PRECISION
)
RETURNS TABLE (
    id UUID,
    name VARCHAR,
    equipment_tag VARCHAR,
    location GEOMETRY
)
LANGUAGE plpgsql
STABLE PARALLEL SAFE
AS $$
BEGIN
    RETURN QUERY
    SELECT e.id, e.name, e.equipment_tag, e.location
    FROM equipment e
    WHERE e.location && ST_MakeEnvelope(min_x, min_y, max_x, max_y, 900913)
        AND ST_Within(e.location, ST_MakeEnvelope(min_x, min_y, max_x, max_y, 900913));
END;
$$;

-- Function to find nearest equipment (optimized with KNN)
CREATE OR REPLACE FUNCTION find_nearest_equipment(
    from_point GEOMETRY,
    equipment_type VARCHAR DEFAULT NULL,
    max_distance DOUBLE PRECISION DEFAULT 10000,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    name VARCHAR,
    distance DOUBLE PRECISION
)
LANGUAGE plpgsql
STABLE PARALLEL SAFE
AS $$
BEGIN
    RETURN QUERY
    SELECT e.id, e.name, ST_Distance(e.location, from_point) as dist
    FROM equipment e
    WHERE (equipment_type IS NULL OR e.equipment_type = equipment_type)
        AND ST_DWithin(e.location, from_point, max_distance)
    ORDER BY e.location <-> from_point
    LIMIT limit_count;
END;
$$;

-- ============================================================================
-- VACUUM AND ANALYZE STRATEGY
-- ============================================================================

-- Create maintenance function for regular optimization
CREATE OR REPLACE FUNCTION maintain_spatial_indices()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Vacuum and analyze spatial tables
    VACUUM ANALYZE buildings;
    VACUUM ANALYZE floors;
    VACUUM ANALYZE rooms;
    VACUUM ANALYZE equipment;

    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW CONCURRENTLY equipment_floor_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY equipment_proximity;

    -- Update spatial index statistics
    ANALYZE buildings (geometry);
    ANALYZE floors (geometry);
    ANALYZE rooms (geometry);
    ANALYZE equipment (location);

    RAISE NOTICE 'Spatial maintenance completed at %', NOW();
END;
$$;

-- Schedule regular maintenance (requires pg_cron extension)
-- Uncomment if pg_cron is available:
-- SELECT cron.schedule('spatial-maintenance', '0 3 * * *', 'SELECT maintain_spatial_indices();');

-- ============================================================================
-- CLUSTERING FOR SPATIAL LOCALITY
-- ============================================================================

-- Cluster tables by spatial indices for better cache performance
CLUSTER equipment USING idx_equipment_location;
CLUSTER rooms USING idx_rooms_geometry;
CLUSTER floors USING idx_floors_geometry;

-- ============================================================================
-- CONSTRAINT OPTIMIZATIONS
-- ============================================================================

-- Add check constraints for faster exclusion
ALTER TABLE equipment ADD CONSTRAINT chk_location_valid
    CHECK (ST_IsValid(location));
ALTER TABLE rooms ADD CONSTRAINT chk_geometry_valid
    CHECK (ST_IsValid(geometry));
ALTER TABLE floors ADD CONSTRAINT chk_geometry_valid
    CHECK (ST_IsValid(geometry));
ALTER TABLE buildings ADD CONSTRAINT chk_geometry_valid
    CHECK (ST_IsValid(geometry));

-- Add range constraints for coordinates (building assumed < 1km x 1km)
ALTER TABLE equipment ADD CONSTRAINT chk_location_bounds
    CHECK (ST_X(location) BETWEEN 0 AND 1000000
       AND ST_Y(location) BETWEEN 0 AND 1000000
       AND ST_Z(location) BETWEEN -100000 AND 500000);

-- ============================================================================
-- STATISTICS CONFIGURATION
-- ============================================================================

-- Increase statistics targets for frequently filtered columns
ALTER TABLE equipment ALTER COLUMN equipment_type SET STATISTICS 1000;
ALTER TABLE equipment ALTER COLUMN status SET STATISTICS 1000;
ALTER TABLE rooms ALTER COLUMN room_type SET STATISTICS 500;
ALTER TABLE equipment ALTER COLUMN location SET STATISTICS 1000;

-- ============================================================================
-- CONNECTION POOLING RECOMMENDATIONS
-- ============================================================================

-- Note: These settings are for PgBouncer if used
-- pool_mode = transaction
-- max_client_conn = 1000
-- default_pool_size = 25
-- min_pool_size = 10
-- server_idle_timeout = 600

-- ============================================================================
-- MONITORING QUERIES
-- ============================================================================

-- Create view for monitoring spatial index usage
CREATE OR REPLACE VIEW spatial_index_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE indexname LIKE '%geometry%'
   OR indexname LIKE '%location%'
   OR indexname LIKE '%spatial%'
ORDER BY idx_scan DESC;

-- Create function to check query performance
CREATE OR REPLACE FUNCTION check_slow_queries()
RETURNS TABLE (
    query TEXT,
    calls BIGINT,
    total_time DOUBLE PRECISION,
    mean_time DOUBLE PRECISION,
    max_time DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        query,
        calls,
        total_exec_time as total_time,
        mean_exec_time as mean_time,
        max_exec_time as max_time
    FROM pg_stat_statements
    WHERE query LIKE '%ST_%'  -- Spatial queries
       OR query LIKE '%equipment%'
       OR query LIKE '%rooms%'
    ORDER BY mean_exec_time DESC
    LIMIT 20;
$$;

-- ============================================================================
-- COMPLETION NOTICE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'PostGIS optimization completed successfully';
    RAISE NOTICE 'Spatial indices created: %',
        (SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE '%geometry%' OR indexname LIKE '%spatial%');
    RAISE NOTICE 'Tables clustered for spatial locality';
    RAISE NOTICE 'Materialized views created for common queries';
    RAISE NOTICE 'Performance settings optimized for building data';
END $$;