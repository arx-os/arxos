-- Enable required PostgreSQL extensions for Fractal ArxObject system
-- This must be run first before other migrations

-- Enable TimescaleDB for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable PostGIS for spatial data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB indexing improvements
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Enable fuzzy string matching for search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create schema for fractal objects
CREATE SCHEMA IF NOT EXISTS fractal;

-- Set search path to include fractal schema
SET search_path TO fractal, public;

-- Verify extensions are loaded
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB version: %', (SELECT extversion FROM pg_extension WHERE extname = 'timescaledb');
    RAISE NOTICE 'PostGIS version: %', (SELECT PostGIS_Version());
    RAISE NOTICE 'Extensions loaded successfully';
END $$;