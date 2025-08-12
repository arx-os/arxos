-- Seed data for testing Fractal ArxObject system with 3 zoom levels
-- Creates a sample campus -> building -> room -> fixture hierarchy

SET search_path TO fractal, public;

-- Create a test user for contributions
INSERT INTO fractal_arxobjects (
    id,
    object_type,
    name,
    description,
    position_x, position_y, position_z,
    min_scale, max_scale, optimal_scale,
    importance_level,
    width, height, depth,
    properties,
    created_by
) VALUES 
-- Campus level (10m/pixel)
(
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'CAMPUS',
    'Tech University Campus',
    'Main university campus with multiple buildings',
    0, 0, 0,  -- Origin point
    5.0, 100.0, 10.0,  -- Visible from 5m/px to 100m/px, optimal at 10m/px
    1,  -- Critical importance
    1000000, 800000, 50000,  -- 1km x 800m x 50m high
    '{"type": "educational", "buildings": 5, "area_sqm": 800000}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),

-- Building level (1m/pixel) 
(
    'b0000000-0000-0000-0000-000000000001'::uuid,
    'BUILDING',
    'Engineering Building',
    '5-story engineering building with labs and classrooms',
    100000, 50000, 0,  -- 100m, 50m from origin
    0.5, 20.0, 1.0,  -- Visible from 0.5m/px to 20m/px, optimal at 1m/px
    1,  -- Critical importance
    80000, 60000, 20000,  -- 80m x 60m x 20m high
    '{"floors": 5, "year_built": 2010, "building_code": "ENG-001"}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),
(
    'b0000000-0000-0000-0000-000000000002'::uuid,
    'BUILDING',
    'Science Building',
    '4-story science building with research labs',
    -50000, 100000, 0,  -- -50m, 100m from origin
    0.5, 20.0, 1.0,
    1,
    70000, 70000, 16000,  -- 70m x 70m x 16m high
    '{"floors": 4, "year_built": 2015, "building_code": "SCI-001"}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),

-- Floor level (0.1m/pixel)
(
    'f0000000-0000-0000-0000-000000000001'::uuid,
    'FLOOR',
    'Engineering Building - Floor 1',
    'Ground floor with lobby and lecture halls',
    100000, 50000, 0,
    0.05, 2.0, 0.1,  -- Visible from 0.05m/px to 2m/px, optimal at 0.1m/px
    2,  -- Important
    80000, 60000, 4000,  -- Same footprint as building, 4m high
    '{"level": 1, "rooms": 12, "area_sqm": 4800}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),
(
    'f0000000-0000-0000-0000-000000000002'::uuid,
    'FLOOR',
    'Engineering Building - Floor 2',
    'Second floor with classrooms and offices',
    100000, 50000, 4000,  -- 4m above ground
    0.05, 2.0, 0.1,
    2,
    80000, 60000, 4000,
    '{"level": 2, "rooms": 20, "area_sqm": 4800}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),

-- Room level (0.01m/pixel - 1cm/pixel)
(
    'r0000000-0000-0000-0000-000000000001'::uuid,
    'ROOM',
    'Lecture Hall 101',
    'Large lecture hall with 200 seats',
    105000, 52000, 0,  -- Within Engineering Building Floor 1
    0.005, 0.5, 0.01,  -- Visible from 5mm/px to 0.5m/px, optimal at 1cm/px
    2,
    20000, 15000, 4000,  -- 20m x 15m x 4m high
    '{"room_number": "101", "capacity": 200, "type": "lecture_hall"}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),
(
    'r0000000-0000-0000-0000-000000000002'::uuid,
    'ROOM',
    'Electronics Lab 201',
    'Electronics teaching laboratory',
    108000, 55000, 4000,  -- Within Engineering Building Floor 2
    0.005, 0.5, 0.01,
    2,
    15000, 12000, 3500,  -- 15m x 12m x 3.5m high
    '{"room_number": "201", "capacity": 30, "type": "laboratory", "equipment": ["oscilloscopes", "power_supplies", "soldering_stations"]}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),
(
    'r0000000-0000-0000-0000-000000000003'::uuid,
    'ROOM',
    'Office 202',
    'Faculty office',
    120000, 52000, 4000,  -- Within Engineering Building Floor 2
    0.005, 0.5, 0.01,
    3,  -- Detail level
    4000, 3000, 3500,  -- 4m x 3m x 3.5m high
    '{"room_number": "202", "type": "office", "occupant": "Dr. Smith"}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),

-- Fixture level (0.001m/pixel - 1mm/pixel)
(
    'x0000000-0000-0000-0000-000000000001'::uuid,
    'ELECTRICAL_OUTLET',
    'Duplex Outlet - LH101-01',
    'Standard 120V duplex outlet',
    106000, 52100, 450,  -- On wall in Lecture Hall 101, 45cm above floor
    0.0001, 0.05, 0.001,  -- Visible from 0.1mm/px to 5cm/px, optimal at 1mm/px
    3,
    100, 120, 50,  -- 10cm x 12cm x 5cm deep
    '{"voltage": 120, "amperage": 20, "type": "duplex", "circuit": "LH101-A"}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),
(
    'x0000000-0000-0000-0000-000000000002'::uuid,
    'LIGHT_FIXTURE',
    'LED Panel - LH101-L01',
    '2x4 LED ceiling panel',
    110000, 57000, 3800,  -- On ceiling in Lecture Hall 101
    0.0001, 0.05, 0.001,
    3,
    1200, 600, 100,  -- 120cm x 60cm x 10cm
    '{"type": "LED_panel", "wattage": 40, "lumens": 4000, "color_temp": 4000}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),
(
    'x0000000-0000-0000-0000-000000000003'::uuid,
    'ELECTRICAL_PANEL',
    'Panel Board - Floor 2',
    '200A electrical distribution panel',
    102000, 51000, 5500,  -- In electrical room on Floor 2
    0.0001, 0.05, 0.001,
    2,  -- Important infrastructure
    600, 900, 200,  -- 60cm x 90cm x 20cm deep
    '{"amperage": 200, "voltage": "120/240", "circuits": 42, "manufacturer": "Square D"}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),
(
    'x0000000-0000-0000-0000-000000000004'::uuid,
    'HVAC_REGISTER',
    'Supply Air Register - Office 202',
    'Ceiling mounted supply air register',
    121500, 53500, 7300,  -- On ceiling in Office 202
    0.0001, 0.05, 0.001,
    4,  -- Optional detail
    300, 300, 100,  -- 30cm x 30cm x 10cm
    '{"type": "supply", "size": "12x12", "cfm": 150}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
),

-- Component level (0.0001m/pixel - 0.1mm/pixel)
(
    'c0000000-0000-0000-0000-000000000001'::uuid,
    'CIRCUIT_BREAKER',
    '20A Single Pole Breaker',
    'Circuit breaker in panel',
    102100, 51200, 5700,  -- Inside electrical panel
    0.00001, 0.005, 0.0001,  -- Visible from 0.01mm/px to 5mm/px, optimal at 0.1mm/px
    3,
    20, 80, 30,  -- 2cm x 8cm x 3cm
    '{"amperage": 20, "poles": 1, "manufacturer": "Square D", "model": "QO120"}'::jsonb,
    '00000000-0000-0000-0000-000000000000'::uuid
);

-- Set parent relationships
UPDATE fractal_arxobjects SET parent_id = 'a0000000-0000-0000-0000-000000000001'::uuid 
WHERE object_type = 'BUILDING';

UPDATE fractal_arxobjects SET parent_id = 'b0000000-0000-0000-0000-000000000001'::uuid 
WHERE id IN (
    'f0000000-0000-0000-0000-000000000001'::uuid,
    'f0000000-0000-0000-0000-000000000002'::uuid
);

UPDATE fractal_arxobjects SET parent_id = 'f0000000-0000-0000-0000-000000000001'::uuid 
WHERE id = 'r0000000-0000-0000-0000-000000000001'::uuid;

UPDATE fractal_arxobjects SET parent_id = 'f0000000-0000-0000-0000-000000000002'::uuid 
WHERE id IN (
    'r0000000-0000-0000-0000-000000000002'::uuid,
    'r0000000-0000-0000-0000-000000000003'::uuid
);

UPDATE fractal_arxobjects SET parent_id = 'r0000000-0000-0000-0000-000000000001'::uuid 
WHERE id IN (
    'x0000000-0000-0000-0000-000000000001'::uuid,
    'x0000000-0000-0000-0000-000000000002'::uuid
);

UPDATE fractal_arxobjects SET parent_id = 'r0000000-0000-0000-0000-000000000003'::uuid 
WHERE id = 'x0000000-0000-0000-0000-000000000004'::uuid;

UPDATE fractal_arxobjects SET parent_id = 'x0000000-0000-0000-0000-000000000003'::uuid 
WHERE id = 'c0000000-0000-0000-0000-000000000001'::uuid;

-- Add some sample contributions
INSERT INTO scale_contributions (
    arxobject_id,
    contributor_id,
    contribution_scale,
    contribution_type,
    data,
    confidence_score,
    peer_validations,
    validation_status,
    bilt_earned
) VALUES
(
    'r0000000-0000-0000-0000-000000000001'::uuid,
    '11111111-0000-0000-0000-000000000001'::uuid,
    0.01,  -- Room scale
    'specification',
    '{"seating_layout": "theater", "av_equipment": ["projector", "screen", "audio_system"], "photos": ["url1", "url2"]}'::jsonb,
    0.85,
    3,
    'validated',
    2.25  -- 1.5 base * 1.5 scale multiplier
),
(
    'x0000000-0000-0000-0000-000000000001'::uuid,
    '11111111-0000-0000-0000-000000000002'::uuid,
    0.001,  -- Fixture scale
    'modification',
    '{"date": "2024-03-15", "description": "Upgraded to GFCI outlet", "before_photo": "url3", "after_photo": "url4"}'::jsonb,
    0.90,
    2,
    'validated',
    4.5  -- 2.5 base * 1.8 scale multiplier
),
(
    'x0000000-0000-0000-0000-000000000003'::uuid,
    '11111111-0000-0000-0000-000000000003'::uuid,
    0.001,  -- Fixture scale
    'schematic',
    '{"diagram_type": "single_line", "circuits": 42, "main_breaker": "200A", "documentation": "url5"}'::jsonb,
    0.95,
    5,
    'validated',
    3.6  -- 2.0 base * 1.8 scale multiplier
);

-- Add visibility rules for different scales
INSERT INTO visibility_rules (
    arxobject_id,
    min_zoom,
    max_zoom,
    render_style,
    simplification_level
) VALUES
-- Buildings shown as simple boxes at campus level
(
    'b0000000-0000-0000-0000-000000000001'::uuid,
    5.0,
    100.0,
    '{"shape": "box", "color": "#4A90E2", "opacity": 0.8}'::jsonb,
    2
),
-- Rooms shown as rectangles at floor level
(
    'r0000000-0000-0000-0000-000000000001'::uuid,
    0.05,
    0.5,
    '{"shape": "rectangle", "color": "#7ED321", "show_label": true}'::jsonb,
    1
),
-- Fixtures shown as icons at room level
(
    'x0000000-0000-0000-0000-000000000001'::uuid,
    0.001,
    0.05,
    '{"icon": "outlet", "size": "small", "color": "#F5A623"}'::jsonb,
    0
);

-- Add some detail records for lazy loading
INSERT INTO arxobject_details (
    arxobject_id,
    detail_level,
    detail_type,
    data,
    data_size_bytes
) VALUES
(
    'r0000000-0000-0000-0000-000000000001'::uuid,
    1,  -- Basic
    'visual',
    '{"shape": "rectangle", "color": "#7ED321"}'::jsonb,
    50
),
(
    'r0000000-0000-0000-0000-000000000001'::uuid,
    2,  -- Standard
    'specifications',
    '{"seats": 200, "projector": "Epson EB-2250U", "screen": "120 inch"}'::jsonb,
    150
),
(
    'r0000000-0000-0000-0000-000000000001'::uuid,
    3,  -- Detailed
    'technical',
    '{"hvac_zones": 2, "lighting_zones": 4, "emergency_exits": 2, "fire_extinguishers": 2}'::jsonb,
    300
);

-- Create some test tiles for caching
INSERT INTO tile_cache (
    z, x, y,
    scale,
    bounds,
    object_count,
    objects,
    expires_at
) VALUES
(
    10, 512, 512,  -- Zoom level 10, center tile
    1.0,  -- Building scale
    ST_MakeEnvelope(-0.703125, -0.703125, 0.703125, 0.703125, 4326),
    2,
    '[{"id": "b0000000-0000-0000-0000-000000000001", "type": "BUILDING", "name": "Engineering Building"}]'::jsonb,
    NOW() + INTERVAL '1 hour'
);

-- Add sample performance metrics
INSERT INTO performance_metrics (
    metric_type,
    duration_ms,
    scale_from,
    scale_to,
    object_count,
    user_id,
    device_memory_gb,
    device_cores
) VALUES
('zoom_transition', 150.5, 10.0, 1.0, 5, '11111111-0000-0000-0000-000000000001'::uuid, 8.0, 4),
('zoom_transition', 180.2, 1.0, 0.1, 12, '11111111-0000-0000-0000-000000000001'::uuid, 8.0, 4),
('tile_load', 45.3, NULL, NULL, 3, '11111111-0000-0000-0000-000000000002'::uuid, 4.0, 2),
('detail_fetch', 23.7, NULL, NULL, 1, '11111111-0000-0000-0000-000000000003'::uuid, 16.0, 8);

-- Verify the data
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM fractal_arxobjects;
    RAISE NOTICE 'Created % fractal ArxObjects', v_count;
    
    SELECT COUNT(*) INTO v_count FROM scale_contributions;
    RAISE NOTICE 'Created % contributions', v_count;
    
    SELECT COUNT(*) INTO v_count FROM visibility_rules;
    RAISE NOTICE 'Created % visibility rules', v_count;
    
    -- Test the get_visible_objects function
    RAISE NOTICE 'Testing scale queries...';
    
    -- Campus scale (10m/px)
    SELECT COUNT(*) INTO v_count 
    FROM get_visible_objects(
        ST_MakeEnvelope(-1000000, -1000000, 1000000, 1000000, 4326),
        10.0,
        100
    );
    RAISE NOTICE 'Objects visible at campus scale (10m/px): %', v_count;
    
    -- Building scale (1m/px)
    SELECT COUNT(*) INTO v_count 
    FROM get_visible_objects(
        ST_MakeEnvelope(0, 0, 200000, 200000, 4326),
        1.0,
        100
    );
    RAISE NOTICE 'Objects visible at building scale (1m/px): %', v_count;
    
    -- Room scale (0.01m/px)
    SELECT COUNT(*) INTO v_count 
    FROM get_visible_objects(
        ST_MakeEnvelope(100000, 50000, 130000, 70000, 4326),
        0.01,
        100
    );
    RAISE NOTICE 'Objects visible at room scale (0.01m/px): %', v_count;
END $$;