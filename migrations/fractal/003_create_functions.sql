-- Stored procedures and functions for Fractal ArxObject system
-- Optimized queries for scale-based operations

SET search_path TO fractal, public;

-- Function to get visible objects for a viewport at a specific scale
CREATE OR REPLACE FUNCTION get_visible_objects(
    p_viewport_bounds GEOMETRY,
    p_scale DECIMAL(10,8),
    p_detail_budget INTEGER DEFAULT 1000,
    p_importance_filter INTEGER DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    object_type VARCHAR(255),
    name VARCHAR(500),
    position_x DECIMAL(15,9),
    position_y DECIMAL(15,9),
    position_z DECIMAL(15,9),
    importance_level INTEGER,
    optimal_scale DECIMAL(10,8),
    properties JSONB,
    distance_from_optimal DECIMAL(10,8)
) AS $$
BEGIN
    RETURN QUERY
    WITH scale_filtered AS (
        SELECT 
            fa.*,
            ABS(fa.optimal_scale - p_scale) as distance_from_optimal
        FROM fractal_arxobjects fa
        WHERE 
            -- Scale range check
            fa.min_scale <= p_scale 
            AND fa.max_scale >= p_scale
            -- Spatial bounds check
            AND ST_Intersects(fa.geom, p_viewport_bounds)
            -- Optional importance filter
            AND (p_importance_filter IS NULL OR fa.importance_level <= p_importance_filter)
    )
    SELECT 
        sf.id,
        sf.object_type,
        sf.name,
        sf.position_x,
        sf.position_y,
        sf.position_z,
        sf.importance_level,
        sf.optimal_scale,
        sf.properties,
        sf.distance_from_optimal
    FROM scale_filtered sf
    ORDER BY 
        sf.importance_level ASC,  -- Most important first
        sf.distance_from_optimal ASC  -- Closest to optimal scale
    LIMIT p_detail_budget;
END;
$$ LANGUAGE plpgsql;

-- Function to get children of an object at a specific scale
CREATE OR REPLACE FUNCTION get_children_at_scale(
    p_parent_id UUID,
    p_scale DECIMAL(10,8),
    p_max_children INTEGER DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    object_type VARCHAR(255),
    name VARCHAR(500),
    position_x DECIMAL(15,9),
    position_y DECIMAL(15,9),
    position_z DECIMAL(15,9),
    importance_level INTEGER,
    properties JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fa.id,
        fa.object_type,
        fa.name,
        fa.position_x,
        fa.position_y,
        fa.position_z,
        fa.importance_level,
        fa.properties
    FROM fractal_arxobjects fa
    WHERE 
        fa.parent_id = p_parent_id
        AND fa.min_scale <= p_scale 
        AND fa.max_scale >= p_scale
    ORDER BY 
        fa.importance_level ASC,
        fa.optimal_scale DESC
    LIMIT p_max_children;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate BILT rewards for contributions
CREATE OR REPLACE FUNCTION calculate_bilt_reward(
    p_contribution_type VARCHAR(100),
    p_scale DECIMAL(10,8),
    p_confidence_score DECIMAL(3,2),
    p_has_documentation BOOLEAN DEFAULT FALSE,
    p_has_photos BOOLEAN DEFAULT FALSE,
    p_is_first_contribution BOOLEAN DEFAULT FALSE
)
RETURNS DECIMAL(18,8) AS $$
DECLARE
    v_base_reward DECIMAL(18,8);
    v_scale_multiplier DECIMAL(4,2);
    v_quality_multiplier DECIMAL(4,2);
    v_bonus DECIMAL(18,8) DEFAULT 0;
BEGIN
    -- Base rewards by contribution type
    v_base_reward := CASE p_contribution_type
        WHEN 'geometry' THEN 1.0
        WHEN 'specification' THEN 1.5
        WHEN 'schematic' THEN 2.0
        WHEN 'modification' THEN 2.5
        WHEN 'validation' THEN 0.5
        WHEN 'photo' THEN 0.8
        WHEN 'measurement' THEN 1.2
        WHEN 'material' THEN 1.3
        WHEN 'connection' THEN 1.8
        ELSE 1.0
    END;
    
    -- Scale multiplier (finer detail = higher reward)
    v_scale_multiplier := CASE
        WHEN p_scale >= 10.0 THEN 1.0    -- Campus level
        WHEN p_scale >= 1.0 THEN 1.0     -- Building level
        WHEN p_scale >= 0.1 THEN 1.2     -- Floor level
        WHEN p_scale >= 0.01 THEN 1.5    -- Room level
        WHEN p_scale >= 0.001 THEN 1.8   -- Fixture level
        WHEN p_scale >= 0.0001 THEN 2.0  -- Component level
        ELSE 2.5                          -- Schematic level
    END;
    
    -- Quality multiplier based on confidence and documentation
    v_quality_multiplier := 0.5 + (p_confidence_score * 0.5);  -- 0.5x to 1x based on confidence
    
    IF p_has_documentation THEN
        v_quality_multiplier := v_quality_multiplier * 1.1;
    END IF;
    
    IF p_has_photos THEN
        v_quality_multiplier := v_quality_multiplier * 1.15;
    END IF;
    
    -- Bonuses
    IF p_is_first_contribution THEN
        v_bonus := v_bonus + 5.0;
    END IF;
    
    -- Calculate final reward
    RETURN ROUND((v_base_reward * v_scale_multiplier * v_quality_multiplier) + v_bonus, 8);
END;
$$ LANGUAGE plpgsql;

-- Function to get tile data for map-style rendering
CREATE OR REPLACE FUNCTION get_tile_data(
    p_z INTEGER,
    p_x INTEGER,
    p_y INTEGER,
    p_scale DECIMAL(10,8)
)
RETURNS JSONB AS $$
DECLARE
    v_tile_bounds GEOMETRY;
    v_tile_size DECIMAL;
    v_min_lon DECIMAL;
    v_max_lon DECIMAL;
    v_min_lat DECIMAL;
    v_max_lat DECIMAL;
    v_result JSONB;
BEGIN
    -- Calculate tile bounds (Web Mercator projection)
    v_tile_size := 360.0 / POWER(2, p_z);
    v_min_lon := p_x * v_tile_size - 180;
    v_max_lon := (p_x + 1) * v_tile_size - 180;
    v_min_lat := p_y * v_tile_size - 90;
    v_max_lat := (p_y + 1) * v_tile_size - 90;
    
    v_tile_bounds := ST_MakeEnvelope(v_min_lon, v_min_lat, v_max_lon, v_max_lat, 4326);
    
    -- Get objects in tile
    SELECT jsonb_build_object(
        'tile', jsonb_build_object('z', p_z, 'x', p_x, 'y', p_y),
        'bounds', jsonb_build_object(
            'min_lon', v_min_lon,
            'min_lat', v_min_lat,
            'max_lon', v_max_lon,
            'max_lat', v_max_lat
        ),
        'objects', jsonb_agg(
            jsonb_build_object(
                'id', o.id,
                'type', o.object_type,
                'name', o.name,
                'x', o.position_x,
                'y', o.position_y,
                'z', o.position_z,
                'importance', o.importance_level,
                'properties', o.properties
            )
        ),
        'count', COUNT(*)
    ) INTO v_result
    FROM get_visible_objects(v_tile_bounds, p_scale, 500) o;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Function to preload adjacent tiles
CREATE OR REPLACE FUNCTION preload_adjacent_tiles(
    p_center_z INTEGER,
    p_center_x INTEGER,
    p_center_y INTEGER,
    p_radius INTEGER DEFAULT 1
)
RETURNS TABLE (
    z INTEGER,
    x INTEGER,
    y INTEGER,
    priority INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE adjacent AS (
        SELECT 
            p_center_z as z,
            p_center_x + dx.offset as x,
            p_center_y + dy.offset as y,
            ABS(dx.offset) + ABS(dy.offset) as distance
        FROM 
            generate_series(-p_radius, p_radius) dx(offset),
            generate_series(-p_radius, p_radius) dy(offset)
        WHERE NOT (dx.offset = 0 AND dy.offset = 0)
    )
    SELECT 
        a.z,
        a.x,
        a.y,
        CASE 
            WHEN a.distance = 1 THEN 1  -- Immediately adjacent
            WHEN a.distance = 2 THEN 2  -- Diagonal or 2 away
            ELSE 3                       -- Further
        END as priority
    FROM adjacent a
    ORDER BY priority, distance;
END;
$$ LANGUAGE plpgsql;

-- Function to validate contribution data based on scale
CREATE OR REPLACE FUNCTION validate_contribution(
    p_arxobject_id UUID,
    p_contribution_type VARCHAR(100),
    p_scale DECIMAL(10,8),
    p_data JSONB
)
RETURNS TABLE (
    is_valid BOOLEAN,
    confidence_score DECIMAL(3,2),
    errors TEXT[]
) AS $$
DECLARE
    v_errors TEXT[] := '{}';
    v_confidence DECIMAL(3,2) := 0.5;
    v_object_record RECORD;
BEGIN
    -- Get the object being contributed to
    SELECT * INTO v_object_record 
    FROM fractal_arxobjects 
    WHERE id = p_arxobject_id;
    
    IF NOT FOUND THEN
        v_errors := array_append(v_errors, 'Object not found');
        RETURN QUERY SELECT FALSE, 0.0, v_errors;
        RETURN;
    END IF;
    
    -- Check if contribution type is valid for scale
    IF p_scale >= 1.0 AND p_contribution_type IN ('wiring', 'connections', 'schematic') THEN
        v_errors := array_append(v_errors, 'Contribution type too detailed for building scale');
    ELSIF p_scale <= 0.001 AND p_contribution_type IN ('floor_plan', 'exterior') THEN
        v_errors := array_append(v_errors, 'Contribution type too broad for component scale');
    END IF;
    
    -- Validate required fields based on contribution type
    CASE p_contribution_type
        WHEN 'geometry' THEN
            IF NOT p_data ? 'coordinates' THEN
                v_errors := array_append(v_errors, 'Missing coordinates');
            END IF;
        WHEN 'specification' THEN
            IF NOT (p_data ? 'make' AND p_data ? 'model') THEN
                v_errors := array_append(v_errors, 'Missing make/model information');
            END IF;
        WHEN 'schematic' THEN
            IF NOT p_data ? 'diagram_type' THEN
                v_errors := array_append(v_errors, 'Missing diagram type');
            END IF;
    ELSE
        -- Default validation
        IF p_data = '{}' OR p_data IS NULL THEN
            v_errors := array_append(v_errors, 'Empty contribution data');
        END IF;
    END CASE;
    
    -- Calculate confidence based on data completeness
    IF p_data ? 'source' THEN v_confidence := v_confidence + 0.1; END IF;
    IF p_data ? 'date_verified' THEN v_confidence := v_confidence + 0.1; END IF;
    IF p_data ? 'photos' AND jsonb_array_length(p_data->'photos') > 0 THEN 
        v_confidence := v_confidence + 0.2; 
    END IF;
    IF p_data ? 'documentation' THEN v_confidence := v_confidence + 0.1; END IF;
    
    -- Cap confidence at 1.0
    v_confidence := LEAST(v_confidence, 1.0);
    
    RETURN QUERY SELECT 
        array_length(v_errors, 1) IS NULL OR array_length(v_errors, 1) = 0,
        v_confidence,
        v_errors;
END;
$$ LANGUAGE plpgsql;

-- Function to propagate changes from child to parent
CREATE OR REPLACE FUNCTION propagate_to_parent(
    p_child_id UUID,
    p_update_type VARCHAR(50)
)
RETURNS VOID AS $$
DECLARE
    v_parent_id UUID;
    v_child_bounds GEOMETRY;
BEGIN
    -- Get parent ID
    SELECT parent_id INTO v_parent_id
    FROM fractal_arxobjects
    WHERE id = p_child_id;
    
    IF v_parent_id IS NULL THEN
        RETURN;  -- No parent to propagate to
    END IF;
    
    -- Update parent based on update type
    CASE p_update_type
        WHEN 'bounds' THEN
            -- Recalculate parent bounds to encompass all children
            WITH child_bounds AS (
                SELECT ST_Extent(geom) as extent
                FROM fractal_arxobjects
                WHERE parent_id = v_parent_id
            )
            UPDATE fractal_arxobjects
            SET 
                properties = properties || 
                    jsonb_build_object('bounds_updated', NOW()),
                updated_at = NOW()
            WHERE id = v_parent_id;
            
        WHEN 'properties' THEN
            -- Aggregate certain properties from children
            UPDATE fractal_arxobjects
            SET 
                properties = properties || 
                    jsonb_build_object(
                        'child_count', (
                            SELECT COUNT(*) 
                            FROM fractal_arxobjects 
                            WHERE parent_id = v_parent_id
                        ),
                        'last_child_update', NOW()
                    ),
                updated_at = NOW()
            WHERE id = v_parent_id;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Function to get scale statistics for monitoring
CREATE OR REPLACE FUNCTION get_scale_statistics(
    p_viewport_bounds GEOMETRY DEFAULT NULL
)
RETURNS TABLE (
    scale_range VARCHAR(50),
    object_count BIGINT,
    avg_importance DECIMAL(3,2),
    total_contributions BIGINT,
    total_bilt_earned DECIMAL(18,8)
) AS $$
BEGIN
    RETURN QUERY
    WITH scale_ranges AS (
        SELECT 
            CASE 
                WHEN optimal_scale >= 10.0 THEN 'Campus (10m/px)'
                WHEN optimal_scale >= 1.0 THEN 'Building (1m/px)'
                WHEN optimal_scale >= 0.1 THEN 'Floor (10cm/px)'
                WHEN optimal_scale >= 0.01 THEN 'Room (1cm/px)'
                WHEN optimal_scale >= 0.001 THEN 'Fixture (1mm/px)'
                WHEN optimal_scale >= 0.0001 THEN 'Component (0.1mm/px)'
                ELSE 'Schematic (0.01mm/px)'
            END as scale_range_name,
            fa.id,
            fa.importance_level
        FROM fractal_arxobjects fa
        WHERE p_viewport_bounds IS NULL OR ST_Intersects(fa.geom, p_viewport_bounds)
    ),
    contribution_stats AS (
        SELECT 
            sr.scale_range_name,
            COUNT(DISTINCT sc.id) as contrib_count,
            SUM(sc.bilt_earned) as bilt_total
        FROM scale_ranges sr
        LEFT JOIN scale_contributions sc ON sr.id = sc.arxobject_id
        GROUP BY sr.scale_range_name
    )
    SELECT 
        sr.scale_range_name,
        COUNT(DISTINCT sr.id) as object_count,
        AVG(sr.importance_level)::DECIMAL(3,2) as avg_importance,
        COALESCE(cs.contrib_count, 0) as total_contributions,
        COALESCE(cs.bilt_total, 0) as total_bilt_earned
    FROM scale_ranges sr
    LEFT JOIN contribution_stats cs ON sr.scale_range_name = cs.scale_range_name
    GROUP BY sr.scale_range_name, cs.contrib_count, cs.bilt_total
    ORDER BY 
        CASE sr.scale_range_name
            WHEN 'Campus (10m/px)' THEN 1
            WHEN 'Building (1m/px)' THEN 2
            WHEN 'Floor (10cm/px)' THEN 3
            WHEN 'Room (1cm/px)' THEN 4
            WHEN 'Fixture (1mm/px)' THEN 5
            WHEN 'Component (0.1mm/px)' THEN 6
            WHEN 'Schematic (0.01mm/px)' THEN 7
        END;
END;
$$ LANGUAGE plpgsql;

-- Create helper function for scale snapping
CREATE OR REPLACE FUNCTION snap_to_scale(
    p_scale DECIMAL(10,8)
)
RETURNS DECIMAL(10,8) AS $$
DECLARE
    v_scales DECIMAL(10,8)[] := ARRAY[10.0, 1.0, 0.1, 0.01, 0.001, 0.0001, 0.00001];
    v_closest DECIMAL(10,8);
    v_min_diff DECIMAL(10,8) := 999999;
    v_diff DECIMAL(10,8);
    v_scale DECIMAL(10,8);
BEGIN
    FOREACH v_scale IN ARRAY v_scales
    LOOP
        v_diff := ABS(v_scale - p_scale);
        IF v_diff < v_min_diff THEN
            v_min_diff := v_diff;
            v_closest := v_scale;
        END IF;
    END LOOP;
    
    RETURN v_closest;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function to clean up old cache entries
CREATE OR REPLACE FUNCTION cleanup_tile_cache()
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM tile_cache
    WHERE expires_at < NOW()
    OR (hit_count = 0 AND created_at < NOW() - INTERVAL '1 hour');
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- Schedule periodic cleanup (requires pg_cron extension if available)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('cleanup-tile-cache', '*/15 * * * *', 'SELECT fractal.cleanup_tile_cache();');