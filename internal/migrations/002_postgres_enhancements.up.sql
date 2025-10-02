-- ArxOS PostgreSQL Enhancements
-- Version: 002
-- Description: Add PostgreSQL-specific features and optimizations
-- Only run this migration when using PostgreSQL

-- =============================================================================
-- Enable Extensions
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- =============================================================================
-- Add UUID generation defaults (PostgreSQL specific)
-- =============================================================================
-- Only modify if columns don't have defaults
DO $$
BEGIN
    -- Organizations
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'organizations'
                   AND column_name = 'id'
                   AND column_default IS NOT NULL) THEN
        ALTER TABLE organizations ALTER COLUMN id SET DEFAULT uuid_generate_v4()::TEXT;
    END IF;

    -- Users
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'users'
                   AND column_name = 'id'
                   AND column_default IS NOT NULL) THEN
        ALTER TABLE users ALTER COLUMN id SET DEFAULT uuid_generate_v4()::TEXT;
    END IF;

    -- Buildings
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'buildings'
                   AND column_name = 'id'
                   AND column_default IS NOT NULL) THEN
        ALTER TABLE buildings ALTER COLUMN id SET DEFAULT uuid_generate_v4()::TEXT;
    END IF;
END $$;

-- =============================================================================
-- Add Spatial Index for Building Locations (PostgreSQL specific)
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_buildings_location_spatial
ON buildings USING gist (
    point(longitude, latitude)
);

-- =============================================================================
-- Create Partitioned Timeseries Table (PostgreSQL specific)
-- =============================================================================
-- Rename existing table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'timeseries_data'
               AND table_type = 'BASE TABLE') THEN
        ALTER TABLE timeseries_data RENAME TO timeseries_data_old;
    END IF;
END $$;

-- Create partitioned table
CREATE TABLE IF NOT EXISTS timeseries_data (
    point_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value TEXT NOT NULL,
    quality INTEGER DEFAULT 100,
    PRIMARY KEY (point_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions for the current and next year
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('month', CURRENT_DATE);
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..23 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'timeseries_data_' || TO_CHAR(start_date, 'YYYY_MM');

        IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
            EXECUTE format('CREATE TABLE %I PARTITION OF timeseries_data
                           FOR VALUES FROM (%L) TO (%L)',
                           partition_name, start_date, end_date);
        END IF;

        start_date := end_date;
    END LOOP;
END $$;

-- =============================================================================
-- Add Update Triggers for updated_at columns
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for all tables with updated_at column
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT table_name
             FROM information_schema.columns
             WHERE column_name = 'updated_at'
             AND table_schema = 'public'
    LOOP
        EXECUTE format('CREATE TRIGGER update_%I_updated_at
                       BEFORE UPDATE ON %I
                       FOR EACH ROW
                       EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END $$;

-- =============================================================================
-- Create Views for Common Queries
-- =============================================================================

-- Building overview with counts
CREATE OR REPLACE VIEW v_building_overview AS
SELECT
    b.id,
    b.arxos_id,
    b.name,
    b.status,
    COUNT(DISTINCT f.id) as floor_count,
    COUNT(DISTINCT r.id) as room_count,
    COUNT(DISTINCT e.id) as equipment_count,
    COUNT(DISTINCT p.id) as point_count
FROM buildings b
LEFT JOIN floors f ON b.id = f.building_id
LEFT JOIN rooms r ON f.id = r.floor_id
LEFT JOIN equipment e ON b.id = e.building_id
LEFT JOIN points p ON e.id = p.equipment_id
GROUP BY b.id, b.arxos_id, b.name, b.status;

-- Active alarms view
CREATE OR REPLACE VIEW v_active_alarms AS
SELECT
    a.*,
    p.name as point_name,
    e.name as equipment_name,
    e.equipment_tag,
    b.arxos_id as building_arxos_id,
    b.name as building_name
FROM alarms a
LEFT JOIN points p ON a.point_id = p.id
LEFT JOIN equipment e ON a.equipment_id = e.id OR p.equipment_id = e.id
LEFT JOIN buildings b ON e.building_id = b.id
WHERE a.state = 'active'
ORDER BY
    CASE a.severity
        WHEN 'critical' THEN 1
        WHEN 'major' THEN 2
        WHEN 'minor' THEN 3
        WHEN 'warning' THEN 4
        WHEN 'info' THEN 5
    END,
    a.triggered_at DESC;

-- Equipment maintenance due view
CREATE OR REPLACE VIEW v_maintenance_due AS
SELECT
    e.id,
    e.equipment_tag,
    e.name,
    e.equipment_type,
    b.arxos_id as building_arxos_id,
    b.name as building_name,
    MAX(m.performed_at) as last_maintenance,
    MIN(m.next_due_date) as next_due_date,
    CASE
        WHEN MIN(m.next_due_date) < CURRENT_DATE THEN 'overdue'
        WHEN MIN(m.next_due_date) <= CURRENT_DATE + INTERVAL '30 days' THEN 'due_soon'
        ELSE 'scheduled'
    END as maintenance_status
FROM equipment e
JOIN buildings b ON e.building_id = b.id
LEFT JOIN maintenance_records m ON e.id = m.equipment_id
WHERE m.next_due_date IS NOT NULL
GROUP BY e.id, e.equipment_tag, e.name, e.equipment_type, b.arxos_id, b.name
ORDER BY MIN(m.next_due_date);

-- =============================================================================
-- Create Indexes for JSON queries (PostgreSQL specific)
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_buildings_metadata ON buildings USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_equipment_metadata ON equipment USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_points_metadata ON points USING gin (metadata);

-- =============================================================================
-- Add Full Text Search (PostgreSQL specific)
-- =============================================================================
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS search_vector tsvector;
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS search_vector tsvector;
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Update search vectors
UPDATE buildings SET search_vector =
    to_tsvector('english', coalesce(name, '') || ' ' ||
                           coalesce(address, '') || ' ' ||
                           coalesce(city, ''));

UPDATE equipment SET search_vector =
    to_tsvector('english', coalesce(name, '') || ' ' ||
                           coalesce(equipment_tag, '') || ' ' ||
                           coalesce(manufacturer, '') || ' ' ||
                           coalesce(model, ''));

UPDATE rooms SET search_vector =
    to_tsvector('english', coalesce(name, '') || ' ' ||
                           coalesce(room_number, '') || ' ' ||
                           coalesce(room_type, ''));

-- Create indexes for full text search
CREATE INDEX IF NOT EXISTS idx_buildings_search ON buildings USING gin (search_vector);
CREATE INDEX IF NOT EXISTS idx_equipment_search ON equipment USING gin (search_vector);
CREATE INDEX IF NOT EXISTS idx_rooms_search ON rooms USING gin (search_vector);

-- Create triggers to keep search vectors updated
CREATE OR REPLACE FUNCTION update_buildings_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        coalesce(NEW.name, '') || ' ' ||
        coalesce(NEW.address, '') || ' ' ||
        coalesce(NEW.city, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_buildings_search
BEFORE INSERT OR UPDATE ON buildings
FOR EACH ROW EXECUTE FUNCTION update_buildings_search_vector();

CREATE OR REPLACE FUNCTION update_equipment_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        coalesce(NEW.name, '') || ' ' ||
        coalesce(NEW.equipment_tag, '') || ' ' ||
        coalesce(NEW.manufacturer, '') || ' ' ||
        coalesce(NEW.model, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_equipment_search
BEFORE INSERT OR UPDATE ON equipment
FOR EACH ROW EXECUTE FUNCTION update_equipment_search_vector();

CREATE OR REPLACE FUNCTION update_rooms_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        coalesce(NEW.name, '') || ' ' ||
        coalesce(NEW.room_number, '') || ' ' ||
        coalesce(NEW.room_type, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_rooms_search
BEFORE INSERT OR UPDATE ON rooms
FOR EACH ROW EXECUTE FUNCTION update_rooms_search_vector();