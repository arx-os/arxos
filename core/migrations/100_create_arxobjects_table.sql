-- Create ArxObjects table for PDF ingestion
-- This migration adds support for storing extracted building objects

-- Create buildings table if not exists (for PDF uploads)
CREATE TABLE IF NOT EXISTS pdf_buildings (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255),
    address TEXT,
    total_floors INTEGER DEFAULT 0,
    total_objects INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Create arx_objects table for storing extracted objects
CREATE TABLE IF NOT EXISTS arx_objects (
    id BIGINT NOT NULL,
    building_id VARCHAR(36) REFERENCES pdf_buildings(id) ON DELETE CASCADE,
    object_type SMALLINT NOT NULL,
    system_type SMALLINT NOT NULL,
    scale_level SMALLINT NOT NULL,
    x_nano BIGINT NOT NULL,  -- Nanometer precision
    y_nano BIGINT NOT NULL,
    z_nano BIGINT NOT NULL,
    length_nano BIGINT NOT NULL,
    width_nano BIGINT NOT NULL,
    height_nano BIGINT NOT NULL,
    type_flags BIGINT NOT NULL,
    rotation_pack BIGINT,
    metadata_id BIGINT,
    parent_id BIGINT,
    properties JSONB,
    geom geometry(PointZ, 4326),  -- PostGIS geometry
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, building_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_arx_objects_building ON arx_objects(building_id);
CREATE INDEX IF NOT EXISTS idx_arx_objects_type ON arx_objects(object_type);
CREATE INDEX IF NOT EXISTS idx_arx_objects_system ON arx_objects(system_type);
CREATE INDEX IF NOT EXISTS idx_arx_objects_parent ON arx_objects(parent_id);
CREATE INDEX IF NOT EXISTS idx_arx_objects_z ON arx_objects(z_nano);
CREATE INDEX IF NOT EXISTS idx_arx_objects_geom ON arx_objects USING GIST(geom);

-- Add comment
COMMENT ON TABLE arx_objects IS 'Stores building objects extracted from PDFs with nanometer precision';
COMMENT ON COLUMN arx_objects.x_nano IS 'X coordinate in nanometers (1nm precision, ±9,223km range)';
COMMENT ON COLUMN arx_objects.y_nano IS 'Y coordinate in nanometers';
COMMENT ON COLUMN arx_objects.z_nano IS 'Z coordinate in nanometers (elevation)';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON arx_objects TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON pdf_buildings TO arxos_api_user;