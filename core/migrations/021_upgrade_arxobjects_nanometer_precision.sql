-- 021_upgrade_arxobjects_nanometer_precision.sql
-- Migration: Upgrade ArxObject coordinates to int64 nanometer precision
-- This enables zooming from campus scale down to circuit board traces

-- Add new columns for nanometer-precision coordinates
-- These will coexist with PostGIS geometry during transition
ALTER TABLE arx_objects 
    ADD COLUMN IF NOT EXISTS x_nano BIGINT,
    ADD COLUMN IF NOT EXISTS y_nano BIGINT,
    ADD COLUMN IF NOT EXISTS z_nano BIGINT,
    ADD COLUMN IF NOT EXISTS length_nano BIGINT,
    ADD COLUMN IF NOT EXISTS width_nano BIGINT,
    ADD COLUMN IF NOT EXISTS height_nano BIGINT,
    ADD COLUMN IF NOT EXISTS rotation_millideg INTEGER,
    ADD COLUMN IF NOT EXISTS scale_level SMALLINT;

-- Add comments explaining the units
COMMENT ON COLUMN arx_objects.x_nano IS 'X position in nanometers (1nm precision, ±9,223,372km range)';
COMMENT ON COLUMN arx_objects.y_nano IS 'Y position in nanometers (1nm precision, ±9,223,372km range)';
COMMENT ON COLUMN arx_objects.z_nano IS 'Z position in nanometers (1nm precision, ±9,223,372km range)';
COMMENT ON COLUMN arx_objects.length_nano IS 'Length in nanometers';
COMMENT ON COLUMN arx_objects.width_nano IS 'Width in nanometers';
COMMENT ON COLUMN arx_objects.height_nano IS 'Height in nanometers';
COMMENT ON COLUMN arx_objects.rotation_millideg IS 'Rotation in millidegrees (0.001 degree precision)';
COMMENT ON COLUMN arx_objects.scale_level IS 'Scale level for rendering optimization (0=circuit, 1=component, 2=room, 3=building, 4=campus)';

-- Migrate existing PostGIS geometry data to nanometer columns
-- Assuming existing geometry is in degrees (SRID 4326), convert to meters then nanometers
UPDATE arx_objects 
SET 
    x_nano = CAST(ST_X(geom) * 111319.5 * 1000000000 AS BIGINT),  -- degrees to meters to nanometers
    y_nano = CAST(ST_Y(geom) * 111319.5 * 1000000000 AS BIGINT),  -- approximate at equator
    z_nano = CAST(COALESCE(ST_Z(geom), 0) * 1000000000 AS BIGINT),
    length_nano = 1000000000,  -- Default 1 meter in nanometers
    width_nano = 1000000000,
    height_nano = 1000000000,
    rotation_millideg = 0,
    scale_level = CASE 
        WHEN type IN ('building', 'floor') THEN 3
        WHEN type IN ('wall', 'room', 'door', 'window') THEN 2
        WHEN type IN ('outlet', 'switch', 'fixture') THEN 1
        ELSE 2
    END
WHERE x_nano IS NULL;

-- Create indexes for efficient spatial queries at different scales
CREATE INDEX IF NOT EXISTS idx_arx_nano_spatial ON arx_objects (x_nano, y_nano, z_nano);
CREATE INDEX IF NOT EXISTS idx_arx_nano_scale ON arx_objects (scale_level, x_nano, y_nano);

-- Create a function to convert nanometers to other units
CREATE OR REPLACE FUNCTION nano_to_meters(nano BIGINT) 
RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN nano::DOUBLE PRECISION / 1000000000.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION nano_to_millimeters(nano BIGINT) 
RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN nano::DOUBLE PRECISION / 1000000.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION nano_to_micrometers(nano BIGINT) 
RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN nano::DOUBLE PRECISION / 1000.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create a function to convert from other units to nanometers
CREATE OR REPLACE FUNCTION meters_to_nano(meters DOUBLE PRECISION) 
RETURNS BIGINT AS $$
BEGIN
    RETURN CAST(meters * 1000000000.0 AS BIGINT);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION millimeters_to_nano(mm DOUBLE PRECISION) 
RETURNS BIGINT AS $$
BEGIN
    RETURN CAST(mm * 1000000.0 AS BIGINT);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION micrometers_to_nano(um DOUBLE PRECISION) 
RETURNS BIGINT AS $$
BEGIN
    RETURN CAST(um * 1000.0 AS BIGINT);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create a view that provides both coordinate systems
CREATE OR REPLACE VIEW arx_objects_with_units AS
SELECT 
    id,
    uuid,
    type,
    system,
    -- Nanometer coordinates (raw)
    x_nano,
    y_nano,
    z_nano,
    length_nano,
    width_nano,
    height_nano,
    -- Meter coordinates (computed)
    nano_to_meters(x_nano) as x_meters,
    nano_to_meters(y_nano) as y_meters,
    nano_to_meters(z_nano) as z_meters,
    nano_to_meters(length_nano) as length_meters,
    nano_to_meters(width_nano) as width_meters,
    nano_to_meters(height_nano) as height_meters,
    -- Millimeter coordinates (computed)
    nano_to_millimeters(x_nano) as x_mm,
    nano_to_millimeters(y_nano) as y_mm,
    nano_to_millimeters(z_nano) as z_mm,
    nano_to_millimeters(length_nano) as length_mm,
    nano_to_millimeters(width_nano) as width_mm,
    nano_to_millimeters(height_nano) as height_mm,
    -- Micrometer coordinates (computed for PCB scale)
    nano_to_micrometers(x_nano) as x_um,
    nano_to_micrometers(y_nano) as y_um,
    nano_to_micrometers(z_nano) as z_um,
    nano_to_micrometers(length_nano) as length_um,
    nano_to_micrometers(width_nano) as width_um,
    nano_to_micrometers(height_nano) as height_um,
    -- Other fields
    rotation_millideg,
    rotation_millideg::DOUBLE PRECISION / 1000.0 as rotation_degrees,
    scale_level,
    parent_id,
    scale_min,
    scale_max,
    status,
    properties,
    created_at,
    updated_at,
    geom
FROM arx_objects;

-- Add new object types for hardware/IoT and circuit levels
DO $$ 
BEGIN
    -- Check if we need to add new types to any enum or reference table
    -- This is placeholder as the current schema uses VARCHAR for type
    NULL;
END $$;