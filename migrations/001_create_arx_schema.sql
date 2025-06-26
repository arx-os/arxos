-- 001_create_arx_schema.sql
-- Migration: Create Arx core, BIM, spatial, and collaboration tables

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- USERS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROJECTS
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BUILDINGS
CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FLOORS
CREATE TABLE floors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    building_id INTEGER REFERENCES buildings(id) ON DELETE CASCADE,
    svg_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DRAWINGS
CREATE TABLE drawings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    svg TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BIM OBJECTS

-- WALLS
CREATE TABLE walls (
    id VARCHAR(64) PRIMARY KEY,
    material VARCHAR(100),
    layer VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50),
    source_svg VARCHAR(255),
    svg_id VARCHAR(255),
    locked_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    room_id VARCHAR(64) REFERENCES rooms(id),
    building_id INTEGER REFERENCES buildings(id),
    floor_id INTEGER REFERENCES floors(id),
    geom geometry(LineString, 4326),
    category VARCHAR(100) NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id)
);
CREATE INDEX idx_walls_geom ON walls USING GIST (geom);
CREATE INDEX idx_walls_assigned_to ON walls (assigned_to);
CREATE INDEX idx_walls_status ON walls (status);
CREATE INDEX idx_walls_created_by ON walls (created_by);
CREATE INDEX idx_walls_locked_by ON walls (locked_by);

-- ROOMS
CREATE TABLE rooms (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255),
    layer VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50),
    source_svg VARCHAR(255),
    svg_id VARCHAR(255),
    locked_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    building_id INTEGER REFERENCES buildings(id),
    floor_id INTEGER REFERENCES floors(id),
    geom geometry(Polygon, 4326),
    category VARCHAR(100) NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id)
);
CREATE INDEX idx_rooms_geom ON rooms USING GIST (geom);
CREATE INDEX idx_rooms_assigned_to ON rooms (assigned_to);
CREATE INDEX idx_rooms_status ON rooms (status);
CREATE INDEX idx_rooms_created_by ON rooms (created_by);
CREATE INDEX idx_rooms_locked_by ON rooms (locked_by);

-- DOORS
CREATE TABLE doors (
    id VARCHAR(64) PRIMARY KEY,
    material VARCHAR(100),
    layer VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50),
    source_svg VARCHAR(255),
    svg_id VARCHAR(255),
    locked_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    room_id VARCHAR(64) REFERENCES rooms(id),
    building_id INTEGER REFERENCES buildings(id),
    floor_id INTEGER REFERENCES floors(id),
    geom geometry(Point, 4326),
    category VARCHAR(100) NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id)
);
CREATE INDEX idx_doors_geom ON doors USING GIST (geom);
CREATE INDEX idx_doors_assigned_to ON doors (assigned_to);
CREATE INDEX idx_doors_status ON doors (status);
CREATE INDEX idx_doors_created_by ON doors (created_by);
CREATE INDEX idx_doors_locked_by ON doors (locked_by);

-- WINDOWS
CREATE TABLE windows (
    id VARCHAR(64) PRIMARY KEY,
    material VARCHAR(100),
    layer VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50),
    source_svg VARCHAR(255),
    svg_id VARCHAR(255),
    locked_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    room_id VARCHAR(64) REFERENCES rooms(id),
    building_id INTEGER REFERENCES buildings(id),
    floor_id INTEGER REFERENCES floors(id),
    geom geometry(LineString, 4326),
    category VARCHAR(100) NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id)
);
CREATE INDEX idx_windows_geom ON windows USING GIST (geom);
CREATE INDEX idx_windows_assigned_to ON windows (assigned_to);
CREATE INDEX idx_windows_status ON windows (status);
CREATE INDEX idx_windows_created_by ON windows (created_by);
CREATE INDEX idx_windows_locked_by ON windows (locked_by);

-- DEVICES
CREATE TABLE devices (
    id VARCHAR(64) PRIMARY KEY,
    type VARCHAR(100),
    system VARCHAR(100),
    subtype VARCHAR(100),
    layer VARCHAR(100),
    room_id VARCHAR(64) REFERENCES rooms(id),
    building_id INTEGER REFERENCES buildings(id),
    floor_id INTEGER REFERENCES floors(id),
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50),
    source_svg VARCHAR(255),
    svg_id VARCHAR(255),
    locked_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    geom geometry(Point, 4326),
    category VARCHAR(100) NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id)
);
CREATE INDEX idx_devices_geom ON devices USING GIST (geom);
CREATE INDEX idx_devices_assigned_to ON devices (assigned_to);
CREATE INDEX idx_devices_status ON devices (status);
CREATE INDEX idx_devices_created_by ON devices (created_by);
CREATE INDEX idx_devices_locked_by ON devices (locked_by);

-- LABELS
CREATE TABLE labels (
    id VARCHAR(64) PRIMARY KEY,
    text VARCHAR(255),
    layer VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50),
    source_svg VARCHAR(255),
    svg_id VARCHAR(255),
    locked_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    room_id VARCHAR(64) REFERENCES rooms(id),
    building_id INTEGER REFERENCES buildings(id),
    floor_id INTEGER REFERENCES floors(id),
    geom geometry(Point, 4326),
    category VARCHAR(100) NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id)
);
CREATE INDEX idx_labels_geom ON labels USING GIST (geom);
CREATE INDEX idx_labels_assigned_to ON labels (assigned_to);
CREATE INDEX idx_labels_status ON labels (status);
CREATE INDEX idx_labels_created_by ON labels (created_by);
CREATE INDEX idx_labels_locked_by ON labels (locked_by);

-- ZONES
CREATE TABLE zones (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255),
    layer VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50),
    source_svg VARCHAR(255),
    svg_id VARCHAR(255),
    locked_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    building_id INTEGER REFERENCES buildings(id),
    floor_id INTEGER REFERENCES floors(id),
    geom geometry(Polygon, 4326),
    category VARCHAR(100) NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id)
);
CREATE INDEX idx_zones_geom ON zones USING GIST (geom);
CREATE INDEX idx_zones_assigned_to ON zones (assigned_to);
CREATE INDEX idx_zones_status ON zones (status);
CREATE INDEX idx_zones_created_by ON zones (created_by);
CREATE INDEX idx_zones_locked_by ON zones (locked_by);

-- COLLABORATION & AUDIT

-- COMMENTS
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ASSIGNMENTS
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP
);

-- OBJECT HISTORY
CREATE TABLE object_history (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    change_type VARCHAR(50) NOT NULL,
    change_data JSONB,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CATEGORIES
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    building_id INTEGER REFERENCES buildings(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- USER CATEGORY PERMISSIONS
CREATE TABLE user_category_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    can_edit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category_id, project_id)
);

-- AUDIT LOGS
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    object_type TEXT,
    object_id TEXT,
    action TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CHAT MESSAGES
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    audit_log_id INTEGER REFERENCES audit_logs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CATALOG ITEMS
CREATE TABLE catalog_items (
    id SERIAL PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    serial_number TEXT,
    category_id INTEGER REFERENCES categories(id),
    type TEXT,
    specs JSONB,
    datasheet_url TEXT,
    approved BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 