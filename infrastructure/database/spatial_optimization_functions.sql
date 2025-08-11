-- Custom PostgreSQL Functions for Spatial Optimization
-- Advanced functions supporting genetic algorithms, NSGA-II, and constraint solving
-- Engineering precision: Production-ready optimization engine functions

-- =============================================================================
-- SPATIAL CALCULATION FUNCTIONS
-- =============================================================================

-- Function: Calculate room utilization efficiency
CREATE OR REPLACE FUNCTION calculate_room_utilization(room_id text)
RETURNS NUMERIC(5,2)
LANGUAGE plpgsql
AS $$
DECLARE
    room_area NUMERIC;
    device_coverage NUMERIC;
    utilization_score NUMERIC;
BEGIN
    -- Get room area
    SELECT ST_Area(geom) INTO room_area
    FROM rooms WHERE id = room_id;
    
    -- Calculate device coverage area
    SELECT COALESCE(SUM(ST_Area(geom)), 0) INTO device_coverage
    FROM devices WHERE room_id = calculate_room_utilization.room_id;
    
    -- Calculate utilization efficiency (0-100%)
    IF room_area > 0 THEN
        utilization_score := LEAST(100, (device_coverage / room_area) * 100);
    ELSE
        utilization_score := 0;
    END IF;
    
    RETURN utilization_score;
END;
$$;

-- Function: Detect spatial conflicts between objects
CREATE OR REPLACE FUNCTION detect_spatial_conflicts(building_id_param integer)
RETURNS TABLE(
    conflict_type text,
    object1_type text,
    object1_id text,
    object2_type text,
    object2_id text,
    conflict_severity numeric,
    resolution_priority integer
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Device overlaps within rooms
    RETURN QUERY
    SELECT 
        'device_overlap' as conflict_type,
        'device' as object1_type,
        d1.id as object1_id,
        'device' as object2_type,
        d2.id as object2_id,
        ST_Area(ST_Intersection(d1.geom, d2.geom))::numeric(10,2) as conflict_severity,
        3 as resolution_priority
    FROM devices d1
    JOIN devices d2 ON d1.room_id = d2.room_id 
        AND d1.id < d2.id 
        AND ST_Intersects(d1.geom, d2.geom)
    WHERE d1.building_id = building_id_param;
    
    -- Devices outside room boundaries
    RETURN QUERY
    SELECT
        'device_boundary_violation' as conflict_type,
        'device' as object1_type,
        d.id as object1_id,
        'room' as object2_type,
        r.id as object2_id,
        ST_Area(ST_Difference(d.geom, r.geom))::numeric(10,2) as conflict_severity,
        1 as resolution_priority
    FROM devices d
    JOIN rooms r ON d.room_id = r.id
    WHERE d.building_id = building_id_param
        AND NOT ST_Within(d.geom, r.geom);
    
    -- Room overlaps on same floor
    RETURN QUERY
    SELECT
        'room_overlap' as conflict_type,
        'room' as object1_type,
        r1.id as object1_id,
        'room' as object2_type,
        r2.id as object2_id,
        ST_Area(ST_Intersection(r1.geom, r2.geom))::numeric(10,2) as conflict_severity,
        2 as resolution_priority
    FROM rooms r1
    JOIN rooms r2 ON r1.floor_id = r2.floor_id 
        AND r1.id < r2.id 
        AND ST_Intersects(r1.geom, r2.geom)
    WHERE r1.building_id = building_id_param;
END;
$$;

-- Function: Calculate building optimization score
CREATE OR REPLACE FUNCTION calculate_building_optimization_score(building_id_param integer)
RETURNS NUMERIC(5,2)
LANGUAGE plpgsql
AS $$
DECLARE
    total_rooms INTEGER;
    optimized_rooms INTEGER;
    conflict_count INTEGER;
    utilization_avg NUMERIC;
    final_score NUMERIC;
BEGIN
    -- Count total rooms
    SELECT COUNT(*) INTO total_rooms
    FROM rooms WHERE building_id = building_id_param;
    
    -- Count conflicts
    SELECT COUNT(*) INTO conflict_count
    FROM detect_spatial_conflicts(building_id_param);
    
    -- Calculate average room utilization
    SELECT AVG(calculate_room_utilization(id)) INTO utilization_avg
    FROM rooms WHERE building_id = building_id_param;
    
    -- Calculate rooms meeting optimization criteria (>80% utilization, no conflicts)
    SELECT COUNT(*) INTO optimized_rooms
    FROM rooms r
    WHERE r.building_id = building_id_param
        AND calculate_room_utilization(r.id) > 80
        AND NOT EXISTS (
            SELECT 1 FROM detect_spatial_conflicts(building_id_param) sc
            WHERE sc.object1_id = r.id OR sc.object2_id = r.id
        );
    
    -- Calculate final optimization score
    IF total_rooms > 0 THEN
        final_score := (
            (optimized_rooms::NUMERIC / total_rooms * 50) + -- 50% weight on optimized rooms
            (COALESCE(utilization_avg, 0) * 0.3) + -- 30% weight on average utilization
            (GREATEST(0, 100 - conflict_count * 5) * 0.2) -- 20% weight on conflict penalty
        );
    ELSE
        final_score := 0;
    END IF;
    
    RETURN LEAST(100, GREATEST(0, final_score));
END;
$$;

-- =============================================================================
-- GENETIC ALGORITHM SUPPORT FUNCTIONS
-- =============================================================================

-- Function: Generate random building layout parameters for genetic algorithm
CREATE OR REPLACE FUNCTION generate_genetic_parameters(building_id_param integer)
RETURNS TABLE(
    room_id text,
    x_offset NUMERIC(8,2),
    y_offset NUMERIC(8,2),
    rotation_angle NUMERIC(6,2),
    scale_factor NUMERIC(4,2),
    optimization_weight NUMERIC(4,2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        (random() * 100 - 50)::NUMERIC(8,2), -- Random offset -50 to +50
        (random() * 100 - 50)::NUMERIC(8,2), -- Random offset -50 to +50  
        (random() * 360)::NUMERIC(6,2), -- Random rotation 0-360 degrees
        (random() * 0.6 + 0.7)::NUMERIC(4,2), -- Random scale 0.7-1.3
        (random() * 0.5 + 0.5)::NUMERIC(4,2) -- Random weight 0.5-1.0
    FROM rooms r
    WHERE r.building_id = building_id_param;
END;
$$;

-- Function: Apply genetic algorithm transformation to room
CREATE OR REPLACE FUNCTION apply_genetic_transformation(
    room_geom geometry,
    x_offset NUMERIC,
    y_offset NUMERIC, 
    rotation_angle NUMERIC,
    scale_factor NUMERIC
)
RETURNS geometry
LANGUAGE plpgsql
AS $$
DECLARE
    centroid geometry;
    transformed_geom geometry;
BEGIN
    -- Get room centroid for rotation center
    centroid := ST_Centroid(room_geom);
    
    -- Apply transformations in sequence: translate, rotate, scale
    transformed_geom := ST_Scale(
        ST_Rotate(
            ST_Translate(room_geom, x_offset, y_offset),
            radians(rotation_angle),
            centroid
        ),
        scale_factor,
        scale_factor
    );
    
    RETURN transformed_geom;
END;
$$;

-- Function: Evaluate genetic algorithm fitness for building layout
CREATE OR REPLACE FUNCTION evaluate_genetic_fitness(
    building_id_param integer,
    genetic_params_json jsonb
)
RETURNS NUMERIC(10,4)
LANGUAGE plpgsql
AS $$
DECLARE
    fitness_score NUMERIC := 0;
    room_record RECORD;
    param_record jsonb;
    transformed_geom geometry;
    overlap_penalty NUMERIC := 0;
    utilization_bonus NUMERIC := 0;
    constraint_penalty NUMERIC := 0;
BEGIN
    -- Iterate through each room's genetic parameters
    FOR param_record IN SELECT * FROM jsonb_array_elements(genetic_params_json)
    LOOP
        -- Get room geometry
        SELECT geom INTO transformed_geom
        FROM rooms 
        WHERE id = param_record->>'room_id' 
            AND building_id = building_id_param;
        
        -- Apply genetic transformation
        transformed_geom := apply_genetic_transformation(
            transformed_geom,
            (param_record->>'x_offset')::NUMERIC,
            (param_record->>'y_offset')::NUMERIC,
            (param_record->>'rotation_angle')::NUMERIC,
            (param_record->>'scale_factor')::NUMERIC
        );
        
        -- Calculate fitness components
        -- 1. Penalize overlaps
        SELECT COUNT(*) * -100 INTO overlap_penalty
        FROM rooms r2
        WHERE r2.building_id = building_id_param
            AND r2.id != param_record->>'room_id'
            AND ST_Overlaps(transformed_geom, r2.geom);
        
        -- 2. Bonus for good utilization
        utilization_bonus := ST_Area(transformed_geom) * 0.1;
        
        -- 3. Penalize constraint violations
        IF ST_Area(transformed_geom) < 10 THEN -- Minimum room size
            constraint_penalty := constraint_penalty - 50;
        END IF;
        
        -- Add to total fitness
        fitness_score := fitness_score + overlap_penalty + utilization_bonus + constraint_penalty;
    END LOOP;
    
    RETURN fitness_score;
END;
$$;

-- =============================================================================
-- NSGA-II MULTI-OBJECTIVE OPTIMIZATION FUNCTIONS
-- =============================================================================

-- Function: Calculate multiple optimization objectives for NSGA-II
CREATE OR REPLACE FUNCTION calculate_nsga_objectives(building_id_param integer)
RETURNS TABLE(
    objective_name text,
    objective_value NUMERIC(10,4),
    weight NUMERIC(4,2),
    target_direction text
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Objective 1: Maximize space utilization
    RETURN QUERY
    SELECT 
        'space_utilization'::text,
        AVG(calculate_room_utilization(id))::NUMERIC(10,4),
        0.30::NUMERIC(4,2),
        'maximize'::text
    FROM rooms WHERE building_id = building_id_param;
    
    -- Objective 2: Minimize spatial conflicts
    RETURN QUERY
    SELECT 
        'conflict_minimization'::text,
        (-1 * COUNT(*))::NUMERIC(10,4), -- Negative for minimization
        0.25::NUMERIC(4,2),
        'maximize'::text -- Maximize the negative value
    FROM detect_spatial_conflicts(building_id_param);
    
    -- Objective 3: Maximize energy efficiency (device density optimization)
    RETURN QUERY
    SELECT
        'energy_efficiency'::text,
        COALESCE(
            AVG(ST_Area(r.geom) / GREATEST(1, device_count.count)), 
            0
        )::NUMERIC(10,4),
        0.20::NUMERIC(4,2),
        'maximize'::text
    FROM rooms r
    LEFT JOIN (
        SELECT room_id, COUNT(*) as count 
        FROM devices 
        WHERE building_id = building_id_param 
        GROUP BY room_id
    ) device_count ON r.id = device_count.room_id
    WHERE r.building_id = building_id_param;
    
    -- Objective 4: Minimize construction cost (based on perimeter)
    RETURN QUERY
    SELECT
        'construction_cost'::text,
        (-1 * SUM(ST_Perimeter(geom)))::NUMERIC(10,4), -- Negative for minimization
        0.15::NUMERIC(4,2),
        'maximize'::text -- Maximize the negative value
    FROM rooms WHERE building_id = building_id_param;
    
    -- Objective 5: Maximize accessibility (distance from entrances)
    RETURN QUERY
    SELECT
        'accessibility'::text,
        AVG(
            CASE WHEN d.type = 'main_entrance' THEN
                1.0 / GREATEST(1, ST_Distance(r.geom, d.geom))
            ELSE 0
            END
        )::NUMERIC(10,4),
        0.10::NUMERIC(4,2),
        'maximize'::text
    FROM rooms r
    CROSS JOIN doors d
    WHERE r.building_id = building_id_param;
END;
$$;

-- Function: Calculate Pareto dominance for NSGA-II
CREATE OR REPLACE FUNCTION calculate_pareto_dominance(
    solution1_objectives NUMERIC[],
    solution2_objectives NUMERIC[]
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    i INTEGER;
    s1_dominates BOOLEAN := FALSE;
    s2_dominates BOOLEAN := FALSE;
BEGIN
    -- Compare each objective
    FOR i IN 1..array_length(solution1_objectives, 1) LOOP
        IF solution1_objectives[i] > solution2_objectives[i] THEN
            s1_dominates := TRUE;
        ELSIF solution1_objectives[i] < solution2_objectives[i] THEN
            s2_dominates := TRUE;
        END IF;
    END LOOP;
    
    -- Return dominance relationship
    IF s1_dominates AND NOT s2_dominates THEN
        RETURN 1; -- Solution 1 dominates Solution 2
    ELSIF s2_dominates AND NOT s1_dominates THEN
        RETURN -1; -- Solution 2 dominates Solution 1
    ELSE
        RETURN 0; -- Non-dominated (equal or incomparable)
    END IF;
END;
$$;

-- =============================================================================
-- CONSTRAINT SATISFACTION FUNCTIONS
-- =============================================================================

-- Function: Validate building code constraints
CREATE OR REPLACE FUNCTION validate_building_constraints(building_id_param integer)
RETURNS TABLE(
    constraint_name text,
    constraint_type text,
    is_satisfied BOOLEAN,
    violation_details text,
    severity_level text
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Constraint 1: Minimum room area (building code)
    RETURN QUERY
    SELECT
        'minimum_room_area'::text,
        'building_code'::text,
        ST_Area(geom) >= 9.0, -- 9 sq meters minimum
        CASE WHEN ST_Area(geom) < 9.0 THEN
            'Room area ' || ST_Area(geom)::text || ' is below minimum 9 sq meters'
        ELSE 'OK'
        END,
        CASE WHEN ST_Area(geom) < 9.0 THEN 'critical' ELSE 'ok' END
    FROM rooms WHERE building_id = building_id_param;
    
    -- Constraint 2: Fire safety - maximum distance to exit
    RETURN QUERY
    SELECT
        'fire_exit_distance'::text,
        'safety'::text,
        COALESCE(min_exit_distance.distance <= 45.0, FALSE), -- 45 meter maximum
        CASE WHEN COALESCE(min_exit_distance.distance > 45.0, TRUE) THEN
            'Distance to nearest exit: ' || COALESCE(min_exit_distance.distance::text, 'unknown') || 'm exceeds 45m limit'
        ELSE 'OK'
        END,
        CASE WHEN COALESCE(min_exit_distance.distance > 45.0, TRUE) THEN 'critical' ELSE 'ok' END
    FROM rooms r
    LEFT JOIN (
        SELECT 
            room_id,
            MIN(ST_Distance(r2.geom, d.geom)) as distance
        FROM rooms r2
        JOIN doors d ON d.building_id = r2.building_id
        WHERE r2.building_id = building_id_param
            AND d.category LIKE '%exit%'
        GROUP BY room_id
    ) min_exit_distance ON r.id = min_exit_distance.room_id
    WHERE r.building_id = building_id_param;
    
    -- Constraint 3: HVAC coverage requirement  
    RETURN QUERY
    SELECT
        'hvac_coverage'::text,
        'environmental'::text,
        hvac_coverage.coverage_ratio >= 0.95, -- 95% coverage required
        CASE WHEN hvac_coverage.coverage_ratio < 0.95 THEN
            'HVAC coverage ' || (hvac_coverage.coverage_ratio * 100)::NUMERIC(5,1)::text || '% is below required 95%'
        ELSE 'OK'
        END,
        CASE WHEN hvac_coverage.coverage_ratio < 0.95 THEN 'warning' ELSE 'ok' END
    FROM rooms r
    JOIN (
        SELECT 
            room_id,
            COALESCE(
                ST_Area(ST_Union(d.geom)) / NULLIF(ST_Area(r2.geom), 0),
                0
            ) as coverage_ratio
        FROM rooms r2
        LEFT JOIN devices d ON d.room_id = r2.id AND d.type = 'HVAC'
        WHERE r2.building_id = building_id_param
        GROUP BY room_id, r2.geom
    ) hvac_coverage ON r.id = hvac_coverage.room_id
    WHERE r.building_id = building_id_param;
    
    -- Constraint 4: Device density limits
    RETURN QUERY
    SELECT
        'device_density'::text,
        'operational'::text,
        device_density.density <= 0.15, -- Maximum 15% of room area for devices
        CASE WHEN device_density.density > 0.15 THEN
            'Device density ' || (device_density.density * 100)::NUMERIC(5,1)::text || '% exceeds 15% limit'
        ELSE 'OK'
        END,
        CASE WHEN device_density.density > 0.15 THEN 'warning' ELSE 'ok' END
    FROM rooms r
    JOIN (
        SELECT 
            room_id,
            COALESCE(
                SUM(ST_Area(d.geom)) / NULLIF(ST_Area(r2.geom), 0),
                0
            ) as density
        FROM rooms r2
        LEFT JOIN devices d ON d.room_id = r2.id
        WHERE r2.building_id = building_id_param
        GROUP BY room_id, r2.geom
    ) device_density ON r.id = device_density.room_id
    WHERE r.building_id = building_id_param;
END;
$$;

-- =============================================================================
-- OPTIMIZATION PERFORMANCE FUNCTIONS
-- =============================================================================

-- Function: Calculate spatial query performance metrics
CREATE OR REPLACE FUNCTION calculate_spatial_performance_metrics(building_id_param integer)
RETURNS TABLE(
    metric_name text,
    metric_value NUMERIC(10,4),
    metric_unit text,
    benchmark_target NUMERIC(10,4)
)
LANGUAGE plpgsql
AS $$
DECLARE
    start_time timestamp;
    end_time timestamp;
    query_duration NUMERIC;
BEGIN
    -- Metric 1: Spatial index query performance
    start_time := clock_timestamp();
    PERFORM COUNT(*) FROM rooms WHERE building_id = building_id_param AND ST_Area(geom) > 0;
    end_time := clock_timestamp();
    query_duration := EXTRACT(epoch FROM end_time - start_time) * 1000; -- milliseconds
    
    RETURN QUERY SELECT 
        'spatial_index_query_time'::text,
        query_duration,
        'milliseconds'::text,
        100.0::NUMERIC(10,4); -- Target: < 100ms
    
    -- Metric 2: Conflict detection performance
    start_time := clock_timestamp();
    PERFORM COUNT(*) FROM detect_spatial_conflicts(building_id_param);
    end_time := clock_timestamp();
    query_duration := EXTRACT(epoch FROM end_time - start_time) * 1000;
    
    RETURN QUERY SELECT 
        'conflict_detection_time'::text,
        query_duration,
        'milliseconds'::text,
        500.0::NUMERIC(10,4); -- Target: < 500ms
        
    -- Metric 3: Optimization score calculation performance
    start_time := clock_timestamp();
    PERFORM calculate_building_optimization_score(building_id_param);
    end_time := clock_timestamp();
    query_duration := EXTRACT(epoch FROM end_time - start_time) * 1000;
    
    RETURN QUERY SELECT 
        'optimization_score_time'::text,
        query_duration,
        'milliseconds'::text,
        200.0::NUMERIC(10,4); -- Target: < 200ms
        
    -- Metric 4: Database object count
    RETURN QUERY SELECT 
        'total_spatial_objects'::text,
        (
            (SELECT COUNT(*) FROM rooms WHERE building_id = building_id_param) +
            (SELECT COUNT(*) FROM devices WHERE building_id = building_id_param) +
            (SELECT COUNT(*) FROM walls WHERE building_id = building_id_param) +
            (SELECT COUNT(*) FROM doors WHERE building_id = building_id_param) +
            (SELECT COUNT(*) FROM windows WHERE building_id = building_id_param)
        )::NUMERIC(10,4),
        'objects'::text,
        10000.0::NUMERIC(10,4); -- Target: handle 10k+ objects efficiently
END;
$$;

-- =============================================================================
-- UTILITY AND MAINTENANCE FUNCTIONS
-- =============================================================================

-- Function: Regenerate spatial indexes for optimization
CREATE OR REPLACE FUNCTION regenerate_spatial_indexes(building_id_param integer)
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
    result_message text := '';
BEGIN
    -- Reindex spatial columns for building-specific data
    EXECUTE 'REINDEX INDEX CONCURRENTLY rooms_geom_idx';
    EXECUTE 'REINDEX INDEX CONCURRENTLY devices_geom_idx';
    EXECUTE 'REINDEX INDEX CONCURRENTLY walls_geom_idx';
    EXECUTE 'REINDEX INDEX CONCURRENTLY doors_geom_idx';
    EXECUTE 'REINDEX INDEX CONCURRENTLY windows_geom_idx';
    
    -- Update table statistics
    EXECUTE 'ANALYZE rooms';
    EXECUTE 'ANALYZE devices';
    EXECUTE 'ANALYZE walls';
    EXECUTE 'ANALYZE doors';
    EXECUTE 'ANALYZE windows';
    
    result_message := 'Spatial indexes regenerated and statistics updated for building ' || building_id_param;
    
    -- Log the operation
    INSERT INTO audit_logs (user_id, object_type, object_id, action, payload)
    VALUES (
        1, -- System user
        'building',
        building_id_param::text,
        'spatial_index_regenerated',
        jsonb_build_object(
            'timestamp', NOW(),
            'operation', 'regenerate_spatial_indexes',
            'status', 'completed'
        )
    );
    
    RETURN result_message;
END;
$$;

-- =============================================================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- =============================================================================

-- Composite indexes for optimization functions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_building_area 
ON rooms (building_id, ST_Area(geom)) 
WHERE status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_room_type 
ON devices (room_id, type) 
WHERE status = 'operational';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_spatial_conflicts 
ON devices USING GIST (building_id, geom) 
WHERE status = 'operational';

-- Partial indexes for constraint validation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rooms_small_areas 
ON rooms (building_id) 
WHERE ST_Area(geom) < 9.0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_hvac 
ON devices USING GIST (room_id, geom) 
WHERE type = 'HVAC' AND status = 'operational';

-- =============================================================================
-- FUNCTION PERMISSIONS AND SECURITY
-- =============================================================================

-- Grant execute permissions to appropriate roles
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arxos_optimizer;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO arxos_api;

-- Create function usage statistics view
CREATE OR REPLACE VIEW function_performance_stats AS
SELECT 
    schemaname,
    funcname,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_user_functions 
WHERE schemaname = 'public'
    AND funcname LIKE '%optimization%' 
    OR funcname LIKE '%genetic%'
    OR funcname LIKE '%nsga%'
    OR funcname LIKE '%spatial%'
ORDER BY total_time DESC;

-- Summary comment
COMMENT ON SCHEMA public IS 'Arxos spatial optimization functions - Production ready for genetic algorithms, NSGA-II multi-objective optimization, and constraint satisfaction';