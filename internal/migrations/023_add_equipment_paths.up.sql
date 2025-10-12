-- Migration 023: Add path columns for universal naming convention
-- Author: Joel Pate
-- Date: 2025-10-12
-- Purpose: Add path column to store equipment addresses like /B1/3/301/HVAC/VAV-301

BEGIN;

-- Add path column to equipment table
ALTER TABLE equipment
ADD COLUMN IF NOT EXISTS path TEXT;

-- Add path column to bas_points table
ALTER TABLE bas_points
ADD COLUMN IF NOT EXISTS path TEXT;

-- Create indexes so we can search by path quickly
-- (Like adding an index to the back of a book - makes searches fast)
CREATE INDEX IF NOT EXISTS idx_equipment_path
ON equipment(path);

CREATE INDEX IF NOT EXISTS idx_bas_points_path
ON bas_points(path);

-- Special indexes for wildcard searches (like /B1/3/*/HVAC/*)
-- The text_pattern_ops makes LIKE queries much faster
CREATE INDEX IF NOT EXISTS idx_equipment_path_prefix
ON equipment(path text_pattern_ops);

CREATE INDEX IF NOT EXISTS idx_bas_points_path_prefix
ON bas_points(path text_pattern_ops);

-- Add documentation about what the column is for
COMMENT ON COLUMN equipment.path IS
'Universal naming convention path (e.g. /B1/3/301/HVAC/VAV-301). Format: /BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT';

COMMENT ON COLUMN bas_points.path IS
'Universal naming convention path (e.g. /B1/3/301/BAS/AI-1-1). Format: /BUILDING/FLOOR/ROOM/BAS/POINT-NAME';

COMMIT;

