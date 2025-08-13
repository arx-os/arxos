-- ArxObject Core Schema
-- This is the foundation of the entire Arxos system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create the main arxobjects table
CREATE TABLE IF NOT EXISTS arxobjects (
    -- Identity
    id VARCHAR(255) PRIMARY KEY, -- Format: "arx:building:floor:room:object"
    type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    system VARCHAR(50) NOT NULL, -- electrical, hvac, plumbing, etc.
    
    -- Hierarchy
    parent_id VARCHAR(255) REFERENCES arxobjects(id) ON DELETE CASCADE,
    child_ids TEXT[], -- Array of child IDs
    
    -- Spatial Location (millimeter precision)
    position_x DOUBLE PRECISION DEFAULT 0,
    position_y DOUBLE PRECISION DEFAULT 0,
    position_z DOUBLE PRECISION DEFAULT 0,
    
    -- Dimensions (millimeters)
    width DOUBLE PRECISION DEFAULT 0,
    height DOUBLE PRECISION DEFAULT 0,
    depth DOUBLE PRECISION DEFAULT 0,
    
    -- Rotation (degrees)
    rotation_x DOUBLE PRECISION DEFAULT 0,
    rotation_y DOUBLE PRECISION DEFAULT 0,
    rotation_z DOUBLE PRECISION DEFAULT 0,
    
    -- System Plane (for overlap resolution)
    system_plane_layer VARCHAR(50),
    system_plane_z_order INTEGER DEFAULT 0,
    system_plane_elevation VARCHAR(50), -- floor, wall, ceiling, above_ceiling
    
    -- Zoom Visibility
    scale_min DOUBLE PRECISION DEFAULT 0.1, -- Minimum zoom to show
    scale_max DOUBLE PRECISION DEFAULT 0.001, -- Maximum zoom to show
    optimal_scale DOUBLE PRECISION DEFAULT 0.01, -- Best viewing zoom
    
    -- Visual Representation
    svg_path TEXT,
    style TEXT,
    icon VARCHAR(10), -- Emoji or symbol for low zoom
    
    -- Symbol Recognition
    symbol_id VARCHAR(255), -- Reference to symbol library
    source VARCHAR(50), -- pdf, photo, lidar, manual, ifc
    confidence DOUBLE PRECISION DEFAULT 1.0,
    
    -- Properties (flexible JSON)
    properties JSONB DEFAULT '{}',
    
    -- Contribution Tracking
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    bilt_reward DOUBLE PRECISION DEFAULT 0,
    
    -- Version Control
    version INTEGER DEFAULT 1,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    verified BOOLEAN DEFAULT FALSE,
    
    -- Search
    tags TEXT[]
);

-- Create indexes for performance
CREATE INDEX idx_arxobjects_parent ON arxobjects(parent_id);
CREATE INDEX idx_arxobjects_system ON arxobjects(system);
CREATE INDEX idx_arxobjects_type ON arxobjects(type);
CREATE INDEX idx_arxobjects_position ON arxobjects(position_x, position_y);
CREATE INDEX idx_arxobjects_scale ON arxobjects(scale_min, scale_max);
CREATE INDEX idx_arxobjects_active ON arxobjects(active);
CREATE INDEX idx_arxobjects_tags ON arxobjects USING GIN(tags);
CREATE INDEX idx_arxobjects_properties ON arxobjects USING GIN(properties);

-- Create spatial index using PostGIS
CREATE INDEX idx_arxobjects_spatial ON arxobjects 
    USING GIST (ST_MakePoint(position_x, position_y, position_z));

-- Connections table (many-to-many relationships)
CREATE TABLE IF NOT EXISTS arxobject_connections (
    id SERIAL PRIMARY KEY,
    from_id VARCHAR(255) NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
    to_id VARCHAR(255) NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
    connection_type VARCHAR(100) NOT NULL, -- electrical_feed, control, data, physical
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(from_id, to_id, connection_type)
);

CREATE INDEX idx_connections_from ON arxobject_connections(from_id);
CREATE INDEX idx_connections_to ON arxobject_connections(to_id);

-- Overlaps table (objects at same X,Y position)
CREATE TABLE IF NOT EXISTS arxobject_overlaps (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(255) NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
    object_id VARCHAR(255) NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
    relationship VARCHAR(50), -- mounted_on, inside, adjacent, controls
    
    UNIQUE(source_id, object_id)
);

CREATE INDEX idx_overlaps_source ON arxobject_overlaps(source_id);
CREATE INDEX idx_overlaps_object ON arxobject_overlaps(object_id);

-- History table (audit trail)
CREATE TABLE IF NOT EXISTS arxobject_history (
    id SERIAL PRIMARY KEY,
    object_id VARCHAR(255) NOT NULL REFERENCES arxobjects(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL, -- created, updated, verified, deleted
    description TEXT,
    old_values JSONB,
    new_values JSONB,
    bilt_reward DOUBLE PRECISION DEFAULT 0
);

CREATE INDEX idx_history_object ON arxobject_history(object_id);
CREATE INDEX idx_history_user ON arxobject_history(user_id);
CREATE INDEX idx_history_timestamp ON arxobject_history(timestamp DESC);

-- Function to automatically update child_ids when parent_id is set
CREATE OR REPLACE FUNCTION update_parent_children() RETURNS TRIGGER AS $$
BEGIN
    -- Remove from old parent's children
    IF OLD.parent_id IS NOT NULL AND OLD.parent_id != NEW.parent_id THEN
        UPDATE arxobjects 
        SET child_ids = array_remove(child_ids, NEW.id)
        WHERE id = OLD.parent_id;
    END IF;
    
    -- Add to new parent's children
    IF NEW.parent_id IS NOT NULL THEN
        UPDATE arxobjects 
        SET child_ids = array_append(
            COALESCE(child_ids, ARRAY[]::TEXT[]), 
            NEW.id
        )
        WHERE id = NEW.parent_id 
        AND NOT (NEW.id = ANY(COALESCE(child_ids, ARRAY[]::TEXT[])));
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_parent_children
    AFTER INSERT OR UPDATE OF parent_id ON arxobjects
    FOR EACH ROW
    EXECUTE FUNCTION update_parent_children();

-- Function to detect overlapping objects
CREATE OR REPLACE FUNCTION detect_overlaps(
    obj_id VARCHAR(255),
    threshold DOUBLE PRECISION DEFAULT 50.0 -- 50mm threshold
) RETURNS TABLE(overlapping_id VARCHAR(255), distance DOUBLE PRECISION) AS $$
DECLARE
    obj_x DOUBLE PRECISION;
    obj_y DOUBLE PRECISION;
    obj_z DOUBLE PRECISION;
BEGIN
    -- Get the object's position
    SELECT position_x, position_y, position_z 
    INTO obj_x, obj_y, obj_z
    FROM arxobjects 
    WHERE id = obj_id;
    
    -- Find overlapping objects
    RETURN QUERY
    SELECT 
        a.id,
        sqrt(
            power(a.position_x - obj_x, 2) + 
            power(a.position_y - obj_y, 2) +
            power(a.position_z - obj_z, 2)
        ) as dist
    FROM arxobjects a
    WHERE a.id != obj_id
        AND a.active = true
        AND sqrt(
            power(a.position_x - obj_x, 2) + 
            power(a.position_y - obj_y, 2)
        ) < threshold
    ORDER BY dist;
END;
$$ LANGUAGE plpgsql;

-- Function to get objects at a specific zoom level and viewport
CREATE OR REPLACE FUNCTION get_objects_at_scale(
    scale DOUBLE PRECISION,
    viewport_min_x DOUBLE PRECISION,
    viewport_min_y DOUBLE PRECISION,
    viewport_max_x DOUBLE PRECISION,
    viewport_max_y DOUBLE PRECISION,
    limit_count INTEGER DEFAULT 10000
) RETURNS TABLE(object_id VARCHAR(255)) AS $$
BEGIN
    RETURN QUERY
    SELECT id
    FROM arxobjects
    WHERE position_x BETWEEN viewport_min_x AND viewport_max_x
        AND position_y BETWEEN viewport_min_y AND viewport_max_y
        AND scale_min >= scale
        AND scale_max <= scale
        AND active = true
    ORDER BY system_plane_z_order, optimal_scale DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE arxobjects IS 'Core ArxObject table - the DNA of building infrastructure';
COMMENT ON COLUMN arxobjects.id IS 'Hierarchical ID format: arx:building:floor:room:object';
COMMENT ON COLUMN arxobjects.system IS 'Building system: electrical, hvac, plumbing, fire_protection, etc.';
COMMENT ON COLUMN arxobjects.scale_min IS 'Minimum zoom level where object is visible (100=campus, 0.001=component)';
COMMENT ON COLUMN arxobjects.bilt_reward IS 'Total BILT tokens earned for contributions to this object';