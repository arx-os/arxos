-- Migration 008: Spatial Structure Tables (ROLLBACK)

-- Drop triggers
DROP TRIGGER IF EXISTS update_equipment_spatial_updated_at ON equipment_spatial;
DROP TRIGGER IF EXISTS update_spatial_structure_updated_at ON spatial_structure;

-- Drop tables
DROP TABLE IF EXISTS equipment_spatial;
DROP TABLE IF EXISTS spatial_structure;
