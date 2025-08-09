-- 003_create_slow_query_log.sql
-- Migration: Create slow query logging table for performance monitoring
--
-- This table stores parsed slow query metrics for trend analysis and
-- performance optimization. It follows Arxos logging standards with
-- structured data and comprehensive indexing.

-- =============================================================================
-- SLOW QUERY LOG TABLE
-- =============================================================================

CREATE TABLE slow_query_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER NOT NULL,
    statement TEXT NOT NULL,
    query_hash VARCHAR(32) NOT NULL,
    user_name VARCHAR(100),
    database_name VARCHAR(100),
    application_name VARCHAR(100),
    client_ip INET,
    process_id VARCHAR(20),
    session_id VARCHAR(20),
    execution_plan TEXT,
    context JSONB,
    severity VARCHAR(20) DEFAULT 'info',
    frequency_per_hour DECIMAL(10,2),
    avg_duration_ms DECIMAL(10,2),
    max_duration_ms INTEGER,
    min_duration_ms INTEGER,
    total_executions INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Primary performance indexes
CREATE INDEX idx_slow_query_log_timestamp ON slow_query_log (timestamp);
CREATE INDEX idx_slow_query_log_duration_ms ON slow_query_log (duration_ms);
CREATE INDEX idx_slow_query_log_query_hash ON slow_query_log (query_hash);
CREATE INDEX idx_slow_query_log_severity ON slow_query_log (severity);

-- User and application indexes
CREATE INDEX idx_slow_query_log_user_name ON slow_query_log (user_name);
CREATE INDEX idx_slow_query_log_database_name ON slow_query_log (database_name);
CREATE INDEX idx_slow_query_log_application_name ON slow_query_log (application_name);

-- Composite indexes for common queries
CREATE INDEX idx_slow_query_log_timestamp_severity ON slow_query_log (timestamp, severity);
CREATE INDEX idx_slow_query_log_duration_severity ON slow_query_log (duration_ms, severity);
CREATE INDEX idx_slow_query_log_user_timestamp ON slow_query_log (user_name, timestamp);
CREATE INDEX idx_slow_query_log_app_timestamp ON slow_query_log (application_name, timestamp);

-- Partial indexes for high-impact queries
CREATE INDEX idx_slow_query_log_critical ON slow_query_log (timestamp, duration_ms)
    WHERE severity = 'critical';
CREATE INDEX idx_slow_query_log_warning ON slow_query_log (timestamp, duration_ms)
    WHERE severity = 'warning';

-- Recent queries index (last 30 days)
CREATE INDEX idx_slow_query_log_recent ON slow_query_log (timestamp, severity)
    WHERE timestamp > NOW() - INTERVAL '30 days';

-- =============================================================================
-- PERFORMANCE MONITORING VIEWS
-- =============================================================================

-- View for critical slow queries
CREATE VIEW v_critical_slow_queries AS
SELECT
    query_hash,
    statement,
    COUNT(*) as execution_count,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    SUM(duration_ms) as total_duration_ms,
    COUNT(DISTINCT user_name) as unique_users,
    COUNT(DISTINCT application_name) as unique_applications,
    MAX(timestamp) as last_execution,
    MIN(timestamp) as first_execution
FROM slow_query_log
WHERE severity = 'critical'
GROUP BY query_hash, statement
ORDER BY total_duration_ms DESC;

-- View for query performance trends
CREATE VIEW v_query_performance_trends AS
SELECT
    DATE_TRUNC('hour', timestamp) as hour_bucket,
    severity,
    COUNT(*) as query_count,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    SUM(duration_ms) as total_duration_ms
FROM slow_query_log
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp), severity
ORDER BY hour_bucket DESC, severity;

-- View for user performance analysis
CREATE VIEW v_user_performance_analysis AS
SELECT
    user_name,
    COUNT(*) as total_queries,
    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_queries,
    COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_queries,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    SUM(duration_ms) as total_duration_ms,
    MAX(timestamp) as last_activity,
    MIN(timestamp) as first_activity
FROM slow_query_log
WHERE user_name IS NOT NULL
GROUP BY user_name
ORDER BY total_duration_ms DESC;

-- View for application performance analysis
CREATE VIEW v_application_performance_analysis AS
SELECT
    application_name,
    COUNT(*) as total_queries,
    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_queries,
    COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_queries,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    SUM(duration_ms) as total_duration_ms,
    COUNT(DISTINCT user_name) as unique_users,
    MAX(timestamp) as last_activity,
    MIN(timestamp) as first_activity
FROM slow_query_log
WHERE application_name IS NOT NULL
GROUP BY application_name
ORDER BY total_duration_ms DESC;

-- =============================================================================
-- CLEANUP AND MAINTENANCE FUNCTIONS
-- =============================================================================

-- Function to clean old slow query logs (older than 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_slow_query_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM slow_query_log
    WHERE timestamp < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log the cleanup operation
    INSERT INTO audit_logs (object_type, object_id, action, payload)
    VALUES ('slow_query_log', 'cleanup', 'cleanup_old_logs',
            jsonb_build_object('deleted_count', deleted_count, 'cutoff_date', NOW() - INTERVAL '90 days'));

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get slow query statistics
CREATE OR REPLACE FUNCTION get_slow_query_stats(days_back INTEGER DEFAULT 7)
RETURNS TABLE (
    total_queries BIGINT,
    critical_queries BIGINT,
    warning_queries BIGINT,
    avg_duration_ms DECIMAL(10,2),
    max_duration_ms INTEGER,
    total_duration_ms BIGINT,
    unique_users BIGINT,
    unique_applications BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_queries,
        COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_queries,
        COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_queries,
        AVG(duration_ms) as avg_duration_ms,
        MAX(duration_ms) as max_duration_ms,
        SUM(duration_ms) as total_duration_ms,
        COUNT(DISTINCT user_name) as unique_users,
        COUNT(DISTINCT application_name) as unique_applications
    FROM slow_query_log
    WHERE timestamp > NOW() - (days_back || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_slow_query_log_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_slow_query_log_updated_at
    BEFORE UPDATE ON slow_query_log
    FOR EACH ROW
    EXECUTE FUNCTION update_slow_query_log_updated_at();

-- =============================================================================
-- GRANTS AND PERMISSIONS
-- =============================================================================

-- Grant appropriate permissions
GRANT SELECT ON slow_query_log TO arxos_app;
GRANT INSERT ON slow_query_log TO arxos_app;
GRANT SELECT ON v_critical_slow_queries TO arxos_app;
GRANT SELECT ON v_query_performance_trends TO arxos_app;
GRANT SELECT ON v_user_performance_analysis TO arxos_app;
GRANT SELECT ON v_application_performance_analysis TO arxos_app;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION cleanup_old_slow_query_logs() TO arxos_app;
GRANT EXECUTE ON FUNCTION get_slow_query_stats(INTEGER) TO arxos_app;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE slow_query_log IS 'Stores parsed slow query metrics for performance analysis and trend tracking';
COMMENT ON COLUMN slow_query_log.query_hash IS 'MD5 hash of normalized query for deduplication';
COMMENT ON COLUMN slow_query_log.severity IS 'Query severity: critical, warning, or info';
COMMENT ON COLUMN slow_query_log.context IS 'Additional context data in JSON format';

COMMENT ON VIEW v_critical_slow_queries IS 'Aggregated view of critical slow queries for immediate attention';
COMMENT ON VIEW v_query_performance_trends IS 'Hourly performance trends for monitoring query patterns';
COMMENT ON VIEW v_user_performance_analysis IS 'User-specific performance analysis for optimization';
COMMENT ON VIEW v_application_performance_analysis IS 'Application-specific performance analysis';

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================

-- This migration creates a comprehensive slow query logging system that:
-- 1. Stores parsed slow query metrics with full context
-- 2. Provides optimized indexes for fast querying
-- 3. Includes views for common analysis patterns
-- 4. Offers maintenance functions for cleanup and statistics
-- 5. Follows Arxos logging standards with structured data
-- 6. Integrates with existing audit logging system
