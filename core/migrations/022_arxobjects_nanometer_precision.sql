-- Migration: Convert ArxObjects to nanometer precision with intelligent confidence scoring
-- Version: 022
-- Description: Upgrades ArxObject storage for nanometer precision and multi-dimensional confidence

BEGIN;

-- Create new arx_objects table with nanometer precision
CREATE TABLE IF NOT EXISTS arx_objects_v2 (
    -- Identity
    id VARCHAR(255) PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,
    
    -- Spatial Position (nanometer precision - stored as BIGINT)
    x BIGINT NOT NULL DEFAULT 0,  -- Nanometers from origin
    y BIGINT NOT NULL DEFAULT 0,  -- Nanometers from origin  
    z BIGINT NOT NULL DEFAULT 0,  -- Nanometers from origin
    
    -- Dimensions (nanometers)
    width BIGINT NOT NULL DEFAULT 100000000,   -- 100mm default
    height BIGINT NOT NULL DEFAULT 100000000,  -- 100mm default
    depth BIGINT NOT NULL DEFAULT 100000000,   -- 100mm default
    
    -- Fractal Scale Levels (0-9)
    scale_min INTEGER NOT NULL DEFAULT 0 CHECK (scale_min >= 0 AND scale_min <= 9),
    scale_max INTEGER NOT NULL DEFAULT 9 CHECK (scale_max >= 0 AND scale_max <= 9),
    
    -- System Classification
    system VARCHAR(50) NOT NULL,
    
    -- Intelligent Properties
    properties JSONB DEFAULT '{}',
    
    -- Multi-dimensional Confidence
    confidence JSONB NOT NULL DEFAULT '{
        "classification": 0.5,
        "position": 0.5,
        "properties": 0.5,
        "relationships": 0.5,
        "overall": 0.5
    }',
    
    -- Hierarchy
    parent_id VARCHAR(255) REFERENCES arx_objects_v2(id) ON DELETE SET NULL,
    building_id BIGINT,
    floor_id BIGINT,
    room_id BIGINT,
    
    -- Metadata
    extraction_method VARCHAR(50),
    source VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    validated_by VARCHAR(255),
    
    -- Constraints
    CONSTRAINT valid_scale CHECK (scale_min <= scale_max),
    CONSTRAINT valid_confidence CHECK (
        (confidence->>'classification')::float >= 0 AND 
        (confidence->>'classification')::float <= 1 AND
        (confidence->>'position')::float >= 0 AND 
        (confidence->>'position')::float <= 1 AND
        (confidence->>'properties')::float >= 0 AND 
        (confidence->>'properties')::float <= 1 AND
        (confidence->>'relationships')::float >= 0 AND 
        (confidence->>'relationships')::float <= 1 AND
        (confidence->>'overall')::float >= 0 AND 
        (confidence->>'overall')::float <= 1
    )
);

-- Create indexes for performance
CREATE INDEX idx_arx_v2_uuid ON arx_objects_v2(uuid);
CREATE INDEX idx_arx_v2_type ON arx_objects_v2(type);
CREATE INDEX idx_arx_v2_system ON arx_objects_v2(system);
CREATE INDEX idx_arx_v2_position ON arx_objects_v2(x, y, z);
CREATE INDEX idx_arx_v2_scale ON arx_objects_v2(scale_min, scale_max);
CREATE INDEX idx_arx_v2_hierarchy ON arx_objects_v2(building_id, floor_id, room_id);
CREATE INDEX idx_arx_v2_parent ON arx_objects_v2(parent_id);
CREATE INDEX idx_arx_v2_confidence ON arx_objects_v2((confidence->>'overall'));
CREATE INDEX idx_arx_v2_validated ON arx_objects_v2(validated_at) WHERE validated_at IS NOT NULL;
CREATE INDEX idx_arx_v2_created ON arx_objects_v2(created_at);

-- Spatial index using PostGIS (convert nanometers to geometry point)
CREATE INDEX idx_arx_v2_spatial ON arx_objects_v2 
    USING GIST (
        ST_SetSRID(
            ST_MakePoint(
                x::float / 1000000000.0,  -- Convert nm to meters
                y::float / 1000000000.0,
                z::float / 1000000000.0
            ), 
            4326
        )
    );

-- Create relationships table
CREATE TABLE IF NOT EXISTS arx_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL REFERENCES arx_objects_v2(id) ON DELETE CASCADE,
    target_id VARCHAR(255) NOT NULL REFERENCES arx_objects_v2(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    properties JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Prevent duplicate relationships
    UNIQUE(source_id, target_id, type),
    -- Prevent self-relationships
    CHECK (source_id != target_id)
);

-- Create indexes for relationships
CREATE INDEX idx_rel_source ON arx_relationships(source_id);
CREATE INDEX idx_rel_target ON arx_relationships(target_id);
CREATE INDEX idx_rel_type ON arx_relationships(type);
CREATE INDEX idx_rel_confidence ON arx_relationships(confidence);

-- Migrate existing data if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'arx_objects') THEN
        INSERT INTO arx_objects_v2 (
            id, uuid, type, system,
            x, y, z,
            width, height, depth,
            scale_min, scale_max,
            building_id, floor_id, room_id,
            properties,
            confidence,
            extraction_method, source,
            created_at, updated_at, validated_at
        )
        SELECT 
            COALESCE('arx_' || uuid::text, 'arx_' || id::text),
            COALESCE(uuid, uuid_generate_v4()),
            type,
            system,
            (COALESCE(x, 0)::NUMERIC * 1000000)::BIGINT,  -- Convert mm to nm
            (COALESCE(y, 0)::NUMERIC * 1000000)::BIGINT,  -- Convert mm to nm
            (COALESCE(z, 0)::NUMERIC * 1000000)::BIGINT,  -- Convert mm to nm
            (COALESCE(width, 100)::NUMERIC * 1000000)::BIGINT,   -- Convert mm to nm
            (COALESCE(height, 100)::NUMERIC * 1000000)::BIGINT,  -- Convert mm to nm
            (COALESCE(depth, 100)::NUMERIC * 1000000)::BIGINT,   -- Convert mm to nm
            COALESCE(scale_min, 0),
            LEAST(COALESCE(scale_max, 9), 9),  -- Ensure max is 9
            building_id,
            floor_id,
            room_id,
            COALESCE(properties, '{}'::jsonb),
            jsonb_build_object(
                'classification', GREATEST(0, LEAST(1, COALESCE(confidence, 0.5))),
                'position', 0.8,  -- High confidence for existing positioned objects
                'properties', 0.7,
                'relationships', 0.5,
                'overall', GREATEST(0, LEAST(1, COALESCE(confidence, 0.5)))
            ),
            extraction_method,
            CASE 
                WHEN extraction_method IS NOT NULL THEN extraction_method
                ELSE 'legacy_migration'
            END,
            COALESCE(created_at, NOW()),
            COALESCE(updated_at, NOW()),
            validated_at
        FROM arx_objects;
        
        -- Log migration
        RAISE NOTICE 'Migrated % objects to nanometer precision', 
            (SELECT COUNT(*) FROM arx_objects);
    END IF;
END $$;

-- Create helper functions

-- Function to convert millimeters to nanometers
CREATE OR REPLACE FUNCTION mm_to_nm(mm FLOAT) RETURNS BIGINT AS $$
BEGIN
    RETURN (mm * 1000000)::BIGINT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to convert nanometers to millimeters
CREATE OR REPLACE FUNCTION nm_to_mm(nm BIGINT) RETURNS FLOAT AS $$
BEGIN
    RETURN nm::FLOAT / 1000000;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate overall confidence
CREATE OR REPLACE FUNCTION calculate_overall_confidence(conf JSONB) RETURNS FLOAT AS $$
DECLARE
    classification FLOAT;
    position FLOAT;
    properties FLOAT;
    relationships FLOAT;
BEGIN
    classification := (conf->>'classification')::FLOAT;
    position := (conf->>'position')::FLOAT;
    properties := (conf->>'properties')::FLOAT;
    relationships := (conf->>'relationships')::FLOAT;
    
    -- Weighted average
    RETURN (classification * 0.3 + position * 0.3 + properties * 0.2 + relationships * 0.2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to get objects in tile with nanometer precision
CREATE OR REPLACE FUNCTION get_objects_in_tile_v2(
    p_zoom INTEGER,
    p_tile_x INTEGER,
    p_tile_y INTEGER
) RETURNS TABLE (
    id VARCHAR,
    uuid UUID,
    type VARCHAR,
    system VARCHAR,
    x BIGINT,
    y BIGINT,
    z BIGINT,
    width BIGINT,
    height BIGINT,
    properties JSONB,
    confidence JSONB
) AS $$
DECLARE
    base_size_nm BIGINT := 10000000000000000; -- 10,000 km in nanometers
    tile_size_nm BIGINT;
    min_x_nm BIGINT;
    max_x_nm BIGINT;
    min_y_nm BIGINT;
    max_y_nm BIGINT;
BEGIN
    -- Calculate tile size for zoom level (each level is 10x smaller)
    tile_size_nm := base_size_nm / POWER(10, p_zoom)::BIGINT;
    
    -- Calculate bounds
    min_x_nm := p_tile_x::BIGINT * tile_size_nm;
    max_x_nm := min_x_nm + tile_size_nm;
    min_y_nm := p_tile_y::BIGINT * tile_size_nm;
    max_y_nm := min_y_nm + tile_size_nm;
    
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
        ao.properties,
        ao.confidence
    FROM arx_objects_v2 ao
    WHERE 
        ao.x >= min_x_nm AND ao.x <= max_x_nm
        AND ao.y >= min_y_nm AND ao.y <= max_y_nm
        AND ao.scale_min <= p_zoom 
        AND ao.scale_max >= p_zoom
    ORDER BY ao.z DESC, calculate_overall_confidence(ao.confidence) DESC
    LIMIT 1000;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_arx_objects_v2_updated_at
    BEFORE UPDATE ON arx_objects_v2
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Create view for backward compatibility (temporary)
CREATE OR REPLACE VIEW arx_objects_compat AS
SELECT 
    id::BIGINT as old_id,
    id,
    uuid,
    type,
    system,
    nm_to_mm(x) as x,
    nm_to_mm(y) as y,
    nm_to_mm(z) as z,
    nm_to_mm(width)::INTEGER as width,
    nm_to_mm(height)::INTEGER as height,
    nm_to_mm(depth)::INTEGER as depth,
    scale_min,
    scale_max,
    building_id,
    floor_id,
    room_id,
    properties,
    calculate_overall_confidence(confidence) as confidence,
    extraction_method,
    created_at,
    updated_at,
    validated_at
FROM arx_objects_v2;

-- Add comments for documentation
COMMENT ON TABLE arx_objects_v2 IS 'Intelligent ArxObjects with nanometer precision and multi-dimensional confidence scoring';
COMMENT ON COLUMN arx_objects_v2.x IS 'X position in nanometers from origin';
COMMENT ON COLUMN arx_objects_v2.y IS 'Y position in nanometers from origin';
COMMENT ON COLUMN arx_objects_v2.z IS 'Z position in nanometers from origin';
COMMENT ON COLUMN arx_objects_v2.confidence IS 'Multi-dimensional confidence score (classification, position, properties, relationships, overall)';
COMMENT ON TABLE arx_relationships IS 'Relationships between ArxObjects with confidence scoring';

COMMIT;

-- Verify migration
SELECT 
    'ArxObjects V2 Table Created' as status,
    COUNT(*) as object_count,
    AVG(calculate_overall_confidence(confidence)) as avg_confidence
FROM arx_objects_v2;