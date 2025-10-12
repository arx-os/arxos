-- Migration 023 DOWN: Remove path columns
-- This removes the changes if we need to rollback

BEGIN;

-- Drop indexes first (must drop indexes before dropping columns)
DROP INDEX IF EXISTS idx_equipment_path_prefix;
DROP INDEX IF EXISTS idx_bas_points_path_prefix;
DROP INDEX IF EXISTS idx_equipment_path;
DROP INDEX IF EXISTS idx_bas_points_path;

-- Drop the columns
ALTER TABLE equipment DROP COLUMN IF EXISTS path;
ALTER TABLE bas_points DROP COLUMN IF EXISTS path;

COMMIT;

