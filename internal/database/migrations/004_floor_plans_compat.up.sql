-- Create floor_plans compatibility view/table
-- Maps the floors table to expected floor_plans structure for backward compatibility

-- Create floor_plans as a view that maps to floors table
CREATE VIEW IF NOT EXISTS floor_plans AS
SELECT
    f.id,
    f.name,
    b.arxos_id as building,
    f.level,
    f.created_at,
    f.updated_at
FROM floors f
LEFT JOIN buildings b ON f.building_id = b.id;

-- Insert default building first (if not exists)
INSERT OR IGNORE INTO buildings (id, arxos_id, name, status, created_at, updated_at)
VALUES ('DEFAULT_BUILDING', 'ARXOS-DEFAULT', 'Default Building', 'OPERATIONAL', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Insert default floor if none exist
INSERT OR IGNORE INTO floors (id, building_id, level, name, created_at, updated_at)
VALUES ('DEFAULT_FLOOR', 'DEFAULT_BUILDING', 1, 'Default Floor', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);