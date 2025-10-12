-- Migration 005: Add spatial indices (simplified for current schema)
-- Description: Creates basic spatial indices for equipment locations

-- Create indices on equipment locations
CREATE INDEX IF NOT EXISTS idx_equipment_location_xyz
ON equipment(location_x, location_y, location_z);

-- Create index for equipment type
CREATE INDEX IF NOT EXISTS idx_equipment_type
ON equipment(equipment_type);

-- Create index for status filtering  
CREATE INDEX IF NOT EXISTS idx_equipment_status
ON equipment(status);

-- Create composite index for building + location queries
CREATE INDEX IF NOT EXISTS idx_equipment_building_location
ON equipment(building_id, location_x, location_y);

-- Note: Advanced PostGIS features skipped - current schema uses simple x/y/z columns
-- Future migrations can add PostGIS GEOMETRY columns when needed
