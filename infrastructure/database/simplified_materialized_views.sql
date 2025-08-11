-- Simplified Materialized Views - Working with Current Schema
-- Real-time analytics for optimization engine

-- =============================================================================
-- BUILDING ANALYTICS MATERIALIZED VIEW (SIMPLIFIED)
-- =============================================================================

CREATE MATERIALIZED VIEW building_analytics AS
SELECT 
    b.id as building_id,
    b.name as building_name,
    b.address,
    
    -- Basic metrics
    COUNT(DISTINCT f.id) as floor_count,
    COUNT(DISTINCT r.id) as room_count,
    COUNT(DISTINCT d.id) as device_count,
    
    -- Spatial metrics
    COALESCE(SUM(ST_Area(r.geom)), 0)::NUMERIC(12,2) as total_floor_area,
    COALESCE(AVG(ST_Area(r.geom)), 0)::NUMERIC(10,2) as avg_room_area,
    
    -- Device distribution
    COUNT(DISTINCT CASE WHEN d.type = 'HVAC' THEN d.id END) as hvac_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Security' THEN d.id END) as security_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Lighting' THEN d.id END) as lighting_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Fire_Safety' THEN d.id END) as fire_safety_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Network' THEN d.id END) as network_devices,
    
    -- Room categories
    COUNT(DISTINCT CASE WHEN r.category = 'office' THEN r.id END) as office_rooms,
    COUNT(DISTINCT CASE WHEN r.category = 'conference' THEN r.id END) as conference_rooms,
    COUNT(DISTINCT CASE WHEN r.category = 'server_room' THEN r.id END) as server_rooms,
    COUNT(DISTINCT CASE WHEN r.category = 'production' THEN r.id END) as production_rooms,
    
    -- Density calculations
    CASE 
        WHEN COUNT(DISTINCT r.id) > 0 THEN 
            COUNT(DISTINCT d.id)::NUMERIC / COUNT(DISTINCT r.id)
        ELSE 0 
    END as devices_per_room,
    
    NOW() as analytics_updated_at
    
FROM buildings b
LEFT JOIN floors f ON f.building_id = b.id
LEFT JOIN rooms r ON r.building_id = b.id
LEFT JOIN devices d ON d.building_id = b.id
GROUP BY b.id, b.name, b.address;

-- =============================================================================
-- ROOM PERFORMANCE MATERIALIZED VIEW (SIMPLIFIED)
-- =============================================================================

CREATE MATERIALIZED VIEW room_performance AS
SELECT 
    r.id as room_id,
    r.name as room_name,
    r.category,
    r.building_id,
    b.name as building_name,
    
    -- Spatial metrics
    ST_Area(r.geom)::NUMERIC(10,2) as area,
    ST_Perimeter(r.geom)::NUMERIC(10,2) as perimeter,
    
    -- Device distribution
    COUNT(d.id) as total_devices,
    COUNT(CASE WHEN d.type = 'HVAC' THEN 1 END) as hvac_count,
    COUNT(CASE WHEN d.type = 'Security' THEN 1 END) as security_count,
    COUNT(CASE WHEN d.type = 'Lighting' THEN 1 END) as lighting_count,
    
    -- Device coverage
    COALESCE(SUM(ST_Area(d.geom)), 0)::NUMERIC(10,2) as total_device_coverage,
    CASE 
        WHEN ST_Area(r.geom) > 0 THEN 
            COALESCE(SUM(ST_Area(d.geom)), 0) / ST_Area(r.geom) * 100
        ELSE 0 
    END as coverage_percentage,
    
    -- Simple efficiency score
    CASE 
        WHEN COUNT(d.id) > 0 AND ST_Area(r.geom) > 9 THEN 
            LEAST(100, COUNT(d.id) * 20 + (ST_Area(r.geom) / 100) * 10)
        WHEN ST_Area(r.geom) > 9 THEN 50
        ELSE 25
    END::NUMERIC(8,2) as efficiency_score,
    
    r.status,
    NOW() as performance_updated_at

FROM rooms r
JOIN buildings b ON r.building_id = b.id
LEFT JOIN devices d ON d.room_id = r.id
GROUP BY r.id, r.name, r.category, r.building_id, b.name, r.geom, r.status;

-- =============================================================================
-- OPTIMIZATION ANALYTICS MATERIALIZED VIEW
-- =============================================================================

CREATE MATERIALIZED VIEW optimization_analytics AS
SELECT 
    building_id,
    algorithm_type,
    
    -- Performance metrics
    COUNT(*) as total_runs,
    AVG(optimization_score)::NUMERIC(8,4) as avg_score,
    MIN(optimization_score)::NUMERIC(8,4) as min_score,
    MAX(optimization_score)::NUMERIC(8,4) as max_score,
    
    -- Convergence analysis
    AVG(convergence_rate)::NUMERIC(8,4) as avg_convergence,
    AVG(execution_time_ms)::NUMERIC(10,3) as avg_execution_time,
    MIN(execution_time_ms)::NUMERIC(10,3) as min_execution_time,
    MAX(execution_time_ms)::NUMERIC(10,3) as max_execution_time,
    
    -- Constraint satisfaction
    AVG(constraints_satisfied::NUMERIC)::NUMERIC(8,2) as avg_constraints_satisfied,
    AVG(constraints_violated::NUMERIC)::NUMERIC(8,2) as avg_constraints_violated,
    
    -- Temporal analysis
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as runs_last_hour,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 day' THEN 1 END) as runs_last_day,
    
    -- Latest results
    MAX(created_at) as last_run_time,
    NOW() as analytics_updated_at

FROM optimization_results
GROUP BY building_id, algorithm_type;

-- =============================================================================
-- DEVICE PERFORMANCE DASHBOARD VIEW
-- =============================================================================

CREATE MATERIALIZED VIEW device_performance_dashboard AS
SELECT 
    d.building_id,
    b.name as building_name,
    d.type as device_type,
    d.system as device_system,
    
    -- Device counts
    COUNT(*) as device_count,
    COUNT(CASE WHEN d.status = 'operational' THEN 1 END) as operational_count,
    COUNT(CASE WHEN d.status = 'maintenance' THEN 1 END) as maintenance_count,
    COUNT(CASE WHEN d.status = 'offline' THEN 1 END) as offline_count,
    
    -- Room distribution
    COUNT(DISTINCT d.room_id) as rooms_with_devices,
    
    -- Performance ratio
    CASE 
        WHEN COUNT(*) > 0 THEN 
            COUNT(CASE WHEN d.status = 'operational' THEN 1 END)::NUMERIC / COUNT(*) * 100
        ELSE 0 
    END as operational_percentage,
    
    NOW() as dashboard_updated_at

FROM devices d
JOIN buildings b ON d.building_id = b.id
GROUP BY d.building_id, b.name, d.type, d.system;

-- =============================================================================
-- INDEXES FOR MATERIALIZED VIEWS
-- =============================================================================

-- Building analytics indexes
CREATE INDEX building_analytics_building_id_idx ON building_analytics (building_id);
CREATE INDEX building_analytics_device_count_idx ON building_analytics (device_count DESC);
CREATE INDEX building_analytics_area_idx ON building_analytics (total_floor_area DESC);

-- Room performance indexes
CREATE INDEX room_performance_efficiency_idx ON room_performance (efficiency_score DESC);
CREATE INDEX room_performance_building_idx ON room_performance (building_id, efficiency_score DESC);
CREATE INDEX room_performance_category_idx ON room_performance (category, building_id);

-- Optimization analytics indexes
CREATE INDEX optimization_analytics_building_idx ON optimization_analytics (building_id, algorithm_type);
CREATE INDEX optimization_analytics_score_idx ON optimization_analytics (avg_score DESC);

-- Device performance indexes
CREATE INDEX device_performance_building_idx ON device_performance_dashboard (building_id);
CREATE INDEX device_performance_type_idx ON device_performance_dashboard (device_type, operational_percentage DESC);

-- =============================================================================
-- REFRESH FUNCTIONS
-- =============================================================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_analytics_views()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    total_time INTERVAL;
BEGIN
    start_time := clock_timestamp();
    
    -- Refresh all materialized views
    REFRESH MATERIALIZED VIEW building_analytics;
    REFRESH MATERIALIZED VIEW room_performance;
    REFRESH MATERIALIZED VIEW optimization_analytics;
    REFRESH MATERIALIZED VIEW device_performance_dashboard;
    
    end_time := clock_timestamp();
    total_time := end_time - start_time;
    
    -- Log the refresh operation
    INSERT INTO audit_logs (user_id, object_type, object_id, action, payload)
    VALUES (
        1, -- System user
        'system',
        'materialized_views',
        'refresh_completed',
        jsonb_build_object(
            'refresh_duration_ms', EXTRACT(epoch FROM total_time) * 1000,
            'views_refreshed', 4,
            'timestamp', NOW()
        )
    );
    
    RETURN 'All analytics views refreshed in ' || total_time;
END;
$$;

-- =============================================================================
-- MONITORING VIEWS
-- =============================================================================

-- Analytics performance summary
CREATE OR REPLACE VIEW analytics_performance_summary AS
SELECT 
    'building_analytics' as view_name,
    (SELECT COUNT(*) FROM building_analytics) as record_count,
    (SELECT AVG(device_count) FROM building_analytics) as avg_metric,
    pg_size_pretty(pg_total_relation_size('building_analytics')) as size
UNION ALL
SELECT 
    'room_performance',
    (SELECT COUNT(*) FROM room_performance),
    (SELECT AVG(efficiency_score) FROM room_performance),
    pg_size_pretty(pg_total_relation_size('room_performance'))
UNION ALL
SELECT 
    'optimization_analytics',
    (SELECT COUNT(*) FROM optimization_analytics),
    (SELECT AVG(avg_score) FROM optimization_analytics),
    pg_size_pretty(pg_total_relation_size('optimization_analytics'))
UNION ALL
SELECT 
    'device_performance_dashboard',
    (SELECT COUNT(*) FROM device_performance_dashboard),
    (SELECT AVG(operational_percentage) FROM device_performance_dashboard),
    pg_size_pretty(pg_total_relation_size('device_performance_dashboard'));

-- =============================================================================
-- TEST THE MATERIALIZED VIEWS
-- =============================================================================

-- Test query 1: Building analytics summary
SELECT 
    building_name,
    room_count,
    device_count,
    devices_per_room,
    hvac_devices + security_devices + lighting_devices as total_active_devices
FROM building_analytics 
ORDER BY device_count DESC 
LIMIT 5;

-- Test query 2: Top performing rooms
SELECT 
    room_name,
    building_name,
    category,
    area,
    total_devices,
    coverage_percentage,
    efficiency_score
FROM room_performance 
ORDER BY efficiency_score DESC 
LIMIT 10;

-- Test query 3: Optimization algorithm performance
SELECT 
    building_id,
    algorithm_type,
    total_runs,
    avg_score,
    avg_execution_time
FROM optimization_analytics
ORDER BY avg_score DESC;

-- Test query 4: Device operational status
SELECT 
    building_name,
    device_type,
    device_count,
    operational_count,
    operational_percentage
FROM device_performance_dashboard
WHERE device_count > 0
ORDER BY operational_percentage DESC;

-- =============================================================================
-- SUMMARY STATISTICS
-- =============================================================================

-- Show materialized view creation results
SELECT 'Materialized Views Creation Summary:' as summary;

SELECT 
    schemaname,
    matviewname as view_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size,
    ispopulated
FROM pg_matviews 
WHERE schemaname = 'public'
ORDER BY matviewname;

COMMENT ON MATERIALIZED VIEW building_analytics IS 'Building performance metrics - refresh every 15 minutes for real-time dashboard';
COMMENT ON MATERIALIZED VIEW room_performance IS 'Room efficiency analytics - refresh every 5 minutes';
COMMENT ON MATERIALIZED VIEW optimization_analytics IS 'Algorithm performance tracking - refresh every minute';
COMMENT ON MATERIALIZED VIEW device_performance_dashboard IS 'Device operational status - refresh every 2 minutes';