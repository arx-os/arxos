-- 001_create_arx_schema.sql
-- Migration: Create Arx core, BIM, spatial, and collaboration tables

-- NOTE: Table creation order is critical for foreign key constraints. Referenced tables must be created before referencing tables.
-- CI VALIDATION: If you add a new table or constraint, ensure referenced tables are defined above. Use a linter or script to check order.

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- =============================================================================
-- LEVEL 1: BASE TABLES (No Dependencies)
-- =============================================================================

-- USERS (Base table - referenced by many others)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- LEVEL 2: TABLES THAT DEPEND ON USERS
-- =============================================================================

-- PROJECTS (depends on users)
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_created_at ON projects(created_at);

-- =============================================================================
-- LEVEL 3: TABLES THAT DEPEND ON PROJECTS
-- =============================================================================

-- BUILDINGS (depends on users, projects)
CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_buildings_project_id ON buildings(project_id);
CREATE INDEX idx_buildings_owner_id ON buildings(owner_id);
CREATE INDEX idx_buildings_created_at ON buildings(created_at);
CREATE INDEX idx_buildings_updated_at ON buildings(updated_at);

-- =============================================================================
-- LEVEL 4: TABLES THAT DEPEND ON BUILDINGS
-- =============================================================================

-- FLOORS (depends on buildings)
CREATE TABLE floors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    building_id INTEGER REFERENCES buildings(id) ON DELETE CASCADE,
    svg_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_floors_building_id ON floors(building_id);
CREATE INDEX idx_floors_name ON floors(name);

-- CATEGORIES (depends on buildings) - MOVED HERE from after zones
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    building_id INTEGER REFERENCES buildings(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_categories_building_id ON categories(building_id);
CREATE INDEX idx_categories_name ON categories(name);

-- =============================================================================
-- LEVEL 5: TABLES THAT DEPEND ON FLOORS
-- =============================================================================

-- ROOMS (depends on users, buildings, floors, projects)
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
CREATE INDEX idx_rooms_building_id ON rooms (building_id);
CREATE INDEX idx_rooms_project_id ON rooms (project_id);
CREATE INDEX idx_rooms_floor_id ON rooms (floor_id);
CREATE INDEX idx_rooms_building_floor ON rooms (building_id, floor_id);
CREATE INDEX idx_rooms_category ON rooms (category);
CREATE INDEX idx_rooms_layer ON rooms (layer);
CREATE INDEX idx_rooms_name ON rooms (name);

-- =============================================================================
-- LEVEL 6: BIM OBJECTS THAT DEPEND ON ROOMS
-- =============================================================================

-- WALLS (depends on users, rooms, buildings, floors, projects)
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
CREATE INDEX idx_walls_building_id ON walls (building_id);
CREATE INDEX idx_walls_project_id ON walls (project_id);
CREATE INDEX idx_walls_room_id ON walls (room_id);
CREATE INDEX idx_walls_floor_id ON walls (floor_id);
CREATE INDEX idx_walls_building_floor ON walls (building_id, floor_id);
CREATE INDEX idx_walls_project_status ON walls (project_id, status);
CREATE INDEX idx_walls_material ON walls (material);
CREATE INDEX idx_walls_layer ON walls (layer);
CREATE INDEX idx_walls_category ON walls (category);

-- DOORS (depends on users, rooms, buildings, floors, projects)
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
CREATE INDEX idx_doors_building_id ON doors (building_id);
CREATE INDEX idx_doors_project_id ON doors (project_id);
CREATE INDEX idx_doors_room_id ON doors (room_id);
CREATE INDEX idx_doors_floor_id ON doors (floor_id);
CREATE INDEX idx_doors_building_floor ON doors (building_id, floor_id);
CREATE INDEX idx_doors_project_status ON doors (project_id, status);
CREATE INDEX idx_doors_material ON doors (material);
CREATE INDEX idx_doors_layer ON doors (layer);
CREATE INDEX idx_doors_category ON doors (category);

-- WINDOWS (depends on users, rooms, buildings, floors, projects)
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
CREATE INDEX idx_windows_building_id ON windows (building_id);
CREATE INDEX idx_windows_project_id ON windows (project_id);
CREATE INDEX idx_windows_room_id ON windows (room_id);
CREATE INDEX idx_windows_floor_id ON windows (floor_id);
CREATE INDEX idx_windows_building_floor ON windows (building_id, floor_id);
CREATE INDEX idx_windows_project_status ON windows (project_id, status);
CREATE INDEX idx_windows_material ON windows (material);
CREATE INDEX idx_windows_layer ON windows (layer);
CREATE INDEX idx_windows_category ON windows (category);

-- DEVICES (depends on users, rooms, buildings, floors, projects)
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
CREATE INDEX idx_devices_building_id ON devices (building_id);
CREATE INDEX idx_devices_project_id ON devices (project_id);
CREATE INDEX idx_devices_room_id ON devices (room_id);
CREATE INDEX idx_devices_floor_id ON devices (floor_id);
CREATE INDEX idx_devices_building_floor ON devices (building_id, floor_id);
CREATE INDEX idx_devices_project_status ON devices (project_id, status);
CREATE INDEX idx_devices_type ON devices (type);
CREATE INDEX idx_devices_system ON devices (system);
CREATE INDEX idx_devices_subtype ON devices (subtype);
CREATE INDEX idx_devices_layer ON devices (layer);
CREATE INDEX idx_devices_category ON devices (category);

-- LABELS (depends on users, rooms, buildings, floors, projects)
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
CREATE INDEX idx_labels_building_id ON labels (building_id);
CREATE INDEX idx_labels_project_id ON labels (project_id);
CREATE INDEX idx_labels_room_id ON labels (room_id);
CREATE INDEX idx_labels_floor_id ON labels (floor_id);
CREATE INDEX idx_labels_building_floor ON labels (building_id, floor_id);
CREATE INDEX idx_labels_project_status ON labels (project_id, status);
CREATE INDEX idx_labels_text ON labels (text);
CREATE INDEX idx_labels_layer ON labels (layer);
CREATE INDEX idx_labels_category ON labels (category);

-- ZONES (depends on users, buildings, floors, projects)
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
CREATE INDEX idx_zones_building_id ON zones (building_id);
CREATE INDEX idx_zones_project_id ON zones (project_id);
CREATE INDEX idx_zones_room_id ON zones (room_id);
CREATE INDEX idx_zones_floor_id ON zones (floor_id);
CREATE INDEX idx_zones_building_floor ON zones (building_id, floor_id);
CREATE INDEX idx_zones_project_status ON zones (project_id, status);
CREATE INDEX idx_zones_name ON zones (name);
CREATE INDEX idx_zones_layer ON zones (layer);
CREATE INDEX idx_zones_category ON zones (category);

-- =============================================================================
-- LEVEL 7: TABLES THAT DEPEND ON PROJECTS (but not other complex objects)
-- =============================================================================

-- DRAWINGS (depends on projects)
CREATE TABLE drawings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    svg TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_drawings_project_id ON drawings(project_id);
CREATE INDEX idx_drawings_name ON drawings(name);
CREATE INDEX idx_drawings_created_at ON drawings(created_at);

-- =============================================================================
-- LEVEL 8: COLLABORATION & AUDIT TABLES
-- =============================================================================

-- COMMENTS (depends on users)
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_object_id ON comments(object_id);
CREATE INDEX idx_comments_object_type ON comments(object_type);
CREATE INDEX idx_comments_created_at ON comments(created_at);

-- ASSIGNMENTS (depends on users)
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP
);
CREATE INDEX idx_assignments_user_id ON assignments(user_id);
CREATE INDEX idx_assignments_object_id ON assignments(object_id);
CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_assignments_object_type ON assignments(object_type);
CREATE INDEX idx_assignments_assigned_at ON assignments(assigned_at);

-- OBJECT HISTORY (depends on users)
CREATE TABLE object_history (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL,
    object_id VARCHAR(64) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    change_type VARCHAR(50) NOT NULL,
    change_data JSONB,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_object_history_user_id ON object_history(user_id);
CREATE INDEX idx_object_history_object_id ON object_history(object_id);
CREATE INDEX idx_object_history_change_type ON object_history(change_type);
CREATE INDEX idx_object_history_object_type ON object_history(object_type);
CREATE INDEX idx_object_history_changed_at ON object_history(changed_at);

-- AUDIT LOGS (depends on users)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    object_type TEXT,
    object_id TEXT,
    action TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_object_id ON audit_logs(object_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_object_type ON audit_logs(object_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- =============================================================================
-- LEVEL 9: TABLES WITH COMPLEX DEPENDENCIES
-- =============================================================================

-- USER CATEGORY PERMISSIONS (depends on users, categories, projects)
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
CREATE INDEX idx_user_category_permissions_user_id ON user_category_permissions(user_id);
CREATE INDEX idx_user_category_permissions_category_id ON user_category_permissions(category_id);
CREATE INDEX idx_user_category_permissions_project_id ON user_category_permissions(project_id);
CREATE INDEX idx_user_category_permissions_can_edit ON user_category_permissions(can_edit);

-- CHAT MESSAGES (depends on buildings, users, audit_logs)
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    audit_log_id INTEGER REFERENCES audit_logs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_chat_messages_building_id ON chat_messages(building_id);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_audit_log_id ON chat_messages(audit_log_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- CATALOG ITEMS (depends on categories, users)
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
CREATE INDEX idx_catalog_items_category_id ON catalog_items(category_id);
CREATE INDEX idx_catalog_items_created_by ON catalog_items(created_by);
CREATE INDEX idx_catalog_items_make ON catalog_items(make);
CREATE INDEX idx_catalog_items_model ON catalog_items(model);
CREATE INDEX idx_catalog_items_type ON catalog_items(type);
CREATE INDEX idx_catalog_items_approved ON catalog_items(approved);
CREATE INDEX idx_catalog_items_created_at ON catalog_items(created_at);
-- Composite index for make/model/type
CREATE INDEX idx_catalog_items_make_model_type ON catalog_items(make, model, type);

-- =============================================================================
-- PERFORMANCE INDEXES FOR COMMON QUERY PATTERNS
-- =============================================================================

-- Composite indexes for complex filtering
CREATE INDEX idx_rooms_building_floor_status ON rooms (building_id, floor_id, status);
CREATE INDEX idx_rooms_building_category ON rooms (building_id, category);
CREATE INDEX idx_walls_building_floor_status ON walls (building_id, floor_id, status);
CREATE INDEX idx_walls_building_material ON walls (building_id, material);
CREATE INDEX idx_doors_building_floor_status ON doors (building_id, floor_id, status);
CREATE INDEX idx_doors_building_material ON doors (building_id, material);
CREATE INDEX idx_windows_building_floor_status ON windows (building_id, floor_id, status);
CREATE INDEX idx_windows_building_material ON windows (building_id, floor_id, material);
CREATE INDEX idx_devices_building_system_type ON devices (building_id, system, type);
CREATE INDEX idx_devices_building_floor_status ON devices (building_id, floor_id, status);
CREATE INDEX idx_labels_building_floor_status ON labels (building_id, floor_id, status);
CREATE INDEX idx_zones_building_floor_status ON zones (building_id, floor_id, status);

-- User activity indexes
CREATE INDEX idx_rooms_assigned_status ON rooms (assigned_to, status);
CREATE INDEX idx_walls_assigned_status ON walls (assigned_to, status);
CREATE INDEX idx_doors_assigned_status ON doors (assigned_to, status);
CREATE INDEX idx_windows_assigned_status ON windows (assigned_to, status);
CREATE INDEX idx_devices_assigned_status ON devices (assigned_to, status);
CREATE INDEX idx_labels_assigned_status ON labels (assigned_to, status);
CREATE INDEX idx_zones_assigned_status ON zones (assigned_to, status);

-- Project-based indexes
CREATE INDEX idx_rooms_project_status ON rooms (project_id, status);
CREATE INDEX idx_walls_project_status ON walls (project_id, status);
CREATE INDEX idx_doors_project_status ON doors (project_id, status);
CREATE INDEX idx_windows_project_status ON windows (project_id, status);
CREATE INDEX idx_devices_project_status ON devices (project_id, status);
CREATE INDEX idx_labels_project_status ON labels (project_id, status);
CREATE INDEX idx_zones_project_status ON zones (project_id, status);

-- Audit and history indexes
CREATE INDEX idx_audit_logs_user_action ON audit_logs (user_id, action);
CREATE INDEX idx_audit_logs_user_created ON audit_logs (user_id, created_at);
CREATE INDEX idx_object_history_user_changed ON object_history (user_id, changed_at);
CREATE INDEX idx_object_history_object_changed ON object_history (object_id, changed_at);

-- =============================================================================
-- PARTIAL INDEXES FOR FILTERED QUERIES
-- =============================================================================

-- Active objects only
CREATE INDEX idx_rooms_active ON rooms (building_id, floor_id) WHERE status = 'active';
CREATE INDEX idx_walls_active ON walls (building_id, floor_id) WHERE status = 'active';
CREATE INDEX idx_doors_active ON doors (building_id, floor_id) WHERE status = 'active';
CREATE INDEX idx_windows_active ON windows (building_id, floor_id) WHERE status = 'active';
CREATE INDEX idx_devices_active ON devices (building_id, floor_id) WHERE status = 'active';
CREATE INDEX idx_labels_active ON labels (building_id, floor_id) WHERE status = 'active';
CREATE INDEX idx_zones_active ON zones (building_id, floor_id) WHERE status = 'active';

-- Locked objects only
CREATE INDEX idx_rooms_locked ON rooms (building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX idx_walls_locked ON walls (building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX idx_doors_locked ON doors (building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX idx_windows_locked ON windows (building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX idx_devices_locked ON devices (building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX idx_labels_locked ON labels (building_id, floor_id) WHERE locked_by IS NOT NULL;
CREATE INDEX idx_zones_locked ON zones (building_id, floor_id) WHERE locked_by IS NOT NULL;

-- Recent audit logs (last 30 days)
CREATE INDEX idx_audit_logs_recent ON audit_logs (user_id, created_at) WHERE created_at > NOW() - INTERVAL '30 days';

-- Recent object history (last 30 days)
CREATE INDEX idx_object_history_recent ON object_history (object_id, changed_at) WHERE changed_at > NOW() - INTERVAL '30 days';

-- =============================================================================
-- COVERING INDEXES FOR FREQUENTLY ACCESSED COLUMNS
-- =============================================================================

-- Building covering index
CREATE INDEX idx_buildings_covering ON buildings (owner_id) INCLUDE (name, address, created_at);

-- Room covering index
CREATE INDEX idx_rooms_covering ON rooms (building_id, floor_id) INCLUDE (name, status, category);

-- Device covering index
CREATE INDEX idx_devices_covering ON devices (building_id, floor_id) INCLUDE (type, system, status);

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================

-- Review query logs regularly and add further indexes as needed for performance.
--
-- DEPENDENCY HIERARCHY SUMMARY:
-- Level 1: users (base table)
-- Level 2: projects (depends on users)
-- Level 3: buildings (depends on users, projects)
-- Level 4: floors, categories (depend on buildings)
-- Level 5: rooms (depends on users, buildings, floors, projects)
-- Level 6: walls, doors, windows, devices, labels, zones (depend on rooms and others)
-- Level 7: drawings (depends on projects)
-- Level 8: comments, assignments, object_history, audit_logs (depend on users)
-- Level 9: user_category_permissions, chat_messages, catalog_items (complex dependencies)
--
-- PERFORMANCE INDEXES ADDED:
-- - Single-column indexes for frequently filtered fields
-- - Composite indexes for complex query patterns
-- - Partial indexes for filtered queries
-- - Covering indexes for frequently accessed columns
-- - Spatial indexes for geometric data
-- - User activity and project-based indexes
