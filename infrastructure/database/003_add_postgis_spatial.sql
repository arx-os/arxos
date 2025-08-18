-- Enable PostGIS extension for spatial features
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Add spatial columns to arx_objects table
ALTER TABLE arx_objects 
ADD COLUMN IF NOT EXISTS geom GEOMETRY(PointZ, 4326),
ADD COLUMN IF NOT EXISTS bounds GEOMETRY(Polygon, 4326),
ADD COLUMN IF NOT EXISTS scale_min INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS scale_max INTEGER DEFAULT 10,
ADD COLUMN IF NOT EXISTS z_order INTEGER DEFAULT 0;

-- Create spatial indexes for performance
CREATE INDEX IF NOT EXISTS idx_arx_objects_geom 
ON arx_objects USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_arx_objects_bounds 
ON arx_objects USING GIST (bounds);

CREATE INDEX IF NOT EXISTS idx_arx_objects_scale 
ON arx_objects (scale_min, scale_max);

CREATE INDEX IF NOT EXISTS idx_arx_objects_z_order 
ON arx_objects (z_order);

-- Create tile cache table for Google Maps-like loading
CREATE TABLE IF NOT EXISTS arx_tiles (
    id BIGSERIAL PRIMARY KEY,
    zoom INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    data JSONB,
    object_count INTEGER DEFAULT 0,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(zoom, x, y)
);

CREATE INDEX IF NOT EXISTS idx_arx_tiles_coords 
ON arx_tiles (zoom, x, y);

CREATE INDEX IF NOT EXISTS idx_arx_tiles_expires 
ON arx_tiles (expires_at);

-- Create spatial relationships table
CREATE TABLE IF NOT EXISTS arx_spatial_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES arx_objects(id) ON DELETE CASCADE,
    target_id BIGINT REFERENCES arx_objects(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- contains, adjacent_to, above, below
    distance FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_id, target_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_spatial_rel_source 
ON arx_spatial_relationships (source_id);

CREATE INDEX IF NOT EXISTS idx_spatial_rel_target 
ON arx_spatial_relationships (target_id);

-- Function to update geometry from x, y, z coordinates
CREATE OR REPLACE FUNCTION update_arx_object_geometry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.x IS NOT NULL AND NEW.y IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.x, NEW.y, COALESCE(NEW.z, 0)), 4326);
        
        -- Create bounds based on width/height if available
        IF NEW.width IS NOT NULL AND NEW.height IS NOT NULL THEN
            NEW.bounds = ST_SetSRID(ST_MakeEnvelope(
                NEW.x - NEW.width/2.0,
                NEW.y - NEW.height/2.0,
                NEW.x + NEW.width/2.0,
                NEW.y + NEW.height/2.0,
                4326
            ), 4326);
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update geometry
CREATE TRIGGER update_geom_trigger
BEFORE INSERT OR UPDATE ON arx_objects
FOR EACH ROW
EXECUTE FUNCTION update_arx_object_geometry();

-- Function to find objects within a bounding box at a specific scale
CREATE OR REPLACE FUNCTION get_objects_in_bounds(
    min_lon FLOAT,
    min_lat FLOAT,
    max_lon FLOAT,
    max_lat FLOAT,
    scale INTEGER
)
RETURNS TABLE (
    id BIGINT,
    uuid VARCHAR,
    type VARCHAR,
    system VARCHAR,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    confidence JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.uuid,
        o.type,
        o.system,
        ST_X(o.geom) as x,
        ST_Y(o.geom) as y,
        ST_Z(o.geom) as z,
        o.confidence
    FROM arx_objects o
    WHERE 
        o.geom && ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        AND o.scale_min <= scale 
        AND o.scale_max >= scale
    ORDER BY o.z_order, o.id
    LIMIT 1000;
END;
$$ LANGUAGE plpgsql;

-- Function to find rooms containing a point
CREATE OR REPLACE FUNCTION get_room_at_point(
    lon FLOAT,
    lat FLOAT,
    floor_level INTEGER DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    uuid VARCHAR,
    name VARCHAR,
    floor INTEGER,
    area FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.uuid,
        o.data->>'name' as name,
        (o.data->>'floor')::INTEGER as floor,
        ST_Area(o.bounds) as area
    FROM arx_objects o
    WHERE 
        o.type = 'room'
        AND o.bounds IS NOT NULL
        AND ST_Contains(o.bounds, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
        AND (floor_level IS NULL OR (o.data->>'floor')::INTEGER = floor_level)
    ORDER BY ST_Area(o.bounds) ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to find adjacent objects
CREATE OR REPLACE FUNCTION find_adjacent_objects(
    object_id BIGINT,
    max_distance FLOAT DEFAULT 5.0
)
RETURNS TABLE (
    id BIGINT,
    type VARCHAR,
    distance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o2.id,
        o2.type,
        ST_Distance(o1.geom, o2.geom) as distance
    FROM arx_objects o1, arx_objects o2
    WHERE 
        o1.id = object_id
        AND o2.id != object_id
        AND ST_DWithin(o1.geom, o2.geom, max_distance)
    ORDER BY ST_Distance(o1.geom, o2.geom)
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate room boundaries from walls
CREATE OR REPLACE FUNCTION calculate_room_from_walls(
    wall_ids BIGINT[]
)
RETURNS GEOMETRY AS $$
DECLARE
    wall_geoms GEOMETRY[];
    room_polygon GEOMETRY;
BEGIN
    -- Collect wall geometries
    SELECT ARRAY_AGG(geom) INTO wall_geoms
    FROM arx_objects
    WHERE id = ANY(wall_ids) AND type = 'wall';
    
    -- Create polygon from wall lines
    -- This is simplified - production would need more sophisticated algorithm
    IF array_length(wall_geoms, 1) > 2 THEN
        room_polygon = ST_ConvexHull(ST_Collect(wall_geoms));
    END IF;
    
    RETURN room_polygon;
END;
$$ LANGUAGE plpgsql;

-- Add sample data for testing
INSERT INTO arx_objects (uuid, type, system, x, y, z, scale_min, scale_max, confidence)
VALUES 
    ('test-wall-1', 'wall', 'structural', -122.4194, 37.7749, 0, 6, 10, '{"overall": 0.85}'),
    ('test-door-1', 'door', 'architectural', -122.4194, 37.7750, 0, 7, 10, '{"overall": 0.75}'),
    ('test-room-1', 'room', 'spatial', -122.4195, 37.7749, 0, 5, 9, '{"overall": 0.90}')
ON CONFLICT (uuid) DO NOTHING;