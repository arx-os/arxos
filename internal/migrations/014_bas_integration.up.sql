-- Migration 014: BAS Integration
-- Description: Add BAS (Building Automation System) integration tables and enhance room model
-- Author: ArxOS Team
-- Date: 2025-01-15

-- ============================================================================
-- BAS Systems Table
-- ============================================================================
-- Stores BAS system configurations (Metasys, Desigo, Honeywell, etc.)
CREATE TABLE IF NOT EXISTS bas_systems (
    id TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES building_repositories(id) ON DELETE CASCADE,

    -- System identification
    name TEXT NOT NULL,
    system_type TEXT NOT NULL CHECK (system_type IN (
        'johnson_controls_metasys',
        'siemens_desigo',
        'honeywell_ebi',
        'tridium_niagara',
        'schneider_electric',
        'other'
    )),
    vendor TEXT,
    version TEXT,

    -- Connection details (optional, for live integration)
    host TEXT,
    port INTEGER,
    protocol TEXT CHECK (protocol IN ('bacnet', 'modbus', 'lonworks', 'http', 'https', NULL)),

    -- Configuration
    enabled BOOLEAN NOT NULL DEFAULT true,
    read_only BOOLEAN NOT NULL DEFAULT true, -- ArxOS defaults to read-only
    sync_interval INTEGER, -- Seconds between syncs (if live connection)
    last_sync TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    notes TEXT,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT bas_systems_unique_name UNIQUE(building_id, name)
);

CREATE INDEX idx_bas_systems_building ON bas_systems(building_id);
CREATE INDEX idx_bas_systems_repository ON bas_systems(repository_id);
CREATE INDEX idx_bas_systems_type ON bas_systems(system_type);
CREATE INDEX idx_bas_systems_enabled ON bas_systems(enabled) WHERE enabled = true;

COMMENT ON TABLE bas_systems IS 'BAS system configurations (Metasys, Desigo, etc.) linked to buildings';
COMMENT ON COLUMN bas_systems.read_only IS 'ArxOS operates in read-only mode by default for safety';
COMMENT ON COLUMN bas_systems.sync_interval IS 'Auto-sync interval in seconds (NULL = manual only)';

-- ============================================================================
-- BAS Points Table
-- ============================================================================
-- Stores individual BAS control points (sensors, actuators, setpoints)
CREATE TABLE IF NOT EXISTS bas_points (
    id TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    bas_system_id TEXT NOT NULL REFERENCES bas_systems(id) ON DELETE CASCADE,

    -- Spatial links (where is this point physically?)
    room_id TEXT REFERENCES rooms(id) ON DELETE SET NULL,
    floor_id TEXT REFERENCES floors(id) ON DELETE SET NULL,
    equipment_id TEXT REFERENCES equipment(id) ON DELETE SET NULL,

    -- BAS identifiers
    point_name TEXT NOT NULL,
    device_id TEXT NOT NULL,
    object_type TEXT NOT NULL, -- "Analog Input", "Binary Output", etc.
    object_instance INTEGER,

    -- Point metadata
    description TEXT,
    units TEXT, -- degF, PSI, CFM, %, etc.
    point_type TEXT, -- temperature, pressure, flow, status, etc.

    -- Location parsing (from CSV import)
    location_text TEXT, -- Original location string from BAS export

    -- Spatial coordinates (optional, for precise positioning)
    location GEOMETRY(POINTZ, 4326),

    -- Point configuration
    writeable BOOLEAN NOT NULL DEFAULT false,
    min_value NUMERIC(10,2),
    max_value NUMERIC(10,2),

    -- Current value (if live connection enabled)
    current_value TEXT,
    current_value_numeric NUMERIC(10,2),
    current_value_boolean BOOLEAN,
    last_updated TIMESTAMPTZ,

    -- Mapping status
    mapped BOOLEAN NOT NULL DEFAULT false,
    mapping_confidence SMALLINT DEFAULT 0 CHECK (mapping_confidence BETWEEN 0 AND 3),

    -- Import tracking
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    import_source TEXT, -- filename or source identifier

    -- Version control (which version added/removed this point)
    added_in_version UUID REFERENCES versions(id) ON DELETE SET NULL,
    removed_in_version UUID REFERENCES versions(id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint on BAS identifiers
    CONSTRAINT bas_points_unique_identifier UNIQUE(bas_system_id, device_id, point_name)
);

-- Indexes for performance
CREATE INDEX idx_bas_points_building ON bas_points(building_id);
CREATE INDEX idx_bas_points_system ON bas_points(bas_system_id);
CREATE INDEX idx_bas_points_room ON bas_points(room_id) WHERE room_id IS NOT NULL;
CREATE INDEX idx_bas_points_floor ON bas_points(floor_id) WHERE floor_id IS NOT NULL;
CREATE INDEX idx_bas_points_equipment ON bas_points(equipment_id) WHERE equipment_id IS NOT NULL;
CREATE INDEX idx_bas_points_device ON bas_points(device_id);
CREATE INDEX idx_bas_points_type ON bas_points(object_type);
CREATE INDEX idx_bas_points_point_type ON bas_points(point_type) WHERE point_type IS NOT NULL;
CREATE INDEX idx_bas_points_unmapped ON bas_points(mapped) WHERE mapped = false;
CREATE INDEX idx_bas_points_location ON bas_points USING GIST(location) WHERE location IS NOT NULL;
CREATE INDEX idx_bas_points_version ON bas_points(added_in_version, removed_in_version);

COMMENT ON TABLE bas_points IS 'BAS control points (sensors, actuators) with spatial mapping to building elements';
COMMENT ON COLUMN bas_points.mapped IS 'Whether point has been mapped to room/equipment';
COMMENT ON COLUMN bas_points.mapping_confidence IS '0=unmapped, 1=auto-mapped low confidence, 2=auto-mapped high confidence, 3=manually verified';
COMMENT ON COLUMN bas_points.location_text IS 'Original location string from BAS export (e.g., "Floor 3 Room 301")';

-- ============================================================================
-- Enhance Rooms Table for Three-Tier Fidelity
-- ============================================================================
-- Add dimensions and fidelity tracking to support text-based room creation

ALTER TABLE rooms ADD COLUMN IF NOT EXISTS width REAL CHECK (width > 0);
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS length REAL CHECK (length > 0);
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS geometry GEOMETRY(POLYGON, 4326);

ALTER TABLE rooms ADD COLUMN IF NOT EXISTS fidelity_source TEXT DEFAULT 'text'
    CHECK (fidelity_source IN ('text', 'ifc', 'lidar', 'survey', 'manual'));

ALTER TABLE rooms ADD COLUMN IF NOT EXISTS confidence_level SMALLINT DEFAULT 0
    CHECK (confidence_level BETWEEN 0 AND 3);

ALTER TABLE rooms ADD COLUMN IF NOT EXISTS scan_session_id UUID;

-- Indexes for room queries
CREATE INDEX IF NOT EXISTS idx_rooms_fidelity ON rooms(fidelity_source);
CREATE INDEX IF NOT EXISTS idx_rooms_confidence ON rooms(confidence_level);
CREATE INDEX IF NOT EXISTS idx_rooms_geometry ON rooms USING GIST(geometry) WHERE geometry IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rooms_dimensions ON rooms(width, length) WHERE width IS NOT NULL AND length IS NOT NULL;

COMMENT ON COLUMN rooms.width IS 'Room width in meters (for text-based/simple rooms)';
COMMENT ON COLUMN rooms.length IS 'Room length in meters (for text-based/simple rooms)';
COMMENT ON COLUMN rooms.geometry IS 'Precise room boundary polygon (from IFC or LiDAR)';
COMMENT ON COLUMN rooms.fidelity_source IS 'Data source: text (manual), ifc (BIM), lidar (scanned), survey (measured), manual (drawn)';
COMMENT ON COLUMN rooms.confidence_level IS '0=low (text only), 1=medium (calculated), 2=high (imported), 3=verified (surveyed)';
COMMENT ON COLUMN rooms.scan_session_id IS 'Reference to LiDAR scan session if room was scanned';

-- ============================================================================
-- BAS Import History Table
-- ============================================================================
-- Track BAS import operations for audit and debugging
CREATE TABLE IF NOT EXISTS bas_import_history (
    id TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    bas_system_id TEXT NOT NULL REFERENCES bas_systems(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES building_repositories(id) ON DELETE SET NULL,
    version_id UUID REFERENCES versions(id) ON DELETE SET NULL,

    -- Import details
    filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash TEXT NOT NULL, -- SHA-256 of imported file

    -- Import results
    points_added INTEGER NOT NULL DEFAULT 0,
    points_modified INTEGER NOT NULL DEFAULT 0,
    points_deleted INTEGER NOT NULL DEFAULT 0,
    points_mapped INTEGER NOT NULL DEFAULT 0,
    points_unmapped INTEGER NOT NULL DEFAULT 0,

    -- Status
    status TEXT NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    error_message TEXT,
    errors JSONB DEFAULT '[]',

    -- Timing
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Audit
    imported_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    import_method TEXT CHECK (import_method IN ('cli', 'api', 'daemon', 'manual')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bas_import_history_building ON bas_import_history(building_id, created_at DESC);
CREATE INDEX idx_bas_import_history_system ON bas_import_history(bas_system_id, created_at DESC);
CREATE INDEX idx_bas_import_history_status ON bas_import_history(status);
CREATE INDEX idx_bas_import_history_file_hash ON bas_import_history(file_hash);

COMMENT ON TABLE bas_import_history IS 'Audit log of BAS point imports with results and timing';
COMMENT ON COLUMN bas_import_history.file_hash IS 'SHA-256 hash to detect duplicate imports';

-- ============================================================================
-- Update trigger for updated_at timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_bas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER bas_systems_updated_at
    BEFORE UPDATE ON bas_systems
    FOR EACH ROW
    EXECUTE FUNCTION update_bas_updated_at();

CREATE TRIGGER bas_points_updated_at
    BEFORE UPDATE ON bas_points
    FOR EACH ROW
    EXECUTE FUNCTION update_bas_updated_at();

-- ============================================================================
-- Schema documentation
-- ============================================================================
COMMENT ON SCHEMA public IS 'ArxOS spatial database schema - Migration 014 applied (BAS Integration)';

