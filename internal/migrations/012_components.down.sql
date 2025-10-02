-- Drop components table and related objects
DROP TRIGGER IF EXISTS trigger_components_updated_at ON components;
DROP FUNCTION IF EXISTS update_components_updated_at();

DROP TABLE IF EXISTS components CASCADE;
