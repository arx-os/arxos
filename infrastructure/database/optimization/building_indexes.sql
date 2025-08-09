-- Building Database Indexes for Performance Optimization
-- This file contains optimized indexes for building-related tables

-- Enable PostGIS extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Building table indexes
CREATE INDEX IF NOT EXISTS idx_buildings_name ON buildings USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_buildings_building_type ON buildings(building_type);
CREATE INDEX IF NOT EXISTS idx_buildings_status ON buildings(status);
CREATE INDEX IF NOT EXISTS idx_buildings_owner_id ON buildings(owner_id);
CREATE INDEX IF NOT EXISTS idx_buildings_year_built ON buildings(year_built);
CREATE INDEX IF NOT EXISTS idx_buildings_total_floors ON buildings(total_floors);
CREATE INDEX IF NOT EXISTS idx_buildings_created_at ON buildings(created_at);
CREATE INDEX IF NOT EXISTS idx_buildings_updated_at ON buildings(updated_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_buildings_type_status ON buildings(building_type, status);
CREATE INDEX IF NOT EXISTS idx_buildings_owner_status ON buildings(owner_id, status);
CREATE INDEX IF NOT EXISTS idx_buildings_year_type ON buildings(year_built, building_type);

-- Spatial indexes for location-based queries
CREATE INDEX IF NOT EXISTS idx_buildings_location ON buildings USING gist(location);
CREATE INDEX IF NOT EXISTS idx_buildings_coordinates ON buildings USING gist(
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
);

-- Address-based indexes
CREATE INDEX IF NOT EXISTS idx_buildings_city ON buildings(city);
CREATE INDEX IF NOT EXISTS idx_buildings_state ON buildings(state);
CREATE INDEX IF NOT EXISTS idx_buildings_country ON buildings(country);
CREATE INDEX IF NOT EXISTS idx_buildings_city_state ON buildings(city, state);

-- Tag-based indexes (assuming tags are stored as JSONB)
CREATE INDEX IF NOT EXISTS idx_buildings_tags ON buildings USING gin(tags);

-- Metadata indexes (assuming metadata is stored as JSONB)
CREATE INDEX IF NOT EXISTS idx_buildings_metadata ON buildings USING gin(metadata);

-- Partial indexes for active buildings
CREATE INDEX IF NOT EXISTS idx_buildings_active ON buildings(id) WHERE status = 'active';

-- Partial indexes for commercial buildings
CREATE INDEX IF NOT EXISTS idx_buildings_commercial ON buildings(id) WHERE building_type = 'commercial';

-- Partial indexes for recent buildings
CREATE INDEX IF NOT EXISTS idx_buildings_recent ON buildings(id) WHERE created_at >= CURRENT_DATE - INTERVAL '1 year';

-- Floor table indexes
CREATE INDEX IF NOT EXISTS idx_floors_building_id ON floors(building_id);
CREATE INDEX IF NOT EXISTS idx_floors_floor_number ON floors(floor_number);
CREATE INDEX IF NOT EXISTS idx_floors_status ON floors(status);
CREATE INDEX IF NOT EXISTS idx_floors_building_status ON floors(building_id, status);

-- Room table indexes
CREATE INDEX IF NOT EXISTS idx_rooms_building_id ON rooms(building_id);
CREATE INDEX IF NOT EXISTS idx_rooms_floor_id ON rooms(floor_id);
CREATE INDEX IF NOT EXISTS idx_rooms_room_type ON rooms(room_type);
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);
CREATE INDEX IF NOT EXISTS idx_rooms_building_floor ON rooms(building_id, floor_id);

-- Device table indexes
CREATE INDEX IF NOT EXISTS idx_devices_building_id ON devices(building_id);
CREATE INDEX IF NOT EXISTS idx_devices_floor_id ON devices(floor_id);
CREATE INDEX IF NOT EXISTS idx_devices_room_id ON devices(room_id);
CREATE INDEX IF NOT EXISTS idx_devices_device_type ON devices(device_type);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_building_type ON devices(building_id, device_type);

-- User table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Project table indexes
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_projects_owner_status ON projects(owner_id, status);

-- Performance monitoring indexes
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_entity_type ON performance_metrics(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_type ON performance_metrics(metric_type);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type ON audit_logs(entity_type, entity_id);

-- Statistics for query planner
ANALYZE buildings;
ANALYZE floors;
ANALYZE rooms;
ANALYZE devices;
ANALYZE users;
ANALYZE projects;
ANALYZE performance_metrics;
ANALYZE audit_logs;
