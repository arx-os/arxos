-- Initialize PostGIS extensions and ArxOS spatial schema
-- This script runs when the Docker container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create spatial reference system for building coordinates (millimeter precision)
-- Using a custom SRID 900913 for building-local coordinates
INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text)
VALUES (
    900913,
    'ARXOS',
    900913,
    'PROJCS["ArxOS Building Local",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Millimeter",0.001]]',
    '+proj=tmerc +lat_0=0 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=mm +no_defs'
) ON CONFLICT (srid) DO NOTHING;

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

CREATE TYPE IF NOT EXISTS equipment_status AS ENUM (
    'operational',
    'maintenance',
    'fault',
    'decommissioned',
    'planned'
);

CREATE TYPE IF NOT EXISTS equipment_type AS ENUM (
    'hvac',
    'electrical',
    'plumbing',
    'fire_safety',
    'security',
    'elevator',
    'lighting',
    'network',
    'structural',
    'other'
);

CREATE TYPE IF NOT EXISTS room_type AS ENUM (
    'office',
    'conference',
    'bathroom',
    'kitchen',
    'storage',
    'hallway',
    'lobby',
    'mechanical',
    'electrical',
    'it_room',
    'stairwell',
    'elevator_shaft',
    'other'
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Buildings table with spatial geometry
CREATE TABLE IF NOT EXISTS buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxos_id VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    geometry GEOMETRY(MULTIPOLYGON, 900913),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Floors table with level-based organization
CREATE TABLE IF NOT EXISTS floors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uuid VARCHAR(50) UNIQUE NOT NULL,
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    level INTEGER NOT NULL,
    elevation_mm INTEGER,  -- Height in millimeters from ground
    geometry GEOMETRY(POLYGON, 900913),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(building_id, level)
);

-- Rooms table with spatial boundaries
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uuid VARCHAR(50) UNIQUE NOT NULL,
    floor_id UUID REFERENCES floors(id) ON DELETE CASCADE,
    room_number VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    room_type room_type,
    geometry GEOMETRY(POLYGON, 900913),
    area_sqmm BIGINT,  -- Area in square millimeters
    height_mm INTEGER,  -- Height in millimeters
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Equipment table with precise 3D location
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uuid VARCHAR(50) UNIQUE NOT NULL,
    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    equipment_tag VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    equipment_type equipment_type NOT NULL,
    status equipment_status DEFAULT 'planned',
    location GEOMETRY(POINTZ, 900913),  -- 3D point with Z coordinate
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    serial_number VARCHAR(255),
    installed_date DATE,
    last_maintained TIMESTAMP WITH TIME ZONE,
    next_maintenance DATE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- IFC entities table for raw IFC data storage
CREATE TABLE IF NOT EXISTS ifc_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(50) UNIQUE NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    attributes JSONB NOT NULL,
    parent_id VARCHAR(50),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    geometry GEOMETRY(GEOMETRY, 900913),  -- Any geometry type
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Repository version tracking
CREATE TABLE IF NOT EXISTS repository_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    commit_hash VARCHAR(40) UNIQUE NOT NULL,
    message TEXT,
    author VARCHAR(255),
    changes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(building_id, version_number)
);

-- Import history for audit trail
CREATE TABLE IF NOT EXISTS import_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT,
    building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    entities_imported INTEGER,
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
) PARTITION BY RANGE (imported_at);

-- Export history for tracking generated files
CREATE TABLE IF NOT EXISTS export_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    format VARCHAR(50) NOT NULL,
    building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    floors_included INTEGER[],
    equipment_count INTEGER,
    file_size BIGINT,
    exported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
) PARTITION BY RANGE (exported_at);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to all tables
CREATE TRIGGER update_buildings_updated_at BEFORE UPDATE ON buildings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_floors_updated_at BEFORE UPDATE ON floors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_ifc_entities_updated_at BEFORE UPDATE ON ifc_entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE arxos TO arxos;
GRANT ALL ON SCHEMA public TO arxos;
GRANT ALL ON ALL TABLES IN SCHEMA public TO arxos;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO arxos;

-- Create test user for CI/CD
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'arxos_ci') THEN
        CREATE USER arxos_ci WITH PASSWORD 'ci_test_pass';
    END IF;
END $$;

GRANT CONNECT ON DATABASE arxos TO arxos_ci;
GRANT USAGE ON SCHEMA public TO arxos_ci;
GRANT CREATE ON SCHEMA public TO arxos_ci;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO arxos_ci;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostGIS initialization completed successfully';
    RAISE NOTICE 'PostGIS version: %', PostGIS_Version();
END $$;