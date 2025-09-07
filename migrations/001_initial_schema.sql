-- ArxOS Database Schema
-- Buildings as queryable databases with hierarchical paths

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Buildings table
CREATE TABLE IF NOT EXISTS buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Building objects with filesystem-like paths
CREATE TABLE IF NOT EXISTS building_objects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    
    -- Hierarchical path (e.g., /electrical/circuits/2/outlet_2B)
    path TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    
    -- Physical location (meters)
    location_x DECIMAL(10,3),
    location_y DECIMAL(10,3), 
    location_z DECIMAL(10,3),
    
    -- Object state
    status VARCHAR(50) DEFAULT 'active',
    health INTEGER DEFAULT 100,
    needs_repair BOOLEAN DEFAULT FALSE,
    
    -- Connections
    parent_id UUID REFERENCES building_objects(id),
    
    -- Flexible properties as JSON
    properties JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(building_id, path)
);

-- Indexes for efficient queries
CREATE INDEX idx_building_objects_building_id ON building_objects(building_id);
CREATE INDEX idx_building_objects_path ON building_objects(path);
CREATE INDEX idx_building_objects_type ON building_objects(object_type);
CREATE INDEX idx_building_objects_status ON building_objects(status);
CREATE INDEX idx_building_objects_needs_repair ON building_objects(needs_repair);
CREATE INDEX idx_building_objects_parent ON building_objects(parent_id);

-- GIN index for JSONB queries
CREATE INDEX idx_building_objects_properties ON building_objects USING GIN (properties);
CREATE INDEX idx_building_objects_metrics ON building_objects USING GIN (metrics);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update timestamps
CREATE TRIGGER update_buildings_updated_at BEFORE UPDATE ON buildings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_building_objects_updated_at BEFORE UPDATE ON building_objects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();