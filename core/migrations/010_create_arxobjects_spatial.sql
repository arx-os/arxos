-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing table if it exists
DROP TABLE IF EXISTS arx_objects CASCADE;

-- Create ArxObjects table with PostGIS geometry
CREATE TABLE arx_objects (
    id BIGSERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Object identification
    type VARCHAR(50) NOT NULL,
    system VARCHAR(50) NOT NULL,
    
    -- Spatial data (using PostGIS)
    geom GEOMETRY(PointZ, 4326),  -- 3D point with geographic coordinates
    
    -- Additional position data for fast queries
    x DOUBLE PRECISION,
    y DOUBLE PRECISION, 
    z DOUBLE PRECISION DEFAULT 0,
    
    -- Dimensions in millimeters
    width INTEGER DEFAULT 100,
    height INTEGER DEFAULT 100,
    depth INTEGER DEFAULT 100,
    
    -- Rotation in degrees
    rotation_z DOUBLE PRECISION DEFAULT 0,
    
    -- Scale visibility range (fractal levels 0-9)
    scale_min INTEGER DEFAULT 0,
    scale_max INTEGER DEFAULT 10,
    
    -- Building hierarchy
    building_id INTEGER,
    floor_id INTEGER,
    room_id INTEGER,
    
    -- Metadata
    properties JSONB DEFAULT '{}',
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    serial_number VARCHAR(255),
    
    -- Confidence scoring (0.0 to 1.0)
    confidence DOUBLE PRECISION DEFAULT 1.0,
    extraction_method VARCHAR(50), -- 'manual', 'ai', 'lidar', 'pdf'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT valid_scale CHECK (scale_min >= 0 AND scale_min <= scale_max AND scale_max <= 10)
);

-- Create spatial index for geographic queries
CREATE INDEX idx_arx_objects_geom ON arx_objects USING GIST(geom);

-- Create standard indexes
CREATE INDEX idx_arx_objects_position ON arx_objects(x, y, z);
CREATE INDEX idx_arx_objects_scale ON arx_objects(scale_min, scale_max);
CREATE INDEX idx_arx_objects_type ON arx_objects(type);
CREATE INDEX idx_arx_objects_system ON arx_objects(system);
CREATE INDEX idx_arx_objects_building ON arx_objects(building_id, floor_id);
CREATE INDEX idx_arx_objects_confidence ON arx_objects(confidence);
CREATE INDEX idx_arx_objects_uuid ON arx_objects(uuid);

-- Create trigger to update geom when x,y,z change
CREATE OR REPLACE FUNCTION update_geom_from_xyz()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.x IS NOT NULL AND NEW.y IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.x, NEW.y, COALESCE(NEW.z, 0)), 4326);
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_arxobject_geom
    BEFORE INSERT OR UPDATE ON arx_objects
    FOR EACH ROW
    EXECUTE FUNCTION update_geom_from_xyz();

-- Create tile cache table
CREATE TABLE IF NOT EXISTS arx_tiles (
    zoom INTEGER,
    x INTEGER,
    y INTEGER,
    data JSONB,
    object_count INTEGER,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (zoom, x, y)
);

CREATE INDEX idx_arx_tiles_expires ON arx_tiles(expires_at);

-- Buildings table
CREATE TABLE IF NOT EXISTS buildings (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    floors INTEGER,
    total_area DOUBLE PRECISION,
    geom GEOMETRY(Polygon, 4326),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Floors table
CREATE TABLE IF NOT EXISTS floors (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id),
    floor_number INTEGER,
    name VARCHAR(255),
    height DOUBLE PRECISION,
    area DOUBLE PRECISION,
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    floor_id INTEGER REFERENCES floors(id),
    name VARCHAR(255),
    type VARCHAR(50),
    area DOUBLE PRECISION,
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to get objects within a bounding box
CREATE OR REPLACE FUNCTION get_objects_in_tile(
    p_zoom INTEGER,
    p_tile_x INTEGER, 
    p_tile_y INTEGER
) RETURNS TABLE (
    id BIGINT,
    uuid UUID,
    type VARCHAR,
    system VARCHAR,
    x DOUBLE PRECISION,
    y DOUBLE PRECISION,
    z DOUBLE PRECISION,
    width INTEGER,
    height INTEGER,
    properties JSONB
) AS $$
DECLARE
    tile_size DOUBLE PRECISION;
    min_x DOUBLE PRECISION;
    max_x DOUBLE PRECISION;
    min_y DOUBLE PRECISION;
    max_y DOUBLE PRECISION;
BEGIN
    -- Calculate tile bounds (simplified, not true Web Mercator)
    tile_size := 256.0 * POWER(2, 10 - p_zoom);
    min_x := p_tile_x * tile_size;
    max_x := (p_tile_x + 1) * tile_size;
    min_y := p_tile_y * tile_size;
    max_y := (p_tile_y + 1) * tile_size;
    
    RETURN QUERY
    SELECT 
        ao.id,
        ao.uuid,
        ao.type,
        ao.system,
        ao.x,
        ao.y,
        ao.z,
        ao.width,
        ao.height,
        ao.properties
    FROM arx_objects ao
    WHERE 
        ao.x >= min_x AND ao.x <= max_x
        AND ao.y >= min_y AND ao.y <= max_y
        AND ao.scale_min <= p_zoom 
        AND ao.scale_max >= p_zoom
    ORDER BY ao.z, ao.id
    LIMIT 1000;
END;
$$ LANGUAGE plpgsql;

-- Insert demo data
INSERT INTO buildings (name, floors, total_area) VALUES
    ('Office Building A', 5, 50000),
    ('Hospital Complex', 8, 120000),
    ('Residential Tower', 20, 180000);

-- Insert demo ArxObjects for first building
DO $$
DECLARE
    building_id INTEGER := 1;
    floor_num INTEGER;
    room_num INTEGER;
    x_pos DOUBLE PRECISION;
    y_pos DOUBLE PRECISION;
BEGIN
    -- Create 5 floors with rooms and objects
    FOR floor_num IN 0..4 LOOP
        -- Create floor walls
        INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max, building_id, floor_id, confidence)
        VALUES
            ('wall', 'structural', 0, floor_num * 500, floor_num * 3000, 10000, 100, 4, 10, building_id, floor_num, 0.95),
            ('wall', 'structural', 0, floor_num * 500 + 4900, floor_num * 3000, 10000, 100, 4, 10, building_id, floor_num, 0.95),
            ('wall', 'structural', 0, floor_num * 500, floor_num * 3000, 100, 5000, 4, 10, building_id, floor_num, 0.95),
            ('wall', 'structural', 9900, floor_num * 500, floor_num * 3000, 100, 5000, 4, 10, building_id, floor_num, 0.95);
        
        -- Create rooms (4 per floor)
        FOR room_num IN 0..3 LOOP
            x_pos := (room_num % 2) * 5000 + 500;
            y_pos := floor_num * 500 + (room_num / 2) * 2500 + 500;
            
            -- Room boundary
            INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max, building_id, floor_id, room_id, confidence)
            VALUES
                ('room', 'structural', x_pos, y_pos, floor_num * 3000, 4000, 2000, 5, 10, building_id, floor_num, room_num, 0.92);
            
            -- Electrical outlet
            INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max, building_id, floor_id, room_id, confidence)
            VALUES
                ('outlet', 'electrical', x_pos + 200, y_pos + 200, floor_num * 3000, 150, 150, 6, 10, building_id, floor_num, room_num, 0.88);
            
            -- HVAC vent
            INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max, building_id, floor_id, room_id, confidence)
            VALUES
                ('vent', 'hvac', x_pos + 2000, y_pos + 1000, floor_num * 3000 + 2800, 400, 200, 6, 10, building_id, floor_num, room_num, 0.85);
            
            -- Door
            INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max, building_id, floor_id, room_id, confidence)
            VALUES
                ('door', 'structural', x_pos, y_pos + 1000, floor_num * 3000, 100, 900, 6, 10, building_id, floor_num, room_num, 0.94);
        END LOOP;
        
        -- Plumbing for bathrooms (one per floor)
        INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max, building_id, floor_id, confidence)
        VALUES
            ('pipe', 'plumbing', 4500, floor_num * 500 + 2000, floor_num * 3000, 50, 1000, 7, 10, building_id, floor_num, 0.82),
            ('fixture', 'plumbing', 4550, floor_num * 500 + 2100, floor_num * 3000, 300, 400, 7, 10, building_id, floor_num, 0.80);
    END LOOP;
END $$;

-- Add some structural columns
INSERT INTO arx_objects (type, system, x, y, z, width, height, scale_min, scale_max, building_id, confidence)
SELECT 
    'column', 
    'structural',
    x * 2500 + 1250,
    y * 2500 + 1250,
    0,
    300,
    300,
    5,
    10,
    1,
    0.96
FROM generate_series(0, 3) x
CROSS JOIN generate_series(0, 1) y;

-- Count total objects
SELECT COUNT(*) as total_objects FROM arx_objects;

-- Grant permissions (adjust as needed)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;