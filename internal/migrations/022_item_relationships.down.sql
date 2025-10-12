-- Migration: 022_item_relationships.down.sql
-- Description: Rollback item_relationships table and equipment enhancements

-- Drop trigger
DROP TRIGGER IF EXISTS trigger_update_item_relationships_updated_at ON item_relationships;
DROP FUNCTION IF EXISTS update_item_relationships_updated_at();

-- Drop indexes
DROP INDEX IF EXISTS idx_item_relationships_from;
DROP INDEX IF EXISTS idx_item_relationships_to;
DROP INDEX IF EXISTS idx_item_relationships_type;
DROP INDEX IF EXISTS idx_item_relationships_created;
DROP INDEX IF EXISTS idx_item_relationships_graph;

DROP INDEX IF EXISTS idx_equipment_category;
DROP INDEX IF EXISTS idx_equipment_subtype;
DROP INDEX IF EXISTS idx_equipment_parent;
DROP INDEX IF EXISTS idx_equipment_system;
DROP INDEX IF EXISTS idx_equipment_tags;

-- Drop table
DROP TABLE IF EXISTS item_relationships;

-- Remove columns from equipment
ALTER TABLE equipment DROP COLUMN IF EXISTS category;
ALTER TABLE equipment DROP COLUMN IF EXISTS subtype;
ALTER TABLE equipment DROP COLUMN IF EXISTS parent_id;
ALTER TABLE equipment DROP COLUMN IF EXISTS system_id;
ALTER TABLE equipment DROP COLUMN IF EXISTS tags;

