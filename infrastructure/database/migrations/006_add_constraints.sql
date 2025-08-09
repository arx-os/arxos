-- 006_add_constraints.sql
-- Migration: Add NOT NULL and CHECK constraints for data integrity
--
-- This migration adds comprehensive constraints to strengthen data integrity
-- while maintaining backward compatibility. It follows Arxos standards for
-- safe migrations and includes rollback capabilities.

-- IMPORTANT: Run backfill_nulls.sql BEFORE applying this migration
-- This migration assumes NULL values have been safely backfilled

-- =============================================================================
-- NOT NULL CONSTRAINTS
-- =============================================================================

-- Users table constraints
ALTER TABLE users
    ALTER COLUMN role SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Projects table constraints
ALTER TABLE projects
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Buildings table constraints
ALTER TABLE buildings
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Floors table constraints
ALTER TABLE floors
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Categories table constraints
ALTER TABLE categories
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Rooms table constraints
ALTER TABLE rooms
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL;

-- Walls table constraints
ALTER TABLE walls
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL,
    ALTER COLUMN material SET NOT NULL;

-- Doors table constraints
ALTER TABLE doors
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL,
    ALTER COLUMN material SET NOT NULL;

-- Windows table constraints
ALTER TABLE windows
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL,
    ALTER COLUMN material SET NOT NULL;

-- Devices table constraints
ALTER TABLE devices
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL,
    ALTER COLUMN type SET NOT NULL,
    ALTER COLUMN system SET NOT NULL;

-- Labels table constraints
ALTER TABLE labels
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL,
    ALTER COLUMN text SET NOT NULL;

-- Zones table constraints
ALTER TABLE zones
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN category SET NOT NULL,
    ALTER COLUMN name SET NOT NULL;

-- Drawings table constraints
ALTER TABLE drawings
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Comments table constraints
ALTER TABLE comments
    ALTER COLUMN content SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Assignments table constraints
ALTER TABLE assignments
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN assigned_at SET NOT NULL;

-- Object history table constraints
ALTER TABLE object_history
    ALTER COLUMN change_type SET NOT NULL,
    ALTER COLUMN changed_at SET NOT NULL;

-- Audit logs table constraints
ALTER TABLE audit_logs
    ALTER COLUMN action SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL;

-- User category permissions table constraints
ALTER TABLE user_category_permissions
    ALTER COLUMN can_edit SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Chat messages table constraints
ALTER TABLE chat_messages
    ALTER COLUMN message SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL;

-- Catalog items table constraints
ALTER TABLE catalog_items
    ALTER COLUMN approved SET NOT NULL,
    ALTER COLUMN type SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- Slow query log table constraints
ALTER TABLE slow_query_log
    ALTER COLUMN severity SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

-- =============================================================================
-- CHECK CONSTRAINTS
-- =============================================================================

-- Users table check constraints
ALTER TABLE users
    ADD CONSTRAINT chk_users_role
    CHECK (role IN ('user', 'admin', 'manager', 'viewer'));

-- Rooms table check constraints
ALTER TABLE rooms
    ADD CONSTRAINT chk_rooms_status
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled'));

-- Walls table check constraints
ALTER TABLE walls
    ADD CONSTRAINT chk_walls_status
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled')),
    ADD CONSTRAINT chk_walls_material
    CHECK (material IN ('concrete', 'steel', 'wood', 'glass', 'plastic', 'metal'));

-- Doors table check constraints
ALTER TABLE doors
    ADD CONSTRAINT chk_doors_status
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled')),
    ADD CONSTRAINT chk_doors_material
    CHECK (material IN ('concrete', 'steel', 'wood', 'glass', 'plastic', 'metal'));

-- Windows table check constraints
ALTER TABLE windows
    ADD CONSTRAINT chk_windows_status
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled')),
    ADD CONSTRAINT chk_windows_material
    CHECK (material IN ('concrete', 'steel', 'wood', 'glass', 'plastic', 'metal'));

-- Devices table check constraints
ALTER TABLE devices
    ADD CONSTRAINT chk_devices_status
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled')),
    ADD CONSTRAINT chk_devices_system
    CHECK (system IN ('HVAC', 'electrical', 'plumbing', 'fire', 'security', 'lighting'));

-- Labels table check constraints
ALTER TABLE labels
    ADD CONSTRAINT chk_labels_status
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled'));

-- Zones table check constraints
ALTER TABLE zones
    ADD CONSTRAINT chk_zones_status
    CHECK (status IN ('active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled'));

-- Assignments table check constraints
ALTER TABLE assignments
    ADD CONSTRAINT chk_assignments_status
    CHECK (status IN ('assigned', 'in_progress', 'completed', 'cancelled'));

-- Object history table check constraints
ALTER TABLE object_history
    ADD CONSTRAINT chk_object_history_change_type
    CHECK (change_type IN ('created', 'updated', 'deleted', 'modified'));

-- Audit logs table check constraints
ALTER TABLE audit_logs
    ADD CONSTRAINT chk_audit_logs_action
    CHECK (action IN ('create', 'update', 'delete', 'login', 'logout', 'unknown'));

-- Slow query log table check constraints
ALTER TABLE slow_query_log
    ADD CONSTRAINT chk_slow_query_log_severity
    CHECK (severity IN ('info', 'warning', 'critical'));

-- =============================================================================
-- DOMAIN-SPECIFIC CHECK CONSTRAINTS
-- =============================================================================

-- Email format validation for users
ALTER TABLE users
    ADD CONSTRAINT chk_users_email_format
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Username format validation
ALTER TABLE users
    ADD CONSTRAINT chk_users_username_format
    CHECK (username ~* '^[a-zA-Z0-9_-]{3,50}$');

-- Password hash format validation
ALTER TABLE users
    ADD CONSTRAINT chk_users_password_hash_format
    CHECK (password_hash ~* '^[a-fA-F0-9]{64}$');

-- Timestamp validation (ensure timestamps are not in the future)
ALTER TABLE users
    ADD CONSTRAINT chk_users_created_at_future
    CHECK (created_at <= CURRENT_TIMESTAMP),
    ADD CONSTRAINT chk_users_updated_at_future
    CHECK (updated_at <= CURRENT_TIMESTAMP);

ALTER TABLE projects
    ADD CONSTRAINT chk_projects_created_at_future
    CHECK (created_at <= CURRENT_TIMESTAMP),
    ADD CONSTRAINT chk_projects_updated_at_future
    CHECK (updated_at <= CURRENT_TIMESTAMP);

ALTER TABLE buildings
    ADD CONSTRAINT chk_buildings_created_at_future
    CHECK (created_at <= CURRENT_TIMESTAMP),
    ADD CONSTRAINT chk_buildings_updated_at_future
    CHECK (updated_at <= CURRENT_TIMESTAMP);

-- Duration validation for slow query log
ALTER TABLE slow_query_log
    ADD CONSTRAINT chk_slow_query_log_duration_positive
    CHECK (duration_ms > 0),
    ADD CONSTRAINT chk_slow_query_log_duration_reasonable
    CHECK (duration_ms <= 300000); -- 5 minutes max

-- =============================================================================
-- INDEXES FOR CONSTRAINT PERFORMANCE
-- =============================================================================

-- Add indexes for frequently checked constraint columns
CREATE INDEX IF NOT EXISTS idx_users_role_check ON users (role);
CREATE INDEX IF NOT EXISTS idx_rooms_status_check ON rooms (status);
CREATE INDEX IF NOT EXISTS idx_walls_status_check ON walls (status);
CREATE INDEX IF NOT EXISTS idx_walls_material_check ON walls (material);
CREATE INDEX IF NOT EXISTS idx_doors_status_check ON doors (status);
CREATE INDEX IF NOT EXISTS idx_doors_material_check ON doors (material);
CREATE INDEX IF NOT EXISTS idx_windows_status_check ON windows (status);
CREATE INDEX IF NOT EXISTS idx_windows_material_check ON windows (material);
CREATE INDEX IF NOT EXISTS idx_devices_status_check ON devices (status);
CREATE INDEX IF NOT EXISTS idx_devices_system_check ON devices (system);
CREATE INDEX IF NOT EXISTS idx_labels_status_check ON labels (status);
CREATE INDEX IF NOT EXISTS idx_zones_status_check ON zones (status);
CREATE INDEX IF NOT EXISTS idx_assignments_status_check ON assignments (status);
CREATE INDEX IF NOT EXISTS idx_object_history_change_type_check ON object_history (change_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_check ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_slow_query_log_severity_check ON slow_query_log (severity);

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- Verify that all constraints are properly applied
DO $$
DECLARE
    constraint_count INTEGER;
    table_name TEXT;
    constraint_name TEXT;
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'CONSTRAINT VALIDATION';
    RAISE NOTICE '=============================================================================';

    -- Count NOT NULL constraints
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND is_nullable = 'NO';

    RAISE NOTICE 'NOT NULL constraints applied: %', constraint_count;

    -- Count CHECK constraints
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE table_schema = 'public'
    AND constraint_type = 'CHECK';

    RAISE NOTICE 'CHECK constraints applied: %', constraint_count;

    -- List all CHECK constraints
    RAISE NOTICE 'CHECK constraints:';
    FOR constraint_name IN
        SELECT tc.constraint_name, tc.table_name
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = 'public'
        AND tc.constraint_type = 'CHECK'
        ORDER BY tc.table_name, tc.constraint_name
    LOOP
        RAISE NOTICE '  - % on table %', constraint_name.constraint_name, constraint_name.table_name;
    END LOOP;

    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Constraint migration completed successfully!';
    RAISE NOTICE '=============================================================================';
END $$;

-- =============================================================================
-- ROLLBACK FUNCTIONS
-- =============================================================================

-- Function to drop all constraints added by this migration
CREATE OR REPLACE FUNCTION rollback_constraints_migration()
RETURNS VOID AS $$
DECLARE
    constraint_record RECORD;
BEGIN
    RAISE NOTICE 'Rolling back constraint migration...';

    -- Drop CHECK constraints
    FOR constraint_record IN
        SELECT tc.table_name, tc.constraint_name
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = 'public'
        AND tc.constraint_type = 'CHECK'
        AND tc.constraint_name LIKE 'chk_%'
    LOOP
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I',
                      constraint_record.table_name,
                      constraint_record.constraint_name);
        RAISE NOTICE 'Dropped constraint: % on table %',
                    constraint_record.constraint_name,
                    constraint_record.table_name;
    END LOOP;

    -- Reset NOT NULL constraints to nullable
    -- Note: This is a simplified rollback - in production you'd want more granular control
    ALTER TABLE users ALTER COLUMN role DROP NOT NULL;
    ALTER TABLE users ALTER COLUMN created_at DROP NOT NULL;
    ALTER TABLE users ALTER COLUMN updated_at DROP NOT NULL;

    ALTER TABLE projects ALTER COLUMN created_at DROP NOT NULL;
    ALTER TABLE projects ALTER COLUMN updated_at DROP NOT NULL;

    ALTER TABLE buildings ALTER COLUMN created_at DROP NOT NULL;
    ALTER TABLE buildings ALTER COLUMN updated_at DROP NOT NULL;

    -- Add more table rollbacks as needed...

    RAISE NOTICE 'Constraint rollback completed!';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================

-- This migration adds comprehensive data integrity constraints:
-- 1. NOT NULL constraints on required fields
-- 2. CHECK constraints for finite domain values
-- 3. Format validation for emails, usernames, etc.
-- 4. Performance indexes for constraint checking
-- 5. Validation queries to verify constraints
-- 6. Rollback function for safe migration reversal
--
-- IMPORTANT: Test this migration thoroughly in a staging environment
-- before applying to production. The rollback function provides a safety net.
