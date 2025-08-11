-- Materialized Views for Real-time Analytics
-- High-performance pre-computed analytics for optimization engine
-- Production-ready views supporting millions of building objects

-- =============================================================================
-- BUILDING ANALYTICS MATERIALIZED VIEW
-- =============================================================================

-- Comprehensive building performance analytics
CREATE MATERIALIZED VIEW building_analytics AS
SELECT 
    b.id as building_id,
    b.name as building_name,
    b.address,
    p.name as project_name,
    
    -- Basic metrics
    COUNT(DISTINCT f.id) as floor_count,
    COUNT(DISTINCT r.id) as room_count,
    COUNT(DISTINCT d.id) as device_count,
    
    -- Spatial metrics
    COALESCE(SUM(ST_Area(r.geom)), 0)::NUMERIC(12,2) as total_floor_area,
    COALESCE(AVG(ST_Area(r.geom)), 0)::NUMERIC(10,2) as avg_room_area,
    COALESCE(SUM(ST_Perimeter(r.geom)), 0)::NUMERIC(12,2) as total_perimeter,
    
    -- Optimization metrics
    calculate_building_optimization_score(b.id) as optimization_score,
    
    -- Device distribution
    COUNT(DISTINCT CASE WHEN d.type = 'HVAC' THEN d.id END) as hvac_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Security' THEN d.id END) as security_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Lighting' THEN d.id END) as lighting_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Fire_Safety' THEN d.id END) as fire_safety_devices,
    COUNT(DISTINCT CASE WHEN d.type = 'Network' THEN d.id END) as network_devices,
    
    -- Room categories
    COUNT(DISTINCT CASE WHEN r.category = 'office' THEN r.id END) as office_rooms,
    COUNT(DISTINCT CASE WHEN r.category = 'conference' THEN r.id END) as conference_rooms,
    COUNT(DISTINCT CASE WHEN r.category = 'common' THEN r.id END) as common_rooms,
    COUNT(DISTINCT CASE WHEN r.category = 'server_room' THEN r.id END) as server_rooms,
    COUNT(DISTINCT CASE WHEN r.category = 'production' THEN r.id END) as production_rooms,
    
    -- Utilization metrics
    COALESCE(AVG(calculate_room_utilization(r.id)), 0)::NUMERIC(8,4) as avg_room_utilization,
    COUNT(DISTINCT CASE WHEN calculate_room_utilization(r.id) > 80 THEN r.id END) as high_utilization_rooms,
    COUNT(DISTINCT CASE WHEN calculate_room_utilization(r.id) < 20 THEN r.id END) as low_utilization_rooms,
    
    -- Conflict metrics
    (SELECT COUNT(*) FROM detect_spatial_conflicts(b.id)) as total_conflicts,
    (SELECT COUNT(*) FROM detect_spatial_conflicts(b.id) WHERE resolution_priority = 1) as critical_conflicts,
    (SELECT COUNT(*) FROM detect_spatial_conflicts(b.id) WHERE resolution_priority = 2) as medium_conflicts,
    (SELECT COUNT(*) FROM detect_spatial_conflicts(b.id) WHERE resolution_priority = 3) as low_conflicts,
    
    -- Constraint compliance
    (SELECT COUNT(*) FROM validate_building_constraints(b.id) WHERE is_satisfied = false) as constraint_violations,
    (SELECT COUNT(*) FROM validate_building_constraints(b.id) WHERE severity_level = 'critical') as critical_violations,
    
    -- Performance metrics
    b.created_at as building_created_at,
    NOW() as analytics_updated_at,
    
    -- Density calculations
    CASE 
        WHEN COUNT(DISTINCT r.id) > 0 THEN 
            COUNT(DISTINCT d.id)::NUMERIC / COUNT(DISTINCT r.id)
        ELSE 0 
    END as devices_per_room,
    
    CASE 
        WHEN SUM(ST_Area(r.geom)) > 0 THEN 
            COUNT(DISTINCT d.id)::NUMERIC / SUM(ST_Area(r.geom)) * 100
        ELSE 0 
    END as device_density_per_100sqm
    
FROM buildings b
LEFT JOIN projects p ON b.project_id = p.id
LEFT JOIN floors f ON f.building_id = b.id
LEFT JOIN rooms r ON r.building_id = b.id
LEFT JOIN devices d ON d.building_id = b.id
GROUP BY b.id, b.name, b.address, p.name, b.created_at;

-- Indexes for building_analytics
CREATE INDEX building_analytics_optimization_score_idx ON building_analytics (optimization_score DESC);
CREATE INDEX building_analytics_conflicts_idx ON building_analytics (total_conflicts);
CREATE INDEX building_analytics_utilization_idx ON building_analytics (avg_room_utilization DESC);
CREATE INDEX building_analytics_area_idx ON building_analytics (total_floor_area DESC);

-- =============================================================================
-- ROOM PERFORMANCE MATERIALIZED VIEW
-- =============================================================================

-- Individual room performance analytics
CREATE MATERIALIZED VIEW room_performance AS
SELECT 
    r.id as room_id,
    r.name as room_name,
    r.category,
    r.building_id,
    b.name as building_name,
    r.floor_id,
    f.name as floor_name,
    
    -- Spatial metrics
    ST_Area(r.geom)::NUMERIC(10,2) as area,
    ST_Perimeter(r.geom)::NUMERIC(10,2) as perimeter,
    ST_X(ST_Centroid(r.geom))::NUMERIC(10,2) as center_x,
    ST_Y(ST_Centroid(r.geom))::NUMERIC(10,2) as center_y,
    
    -- Utilization analysis
    calculate_room_utilization(r.id) as utilization_score,
    CASE 
        WHEN calculate_room_utilization(r.id) >= 80 THEN 'high'
        WHEN calculate_room_utilization(r.id) >= 40 THEN 'medium'
        ELSE 'low'
    END as utilization_category,
    
    -- Device distribution
    COUNT(d.id) as total_devices,
    COUNT(CASE WHEN d.type = 'HVAC' THEN 1 END) as hvac_count,
    COUNT(CASE WHEN d.type = 'Security' THEN 1 END) as security_count,
    COUNT(CASE WHEN d.type = 'Lighting' THEN 1 END) as lighting_count,
    COUNT(CASE WHEN d.type = 'Fire_Safety' THEN 1 END) as fire_safety_count,
    COUNT(CASE WHEN d.type = 'Network' THEN 1 END) as network_count,
    
    -- Device coverage
    COALESCE(SUM(ST_Area(d.geom)), 0)::NUMERIC(10,2) as total_device_coverage,
    CASE 
        WHEN ST_Area(r.geom) > 0 THEN 
            COALESCE(SUM(ST_Area(d.geom)), 0) / ST_Area(r.geom) * 100
        ELSE 0 
    END as coverage_percentage,
    
    -- Conflict analysis
    (SELECT COUNT(*) 
     FROM detect_spatial_conflicts(r.building_id) sc 
     WHERE sc.object1_id = r.id OR sc.object2_id = r.id) as room_conflicts,
     
    -- Constraint violations
    (SELECT COUNT(*) 
     FROM validate_building_constraints(r.building_id) vc 
     WHERE vc.constraint_name LIKE '%room%' 
     AND vc.violation_details LIKE '%' || r.id || '%'
     AND NOT vc.is_satisfied) as constraint_violations,
    
    -- Accessibility metrics
    (SELECT MIN(ST_Distance(r.geom, d2.geom)) 
     FROM doors d2 
     WHERE d2.building_id = r.building_id) as nearest_door_distance,
     
    -- Room efficiency score (composite metric)
    (
        LEAST(100, calculate_room_utilization(r.id)) * 0.4 + -- 40% utilization
        GREATEST(0, 100 - (SELECT COUNT(*) FROM detect_spatial_conflicts(r.building_id) sc 
                          WHERE sc.object1_id = r.id OR sc.object2_id = r.id) * 10) * 0.3 + -- 30% conflict penalty
        CASE 
            WHEN ST_Area(r.geom) >= 9 THEN 100 
            ELSE ST_Area(r.geom) / 9 * 100 
        END * 0.2 + -- 20% size adequacy
        CASE 
            WHEN COUNT(d.id) > 0 THEN LEAST(100, COUNT(d.id) * 20)
            ELSE 0 
        END * 0.1 -- 10% device availability
    )::NUMERIC(8,2) as efficiency_score,
    
    r.status,
    r.created_at as room_created_at,
    NOW() as performance_updated_at

FROM rooms r
JOIN buildings b ON r.building_id = b.id
JOIN floors f ON r.floor_id = f.id
LEFT JOIN devices d ON d.room_id = r.id
GROUP BY r.id, r.name, r.category, r.building_id, b.name, r.floor_id, f.name, 
         r.geom, r.status, r.created_at;

-- Indexes for room_performance
CREATE INDEX room_performance_efficiency_idx ON room_performance (efficiency_score DESC);
CREATE INDEX room_performance_utilization_idx ON room_performance (utilization_score DESC);
CREATE INDEX room_performance_conflicts_idx ON room_performance (room_conflicts);
CREATE INDEX room_performance_category_idx ON room_performance (category, building_id);
CREATE INDEX room_performance_building_idx ON room_performance (building_id, efficiency_score DESC);

-- =============================================================================
-- OPTIMIZATION ANALYTICS MATERIALIZED VIEW  
-- =============================================================================

-- Real-time optimization algorithm performance analytics
CREATE MATERIALIZED VIEW optimization_analytics AS
SELECT 
    building_id,
    algorithm_type,
    
    -- Performance metrics
    COUNT(*) as total_runs,
    AVG(optimization_score)::NUMERIC(8,4) as avg_score,
    MIN(optimization_score)::NUMERIC(8,4) as min_score,
    MAX(optimization_score)::NUMERIC(8,4) as max_score,
    STDDEV(optimization_score)::NUMERIC(8,4) as score_stddev,
    
    -- Convergence analysis
    AVG(convergence_rate)::NUMERIC(8,4) as avg_convergence,
    AVG(execution_time_ms)::NUMERIC(10,3) as avg_execution_time,
    MIN(execution_time_ms)::NUMERIC(10,3) as min_execution_time,
    MAX(execution_time_ms)::NUMERIC(10,3) as max_execution_time,
    
    -- Constraint satisfaction
    AVG(constraints_satisfied::NUMERIC)::NUMERIC(8,2) as avg_constraints_satisfied,
    AVG(constraints_violated::NUMERIC)::NUMERIC(8,2) as avg_constraints_violated,
    SUM(CASE WHEN constraints_violated = 0 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100 as feasible_solutions_pct,
    
    -- Pareto analysis (NSGA-II specific)
    COUNT(CASE WHEN pareto_rank = 1 THEN 1 END) as pareto_front_solutions,
    AVG(CASE WHEN pareto_rank IS NOT NULL THEN crowding_distance END)::NUMERIC(10,6) as avg_crowding_distance,
    
    -- Temporal analysis
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as runs_last_hour,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 day' THEN 1 END) as runs_last_day,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 week' THEN 1 END) as runs_last_week,
    
    -- Performance trends
    (SELECT AVG(optimization_score) 
     FROM optimization_results or2 
     WHERE or2.building_id = or1.building_id 
     AND or2.algorithm_type = or1.algorithm_type
     AND or2.created_at >= NOW() - INTERVAL '1 day')::NUMERIC(8,4) as score_trend_24h,
     
    (SELECT AVG(execution_time_ms)
     FROM optimization_results or2 
     WHERE or2.building_id = or1.building_id 
     AND or2.algorithm_type = or1.algorithm_type
     AND or2.created_at >= NOW() - INTERVAL '1 day')::NUMERIC(10,3) as time_trend_24h,
    
    -- Latest results
    (SELECT MAX(created_at) 
     FROM optimization_results or2 
     WHERE or2.building_id = or1.building_id 
     AND or2.algorithm_type = or1.algorithm_type) as last_run_time,
     
    NOW() as analytics_updated_at

FROM optimization_results or1
GROUP BY building_id, algorithm_type;

-- Indexes for optimization_analytics
CREATE INDEX optimization_analytics_score_idx ON optimization_analytics (avg_score DESC);
CREATE INDEX optimization_analytics_performance_idx ON optimization_analytics (avg_execution_time);
CREATE INDEX optimization_analytics_building_idx ON optimization_analytics (building_id, algorithm_type);

-- =============================================================================
-- SPATIAL CONFLICT SUMMARY VIEW
-- =============================================================================

-- Pre-computed spatial conflict analytics for all buildings
CREATE MATERIALIZED VIEW spatial_conflict_summary AS
SELECT 
    building_id,
    conflict_type,
    COUNT(*) as conflict_count,
    AVG(conflict_severity)::NUMERIC(10,4) as avg_severity,
    MAX(conflict_severity)::NUMERIC(10,4) as max_severity,
    MIN(conflict_severity)::NUMERIC(10,4) as min_severity,
    SUM(CASE WHEN resolution_priority = 1 THEN 1 ELSE 0 END) as critical_priority,
    SUM(CASE WHEN resolution_priority = 2 THEN 1 ELSE 0 END) as medium_priority,
    SUM(CASE WHEN resolution_priority = 3 THEN 1 ELSE 0 END) as low_priority,
    NOW() as summary_updated_at
FROM (
    SELECT 
        b.id as building_id,
        sc.conflict_type,
        sc.conflict_severity,
        sc.resolution_priority
    FROM buildings b
    CROSS JOIN LATERAL detect_spatial_conflicts(b.id) sc
) conflicts
GROUP BY building_id, conflict_type;

-- Index for spatial_conflict_summary
CREATE INDEX spatial_conflict_summary_building_idx ON spatial_conflict_summary (building_id);
CREATE INDEX spatial_conflict_summary_severity_idx ON spatial_conflict_summary (avg_severity DESC);

-- =============================================================================
-- DEVICE PERFORMANCE DASHBOARD VIEW
-- =============================================================================

-- Device analytics aggregated for performance dashboard
CREATE MATERIALIZED VIEW device_performance_dashboard AS
SELECT 
    d.building_id,
    b.name as building_name,
    d.type as device_type,
    d.system as device_system,
    d.subtype as device_subtype,
    
    -- Device counts
    COUNT(*) as device_count,
    COUNT(CASE WHEN d.status = 'operational' THEN 1 END) as operational_count,
    COUNT(CASE WHEN d.status = 'maintenance' THEN 1 END) as maintenance_count,
    COUNT(CASE WHEN d.status = 'offline' THEN 1 END) as offline_count,
    
    -- Spatial distribution
    AVG(ST_X(ST_Centroid(d.geom)))::NUMERIC(10,2) as avg_center_x,
    AVG(ST_Y(ST_Centroid(d.geom)))::NUMERIC(10,2) as avg_center_y,
    AVG(ST_Area(d.geom))::NUMERIC(10,4) as avg_device_area,
    SUM(ST_Area(d.geom))::NUMERIC(12,4) as total_device_area,
    
    -- Room distribution
    COUNT(DISTINCT d.room_id) as rooms_with_devices,
    COUNT(*) / NULLIF(COUNT(DISTINCT d.room_id), 0)::NUMERIC as avg_devices_per_room,
    
    -- Coverage analysis
    (SELECT COUNT(DISTINCT r.id) 
     FROM rooms r 
     WHERE r.building_id = d.building_id 
     AND EXISTS (
         SELECT 1 FROM devices d2 
         WHERE d2.room_id = r.id 
         AND d2.type = d.type
     )) as rooms_with_coverage,
     
    (SELECT COUNT(DISTINCT r.id) 
     FROM rooms r 
     WHERE r.building_id = d.building_id) as total_rooms_in_building,
    
    -- Performance ratio
    CASE 
        WHEN COUNT(*) > 0 THEN 
            COUNT(CASE WHEN d.status = 'operational' THEN 1 END)::NUMERIC / COUNT(*) * 100
        ELSE 0 
    END as operational_percentage,
    
    NOW() as dashboard_updated_at

FROM devices d
JOIN buildings b ON d.building_id = b.id
GROUP BY d.building_id, b.name, d.type, d.system, d.subtype;

-- Index for device_performance_dashboard
CREATE INDEX device_performance_dashboard_building_idx ON device_performance_dashboard (building_id);
CREATE INDEX device_performance_dashboard_type_idx ON device_performance_dashboard (device_type, operational_percentage DESC);

-- =============================================================================
-- MATERIALIZED VIEW REFRESH FUNCTIONS
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
    result TEXT;
BEGIN
    start_time := clock_timestamp();
    
    -- Refresh all materialized views
    REFRESH MATERIALIZED VIEW building_analytics;
    REFRESH MATERIALIZED VIEW room_performance;
    REFRESH MATERIALIZED VIEW optimization_analytics;
    REFRESH MATERIALIZED VIEW spatial_conflict_summary;
    REFRESH MATERIALIZED VIEW device_performance_dashboard;
    
    end_time := clock_timestamp();
    total_time := end_time - start_time;
    
    result := 'All analytics views refreshed in ' || total_time;
    
    -- Log the refresh operation
    INSERT INTO audit_logs (user_id, object_type, object_id, action, payload)
    VALUES (
        1, -- System user
        'system',
        'materialized_views',
        'refresh_completed',
        jsonb_build_object(
            'refresh_duration_ms', EXTRACT(epoch FROM total_time) * 1000,
            'views_refreshed', 5,
            'timestamp', NOW()
        )
    );
    
    RETURN result;
END;
$$;

-- Function to refresh specific view
CREATE OR REPLACE FUNCTION refresh_analytics_view(view_name TEXT)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    total_time INTERVAL;
BEGIN
    start_time := clock_timestamp();
    
    CASE view_name
        WHEN 'building_analytics' THEN 
            REFRESH MATERIALIZED VIEW building_analytics;
        WHEN 'room_performance' THEN 
            REFRESH MATERIALIZED VIEW room_performance;
        WHEN 'optimization_analytics' THEN 
            REFRESH MATERIALIZED VIEW optimization_analytics;
        WHEN 'spatial_conflict_summary' THEN 
            REFRESH MATERIALIZED VIEW spatial_conflict_summary;
        WHEN 'device_performance_dashboard' THEN 
            REFRESH MATERIALIZED VIEW device_performance_dashboard;
        ELSE
            RAISE EXCEPTION 'Unknown view name: %', view_name;
    END CASE;
    
    end_time := clock_timestamp();
    total_time := end_time - start_time;
    
    RETURN 'View ' || view_name || ' refreshed in ' || total_time;
END;
$$;

-- =============================================================================
-- ANALYTICS VIEW MONITORING
-- =============================================================================

-- View to monitor materialized view freshness and sizes
CREATE OR REPLACE VIEW analytics_view_status AS
SELECT 
    schemaname,
    matviewname as view_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as view_size,
    ispopulated,
    definition
FROM pg_matviews 
WHERE matviewname IN (
    'building_analytics',
    'room_performance', 
    'optimization_analytics',
    'spatial_conflict_summary',
    'device_performance_dashboard'
)
ORDER BY pg_total_relation_size(schemaname||'.'||matviewname) DESC;

-- Performance monitoring for views
CREATE OR REPLACE VIEW analytics_performance_summary AS
SELECT 
    'building_analytics' as view_name,
    (SELECT COUNT(*) FROM building_analytics) as record_count,
    (SELECT AVG(optimization_score) FROM building_analytics) as avg_metric,
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
    'spatial_conflict_summary',
    (SELECT COUNT(*) FROM spatial_conflict_summary),
    (SELECT AVG(avg_severity) FROM spatial_conflict_summary),
    pg_size_pretty(pg_total_relation_size('spatial_conflict_summary'))
UNION ALL
SELECT 
    'device_performance_dashboard',
    (SELECT COUNT(*) FROM device_performance_dashboard),
    (SELECT AVG(operational_percentage) FROM device_performance_dashboard),
    pg_size_pretty(pg_total_relation_size('device_performance_dashboard'));

-- Summary comments
COMMENT ON MATERIALIZED VIEW building_analytics IS 'Comprehensive building performance metrics - refresh every 15 minutes';
COMMENT ON MATERIALIZED VIEW room_performance IS 'Individual room efficiency analytics - refresh every 5 minutes'; 
COMMENT ON MATERIALIZED VIEW optimization_analytics IS 'Algorithm performance tracking - refresh every minute';
COMMENT ON FUNCTION refresh_all_analytics_views() IS 'Refresh all materialized views - should be called by scheduled job';