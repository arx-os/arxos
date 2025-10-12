-- Migration: 011_circuit_tables.up.sql
-- Description: Create circuit-related tables for CADTUI functionality
-- Author: ArxOS Team
-- Date: 2024

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Circuit definitions table
CREATE TABLE circuits (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    repository_id VARCHAR(255) REFERENCES building_repositories(id) ON DELETE CASCADE,
    source_type VARCHAR(20) NOT NULL DEFAULT 'created', -- 'imported', 'created', 'converted'
    source_format VARCHAR(20), -- 'ifc', etc.
    source_file_path TEXT, -- Original file path for imported circuits
    grid_data JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Component definitions table
CREATE TABLE circuit_components (
    id VARCHAR(255) PRIMARY KEY,
    circuit_id VARCHAR(255) REFERENCES circuits(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    symbol CHAR(1) NOT NULL,
    position GEOMETRY(POINT, 4326),
    properties JSONB DEFAULT '{}',
    source_component_id VARCHAR(255), -- Reference to original component
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Connection definitions table
CREATE TABLE circuit_connections (
    id VARCHAR(255) PRIMARY KEY,
    circuit_id VARCHAR(255) REFERENCES circuits(id) ON DELETE CASCADE,
    from_component_id VARCHAR(255) REFERENCES circuit_components(id) ON DELETE CASCADE,
    to_component_id VARCHAR(255) REFERENCES circuit_components(id) ON DELETE CASCADE,
    path GEOMETRY(LINESTRING, 4326),
    properties JSONB DEFAULT '{}',
    source_connection_id VARCHAR(255), -- Reference to original connection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Particle definitions table
CREATE TABLE circuit_particles (
    id VARCHAR(255) PRIMARY KEY,
    animation_id VARCHAR(255) NOT NULL,
    symbol CHAR(1) NOT NULL,
    position GEOMETRY(POINT, 4326) NOT NULL,
    velocity JSONB NOT NULL DEFAULT '{}', -- {vx: float, vy: float}
    lifetime INTEGER NOT NULL DEFAULT 100,
    color VARCHAR(20) NOT NULL DEFAULT 'yellow',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Animation definitions table
CREATE TABLE circuit_animations (
    id VARCHAR(255) PRIMARY KEY,
    circuit_id VARCHAR(255) REFERENCES circuits(id) ON DELETE CASCADE,
    fps INTEGER NOT NULL DEFAULT 30,
    duration INTEGER NOT NULL DEFAULT 5000, -- milliseconds
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Field markups table
CREATE TABLE field_markups (
    id VARCHAR(255) PRIMARY KEY,
    circuit_id VARCHAR(255) REFERENCES circuits(id) ON DELETE CASCADE,
    ifc_id VARCHAR(255) REFERENCES ifc_elements(ifc_id) ON DELETE CASCADE,
    change_description TEXT NOT NULL,
    via VARCHAR(20) NOT NULL, -- 'ar' or 'text'
    user_id VARCHAR(255),
    position GEOMETRY(POINT, 4326),
    geometry JSONB NOT NULL DEFAULT '{}', -- {type: string, coordinates: array, properties: object}
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'applied', 'rejected', 'synced'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simulation results table
CREATE TABLE simulation_results (
    id VARCHAR(255) PRIMARY KEY,
    circuit_id VARCHAR(255) REFERENCES circuits(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    results JSONB DEFAULT '{}',
    errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    duration INTEGER DEFAULT 0, -- milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_circuits_repository_id ON circuits(repository_id);
CREATE INDEX idx_circuits_source_type ON circuits(source_type);
CREATE INDEX idx_circuits_created_at ON circuits(created_at);

CREATE INDEX idx_circuit_components_circuit_id ON circuit_components(circuit_id);
CREATE INDEX idx_circuit_components_type ON circuit_components(type);
CREATE INDEX idx_circuit_components_position ON circuit_components USING GIST(position);

CREATE INDEX idx_circuit_connections_circuit_id ON circuit_connections(circuit_id);
CREATE INDEX idx_circuit_connections_from_component ON circuit_connections(from_component_id);
CREATE INDEX idx_circuit_connections_to_component ON circuit_connections(to_component_id);
CREATE INDEX idx_circuit_connections_path ON circuit_connections USING GIST(path);

CREATE INDEX idx_circuit_particles_animation_id ON circuit_particles(animation_id);
CREATE INDEX idx_circuit_particles_position ON circuit_particles USING GIST(position);

CREATE INDEX idx_circuit_animations_circuit_id ON circuit_animations(circuit_id);
CREATE INDEX idx_circuit_animations_is_running ON circuit_animations(is_running);

CREATE INDEX idx_field_markups_circuit_id ON field_markups(circuit_id);
CREATE INDEX idx_field_markups_ifc_id ON field_markups(ifc_id);
CREATE INDEX idx_field_markups_status ON field_markups(status);
CREATE INDEX idx_field_markups_via ON field_markups(via);
CREATE INDEX idx_field_markups_position ON field_markups USING GIST(position);
CREATE INDEX idx_field_markups_created_at ON field_markups(created_at);

CREATE INDEX idx_simulation_results_circuit_id ON simulation_results(circuit_id);
CREATE INDEX idx_simulation_results_status ON simulation_results(status);
CREATE INDEX idx_simulation_results_created_at ON simulation_results(created_at);

-- Add constraints
ALTER TABLE circuits ADD CONSTRAINT chk_circuits_source_type
    CHECK (source_type IN ('imported', 'created', 'converted'));

ALTER TABLE circuit_components ADD CONSTRAINT chk_circuit_components_type
    CHECK (type IN ('resistor', 'capacitor', 'inductor', 'voltage_source', 'current_source', 'ground', 'wire', 'junction'));

ALTER TABLE circuit_connections ADD CONSTRAINT chk_circuit_connections_type
    CHECK (properties->>'type' IN ('wire', 'bus', 'power', 'signal'));

ALTER TABLE field_markups ADD CONSTRAINT chk_field_markups_via
    CHECK (via IN ('ar', 'text'));

ALTER TABLE field_markups ADD CONSTRAINT chk_field_markups_status
    CHECK (status IN ('pending', 'applied', 'rejected', 'synced'));

ALTER TABLE simulation_results ADD CONSTRAINT chk_simulation_results_status
    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_circuits_updated_at BEFORE UPDATE ON circuits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_circuit_animations_updated_at BEFORE UPDATE ON circuit_animations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_field_markups_updated_at BEFORE UPDATE ON field_markups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE circuits IS 'Circuit definitions for CADTUI functionality';
COMMENT ON TABLE circuit_components IS 'Components within circuits';
COMMENT ON TABLE circuit_connections IS 'Connections between components';
COMMENT ON TABLE circuit_particles IS 'Animated particles for signal flow visualization';
COMMENT ON TABLE circuit_animations IS 'Animation configurations for circuits';
COMMENT ON TABLE field_markups IS 'Field markups from mobile AR/text input';
COMMENT ON TABLE simulation_results IS 'Results from circuit simulations';

COMMENT ON COLUMN circuits.source_type IS 'How the circuit was created: imported, created, or converted';
COMMENT ON COLUMN circuits.source_format IS 'Original format if imported (ifc, etc.)';
COMMENT ON COLUMN circuits.source_file_path IS 'Path to original file if imported';
COMMENT ON COLUMN circuits.grid_data IS 'Grid configuration and state';

COMMENT ON COLUMN circuit_components.symbol IS 'Unicode character representing the component';
COMMENT ON COLUMN circuit_components.position IS 'Spatial position of the component';
COMMENT ON COLUMN circuit_components.source_component_id IS 'Reference to original component if imported';

COMMENT ON COLUMN circuit_connections.path IS 'Spatial path of the connection';
COMMENT ON COLUMN circuit_connections.source_connection_id IS 'Reference to original connection if imported';

COMMENT ON COLUMN circuit_particles.velocity IS 'Velocity vector as JSON: {vx: float, vy: float}';
COMMENT ON COLUMN circuit_particles.lifetime IS 'Number of animation frames remaining';

COMMENT ON COLUMN field_markups.via IS 'How the markup was created: ar or text';
COMMENT ON COLUMN field_markups.geometry IS 'Geometric data as JSON: {type, coordinates, properties}';
COMMENT ON COLUMN field_markups.status IS 'Current status of the markup';
