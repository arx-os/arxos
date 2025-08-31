//! ArxObject implementation - the 13-byte foundation of building intelligence
//!
//! This module implements the complete ArxObject specification v1.0

use core::mem;

/// The core ArxObject structure - exactly 13 bytes
/// 
/// Memory layout (little-endian):
/// - Bytes 0-1: Object ID (unique within building)
/// - Byte 2: Object type (category and subtype)
/// - Bytes 3-4: X coordinate (millimeters)
/// - Bytes 5-6: Y coordinate (millimeters)
/// - Bytes 7-8: Z coordinate (millimeters)
/// - Bytes 9-12: Type-specific properties
#[repr(C, packed)]
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct ArxObject {
    /// Unique identifier within building (0x0001-0xFFFE)
    pub id: u16,
    
    /// Object type (see object_types module)
    pub object_type: u8,
    
    /// X coordinate in millimeters (0-65535mm = 0-65.535m)
    pub x: u16,
    
    /// Y coordinate in millimeters (0-65535mm = 0-65.535m)
    pub y: u16,
    
    /// Z coordinate in millimeters (0-65535mm = 0-65.535m)
    pub z: u16,
    
    /// Type-specific properties (4 bytes)
    /// Encoding depends on object_type
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

    /// Create a new ArxObject with default properties
    pub fn new(id: u16, object_type: u8, x: u16, y: u16, z: u16) -> Self {
        Self {
            id,
            object_type,
            x,
            y,
            z,
            properties: [0; 4],
        }
    }
    
    /// Create ArxObject with properties
    pub fn with_properties(
        id: u16,
        object_type: u8,
        x: u16,
        y: u16,
        z: u16,
        properties: [u8; 4],
    ) -> Self {
        Self {
            id,
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
        // Check ID range
        if self.id == Self::NULL_ID {
            return Err(ValidationError::InvalidId("NULL ID"));
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
        self.id == Self::BROADCAST_ID
    }
    
    /// Calculate CRC8 checksum for validation
    pub fn calculate_crc8(&self) -> u8 {
        let bytes = self.to_bytes();
        crc8(&bytes)
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
    
    // Lighting
    pub const LIGHT: u8 = 0x30;
    
    // Fire Safety
    pub const FIRE_ALARM: u8 = 0x40;
    pub const SMOKE_DETECTOR: u8 = 0x41;
    pub const EMERGENCY_EXIT: u8 = 0x42;
    
    // Generic
    pub const GENERIC: u8 = 0xFF;
    pub const VAV_BOX: u8 = 0x22;
    pub const AIR_HANDLER: u8 = 0x23;
    pub const CHILLER: u8 = 0x24;
    pub const BOILER: u8 = 0x25;
    pub const COOLING_TOWER: u8 = 0x26;
    pub const PUMP: u8 = 0x27;
    pub const FAN: u8 = 0x28;
    
    // Sensors (0x30-0x3F)
    pub const TEMPERATURE_SENSOR: u8 = 0x30;
    pub const MOTION_SENSOR: u8 = 0x31;
    pub const CO2_SENSOR: u8 = 0x32;
    pub const LIGHT_SENSOR: u8 = 0x33;
    pub const PRESSURE_SENSOR: u8 = 0x34;
    pub const HUMIDITY_SENSOR: u8 = 0x35;
    pub const CO2_DETECTOR: u8 = 0x36;  // Renamed to avoid duplicate
    pub const WATER_LEAK_SENSOR: u8 = 0x37;
    pub const VIBRATION_SENSOR: u8 = 0x38;
    pub const SOUND_SENSOR: u8 = 0x39;
    
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
    
    // Plumbing (0x60-0x6F)
    pub const WATER_VALVE: u8 = 0x60;
    pub const WATER_METER: u8 = 0x61;
    pub const WATER_HEATER: u8 = 0x62;
    pub const FAUCET: u8 = 0x63;
    pub const TOILET: u8 = 0x64;
    pub const DRAIN: u8 = 0x65;
    pub const SUMP_PUMP: u8 = 0x66;
    pub const SPRINKLER: u8 = 0x67;
    
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
        
        assert_eq!(obj.x, 10500);
        assert_eq!(obj.y, 8250);
        assert_eq!(obj.z, 3000);
        
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