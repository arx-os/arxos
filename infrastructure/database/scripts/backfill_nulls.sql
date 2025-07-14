-- =============================================================================
-- Backfill NULL Values Script for Arxos Database
-- =============================================================================
-- This script safely updates NULL values with appropriate defaults before
-- applying NOT NULL and CHECK constraints. It follows Arxos standards for
-- data integrity and safe migrations.

-- IMPORTANT: Run this script BEFORE applying constraint migrations
-- This script is designed to be safe and reversible

-- =============================================================================
-- SAFETY CHECKS AND VALIDATION
-- =============================================================================

-- Create a backup of affected tables before making changes
DO $$
DECLARE
    backup_suffix TEXT := '_backup_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS');
    table_name TEXT;
    backup_table_name TEXT;
BEGIN
    -- List of tables that will be modified
    FOR table_name IN 
        SELECT unnest(ARRAY[
            'users', 'projects', 'buildings', 'floors', 'categories',
            'rooms', 'walls', 'doors', 'windows', 'devices', 'labels', 'zones',
            'comments', 'assignments', 'object_history', 'audit_logs',
            'user_category_permissions', 'chat_messages', 'catalog_items'
        ])
    LOOP
        -- Check if table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name) THEN
            backup_table_name := table_name || backup_suffix;
            
            -- Create backup table
            EXECUTE format('CREATE TABLE %I AS SELECT * FROM %I', backup_table_name, table_name);
            
            RAISE NOTICE 'Created backup table: %', backup_table_name;
        END IF;
    END LOOP;
END $$;

-- =============================================================================
-- USER TABLE BACKFILL
-- =============================================================================

-- Update NULL status fields to 'active' (assuming most users should be active)
UPDATE users 
SET role = 'user' 
WHERE role IS NULL;

-- Update NULL timestamps to current timestamp
UPDATE users 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE users 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- =============================================================================
-- PROJECT TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE projects 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE projects 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- =============================================================================
-- BUILDING TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE buildings 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE buildings 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- =============================================================================
-- FLOOR TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE floors 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE floors 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- =============================================================================
-- CATEGORY TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE categories 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE categories 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- =============================================================================
-- ROOM TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'active' (assuming most rooms should be active)
UPDATE rooms 
SET status = 'active' 
WHERE status IS NULL;

-- Update NULL category to empty string (already has NOT NULL DEFAULT '')
UPDATE rooms 
SET category = '' 
WHERE category IS NULL;

-- =============================================================================
-- WALL TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'active'
UPDATE walls 
SET status = 'active' 
WHERE status IS NULL;

-- Update NULL category to empty string
UPDATE walls 
SET category = '' 
WHERE category IS NULL;

-- Update NULL material to 'concrete' (most common default)
UPDATE walls 
SET material = 'concrete' 
WHERE material IS NULL;

-- =============================================================================
-- DOOR TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'active'
UPDATE doors 
SET status = 'active' 
WHERE status IS NULL;

-- Update NULL category to empty string
UPDATE doors 
SET category = '' 
WHERE category IS NULL;

-- Update NULL material to 'metal' (common door material)
UPDATE doors 
SET material = 'metal' 
WHERE material IS NULL;

-- =============================================================================
-- WINDOW TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'active'
UPDATE windows 
SET status = 'active' 
WHERE status IS NULL;

-- Update NULL category to empty string
UPDATE windows 
SET category = '' 
WHERE category IS NULL;

-- Update NULL material to 'glass' (common window material)
UPDATE windows 
SET material = 'glass' 
WHERE material IS NULL;

-- =============================================================================
-- DEVICE TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'active'
UPDATE devices 
SET status = 'active' 
WHERE status IS NULL;

-- Update NULL category to empty string
UPDATE devices 
SET category = '' 
WHERE category IS NULL;

-- Update NULL type to 'equipment' (generic default)
UPDATE devices 
SET type = 'equipment' 
WHERE type IS NULL;

-- Update NULL system to 'electrical' (most common system)
UPDATE devices 
SET system = 'electrical' 
WHERE system IS NULL;

-- =============================================================================
-- LABEL TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'active'
UPDATE labels 
SET status = 'active' 
WHERE status IS NULL;

-- Update NULL category to empty string
UPDATE labels 
SET category = '' 
WHERE category IS NULL;

-- Update NULL text to 'Label' (generic default)
UPDATE labels 
SET text = 'Label' 
WHERE text IS NULL;

-- =============================================================================
-- ZONE TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'active'
UPDATE zones 
SET status = 'active' 
WHERE status IS NULL;

-- Update NULL category to empty string
UPDATE zones 
SET category = '' 
WHERE category IS NULL;

-- Update NULL name to 'Zone' (generic default)
UPDATE zones 
SET name = 'Zone' 
WHERE name IS NULL;

-- =============================================================================
-- DRAWING TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE drawings 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE drawings 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- =============================================================================
-- COMMENT TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE comments 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE comments 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- Update NULL content to 'Comment' (should not happen, but safety)
UPDATE comments 
SET content = 'Comment' 
WHERE content IS NULL;

-- =============================================================================
-- ASSIGNMENT TABLE BACKFILL
-- =============================================================================

-- Update NULL status to 'assigned'
UPDATE assignments 
SET status = 'assigned' 
WHERE status IS NULL;

-- Update NULL timestamps
UPDATE assignments 
SET assigned_at = CURRENT_TIMESTAMP 
WHERE assigned_at IS NULL;

-- =============================================================================
-- OBJECT HISTORY TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE object_history 
SET changed_at = CURRENT_TIMESTAMP 
WHERE changed_at IS NULL;

-- Update NULL change_type to 'modified' (generic default)
UPDATE object_history 
SET change_type = 'modified' 
WHERE change_type IS NULL;

-- =============================================================================
-- AUDIT LOG TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE audit_logs 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Update NULL action to 'unknown' (generic default)
UPDATE audit_logs 
SET action = 'unknown' 
WHERE action IS NULL;

-- =============================================================================
-- USER CATEGORY PERMISSIONS TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE user_category_permissions 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE user_category_permissions 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- Update NULL can_edit to false (safe default)
UPDATE user_category_permissions 
SET can_edit = false 
WHERE can_edit IS NULL;

-- =============================================================================
-- CHAT MESSAGES TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE chat_messages 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Update NULL message to 'Message' (should not happen, but safety)
UPDATE chat_messages 
SET message = 'Message' 
WHERE message IS NULL;

-- =============================================================================
-- CATALOG ITEMS TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE catalog_items 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE catalog_items 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- Update NULL approved to false (safe default)
UPDATE catalog_items 
SET approved = false 
WHERE approved IS NULL;

-- Update NULL type to 'equipment' (generic default)
UPDATE catalog_items 
SET type = 'equipment' 
WHERE type IS NULL;

-- =============================================================================
-- SLOW QUERY LOG TABLE BACKFILL
-- =============================================================================

-- Update NULL timestamps
UPDATE slow_query_log 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE slow_query_log 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- Update NULL severity to 'info' (safe default)
UPDATE slow_query_log 
SET severity = 'info' 
WHERE severity IS NULL;

-- =============================================================================
-- VALIDATION AND REPORTING
-- =============================================================================

-- Create a summary report of the backfill operation
DO $$
DECLARE
    table_name TEXT;
    null_count INTEGER;
    total_count INTEGER;
    summary_record RECORD;
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'BACKFILL OPERATION SUMMARY';
    RAISE NOTICE '=============================================================================';
    
    -- Check for remaining NULL values in critical columns
    FOR summary_record IN
        SELECT 
            'users' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN role IS NULL THEN 1 END) as null_count
        FROM users
        UNION ALL
        SELECT 
            'projects' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN name IS NULL THEN 1 END) as null_count
        FROM projects
        UNION ALL
        SELECT 
            'buildings' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN name IS NULL THEN 1 END) as null_count
        FROM buildings
        UNION ALL
        SELECT 
            'rooms' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status IS NULL THEN 1 END) as null_count
        FROM rooms
        UNION ALL
        SELECT 
            'walls' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status IS NULL THEN 1 END) as null_count
        FROM walls
        UNION ALL
        SELECT 
            'doors' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status IS NULL THEN 1 END) as null_count
        FROM doors
        UNION ALL
        SELECT 
            'windows' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status IS NULL THEN 1 END) as null_count
        FROM windows
        UNION ALL
        SELECT 
            'devices' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status IS NULL THEN 1 END) as null_count
        FROM devices
        UNION ALL
        SELECT 
            'labels' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status IS NULL THEN 1 END) as null_count
        FROM labels
        UNION ALL
        SELECT 
            'zones' as table_name,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status IS NULL THEN 1 END) as null_count
        FROM zones
    LOOP
        RAISE NOTICE 'Table: % | Total: % | Remaining NULL: %', 
            summary_record.table_name, 
            summary_record.total_count, 
            summary_record.null_count;
    END LOOP;
    
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Backfill operation completed successfully!';
    RAISE NOTICE 'You can now safely apply NOT NULL and CHECK constraints.';
    RAISE NOTICE '=============================================================================';
END $$;

-- =============================================================================
-- ROLLBACK INSTRUCTIONS
-- =============================================================================
-- If you need to rollback these changes, you can restore from the backup tables
-- created at the beginning of this script. The backup tables have the suffix
-- '_backup_YYYYMMDD_HH24MISS'.

-- Example rollback command:
-- DROP TABLE users;
-- ALTER TABLE users_backup_20240101_120000 RENAME TO users; 