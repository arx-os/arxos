-- Create core fractal ArxObject tables
-- Implements the scale-aware data model for infinite zoom

SET search_path TO fractal, public;

-- Main fractal objects table with scale awareness
CREATE TABLE IF NOT EXISTS fractal_arxobjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID REFERENCES fractal_arxobjects(id) ON DELETE CASCADE,
    
    -- Object identity
    object_type VARCHAR(255) NOT NULL,
    object_subtype VARCHAR(255),
    name VARCHAR(500),
    description TEXT,
    
    -- Spatial coordinates (millimeter precision)
    -- Using DECIMAL for exact precision without floating point errors
    position_x DECIMAL(15,9) NOT NULL,  -- Up to 1km with mm precision
    position_y DECIMAL(15,9) NOT NULL,
    position_z DECIMAL(15,9) DEFAULT 0,
    
    -- Rotation in degrees
    rotation_x DECIMAL(7,4) DEFAULT 0,
    rotation_y DECIMAL(7,4) DEFAULT 0,
    rotation_z DECIMAL(7,4) DEFAULT 0,
    
    -- Scale information (meters per pixel)
    min_scale DECIMAL(10,8) NOT NULL,      -- Minimum meaningful scale
    max_scale DECIMAL(10,8) NOT NULL,      -- Maximum meaningful scale  
    optimal_scale DECIMAL(10,8) NOT NULL,  -- Best viewing scale
    
    -- Importance for progressive loading
    importance_level INTEGER NOT NULL DEFAULT 3
        CHECK (importance_level BETWEEN 1 AND 4),
    -- 1=critical (always show), 2=important, 3=detail, 4=optional
    
    -- Physical dimensions in millimeters
    width DECIMAL(10,6),
    height DECIMAL(10,6),
    depth DECIMAL(10,6),
    
    -- Flexible properties and metadata
    properties JSONB NOT NULL DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    -- Versioning and audit
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT valid_scale_range 
        CHECK (min_scale <= optimal_scale AND optimal_scale <= max_scale),
    CONSTRAINT valid_dimensions 
        CHECK (width IS NULL OR width >= 0)
        AND (height IS NULL OR height >= 0)
        AND (depth IS NULL OR depth >= 0),
    CONSTRAINT valid_rotation
        CHECK (rotation_x BETWEEN -180 AND 180)
        AND (rotation_y BETWEEN -180 AND 180)
        AND (rotation_z BETWEEN -180 AND 180)
);

-- Create spatial column for PostGIS operations
SELECT AddGeometryColumn('fractal', 'fractal_arxobjects', 'geom', 4326, 'POINT', 3);

-- Update geometry when position changes
CREATE OR REPLACE FUNCTION update_fractal_geom()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom = ST_SetSRID(
        ST_MakePoint(
            NEW.position_x::float,
            NEW.position_y::float,
            NEW.position_z::float
        ),
        4326
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_fractal_geom_trigger
    BEFORE INSERT OR UPDATE OF position_x, position_y, position_z
    ON fractal_arxobjects
    FOR EACH ROW
    EXECUTE FUNCTION update_fractal_geom();

-- Visibility rules for different scales
CREATE TABLE IF NOT EXISTS visibility_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxobject_id UUID NOT NULL REFERENCES fractal_arxobjects(id) ON DELETE CASCADE,
    
    -- Zoom range where object is visible
    min_zoom DECIMAL(10,8) NOT NULL,
    max_zoom DECIMAL(10,8) NOT NULL,
    
    -- Style and rendering options at different scales
    render_style JSONB DEFAULT '{}',
    simplification_level INTEGER DEFAULT 0,  -- Level of detail (0=full, higher=simplified)
    opacity DECIMAL(3,2) DEFAULT 1.0 CHECK (opacity BETWEEN 0 AND 1),
    
    -- Conditional visibility
    condition_expression TEXT,  -- SQL expression for dynamic visibility
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_zoom_range CHECK (min_zoom <= max_zoom)
);

-- Contributions at different scales
CREATE TABLE IF NOT EXISTS scale_contributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxobject_id UUID NOT NULL REFERENCES fractal_arxobjects(id) ON DELETE CASCADE,
    
    -- Contributor information
    contributor_id UUID NOT NULL,
    contribution_scale DECIMAL(10,8) NOT NULL,  -- Scale at which contributed
    
    -- Contribution details
    contribution_type VARCHAR(100) NOT NULL,
    -- Types: 'geometry', 'specification', 'schematic', 'modification', 'validation', 'photo'
    
    data JSONB NOT NULL,
    attachments TEXT[],  -- URLs to attached files in MinIO
    
    -- Quality and validation
    confidence_score DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence_score BETWEEN 0 AND 1),
    peer_validations INTEGER DEFAULT 0,
    validation_status VARCHAR(50) DEFAULT 'pending',
    -- Status: 'pending', 'validated', 'disputed', 'rejected'
    
    -- Rewards
    bilt_earned DECIMAL(18,8),
    bilt_paid BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validated_at TIMESTAMPTZ,
    validated_by UUID,
    
    CONSTRAINT valid_contribution_type CHECK (
        contribution_type IN (
            'geometry', 'specification', 'schematic', 
            'modification', 'validation', 'photo', 
            'measurement', 'material', 'connection'
        )
    )
);

-- Detail levels for lazy loading
CREATE TABLE IF NOT EXISTS arxobject_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxobject_id UUID NOT NULL REFERENCES fractal_arxobjects(id) ON DELETE CASCADE,
    
    -- Detail level (1=basic to 5=microscopic)
    detail_level INTEGER NOT NULL CHECK (detail_level BETWEEN 1 AND 5),
    
    -- Type of detail
    detail_type VARCHAR(100) NOT NULL,
    -- Types: 'visual', 'technical', 'specifications', 'history', 'relationships', 'schematic'
    
    -- The actual detail data
    data JSONB NOT NULL,
    data_size_bytes INTEGER NOT NULL,
    
    -- Storage optimization
    is_compressed BOOLEAN DEFAULT false,
    compression_type VARCHAR(50),
    storage_url TEXT,  -- URL for large binary data in MinIO
    
    -- Cache management
    last_accessed TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    cache_priority INTEGER DEFAULT 3,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tile cache for map-style loading
CREATE TABLE IF NOT EXISTS tile_cache (
    z INTEGER NOT NULL,  -- Zoom level
    x INTEGER NOT NULL,  -- Tile X coordinate
    y INTEGER NOT NULL,  -- Tile Y coordinate
    
    scale DECIMAL(10,8) NOT NULL,
    bounds GEOMETRY(Polygon, 4326) NOT NULL,
    
    -- Cached data
    object_count INTEGER NOT NULL,
    objects JSONB NOT NULL,  -- Simplified object data for tile
    
    -- Cache management
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_hit TIMESTAMPTZ,
    
    PRIMARY KEY (z, x, y)
);

-- Performance tracking
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    metric_type VARCHAR(100) NOT NULL,
    -- Types: 'zoom_transition', 'tile_load', 'detail_fetch', 'render_frame'
    
    -- Timing data
    duration_ms DECIMAL(10,3) NOT NULL,
    
    -- Context
    scale_from DECIMAL(10,8),
    scale_to DECIMAL(10,8),
    viewport_bounds GEOMETRY(Polygon, 4326),
    object_count INTEGER,
    
    -- User and session
    user_id UUID,
    session_id UUID,
    
    -- Device capabilities
    device_memory_gb DECIMAL(4,2),
    device_cores INTEGER,
    browser_info JSONB,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_fractal_spatial ON fractal_arxobjects USING GIST (geom);
CREATE INDEX idx_fractal_scale_range ON fractal_arxobjects (min_scale, max_scale);
CREATE INDEX idx_fractal_optimal_scale ON fractal_arxobjects (optimal_scale);
CREATE INDEX idx_fractal_importance ON fractal_arxobjects (importance_level, optimal_scale);
CREATE INDEX idx_fractal_parent ON fractal_arxobjects (parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_fractal_type_scale ON fractal_arxobjects (object_type, optimal_scale);
CREATE INDEX idx_fractal_tags ON fractal_arxobjects USING GIN (tags);
CREATE INDEX idx_fractal_properties ON fractal_arxobjects USING GIN (properties);

CREATE INDEX idx_visibility_object ON visibility_rules (arxobject_id);
CREATE INDEX idx_visibility_zoom ON visibility_rules (min_zoom, max_zoom);

CREATE INDEX idx_contrib_object ON scale_contributions (arxobject_id);
CREATE INDEX idx_contrib_scale ON scale_contributions (contribution_scale);
CREATE INDEX idx_contrib_type ON scale_contributions (contribution_type, contribution_scale);
CREATE INDEX idx_contrib_contributor ON scale_contributions (contributor_id, created_at DESC);
CREATE INDEX idx_contrib_validation ON scale_contributions (validation_status) 
    WHERE validation_status = 'pending';

CREATE INDEX idx_detail_object_level ON arxobject_details (arxobject_id, detail_level);
CREATE INDEX idx_detail_type ON arxobject_details (detail_type);
CREATE INDEX idx_detail_access ON arxobject_details (last_accessed, access_count);

CREATE INDEX idx_tile_cache_bounds ON tile_cache USING GIST (bounds);
CREATE INDEX idx_tile_expires ON tile_cache (expires_at);

CREATE INDEX idx_perf_metrics_type ON performance_metrics (metric_type, created_at DESC);
CREATE INDEX idx_perf_metrics_user ON performance_metrics (user_id, created_at DESC);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_fractal_arxobjects_updated_at 
    BEFORE UPDATE ON fractal_arxobjects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_visibility_rules_updated_at 
    BEFORE UPDATE ON visibility_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_arxobject_details_updated_at 
    BEFORE UPDATE ON arxobject_details 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Convert performance_metrics to TimescaleDB hypertable for efficient time-series queries
SELECT create_hypertable('performance_metrics', 'created_at', if_not_exists => TRUE);

-- Add compression policy for old metrics (compress after 7 days)
SELECT add_compression_policy('performance_metrics', INTERVAL '7 days');

-- Add retention policy (delete after 90 days)
SELECT add_retention_policy('performance_metrics', INTERVAL '90 days');

-- Create continuous aggregate for performance analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_performance_stats
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', created_at) AS hour,
    metric_type,
    COUNT(*) as count,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as median_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms
FROM performance_metrics
GROUP BY hour, metric_type
WITH NO DATA;

-- Refresh the continuous aggregate
SELECT add_continuous_aggregate_policy('hourly_performance_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');