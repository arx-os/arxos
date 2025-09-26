-- Migration 008: Spatial Structure Tables
-- This migration adds spatial structure tables for buildings and equipment

-- Create spatial structure table for building hierarchy
CREATE TABLE IF NOT EXISTS spatial_structure (
    id VARCHAR(255) PRIMARY KEY,
    building_id VARCHAR(255) NOT NULL,
    path VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'floor', 'room', 'zone', etc.
    name VARCHAR(255) NOT NULL,
    parent_id VARCHAR(255),
    level INTEGER DEFAULT 0,
    geometry GEOMETRY,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create equipment spatial table for spatial queries
CREATE TABLE IF NOT EXISTS equipment_spatial (
    id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(255) NOT NULL,
    position JSONB,
    path VARCHAR(500) NOT NULL,
    geometry GEOMETRY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(equipment_id)
);

-- Create indexes for spatial queries
CREATE INDEX IF NOT EXISTS idx_spatial_structure_building_id ON spatial_structure(building_id);
CREATE INDEX IF NOT EXISTS idx_spatial_structure_path ON spatial_structure(path);
CREATE INDEX IF NOT EXISTS idx_spatial_structure_type ON spatial_structure(type);
CREATE INDEX IF NOT EXISTS idx_spatial_structure_parent_id ON spatial_structure(parent_id);

CREATE INDEX IF NOT EXISTS idx_equipment_spatial_equipment_id ON equipment_spatial(equipment_id);
CREATE INDEX IF NOT EXISTS idx_equipment_spatial_path ON equipment_spatial(path);

-- Create spatial indexes for geometry columns
CREATE INDEX IF NOT EXISTS idx_spatial_structure_geometry ON spatial_structure USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_equipment_spatial_geometry ON equipment_spatial USING GIST (geometry);

-- Create updated_at triggers
CREATE TRIGGER update_spatial_structure_updated_at 
    BEFORE UPDATE ON spatial_structure 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_spatial_updated_at 
    BEFORE UPDATE ON equipment_spatial 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE spatial_structure IS 'Hierarchical spatial structure for buildings (floors, rooms, zones)';
COMMENT ON TABLE equipment_spatial IS 'Spatial positioning and geometry for equipment';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON spatial_structure TO arxos_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON equipment_spatial TO arxos_user;
GRANT USAGE, SELECT ON SEQUENCE equipment_spatial_id_seq TO arxos_user;
