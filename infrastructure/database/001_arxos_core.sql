-- Arxos Core Schema: PostGIS-powered spatial database for building intelligence
-- This replaces the complex multi-file schema with a clean, focused design

-- Enable PostGIS if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables to start fresh
DROP TABLE IF EXISTS arx_connections CASCADE;
DROP TABLE IF EXISTS arx_objects CASCADE;
DROP TABLE IF EXISTS arx_tiles CASCADE;

-- Core ArxObject table with spatial indexing
CREATE TABLE arx_objects (
    id BIGSERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    
    -- Identity
    type VARCHAR(50) NOT NULL,           -- outlet, switch, panel, duct, etc.
    manufacturer VARCHAR(100),           -- Siemens, Carrier, Square D
    model VARCHAR(100),                   -- Specific model number
    serial_number VARCHAR(100),           -- Unique serial
    
    -- Spatial data (3D point with real-world coordinates)
    geom GEOMETRY(POINTZ, 4326) NOT NULL,
    width SMALLINT DEFAULT 0,             -- mm
    height SMALLINT DEFAULT 0,            -- mm
    depth SMALLINT DEFAULT 0,             -- mm
    rotation SMALLINT DEFAULT 0,          -- degrees
    
    -- Hierarchy
    parent_id BIGINT REFERENCES arx_objects(id) ON DELETE CASCADE,
    
    -- Scale visibility (fractal zoom levels)
    scale_min INTEGER NOT NULL DEFAULT 1,      -- Minimum scale to show
    scale_max INTEGER NOT NULL DEFAULT 10000000, -- Maximum scale to show
    
    -- System classification
    system VARCHAR(20) NOT NULL,          -- electrical, hvac, plumbing, structural
    subsystem VARCHAR(50),                 -- power, lighting, supply, return, etc.
    
    -- Rendering
    z_order INTEGER DEFAULT 0,             -- Draw order within scale
    style JSONB DEFAULT '{}',              -- Color, icon, etc.
    
    -- Properties and metadata
    properties JSONB DEFAULT '{}',         -- Flexible attributes
    tags TEXT[],                          -- Searchable tags
    
    -- Lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    installed_at TIMESTAMP WITH TIME ZONE,
    last_serviced TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, inactive, maintenance, failed
    condition FLOAT DEFAULT 1.0            -- 0.0 to 1.0 health score
);

-- Topology connections (what feeds what)
CREATE TABLE arx_connections (
    id BIGSERIAL PRIMARY KEY,
    from_id BIGINT NOT NULL REFERENCES arx_objects(id) ON DELETE CASCADE,
    to_id BIGINT NOT NULL REFERENCES arx_objects(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) NOT NULL,  -- power, data, fluid, air, structural
    properties JSONB DEFAULT '{}',         -- voltage, flow rate, capacity, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(from_id, to_id, connection_type)
);

-- Tile cache for Google Maps pattern
CREATE TABLE arx_tiles (
    zoom INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    data JSONB NOT NULL,
    object_count INTEGER DEFAULT 0,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 hour',
    
    PRIMARY KEY (zoom, x, y)
);

-- CRITICAL INDEXES for performance

-- Spatial index for viewport queries (most important!)
CREATE INDEX idx_arx_spatial ON arx_objects USING GIST (geom);

-- Scale-based filtering
CREATE INDEX idx_arx_scale ON arx_objects (scale_min, scale_max);
CREATE INDEX idx_arx_scale_system ON arx_objects (scale_min, scale_max, system);

-- System and type lookups
CREATE INDEX idx_arx_system ON arx_objects (system);
CREATE INDEX idx_arx_type ON arx_objects (type);
CREATE INDEX idx_arx_status ON arx_objects (status) WHERE status != 'active';

-- Hierarchy navigation
CREATE INDEX idx_arx_parent ON arx_objects (parent_id);

-- UUID lookups
CREATE INDEX idx_arx_uuid ON arx_objects (uuid);

-- Connection queries
CREATE INDEX idx_conn_from ON arx_connections (from_id);
CREATE INDEX idx_conn_to ON arx_connections (to_id);
CREATE INDEX idx_conn_type ON arx_connections (connection_type);

-- Tile expiration
CREATE INDEX idx_tile_expires ON arx_tiles (expires_at);

-- Helper function to get objects in a bounding box at a specific scale
CREATE OR REPLACE FUNCTION get_objects_in_bounds(
    min_lon FLOAT,
    min_lat FLOAT, 
    max_lon FLOAT,
    max_lat FLOAT,
    scale INTEGER
) RETURNS TABLE (
    id BIGINT,
    type VARCHAR,
    system VARCHAR,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    properties JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.type,
        o.system,
        ST_X(o.geom) as x,
        ST_Y(o.geom) as y,
        ST_Z(o.geom) as z,
        o.properties
    FROM arx_objects o
    WHERE 
        o.geom && ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        AND o.scale_min <= scale 
        AND o.scale_max >= scale
    ORDER BY o.z_order, o.id;
END;
$$ LANGUAGE plpgsql;

-- Helper function to calculate tile bounds (Web Mercator)
CREATE OR REPLACE FUNCTION tile_to_bounds(zoom INTEGER, x INTEGER, y INTEGER)
RETURNS TABLE (
    min_lon FLOAT,
    min_lat FLOAT,
    max_lon FLOAT,
    max_lat FLOAT
) AS $$
DECLARE
    n FLOAT;
BEGIN
    n := 2.0 ^ zoom;
    min_lon := x / n * 360.0 - 180.0;
    max_lon := (x + 1) / n * 360.0 - 180.0;
    max_lat := 180.0 / pi() * atan(sinh(pi() * (1 - 2 * y / n)));
    min_lat := 180.0 / pi() * atan(sinh(pi() * (1 - 2 * (y + 1) / n)));
    
    RETURN QUERY SELECT min_lon, min_lat, max_lon, max_lat;
END;
$$ LANGUAGE plpgsql;

-- Insert some sample data for testing
INSERT INTO arx_objects (type, system, geom, scale_min, scale_max, properties) VALUES
-- Building outline (visible at campus scale)
('building', 'structural', ST_SetSRID(ST_MakePoint(-73.9857, 40.7484, 0), 4326), 10000, 10000000, 
 '{"name": "Demo Building", "floors": 3, "area": 5000}'::jsonb),

-- Floors (visible at building scale)
('floor', 'structural', ST_SetSRID(ST_MakePoint(-73.9857, 40.7484, 0), 4326), 1000, 100000,
 '{"level": 1, "name": "Ground Floor", "height": 4.5}'::jsonb),
('floor', 'structural', ST_SetSRID(ST_MakePoint(-73.9857, 40.7484, 4.5), 4326), 1000, 100000,
 '{"level": 2, "name": "Second Floor", "height": 4.5}'::jsonb),

-- Rooms (visible at floor scale)
('room', 'structural', ST_SetSRID(ST_MakePoint(-73.9856, 40.7483, 0), 4326), 100, 10000,
 '{"number": "101", "name": "Lobby", "area": 200}'::jsonb),
('room', 'structural', ST_SetSRID(ST_MakePoint(-73.9855, 40.7483, 0), 4326), 100, 10000,
 '{"number": "102", "name": "Conference Room", "area": 50}'::jsonb),

-- Electrical components (visible at room scale)
('panel', 'electrical', ST_SetSRID(ST_MakePoint(-73.9856, 40.7483, 1.5), 4326), 10, 1000,
 '{"name": "EP-1", "voltage": 480, "amperage": 200, "circuits": 42}'::jsonb),
('outlet', 'electrical', ST_SetSRID(ST_MakePoint(-73.9855, 40.7483, 0.3), 4326), 1, 100,
 '{"type": "duplex", "voltage": 120, "circuit": 1}'::jsonb),
('outlet', 'electrical', ST_SetSRID(ST_MakePoint(-73.9855, 40.7483, 0.3), 4326), 1, 100,
 '{"type": "duplex", "voltage": 120, "circuit": 1}'::jsonb),

-- HVAC components
('diffuser', 'hvac', ST_SetSRID(ST_MakePoint(-73.9856, 40.7483, 3), 4326), 1, 100,
 '{"type": "supply", "size": "12x12", "cfm": 150}'::jsonb),
('thermostat', 'hvac', ST_SetSRID(ST_MakePoint(-73.9855, 40.7483, 1.5), 4326), 1, 100,
 '{"model": "Nest", "zone": "Zone-1"}'::jsonb),

-- Plumbing
('valve', 'plumbing', ST_SetSRID(ST_MakePoint(-73.9856, 40.7482, 0), 4326), 1, 100,
 '{"type": "shutoff", "size": "1 inch", "material": "brass"}'::jsonb);

-- Add some connections
INSERT INTO arx_connections (from_id, to_id, connection_type, properties) VALUES
(6, 7, 'power', '{"circuit": 1, "voltage": 120}'::jsonb),
(6, 8, 'power', '{"circuit": 1, "voltage": 120}'::jsonb);

-- Create a view for easy querying
CREATE OR REPLACE VIEW arx_objects_with_connections AS
SELECT 
    o.*,
    array_agg(DISTINCT c_from.to_id) FILTER (WHERE c_from.to_id IS NOT NULL) as feeds,
    array_agg(DISTINCT c_to.from_id) FILTER (WHERE c_to.from_id IS NOT NULL) as fed_by
FROM arx_objects o
LEFT JOIN arx_connections c_from ON c_from.from_id = o.id
LEFT JOIN arx_connections c_to ON c_to.to_id = o.id
GROUP BY o.id;