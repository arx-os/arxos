-- Rollback migration: Remove spatial anchor support

-- Drop views first
DROP VIEW IF EXISTS equipment_spatial;

-- Drop tables
DROP TABLE IF EXISTS spatial_zones;
DROP TABLE IF EXISTS spatial_anchors;