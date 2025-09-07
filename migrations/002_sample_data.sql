-- Sample building data for testing

-- Insert sample building
INSERT INTO buildings (id, name, address) VALUES 
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Building 42', '123 Main St, Tech City, TC 12345');

-- Insert building objects with hierarchical paths
INSERT INTO building_objects (building_id, path, name, object_type, location_x, location_y, location_z, status, properties) VALUES
    -- Electrical system
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical', 'electrical', 'system', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical/panels', 'panels', 'directory', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical/panels/panel_1', 'panel_1', 'panel', 10.5, 2.0, 1.5, 'active', '{"voltage": 240, "amperage": 200}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical/circuits', 'circuits', 'directory', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical/circuits/1', '1', 'circuit', 0, 0, 0, 'active', '{"amperage": 15}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical/circuits/2', '2', 'circuit', 0, 0, 0, 'active', '{"amperage": 20}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical/circuits/2/outlet_2A', 'outlet_2A', 'outlet', 10.5, 2.3, 1.2, 'active', '{"voltage": 120}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/electrical/circuits/2/outlet_2B', 'outlet_2B', 'outlet', 14.2, 2.3, 1.2, 'failed', '{"voltage": 120}'),
    
    -- Plumbing system  
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/plumbing', 'plumbing', 'system', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/plumbing/supply', 'supply', 'directory', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/plumbing/supply/hot', 'hot', 'directory', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/plumbing/supply/hot/valve_3', 'valve_3', 'valve', 8.0, 4.0, 0.5, 'active', '{"type": "ball", "size": "3/4 inch"}'),
    
    -- HVAC system
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/hvac', 'hvac', 'system', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/hvac/zones', 'zones', 'directory', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/hvac/zones/north', 'north', 'zone', 0, 10, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/hvac/zones/north/thermostat_1', 'thermostat_1', 'thermostat', 5.0, 10.0, 1.5, 'active', '{"setpoint": 72, "mode": "heat"}'),
    
    -- Spaces
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/spaces', 'spaces', 'system', 0, 0, 0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/spaces/floor_2', 'floor_2', 'floor', 0, 0, 3.0, 'active', '{}'),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/spaces/floor_2/room_205', 'room_205', 'room', 10, 10, 3.0, 'active', '{"occupancy": 4}');

-- Mark outlet_2B as needing repair
UPDATE building_objects 
SET needs_repair = true, health = 25 
WHERE path = '/electrical/circuits/2/outlet_2B';