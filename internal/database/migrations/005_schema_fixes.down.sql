-- Rollback schema fixes
-- Version: 005

-- Drop added indexes
DROP INDEX IF EXISTS idx_equipment_status;
DROP INDEX IF EXISTS idx_equipment_location;
DROP INDEX IF EXISTS idx_equipment_updated;
DROP INDEX IF EXISTS idx_rooms_floor;
DROP INDEX IF EXISTS idx_rooms_zone;
DROP INDEX IF EXISTS idx_floors_building_level;
DROP INDEX IF EXISTS idx_equipment_building_type;
DROP INDEX IF EXISTS idx_equipment_floor_status;

-- Drop normalized view
DROP VIEW IF EXISTS equipment_normalized;