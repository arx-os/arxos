-- Migration 014: BAS Integration - Rollback
-- Description: Remove BAS integration tables and room enhancements
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- Drop triggers
-- ============================================================================
DROP TRIGGER IF EXISTS bas_points_updated_at ON bas_points;
DROP TRIGGER IF EXISTS bas_systems_updated_at ON bas_systems;
DROP FUNCTION IF EXISTS update_bas_updated_at();

-- ============================================================================
-- Drop tables (in reverse order of creation)
-- ============================================================================
DROP TABLE IF EXISTS bas_import_history CASCADE;
DROP TABLE IF EXISTS bas_points CASCADE;
DROP TABLE IF EXISTS bas_systems CASCADE;

-- ============================================================================
-- Revert rooms table changes
-- ============================================================================
DROP INDEX IF EXISTS idx_rooms_dimensions;
DROP INDEX IF EXISTS idx_rooms_geometry;
DROP INDEX IF EXISTS idx_rooms_confidence;
DROP INDEX IF EXISTS idx_rooms_fidelity;

ALTER TABLE rooms DROP COLUMN IF EXISTS scan_session_id;
ALTER TABLE rooms DROP COLUMN IF EXISTS confidence_level;
ALTER TABLE rooms DROP COLUMN IF EXISTS fidelity_source;
ALTER TABLE rooms DROP COLUMN IF EXISTS geometry;
ALTER TABLE rooms DROP COLUMN IF EXISTS length;
ALTER TABLE rooms DROP COLUMN IF EXISTS width;

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 014 rolled back';

