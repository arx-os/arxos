-- Advanced Sample Data Generation for Arxos Database (Fixed)
-- Comprehensive dataset demonstrating full BIM capabilities
-- Engineering precision: Realistic buildings, spatial relationships, device networks

BEGIN;

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

-- Insert diverse building types
INSERT INTO buildings (name, address, owner_id, project_id) VALUES
('Corporate Campus North', '500 Technology Drive, Palo Alto, CA 94301', 2, 2),
('Manufacturing Plant Delta', '1200 Industrial Blvd, San Jose, CA 95112', 3, 3),
('Residential Tower Azure', '750 Market Street, San Francisco, CA 94102', 2, 4),
('Medical Center Alpha', '2000 Healthcare Ave, Oakland, CA 94612', 3, 5),
('Data Center Prime', '300 Server Farm Rd, Santa Clara, CA 95051', 4, 6);

-- Corporate Campus North - 5 floors
INSERT INTO floors (name, building_id) VALUES
('Basement Level', 2), ('Ground Floor', 2), ('Floor 2', 2), ('Floor 3', 2), ('Penthouse', 2);

-- Manufacturing Plant - 3 floors  
INSERT INTO floors (name, building_id) VALUES
('Production Floor', 3), ('Quality Control', 3), ('Administration', 3);

-- Medical Center - 4 floors
INSERT INTO floors (name, building_id) VALUES
('Emergency & Admissions', 5), ('Surgery & ICU', 5), ('General Medicine', 5), ('Administration', 5);

-- Data Center - 2 floors
INSERT INTO floors (name, building_id) VALUES
('Server Hall Alpha', 6), ('Server Hall Beta', 6);

-- Corporate Campus rooms with precise spatial layouts
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id) VALUES
('corp_01', 'Executive Conference Room', 2, 5, 'conference', 'active', ST_GeomFromText('POLYGON((0 0, 20 0, 20 15, 0 15, 0 0))', 4326), 2, 2),
('corp_02', 'Open Workspace Alpha', 2, 6, 'workspace', 'active', ST_GeomFromText('POLYGON((25 0, 65 0, 65 25, 25 25, 25 0))', 4326), 2, 2),
('corp_03', 'Break Room Central', 2, 6, 'common', 'active', ST_GeomFromText('POLYGON((70 0, 90 0, 90 12, 70 12, 70 0))', 4326), 2, 2),
('corp_04', 'Meeting Room Beta', 2, 7, 'conference', 'active', ST_GeomFromText('POLYGON((0 20, 15 20, 15 30, 0 30, 0 20))', 4326), 2, 2),
('corp_05', 'Tech Lab Gamma', 2, 7, 'laboratory', 'active', ST_GeomFromText('POLYGON((20 20, 40 20, 40 35, 20 35, 20 20))', 4326), 2, 2),
('corp_06', 'Server Closet', 2, 5, 'technical', 'active', ST_GeomFromText('POLYGON((45 20, 55 20, 55 25, 45 25, 45 20))', 4326), 2, 2);

-- Manufacturing rooms
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id) VALUES
('mfg_01', 'Production Line Alpha', 3, 9, 'production', 'active', ST_GeomFromText('POLYGON((0 0, 50 0, 50 30, 0 30, 0 0))', 4326), 3, 3),
('mfg_02', 'Production Line Beta', 3, 9, 'production', 'active', ST_GeomFromText('POLYGON((55 0, 105 0, 105 30, 55 30, 55 0))', 4326), 3, 3),
('mfg_03', 'Quality Control Station', 3, 10, 'quality_control', 'active', ST_GeomFromText('POLYGON((0 35, 30 35, 30 50, 0 50, 0 35))', 4326), 3, 3),
('mfg_04', 'Administrative Office', 3, 11, 'office', 'active', ST_GeomFromText('POLYGON((35 35, 60 35, 60 50, 35 50, 35 35))', 4326), 3, 3);

-- Medical Center rooms
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id) VALUES
('med_01', 'Emergency Room 1', 5, 12, 'emergency', 'active', ST_GeomFromText('POLYGON((0 0, 12 0, 12 10, 0 10, 0 0))', 4326), 3, 5),
('med_02', 'Emergency Room 2', 5, 12, 'emergency', 'active', ST_GeomFromText('POLYGON((15 0, 27 0, 27 10, 15 10, 15 0))', 4326), 3, 5),
('med_03', 'Operating Theater 1', 5, 13, 'surgery', 'active', ST_GeomFromText('POLYGON((0 15, 15 15, 15 25, 0 25, 0 15))', 4326), 3, 5),
('med_04', 'Operating Theater 2', 5, 13, 'surgery', 'active', ST_GeomFromText('POLYGON((20 15, 35 15, 35 25, 20 25, 20 15))', 4326), 3, 5),
('med_05', 'Patient Room 101', 5, 14, 'patient_room', 'active', ST_GeomFromText('POLYGON((0 30, 8 30, 8 35, 0 35, 0 30))', 4326), 3, 5),
('med_06', 'Laboratory A', 5, 14, 'laboratory', 'active', ST_GeomFromText('POLYGON((10 30, 25 30, 25 40, 10 40, 10 30))', 4326), 3, 5);

-- Data Center server rooms
INSERT INTO rooms (id, name, building_id, floor_id, category, status, geom, created_by, project_id) VALUES
('dc_01', 'Server Zone Alpha', 6, 16, 'server_room', 'active', ST_GeomFromText('POLYGON((0 0, 25 0, 25 20, 0 20, 0 0))', 4326), 4, 6),
('dc_02', 'Server Zone Beta', 6, 16, 'server_room', 'active', ST_GeomFromText('POLYGON((30 0, 55 0, 55 20, 30 20, 30 0))', 4326), 4, 6),
('dc_03', 'Server Zone Gamma', 6, 17, 'server_room', 'active', ST_GeomFromText('POLYGON((0 25, 25 25, 25 45, 0 45, 0 25))', 4326), 4, 6),
('dc_04', 'Cooling Equipment', 6, 17, 'technical', 'active', ST_GeomFromText('POLYGON((30 25, 45 25, 45 35, 30 35, 30 25))', 4326), 4, 6);

-- Generate walls (LineString geometry for walls)
INSERT INTO walls (id, material, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_wall_' || wall_num,
  CASE 
    WHEN r.category IN ('server_room', 'technical') THEN 'reinforced_concrete'
    WHEN r.category IN ('production', 'quality_control') THEN 'steel_frame'
    WHEN r.category IN ('surgery', 'laboratory') THEN 'medical_grade'
    ELSE 'drywall'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  -- Create LineString walls from polygon boundary
  ST_MakeLine(
    ST_PointN(ST_Boundary(r.geom), wall_num),
    ST_PointN(ST_Boundary(r.geom), CASE WHEN wall_num = ST_NPoints(ST_Boundary(r.geom)) THEN 1 ELSE wall_num + 1 END)
  ),
  r.category || '_wall',
  'active',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN generate_series(1, 4) AS wall_num -- 4 walls per room
WHERE r.building_id > 1;

-- Generate doors (Point geometry)
INSERT INTO doors (id, material, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_door',
  CASE 
    WHEN r.category IN ('emergency', 'surgery') THEN 'automatic_sliding'
    WHEN r.category = 'server_room' THEN 'security_access'
    WHEN r.category = 'production' THEN 'industrial_steel'
    ELSE 'standard_wood'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_PointOnSurface(r.geom),
  r.category || '_access',
  'active',
  r.created_by,
  r.project_id
FROM rooms r
WHERE r.building_id > 1;

-- Generate windows (LineString geometry for windows)
INSERT INTO windows (id, material, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_window',
  CASE 
    WHEN r.building_id = 6 THEN 'none' -- Data centers have no windows
    WHEN r.category IN ('office', 'conference') THEN 'double_glazed'
    WHEN r.category = 'production' THEN 'industrial_safety'
    ELSE 'standard_single'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  -- Create a small LineString for window
  ST_MakeLine(
    ST_PointN(ST_Boundary(r.geom), 1),
    ST_PointN(ST_Boundary(r.geom), 2)
  ),
  r.category || '_fenestration',
  CASE WHEN r.building_id = 6 THEN 'not_applicable' ELSE 'active' END,
  r.created_by,
  r.project_id
FROM rooms r
WHERE r.building_id > 1 AND r.building_id != 6; -- No windows in data center

-- Generate comprehensive device network
INSERT INTO devices (id, type, system, subtype, building_id, floor_id, room_id, geom, category, status, created_by, project_id)
SELECT 
  r.id || '_' || device_type || '_' || device_num,
  device_type,
  CASE device_type
    WHEN 'HVAC' THEN 'climate_control'
    WHEN 'Security' THEN 'access_control'
    WHEN 'Lighting' THEN 'illumination'
    WHEN 'Fire_Safety' THEN 'life_safety'
    WHEN 'Network' THEN 'data_infrastructure'
    ELSE 'monitoring'
  END,
  CASE 
    WHEN device_type = 'HVAC' AND r.category = 'server_room' THEN 'precision_cooling'
    WHEN device_type = 'HVAC' AND r.category IN ('surgery', 'laboratory') THEN 'medical_grade'
    WHEN device_type = 'Security' AND r.category IN ('server_room', 'surgery') THEN 'biometric_scanner'
    WHEN device_type = 'Lighting' AND r.category = 'surgery' THEN 'surgical_led'
    WHEN device_type = 'Fire_Safety' AND r.category = 'server_room' THEN 'gas_suppression'
    ELSE 'standard'
  END,
  r.building_id,
  r.floor_id,
  r.id,
  ST_Buffer(ST_Centroid(r.geom), device_num * 0.5),
  CASE device_type
    WHEN 'HVAC' THEN 'environmental_control'
    WHEN 'Security' THEN 'security_monitoring'  
    WHEN 'Lighting' THEN 'illumination_control'
    WHEN 'Fire_Safety' THEN 'fire_suppression'
    ELSE 'data_systems'
  END,
  'operational',
  r.created_by,
  r.project_id
FROM rooms r
CROSS JOIN (VALUES ('HVAC'), ('Security'), ('Lighting'), ('Fire_Safety'), ('Network')) AS devices(device_type)
CROSS JOIN generate_series(1, 2) AS device_num
WHERE r.building_id > 1;

COMMIT;

-- Generate summary of created data
SELECT 
  'Advanced Sample Data Complete' as status,
  (SELECT COUNT(*) FROM buildings WHERE id > 1) as new_buildings,
  (SELECT COUNT(*) FROM floors WHERE building_id > 1) as new_floors,
  (SELECT COUNT(*) FROM rooms WHERE building_id > 1) as new_rooms,
  (SELECT COUNT(*) FROM devices WHERE building_id > 1) as new_devices,
  (SELECT COUNT(*) FROM walls WHERE building_id > 1) as new_walls,
  (SELECT COUNT(*) FROM doors WHERE building_id > 1) as new_doors,
  (SELECT COUNT(*) FROM windows WHERE building_id > 1) as new_windows;