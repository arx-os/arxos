-- Rollback: Rename domain-agnostic fields back to building-centric names

-- Rename space_tree → building_tree
ALTER TABLE version_snapshots
    RENAME COLUMN space_tree TO building_tree;

-- Rename item_tree → equipment_tree
ALTER TABLE version_snapshots
    RENAME COLUMN item_tree TO equipment_tree;

-- Restore original index
DROP INDEX IF EXISTS idx_version_snapshots_trees;
CREATE INDEX idx_version_snapshots_trees ON version_snapshots(building_tree, equipment_tree, spatial_tree);

-- Restore original comments
COMMENT ON COLUMN version_snapshots.building_tree IS 'Hash of building structure Merkle tree';
COMMENT ON COLUMN version_snapshots.equipment_tree IS 'Hash of equipment Merkle tree';
COMMENT ON TABLE version_snapshots IS 'Version snapshots for building repositories';

