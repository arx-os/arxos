-- Migration: Seed industry benchmarks and sample data
-- Date: 2024-01-15

-- Clear existing industry benchmarks to avoid duplicates
DELETE FROM industry_benchmarks;

-- Insert comprehensive industry benchmarks
INSERT INTO industry_benchmarks (equipment_type, system, metric, value, unit, source, year, description, region, building_type, confidence_level, sample_size) VALUES

-- HVAC System Benchmarks
('HVAC', 'Heating', 'efficiency', 85.0, 'percent', 'ASHRAE', 2023, 'Typical HVAC heating system efficiency rating', 'North America', 'Commercial', 0.95, 1250),
('HVAC', 'Cooling', 'efficiency', 82.0, 'percent', 'ASHRAE', 2023, 'Typical HVAC cooling system efficiency rating', 'North America', 'Commercial', 0.93, 1180),
('HVAC', 'Ventilation', 'air_changes_per_hour', 6.0, 'ACH', 'ASHRAE', 2023, 'Standard ventilation rate for commercial buildings', 'North America', 'Commercial', 0.90, 850),
('Chiller', 'HVAC', 'efficiency', 0.6, 'kW/ton', 'ASHRAE', 2023, 'Water-cooled chiller efficiency', 'North America', 'Commercial', 0.92, 450),
('Chiller', 'HVAC', 'efficiency', 0.8, 'kW/ton', 'ASHRAE', 2023, 'Air-cooled chiller efficiency', 'North America', 'Commercial', 0.89, 320),
('Boiler', 'HVAC', 'efficiency', 88.0, 'percent', 'ASHRAE', 2023, 'Gas-fired boiler efficiency', 'North America', 'Commercial', 0.94, 680),
('Boiler', 'HVAC', 'efficiency', 85.0, 'percent', 'ASHRAE', 2023, 'Oil-fired boiler efficiency', 'North America', 'Commercial', 0.91, 420),
('Air Handler', 'HVAC', 'efficiency', 75.0, 'percent', 'AMCA', 2023, 'Air handling unit fan efficiency', 'North America', 'Commercial', 0.88, 560),
('VAV Box', 'HVAC', 'efficiency', 80.0, 'percent', 'ASHRAE', 2023, 'Variable air volume box efficiency', 'North America', 'Commercial', 0.87, 890),
('Heat Pump', 'HVAC', 'efficiency', 3.2, 'COP', 'ASHRAE', 2023, 'Air-source heat pump coefficient of performance', 'North America', 'Commercial', 0.90, 720),

-- Electrical System Benchmarks
('Lighting', 'Electrical', 'efficiency', 90.0, 'percent', 'IES', 2023, 'LED lighting efficiency', 'North America', 'Commercial', 0.96, 2100),
('Lighting', 'Electrical', 'power_density', 0.8, 'W/sqft', 'ASHRAE', 2023, 'LED lighting power density', 'North America', 'Commercial', 0.94, 1850),
('Motor', 'Electrical', 'efficiency', 92.0, 'percent', 'NEMA', 2023, 'Premium efficiency motor', 'North America', 'Commercial', 0.95, 1100),
('Motor', 'Electrical', 'efficiency', 88.0, 'percent', 'NEMA', 2023, 'Standard efficiency motor', 'North America', 'Commercial', 0.92, 950),
('Transformer', 'Electrical', 'efficiency', 98.5, 'percent', 'IEEE', 2023, 'Distribution transformer efficiency', 'North America', 'Commercial', 0.97, 680),
('UPS', 'Electrical', 'efficiency', 95.0, 'percent', 'IEEE', 2023, 'Uninterruptible power supply efficiency', 'North America', 'Commercial', 0.93, 420),
('Generator', 'Electrical', 'efficiency', 85.0, 'percent', 'IEEE', 2023, 'Diesel generator efficiency', 'North America', 'Commercial', 0.91, 380),
('Switchgear', 'Electrical', 'efficiency', 99.0, 'percent', 'IEEE', 2023, 'Electrical switchgear efficiency', 'North America', 'Commercial', 0.96, 520),

-- Plumbing System Benchmarks
('Pump', 'Plumbing', 'efficiency', 75.0, 'percent', 'Hydraulic Institute', 2023, 'Centrifugal pump efficiency', 'North America', 'Commercial', 0.89, 650),
('Pump', 'Plumbing', 'efficiency', 80.0, 'percent', 'Hydraulic Institute', 2023, 'High-efficiency pump efficiency', 'North America', 'Commercial', 0.91, 480),
('Water Heater', 'Plumbing', 'efficiency', 90.0, 'percent', 'DOE', 2023, 'Tankless water heater efficiency', 'North America', 'Commercial', 0.94, 720),
('Water Heater', 'Plumbing', 'efficiency', 85.0, 'percent', 'DOE', 2023, 'Storage water heater efficiency', 'North America', 'Commercial', 0.92, 580),
('Backflow Preventer', 'Plumbing', 'pressure_loss', 5.0, 'PSI', 'ASSE', 2023, 'Typical pressure loss across backflow preventer', 'North America', 'Commercial', 0.88, 320),

-- Fire Protection System Benchmarks
('Fire Pump', 'Fire Protection', 'efficiency', 70.0, 'percent', 'NFPA', 2023, 'Fire pump efficiency', 'North America', 'Commercial', 0.87, 280),
('Sprinkler System', 'Fire Protection', 'coverage', 95.0, 'percent', 'NFPA', 2023, 'Sprinkler system coverage area', 'North America', 'Commercial', 0.95, 1200),
('Fire Alarm', 'Fire Protection', 'response_time', 30.0, 'seconds', 'NFPA', 2023, 'Fire alarm system response time', 'North America', 'Commercial', 0.93, 850),

-- Security System Benchmarks
('CCTV Camera', 'Security', 'resolution', 4.0, 'MP', 'SIA', 2023, 'Standard CCTV camera resolution', 'North America', 'Commercial', 0.90, 1100),
('Access Control', 'Security', 'response_time', 2.0, 'seconds', 'SIA', 2023, 'Access control system response time', 'North America', 'Commercial', 0.92, 680),
('Intrusion Detection', 'Security', 'detection_rate', 98.0, 'percent', 'SIA', 2023, 'Intrusion detection system accuracy', 'North America', 'Commercial', 0.94, 420),

-- Lifecycle and Maintenance Benchmarks
('HVAC', 'Maintenance', 'lifespan', 15.0, 'years', 'ASHRAE', 2023, 'Typical HVAC system lifespan', 'North America', 'Commercial', 0.88, 950),
('Electrical', 'Maintenance', 'lifespan', 25.0, 'years', 'IEEE', 2023, 'Typical electrical system lifespan', 'North America', 'Commercial', 0.92, 780),
('Plumbing', 'Maintenance', 'lifespan', 20.0, 'years', 'ASPE', 2023, 'Typical plumbing system lifespan', 'North America', 'Commercial', 0.89, 650),
('Fire Protection', 'Maintenance', 'lifespan', 30.0, 'years', 'NFPA', 2023, 'Typical fire protection system lifespan', 'North America', 'Commercial', 0.95, 420),
('Security', 'Maintenance', 'lifespan', 8.0, 'years', 'SIA', 2023, 'Typical security system lifespan', 'North America', 'Commercial', 0.87, 580),

-- Cost Benchmarks
('HVAC', 'Cost', 'installation_cost_per_sqft', 15.0, 'USD/sqft', 'RSMeans', 2023, 'HVAC system installation cost', 'North America', 'Commercial', 0.85, 1200),
('Electrical', 'Cost', 'installation_cost_per_sqft', 12.0, 'USD/sqft', 'RSMeans', 2023, 'Electrical system installation cost', 'North America', 'Commercial', 0.87, 980),
('Plumbing', 'Cost', 'installation_cost_per_sqft', 8.0, 'USD/sqft', 'RSMeans', 2023, 'Plumbing system installation cost', 'North America', 'Commercial', 0.84, 750),
('Fire Protection', 'Cost', 'installation_cost_per_sqft', 6.0, 'USD/sqft', 'RSMeans', 2023, 'Fire protection system installation cost', 'North America', 'Commercial', 0.86, 520),
('Security', 'Cost', 'installation_cost_per_sqft', 4.0, 'USD/sqft', 'RSMeans', 2023, 'Security system installation cost', 'North America', 'Commercial', 0.83, 680),

-- Energy Performance Benchmarks
('Building', 'Energy', 'eui', 80.0, 'kBTU/sqft/year', 'ENERGY STAR', 2023, 'Typical commercial building energy use intensity', 'North America', 'Commercial', 0.91, 2500),
('Building', 'Energy', 'eui', 120.0, 'kBTU/sqft/year', 'ENERGY STAR', 2023, 'High-performance building energy use intensity', 'North America', 'Commercial', 0.89, 850),
('Building', 'Energy', 'eui', 150.0, 'kBTU/sqft/year', 'ENERGY STAR', 2023, 'Standard building energy use intensity', 'North America', 'Commercial', 0.87, 1800),

-- European Benchmarks
('HVAC', 'Heating', 'efficiency', 88.0, 'percent', 'CEN', 2023, 'European HVAC heating system efficiency', 'Europe', 'Commercial', 0.94, 980),
('Lighting', 'Electrical', 'efficiency', 92.0, 'percent', 'CEN', 2023, 'European LED lighting efficiency', 'Europe', 'Commercial', 0.96, 1450),
('Building', 'Energy', 'eui', 70.0, 'kWh/m2/year', 'EPBD', 2023, 'European building energy performance', 'Europe', 'Commercial', 0.93, 1200),

-- Asian Benchmarks
('HVAC', 'Cooling', 'efficiency', 85.0, 'percent', 'ASHRAE', 2023, 'Asian HVAC cooling system efficiency', 'Asia', 'Commercial', 0.90, 850),
('Lighting', 'Electrical', 'efficiency', 88.0, 'percent', 'IES', 2023, 'Asian LED lighting efficiency', 'Asia', 'Commercial', 0.92, 1100),
('Building', 'Energy', 'eui', 90.0, 'kWh/m2/year', 'GBRC', 2023, 'Asian building energy performance', 'Asia', 'Commercial', 0.88, 950);

-- Insert sample buildings with different access levels
INSERT INTO buildings (name, address, city, state, zip_code, building_type, status, access_level, owner_id, created_at, updated_at) VALUES
('Downtown Office Tower', '123 Main St', 'New York', 'NY', '10001', 'Office', 'active', 'public', 1, NOW(), NOW()),
('Tech Campus Building A', '456 Innovation Dr', 'San Francisco', 'CA', '94105', 'Office', 'active', 'basic', 1, NOW(), NOW()),
('Medical Center West', '789 Health Ave', 'Chicago', 'IL', '60601', 'Healthcare', 'active', 'premium', 1, NOW(), NOW()),
('Financial District Plaza', '321 Wall St', 'New York', 'NY', '10005', 'Office', 'active', 'enterprise', 1, NOW(), NOW()),
('University Research Lab', '654 Science Blvd', 'Boston', 'MA', '02115', 'Education', 'active', 'premium', 1, NOW(), NOW()),
('Shopping Mall Central', '987 Retail Rd', 'Los Angeles', 'CA', '90210', 'Retail', 'active', 'public', 1, NOW(), NOW()),
('Hotel Grand', '147 Hospitality Way', 'Miami', 'FL', '33101', 'Hospitality', 'active', 'basic', 1, NOW(), NOW()),
('Manufacturing Plant', '258 Industrial Pkwy', 'Detroit', 'MI', '48201', 'Industrial', 'active', 'enterprise', 1, NOW(), NOW()),
('Data Center Alpha', '369 Technology Cir', 'Seattle', 'WA', '98101', 'Data Center', 'active', 'enterprise', 1, NOW(), NOW()),
('Government Building', '741 Civic Center Dr', 'Washington', 'DC', '20001', 'Government', 'active', 'premium', 1, NOW(), NOW());

-- Insert sample floors for buildings
INSERT INTO floors (building_id, name, svg_path, created_at, updated_at) VALUES
(1, 'Ground Floor', '/floors/building_1_ground.svg', NOW(), NOW()),
(1, '1st Floor', '/floors/building_1_floor1.svg', NOW(), NOW()),
(1, '2nd Floor', '/floors/building_1_floor2.svg', NOW(), NOW()),
(2, 'Ground Floor', '/floors/building_2_ground.svg', NOW(), NOW()),
(2, '1st Floor', '/floors/building_2_floor1.svg', NOW(), NOW()),
(3, 'Ground Floor', '/floors/building_3_ground.svg', NOW(), NOW()),
(3, '1st Floor', '/floors/building_3_floor1.svg', NOW(), NOW()),
(3, '2nd Floor', '/floors/building_3_floor2.svg', NOW(), NOW()),
(4, 'Ground Floor', '/floors/building_4_ground.svg', NOW(), NOW()),
(4, '1st Floor', '/floors/building_4_floor1.svg', NOW(), NOW()),
(5, 'Ground Floor', '/floors/building_5_ground.svg', NOW(), NOW()),
(6, 'Ground Floor', '/floors/building_6_ground.svg', NOW(), NOW()),
(7, 'Ground Floor', '/floors/building_7_ground.svg', NOW(), NOW()),
(8, 'Ground Floor', '/floors/building_8_ground.svg', NOW(), NOW()),
(9, 'Ground Floor', '/floors/building_9_ground.svg', NOW(), NOW()),
(10, 'Ground Floor', '/floors/building_10_ground.svg', NOW(), NOW());

-- Insert sample building assets
INSERT INTO building_assets (id, building_id, floor_id, room_id, symbol_id, asset_type, system, subsystem, location_floor, location_room, location_area, location_x, location_y, location_coordinates, specifications, metadata, age, efficiency_rating, lifecycle_stage, estimated_value, replacement_cost, status, created_by, created_at, updated_at) VALUES

-- HVAC Assets
('HVAC_001', 1, 1, 'ROOM_101', 'ahu', 'HVAC', 'Heating', 'Air Handling', 'Ground Floor', '101', 'North Wing', 150.5, 200.0, '150.5,200.0', 
'{"manufacturer": "Carrier", "model": "48TC", "capacity": "10 tons", "efficiency": "SEER 16", "voltage": "480V", "phase": "3"}',
'{"installation_date": "2020-03-15", "warranty_expiry": "2025-03-15", "last_maintenance": "2024-01-10", "next_maintenance": "2024-04-10"}',
4, 'A', 'operational', 25000.00, 30000.00, 'active', 1, NOW(), NOW()),

('HVAC_002', 1, 2, 'ROOM_201', 'chiller', 'HVAC', 'Cooling', 'Chiller', '1st Floor', '201', 'Mechanical Room', 300.0, 150.0, '300.0,150.0',
'{"manufacturer": "Trane", "model": "CVHE", "capacity": "200 tons", "efficiency": "0.6 kW/ton", "refrigerant": "R-134a"}',
'{"installation_date": "2019-06-20", "warranty_expiry": "2024-06-20", "last_maintenance": "2024-01-15", "next_maintenance": "2024-07-15"}',
5, 'A', 'operational', 150000.00, 180000.00, 'active', 1, NOW(), NOW()),

('HVAC_003', 2, 1, 'ROOM_101', 'vav', 'HVAC', 'Ventilation', 'VAV Box', 'Ground Floor', '101', 'Office Area', 100.0, 120.0, '100.0,120.0',
'{"manufacturer": "Titus", "model": "VAV-1", "capacity": "500 CFM", "control": "DDC"}',
'{"installation_date": "2021-02-10", "warranty_expiry": "2026-02-10", "last_maintenance": "2024-01-05", "next_maintenance": "2024-04-05"}',
3, 'A', 'operational', 2500.00, 3000.00, 'active', 1, NOW(), NOW()),

-- Electrical Assets
('ELEC_001', 1, 1, 'ROOM_102', 'panel', 'Electrical', 'Power Distribution', 'Panel', 'Ground Floor', '102', 'Electrical Room', 200.0, 250.0, '200.0,250.0',
'{"manufacturer": "Square D", "model": "NQOD", "capacity": "400A", "voltage": "480V", "phase": "3"}',
'{"installation_date": "2018-09-15", "warranty_expiry": "2023-09-15", "last_maintenance": "2024-01-20", "next_maintenance": "2024-07-20"}',
6, 'A', 'operational', 15000.00, 18000.00, 'active', 1, NOW(), NOW()),

('ELEC_002', 1, 1, 'ROOM_103', 'ups', 'Electrical', 'Power Protection', 'UPS', 'Ground Floor', '103', 'Server Room', 180.0, 180.0, '180.0,180.0',
'{"manufacturer": "APC", "model": "Symmetra LX", "capacity": "10kVA", "runtime": "30 minutes", "battery_type": "VRLA"}',
'{"installation_date": "2022-01-10", "warranty_expiry": "2027-01-10", "last_maintenance": "2024-01-12", "next_maintenance": "2024-04-12"}',
2, 'A', 'operational', 25000.00, 30000.00, 'active', 1, NOW(), NOW()),

('ELEC_003', 2, 1, 'ROOM_102', 'lighting', 'Electrical', 'Lighting', 'LED Fixtures', 'Ground Floor', '102', 'Office Area', 120.0, 140.0, '120.0,140.0',
'{"manufacturer": "Philips", "model": "LED Panel", "wattage": "32W", "lumens": "4000", "color_temp": "4000K"}',
'{"installation_date": "2021-08-20", "warranty_expiry": "2026-08-20", "last_maintenance": "2024-01-08", "next_maintenance": "2024-07-08"}',
3, 'A', 'operational', 800.00, 1000.00, 'active', 1, NOW(), NOW()),

-- Plumbing Assets
('PLUMB_001', 1, 1, 'ROOM_104', 'pump', 'Plumbing', 'Water Distribution', 'Pump', 'Ground Floor', '104', 'Mechanical Room', 250.0, 300.0, '250.0,300.0',
'{"manufacturer": "Grundfos", "model": "CRN", "capacity": "50 GPM", "head": "100 ft", "efficiency": "75%"}',
'{"installation_date": "2019-11-05", "warranty_expiry": "2024-11-05", "last_maintenance": "2024-01-18", "next_maintenance": "2024-04-18"}',
5, 'A', 'operational', 12000.00, 15000.00, 'active', 1, NOW(), NOW()),

('PLUMB_002', 1, 1, 'ROOM_105', 'wh', 'Plumbing', 'Water Heating', 'Water Heater', 'Ground Floor', '105', 'Mechanical Room', 280.0, 320.0, '280.0,320.0',
'{"manufacturer": "A.O. Smith", "model": "Commercial", "capacity": "100 gallons", "efficiency": "90%", "fuel": "Natural Gas"}',
'{"installation_date": "2020-05-12", "warranty_expiry": "2025-05-12", "last_maintenance": "2024-01-14", "next_maintenance": "2024-07-14"}',
4, 'A', 'operational', 8000.00, 10000.00, 'active', 1, NOW(), NOW()),

-- Fire Protection Assets
('FIRE_001', 1, 1, 'ROOM_106', 'fire_pump', 'Fire Protection', 'Fire Suppression', 'Fire Pump', 'Ground Floor', '106', 'Fire Pump Room', 320.0, 350.0, '320.0,350.0',
'{"manufacturer": "Peerless", "model": "Fire Pump", "capacity": "500 GPM", "pressure": "150 PSI", "driver": "Electric"}',
'{"installation_date": "2018-12-01", "warranty_expiry": "2023-12-01", "last_maintenance": "2024-01-16", "next_maintenance": "2024-04-16"}',
6, 'A', 'operational', 45000.00, 55000.00, 'active', 1, NOW(), NOW()),

('FIRE_002', 1, 1, 'ROOM_107', 'sprinkler', 'Fire Protection', 'Fire Suppression', 'Sprinkler System', 'Ground Floor', '107', 'Throughout Building', 150.0, 150.0, '150.0,150.0',
'{"manufacturer": "Tyco", "model": "Wet Pipe", "coverage": "95%", "pressure": "50 PSI", "type": "Automatic"}',
'{"installation_date": "2018-12-01", "warranty_expiry": "2023-12-01", "last_maintenance": "2024-01-17", "next_maintenance": "2024-07-17"}',
6, 'A', 'operational', 35000.00, 42000.00, 'active', 1, NOW(), NOW()),

-- Security Assets
('SEC_001', 1, 1, 'ROOM_108', 'cctv', 'Security', 'Surveillance', 'CCTV Camera', 'Ground Floor', '108', 'Lobby', 100.0, 100.0, '100.0,100.0',
'{"manufacturer": "Hikvision", "model": "Dome Camera", "resolution": "4MP", "night_vision": "Yes", "ptz": "No"}',
'{"installation_date": "2021-03-15", "warranty_expiry": "2026-03-15", "last_maintenance": "2024-01-19", "next_maintenance": "2024-04-19"}',
3, 'A', 'operational', 500.00, 600.00, 'active', 1, NOW(), NOW()),

('SEC_002', 1, 1, 'ROOM_109', 'card_reader', 'Security', 'Access Control', 'Card Reader', 'Ground Floor', '109', 'Main Entrance', 80.0, 120.0, '80.0,120.0',
'{"manufacturer": "HID", "model": "iCLASS", "technology": "RFID", "read_range": "3 inches"}',
'{"installation_date": "2021-03-15", "warranty_expiry": "2026-03-15", "last_maintenance": "2024-01-20", "next_maintenance": "2024-04-20"}',
3, 'A', 'operational', 800.00, 1000.00, 'active', 1, NOW(), NOW());

-- Insert sample data vendor API keys for testing
INSERT INTO data_vendor_api_keys (`key`, vendor_name, email, access_level, rate_limit, is_active, expires_at, created_at, updated_at) VALUES
('arx_test_basic_1234567890', 'Test Vendor Basic', 'basic@testvendor.com', 'basic', 1000, true, DATE_ADD(NOW(), INTERVAL 1 YEAR), NOW(), NOW()),
('arx_test_premium_1234567890', 'Test Vendor Premium', 'premium@testvendor.com', 'premium', 5000, true, DATE_ADD(NOW(), INTERVAL 1 YEAR), NOW(), NOW()),
('arx_test_enterprise_1234567890', 'Test Vendor Enterprise', 'enterprise@testvendor.com', 'enterprise', 20000, true, DATE_ADD(NOW(), INTERVAL 1 YEAR), NOW(), NOW()),
('arx_inactive_key_1234567890', 'Inactive Test Vendor', 'inactive@testvendor.com', 'basic', 1000, false, DATE_ADD(NOW(), INTERVAL 1 YEAR), NOW(), NOW());

-- Insert sample API key usage data for testing
INSERT INTO api_key_usage (api_key_id, endpoint, method, status, response_time, request_size, response_size, ip_address, user_agent, error_code, error_message, rate_limit_hit, created_at) VALUES
(1, '/api/vendor/buildings', 'GET', 200, 150, 0, 2048, '192.168.1.100', 'curl/7.68.0', NULL, NULL, false, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(1, '/api/vendor/buildings/1/inventory', 'GET', 200, 250, 0, 5120, '192.168.1.100', 'curl/7.68.0', NULL, NULL, false, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
(2, '/api/vendor/buildings', 'GET', 200, 120, 0, 2048, '10.0.0.50', 'PostmanRuntime/7.29.0', NULL, NULL, false, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(2, '/api/vendor/industry-benchmarks', 'GET', 200, 180, 0, 3072, '10.0.0.50', 'PostmanRuntime/7.29.0', NULL, NULL, false, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(3, '/api/vendor/buildings', 'GET', 200, 100, 0, 2048, '172.16.0.25', 'python-requests/2.28.0', NULL, NULL, false, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
(3, '/api/vendor/buildings/4/summary', 'GET', 200, 300, 0, 1536, '172.16.0.25', 'python-requests/2.28.0', NULL, NULL, false, DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
(1, '/api/vendor/buildings/999/inventory', 'GET', 404, 50, 0, 256, '192.168.1.100', 'curl/7.68.0', 'NOT_FOUND', 'Building not found', false, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
(1, '/api/vendor/buildings', 'GET', 429, 10, 0, 128, '192.168.1.100', 'curl/7.68.0', 'RATE_LIMIT', 'Rate limit exceeded', true, NOW());

-- Create sample asset history records
INSERT INTO asset_history (asset_id, event_type, event_date, description, cost, contractor, warranty, documents, created_by, created_at) VALUES
('HVAC_001', 'installation', '2020-03-15', 'Initial installation of Carrier 48TC air handler', 25000.00, 'ABC HVAC Services', '5 years parts and labor', '["installation_certificate.pdf", "warranty_document.pdf"]', 1, NOW()),
('HVAC_001', 'maintenance', '2024-01-10', 'Annual preventive maintenance - filter replacement, belt adjustment, motor inspection', 500.00, 'ABC HVAC Services', NULL, '["maintenance_report.pdf", "filter_replacement_log.pdf"]', 1, NOW()),
('ELEC_001', 'installation', '2018-09-15', 'Installation of Square D NQOD electrical panel', 15000.00, 'XYZ Electrical', '3 years parts and labor', '["electrical_permit.pdf", "inspection_certificate.pdf"]', 1, NOW()),
('ELEC_001', 'upgrade', '2023-06-20', 'Panel upgrade to accommodate increased load requirements', 8000.00, 'XYZ Electrical', '2 years parts and labor', '["upgrade_specifications.pdf", "load_calculation.pdf"]', 1, NOW());

-- Create sample asset maintenance records
INSERT INTO asset_maintenance (asset_id, maintenance_type, status, scheduled_date, completed_date, description, cost, technician, parts, notes, created_by, created_at, updated_at) VALUES
('HVAC_001', 'preventive', 'completed', '2024-01-10', '2024-01-10', 'Annual preventive maintenance', 500.00, 'John Smith', '["air_filter", "belt"]', 'All systems operating normally', 1, NOW(), NOW()),
('HVAC_002', 'preventive', 'scheduled', '2024-02-15', NULL, 'Quarterly chiller maintenance', 1200.00, 'Mike Johnson', '["refrigerant", "oil_filter"]', 'Scheduled for February maintenance window', 1, NOW(), NOW()),
('ELEC_001', 'inspection', 'completed', '2024-01-20', '2024-01-20', 'Annual electrical panel inspection', 300.00, 'Sarah Wilson', '[]', 'Panel in good condition, no issues found', 1, NOW(), NOW()),
('PLUMB_001', 'corrective', 'in_progress', '2024-01-25', NULL, 'Pump bearing replacement', 800.00, 'David Brown', '["bearings", "seals"]', 'Bearing noise detected during routine inspection', 1, NOW(), NOW());

-- Create sample asset valuations
INSERT INTO asset_valuations (asset_id, valuation_date, valuation_type, value, currency, valuation_method, notes, created_by, created_at) VALUES
('HVAC_001', '2024-01-01', 'market', 25000.00, 'USD', 'Comparable sales', 'Based on similar equipment sales in the market', 1, NOW()),
('HVAC_001', '2024-01-01', 'replacement', 30000.00, 'USD', 'Replacement cost', 'Current replacement cost including installation', 1, NOW()),
('ELEC_001', '2024-01-01', 'market', 15000.00, 'USD', 'Comparable sales', 'Market value based on similar electrical panels', 1, NOW()),
('ELEC_001', '2024-01-01', 'replacement', 18000.00, 'USD', 'Replacement cost', 'Replacement cost including labor and materials', 1, NOW());

-- Update building access levels to match the sample data
UPDATE buildings SET access_level = 'public' WHERE id IN (1, 6);
UPDATE buildings SET access_level = 'basic' WHERE id IN (2, 7);
UPDATE buildings SET access_level = 'premium' WHERE id IN (3, 5, 10);
UPDATE buildings SET access_level = 'enterprise' WHERE id IN (4, 8, 9); 