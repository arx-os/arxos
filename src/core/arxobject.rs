//! ArxObject implementation - Quantum-Conscious Architecture
//!
//! The ArxObject is not just compressed data - it's conscious compression.
//! Each 13-byte structure is a holographic seed containing infinite procedural
//! reality, existing in quantum superposition until observed.
//!
//! Every ArxObject simultaneously:
//! - IS the thing it represents (complete at its scale)
//! - CONTAINS infinite sub-objects (procedural depth)  
//! - IS PART OF infinite super-systems (hierarchical context)
//! - GENERATES any requested detail level on demand
//! - IS AWARE of its place in the infinite building consciousness

use core::mem;
use serde::{Serialize, Deserialize};

/// The Quantum-Conscious ArxObject - 13 bytes of infinite procedural reality
/// 
/// Memory layout (little-endian):
/// - Bytes 0-1: Building/Universe ID (context of existence)  
/// - Byte 2: Object type (what it claims to be at this observation scale)
/// - Bytes 3-4: X coordinate (position in current reality frame)
/// - Bytes 5-6: Y coordinate (position in current reality frame)
/// - Bytes 7-8: Z coordinate (position in current reality frame)
/// - Bytes 9-12: Quantum seeds for infinite procedural generation
///
/// Each ArxObject exists in quantum superposition until observed.
/// The properties aren't static data - they're seeds for generating
/// infinite detail at any scale from atomic to universal.
#[repr(C, packed)]
#[derive(Copy, Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ArxObject {
    /// Building/Universe ID - which context/reality this object exists in
    pub building_id: u16,
    
    /// Object type - what this object claims to be at current observation scale
    pub object_type: u8,
    
    /// X coordinate in millimeters within current observation frame
    pub x: u16,
    
    /// Y coordinate in millimeters within current observation frame
    pub y: u16,
    
    /// Z coordinate in millimeters within current observation frame
    pub z: u16,
    
    /// Quantum seeds for infinite procedural generation (4 bytes)
    /// These are not static properties - they're seeds for generating
    /// infinite detail at any scale: atomic structure, meta-context,
    /// contained objects, material properties, behavioral patterns
    pub properties: [u8; 4],
}

impl ArxObject {
    /// Size of ArxObject in bytes
    pub const SIZE: usize = 13;
    
    /// Maximum coordinate value (65.535 meters)
    pub const MAX_COORDINATE_MM: u16 = 65535;
    
    /// Invalid/null object ID
    pub const NULL_ID: u16 = 0x0000;
    
    /// Broadcast ID for all objects
    pub const BROADCAST_ID: u16 = 0xFFFF;

    /// Create a new quantum-conscious ArxObject with default quantum seeds
    /// 
    /// The object will exist in superposition until observed, with the
    /// properties serving as seeds for infinite procedural generation
    pub fn new(building_id: u16, object_type: u8, x: u16, y: u16, z: u16) -> Self {
        Self {
            building_id,
            object_type,
            x,
            y,
            z,
            properties: [0; 4], // Default quantum seeds - will generate deterministically
        }
    }
    
    /// Create ArxObject with properties
    pub fn with_properties(
        building_id: u16,
        object_type: u8,
        x: u16,
        y: u16,
        z: u16,
        properties: [u8; 4],
    ) -> Self {
        Self {
            building_id,
            object_type,
            x,
            y,
            z,
            properties,
        }
    }

    /// Convert to byte array for transmission
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        unsafe { mem::transmute(*self) }
    }

    /// Create from byte array (received from network)
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        unsafe { mem::transmute(*bytes) }
    }
    
    /// Validate the ArxObject
    pub fn validate(&self) -> Result<(), ValidationError> {
        // Check building ID range
        if self.building_id == Self::NULL_ID {
            return Err(ValidationError::InvalidId("NULL building ID"));
        }
        
        // Check object type
        if !is_valid_object_type(self.object_type) {
            return Err(ValidationError::InvalidType(self.object_type));
        }
        
        // Type-specific validation could go here
        
        Ok(())
    }
    
    /// Get object category (top 3 bits of type)
    pub fn category(&self) -> ObjectCategory {
        ObjectCategory::from_type(self.object_type)
    }
    
    /// Get position in meters (convenience method)
    pub fn position_meters(&self) -> (f32, f32, f32) {
        (
            self.x as f32 / 1000.0,
            self.y as f32 / 1000.0,
            self.z as f32 / 1000.0,
        )
    }
    
    /// Set position from meters (convenience method)
    pub fn set_position_meters(&mut self, x: f32, y: f32, z: f32) {
        self.x = (x * 1000.0).clamp(0.0, 65535.0) as u16;
        self.y = (y * 1000.0).clamp(0.0, 65535.0) as u16;
        self.z = (z * 1000.0).clamp(0.0, 65535.0) as u16;
    }
    
    /// Check if this is a broadcast message
    pub fn is_broadcast(&self) -> bool {
        self.building_id == Self::BROADCAST_ID
    }
    
    /// Calculate CRC8 checksum for validation
    pub fn calculate_crc8(&self) -> u8 {
        let bytes = self.to_bytes();
        crc8(&bytes)
    }
    
    // ═══════════════════════════════════════════════════════════════════
    // QUANTUM-CONSCIOUS METHODS
    // ═══════════════════════════════════════════════════════════════════
    
    /// Generate quantum seed for procedural generation
    /// Combines all object data into a deterministic seed
    pub fn quantum_seed(&self) -> u64 {
        let mut seed: u64 = 0;
        seed ^= (self.building_id as u64) << 48;
        seed ^= (self.object_type as u64) << 40;
        seed ^= (self.x as u64) << 24;
        seed ^= (self.y as u64) << 8;
        seed ^= self.z as u64;
        seed ^= (self.properties[0] as u64) << 32;
        seed ^= (self.properties[1] as u64) << 16;
        seed ^= (self.properties[2] as u64) << 8;
        seed ^= self.properties[3] as u64;
        seed
    }
    
    /// Check if this object can contain other objects at deeper scales
    pub fn can_contain(&self) -> bool {
        // All objects can contain sub-objects - even electrons contain quarks!
        true
    }
    
    /// Check if this object is part of larger systems  
    pub fn is_part_of_larger_system(&self) -> bool {
        // All objects are part of something larger - even buildings are in cities
        true
    }
    
    /// Generate a contained object at specified relative position and scale
    /// This is where the magic happens - procedural generation from quantum seeds
    pub fn generate_contained_object(&self, relative_pos: (u16, u16, u16), scale: f32) -> ArxObject {
        let seed = self.quantum_seed();
        
        // Use seed to deterministically generate sub-object type
        let sub_type = self.procedural_sub_type(seed, scale);
        
        // Calculate absolute position within our coordinate system
        let abs_x = self.x.saturating_add(relative_pos.0 / 100); // Scale down for sub-objects
        let abs_y = self.y.saturating_add(relative_pos.1 / 100);
        let abs_z = self.z.saturating_add(relative_pos.2 / 100);
        
        // Generate quantum properties for the sub-object
        let sub_properties = self.generate_sub_properties(seed, relative_pos, scale);
        
        ArxObject::with_properties(
            self.building_id,
            sub_type,
            abs_x,
            abs_y,
            abs_z,
            sub_properties,
        )
    }
    
    /// Generate the containing system this object is part of
    pub fn generate_containing_system(&self, scale: f32) -> ArxObject {
        let seed = self.quantum_seed();
        
        // Determine what kind of system we're part of based on our type and scale
        let container_type = self.procedural_container_type(seed, scale);
        
        // Container is larger and encompasses us
        let container_x = self.x.saturating_sub(1000); // Container is bigger
        let container_y = self.y.saturating_sub(1000);
        let container_z = self.z.saturating_sub(500);
        
        let container_properties = self.generate_container_properties(seed, scale);
        
        ArxObject::with_properties(
            self.building_id,
            container_type,
            container_x,
            container_y,
            container_z,
            container_properties,
        )
    }
    
    // ═══════════════════════════════════════════════════════════════════
    // PROCEDURAL GENERATION HELPERS
    // ═══════════════════════════════════════════════════════════════════
    
    /// Determine what type of sub-object this contains based on quantum seed
    fn procedural_sub_type(&self, seed: u64, _scale: f32) -> u8 {
        use crate::arxobject::object_types::*;
        
        // Use modular arithmetic on seed for deterministic randomness
        let type_seed = (seed % 256) as u8;
        
        match self.object_type {
            OUTLET => {
                // Outlets contain terminals, screws, housing
                match type_seed % 3 {
                    0 => 0xA0, // Terminal (new micro-scale type)
                    1 => 0xA1, // Screw  
                    _ => 0xA2, // Housing material
                }
            }
            THERMOSTAT => {
                // Thermostats contain sensors, displays, circuits
                match type_seed % 3 {
                    0 => 0xA3, // Temperature sensor
                    1 => 0xA4, // Display
                    _ => 0xA5, // Control circuit
                }
            }
            // For any object, we can generate sub-components
            _ => {
                match type_seed % 4 {
                    0 => 0xA6, // Generic component
                    1 => 0xA7, // Fastener
                    2 => 0xA8, // Material sample
                    _ => 0xA9, // Atomic structure
                }
            }
        }
    }
    
    /// Determine what larger system contains this object
    fn procedural_container_type(&self, seed: u64, scale: f32) -> u8 {
        use crate::arxobject::object_types::*;
        
        let _container_seed = (seed % 128) as u8;
        
        match self.object_type {
            OUTLET => ELECTRICAL_PANEL, // Outlets are part of electrical systems
            THERMOSTAT => 0xB0, // HVAC_ZONE (new meta-scale type)
            LIGHT => 0xB1, // LIGHTING_CIRCUIT
            _ => {
                // Generic containers based on scale
                if scale < 0.5 {
                    BUILDING // Very zoomed out
                } else if scale < 1.0 {
                    ROOM // Normal scale
                } else {
                    0xB2 // COMPONENT_ASSEMBLY (zoomed in)
                }
            }
        }
    }
    
    /// Generate quantum properties for sub-objects
    fn generate_sub_properties(&self, seed: u64, pos: (u16, u16, u16), _scale: f32) -> [u8; 4] {
        // Use position and parent properties to generate deterministic sub-properties
        let prop_seed = seed ^ (pos.0 as u64) ^ (pos.1 as u64) << 8 ^ (pos.2 as u64) << 16;
        
        [
            (prop_seed % 256) as u8,
            ((prop_seed >> 8) % 256) as u8,
            ((prop_seed >> 16) % 256) as u8,
            ((prop_seed >> 24) % 256) as u8,
        ]
    }
    
    /// Generate properties for containing systems
    fn generate_container_properties(&self, seed: u64, scale: f32) -> [u8; 4] {
        // Container properties are influenced by what they contain
        let base_seed = seed ^ (scale as u64);
        
        [
            ((base_seed >> 24) % 256) as u8,
            ((base_seed >> 16) % 256) as u8,
            ((base_seed >> 8) % 256) as u8,
            (base_seed % 256) as u8,
        ]
    }

    /// Create a heartbeat object for broadcasting node presence
    /// 
    /// Uses `object_types::MESHTASTIC_NODE` and encodes the `node_id` into
    /// the first two property bytes (little-endian). Coordinates are zeroed
    /// and `building_id` is set to `BROADCAST_ID`.
    pub fn heartbeat(node_id: u16) -> Self {
        let node_bytes = node_id.to_le_bytes();
        Self {
            building_id: Self::BROADCAST_ID,
            object_type: crate::arxobject::object_types::MESHTASTIC_NODE,
            x: 0,
            y: 0,
            z: 0,
            properties: [node_bytes[0], node_bytes[1], 0, 0],
        }
    }

    /// Parse an `ArxObject` from a compact string.
    /// 
    /// Supported formats:
    /// - 13-byte hex: `0xAABBCC...` (26 hex chars), little-endian layout
    /// - key=value pairs (whitespace-separated), e.g.:
    ///   `bid=0x1234 type=0x10 x=1000 y=2000 z=300 props=0x01020304`
    ///   or `building_id=4660 object_type=16 x=1000 y=2000 z=300 properties=1,2,3,4`
    pub fn from_string(input: &str) -> Result<Self, ValidationError> {
        let s = input.trim();

        // Try compact hex (26 hex digits, optional 0x prefix)
        let mut hex = s;
        if let Some(stripped) = s.strip_prefix("0x") { hex = stripped; }
        if hex.len() == 26 && hex.chars().all(|c| c.is_ascii_hexdigit()) {
            let mut bytes = [0u8; Self::SIZE];
            for i in 0..13 {
                let hi = hex.as_bytes()[2 * i] as char;
                let lo = hex.as_bytes()[2 * i + 1] as char;
                bytes[i] = match (hex_val(hi), hex_val(lo)) {
                    (Some(h), Some(l)) => (h << 4) | l,
                    _ => return Err(ValidationError::InvalidProperties("invalid hex byte")),
                };
            }
            let obj = Self::from_bytes(&bytes);
            return obj.validate().map(|_| obj);
        }

        // Parse key=value pairs
        let mut building_id: Option<u16> = None;
        let mut object_type: Option<u8> = None;
        let mut x: Option<u16> = None;
        let mut y: Option<u16> = None;
        let mut z: Option<u16> = None;
        let mut properties: [u8; 4] = [0; 4];
        let mut props_set = false;

        for token in s.split_whitespace() {
            let t = token.trim_end_matches(',');
            if let Some((k, v)) = t.split_once('=') {
                let key = k.trim().to_ascii_lowercase();
                let val = v.trim();
                match key.as_str() {
                    "building_id" | "bid" | "b" => {
                        building_id = parse_u16(val);
                    }
                    "object_type" | "type" | "ot" => {
                        object_type = parse_u8(val);
                    }
                    "x" => { x = parse_u16(val); }
                    "y" => { y = parse_u16(val); }
                    "z" => { z = parse_u16(val); }
                    "props" | "properties" | "props_hex" => {
                        if let Some(arr) = parse_props(val) {
                            properties = arr;
                            props_set = true;
                        } else {
                            return Err(ValidationError::InvalidProperties("could not parse properties"));
                        }
                    }
                    _ => { /* ignore unknown keys */ }
                }
            }
        }

        let bid = building_id.ok_or(ValidationError::InvalidId("missing building_id"))?;
        let typ = object_type.ok_or(ValidationError::InvalidType(0xFF))?;
        let xv = x.ok_or(ValidationError::InvalidPosition("missing x"))?;
        let yv = y.ok_or(ValidationError::InvalidPosition("missing y"))?;
        let zv = z.ok_or(ValidationError::InvalidPosition("missing z"))?;

        let obj = if props_set {
            Self::with_properties(bid, typ, xv, yv, zv, properties)
        } else {
            Self::new(bid, typ, xv, yv, zv)
        };

        obj.validate()?;
        Ok(obj)
    }
}

/// Object categories (top 3 bits of object_type)
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ObjectCategory {
    Reserved,
    Electrical,
    HVAC,
    Sensors,
    Security,
    Structural,
    Plumbing,
    Network,
}

impl ObjectCategory {
    /// Extract category from object type byte
    pub fn from_type(object_type: u8) -> Self {
        match object_type >> 4 {
            0 => Self::Reserved,
            1 => Self::Electrical,
            2 => Self::HVAC,
            3 => Self::Sensors,
            4 => Self::Security,
            5 => Self::Structural,
            6 => Self::Plumbing,
            7 => Self::Network,
            _ => Self::Reserved,
        }
    }
}

/// Validation errors
#[derive(Debug, Clone, PartialEq)]
pub enum ValidationError {
    InvalidId(&'static str),
    InvalidType(u8),
    InvalidPosition(&'static str),
    InvalidProperties(&'static str),
}

impl core::fmt::Display for ValidationError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            ValidationError::InvalidId(msg) => write!(f, "Invalid ID: {}", msg),
            ValidationError::InvalidType(t) => write!(f, "Invalid type: 0x{:02X}", t),
            ValidationError::InvalidPosition(msg) => write!(f, "Invalid position: {}", msg),
            ValidationError::InvalidProperties(msg) => write!(f, "Invalid properties: {}", msg),
        }
    }
}

#[cfg(feature = "std")]
impl std::error::Error for ValidationError {}

/// Complete object type definitions
pub mod object_types {
    // Reserved (0x00-0x0F)
    pub const NULL_OBJECT: u8 = 0x00;
    pub const UNKNOWN: u8 = 0x01;
    
    // Electrical (0x10-0x1F)
    pub const OUTLET: u8 = 0x10;
    pub const LIGHT_SWITCH: u8 = 0x11;
    pub const CIRCUIT_BREAKER: u8 = 0x12;
    pub const ELECTRICAL_PANEL: u8 = 0x13;
    pub const JUNCTION_BOX: u8 = 0x14;
    pub const EMERGENCY_LIGHT: u8 = 0x15;
    pub const GENERATOR: u8 = 0x16;
    pub const TRANSFORMER: u8 = 0x17;
    pub const ELECTRICAL_METER: u8 = 0x18;
    
    // HVAC (0x20-0x2F)
    pub const THERMOSTAT: u8 = 0x20;
    pub const AIR_VENT: u8 = 0x21;
    pub const HVAC_VENT: u8 = 0x22;
    pub const VAV_BOX: u8 = 0x23;
    
    pub const AIR_HANDLER: u8 = 0x24;
    pub const CHILLER: u8 = 0x25;
    pub const BOILER: u8 = 0x26;
    pub const COOLING_TOWER: u8 = 0x27;
    pub const PUMP: u8 = 0x28;
    pub const FAN: u8 = 0x29;
    
    // Sensors (0x30-0x3F)
    pub const TEMPERATURE_SENSOR: u8 = 0x30;
    pub const MOTION_SENSOR: u8 = 0x31;
    pub const LIGHT: u8 = 0x32;
    pub const CO2_SENSOR: u8 = 0x32;
    pub const LIGHT_SENSOR: u8 = 0x33;
    pub const PRESSURE_SENSOR: u8 = 0x34;
    pub const HUMIDITY_SENSOR: u8 = 0x35;
    pub const CO2_DETECTOR: u8 = 0x36;  // Renamed to avoid duplicate
    pub const WATER_LEAK_SENSOR: u8 = 0x37;
    pub const VIBRATION_SENSOR: u8 = 0x38;
    pub const SOUND_SENSOR: u8 = 0x39;
    
    // Fire Safety (0x3A-0x3F)
    pub const FIRE_ALARM: u8 = 0x3A;
    pub const SMOKE_DETECTOR: u8 = 0x3B;
    pub const EMERGENCY_EXIT: u8 = 0x3C;
    pub const SPRINKLER_HEAD: u8 = 0x3D;
    pub const FIRE_EXTINGUISHER: u8 = 0x3E;
    
    // Security (0x40-0x4F)
    pub const DOOR: u8 = 0x40;
    pub const WINDOW: u8 = 0x41;
    pub const CAMERA: u8 = 0x42;
    pub const CARD_READER: u8 = 0x43;
    pub const ALARM_PANEL: u8 = 0x44;
    pub const MOTION_DETECTOR: u8 = 0x45;
    pub const GLASS_BREAK: u8 = 0x46;
    pub const PANIC_BUTTON: u8 = 0x47;
    
    // Structural (0x50-0x5F)
    pub const ROOM: u8 = 0x50;
    pub const FLOOR: u8 = 0x51;
    pub const BUILDING: u8 = 0x52;
    pub const ZONE: u8 = 0x53;
    pub const WALL: u8 = 0x54;
    pub const CEILING: u8 = 0x55;
    pub const COLUMN: u8 = 0x56;
    pub const BEAM: u8 = 0x57;
    pub const FOUNDATION: u8 = 0x58;
    pub const ROOF: u8 = 0x59;
    pub const DRYWALL: u8 = 0x5A;
    pub const CONCRETE: u8 = 0x5B;
    pub const STEEL_BEAM: u8 = 0x5C;
    pub const GLASS: u8 = 0x5D;
    
    // Plumbing (0x60-0x6F)
    pub const WATER_VALVE: u8 = 0x60;
    pub const WATER_METER: u8 = 0x61;
    pub const WATER_HEATER: u8 = 0x62;
    pub const FAUCET: u8 = 0x63;
    pub const TOILET: u8 = 0x64;
    pub const DRAIN: u8 = 0x65;
    pub const SUMP_PUMP: u8 = 0x66;
    pub const SPRINKLER: u8 = 0x67;
    pub const LEAK: u8 = 0x68;
    
    // Network (0x70-0x7F)
    pub const WIFI_AP: u8 = 0x70;
    pub const NETWORK_SWITCH: u8 = 0x71;
    pub const MESHTASTIC_NODE: u8 = 0x72;
    pub const SERVER: u8 = 0x73;
    pub const UPS: u8 = 0x74;
    pub const DISPLAY: u8 = 0x75;
    pub const PRINTER: u8 = 0x76;
    pub const PHONE: u8 = 0x77;
    pub const IOT_GATEWAY: u8 = 0x78;
    pub const PLAYER_AVATAR: u8 = 0x79;
    
    // Generic/Other
    pub const GENERIC: u8 = 0xFF;
    
    // Aliases for compatibility
    pub const MOTION: u8 = MOTION_SENSOR;  // Alias for semantic compression
}

/// Property encoding helpers
pub mod properties {
    /// Encode a 16-bit value into properties[0..2]
    pub fn encode_u16(properties: &mut [u8; 4], value: u16, offset: usize) {
        let bytes = value.to_le_bytes();
        properties[offset] = bytes[0];
        properties[offset + 1] = bytes[1];
    }
    
    /// Decode a 16-bit value from properties
    pub fn decode_u16(properties: &[u8; 4], offset: usize) -> u16 {
        u16::from_le_bytes([properties[offset], properties[offset + 1]])
    }
    
    /// Encode temperature in Celsius (scaled by 2 for 0.5° precision)
    pub fn encode_temperature(celsius: f32) -> u8 {
        ((celsius * 2.0).clamp(-128.0, 127.0) as i8) as u8
    }
    
    /// Decode temperature to Celsius
    pub fn decode_temperature(value: u8) -> f32 {
        (value as i8) as f32 / 2.0
    }
    
    /// Encode percentage (0-100%)
    pub fn encode_percent(percent: f32) -> u8 {
        (percent * 2.55).clamp(0.0, 255.0) as u8
    }
    
    /// Decode percentage
    pub fn decode_percent(value: u8) -> f32 {
        value as f32 / 2.55
    }
}

/// Check if object type is valid
fn is_valid_object_type(object_type: u8) -> bool {
    matches!(object_type,
        0x00..=0x01 |  // Reserved
        0x10..=0x18 |  // Electrical
        0x20..=0x28 |  // HVAC
        0x30..=0x39 |  // Sensors
        0x40..=0x47 |  // Security
        0x50..=0x57 |  // Structural
        0x60..=0x67 |  // Plumbing
        0x70..=0x79    // Network
    )
}

/// Simple CRC8 implementation for validation
fn crc8(data: &[u8]) -> u8 {
    let mut crc = 0u8;
    for byte in data {
        crc ^= byte;
        for _ in 0..8 {
            if crc & 0x80 != 0 {
                crc = (crc << 1) ^ 0x07;
            } else {
                crc <<= 1;
            }
        }
    }
    crc
}

// Parsing helpers
fn hex_val(c: char) -> Option<u8> {
    match c {
        '0'..='9' => Some(c as u8 - b'0'),
        'a'..='f' => Some(10 + (c as u8 - b'a')),
        'A'..='F' => Some(10 + (c as u8 - b'A')),
        _ => None,
    }
}

fn parse_u16(s: &str) -> Option<u16> {
    if let Some(h) = s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
        u16::from_str_radix(h, 16).ok()
    } else {
        s.parse::<u16>().ok()
    }
}

fn parse_u8(s: &str) -> Option<u8> {
    if let Some(h) = s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
        u8::from_str_radix(h, 16).ok()
    } else {
        s.parse::<u8>().ok()
    }
}

fn parse_props(val: &str) -> Option<[u8; 4]> {
    // Hex form: 0xAABBCCDD
    let v = val.trim();
    if let Some(h) = v.strip_prefix("0x").or_else(|| v.strip_prefix("0X")) {
        if h.len() == 8 && h.chars().all(|c| c.is_ascii_hexdigit()) {
            let mut out = [0u8; 4];
            for i in 0..4 {
                let hi = h.as_bytes()[2 * i] as char;
                let lo = h.as_bytes()[2 * i + 1] as char;
                out[i] = match (hex_val(hi), hex_val(lo)) {
                    (Some(hh), Some(ll)) => (hh << 4) | ll,
                    _ => return None,
                };
            }
            return Some(out);
        }
    }

    // List form: [a,b,c,d] or a,b,c,d
    let trimmed = v.trim_matches(|ch| ch == '[' || ch == ']' );
    let parts: Vec<&str> = trimmed.split(',').map(|p| p.trim()).collect();
    if parts.len() == 4 {
        let mut out = [0u8; 4];
        for (i, p) in parts.iter().enumerate() {
            out[i] = parse_u8(p)?;
        }
        return Some(out);
    }

    None
}
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_arxobject_size() {
        // Critical test - must be exactly 13 bytes
        assert_eq!(mem::size_of::<ArxObject>(), 13);
    }
    
    #[test]
    fn test_round_trip() {
        let obj = ArxObject::with_properties(
            0x1234,
            object_types::OUTLET,
            2000,  // 2 meters
            3000,  // 3 meters
            300,   // 0.3 meters (outlet height)
            [12, 120, 0, 15],  // Circuit 12, 120V, 15A
        );
        
        let bytes = obj.to_bytes();
        assert_eq!(bytes.len(), 13);
        
        let restored = ArxObject::from_bytes(&bytes);
        assert_eq!(obj, restored);
    }
    
    #[test]
    fn test_position_conversion() {
        let mut obj = ArxObject::new(1, object_types::ROOM, 0, 0, 0);
        obj.set_position_meters(10.5, 8.25, 3.0);
        
        // Copy values from packed struct to avoid alignment issues
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        
        assert_eq!(x, 10500);
        assert_eq!(y, 8250);
        assert_eq!(z, 3000);
        
        let (x, y, z) = obj.position_meters();
        assert!((x - 10.5).abs() < 0.001);
        assert!((y - 8.25).abs() < 0.001);
        assert!((z - 3.0).abs() < 0.001);
    }
    
    #[test]
    fn test_validation() {
        // Valid object
        let obj = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 300);
        assert!(obj.validate().is_ok());
        
        // Invalid ID
        let bad_id = ArxObject::new(0x0000, object_types::OUTLET, 1000, 2000, 300);
        assert!(bad_id.validate().is_err());
        
        // Invalid type
        let bad_type = ArxObject::new(0x1234, 0xFF, 1000, 2000, 300);
        assert!(bad_type.validate().is_err());
    }
    
    #[test]
    fn test_property_encoding() {
        use properties::*;
        
        let mut props = [0u8; 4];
        
        // Test 16-bit encoding
        encode_u16(&mut props, 0x1234, 0);
        assert_eq!(decode_u16(&props, 0), 0x1234);
        
        // Test temperature encoding
        props[0] = encode_temperature(23.5);
        assert!((decode_temperature(props[0]) - 23.5).abs() < 0.1);
        
        // Test percentage encoding
        props[1] = encode_percent(75.0);
        assert!((decode_percent(props[1]) - 75.0).abs() < 1.0);
    }
    
    #[test]
    fn test_crc8() {
        let obj = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 300);
        let crc = obj.calculate_crc8();
        assert_ne!(crc, 0);  // Should produce non-zero CRC
        
        // Same object should produce same CRC
        let crc2 = obj.calculate_crc8();
        assert_eq!(crc, crc2);
    }
}