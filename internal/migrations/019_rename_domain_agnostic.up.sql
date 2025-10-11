-- Migration: Rename building-centric fields to domain-agnostic names
-- This aligns the database with ArxOS's "blank slate" vision
-- ArxOS works for buildings, ships, warehouses, or any spatial structure

-- Rename building_tree → space_tree in version_snapshots
ALTER TABLE version_snapshots
    RENAME COLUMN building_tree TO space_tree;

-- Rename equipment_tree → item_tree in version_snapshots
ALTER TABLE version_snapshots
    RENAME COLUMN equipment_tree TO item_tree;

-- Update index to use new column names
DROP INDEX IF EXISTS idx_version_snapshots_trees;
CREATE INDEX idx_version_snapshots_trees ON version_snapshots(space_tree, item_tree, spatial_tree);

-- Update column comments to reflect domain-agnostic nature
COMMENT ON COLUMN version_snapshots.space_tree IS 'Hash of spatial hierarchy Merkle tree (buildings, ships, warehouses, etc.)';
COMMENT ON COLUMN version_snapshots.item_tree IS 'Hash of items Merkle tree (equipment, cargo, inventory, etc.)';

-- Add comment explaining the vision
COMMENT ON TABLE version_snapshots IS 'Version snapshots for spatial structures. Domain-agnostic: works for buildings, ships, warehouses, or any spatial hierarchy.';

