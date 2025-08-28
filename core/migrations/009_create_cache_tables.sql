-- 024_create_cache_tables.sql
-- Migration: Replace Redis with PostgreSQL-based caching system
-- This migration creates efficient cache tables with proper indexing and automatic cleanup

-- ============================================
-- General Purpose Cache Table
-- ============================================
-- Replaces Redis key-value operations with PostgreSQL
CREATE TABLE IF NOT EXISTS cache_entries (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    cache_type VARCHAR(50) NOT NULL DEFAULT 'general',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_count BIGINT DEFAULT 0,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for efficient cache operations
CREATE INDEX idx_cache_entries_expires_at ON cache_entries(expires_at);
CREATE INDEX idx_cache_entries_type ON cache_entries(cache_type);
CREATE INDEX idx_cache_entries_last_accessed ON cache_entries(last_accessed_at);
CREATE INDEX idx_cache_entries_metadata ON cache_entries USING GIN(metadata);

-- ============================================
-- HTTP Response Cache Table
-- ============================================
-- Specialized table for HTTP response caching
CREATE TABLE IF NOT EXISTS http_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    request_method VARCHAR(10) NOT NULL,
    request_path VARCHAR(500) NOT NULL,
    request_query TEXT,
    response_status INTEGER NOT NULL,
    response_headers JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_body BYTEA NOT NULL,
    content_type VARCHAR(100),
    etag VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    hit_count BIGINT DEFAULT 0,
    last_hit_at TIMESTAMP,
    cache_control TEXT,
    vary_headers TEXT[]
);

-- Indexes for HTTP cache
CREATE INDEX idx_http_cache_expires_at ON http_cache(expires_at);
CREATE INDEX idx_http_cache_path ON http_cache(request_path);
CREATE INDEX idx_http_cache_method_path ON http_cache(request_method, request_path);
CREATE INDEX idx_http_cache_etag ON http_cache(etag) WHERE etag IS NOT NULL;
CREATE INDEX idx_http_cache_last_hit ON http_cache(last_hit_at);

-- ============================================
-- Confidence Score Cache Table
-- ============================================
-- Specialized table for ArxObject confidence caching
CREATE TABLE IF NOT EXISTS confidence_cache (
    object_id BIGINT PRIMARY KEY,
    building_id VARCHAR(36),
    confidence_score JSONB NOT NULL,
    validation_count INTEGER DEFAULT 0,
    last_validated_at TIMESTAMP,
    propagation_depth INTEGER DEFAULT 0,
    related_objects BIGINT[] DEFAULT ARRAY[]::BIGINT[],
    pattern_signature VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_count BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for confidence cache
CREATE INDEX idx_confidence_cache_building ON confidence_cache(building_id);
CREATE INDEX idx_confidence_cache_expires_at ON confidence_cache(expires_at);
CREATE INDEX idx_confidence_cache_pattern ON confidence_cache(pattern_signature);
CREATE INDEX idx_confidence_cache_related ON confidence_cache USING GIN(related_objects);
CREATE INDEX idx_confidence_cache_validated ON confidence_cache(last_validated_at);

-- ============================================
-- Cache Statistics Table
-- ============================================
-- Track cache performance metrics
CREATE TABLE IF NOT EXISTS cache_statistics (
    id SERIAL PRIMARY KEY,
    cache_type VARCHAR(50) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    hits BIGINT DEFAULT 0,
    misses BIGINT DEFAULT 0,
    evictions BIGINT DEFAULT 0,
    total_entries BIGINT DEFAULT 0,
    avg_response_time_ms FLOAT,
    memory_usage_bytes BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_stats_period ON cache_statistics(period_start, period_end);
CREATE INDEX idx_cache_stats_type ON cache_statistics(cache_type);

-- ============================================
-- Cache Invalidation Patterns Table
-- ============================================
-- Store invalidation patterns for smart cache clearing
CREATE TABLE IF NOT EXISTS cache_invalidation_patterns (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(100) NOT NULL UNIQUE,
    pattern_regex VARCHAR(500) NOT NULL,
    cache_type VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_invalidation_active ON cache_invalidation_patterns(is_active);
CREATE INDEX idx_cache_invalidation_type ON cache_invalidation_patterns(cache_type);

-- ============================================
-- Functions for Cache Management
-- ============================================

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache() 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired entries from cache_entries
    DELETE FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete expired entries from http_cache
    DELETE FROM http_cache WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Delete expired entries from confidence_cache
    DELETE FROM confidence_cache WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Log statistics
    INSERT INTO cache_statistics (cache_type, period_start, period_end, evictions)
    VALUES ('cleanup', CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP, deleted_count);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get cache entry with automatic access tracking
CREATE OR REPLACE FUNCTION get_cache_entry(p_key VARCHAR(255))
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    -- Update access count and last accessed time
    UPDATE cache_entries 
    SET access_count = access_count + 1,
        last_accessed_at = CURRENT_TIMESTAMP
    WHERE cache_key = p_key 
        AND expires_at > CURRENT_TIMESTAMP
    RETURNING cache_value INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to set cache entry with automatic expiry
CREATE OR REPLACE FUNCTION set_cache_entry(
    p_key VARCHAR(255),
    p_value JSONB,
    p_ttl_seconds INTEGER DEFAULT 300,
    p_type VARCHAR(50) DEFAULT 'general'
)
RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO cache_entries (cache_key, cache_value, cache_type, expires_at)
    VALUES (p_key, p_value, p_type, CURRENT_TIMESTAMP + (p_ttl_seconds || ' seconds')::INTERVAL)
    ON CONFLICT (cache_key) DO UPDATE
    SET cache_value = EXCLUDED.cache_value,
        cache_type = EXCLUDED.cache_type,
        expires_at = EXCLUDED.expires_at,
        updated_at = CURRENT_TIMESTAMP,
        access_count = cache_entries.access_count + 1;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to invalidate cache by pattern
CREATE OR REPLACE FUNCTION invalidate_cache_pattern(p_pattern VARCHAR(255))
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM cache_entries WHERE cache_key LIKE p_pattern;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM http_cache WHERE cache_key LIKE p_pattern;
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get cache statistics
CREATE OR REPLACE FUNCTION get_cache_stats()
RETURNS TABLE(
    cache_type VARCHAR(50),
    total_entries BIGINT,
    expired_entries BIGINT,
    avg_access_count FLOAT,
    memory_usage_estimate BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'general'::VARCHAR(50) as cache_type,
        COUNT(*)::BIGINT as total_entries,
        COUNT(CASE WHEN expires_at < CURRENT_TIMESTAMP THEN 1 END)::BIGINT as expired_entries,
        AVG(access_count)::FLOAT as avg_access_count,
        SUM(pg_column_size(cache_value))::BIGINT as memory_usage_estimate
    FROM cache_entries
    UNION ALL
    SELECT 
        'http'::VARCHAR(50),
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN expires_at < CURRENT_TIMESTAMP THEN 1 END)::BIGINT,
        AVG(hit_count)::FLOAT,
        SUM(pg_column_size(response_body))::BIGINT
    FROM http_cache
    UNION ALL
    SELECT 
        'confidence'::VARCHAR(50),
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN expires_at < CURRENT_TIMESTAMP THEN 1 END)::BIGINT,
        AVG(access_count)::FLOAT,
        SUM(pg_column_size(confidence_score))::BIGINT
    FROM confidence_cache;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Triggers for Automatic Updates
-- ============================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cache_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cache_entries_updated
    BEFORE UPDATE ON cache_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_cache_timestamp();

CREATE TRIGGER trigger_confidence_cache_updated
    BEFORE UPDATE ON confidence_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_cache_timestamp();

-- ============================================
-- Scheduled Jobs (using pg_cron or application-level)
-- ============================================

-- Create a scheduled job to clean expired cache entries every hour
-- Note: This requires pg_cron extension or should be run from application
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('clean-expired-cache', '0 * * * *', 'SELECT clean_expired_cache();');

-- ============================================
-- Initial Data and Configuration
-- ============================================

-- Insert default cache invalidation patterns
INSERT INTO cache_invalidation_patterns (pattern_name, pattern_regex, cache_type, description)
VALUES 
    ('user_cache', 'user:%', 'general', 'Invalidate user-related cache'),
    ('building_cache', 'building:%', 'general', 'Invalidate building-related cache'),
    ('api_response', 'http_cache:api:%', 'http', 'Invalidate API response cache'),
    ('confidence_pattern', 'confidence:%', 'confidence', 'Invalidate confidence scores')
ON CONFLICT (pattern_name) DO NOTHING;

-- ============================================
-- Permissions
-- ============================================

-- Grant permissions to the application user
GRANT SELECT, INSERT, UPDATE, DELETE ON cache_entries TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON http_cache TO arxos_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON confidence_cache TO arxos_api_user;
GRANT SELECT, INSERT ON cache_statistics TO arxos_api_user;
GRANT SELECT ON cache_invalidation_patterns TO arxos_api_user;
GRANT EXECUTE ON FUNCTION get_cache_entry TO arxos_api_user;
GRANT EXECUTE ON FUNCTION set_cache_entry TO arxos_api_user;
GRANT EXECUTE ON FUNCTION invalidate_cache_pattern TO arxos_api_user;
GRANT EXECUTE ON FUNCTION get_cache_stats TO arxos_api_user;
GRANT EXECUTE ON FUNCTION clean_expired_cache TO arxos_api_user;

-- Add comments for documentation
COMMENT ON TABLE cache_entries IS 'General purpose cache table replacing Redis key-value store';
COMMENT ON TABLE http_cache IS 'Specialized cache for HTTP responses with proper headers and ETags';
COMMENT ON TABLE confidence_cache IS 'Cache for AI-extracted ArxObject confidence scores';
COMMENT ON TABLE cache_statistics IS 'Performance metrics and statistics for cache operations';
COMMENT ON TABLE cache_invalidation_patterns IS 'Patterns for smart cache invalidation';