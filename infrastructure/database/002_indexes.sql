-- 002_indexes.sql
-- Performance optimization indexes for Arxos Platform

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- USER AND AUTHENTICATION INDEXES
-- ============================================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);
CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users (updated_at);

-- ============================================================================
-- PROJECT AND ORGANIZATION INDEXES
-- ============================================================================

-- Projects table indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects (user_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects (created_at);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects (updated_at);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects USING gin(to_tsvector('english', name));

-- ============================================================================
-- BUILDING AND FLOOR INDEXES
-- ============================================================================

-- Buildings table indexes
CREATE INDEX IF NOT EXISTS idx_buildings_owner_id ON buildings (owner_id);
CREATE INDEX IF NOT EXISTS idx_buildings_project_id ON buildings (project_id);
CREATE INDEX IF NOT EXISTS idx_buildings_created_at ON buildings (created_at);
CREATE INDEX IF NOT EXISTS idx_buildings_updated_at ON buildings (updated_at);
CREATE INDEX IF NOT EXISTS idx_buildings_name ON buildings USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_buildings_address ON buildings USING gin(to_tsvector('english', address));

-- Floors table indexes
CREATE INDEX IF NOT EXISTS idx_floors_building_id ON floors (building_id);
CREATE INDEX IF NOT EXISTS idx_floors_created_at ON floors (created_at);
CREATE INDEX IF NOT EXISTS idx_floors_updated_at ON floors (updated_at);
CREATE INDEX IF NOT EXISTS idx_floors_name ON floors USING gin(to_tsvector('english', name));

-- ============================================================================
-- DRAWINGS INDEXES
-- ============================================================================

-- Drawings table indexes
CREATE INDEX IF NOT EXISTS idx_drawings_project_id ON drawings (project_id);
CREATE INDEX IF NOT EXISTS idx_drawings_created_at ON drawings (created_at);
CREATE INDEX IF NOT EXISTS idx_drawings_updated_at ON drawings (updated_at);
CREATE INDEX IF NOT EXISTS idx_drawings_name ON drawings USING gin(to_tsvector('english', name));

-- ============================================================================
-- BIM OBJECTS - COMPOUND INDEXES FOR PERFORMANCE
-- ============================================================================

-- Walls table compound indexes
CREATE INDEX IF NOT EXISTS idx_walls_building_floor ON walls (building_id, floor_id);
CREATE INDEX IF NOT EXISTS idx_walls_project_status ON walls (project_id, status);
CREATE INDEX IF NOT EXISTS idx_walls_assigned_status ON walls (assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_walls_created_status ON walls (created_by, status);
CREATE INDEX IF NOT EXISTS idx_walls_category_status ON walls (category, status);
CREATE INDEX IF NOT EXISTS idx_walls_room_status ON walls (room_id, status);
CREATE INDEX IF NOT EXISTS idx_walls_geom_category ON walls USING gist (geom) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_walls_project_geom ON walls USING gist (geom) WHERE project_id IS NOT NULL;

-- Rooms table compound indexes
CREATE INDEX IF NOT EXISTS idx_rooms_building_floor ON rooms (building_id, floor_id);
CREATE INDEX IF NOT EXISTS idx_rooms_project_status ON rooms (project_id, status);
CREATE INDEX IF NOT EXISTS idx_rooms_assigned_status ON rooms (assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_rooms_created_status ON rooms (created_by, status);
CREATE INDEX IF NOT EXISTS idx_rooms_category_status ON rooms (category, status);
CREATE INDEX IF NOT EXISTS idx_rooms_geom_category ON rooms USING gist (geom) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rooms_project_geom ON rooms USING gist (geom) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rooms_name_search ON rooms USING gin(to_tsvector('english', name));

-- Doors table compound indexes
CREATE INDEX IF NOT EXISTS idx_doors_building_floor ON doors (building_id, floor_id);
CREATE INDEX IF NOT EXISTS idx_doors_project_status ON doors (project_id, status);
CREATE INDEX IF NOT EXISTS idx_doors_assigned_status ON doors (assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_doors_created_status ON doors (created_by, status);
CREATE INDEX IF NOT EXISTS idx_doors_category_status ON doors (category, status);
CREATE INDEX IF NOT EXISTS idx_doors_room_status ON doors (room_id, status);
CREATE INDEX IF NOT EXISTS idx_doors_geom_category ON doors USING gist (geom) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doors_project_geom ON doors USING gist (geom) WHERE project_id IS NOT NULL;

-- Windows table compound indexes
CREATE INDEX IF NOT EXISTS idx_windows_building_floor ON windows (building_id, floor_id);
CREATE INDEX IF NOT EXISTS idx_windows_project_status ON windows (project_id, status);
CREATE INDEX IF NOT EXISTS idx_windows_assigned_status ON windows (assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_windows_created_status ON windows (created_by, status);
CREATE INDEX IF NOT EXISTS idx_windows_category_status ON windows (category, status);
CREATE INDEX IF NOT EXISTS idx_windows_room_status ON windows (room_id, status);
CREATE INDEX IF NOT EXISTS idx_windows_geom_category ON windows USING gist (geom) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_windows_project_geom ON windows USING gist (geom) WHERE project_id IS NOT NULL;

-- Devices table compound indexes
CREATE INDEX IF NOT EXISTS idx_devices_building_floor ON devices (building_id, floor_id);
CREATE INDEX IF NOT EXISTS idx_devices_project_status ON devices (project_id, status);
CREATE INDEX IF NOT EXISTS idx_devices_assigned_status ON devices (assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_devices_created_status ON devices (created_by, status);
CREATE INDEX IF NOT EXISTS idx_devices_category_status ON devices (category, status);
CREATE INDEX IF NOT EXISTS idx_devices_room_status ON devices (room_id, status);
CREATE INDEX IF NOT EXISTS idx_devices_type_system ON devices (type, system);
CREATE INDEX IF NOT EXISTS idx_devices_geom_category ON devices USING gist (geom) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_devices_project_geom ON devices USING gist (geom) WHERE project_id IS NOT NULL;

-- Labels table compound indexes
CREATE INDEX IF NOT EXISTS idx_labels_building_floor ON labels (building_id, floor_id);
CREATE INDEX IF NOT EXISTS idx_labels_project_status ON labels (project_id, status);
CREATE INDEX IF NOT EXISTS idx_labels_assigned_status ON labels (assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_labels_created_status ON labels (created_by, status);
CREATE INDEX IF NOT EXISTS idx_labels_category_status ON labels (category, status);
CREATE INDEX IF NOT EXISTS idx_labels_room_status ON labels (room_id, status);
CREATE INDEX IF NOT EXISTS idx_labels_geom_category ON labels USING gist (geom) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_labels_project_geom ON labels USING gist (geom) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_labels_text_search ON labels USING gin(to_tsvector('english', text));

-- Zones table compound indexes
CREATE INDEX IF NOT EXISTS idx_zones_building_floor ON zones (building_id, floor_id);
CREATE INDEX IF NOT EXISTS idx_zones_project_status ON zones (project_id, status);
CREATE INDEX IF NOT EXISTS idx_zones_assigned_status ON zones (assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_zones_created_status ON zones (created_by, status);
CREATE INDEX IF NOT EXISTS idx_zones_category_status ON zones (category, status);
CREATE INDEX IF NOT EXISTS idx_zones_geom_category ON zones USING gist (geom) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_zones_project_geom ON zones USING gist (geom) WHERE project_id IS NOT NULL;

-- ============================================================================
-- COLLABORATION AND WORKFLOW INDEXES
-- ============================================================================

-- Comments table indexes
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments (user_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments (created_at);
CREATE INDEX IF NOT EXISTS idx_comments_object_type_id ON comments (object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_comments_project_id ON comments (project_id);

-- Assignments table indexes
CREATE INDEX IF NOT EXISTS idx_assignments_user_id ON assignments (user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_assigned_to ON assignments (assigned_to);
CREATE INDEX IF NOT EXISTS idx_assignments_object_type_id ON assignments (object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments (status);
CREATE INDEX IF NOT EXISTS idx_assignments_created_at ON assignments (created_at);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments (due_date);

-- Object history table indexes
CREATE INDEX IF NOT EXISTS idx_object_history_object_type_id ON object_history (object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_object_history_user_id ON object_history (user_id);
CREATE INDEX IF NOT EXISTS idx_object_history_action ON object_history (action);
CREATE INDEX IF NOT EXISTS idx_object_history_created_at ON object_history (created_at);
CREATE INDEX IF NOT EXISTS idx_object_history_project_id ON object_history (project_id);

-- ============================================================================
-- CATEGORIES AND PERMISSIONS INDEXES
-- ============================================================================

-- Categories table indexes
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories (parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_project_id ON categories (project_id);

-- User category permissions table indexes
CREATE INDEX IF NOT EXISTS idx_user_category_permissions_user_id ON user_category_permissions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_category_permissions_category_id ON user_category_permissions (category_id);
CREATE INDEX IF NOT EXISTS idx_user_category_permissions_permission ON user_category_permissions (permission);
CREATE INDEX IF NOT EXISTS idx_user_category_permissions_user_category ON user_category_permissions (user_id, category_id);

-- ============================================================================
-- AUDIT AND MONITORING INDEXES
-- ============================================================================

-- Audit logs table indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_object_type_id ON audit_logs (object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_project_id ON audit_logs (project_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address ON audit_logs (ip_address);

-- Chat messages table indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_room_id ON chat_messages (room_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages (created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_project_id ON chat_messages (project_id);

-- ============================================================================
-- CATALOG AND SYMBOL INDEXES
-- ============================================================================

-- Catalog items table indexes
CREATE INDEX IF NOT EXISTS idx_catalog_items_category ON catalog_items (category);
CREATE INDEX IF NOT EXISTS idx_catalog_items_type ON catalog_items (type);
CREATE INDEX IF NOT EXISTS idx_catalog_items_created_at ON catalog_items (created_at);
CREATE INDEX IF NOT EXISTS idx_catalog_items_name ON catalog_items USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_catalog_items_category_type ON catalog_items (category, type);

-- ============================================================================
-- PERFORMANCE MONITORING INDEXES
-- ============================================================================

-- Export monitoring indexes (if table exists)
-- CREATE INDEX IF NOT EXISTS idx_export_metrics_format ON export_metrics (format);
-- CREATE INDEX IF NOT EXISTS idx_export_metrics_status ON export_metrics (status);
-- CREATE INDEX IF NOT EXISTS idx_export_metrics_user_id ON export_metrics (user_id);
-- CREATE INDEX IF NOT EXISTS idx_export_metrics_project_id ON export_metrics (project_id);
-- CREATE INDEX IF NOT EXISTS idx_export_metrics_created_at ON export_metrics (created_at);
-- CREATE INDEX IF NOT EXISTS idx_export_metrics_format_status ON export_metrics (format, status);

-- Sync monitoring indexes (if table exists)
-- CREATE INDEX IF NOT EXISTS idx_sync_metrics_sync_type ON sync_metrics (sync_type);
-- CREATE INDEX IF NOT EXISTS idx_sync_metrics_status ON sync_metrics (status);
-- CREATE INDEX IF NOT EXISTS idx_sync_metrics_connection_id ON sync_metrics (connection_id);
-- CREATE INDEX IF NOT EXISTS idx_sync_metrics_created_at ON sync_metrics (created_at);

-- ============================================================================
-- CACHE AND BACKGROUND JOB INDEXES
-- ============================================================================

-- Cache entries table indexes (if table exists)
-- CREATE INDEX IF NOT EXISTS idx_cache_entries_key ON cache_entries (cache_key);
-- CREATE INDEX IF NOT EXISTS idx_cache_entries_format ON cache_entries (format);
-- CREATE INDEX IF NOT EXISTS idx_cache_entries_model_hash ON cache_entries (model_hash);
-- CREATE INDEX IF NOT EXISTS idx_cache_entries_expires_at ON cache_entries (expires_at);
-- CREATE INDEX IF NOT EXISTS idx_cache_entries_created_at ON cache_entries (created_at);

-- Background jobs table indexes (if table exists)
-- CREATE INDEX IF NOT EXISTS idx_background_jobs_job_id ON background_jobs (job_id);
-- CREATE INDEX IF NOT EXISTS idx_background_jobs_job_type ON background_jobs (job_type);
-- CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs (status);
-- CREATE INDEX IF NOT EXISTS idx_background_jobs_priority ON background_jobs (priority);
-- CREATE INDEX IF NOT EXISTS idx_background_jobs_user_id ON background_jobs (user_id);
-- CREATE INDEX IF NOT EXISTS idx_background_jobs_created_at ON background_jobs (created_at);
-- CREATE INDEX IF NOT EXISTS idx_background_jobs_status_priority ON background_jobs (status, priority);

-- ============================================================================
-- FULL-TEXT SEARCH INDEXES
-- ============================================================================

-- Combined search indexes for BIM objects
CREATE INDEX IF NOT EXISTS idx_bim_objects_search ON (
    SELECT id, 'wall' as object_type, name, category, project_id, building_id, floor_id, created_at
    FROM walls
    UNION ALL
    SELECT id, 'room' as object_type, name, category, project_id, building_id, floor_id, created_at
    FROM rooms
    UNION ALL
    SELECT id, 'door' as object_type, name, category, project_id, building_id, floor_id, created_at
    FROM doors
    UNION ALL
    SELECT id, 'window' as object_type, name, category, project_id, building_id, floor_id, created_at
    FROM windows
    UNION ALL
    SELECT id, 'device' as object_type, name, category, project_id, building_id, floor_id, created_at
    FROM devices
) USING gin(to_tsvector('english', name || ' ' || category));

-- ============================================================================
-- SPATIAL INDEXES FOR PERFORMANCE
-- ============================================================================

-- Spatial indexes for geometric queries
CREATE INDEX IF NOT EXISTS idx_spatial_buildings ON buildings USING gist (ST_Transform(geom, 4326));
CREATE INDEX IF NOT EXISTS idx_spatial_floors ON floors USING gist (ST_Transform(geom, 4326));

-- ============================================================================
-- PARTIAL INDEXES FOR COMMON QUERIES
-- ============================================================================

-- Active assignments only
CREATE INDEX IF NOT EXISTS idx_assignments_active ON assignments (assigned_to, object_type, object_id)
WHERE status = 'active';

-- Recent comments only
CREATE INDEX IF NOT EXISTS idx_comments_recent ON comments (object_type, object_id, created_at)
WHERE created_at > CURRENT_DATE - INTERVAL '30 days';

-- Active BIM objects only
CREATE INDEX IF NOT EXISTS idx_bim_objects_active ON (
    SELECT id, 'wall' as object_type, project_id, building_id, floor_id, status
    FROM walls WHERE status = 'active'
    UNION ALL
    SELECT id, 'room' as object_type, project_id, building_id, floor_id, status
    FROM rooms WHERE status = 'active'
    UNION ALL
    SELECT id, 'door' as object_type, project_id, building_id, floor_id, status
    FROM doors WHERE status = 'active'
    UNION ALL
    SELECT id, 'window' as object_type, project_id, building_id, floor_id, status
    FROM windows WHERE status = 'active'
    UNION ALL
    SELECT id, 'device' as object_type, project_id, building_id, floor_id, status
    FROM devices WHERE status = 'active'
) (project_id, building_id, floor_id);

-- ============================================================================
-- STATISTICS AND ANALYTICS
-- ============================================================================

-- Update table statistics for query planner
ANALYZE users;
ANALYZE projects;
ANALYZE buildings;
ANALYZE floors;
ANALYZE walls;
ANALYZE rooms;
ANALYZE doors;
ANALYZE windows;
ANALYZE devices;
ANALYZE labels;
ANALYZE zones;
ANALYZE comments;
ANALYZE assignments;
ANALYZE object_history;
ANALYZE categories;
ANALYZE user_category_permissions;
ANALYZE audit_logs;
ANALYZE chat_messages;
ANALYZE catalog_items;

-- ============================================================================
-- INDEX MAINTENANCE
-- ============================================================================

-- Create function to maintain indexes
CREATE OR REPLACE FUNCTION maintain_indexes()
RETURNS void AS $$
BEGIN
    -- Reindex frequently updated tables
    REINDEX INDEX CONCURRENTLY idx_walls_project_status;
    REINDEX INDEX CONCURRENTLY idx_rooms_project_status;
    REINDEX INDEX CONCURRENTLY idx_doors_project_status;
    REINDEX INDEX CONCURRENTLY idx_windows_project_status;
    REINDEX INDEX CONCURRENTLY idx_devices_project_status;

    -- Update statistics
    ANALYZE;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run index maintenance (requires pg_cron extension)
-- SELECT cron.schedule('index-maintenance', '0 2 * * 0', 'SELECT maintain_indexes();');

-- ============================================================================
-- PERFORMANCE VIEWS
-- ============================================================================

-- Create view for active BIM objects by project
CREATE OR REPLACE VIEW active_bim_objects AS
SELECT
    'wall' as object_type,
    id,
    name,
    category,
    status,
    project_id,
    building_id,
    floor_id,
    created_by,
    assigned_to,
    created_at,
    updated_at
FROM walls WHERE status = 'active'
UNION ALL
SELECT
    'room' as object_type,
    id,
    name,
    category,
    status,
    project_id,
    building_id,
    floor_id,
    created_by,
    assigned_to,
    created_at,
    updated_at
FROM rooms WHERE status = 'active'
UNION ALL
SELECT
    'door' as object_type,
    id,
    name,
    category,
    status,
    project_id,
    building_id,
    floor_id,
    created_by,
    assigned_to,
    created_at,
    updated_at
FROM doors WHERE status = 'active'
UNION ALL
SELECT
    'window' as object_type,
    id,
    name,
    category,
    status,
    project_id,
    building_id,
    floor_id,
    created_by,
    assigned_to,
    created_at,
    updated_at
FROM windows WHERE status = 'active'
UNION ALL
SELECT
    'device' as object_type,
    id,
    name,
    category,
    status,
    project_id,
    building_id,
    floor_id,
    created_by,
    assigned_to,
    created_at,
    updated_at
FROM devices WHERE status = 'active';

-- Create index on the view
CREATE INDEX IF NOT EXISTS idx_active_bim_objects_project ON active_bim_objects (project_id);
CREATE INDEX IF NOT EXISTS idx_active_bim_objects_building ON active_bim_objects (building_id);
CREATE INDEX IF NOT EXISTS idx_active_bim_objects_category ON active_bim_objects (category);
CREATE INDEX IF NOT EXISTS idx_active_bim_objects_assigned ON active_bim_objects (assigned_to);

-- ============================================================================
-- INDEX USAGE MONITORING
-- ============================================================================

-- Create view to monitor index usage
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Create view to identify unused indexes
CREATE OR REPLACE VIEW unused_indexes AS
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
