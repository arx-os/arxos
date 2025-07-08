-- Migration: Database Performance Optimization
-- This migration implements performance optimizations based on analysis

-- ============================================================================
-- 1. ADD MISSING INDEXES FOR COMMON QUERIES
-- ============================================================================

-- Building queries optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_owner_id ON buildings(owner_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_project_id ON buildings(project_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_created_at ON buildings(created_at);

-- Floor queries optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_floors_building_id ON floors(building_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_floors_name ON floors(name);

-- Asset queries optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_building_system ON building_assets(building_id, system);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_building_floor ON building_assets(building_id, floor_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_status_created ON building_assets(status, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_asset_type_system ON building_assets(asset_type, system);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_symbol_id ON building_assets(symbol_id);

-- Asset history optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_history_asset_date ON asset_history(asset_id, event_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_history_event_type ON asset_history(event_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_history_created_by ON asset_history(created_by);

-- Asset maintenance optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_maintenance_asset_status ON asset_maintenance(asset_id, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_maintenance_scheduled_date ON asset_maintenance(scheduled_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_maintenance_type_status ON asset_maintenance(maintenance_type, status);

-- Audit logs optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_object_type_id ON audit_logs(object_type, object_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_action_created ON audit_logs(action, created_at);

-- ============================================================================
-- 2. COMPOSITE INDEXES FOR COMPLEX QUERIES
-- ============================================================================

-- Spatial queries with building context
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_walls_building_floor_status ON walls(building_id, floor_id, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_building_floor_category ON rooms(building_id, floor_id, category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_doors_building_floor_status ON doors(building_id, floor_id, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_windows_building_floor_status ON windows(building_id, floor_id, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_building_system_type ON devices(building_id, system, type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labels_building_floor_category ON labels(building_id, floor_id, category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zones_building_floor_category ON zones(building_id, floor_id, category);

-- User assignment queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_walls_assigned_status ON walls(assigned_to, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_assigned_status ON rooms(assigned_to, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_doors_assigned_status ON doors(assigned_to, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_windows_assigned_status ON windows(assigned_to, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_assigned_status ON devices(assigned_to, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_labels_assigned_status ON labels(assigned_to, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zones_assigned_status ON zones(assigned_to, status);

-- ============================================================================
-- 3. PARTIAL INDEXES FOR FILTERED QUERIES
-- ============================================================================

-- Active assets only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_active ON building_assets(building_id, system) WHERE status = 'active';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_inactive ON building_assets(building_id, system) WHERE status = 'inactive';

-- Recent audit logs
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_recent ON audit_logs(user_id, created_at) WHERE created_at > NOW() - INTERVAL '30 days';

-- Pending maintenance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_maintenance_pending ON asset_maintenance(asset_id, scheduled_date) WHERE status = 'pending';

-- Locked objects
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_walls_locked ON walls(building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_locked ON rooms(building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_doors_locked ON doors(building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_windows_locked ON windows(building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_locked ON devices(building_id, floor_id) WHERE locked_by IS NOT NULL;

-- ============================================================================
-- 4. COVERING INDEXES FOR FREQUENTLY ACCESSED COLUMNS
-- ============================================================================

-- Building covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_covering ON buildings(owner_id) INCLUDE (name, address, created_at);

-- Asset covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_covering ON building_assets(building_id, system) INCLUDE (asset_type, status, created_at);

-- Floor covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_floors_covering ON floors(building_id) INCLUDE (name, svg_path);

-- ============================================================================
-- 5. SPATIAL INDEX OPTIMIZATION
-- ============================================================================

-- Ensure spatial indexes exist and are optimized
-- Note: These should already exist from the original schema, but we'll ensure they're properly configured

-- Drop and recreate spatial indexes with better configuration
DROP INDEX IF EXISTS idx_walls_geom;
CREATE INDEX CONCURRENTLY idx_walls_geom ON walls USING GIST (geom) WITH (FILLFACTOR = 90);

DROP INDEX IF EXISTS idx_rooms_geom;
CREATE INDEX CONCURRENTLY idx_rooms_geom ON rooms USING GIST (geom) WITH (FILLFACTOR = 90);

DROP INDEX IF EXISTS idx_doors_geom;
CREATE INDEX CONCURRENTLY idx_doors_geom ON doors USING GIST (geom) WITH (FILLFACTOR = 90);

DROP INDEX IF EXISTS idx_windows_geom;
CREATE INDEX CONCURRENTLY idx_windows_geom ON windows USING GIST (geom) WITH (FILLFACTOR = 90);

DROP INDEX IF EXISTS idx_devices_geom;
CREATE INDEX CONCURRENTLY idx_devices_geom ON devices USING GIST (geom) WITH (FILLFACTOR = 90);

DROP INDEX IF EXISTS idx_labels_geom;
CREATE INDEX CONCURRENTLY idx_labels_geom ON labels USING GIST (geom) WITH (FILLFACTOR = 90);

DROP INDEX IF EXISTS idx_zones_geom;
CREATE INDEX CONCURRENTLY idx_zones_geom ON zones USING GIST (geom) WITH (FILLFACTOR = 90);

-- ============================================================================
-- 6. FUNCTIONAL INDEXES FOR COMPLEX QUERIES
-- ============================================================================

-- Case-insensitive search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_name_lower ON buildings(LOWER(name));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_floors_name_lower ON floors(LOWER(name));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_asset_type_lower ON building_assets(LOWER(asset_type));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_system_lower ON building_assets(LOWER(system));

-- Date-based indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_created_date ON buildings(DATE(created_at));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_created_date ON building_assets(DATE(created_at));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_date ON audit_logs(DATE(created_at));

-- ============================================================================
-- 7. STATISTICS AND ANALYZE
-- ============================================================================

-- Update table statistics for better query planning
ANALYZE buildings;
ANALYZE floors;
ANALYZE building_assets;
ANALYZE asset_history;
ANALYZE asset_maintenance;
ANALYZE audit_logs;
ANALYZE walls;
ANALYZE rooms;
ANALYZE doors;
ANALYZE windows;
ANALYZE devices;
ANALYZE labels;
ANALYZE zones;

-- ============================================================================
-- 8. PERFORMANCE MONITORING VIEWS
-- ============================================================================

-- Create performance monitoring view
CREATE OR REPLACE VIEW performance_monitoring AS
SELECT 
    'index_usage' as metric_type,
    schemaname,
    tablename,
    indexname,
    idx_scan as value,
    CASE 
        WHEN idx_scan = 0 THEN 'unused'
        WHEN idx_scan < 10 THEN 'rarely_used'
        WHEN idx_scan < 100 THEN 'occasionally_used'
        ELSE 'frequently_used'
    END as status
FROM pg_stat_user_indexes
UNION ALL
SELECT 
    'table_scans' as metric_type,
    schemaname,
    tablename,
    '' as indexname,
    seq_scan as value,
    CASE 
        WHEN seq_scan > idx_scan THEN 'high_seq_scans'
        WHEN seq_scan > 0 THEN 'some_seq_scans'
        ELSE 'index_scans_only'
    END as status
FROM pg_stat_user_tables;

-- Create cache performance view
CREATE OR REPLACE VIEW cache_performance_monitoring AS
SELECT 
    schemaname,
    tablename,
    heap_blks_read,
    heap_blks_hit,
    CASE 
        WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
        ELSE ROUND(100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read), 2)
    END as cache_hit_ratio,
    CASE 
        WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 'no_activity'
        WHEN (heap_blks_hit + heap_blks_read) > 0 AND heap_blks_hit / (heap_blks_hit + heap_blks_read) < 0.8 THEN 'poor'
        WHEN (heap_blks_hit + heap_blks_read) > 0 AND heap_blks_hit / (heap_blks_hit + heap_blks_read) < 0.95 THEN 'good'
        ELSE 'excellent'
    END as performance_rating
FROM pg_statio_user_tables
ORDER BY cache_hit_ratio ASC;

-- ============================================================================
-- 9. PERFORMANCE BASELINE TABLE
-- ============================================================================

-- Create performance baseline table for tracking improvements
CREATE TABLE IF NOT EXISTS performance_baseline (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(50),
    description TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial baseline metrics
INSERT INTO performance_baseline (metric_name, metric_value, metric_unit, description) VALUES
('total_index_scans', (SELECT COALESCE(SUM(idx_scan), 0) FROM pg_stat_user_indexes), 'count', 'Total index scans across all indexes'),
('total_seq_scans', (SELECT COALESCE(SUM(seq_scan), 0) FROM pg_stat_user_tables), 'count', 'Total sequential scans across all tables'),
('avg_cache_hit_ratio', 
    (SELECT COALESCE(AVG(CASE 
        WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
        ELSE 100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read)
    END), 0) FROM pg_statio_user_tables), 
    'percentage', 'Average cache hit ratio across all tables'),
('unused_indexes', (SELECT COUNT(*) FROM pg_stat_user_indexes WHERE idx_scan = 0), 'count', 'Number of unused indexes'),
('high_seq_scan_tables', (SELECT COUNT(*) FROM pg_stat_user_tables WHERE seq_scan > idx_scan), 'count', 'Number of tables with high sequential scan ratio');

-- ============================================================================
-- 10. AUTOMATED MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to identify unused indexes
CREATE OR REPLACE FUNCTION get_unused_indexes()
RETURNS TABLE (
    schemaname TEXT,
    tablename TEXT,
    indexname TEXT,
    index_size TEXT,
    index_scans BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.schemaname,
        i.tablename,
        i.indexname,
        pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size,
        i.idx_scan as index_scans
    FROM pg_stat_user_indexes i
    WHERE i.idx_scan = 0
    ORDER BY pg_relation_size(i.indexrelid) DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to identify tables needing vacuum
CREATE OR REPLACE FUNCTION get_tables_needing_vacuum()
RETURNS TABLE (
    schemaname TEXT,
    tablename TEXT,
    live_tuples BIGINT,
    dead_tuples BIGINT,
    dead_ratio NUMERIC,
    last_vacuum TIMESTAMP,
    last_autovacuum TIMESTAMP,
    vacuum_status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.schemaname,
        t.tablename,
        t.n_live_tup as live_tuples,
        t.n_dead_tup as dead_tuples,
        CASE 
            WHEN t.n_live_tup = 0 THEN 0
            ELSE ROUND(100.0 * t.n_dead_tup / t.n_live_tup, 2)
        END as dead_ratio,
        t.last_vacuum,
        t.last_autovacuum,
        CASE 
            WHEN t.n_dead_tup > t.n_live_tup * 0.1 THEN 'NEEDS_VACUUM'
            WHEN t.n_dead_tup > 1000 THEN 'CONSIDER_VACUUM'
            ELSE 'OK'
        END as vacuum_status
    FROM pg_stat_user_tables t
    ORDER BY t.n_dead_tup DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get cache performance summary
CREATE OR REPLACE FUNCTION get_cache_performance_summary()
RETURNS TABLE (
    total_tables INTEGER,
    excellent_cache INTEGER,
    good_cache INTEGER,
    poor_cache INTEGER,
    no_activity INTEGER,
    avg_cache_hit_ratio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_tables,
        COUNT(*) FILTER (WHERE 
            (heap_blks_hit + heap_blks_read) > 0 AND 
            heap_blks_hit / (heap_blks_hit + heap_blks_read) >= 0.95
        ) as excellent_cache,
        COUNT(*) FILTER (WHERE 
            (heap_blks_hit + heap_blks_read) > 0 AND 
            heap_blks_hit / (heap_blks_hit + heap_blks_read) >= 0.8 AND
            heap_blks_hit / (heap_blks_hit + heap_blks_read) < 0.95
        ) as good_cache,
        COUNT(*) FILTER (WHERE 
            (heap_blks_hit + heap_blks_read) > 0 AND 
            heap_blks_hit / (heap_blks_hit + heap_blks_read) < 0.8
        ) as poor_cache,
        COUNT(*) FILTER (WHERE (heap_blks_hit + heap_blks_read) = 0) as no_activity,
        ROUND(AVG(CASE 
            WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
            ELSE 100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read)
        END), 2) as avg_cache_hit_ratio
    FROM pg_statio_user_tables;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 11. PERFORMANCE ALERTS
-- ============================================================================

-- Create performance alerts table
CREATE TABLE IF NOT EXISTS performance_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metric_value NUMERIC,
    threshold_value NUMERIC,
    table_name VARCHAR(100),
    index_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100)
);

-- Function to check for performance issues and create alerts
CREATE OR REPLACE FUNCTION check_performance_alerts()
RETURNS INTEGER AS $$
DECLARE
    alert_count INTEGER := 0;
    cache_threshold NUMERIC := 80.0;
    seq_scan_threshold INTEGER := 100;
BEGIN
    -- Check for low cache hit ratios
    INSERT INTO performance_alerts (alert_type, severity, message, metric_value, threshold_value, table_name)
    SELECT 
        'LOW_CACHE_HIT_RATIO',
        CASE 
            WHEN cache_ratio < 50 THEN 'CRITICAL'
            WHEN cache_ratio < 70 THEN 'HIGH'
            ELSE 'MEDIUM'
        END,
        'Table ' || tablename || ' has low cache hit ratio: ' || cache_ratio || '%',
        cache_ratio,
        cache_threshold,
        tablename
    FROM (
        SELECT 
            tablename,
            CASE 
                WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
                ELSE ROUND(100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read), 2)
            END as cache_ratio
        FROM pg_statio_user_tables
        WHERE (heap_blks_hit + heap_blks_read) > 0
    ) cache_stats
    WHERE cache_ratio < cache_threshold
    AND NOT EXISTS (
        SELECT 1 FROM performance_alerts 
        WHERE alert_type = 'LOW_CACHE_HIT_RATIO' 
        AND table_name = cache_stats.tablename 
        AND resolved_at IS NULL
    );
    
    GET DIAGNOSTICS alert_count = ROW_COUNT;
    
    -- Check for high sequential scans
    INSERT INTO performance_alerts (alert_type, severity, message, metric_value, threshold_value, table_name)
    SELECT 
        'HIGH_SEQUENTIAL_SCANS',
        CASE 
            WHEN seq_scan > 1000 THEN 'CRITICAL'
            WHEN seq_scan > 500 THEN 'HIGH'
            ELSE 'MEDIUM'
        END,
        'Table ' || tablename || ' has high sequential scan count: ' || seq_scan,
        seq_scan,
        seq_scan_threshold,
        tablename
    FROM pg_stat_user_tables
    WHERE seq_scan > seq_scan_threshold
    AND NOT EXISTS (
        SELECT 1 FROM performance_alerts 
        WHERE alert_type = 'HIGH_SEQUENTIAL_SCANS' 
        AND table_name = pg_stat_user_tables.tablename 
        AND resolved_at IS NULL
    );
    
    GET DIAGNOSTICS alert_count = alert_count + ROW_COUNT;
    
    RETURN alert_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 12. MIGRATION COMPLETION
-- ============================================================================

-- Log the completion of this migration
INSERT INTO performance_baseline (metric_name, metric_value, metric_unit, description) VALUES
('migration_012_completed', 1, 'boolean', 'Database performance optimization migration completed');

-- Update the migration log
-- (This assumes you have a migration tracking table)
-- INSERT INTO schema_migrations (version, applied_at) VALUES ('012_database_performance_optimization', NOW());

COMMENT ON MIGRATION '012_database_performance_optimization' IS 'Database performance optimization with comprehensive indexing strategy, monitoring views, and automated maintenance functions'; 