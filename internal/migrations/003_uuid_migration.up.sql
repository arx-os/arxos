-- ArxOS UUID Migration Schema
-- Version: 003
-- Description: Add UUID support to existing tables for gradual migration
-- 
-- This migration adds UUID columns alongside existing TEXT ID columns
-- to enable gradual migration while maintaining backward compatibility

-- =============================================================================
-- ID Mappings Table
-- =============================================================================
-- This table stores mappings between UUID and legacy IDs for reference
CREATE TABLE IF NOT EXISTS id_mappings (
    id SERIAL PRIMARY KEY,
    uuid_id VARCHAR(36) NOT NULL,
    legacy_id VARCHAR(255) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    migrated BOOLEAN DEFAULT FALSE,
    UNIQUE(uuid_id, legacy_id, table_name)
);

CREATE INDEX IF NOT EXISTS idx_id_mappings_uuid ON id_mappings(uuid_id);
CREATE INDEX IF NOT EXISTS idx_id_mappings_legacy ON id_mappings(legacy_id);
CREATE INDEX IF NOT EXISTS idx_id_mappings_table ON id_mappings(table_name);

-- =============================================================================
-- Organizations Table - Add UUID Support
-- =============================================================================
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_organizations_uuid ON organizations(uuid_id);

-- =============================================================================
-- Users Table - Add UUID Support
-- =============================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid_id);

-- =============================================================================
-- Buildings Table - Add UUID Support
-- =============================================================================
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_buildings_uuid ON buildings(uuid_id);

-- =============================================================================
-- Floors Table - Add UUID Support
-- =============================================================================
ALTER TABLE floors ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_floors_uuid ON floors(uuid_id);

-- =============================================================================
-- Zones Table - Add UUID Support
-- =============================================================================
ALTER TABLE zones ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_zones_uuid ON zones(uuid_id);

-- =============================================================================
-- Rooms Table - Add UUID Support
-- =============================================================================
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_rooms_uuid ON rooms(uuid_id);

-- =============================================================================
-- Equipment Table - Add UUID Support
-- =============================================================================
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_equipment_uuid ON equipment(uuid_id);

-- =============================================================================
-- Points Table - Add UUID Support
-- =============================================================================
ALTER TABLE points ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_points_uuid ON points(uuid_id);

-- =============================================================================
-- Alarms Table - Add UUID Support
-- =============================================================================
ALTER TABLE alarms ADD COLUMN IF NOT EXISTS uuid_id UUID DEFAULT gen_random_uuid();

-- Create index on UUID column
CREATE INDEX IF NOT EXISTS idx_alarms_uuid ON alarms(uuid_id);

-- =============================================================================
-- Migration Functions
-- =============================================================================

-- Function to generate UUID for existing records without UUID
CREATE OR REPLACE FUNCTION generate_uuids_for_table(table_name TEXT)
RETURNS INTEGER AS $$
DECLARE
    update_query TEXT;
    result INTEGER;
BEGIN
    -- Build dynamic update query
    update_query := format('UPDATE %I SET uuid_id = gen_random_uuid() WHERE uuid_id IS NULL', table_name);
    
    -- Execute update
    EXECUTE update_query;
    
    -- Get affected rows
    GET DIAGNOSTICS result = ROW_COUNT;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to create ID mappings for a table
CREATE OR REPLACE FUNCTION create_id_mappings_for_table(table_name TEXT)
RETURNS INTEGER AS $$
DECLARE
    insert_query TEXT;
    result INTEGER;
BEGIN
    -- Build dynamic insert query
    insert_query := format('
        INSERT INTO id_mappings (uuid_id, legacy_id, table_name, created_at, migrated)
        SELECT uuid_id, id, %L, CURRENT_TIMESTAMP, FALSE
        FROM %I 
        WHERE uuid_id IS NOT NULL AND id IS NOT NULL
        ON CONFLICT (uuid_id, legacy_id, table_name) DO NOTHING
    ', table_name, table_name);
    
    -- Execute insert
    EXECUTE insert_query;
    
    -- Get affected rows
    GET DIAGNOSTICS result = ROW_COUNT;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Initial Data Migration
-- =============================================================================

-- Generate UUIDs for existing records
DO $$
DECLARE
    tables TEXT[] := ARRAY['organizations', 'users', 'buildings', 'floors', 'zones', 'rooms', 'equipment', 'points', 'alarms'];
    table_name TEXT;
    updated_count INTEGER;
BEGIN
    FOREACH table_name IN ARRAY tables
    LOOP
        SELECT generate_uuids_for_table(table_name) INTO updated_count;
        RAISE NOTICE 'Generated UUIDs for %: % records', table_name, updated_count;
        
        SELECT create_id_mappings_for_table(table_name) INTO updated_count;
        RAISE NOTICE 'Created mappings for %: % records', table_name, updated_count;
    END LOOP;
END $$;

-- =============================================================================
-- Migration Status View
-- =============================================================================
CREATE OR REPLACE VIEW migration_status AS
SELECT 
    'organizations' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM organizations
UNION ALL
SELECT 
    'users' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM users
UNION ALL
SELECT 
    'buildings' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM buildings
UNION ALL
SELECT 
    'floors' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM floors
UNION ALL
SELECT 
    'zones' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM zones
UNION ALL
SELECT 
    'rooms' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM rooms
UNION ALL
SELECT 
    'equipment' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM equipment
UNION ALL
SELECT 
    'points' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM points
UNION ALL
SELECT 
    'alarms' as table_name,
    COUNT(*) as total_records,
    COUNT(uuid_id) as uuid_records,
    COUNT(*) - COUNT(uuid_id) as legacy_records,
    ROUND(COUNT(uuid_id)::numeric / COUNT(*)::numeric * 100, 2) as migration_percentage
FROM alarms;

-- =============================================================================
-- Comments
-- =============================================================================
COMMENT ON TABLE id_mappings IS 'Maps UUID IDs to legacy TEXT IDs for backward compatibility during migration';
COMMENT ON COLUMN organizations.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN users.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN buildings.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN floors.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN zones.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN rooms.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN equipment.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN points.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON COLUMN alarms.uuid_id IS 'UUID identifier for gradual migration from TEXT ID';
COMMENT ON VIEW migration_status IS 'Shows migration progress for all tables';
