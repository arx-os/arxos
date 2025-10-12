-- Create floor_plans compatibility view/table
-- Maps the floors table to expected floor_plans structure for backward compatibility

-- Create floor_plans as a view that maps to floors table
CREATE OR REPLACE VIEW floor_plans AS
SELECT
    f.id,
    f.name,
    b.arxos_id as building,
    f.level,
    f.created_at,
    f.updated_at
FROM floors f
LEFT JOIN buildings b ON f.building_id = b.id;

-- Note: Removed default floor insert as it would violate foreign key constraints
-- Applications should create floors explicitly for existing buildings
