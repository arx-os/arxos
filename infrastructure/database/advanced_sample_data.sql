-- Advanced Sample Data Generation for Arxos Database
-- Comprehensive dataset demonstrating full BIM capabilities
-- Engineering precision: Realistic buildings, spatial relationships, device networks

BEGIN;

-- =============================================================================
-- PHASE 1: USERS AND PROJECTS
-- =============================================================================

-- Insert additional users with different roles
INSERT INTO users (email, username, password_hash, role) VALUES
('architect@arxos.com', 'lead_architect', '$2b$12$LQv3c1yqBwLFhyEpHYFjPObLqS8TfRvNxkvJO3s0MBiO2YhD6FNzC', 'architect'),
('engineer@arxos.com', 'structural_eng', '$2b$12$LQv3c1yqBwLFhyEpHYFjPObLqS8TfRvNxkvJO3s0MBiO2YhD6FNzC', 'engineer'),
('manager@arxos.com', 'project_mgr', '$2b$12$LQv3c1yqBwLFhyEpHYFjPObLqS8TfRvNxkvJO3s0MBiO2YhD6FNzC', 'manager'),
('analyst@arxos.com', 'data_analyst', '$2b$12$LQv3c1yqBwLFhyEpHYFjPObLqS8TfRvNxkvJO3s0MBiO2YhD6FNzC', 'analyst'),
('operator@arxos.com', 'facility_ops', '$2b$12$LQv3c1yqBwLFhyEpHYFjPObLqS8TfRvNxkvJO3s0MBiO2YhD6FNzC', 'operator');

-- Insert comprehensive projects
INSERT INTO projects (name, user_id) VALUES
('Smart Campus Initiative', 2),
('Industrial Complex Optimization', 3),
('Residential Tower Development', 2),
('Healthcare Facility Modernization', 3),
('Data Center Infrastructure', 4);

-- =============================================================================
-- PHASE 2: ADVANCED BUILDING PORTFOLIO
-- =============================================================================

-- Insert diverse building types with realistic specifications
INSERT INTO buildings (name, address, owner_id, project_id) VALUES
('Corporate Campus North', '500 Technology Drive, Palo Alto, CA 94301', 2, 2),
('Manufacturing Plant Delta', '1200 Industrial Blvd, San Jose, CA 95112', 3, 3),
('Residential Tower Azure', '750 Market Street, San Francisco, CA 94102', 2, 4),
('Medical Center Alpha', '2000 Healthcare Ave, Oakland, CA 94612', 3, 5),
('Data Center Prime', '300 Server Farm Rd, Santa Clara, CA 95051', 4, 6),
('Educational Complex Beta', '400 Learning Lane, Berkeley, CA 94720', 2, 2),
('Retail Hub Gamma', '1500 Commerce St, San Mateo, CA 94403', 3, 3);

-- =============================================================================
-- PHASE 3: COMPREHENSIVE FLOOR LAYOUTS
-- =============================================================================

-- Corporate Campus North (Building 2) - 8 floors
INSERT INTO floors (name, building_id) VALUES
('Basement Level B1', 2), ('Ground Floor', 2), ('Mezzanine', 2),
('Floor 2', 2), ('Floor 3', 2), ('Floor 4', 2), ('Floor 5', 2), ('Penthouse', 2);

-- Manufacturing Plant Delta (Building 3) - 3 floors  
INSERT INTO floors (name, building_id) VALUES
('Production Floor', 3), ('Quality Control', 3), ('Administration', 3);

-- Residential Tower Azure (Building 4) - 25 floors
INSERT INTO floors (name, building_id) 
SELECT 'Residential Floor ' || generate_series(1, 25), 4;

-- Medical Center Alpha (Building 5) - 6 floors
INSERT INTO floors (name, building_id) VALUES
('Emergency & Admissions', 5), ('Surgery & ICU', 5), ('General Medicine', 5),
('Diagnostics & Labs', 5), ('Outpatient Services', 5), ('Administration', 5);

-- Data Center Prime (Building 6) - 2 floors
INSERT INTO floors (name, building_id) VALUES
('Server Hall Alpha', 6), ('Server Hall Beta', 6);

-- =============================================================================
-- PHASE 4: SOPHISTICATED ROOM NETWORK WITH SPATIAL DATA
-- =============================================================================

-- Corporate Campus North rooms with precise spatial layouts
WITH floor_data AS (
  SELECT id, name FROM floors WHERE building_id = 2 ORDER BY id LIMIT 8
)
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id)
SELECT 
  'corp_' || f.id || '_' || room_num,
  CASE room_num
    WHEN 1 THEN 'Executive Conference'
    WHEN 2 THEN 'Open Workspace'
    WHEN 3 THEN 'Break Room'
    WHEN 4 THEN 'Meeting Room ' || chr(64 + room_num)
    ELSE 'Office Suite ' || room_num
  END,
  2, -- building_id
  f.id, -- floor_id
  CASE room_num
    WHEN 1 THEN 'conference'
    WHEN 2 THEN 'workspace'
    WHEN 3 THEN 'common'
    ELSE 'office'
  END,
  'active',
  ST_GeomFromText(
    'POLYGON((' || 
    (room_num * 15) || ' ' || ((f.id - 4) * 10) || ',' ||
    (room_num * 15 + 12) || ' ' || ((f.id - 4) * 10) || ',' ||
    (room_num * 15 + 12) || ' ' || ((f.id - 4) * 10 + 8) || ',' ||
    (room_num * 15) || ' ' || ((f.id - 4) * 10 + 8) || ',' ||
    (room_num * 15) || ' ' || ((f.id - 4) * 10) || '))', 4326),
  2, -- created_by
  2  -- project_id
FROM floor_data f
CROSS JOIN generate_series(1, 6) AS room_num;

-- Manufacturing Plant rooms with industrial specifications
WITH mfg_floors AS (
  SELECT id, name FROM floors WHERE building_id = 3 ORDER BY id
)
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id)
SELECT 
  'mfg_' || f.id || '_' || area_num,
  CASE 
    WHEN f.name = 'Production Floor' THEN 'Production Line ' || area_num
    WHEN f.name = 'Quality Control' THEN 'QC Station ' || area_num
    ELSE 'Admin Office ' || area_num
  END,
  3, -- building_id
  f.id,
  CASE 
    WHEN f.name = 'Production Floor' THEN 'production'
    WHEN f.name = 'Quality Control' THEN 'quality_control'
    ELSE 'office'
  END,
  'active',
  ST_GeomFromText(
    'POLYGON((' || 
    (area_num * 25) || ' ' || (f.id * 20) || ',' ||
    (area_num * 25 + 20) || ' ' || (f.id * 20) || ',' ||
    (area_num * 25 + 20) || ' ' || (f.id * 20 + 15) || ',' ||
    (area_num * 25) || ' ' || (f.id * 20 + 15) || ',' ||
    (area_num * 25) || ' ' || (f.id * 20) || '))', 4326),
  3, -- created_by
  3  -- project_id
FROM mfg_floors f
CROSS JOIN generate_series(1, 4) AS area_num;

-- Medical Center rooms with healthcare-specific layouts
WITH med_floors AS (
  SELECT id, name FROM floors WHERE building_id = 5 ORDER BY id
)
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id)
SELECT 
  'med_' || f.id || '_' || room_num,
  CASE 
    WHEN f.name LIKE '%Emergency%' THEN 'Emergency Room ' || room_num
    WHEN f.name LIKE '%Surgery%' THEN 'OR Suite ' || room_num
    WHEN f.name LIKE '%Medicine%' THEN 'Patient Room ' || room_num
    WHEN f.name LIKE '%Diagnostics%' THEN 'Lab Room ' || room_num
    WHEN f.name LIKE '%Outpatient%' THEN 'Clinic Room ' || room_num
    ELSE 'Admin Office ' || room_num
  END,
  5, -- building_id
  f.id,
  CASE 
    WHEN f.name LIKE '%Emergency%' THEN 'emergency'
    WHEN f.name LIKE '%Surgery%' THEN 'surgery'
    WHEN f.name LIKE '%Medicine%' THEN 'patient_room'
    WHEN f.name LIKE '%Diagnostics%' THEN 'laboratory'
    WHEN f.name LIKE '%Outpatient%' THEN 'clinic'
    ELSE 'office'
  END,
  'active',
  ST_GeomFromText(
    'POLYGON((' || 
    (room_num * 8) || ' ' || (f.id * 12) || ',' ||
    (room_num * 8 + 6) || ' ' || (f.id * 12) || ',' ||
    (room_num * 8 + 6) || ' ' || (f.id * 12 + 8) || ',' ||
    (room_num * 8) || ' ' || (f.id * 12 + 8) || ',' ||
    (room_num * 8) || ' ' || (f.id * 12) || '))', 4326),
  3, -- created_by
  5  -- project_id
FROM med_floors f
CROSS JOIN generate_series(1, 8) AS room_num;

-- Data Center server rooms with precision cooling zones
WITH dc_floors AS (
  SELECT id, name FROM floors WHERE building_id = 6 ORDER BY id
)
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id)
SELECT 
  'dc_' || f.id || '_' || zone_num,
  'Server Zone ' || chr(64 + zone_num) || ' (' || f.name || ')',
  6, -- building_id
  f.id,
  'server_room',
  'active',
  ST_GeomFromText(
    'POLYGON((' || 
    (zone_num * 20) || ' ' || (f.id * 30) || ',' ||
    (zone_num * 20 + 18) || ' ' || (f.id * 30) || ',' ||
    (zone_num * 20 + 18) || ' ' || (f.id * 30 + 25) || ',' ||
    (zone_num * 20) || ' ' || (f.id * 30 + 25) || ',' ||
    (zone_num * 20) || ' ' || (f.id * 30) || '))', 4326),
  4, -- created_by
  6  -- project_id
FROM dc_floors f
CROSS JOIN generate_series(1, 6) AS zone_num;

-- =============================================================================
-- PHASE 5: COMPREHENSIVE BIM OBJECTS (WALLS, DOORS, WINDOWS)
-- =============================================================================

-- Generate walls for all rooms (4 walls per room)
INSERT INTO walls (id, material, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_wall_' || wall_side,
  CASE 
    WHEN r.category IN ('server_room', 'laboratory') THEN 'reinforced_concrete'
    WHEN r.category IN ('production', 'quality_control') THEN 'steel_frame'
    ELSE 'drywall'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  CASE wall_side
    WHEN 'north' THEN ST_Boundary(ST_Buffer(r.geom, 0.1))
    WHEN 'south' THEN ST_Boundary(ST_Buffer(r.geom, -0.1))
    WHEN 'east' THEN ST_Boundary(ST_Buffer(r.geom, 0.05))
    ELSE ST_Boundary(ST_Buffer(r.geom, -0.05))
  END,
  r.category || '_wall',
  'active',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN (VALUES ('north'), ('south'), ('east'), ('west')) AS walls(wall_side)
WHERE r.building_id > 1; -- Skip original sample building

-- Generate doors (1-2 doors per room based on room type)
INSERT INTO doors (id, material, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_door_' || door_num,
  CASE 
    WHEN r.category IN ('emergency', 'surgery') THEN 'automatic_sliding'
    WHEN r.category = 'server_room' THEN 'security_access'
    WHEN r.category = 'production' THEN 'industrial_steel'
    ELSE 'standard_wood'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_PointOnSurface(r.geom), -- Door positioned at room center for simplicity
  r.category || '_access',
  'active',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN generate_series(1, 
  CASE 
    WHEN r.category IN ('conference', 'server_room') THEN 2
    ELSE 1
  END
) AS door_num
WHERE r.building_id > 1;

-- Generate windows (exterior rooms only)
INSERT INTO windows (id, material, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_window_' || window_num,
  CASE 
    WHEN r.building_id = 6 THEN 'none' -- Data centers have no windows
    WHEN r.category IN ('office', 'conference') THEN 'double_glazed'
    WHEN r.category = 'production' THEN 'industrial_safety'
    ELSE 'standard_single'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_Buffer(ST_PointOnSurface(r.geom), 0.5), -- Window area
  r.category || '_fenestration',
  CASE WHEN r.building_id = 6 THEN 'not_applicable' ELSE 'active' END,
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN generate_series(1, 
  CASE 
    WHEN r.building_id = 6 THEN 0 -- No windows in data center
    WHEN r.category IN ('conference', 'office') THEN 3
    WHEN r.category = 'production' THEN 2
    ELSE 1
  END
) AS window_num
WHERE r.building_id > 1 AND window_num > 0;

-- =============================================================================
-- PHASE 6: COMPREHENSIVE DEVICE NETWORK
-- =============================================================================

-- HVAC Systems
INSERT INTO devices (id, type, system, subtype, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_hvac_' || hvac_num,
  'HVAC',
  'climate_control',
  CASE 
    WHEN r.category = 'server_room' THEN 'precision_cooling'
    WHEN r.category IN ('surgery', 'laboratory') THEN 'medical_grade'
    WHEN r.category = 'production' THEN 'industrial_hvac'
    ELSE 'standard_vav'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_Centroid(r.geom),
  'environmental_control',
  'operational',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN generate_series(1, 
  CASE 
    WHEN r.category = 'server_room' THEN 4 -- High cooling demand
    WHEN r.category IN ('production', 'surgery') THEN 2
    ELSE 1
  END
) AS hvac_num
WHERE r.building_id > 1;

-- Security Systems
INSERT INTO devices (id, type, system, subtype, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_security_' || sec_num,
  'Security',
  'access_control',
  CASE 
    WHEN r.category IN ('server_room', 'surgery') THEN 'biometric_scanner'
    WHEN r.category IN ('production', 'laboratory') THEN 'keycard_reader'
    ELSE 'standard_camera'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_Buffer(ST_Centroid(r.geom), 0.2),
  'security_monitoring',
  'operational',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN generate_series(1, 2) AS sec_num
WHERE r.building_id > 1;

-- Lighting Systems
INSERT INTO devices (id, type, system, subtype, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_lighting_' || light_num,
  'Lighting',
  'illumination',
  CASE 
    WHEN r.category IN ('surgery', 'laboratory') THEN 'surgical_led'
    WHEN r.category = 'server_room' THEN 'low_heat_led'
    WHEN r.category = 'production' THEN 'industrial_fluorescent'
    ELSE 'smart_led'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_Buffer(ST_Centroid(r.geom), light_num * 0.3),
  'illumination_control',
  'operational',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN generate_series(1, 
  CASE 
    WHEN ST_Area(r.geom) > 300 THEN 6 -- Large rooms need more lighting
    WHEN ST_Area(r.geom) > 150 THEN 4
    ELSE 2
  END
) AS light_num
WHERE r.building_id > 1;

-- Fire Safety Systems
INSERT INTO devices (id, type, system, subtype, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_fire_' || fire_num,
  'Fire_Safety',
  'life_safety',
  CASE 
    WHEN r.category = 'server_room' THEN 'gas_suppression'
    WHEN r.category IN ('surgery', 'emergency') THEN 'medical_grade_sprinkler'
    WHEN r.category = 'production' THEN 'industrial_foam'
    ELSE 'standard_sprinkler'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_Buffer(ST_Centroid(r.geom), 0.1),
  'fire_suppression',
  'operational',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN generate_series(1, 
  CASE 
    WHEN r.category IN ('server_room', 'production') THEN 3
    ELSE 1
  END
) AS fire_num
WHERE r.building_id > 1;

-- =============================================================================
-- PHASE 7: CATEGORIES AND PERMISSIONS
-- =============================================================================

-- Insert comprehensive categories for all buildings
INSERT INTO categories (name, building_id) VALUES
-- Corporate Campus North
('office_spaces', 2), ('meeting_rooms', 2), ('common_areas', 2), ('technical_rooms', 2),
-- Manufacturing Plant
('production_areas', 3), ('quality_control', 3), ('administrative', 3), ('storage', 3),
-- Medical Center
('patient_care', 5), ('surgical_suites', 5), ('diagnostic_areas', 5), ('support_services', 5),
-- Data Center
('server_infrastructure', 6), ('cooling_systems', 6), ('power_distribution', 6), ('monitoring', 6);

-- Set up user category permissions with role-based access
INSERT INTO user_category_permissions (user_id, category_id, project_id, can_edit)
SELECT 
  u.id,
  c.id,
  CASE c.building_id 
    WHEN 2 THEN 2 -- Corporate project
    WHEN 3 THEN 3 -- Industrial project  
    WHEN 5 THEN 5 -- Healthcare project
    WHEN 6 THEN 6 -- Data center project
  END,
  CASE u.role
    WHEN 'admin' THEN true
    WHEN 'architect' THEN true
    WHEN 'engineer' THEN true
    WHEN 'manager' THEN c.name NOT LIKE '%technical%'
    ELSE false
  END
FROM users u
CROSS JOIN categories c
WHERE c.building_id IN (2, 3, 5, 6);

-- =============================================================================
-- PHASE 8: AUDIT LOGS AND COLLABORATION DATA
-- =============================================================================

-- Generate realistic audit log entries
INSERT INTO audit_logs (user_id, object_type, object_id, action, payload)
SELECT 
  (ARRAY[1,2,3,4,5])[1 + (random() * 4)::int], -- Random user
  'room',
  r.id,
  (ARRAY['created', 'updated', 'assigned', 'locked', 'optimized'])[1 + (random() * 4)::int],
  jsonb_build_object(
    'previous_status', 'draft',
    'new_status', r.status,
    'optimization_score', (random() * 40 + 60)::numeric(5,2),
    'area_sqm', ST_Area(r.geom),
    'timestamp', NOW() - (random() * interval '30 days')
  )
FROM rooms r
WHERE r.building_id > 1
ORDER BY random()
LIMIT 200;

-- Generate object history for tracking changes
INSERT INTO object_history (object_type, object_id, user_id, change_type, change_data)
SELECT 
  'device',
  d.id,
  (ARRAY[1,2,3,4,5])[1 + (random() * 4)::int],
  (ARRAY['status_update', 'configuration_change', 'maintenance', 'calibration'])[1 + (random() * 3)::int],
  jsonb_build_object(
    'device_type', d.type,
    'system', d.system,
    'previous_status', 'offline',
    'new_status', d.status,
    'performance_metric', (random() * 20 + 80)::numeric(5,2),
    'last_maintenance', NOW() - (random() * interval '90 days')
  )
FROM devices d
ORDER BY random()
LIMIT 150;

-- =============================================================================
-- PHASE 9: PERFORMANCE DATA AND ANALYTICS FOUNDATION
-- =============================================================================

-- Insert sample assignments for collaboration tracking
INSERT INTO assignments (object_type, object_id, user_id, status)
SELECT 
  'room',
  r.id,
  (ARRAY[2,3,4,5])[1 + (random() * 3)::int], -- Assign to non-admin users
  (ARRAY['assigned', 'in_progress', 'completed', 'reviewed'])[1 + (random() * 3)::int]
FROM rooms r
WHERE r.building_id > 1 AND random() < 0.4; -- 40% of rooms have assignments

-- Insert comments for collaboration
INSERT INTO comments (object_type, object_id, user_id, content)
SELECT 
  'room',
  r.id,
  (ARRAY[1,2,3,4,5])[1 + (random() * 4)::int],
  (ARRAY[
    'Optimization analysis complete - recommend layout adjustment',
    'HVAC system requires calibration for optimal efficiency',
    'Space utilization can be improved by 15% with minor changes',
    'Fire safety compliance verified - all systems operational',
    'Energy efficiency target exceeded by 8% this quarter',
    'Sensor network deployed and collecting baseline data',
    'Spatial conflict detected - requires engineering review'
  ])[1 + (random() * 6)::int]
FROM rooms r
WHERE r.building_id > 1 AND random() < 0.3; -- 30% of rooms have comments

COMMIT;

-- =============================================================================
-- SUMMARY STATISTICS
-- =============================================================================

-- Generate summary of created data
SELECT 
  'Sample Data Generation Complete' as status,
  (SELECT COUNT(*) FROM buildings WHERE id > 1) as new_buildings,
  (SELECT COUNT(*) FROM floors WHERE building_id > 1) as new_floors,
  (SELECT COUNT(*) FROM rooms WHERE building_id > 1) as new_rooms,
  (SELECT COUNT(*) FROM devices WHERE building_id > 1) as new_devices,
  (SELECT COUNT(*) FROM walls WHERE building_id > 1) as new_walls,
  (SELECT COUNT(*) FROM doors WHERE building_id > 1) as new_doors,
  (SELECT COUNT(*) FROM windows WHERE building_id > 1) as new_windows;