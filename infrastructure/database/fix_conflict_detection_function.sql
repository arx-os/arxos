-- Fix detect_spatial_conflicts function data type issues

DROP FUNCTION IF EXISTS detect_spatial_conflicts(integer);

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
        'device_overlap'::text as conflict_type,
        'device'::text as object1_type,
        d1.id::text as object1_id,
        'device'::text as object2_type,
        d2.id::text as object2_id,
        ST_Area(ST_Intersection(d1.geom, d2.geom))::numeric(10,2) as conflict_severity,
        3::integer as resolution_priority
    FROM devices d1
    JOIN devices d2 ON d1.room_id = d2.room_id 
        AND d1.id < d2.id 
        AND ST_Intersects(d1.geom, d2.geom)
    WHERE d1.building_id = building_id_param;
    
    -- Devices outside room boundaries
    RETURN QUERY
    SELECT
        'device_boundary_violation'::text as conflict_type,
        'device'::text as object1_type,
        d.id::text as object1_id,
        'room'::text as object2_type,
        r.id::text as object2_id,
        ST_Area(ST_Difference(d.geom, r.geom))::numeric(10,2) as conflict_severity,
        1::integer as resolution_priority
    FROM devices d
    JOIN rooms r ON d.room_id = r.id
    WHERE d.building_id = building_id_param
        AND NOT ST_Within(d.geom, r.geom);
    
    -- Room overlaps on same floor
    RETURN QUERY
    SELECT
        'room_overlap'::text as conflict_type,
        'room'::text as object1_type,
        r1.id::text as object1_id,
        'room'::text as object2_type,
        r2.id::text as object2_id,
        ST_Area(ST_Intersection(r1.geom, r2.geom))::numeric(10,2) as conflict_severity,
        2::integer as resolution_priority
    FROM rooms r1
    JOIN rooms r2 ON r1.floor_id = r2.floor_id 
        AND r1.id < r2.id 
        AND ST_Intersects(r1.geom, r2.geom)
    WHERE r1.building_id = building_id_param;
END;
$$;