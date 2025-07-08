-- Migration: Add Performance Indexes
-- Date: 2024-01-XX
-- Description: Add performance indexes for common query patterns to improve database performance

-- ============================================================================
-- BUILDING QUERIES
-- ============================================================================

-- Building queries optimization
-- Note: Using owner_id instead of organization_id based on current schema
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_owner_id ON buildings(owner_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_created_at ON buildings(created_at);

-- ============================================================================
-- ASSET QUERIES (building_assets table)
-- ============================================================================

-- Asset queries optimization
-- Note: Using building_assets table name based on current schema
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_building_floor ON building_assets(building_id, floor_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_type_status ON building_assets(asset_type, status);

-- Additional asset indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_system_status ON building_assets(system, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_created_by ON building_assets(created_by);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_created_at ON building_assets(created_at);

-- ============================================================================
-- VERSION CONTROL QUERIES
-- ============================================================================

-- Version control queries optimization
-- Note: These indexes are for the version control system tables
-- The main schema doesn't have a versions table, but version control system does

-- For drawing_versions table (if it exists in the main database)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_drawing_versions_floor_id ON drawing_versions(floor_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_drawing_versions_created_at ON drawing_versions(created_at);

-- For version_sessions table (if it exists in the main database)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_version_sessions_user_floor ON version_sessions(user_id, floor_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_version_sessions_created_at ON version_sessions(created_at);

-- For version_branches table (if it exists in the main database)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_version_branches_floor_id ON version_branches(floor_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_version_branches_created_at ON version_branches(created_at);

-- ============================================================================
-- AUDIT LOG QUERIES
-- ============================================================================

-- Audit log queries optimization
-- Note: Using created_at instead of timestamp based on current schema
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_action_object_type ON audit_logs(action, object_type);

-- Additional audit log indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_object_type_id ON audit_logs(object_type, object_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_at_desc ON audit_logs(created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_building_id ON audit_logs(building_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_floor_id ON audit_logs(floor_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_asset_id ON audit_logs(asset_id);

-- ============================================================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- ============================================================================

-- Building and floor context queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_building_floor_status ON building_assets(building_id, floor_id, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_building_system_type ON building_assets(building_id, system, asset_type);

-- User activity queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action_created ON audit_logs(user_id, action, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_building_user_created ON audit_logs(building_id, user_id, created_at);

-- ============================================================================
-- PARTIAL INDEXES FOR FILTERED QUERIES
-- ============================================================================

-- Active assets only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_active ON building_assets(building_id, floor_id) WHERE status = 'active';

-- Recent audit logs (last 30 days)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_recent ON audit_logs(user_id, created_at) WHERE created_at > NOW() - INTERVAL '30 days';

-- Non-archived audit logs
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_non_archived ON audit_logs(user_id, created_at) WHERE archived = false;

-- ============================================================================
-- COVERING INDEXES FOR FREQUENTLY ACCESSED COLUMNS
-- ============================================================================

-- Building covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_covering ON buildings(owner_id) INCLUDE (name, address, created_at);

-- Asset covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_covering ON building_assets(building_id, floor_id) INCLUDE (asset_type, system, status, created_at);

-- Audit log covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_covering ON audit_logs(user_id, created_at) INCLUDE (action, object_type, object_id);

-- ============================================================================
-- FUNCTIONAL INDEXES FOR COMPLEX QUERIES
-- ============================================================================

-- Case-insensitive search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_name_lower ON buildings(LOWER(name));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_asset_type_lower ON building_assets(LOWER(asset_type));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_system_lower ON building_assets(LOWER(system));

-- Date-based indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_buildings_created_date ON buildings(DATE(created_at));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_building_assets_created_date ON building_assets(DATE(created_at));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_date ON audit_logs(DATE(created_at));

-- ============================================================================
-- SPATIAL INDEXES (if using PostGIS)
-- ============================================================================

-- Ensure spatial indexes exist for BIM objects (these should already exist)
-- These are commented out as they should already be created in the original schema
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_walls_geom ON walls USING GIST (geom);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_geom ON rooms USING GIST (geom);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_doors_geom ON doors USING GIST (geom);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_windows_geom ON windows USING GIST (geom);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_geom ON devices USING GIST (geom);

-- ============================================================================
-- STATISTICS UPDATE
-- ============================================================================

-- Update table statistics for better query planning
ANALYZE buildings;
ANALYZE building_assets;
ANALYZE audit_logs;

-- Update statistics for version control tables if they exist
-- ANALYZE drawing_versions;
-- ANALYZE version_sessions;
-- ANALYZE version_branches;

-- ============================================================================
-- INDEX USAGE MONITORING
-- ============================================================================

-- Create a view to monitor index usage for these new indexes
CREATE OR REPLACE VIEW performance_indexes_monitoring AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 10 THEN 'RARELY_USED'
        WHEN idx_scan < 100 THEN 'OCCASIONALLY_USED'
        ELSE 'FREQUENTLY_USED'
    END as usage_category
FROM pg_stat_user_indexes
WHERE indexname LIKE 'idx_%'
ORDER BY idx_scan DESC;

-- ============================================================================
-- MIGRATION COMPLETION
-- ============================================================================

-- Log the completion of this migration
INSERT INTO performance_baseline (metric_name, metric_value, metric_unit, description) VALUES
('migration_019_completed', 1, 'boolean', 'Performance indexes migration completed');

-- Add comments for documentation
COMMENT ON INDEX idx_buildings_owner_id IS 'Index for filtering buildings by owner';
COMMENT ON INDEX idx_buildings_created_at IS 'Index for sorting buildings by creation date';
COMMENT ON INDEX idx_building_assets_building_floor IS 'Composite index for filtering assets by building and floor';
COMMENT ON INDEX idx_building_assets_type_status IS 'Composite index for filtering assets by type and status';
COMMENT ON INDEX idx_audit_logs_user_created IS 'Composite index for filtering audit logs by user and creation date';
COMMENT ON INDEX idx_audit_logs_action_object_type IS 'Composite index for filtering audit logs by action and object type';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- These queries can be run to verify the indexes were created successfully
-- SELECT indexname, tablename FROM pg_indexes WHERE indexname LIKE 'idx_%' ORDER BY tablename, indexname;
-- SELECT * FROM performance_indexes_monitoring WHERE usage_category = 'UNUSED'; 