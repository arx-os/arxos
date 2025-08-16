-- Migration: 022_create_topology_tables.sql
-- Purpose: Create tables for building topology and BIM conversion
-- Author: Arxos Engineering
-- Date: 2024-01-15

BEGIN;

-- Create enum types for better type safety
CREATE TYPE topology.wall_type AS ENUM (
    'unknown',
    'exterior',
    'interior', 
    'structural',
    'partition',
    'curtain'
);

CREATE TYPE topology.room_function AS ENUM (
    'unknown',
    'classroom',
    'office',
    'corridor',
    'bathroom',
    'storage',
    'mechanical',
    'cafeteria',
    'gymnasium',
    'library',
    'laboratory',
    'auditorium',
    'lobby'
);

CREATE TYPE topology.building_type AS ENUM (
    'unknown',
    'educational',
    'healthcare',
    'office',
    'residential',
    'industrial',
    'retail'
);

CREATE TYPE topology.validation_status AS ENUM (
    'pending',
    'automatic',
    'manual',
    'approved',
    'rejected'
);

CREATE TYPE topology.processing_status AS ENUM (
    'processing',
    'pending_review',
    'in_review',
    'completed',
    'failed'
);

-- Building metadata table
CREATE TABLE topology.buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    building_type topology.building_type DEFAULT 'unknown',
    year_built INTEGER,
    total_area_nm2 BIGINT, -- Square nanometers
    num_floors INTEGER DEFAULT 1,
    
    -- Educational specific fields
    school_level VARCHAR(50), -- elementary, middle, high
    district_id VARCHAR(100),
    prototype_id VARCHAR(100), -- For standardized designs
    
    -- Spatial data
    boundary_polygon GEOMETRY(POLYGON, 4326),
    
    -- Processing metadata
    source_file VARCHAR(500),
    processing_status topology.processing_status DEFAULT 'pending',
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    validation_status topology.validation_status DEFAULT 'pending',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    -- Indexes for common queries
    INDEX idx_buildings_type (building_type),
    INDEX idx_buildings_district (district_id),
    INDEX idx_buildings_status (processing_status),
    INDEX idx_buildings_confidence (confidence_score)
);

-- Walls table with nanometer precision
CREATE TABLE topology.walls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID NOT NULL REFERENCES topology.buildings(id) ON DELETE CASCADE,
    
    -- Geometry in nanometers
    start_x BIGINT NOT NULL,
    start_y BIGINT NOT NULL,
    start_z BIGINT NOT NULL DEFAULT 0,
    end_x BIGINT NOT NULL,
    end_y BIGINT NOT NULL,
    end_z BIGINT NOT NULL DEFAULT 0,
    
    -- Dimensions in nanometers
    thickness BIGINT NOT NULL,
    height BIGINT NOT NULL,
    
    -- Properties
    wall_type topology.wall_type DEFAULT 'unknown',
    material VARCHAR(100),
    fire_rating VARCHAR(10),
    load_bearing BOOLEAN DEFAULT FALSE,
    
    -- Quality metrics
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    validation_status topology.validation_status DEFAULT 'pending',
    source VARCHAR(50), -- pdf_vector, image_raster, manual, lidar
    
    -- Spatial line for geometric operations
    geometry GEOMETRY(LINESTRING, 4326),
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_walls_building (building_id),
    INDEX idx_walls_type (wall_type),
    INDEX idx_walls_confidence (confidence_score),
    SPATIAL INDEX idx_walls_geometry (geometry)
);

-- Wall connections junction table
CREATE TABLE topology.wall_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wall_id_1 UUID NOT NULL REFERENCES topology.walls(id) ON DELETE CASCADE,
    wall_id_2 UUID NOT NULL REFERENCES topology.walls(id) ON DELETE CASCADE,
    
    -- Connection point in nanometers
    connection_x BIGINT NOT NULL,
    connection_y BIGINT NOT NULL,
    connection_z BIGINT NOT NULL DEFAULT 0,
    
    connection_type VARCHAR(50), -- corner, T-junction, cross
    angle_degrees DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure no duplicate connections
    UNIQUE(wall_id_1, wall_id_2),
    CHECK (wall_id_1 < wall_id_2), -- Enforce ordering to prevent duplicates
    
    INDEX idx_wall_connections_wall1 (wall_id_1),
    INDEX idx_wall_connections_wall2 (wall_id_2)
);

-- Rooms table
CREATE TABLE topology.rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID NOT NULL REFERENCES topology.buildings(id) ON DELETE CASCADE,
    floor_number INTEGER DEFAULT 0,
    
    -- Identification
    room_number VARCHAR(50),
    room_name VARCHAR(255),
    room_function topology.room_function DEFAULT 'unknown',
    
    -- Geometry
    footprint_polygon GEOMETRY(POLYGON, 4326) NOT NULL,
    centroid_x BIGINT NOT NULL,
    centroid_y BIGINT NOT NULL,
    centroid_z BIGINT NOT NULL DEFAULT 0,
    
    -- Dimensions in nanometers
    area_nm2 BIGINT NOT NULL,
    floor_height_nm BIGINT NOT NULL DEFAULT 0,
    ceiling_height_nm BIGINT NOT NULL,
    
    -- Properties
    occupancy_type VARCHAR(100),
    max_occupancy INTEGER,
    
    -- Quality metrics
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    validation_status topology.validation_status DEFAULT 'pending',
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_rooms_building (building_id),
    INDEX idx_rooms_function (room_function),
    INDEX idx_rooms_number (room_number),
    SPATIAL INDEX idx_rooms_footprint (footprint_polygon)
);

-- Room-Wall relationship table
CREATE TABLE topology.room_walls (
    room_id UUID NOT NULL REFERENCES topology.rooms(id) ON DELETE CASCADE,
    wall_id UUID NOT NULL REFERENCES topology.walls(id) ON DELETE CASCADE,
    wall_order INTEGER NOT NULL, -- Order of wall in room boundary
    
    PRIMARY KEY (room_id, wall_id),
    INDEX idx_room_walls_room (room_id),
    INDEX idx_room_walls_wall (wall_id)
);

-- Room adjacency table
CREATE TABLE topology.room_adjacency (
    room_id_1 UUID NOT NULL REFERENCES topology.rooms(id) ON DELETE CASCADE,
    room_id_2 UUID NOT NULL REFERENCES topology.rooms(id) ON DELETE CASCADE,
    shared_wall_id UUID REFERENCES topology.walls(id) ON DELETE SET NULL,
    adjacency_type VARCHAR(50), -- adjacent, above, below, diagonal
    
    PRIMARY KEY (room_id_1, room_id_2),
    CHECK (room_id_1 < room_id_2), -- Enforce ordering
    INDEX idx_adjacency_room1 (room_id_1),
    INDEX idx_adjacency_room2 (room_id_2)
);

-- Wall openings (doors, windows)
CREATE TABLE topology.openings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wall_id UUID NOT NULL REFERENCES topology.walls(id) ON DELETE CASCADE,
    
    -- Position along wall from start point (nanometers)
    position_nm BIGINT NOT NULL,
    width_nm BIGINT NOT NULL,
    height_nm BIGINT NOT NULL,
    sill_height_nm BIGINT DEFAULT 0,
    
    opening_type VARCHAR(50) NOT NULL, -- door, window, archway, service
    subtype VARCHAR(100), -- single, double, sliding, etc.
    
    -- Properties
    fire_rated BOOLEAN DEFAULT FALSE,
    accessible BOOLEAN DEFAULT FALSE,
    emergency_exit BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_openings_wall (wall_id),
    INDEX idx_openings_type (opening_type)
);

-- Processing results table
CREATE TABLE topology.processing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES topology.buildings(id) ON DELETE CASCADE,
    
    -- Input
    input_file VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64), -- SHA256 hash for deduplication
    
    -- Processing metrics
    raw_segments INTEGER,
    merged_segments INTEGER,
    detected_rooms INTEGER,
    detected_walls INTEGER,
    
    -- Quality metrics
    overall_confidence DECIMAL(3,2),
    semantic_confidence DECIMAL(3,2),
    geometric_confidence DECIMAL(3,2),
    
    -- Timing
    processing_time_ms INTEGER,
    stages_completed JSONB, -- Detailed timing per stage
    
    -- Status
    status topology.processing_status NOT NULL,
    error_message TEXT,
    requires_review BOOLEAN DEFAULT FALSE,
    
    -- Results
    validation_issues JSONB,
    semantic_analysis JSONB,
    clustering_stats JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_results_building (building_id),
    INDEX idx_results_status (status),
    INDEX idx_results_confidence (overall_confidence)
);

-- Validation issues table
CREATE TABLE topology.validation_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID NOT NULL REFERENCES topology.buildings(id) ON DELETE CASCADE,
    processing_result_id UUID REFERENCES topology.processing_results(id) ON DELETE CASCADE,
    
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- info, warning, error, critical
    description TEXT NOT NULL,
    
    -- Location
    location_x BIGINT,
    location_y BIGINT,
    
    -- Affected entities
    affected_walls UUID[] DEFAULT '{}',
    affected_rooms UUID[] DEFAULT '{}',
    
    -- Resolution
    suggested_fix TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_issues_building (building_id),
    INDEX idx_issues_severity (severity),
    INDEX idx_issues_resolved (resolved)
);

-- Manual corrections table for audit trail
CREATE TABLE topology.manual_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID NOT NULL REFERENCES topology.buildings(id) ON DELETE CASCADE,
    
    correction_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- wall, room, opening
    entity_id UUID NOT NULL,
    
    -- Change tracking
    before_state JSONB NOT NULL,
    after_state JSONB NOT NULL,
    
    -- Metadata
    reason TEXT,
    confidence DECIMAL(3,2),
    
    -- Audit
    corrected_by UUID NOT NULL REFERENCES users(id),
    corrected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_corrections_building (building_id),
    INDEX idx_corrections_entity (entity_type, entity_id),
    INDEX idx_corrections_user (corrected_by)
);

-- Semantic patterns table for learning
CREATE TABLE topology.semantic_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(100) NOT NULL,
    building_type topology.building_type NOT NULL,
    
    -- Pattern definition
    pattern_rules JSONB NOT NULL,
    min_confidence DECIMAL(3,2) DEFAULT 0.8,
    
    -- Statistics
    occurrences INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2),
    last_seen_building_id UUID REFERENCES topology.buildings(id),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Learning
    is_active BOOLEAN DEFAULT TRUE,
    created_from_building_ids UUID[] DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(pattern_name, building_type),
    INDEX idx_patterns_type (building_type),
    INDEX idx_patterns_active (is_active)
);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION topology.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_buildings_updated_at BEFORE UPDATE ON topology.buildings
    FOR EACH ROW EXECUTE FUNCTION topology.update_updated_at_column();

CREATE TRIGGER update_walls_updated_at BEFORE UPDATE ON topology.walls
    FOR EACH ROW EXECUTE FUNCTION topology.update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON topology.rooms
    FOR EACH ROW EXECUTE FUNCTION topology.update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE topology.buildings IS 'Master table for building topology and metadata';
COMMENT ON TABLE topology.walls IS 'Wall segments with nanometer precision coordinates';
COMMENT ON TABLE topology.rooms IS 'Detected rooms with boundaries and classification';
COMMENT ON TABLE topology.processing_results IS 'Audit trail of PDF processing attempts';
COMMENT ON TABLE topology.manual_corrections IS 'Human corrections for continuous learning';
COMMENT ON COLUMN topology.walls.geometry IS 'PostGIS LineString for spatial operations';
COMMENT ON COLUMN topology.rooms.footprint_polygon IS 'PostGIS Polygon defining room boundary';

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA topology TO arxos_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA topology TO arxos_app;

COMMIT;