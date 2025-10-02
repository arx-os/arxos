-- ArxOS Initial Database Schema
-- Version: 001
-- Description: Create initial tables for ArxOS building management system

-- =============================================================================
-- Organizations
-- =============================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_organizations_name ON organizations(name);

-- =============================================================================
-- Users
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    organization_id TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_organization ON users(organization_id);

-- =============================================================================
-- Buildings
-- =============================================================================
CREATE TABLE IF NOT EXISTS buildings (
    id TEXT PRIMARY KEY,
    arxos_id TEXT UNIQUE NOT NULL, -- e.g., ARXOS-NA-US-NY-NYC-0001
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    postal_code TEXT,
    latitude REAL,
    longitude REAL,
    organization_id TEXT,
    total_area REAL,
    floors_count INTEGER,
    year_built INTEGER,
    building_type TEXT,
    status TEXT DEFAULT 'OPERATIONAL',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE INDEX idx_buildings_arxos_id ON buildings(arxos_id);
CREATE INDEX idx_buildings_organization ON buildings(organization_id);
CREATE INDEX idx_buildings_location ON buildings(city, state, country);

-- =============================================================================
-- Floors
-- =============================================================================
CREATE TABLE IF NOT EXISTS floors (
    id TEXT PRIMARY KEY,
    building_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    name TEXT NOT NULL,
    area REAL,
    height REAL,
    floor_type TEXT,
    status TEXT DEFAULT 'OPERATIONAL',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

CREATE INDEX idx_floors_building ON floors(building_id);
CREATE INDEX idx_floors_level ON floors(building_id, level);

-- =============================================================================
-- Zones
-- =============================================================================
CREATE TABLE IF NOT EXISTS zones (
    id TEXT PRIMARY KEY,
    floor_id TEXT NOT NULL,
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    area REAL,
    occupancy_limit INTEGER,
    hvac_zone_id TEXT,
    status TEXT DEFAULT 'OPERATIONAL',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (floor_id) REFERENCES floors(id) ON DELETE CASCADE
);

CREATE INDEX idx_zones_floor ON zones(floor_id);
CREATE INDEX idx_zones_type ON zones(zone_type);

-- =============================================================================
-- Rooms
-- =============================================================================
CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY,
    floor_id TEXT NOT NULL,
    zone_id TEXT,
    room_number TEXT NOT NULL,
    name TEXT NOT NULL,
    room_type TEXT,
    area REAL,
    height REAL,
    capacity INTEGER,
    status TEXT DEFAULT 'OPERATIONAL',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (floor_id) REFERENCES floors(id) ON DELETE CASCADE,
    FOREIGN KEY (zone_id) REFERENCES zones(id) ON DELETE SET NULL
);

CREATE INDEX idx_rooms_floor ON rooms(floor_id);
CREATE INDEX idx_rooms_zone ON rooms(zone_id);
CREATE INDEX idx_rooms_number ON rooms(room_number);

-- =============================================================================
-- Equipment
-- =============================================================================
CREATE TABLE IF NOT EXISTS equipment (
    id TEXT PRIMARY KEY,
    room_id TEXT,
    floor_id TEXT,
    building_id TEXT NOT NULL,
    equipment_tag TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    installation_date DATE,
    warranty_expiry DATE,
    status TEXT DEFAULT 'OPERATIONAL',
    location_x REAL,
    location_y REAL,
    location_z REAL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
    FOREIGN KEY (floor_id) REFERENCES floors(id) ON DELETE SET NULL,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

CREATE INDEX idx_equipment_tag ON equipment(equipment_tag);
CREATE INDEX idx_equipment_room ON equipment(room_id);
CREATE INDEX idx_equipment_floor ON equipment(floor_id);
CREATE INDEX idx_equipment_building ON equipment(building_id);
CREATE INDEX idx_equipment_type ON equipment(equipment_type);

-- =============================================================================
-- Points (BAS/IoT data points)
-- =============================================================================
CREATE TABLE IF NOT EXISTS points (
    id TEXT PRIMARY KEY,
    equipment_id TEXT,
    room_id TEXT,
    point_tag TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    point_type TEXT NOT NULL, -- sensor, actuator, setpoint, status
    data_type TEXT NOT NULL, -- boolean, integer, float, string
    unit TEXT,
    current_value TEXT,
    last_updated TIMESTAMP,
    update_frequency INTEGER, -- in seconds
    is_writable BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
);

CREATE INDEX idx_points_tag ON points(point_tag);
CREATE INDEX idx_points_equipment ON points(equipment_id);
CREATE INDEX idx_points_room ON points(room_id);
CREATE INDEX idx_points_type ON points(point_type);
CREATE INDEX idx_points_updated ON points(last_updated);

-- =============================================================================
-- Timeseries Data
-- =============================================================================
CREATE TABLE IF NOT EXISTS timeseries_data (
    point_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value TEXT NOT NULL,
    quality INTEGER DEFAULT 100,
    PRIMARY KEY (point_id, timestamp),
    FOREIGN KEY (point_id) REFERENCES points(id) ON DELETE CASCADE
);

CREATE INDEX idx_timeseries_point_time ON timeseries_data(point_id, timestamp DESC);

-- =============================================================================
-- Alarms
-- =============================================================================
CREATE TABLE IF NOT EXISTS alarms (
    id TEXT PRIMARY KEY,
    point_id TEXT,
    equipment_id TEXT,
    alarm_type TEXT NOT NULL,
    severity TEXT NOT NULL, -- critical, major, minor, warning, info
    state TEXT NOT NULL, -- active, acknowledged, cleared
    message TEXT NOT NULL,
    triggered_at TIMESTAMP NOT NULL,
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    cleared_at TIMESTAMP,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (point_id) REFERENCES points(id) ON DELETE SET NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_alarms_state ON alarms(state);
CREATE INDEX idx_alarms_severity ON alarms(severity);
CREATE INDEX idx_alarms_point ON alarms(point_id);
CREATE INDEX idx_alarms_equipment ON alarms(equipment_id);
CREATE INDEX idx_alarms_triggered ON alarms(triggered_at DESC);

-- =============================================================================
-- Maintenance Records
-- =============================================================================
CREATE TABLE IF NOT EXISTS maintenance_records (
    id TEXT PRIMARY KEY,
    equipment_id TEXT NOT NULL,
    maintenance_type TEXT NOT NULL, -- preventive, corrective, inspection
    description TEXT,
    performed_by TEXT,
    performed_at TIMESTAMP NOT NULL,
    next_due_date DATE,
    cost DECIMAL(10,2),
    duration_hours REAL,
    status TEXT DEFAULT 'completed',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_maintenance_equipment ON maintenance_records(equipment_id);
CREATE INDEX idx_maintenance_date ON maintenance_records(performed_at DESC);
CREATE INDEX idx_maintenance_due ON maintenance_records(next_due_date);

-- =============================================================================
-- API Keys
-- =============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    key_hash TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    permissions JSON,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);

-- =============================================================================
-- Sessions
-- =============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- =============================================================================
-- Audit Log
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    old_value JSON,
    new_value JSON,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);