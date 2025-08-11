-- Fix benchmark function variable naming conflict

-- Drop and recreate benchmark function with corrected variable names
DROP FUNCTION IF EXISTS benchmark_spatial_optimization(integer, integer);

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
    exec_time numeric;
BEGIN
    -- Initialize array
    execution_times := ARRAY[]::numeric[];
    
    -- Benchmark 1: Room utilization calculation
    FOR i IN 1..iterations LOOP
        start_time := clock_timestamp();
        PERFORM calculate_room_utilization(r.id) FROM rooms r WHERE building_id = building_id_param LIMIT 5;
        end_time := clock_timestamp();
        exec_time := EXTRACT(epoch FROM end_time - start_time) * 1000;
        execution_times := array_append(execution_times, exec_time);
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
        exec_time := EXTRACT(epoch FROM end_time - start_time) * 1000;
        execution_times := array_append(execution_times, exec_time);
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
        exec_time := EXTRACT(epoch FROM end_time - start_time) * 1000;
        execution_times := array_append(execution_times, exec_time);
    END LOOP;
    
    RETURN QUERY SELECT 
        'building_optimization_score'::text,
        ROUND((SELECT AVG(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MIN(x) FROM unnest(execution_times) x)::numeric, 3),
        ROUND((SELECT MAX(x) FROM unnest(execution_times) x)::numeric, 3),
        iterations;
END;
$$;