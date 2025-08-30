-- ArxObject type definitions for semantic building intelligence
-- Maps to src/core/object_types.rs constants

-- Object type lookup table for human-readable descriptions
CREATE TABLE IF NOT EXISTS object_types (
    type_id INTEGER PRIMARY KEY, -- Maps to ArxObject.object_type
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    typical_properties TEXT, -- JSON schema for expected properties
    bilt_reward INTEGER DEFAULT 10 -- Base BILT points for marking this type
);

-- Standard building object types (matches Rust constants)
INSERT OR IGNORE INTO object_types VALUES 
-- Electrical systems (type_id 1-15)
(1, 'outlet', 'electrical', 'Standard electrical outlet', '{"circuit": "string", "voltage": "number", "amperage": "number", "gfci": "boolean"}', 10),
(2, 'light_switch', 'electrical', 'Light switch or dimmer', '{"circuit": "string", "switch_type": "string", "controlled_lights": "array"}', 8),
(3, 'light_fixture', 'electrical', 'Light fixture or luminaire', '{"wattage": "number", "type": "string", "controlled_by": "string"}', 15),
(4, 'electrical_panel', 'electrical', 'Circuit breaker panel', '{"total_amps": "number", "circuits": "array", "manufacturer": "string"}', 50),
(5, 'junction_box', 'electrical', 'Electrical junction box', '{"circuit": "string", "wire_gauge": "string", "connections": "number"}', 5),

-- HVAC systems (type_id 16-30)
(16, 'thermostat', 'hvac', 'Temperature control device', '{"current_temp": "number", "setpoint": "number", "zone": "string", "mode": "string"}', 12),
(17, 'air_handler', 'hvac', 'Air handling unit', '{"capacity": "number", "zone": "string", "model": "string", "maintenance_date": "string"}', 40),
(18, 'ductwork', 'hvac', 'Air distribution ducting', '{"size": "string", "material": "string", "insulation": "boolean", "zone": "string"}', 8),
(19, 'hvac_vent', 'hvac', 'Supply or return air vent', '{"size": "string", "type": "string", "flow_rate": "number", "zone": "string"}', 6),
(20, 'hvac_unit', 'hvac', 'Rooftop or split system unit', '{"tonnage": "number", "model": "string", "refrigerant": "string", "install_date": "string"}', 60),

-- Safety and security (type_id 31-45)
(31, 'fire_extinguisher', 'safety', 'Portable fire extinguisher', '{"type": "string", "size": "string", "expiration": "string", "last_inspection": "string"}', 25),
(32, 'smoke_detector', 'safety', 'Smoke detection device', '{"type": "string", "battery_life": "string", "last_test": "string", "zone": "string"}', 20),
(33, 'emergency_exit', 'safety', 'Emergency egress route', '{"width": "number", "lighted": "boolean", "accessible": "boolean", "capacity": "number"}', 30),
(34, 'security_camera', 'security', 'Surveillance camera', '{"resolution": "string", "ptz": "boolean", "night_vision": "boolean", "recording": "boolean"}', 18),
(35, 'access_control', 'security', 'Door access control system', '{"card_reader": "boolean", "biometric": "boolean", "access_levels": "array"}', 22),

-- Plumbing systems (type_id 46-60)  
(46, 'water_valve', 'plumbing', 'Water shut-off valve', '{"size": "string", "material": "string", "pressure_rating": "number", "accessible": "boolean"}', 10),
(47, 'water_heater', 'plumbing', 'Hot water heating system', '{"capacity": "number", "fuel_type": "string", "model": "string", "install_date": "string"}', 45),
(48, 'drain', 'plumbing', 'Floor or fixture drain', '{"size": "string", "location": "string", "connected_to": "string"}', 5),
(49, 'water_meter', 'plumbing', 'Water usage monitoring device', '{"size": "string", "type": "string", "last_reading": "number", "location": "string"}', 15),

-- Structural elements (type_id 61-75)
(61, 'door', 'structural', 'Interior or exterior door', '{"material": "string", "width": "number", "height": "number", "fire_rated": "boolean"}', 8),
(62, 'window', 'structural', 'Window opening', '{"material": "string", "width": "number", "height": "number", "glazing": "string"}', 8),
(63, 'wall', 'structural', 'Interior or exterior wall', '{"material": "string", "thickness": "number", "load_bearing": "boolean", "fire_rated": "boolean"}', 12),
(64, 'column', 'structural', 'Structural support column', '{"material": "string", "size": "string", "load_capacity": "number"}', 15),

-- Technology systems (type_id 76-90)
(76, 'wifi_access_point', 'technology', 'Wireless network access point', '{"ssid": "string", "frequency": "string", "power": "number", "coverage_area": "number"}', 20),
(77, 'network_switch', 'technology', 'Network switching equipment', '{"ports": "number", "speed": "string", "managed": "boolean", "poe": "boolean"}', 35),
(78, 'security_panel', 'technology', 'Security system control panel', '{"zones": "number", "wireless": "boolean", "cellular": "boolean"}', 40),

-- Room/space definitions (type_id 91-100)
(91, 'room', 'space', 'Defined interior space', '{"area": "number", "occupancy": "number", "use_type": "string", "accessibility": "boolean"}', 25),
(92, 'corridor', 'space', 'Hallway or passage', '{"width": "number", "length": "number", "public": "boolean"}', 15),
(93, 'stairway', 'space', 'Vertical circulation', '{"flights": "number", "handrails": "boolean", "emergency": "boolean"}', 20),
(94, 'elevator', 'space', 'Vertical transportation', '{"capacity": "number", "floors_served": "array", "accessible": "boolean"}', 50),

-- Specialized stadium equipment (type_id 101-110) 
(101, 'concession_stand', 'stadium', 'Food service area', '{"type": "string", "electrical_load": "number", "water": "boolean", "gas": "boolean"}', 35),
(102, 'scoreboard', 'stadium', 'Electronic display system', '{"type": "string", "resolution": "string", "power": "number", "network": "boolean"}', 75),
(103, 'field_lighting', 'stadium', 'Athletic field illumination', '{"wattage": "number", "type": "string", "control_zone": "string", "lux_level": "number"}', 40),
(104, 'sound_system', 'stadium', 'Audio amplification equipment', '{"zones": "array", "power": "number", "type": "string", "backup": "boolean"}', 30);

-- Property validation constraints
CREATE TABLE IF NOT EXISTS property_constraints (
    object_type_id INTEGER,
    property_name TEXT,
    data_type TEXT NOT NULL, -- 'string', 'number', 'boolean', 'array', 'object'
    required BOOLEAN DEFAULT FALSE,
    min_value REAL,
    max_value REAL,
    allowed_values TEXT, -- JSON array of allowed values
    
    FOREIGN KEY (object_type_id) REFERENCES object_types(type_id)
);

-- BILT reward multipliers for professional verification
CREATE TABLE IF NOT EXISTS professional_multipliers (
    role TEXT PRIMARY KEY,
    multiplier REAL NOT NULL DEFAULT 1.0,
    description TEXT
);

INSERT OR IGNORE INTO professional_multipliers VALUES
('contractor', 1.0, 'Base rate for general contractors'),
('electrician', 1.2, '20% bonus for electrical objects'),
('hvac_tech', 1.2, '20% bonus for HVAC objects'),  
('plumber', 1.2, '20% bonus for plumbing objects'),
('facilities_manager', 1.1, '10% bonus for facility oversight'),
('safety_inspector', 1.3, '30% bonus for safety-critical objects'),
('licensed_professional', 1.5, '50% bonus for licensed professionals');

-- Index for fast object type lookups
CREATE INDEX IF NOT EXISTS idx_object_types_category ON object_types(category);
CREATE INDEX IF NOT EXISTS idx_property_constraints_type ON property_constraints(object_type_id);