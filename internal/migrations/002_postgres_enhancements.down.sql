-- ArxOS PostgreSQL Enhancements Rollback
-- Version: 002
-- Description: Remove PostgreSQL-specific features

-- Drop triggers
DROP TRIGGER IF EXISTS update_buildings_search ON buildings;
DROP TRIGGER IF EXISTS update_equipment_search ON equipment;
DROP TRIGGER IF EXISTS update_rooms_search ON rooms;

-- Drop search functions
DROP FUNCTION IF EXISTS update_buildings_search_vector();
DROP FUNCTION IF EXISTS update_equipment_search_vector();
DROP FUNCTION IF EXISTS update_rooms_search_vector();

-- Remove search columns
ALTER TABLE buildings DROP COLUMN IF EXISTS search_vector;
ALTER TABLE equipment DROP COLUMN IF EXISTS search_vector;
ALTER TABLE rooms DROP COLUMN IF EXISTS search_vector;

-- Drop views
DROP VIEW IF EXISTS v_maintenance_due;
DROP VIEW IF EXISTS v_active_alarms;
DROP VIEW IF EXISTS v_building_overview;

-- Drop update triggers
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT table_name
             FROM information_schema.columns
             WHERE column_name = 'updated_at'
             AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', t, t);
    END LOOP;
END $$;

DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop partitioned table and restore original
DROP TABLE IF EXISTS timeseries_data CASCADE;

-- Restore original table if it was renamed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'timeseries_data_old') THEN
        ALTER TABLE timeseries_data_old RENAME TO timeseries_data;
    END IF;
END $$;

-- Note: We don't drop extensions as they might be used by other applications