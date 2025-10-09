-- Migration 013: Version Control System
-- Implements Git-like version control for building data
-- Based on ADR-007: Version Control System Architecture

-- Object store (content-addressable storage)
CREATE TABLE IF NOT EXISTS version_objects (
    hash         TEXT PRIMARY KEY,
    type         TEXT NOT NULL CHECK (type IN ('blob', 'tree', 'snapshot', 'version')),
    size         BIGINT NOT NULL CHECK (size >= 0),
    contents     BYTEA,              -- For small objects (< 1KB)
    store_path   TEXT,               -- For large objects (filesystem path)
    compressed   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ref_count    INTEGER NOT NULL DEFAULT 0 CHECK (ref_count >= 0)
);

-- Indexes for object store
CREATE INDEX IF NOT EXISTS idx_version_objects_type ON version_objects(type);
CREATE INDEX IF NOT EXISTS idx_version_objects_created ON version_objects(created_at);
CREATE INDEX IF NOT EXISTS idx_version_objects_ref_count ON version_objects(ref_count) WHERE ref_count = 0;

-- Snapshots (building state at a point in time)
CREATE TABLE IF NOT EXISTS version_snapshots (
    hash            TEXT PRIMARY KEY,
    repository_id   UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    building_tree   TEXT NOT NULL REFERENCES version_objects(hash),
    equipment_tree  TEXT NOT NULL REFERENCES version_objects(hash),
    spatial_tree    TEXT NOT NULL REFERENCES version_objects(hash),
    files_tree      TEXT NOT NULL REFERENCES version_objects(hash),
    operations_tree TEXT NOT NULL REFERENCES version_objects(hash),
    metadata        JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for snapshots
CREATE INDEX IF NOT EXISTS idx_version_snapshots_repository ON version_snapshots(repository_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_version_snapshots_trees ON version_snapshots(building_tree, equipment_tree, spatial_tree);

-- Versions (commits)
CREATE TABLE IF NOT EXISTS versions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hash          TEXT UNIQUE NOT NULL,
    repository_id UUID NOT NULL REFERENCES building_repositories(id) ON DELETE CASCADE,
    snapshot      TEXT NOT NULL REFERENCES version_snapshots(hash),
    parent        TEXT REFERENCES versions(hash),
    tag           TEXT,
    message       TEXT NOT NULL,
    author_name   TEXT NOT NULL,
    author_email  TEXT NOT NULL,
    author_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata      JSONB NOT NULL,

    CONSTRAINT versions_unique_tag UNIQUE(repository_id, tag)
);

-- Indexes for versions
CREATE INDEX IF NOT EXISTS idx_versions_repository ON versions(repository_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_versions_tag ON versions(repository_id, tag) WHERE tag IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_versions_parent ON versions(parent);
CREATE INDEX IF NOT EXISTS idx_versions_snapshot ON versions(snapshot);
CREATE INDEX IF NOT EXISTS idx_versions_hash ON versions(hash);

-- Parent relationships (for merge commits with multiple parents)
CREATE TABLE IF NOT EXISTS version_parents (
    version_hash TEXT NOT NULL REFERENCES versions(hash) ON DELETE CASCADE,
    parent_hash  TEXT NOT NULL REFERENCES versions(hash) ON DELETE CASCADE,
    parent_order INT NOT NULL CHECK (parent_order >= 0),
    PRIMARY KEY (version_hash, parent_hash)
);

-- Index for parent relationships
CREATE INDEX IF NOT EXISTS idx_version_parents_version ON version_parents(version_hash);
CREATE INDEX IF NOT EXISTS idx_version_parents_parent ON version_parents(parent_hash);

-- Spatial version metadata (for spatial queries on versions)
CREATE TABLE IF NOT EXISTS version_spatial_metadata (
    snapshot_hash TEXT PRIMARY KEY REFERENCES version_snapshots(hash) ON DELETE CASCADE,
    bounds        GEOMETRY(POLYGON, 4326) NOT NULL,
    center        GEOMETRY(POINT, 4326) NOT NULL,
    floor_count   INTEGER NOT NULL CHECK (floor_count >= 0),
    room_count    INTEGER NOT NULL CHECK (room_count >= 0),
    total_area    NUMERIC(10,2) NOT NULL CHECK (total_area >= 0)
);

-- Spatial index for version metadata
CREATE INDEX IF NOT EXISTS idx_version_spatial_bounds ON version_spatial_metadata USING GIST(bounds);
CREATE INDEX IF NOT EXISTS idx_version_spatial_center ON version_spatial_metadata USING GIST(center);

-- Comments for documentation
COMMENT ON TABLE version_objects IS 'Content-addressable object store for version control (Git-like)';
COMMENT ON TABLE version_snapshots IS 'Building state snapshots using Merkle trees';
COMMENT ON TABLE versions IS 'Version commits with metadata and parent relationships';
COMMENT ON TABLE version_parents IS 'Multiple parent relationships for merge commits';
COMMENT ON TABLE version_spatial_metadata IS 'Spatial metadata for version snapshots';

COMMENT ON COLUMN version_objects.hash IS 'SHA-256 hash of object contents (content-addressable)';
COMMENT ON COLUMN version_objects.type IS 'Object type: blob, tree, snapshot, or version';
COMMENT ON COLUMN version_objects.contents IS 'Object contents for small objects (< 1KB)';
COMMENT ON COLUMN version_objects.store_path IS 'Filesystem path for large objects (>= 1KB)';
COMMENT ON COLUMN version_objects.ref_count IS 'Reference count for garbage collection';

COMMENT ON COLUMN version_snapshots.building_tree IS 'Hash of building structure Merkle tree';
COMMENT ON COLUMN version_snapshots.equipment_tree IS 'Hash of equipment Merkle tree';
COMMENT ON COLUMN version_snapshots.spatial_tree IS 'Hash of spatial data Merkle tree';
COMMENT ON COLUMN version_snapshots.files_tree IS 'Hash of files Merkle tree';
COMMENT ON COLUMN version_snapshots.operations_tree IS 'Hash of operations data Merkle tree';

COMMENT ON COLUMN versions.hash IS 'SHA-256 hash of version (calculated from snapshot + metadata)';
COMMENT ON COLUMN versions.snapshot IS 'Reference to building state snapshot';
COMMENT ON COLUMN versions.parent IS 'Primary parent version (for version graph)';
COMMENT ON COLUMN versions.tag IS 'Semantic version tag (e.g., v1.0.0)';

