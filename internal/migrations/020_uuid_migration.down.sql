-- ArxOS UUID Migration Rollback
-- Version: 003
-- Description: Rollback UUID migration changes
-- 
-- This migration removes UUID columns and related infrastructure
-- WARNING: This will remove all UUID data and mappings!

-- =============================================================================
-- Drop Migration Status View
-- =============================================================================
DROP VIEW IF EXISTS migration_status;

-- =============================================================================
-- Drop Migration Functions
-- =============================================================================
DROP FUNCTION IF EXISTS generate_uuids_for_table(TEXT);
DROP FUNCTION IF EXISTS create_id_mappings_for_table(TEXT);

-- =============================================================================
-- Remove UUID Columns from Tables
-- =============================================================================

-- Remove UUID columns and indexes
ALTER TABLE organizations DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_organizations_uuid;

ALTER TABLE users DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_users_uuid;

ALTER TABLE buildings DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_buildings_uuid;

ALTER TABLE floors DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_floors_uuid;

ALTER TABLE zones DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_zones_uuid;

ALTER TABLE rooms DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_rooms_uuid;

ALTER TABLE equipment DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_equipment_uuid;

ALTER TABLE points DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_points_uuid;

ALTER TABLE alarms DROP COLUMN IF EXISTS uuid_id;
DROP INDEX IF EXISTS idx_alarms_uuid;

-- =============================================================================
-- Drop ID Mappings Table
-- =============================================================================
DROP TABLE IF EXISTS id_mappings;

-- =============================================================================
-- Comments
-- =============================================================================
-- Migration rollback completed
-- All UUID-related infrastructure has been removed
-- System is back to TEXT-only ID system
