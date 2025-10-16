-- Migration 024 DOWN: Remove room geometry support
-- This removes the geometry columns and functions added in the up migration

-- Start transaction
BEGIN;

-- Drop triggers first
DROP TRIGGER IF EXISTS trigger_update_room_dimensions ON rooms;
DROP TRIGGER IF EXISTS trigger_update_room_center_point ON rooms;

-- Drop functions
DROP FUNCTION IF EXISTS update_room_dimensions_from_geometry();
DROP FUNCTION IF EXISTS update_room_center_point();
DROP FUNCTION IF EXISTS calculate_room_area_from_geometry(GEOMETRY);
DROP FUNCTION IF EXISTS get_rooms_in_bounds(REAL, REAL, REAL, REAL);
DROP FUNCTION IF EXISTS get_rooms_near_point(REAL, REAL, REAL);
DROP FUNCTION IF EXISTS get_room_geojson(TEXT);

-- Drop indexes
DROP INDEX IF EXISTS idx_rooms_geometry;
DROP INDEX IF EXISTS idx_rooms_center_point;

-- Drop columns
ALTER TABLE rooms DROP COLUMN IF EXISTS geometry;
ALTER TABLE rooms DROP COLUMN IF EXISTS center_point;
ALTER TABLE rooms DROP COLUMN IF EXISTS width;

-- Commit transaction
COMMIT;
