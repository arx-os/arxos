-- Schema fixes for consistency
-- Version: 005
-- Description: Fix column naming inconsistencies and add missing indexes

-- Note: SQLite doesn't support ALTER COLUMN, so we need to be careful
-- This migration focuses on adding missing indexes and constraints

-- Add missing indexes for better performance
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment(location_x, location_y, location_z);
CREATE INDEX IF NOT EXISTS idx_equipment_updated ON equipment(updated_at);

-- Add indexes for rooms
CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms(floor_id);
CREATE INDEX IF NOT EXISTS idx_rooms_zone ON rooms(zone_id);

-- Add indexes for floors
CREATE INDEX IF NOT EXISTS idx_floors_building_level ON floors(building_id, level);

-- Create a normalized view for equipment with consistent naming
CREATE VIEW IF NOT EXISTS equipment_normalized AS
SELECT
    id,
    room_id,
    floor_id,
    building_id,
    equipment_tag as tag,
    name,
    equipment_type as type,
    manufacturer,
    model,
    serial_number as serial,
    installation_date as installed,
    warranty_expiry as warranty,
    status,
    location_x,
    location_y,
    location_z,
    metadata,
    created_at,
    updated_at
FROM equipment;

-- Add composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_equipment_building_type ON equipment(building_id, equipment_type);
CREATE INDEX IF NOT EXISTS idx_equipment_floor_status ON equipment(floor_id, status);

-- Ensure foreign key constraints are enabled (SQLite specific)
PRAGMA foreign_keys = ON;