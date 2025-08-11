-- Fix room utilization function ambiguous column reference

DROP FUNCTION IF EXISTS calculate_room_utilization(text);

CREATE OR REPLACE FUNCTION calculate_room_utilization(room_id_param text)
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
    FROM rooms WHERE id = room_id_param;
    
    -- Calculate device coverage area
    SELECT COALESCE(SUM(ST_Area(geom)), 0) INTO device_coverage
    FROM devices WHERE room_id = room_id_param;
    
    -- Calculate utilization efficiency (0-100%)
    IF room_area > 0 THEN
        utilization_score := LEAST(100, (device_coverage / room_area) * 100);
    ELSE
        utilization_score := 0;
    END IF;
    
    RETURN utilization_score;
END;
$$;