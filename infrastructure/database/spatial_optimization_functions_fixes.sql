-- Fix spatial optimization functions - Index and View corrections

-- =============================================================================
-- CORRECTED PERFORMANCE OPTIMIZATION INDEXES
-- =============================================================================

-- Drop problematic indexes if they exist
DROP INDEX IF EXISTS idx_spatial_conflicts;
DROP INDEX IF EXISTS idx_devices_hvac;

-- Corrected composite indexes for optimization functions
DROP INDEX IF EXISTS idx_rooms_building_area;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_building_area 
ON rooms (building_id, (ST_Area(geom)::numeric(10,2))) 
WHERE status = 'active';

DROP INDEX IF EXISTS idx_devices_room_type;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_room_type 
ON devices (room_id, type) 
WHERE status = 'operational';

-- Corrected spatial index for devices 
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_spatial_optimization 
ON devices USING GIST (geom) 
WHERE status = 'operational';

-- Corrected partial indexes for constraint validation
DROP INDEX IF EXISTS idx_rooms_small_areas;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_small_areas 
ON rooms (building_id) 
WHERE ST_Area(geom) < 9.0;

-- Corrected HVAC device spatial index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_hvac_spatial 
ON devices USING GIST (geom) 
WHERE type = 'HVAC' AND status = 'operational';

-- Additional performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_floor_optimization
ON rooms (floor_id, category, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_system_subtype
ON devices (system, subtype, status);

-- =============================================================================
-- CORRECTED FUNCTION PERFORMANCE STATISTICS VIEW
-- =============================================================================

-- Drop existing view if it exists
DROP VIEW IF EXISTS function_performance_stats;

-- Corrected function usage statistics view (compatible with PostgreSQL versions)
CREATE OR REPLACE VIEW function_performance_stats AS
SELECT 
    schemaname,
    funcname,
    calls,
    total_time,
    CASE 
        WHEN calls > 0 THEN total_time / calls 
        ELSE 0 
    END as mean_time
FROM pg_stat_user_functions 
WHERE schemaname = 'public'
    AND (funcname LIKE '%optimization%' 
         OR funcname LIKE '%genetic%'
         OR funcname LIKE '%nsga%'
         OR funcname LIKE '%spatial%'
         OR funcname LIKE '%calculate%'
         OR funcname LIKE '%detect%')
ORDER BY total_time DESC;

-- =============================================================================
-- ADDITIONAL UTILITY FUNCTIONS
-- =============================================================================

-- Function: Get optimization function execution statistics
CREATE OR REPLACE FUNCTION get_optimization_stats()
RETURNS TABLE(
    function_name text,
    total_calls bigint,
    avg_execution_time_ms numeric,
    total_time_ms numeric
)
LANGUAGE sql
AS $$
SELECT 
    funcname::text as function_name,
    calls as total_calls,
    CASE 
        WHEN calls > 0 THEN ROUND((total_time / calls)::numeric, 3)
        ELSE 0 
    END as avg_execution_time_ms,
    ROUND(total_time::numeric, 3) as total_time_ms
FROM pg_stat_user_functions 
WHERE schemaname = 'public'
    AND (funcname LIKE '%optimization%' 
         OR funcname LIKE '%genetic%'
         OR funcname LIKE '%nsga%'
         OR funcname LIKE '%spatial%'
         OR funcname LIKE '%calculate%'
         OR funcname LIKE '%detect%')
ORDER BY total_time DESC;
$$;

-- Function: Reset optimization function statistics
CREATE OR REPLACE FUNCTION reset_optimization_stats()
RETURNS text
LANGUAGE plpgsql
AS $$
BEGIN
    -- Reset PostgreSQL function statistics
    SELECT pg_stat_reset();
    
    RETURN 'Optimization function statistics reset successfully';
END;
$$;

-- =============================================================================
-- PERFORMANCE TESTING FUNCTIONS
-- =============================================================================

-- Function: Benchmark spatial optimization performance
CREATE OR REPLACE FUNCTION benchmark_spatial_optimization(building_id_param integer, iterations integer DEFAULT 10)
RETURNS TABLE(
    test_name text,
    avg_time_ms numeric,
    min_time_ms numeric,
    max_time_ms numeric,
    total_iterations integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    i integer;
    start_time timestamp;
    end_time timestamp;
    execution_times numeric[];
    current_time numeric;
BEGIN
    -- Initialize array
    execution_times := ARRAY[]::numeric[];
    
    -- Benchmark 1: Room utilization calculation
    FOR i IN 1..iterations LOOP
        start_time := clock_timestamp();
        PERFORM calculate_room_utilization(r.id) FROM rooms r WHERE building_id = building_id_param LIMIT 5;
        end_time := clock_timestamp();
        current_time := EXTRACT(epoch FROM end_time - start_time) * 1000;
        execution_times := array_append(execution_times, current_time);
    END LOOP;
    
    RETURN QUERY SELECT 
        'room_utilization_calculation'::text,
        ROUND((SELECT AVG(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MIN(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MAX(x) FROM unnest(execution_times) x)::numeric, 3),
        iterations;
    
    -- Reset for next test
    execution_times := ARRAY[]::numeric[];
    
    -- Benchmark 2: Conflict detection
    FOR i IN 1..iterations LOOP
        start_time := clock_timestamp();
        PERFORM COUNT(*) FROM detect_spatial_conflicts(building_id_param);
        end_time := clock_timestamp();
        current_time := EXTRACT(epoch FROM end_time - start_time) * 1000;
        execution_times := array_append(execution_times, current_time);
    END LOOP;
    
    RETURN QUERY SELECT 
        'spatial_conflict_detection'::text,
        ROUND((SELECT AVG(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MIN(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MAX(x) FROM unnest(execution_times) x)::numeric, 3),
        iterations;
    
    -- Reset for next test
    execution_times := ARRAY[]::numeric[];
    
    -- Benchmark 3: Building optimization score
    FOR i IN 1..iterations LOOP
        start_time := clock_timestamp();
        PERFORM calculate_building_optimization_score(building_id_param);
        end_time := clock_timestamp();
        current_time := EXTRACT(epoch FROM end_time - start_time) * 1000;
        execution_times := array_append(execution_times, current_time);
    END LOOP;
    
    RETURN QUERY SELECT 
        'building_optimization_score'::text,
        ROUND((SELECT AVG(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MIN(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MAX(x) FROM unnest(execution_times) x)::numeric, 3),
        iterations;
END;
$$;