-- =============================================================================
-- Performance Indexes Validation Script
-- =============================================================================
-- This script validates the performance indexes added to the database schema
-- Run with: psql -d your_database -f validate_performance_indexes.sql

-- =============================================================================
-- 1. INDEX VALIDATION QUERIES
-- =============================================================================

-- Check if all indexes exist
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- =============================================================================
-- 2. PERFORMANCE TESTING QUERIES
-- =============================================================================

-- Test 1: Building queries with owner filtering
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM buildings WHERE owner_id = 1;

-- Test 2: Room queries with building and floor filtering
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM rooms WHERE building_id = 1 AND floor_id = 1 AND status = 'active';

-- Test 3: Wall queries with material filtering
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM walls WHERE building_id = 1 AND material = 'concrete';

-- Test 4: Device queries with system and type filtering
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM devices WHERE building_id = 1 AND system = 'HVAC' AND type = 'vent';

-- Test 5: User assignment queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM walls WHERE assigned_to = 1 AND status = 'active';

-- Test 6: Project-based queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM rooms WHERE project_id = 1 AND status = 'active';

-- Test 7: Audit log queries with user and time filtering
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM audit_logs WHERE user_id = 1 AND created_at > NOW() - INTERVAL '30 days';

-- Test 8: Object history queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM object_history WHERE object_id = 'room_123' AND changed_at > NOW() - INTERVAL '7 days';

-- Test 9: Catalog item queries
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM catalog_items WHERE make = 'Siemens' AND model = 'VAV-100' AND type = 'vent';

-- Test 10: Spatial queries with building context
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM walls 
WHERE building_id = 1 
AND ST_Intersects(geom, ST_MakeEnvelope(0, 0, 100, 100, 4326));

-- =============================================================================
-- 3. COMPOSITE INDEX VALIDATION
-- =============================================================================

-- Test composite indexes for complex filtering
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM rooms 
WHERE building_id = 1 
AND floor_id = 1 
AND status = 'active' 
AND category = 'office';

-- Test covering indexes
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT name, address, created_at 
FROM buildings 
WHERE owner_id = 1;

-- Test partial indexes
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
SELECT * FROM rooms 
WHERE building_id = 1 
AND floor_id = 1 
AND status = 'active';

-- =============================================================================
-- 4. INDEX USAGE STATISTICS
-- =============================================================================

-- View index usage statistics
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
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- =============================================================================
-- 5. INDEX SIZE ANALYSIS
-- =============================================================================

-- View index sizes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_relation_size(indexrelid) as size_bytes
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- =============================================================================
-- 6. PERFORMANCE COMPARISON QUERIES
-- =============================================================================

-- Compare performance with and without indexes
-- (These queries should show significant performance differences)

-- Query 1: Building filtering (should use idx_buildings_owner_id)
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM buildings WHERE owner_id = 1;

-- Query 2: Room filtering (should use idx_rooms_building_floor_status)
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM rooms WHERE building_id = 1 AND floor_id = 1 AND status = 'active';

-- Query 3: Device filtering (should use idx_devices_building_system_type)
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM devices WHERE building_id = 1 AND system = 'HVAC' AND type = 'vent';

-- Query 4: Audit log filtering (should use idx_audit_logs_recent)
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM audit_logs WHERE user_id = 1 AND created_at > NOW() - INTERVAL '30 days';

-- =============================================================================
-- 7. INDEX MAINTENANCE QUERIES
-- =============================================================================

-- Update table statistics for better query planning
ANALYZE buildings;
ANALYZE rooms;
ANALYZE walls;
ANALYZE doors;
ANALYZE windows;
ANALYZE devices;
ANALYZE labels;
ANALYZE zones;
ANALYZE audit_logs;
ANALYZE object_history;
ANALYZE catalog_items;

-- =============================================================================
-- 8. EXPECTED RESULTS SUMMARY
-- =============================================================================

/*
EXPECTED PERFORMANCE IMPROVEMENTS:

1. Building Queries:
   - Before: Sequential scan on buildings table
   - After: Index scan using idx_buildings_owner_id
   - Expected Improvement: 80-90% faster

2. Room Queries:
   - Before: Sequential scan on rooms table
   - After: Index scan using idx_rooms_building_floor_status
   - Expected Improvement: 70-85% faster

3. Device Queries:
   - Before: Sequential scan on devices table
   - After: Index scan using idx_devices_building_system_type
   - Expected Improvement: 75-90% faster

4. Audit Log Queries:
   - Before: Sequential scan on audit_logs table
   - After: Index scan using idx_audit_logs_recent
   - Expected Improvement: 70-85% faster

5. Spatial Queries:
   - Before: Sequential scan with spatial filtering
   - After: GIST index scan with building context
   - Expected Improvement: 60-80% faster

VALIDATION CRITERIA:
- All EXPLAIN ANALYZE queries should show "Index Scan" instead of "Seq Scan"
- Query execution time should be significantly reduced
- Buffer usage should be optimized
- Index usage statistics should show frequent usage of new indexes
*/

-- =============================================================================
-- END OF VALIDATION SCRIPT
-- ============================================================================= 