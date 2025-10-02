-- Create components table for universal building components
CREATE TABLE IF NOT EXISTS components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    path VARCHAR(500) NOT NULL UNIQUE,
    location_json JSONB NOT NULL DEFAULT '{}',
    properties_json JSONB NOT NULL DEFAULT '{}',
    relations_json JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_components_type ON components(type);
CREATE INDEX IF NOT EXISTS idx_components_status ON components(status);
CREATE INDEX IF NOT EXISTS idx_components_path ON components(path);
CREATE INDEX IF NOT EXISTS idx_components_created_by ON components(created_by);
CREATE INDEX IF NOT EXISTS idx_components_created_at ON components(created_at);

-- Create GIN indexes for JSON fields
CREATE INDEX IF NOT EXISTS idx_components_location_gin ON components USING GIN(location_json);
CREATE INDEX IF NOT EXISTS idx_components_properties_gin ON components USING GIN(properties_json);
CREATE INDEX IF NOT EXISTS idx_components_relations_gin ON components USING GIN(relations_json);

-- Create spatial index for location queries (if PostGIS is available)
-- This will be created only if PostGIS extension is available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        -- Create spatial index for 3D coordinates
        CREATE INDEX IF NOT EXISTS idx_components_location_spatial 
        ON components USING GIST(
            ST_SetSRID(
                ST_MakePoint(
                    (location_json->>'x')::float, 
                    (location_json->>'y')::float, 
                    (location_json->>'z')::float
                ), 
                4326
            )
        );
    END IF;
END $$;

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_components_type_status ON components(type, status);
CREATE INDEX IF NOT EXISTS idx_components_building_floor ON components(
    (location_json->>'building'), 
    (location_json->>'floor')
);

-- Add constraints
ALTER TABLE components ADD CONSTRAINT chk_component_type 
    CHECK (type IN (
        'hvac_unit', 'damper', 'thermostat', 'vent',
        'electrical_panel', 'outlet', 'switch', 'light',
        'faucet', 'toilet', 'pipe', 'valve',
        'fire_detector', 'sprinkler', 'fire_alarm',
        'door', 'lock', 'card_reader',
        'generic', 'food_item', 'furniture', 'equipment'
    ));

ALTER TABLE components ADD CONSTRAINT chk_component_status 
    CHECK (status IN ('active', 'inactive', 'maintenance', 'failed', 'unknown'));

ALTER TABLE components ADD CONSTRAINT chk_component_path 
    CHECK (path LIKE '/%');

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_components_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_components_updated_at
    BEFORE UPDATE ON components
    FOR EACH ROW
    EXECUTE FUNCTION update_components_updated_at();

-- Add comments for documentation
COMMENT ON TABLE components IS 'Universal building components table - stores any physical element in a building';
COMMENT ON COLUMN components.id IS 'Unique identifier for the component';
COMMENT ON COLUMN components.name IS 'Human-readable name of the component';
COMMENT ON COLUMN components.type IS 'Type of component (hvac_unit, electrical_panel, etc.)';
COMMENT ON COLUMN components.path IS 'Universal path like /B1/3/CONF-301/HVAC/UNIT-01';
COMMENT ON COLUMN components.location_json IS 'Spatial coordinates and location metadata';
COMMENT ON COLUMN components.properties_json IS 'Type-specific properties and configuration';
COMMENT ON COLUMN components.relations_json IS 'Relationships to other components';
COMMENT ON COLUMN components.status IS 'Operational status of the component';
COMMENT ON COLUMN components.version IS 'Version of the component definition';
COMMENT ON COLUMN components.created_by IS 'User who created the component';
COMMENT ON COLUMN components.updated_by IS 'User who last updated the component';
