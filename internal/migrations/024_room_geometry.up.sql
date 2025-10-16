-- Migration 024: Add room geometry support for PostGIS
-- Author: ArxOS Team
-- Date: 2025-01-15
-- Purpose: Add geometry column and width field to rooms table for spatial queries and TUI rendering

-- Start transaction
BEGIN;

-- Add width column to rooms table (height already exists)
ALTER TABLE rooms
ADD COLUMN IF NOT EXISTS width REAL;

-- Add geometry column for PostGIS spatial data
-- This will store the room boundary as a polygon
ALTER TABLE rooms
ADD COLUMN IF NOT EXISTS geometry GEOMETRY(POLYGON, 4326);

-- Add center point column for quick location queries
ALTER TABLE rooms
ADD COLUMN IF NOT EXISTS center_point GEOMETRY(POINT, 4326);

-- Create spatial indexes for fast geometry queries
CREATE INDEX IF NOT EXISTS idx_rooms_geometry 
ON rooms USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_rooms_center_point 
ON rooms USING GIST (center_point);

-- Add comments for documentation
COMMENT ON COLUMN rooms.width IS 'Room width in meters';
COMMENT ON COLUMN rooms.geometry IS 'Room boundary polygon in WGS84 (SRID 4326)';
COMMENT ON COLUMN rooms.center_point IS 'Room center point in WGS84 (SRID 4326)';

-- Create function to update center point from geometry
CREATE OR REPLACE FUNCTION update_room_center_point()
RETURNS TRIGGER AS $$
BEGIN
    -- Update center point from geometry if geometry exists
    IF NEW.geometry IS NOT NULL THEN
        NEW.center_point = ST_Centroid(NEW.geometry);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update center point
DROP TRIGGER IF EXISTS trigger_update_room_center_point ON rooms;
CREATE TRIGGER trigger_update_room_center_point
    BEFORE INSERT OR UPDATE OF geometry ON rooms
    FOR EACH ROW
    EXECUTE FUNCTION update_room_center_point();

-- Create function to calculate room area from geometry
CREATE OR REPLACE FUNCTION calculate_room_area_from_geometry(room_geometry GEOMETRY)
RETURNS REAL AS $$
BEGIN
    -- Return area in square meters (convert from degrees to meters)
    -- This is approximate - for precise calculations, use a projected coordinate system
    RETURN ST_Area(room_geometry::geography);
END;
$$ LANGUAGE plpgsql;

-- Create function to update room dimensions from geometry
CREATE OR REPLACE FUNCTION update_room_dimensions_from_geometry()
RETURNS TRIGGER AS $$
DECLARE
    room_bounds GEOMETRY;
    room_width REAL;
    room_height REAL;
BEGIN
    -- Only proceed if geometry exists
    IF NEW.geometry IS NOT NULL THEN
        -- Get bounding box
        room_bounds := ST_Envelope(NEW.geometry);
        
        -- Calculate width and height from bounding box
        room_width := ST_XMax(room_bounds) - ST_XMin(room_bounds);
        room_height := ST_YMax(room_bounds) - ST_YMin(room_bounds);
        
        -- Update dimensions (convert from degrees to meters approximately)
        -- For more precision, use a projected coordinate system
        NEW.width := room_width * 111320; -- Approximate meters per degree longitude
        NEW.height := room_height * 111320; -- Approximate meters per degree latitude
        
        -- Update area from geometry
        NEW.area := calculate_room_area_from_geometry(NEW.geometry);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update dimensions from geometry
DROP TRIGGER IF EXISTS trigger_update_room_dimensions ON rooms;
CREATE TRIGGER trigger_update_room_dimensions
    BEFORE INSERT OR UPDATE OF geometry ON rooms
    FOR EACH ROW
    EXECUTE FUNCTION update_room_dimensions_from_geometry();

-- Create spatial query functions for rooms

-- Function to find rooms within a bounding box
CREATE OR REPLACE FUNCTION get_rooms_in_bounds(
    min_x REAL,
    min_y REAL,
    max_x REAL,
    max_y REAL
)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    room_number TEXT,
    area REAL,
    width REAL,
    height REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.name,
        r.room_number,
        r.area,
        r.width,
        r.height
    FROM rooms r
    WHERE r.geometry && ST_MakeEnvelope(min_x, min_y, max_x, max_y, 4326)
    ORDER BY r.room_number;
END;
$$ LANGUAGE plpgsql;

-- Function to find rooms near a point
CREATE OR REPLACE FUNCTION get_rooms_near_point(
    point_x REAL,
    point_y REAL,
    radius_meters REAL DEFAULT 100.0
)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    room_number TEXT,
    distance_meters REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.name,
        r.room_number,
        ST_Distance(
            r.center_point::geography,
            ST_SetSRID(ST_MakePoint(point_x, point_y), 4326)::geography
        ) as distance_meters
    FROM rooms r
    WHERE ST_DWithin(
        r.center_point::geography,
        ST_SetSRID(ST_MakePoint(point_x, point_y), 4326)::geography,
        radius_meters
    )
    ORDER BY distance_meters;
END;
$$ LANGUAGE plpgsql;

-- Function to get room geometry as GeoJSON
CREATE OR REPLACE FUNCTION get_room_geojson(room_id TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT ST_AsGeoJSON(geometry)::JSON
    INTO result
    FROM rooms
    WHERE id = room_id AND geometry IS NOT NULL;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Commit transaction
COMMIT;
