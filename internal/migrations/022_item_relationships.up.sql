-- Migration: 022_item_relationships.up.sql
-- Description: Create item_relationships table for equipment topology and graph traversal
-- Author: ArxOS Team
-- Date: 2025-10-12

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Item Relationships table for graph-based topology
CREATE TABLE IF NOT EXISTS item_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_item_id TEXT NOT NULL,
    to_item_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    strength REAL DEFAULT 1.0, -- Relationship strength (0-1)
    bidirectional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,

    -- Ensure from and to are different
    CHECK (from_item_id != to_item_id),

    -- Prevent duplicate relationships
    UNIQUE (from_item_id, to_item_id, relationship_type)
);

-- Add category and subtype fields to equipment for better organization
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS subtype TEXT;
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS parent_id TEXT;
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS system_id TEXT;
ALTER TABLE equipment ADD COLUMN IF NOT EXISTS tags TEXT[];

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_item_relationships_from ON item_relationships(from_item_id);
CREATE INDEX IF NOT EXISTS idx_item_relationships_to ON item_relationships(to_item_id);
CREATE INDEX IF NOT EXISTS idx_item_relationships_type ON item_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_item_relationships_created ON item_relationships(created_at);

-- Composite index for graph traversal
CREATE INDEX IF NOT EXISTS idx_item_relationships_graph ON item_relationships(from_item_id, to_item_id, relationship_type);

-- Equipment category and subtype indexes
CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment(category);
CREATE INDEX IF NOT EXISTS idx_equipment_subtype ON equipment(subtype);
CREATE INDEX IF NOT EXISTS idx_equipment_parent ON equipment(parent_id);
CREATE INDEX IF NOT EXISTS idx_equipment_system ON equipment(system_id);
CREATE INDEX IF NOT EXISTS idx_equipment_tags ON equipment USING GIN(tags);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_item_relationships_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_item_relationships_updated_at
    BEFORE UPDATE ON item_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_item_relationships_updated_at();

-- Add comments for documentation
COMMENT ON TABLE item_relationships IS 'Graph-based relationships between equipment items for topology modeling';
COMMENT ON COLUMN item_relationships.relationship_type IS 'Type of relationship: feeds, controls, contains, parent_of, connects_to, powers, cools, monitors, etc.';
COMMENT ON COLUMN item_relationships.properties IS 'Additional metadata about the relationship (e.g., voltage, bandwidth, flow rate)';
COMMENT ON COLUMN item_relationships.strength IS 'Relationship strength or importance (0-1 scale)';
COMMENT ON COLUMN item_relationships.bidirectional IS 'Whether the relationship is bidirectional';

COMMENT ON COLUMN equipment.category IS 'High-level category: electrical, network, hvac, plumbing, custodial, safety, it, av, etc.';
COMMENT ON COLUMN equipment.subtype IS 'Specific type: transformer, panel, outlet, spill_marker, desktop_config, etc.';
COMMENT ON COLUMN equipment.parent_id IS 'Direct parent item for quick hierarchy lookup';
COMMENT ON COLUMN equipment.system_id IS 'Optional system membership (electrical system, HVAC zone, etc.)';
COMMENT ON COLUMN equipment.tags IS 'Array of tags for filtering: critical, inspected, high_voltage, etc.';

