-- Migration 013 Down: Remove Version Control System

-- Drop tables in reverse order (respecting foreign keys)
DROP TABLE IF EXISTS version_spatial_metadata;
DROP TABLE IF EXISTS version_parents;
DROP TABLE IF EXISTS versions;
DROP TABLE IF EXISTS version_snapshots;
DROP TABLE IF EXISTS version_objects;

-- Note: Indexes are automatically dropped with their tables

