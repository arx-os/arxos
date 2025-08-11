-- Fix NSGA-II function to use correct door attributes

DROP FUNCTION IF EXISTS calculate_nsga_objectives(integer);

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
    
    -- Objective 5: Maximize accessibility (distance from room entrances)
    RETURN QUERY
    SELECT
        'accessibility'::text,
        AVG(
            CASE WHEN d.category LIKE '%access%' OR d.category LIKE '%entrance%' THEN
                1.0 / GREATEST(1, ST_Distance(r.geom, d.geom))
            ELSE 0
            END
        )::NUMERIC(10,4),
        0.10::NUMERIC(4,2),
        'maximize'::text
    FROM rooms r
    CROSS JOIN doors d
    WHERE r.building_id = building_id_param
        AND d.building_id = building_id_param;
END;
$$;