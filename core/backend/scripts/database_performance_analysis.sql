-- Database Performance Analysis Script for Arxos
-- This script analyzes database performance and provides optimization recommendations

-- ============================================================================
-- 1. DATABASE OVERVIEW AND STATISTICS
-- ============================================================================

-- Get database size and table information
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Table sizes and row counts
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
    (SELECT reltuples FROM pg_class WHERE relname = tablename) as row_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- 2. INDEX USAGE ANALYSIS
-- ============================================================================

-- Index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 10 THEN 'RARELY_USED'
        WHEN idx_scan < 100 THEN 'OCCASIONALLY_USED'
        ELSE 'FREQUENTLY_USED'
    END as usage_category
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Unused indexes (potential candidates for removal)
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_relation_size(indexrelid) as size_bytes
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- 3. SLOW QUERY ANALYSIS
-- ============================================================================

-- Analyze common query patterns (if pg_stat_statements is enabled)
-- Note: This requires pg_stat_statements extension to be installed
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    shared_blks_hit,
    shared_blks_read,
    shared_blks_written,
    shared_blks_dirtied,
    temp_blks_read,
    temp_blks_written,
    blk_read_time,
    blk_write_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- ============================================================================
-- 4. SPECIFIC QUERY PERFORMANCE ANALYSIS
-- ============================================================================

-- Analyze building queries (as mentioned in the task)
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM buildings WHERE owner_id = 1;

-- Analyze asset queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM building_assets WHERE building_id = 1;

-- Analyze spatial queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM walls WHERE building_id = 1 AND ST_Intersects(geom, ST_MakeEnvelope(0, 0, 100, 100, 4326));

-- Analyze complex joins
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT
    b.name as building_name,
    f.name as floor_name,
    COUNT(w.id) as wall_count,
    COUNT(r.id) as room_count,
    COUNT(d.id) as device_count
FROM buildings b
LEFT JOIN floors f ON b.id = f.building_id
LEFT JOIN walls w ON f.id = w.floor_id
LEFT JOIN rooms r ON f.id = r.floor_id
LEFT JOIN devices d ON f.id = d.floor_id
WHERE b.owner_id = 1
GROUP BY b.id, b.name, f.id, f.name;

-- ============================================================================
-- 5. TABLE SCAN ANALYSIS
-- ============================================================================

-- Tables with high sequential scans
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    CASE
        WHEN seq_scan > idx_scan THEN 'HIGH_SEQ_SCANS'
        WHEN seq_scan > 0 THEN 'SOME_SEQ_SCANS'
        ELSE 'INDEX_SCANS_ONLY'
    END as scan_pattern
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;

-- ============================================================================
-- 6. CACHE HIT RATIO ANALYSIS
-- ============================================================================

-- Buffer cache hit ratios
SELECT
    schemaname,
    tablename,
    heap_blks_read,
    heap_blks_hit,
    CASE
        WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
        ELSE ROUND(100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read), 2)
    END as cache_hit_ratio
FROM pg_statio_user_tables
ORDER BY cache_hit_ratio ASC;

-- ============================================================================
-- 7. LOCK ANALYSIS
-- ============================================================================

-- Current locks
SELECT
    l.pid,
    l.mode,
    l.granted,
    t.relname as table_name,
    a.usename as username,
    a.application_name,
    a.client_addr,
    a.state,
    a.query_start,
    a.query
FROM pg_locks l
JOIN pg_class t ON l.relation = t.oid
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE t.relkind = 'r'
ORDER BY l.pid;

-- ============================================================================
-- 8. VACUUM AND MAINTENANCE ANALYSIS
-- ============================================================================

-- Tables needing vacuum
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    last_vacuum,
    last_autovacuum,
    CASE
        WHEN n_dead_tup > n_live_tup * 0.1 THEN 'NEEDS_VACUUM'
        WHEN n_dead_tup > 1000 THEN 'CONSIDER_VACUUM'
        ELSE 'OK'
    END as vacuum_status
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- ============================================================================
-- 9. SPATIAL INDEX ANALYSIS (PostGIS)
-- ============================================================================

-- Spatial index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexname LIKE '%geom%' OR indexname LIKE '%spatial%'
ORDER BY idx_scan DESC;

-- ============================================================================
-- 10. PERFORMANCE RECOMMENDATIONS
-- ============================================================================

-- Missing indexes analysis
-- This section provides recommendations based on the analysis above

-- Example: Check for missing indexes on frequently queried columns
-- (This would be populated based on the analysis results)

-- ============================================================================
-- 11. QUERY OPTIMIZATION SUGGESTIONS
-- ============================================================================

-- Common optimization patterns for Arxos queries

-- 1. Building queries optimization
-- Current: SELECT * FROM buildings WHERE owner_id = ?
-- Recommendation: Ensure index on owner_id exists
-- CREATE INDEX IF NOT EXISTS idx_buildings_owner_id ON buildings(owner_id);

-- 2. Asset queries optimization
-- Current: SELECT * FROM building_assets WHERE building_id = ? AND system = ?
-- Recommendation: Composite index for common filter combinations
-- CREATE INDEX IF NOT EXISTS idx_building_assets_building_system ON building_assets(building_id, system);

-- 3. Spatial queries optimization
-- Current: SELECT * FROM walls WHERE building_id = ? AND ST_Intersects(geom, ?)
-- Recommendation: Ensure spatial index exists and is being used
-- CREATE INDEX IF NOT EXISTS idx_walls_building_geom ON walls USING GIST (building_id, geom);

-- 4. Complex join optimization
-- Current: Multiple joins on building_id, floor_id
-- Recommendation: Ensure proper indexes on foreign keys
-- CREATE INDEX IF NOT EXISTS idx_floors_building_id ON floors(building_id);
-- CREATE INDEX IF NOT EXISTS idx_walls_floor_id ON walls(floor_id);

-- ============================================================================
-- 12. MONITORING QUERIES
-- ============================================================================

-- Create a view for ongoing monitoring
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

-- ============================================================================
-- 13. AUTOMATED OPTIMIZATION SCRIPT
-- ============================================================================

-- This section contains SQL statements that can be run to optimize performance

-- 1. Create missing indexes for common queries
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_owner_id ON buildings(owner_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_building_system ON building_assets(building_id, system);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_status_created ON building_assets(status, created_at);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_history_asset_date ON asset_history(asset_id, event_date);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at);

-- 2. Create composite indexes for complex queries
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_walls_building_floor_status ON walls(building_id, floor_id, status);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_building_system_type ON devices(building_id, system, type);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_building_floor_category ON rooms(building_id, floor_id, category);

-- 3. Create partial indexes for filtered queries
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_active ON building_assets(building_id, system) WHERE status = 'active';
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_recent ON audit_logs(user_id, created_at) WHERE created_at > NOW() - INTERVAL '30 days';

-- 4. Create covering indexes for frequently accessed columns
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_covering ON buildings(owner_id) INCLUDE (name, address, created_at);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_covering ON building_assets(building_id, system) INCLUDE (asset_type, status, created_at);

-- ============================================================================
-- 14. PERFORMANCE BASELINE
-- ============================================================================

-- Store current performance metrics for comparison
CREATE TABLE IF NOT EXISTS performance_baseline (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value NUMERIC,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert baseline metrics
INSERT INTO performance_baseline (metric_name, metric_value)
SELECT 'total_index_scans', SUM(idx_scan) FROM pg_stat_user_indexes;

INSERT INTO performance_baseline (metric_name, metric_value)
SELECT 'total_seq_scans', SUM(seq_scan) FROM pg_stat_user_tables;

INSERT INTO performance_baseline (metric_name, metric_value)
SELECT 'avg_cache_hit_ratio',
    AVG(CASE
        WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
        ELSE 100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read)
    END)
FROM pg_statio_user_tables;

-- ============================================================================
-- 15. SUMMARY REPORT
-- ============================================================================

-- Generate a summary report
SELECT
    'PERFORMANCE SUMMARY' as report_section,
    'Total Tables: ' || COUNT(*) as metric,
    '' as value
FROM pg_tables
WHERE schemaname = 'public'
UNION ALL
SELECT
    'PERFORMANCE SUMMARY',
    'Total Indexes: ' || COUNT(*),
    ''
FROM pg_stat_user_indexes
UNION ALL
SELECT
    'PERFORMANCE SUMMARY',
    'Unused Indexes: ' || COUNT(*),
    ''
FROM pg_stat_user_indexes
WHERE idx_scan = 0
UNION ALL
SELECT
    'PERFORMANCE SUMMARY',
    'Tables with High Seq Scans: ' || COUNT(*),
    ''
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan
UNION ALL
SELECT
    'PERFORMANCE SUMMARY',
    'Average Cache Hit Ratio: ' || ROUND(AVG(CASE
        WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
        ELSE 100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read)
    END), 2) || '%',
    ''
FROM pg_statio_user_tables;
