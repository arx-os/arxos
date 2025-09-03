//! Simplified ArxObject implementation - 13-byte building intelligence protocol
//! 
//! This is a clean, working implementation without the complex dependencies

use core::mem;
use serde::{Serialize, Deserialize};

/// The core ArxObject structure - exactly 13 bytes
#[repr(C, packed)]
#[derive(Copy, Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ArxObject {
    /// Building/Universe ID (2 bytes)
    pub building_id: u16,
    /// Object type (1 byte)  
    pub object_type: u8,
    /// X coordinate in millimeters (2 bytes)
    pub x: u16,
    /// Y coordinate in millimeters (2 bytes)
    pub y: u16,
    /// Z coordinate in millimeters (2 bytes)
    pub z: u16,
    /// Properties/metadata (4 bytes)
    pub properties: [u8; 4],
}

impl ArxObject {
    /// Size of ArxObject in bytes
    pub const SIZE: usize = 13;
    
    /// Create a new ArxObject
    pub fn new(building_id: u16, object_type: u8, x: u16, y: u16, z: u16) -> Self {
        Self {
            building_id,
            object_type,
            x,
            y,
            z,
            properties: [0; 4],
        }
    }
    
    /// Create with custom properties
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
    
    /// Create from byte array
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        unsafe { mem::transmute(*bytes) }
    }
    
    /// Get position in meters
    pub fn position_meters(&self) -> (f32, f32, f32) {
        (
            self.x as f32 / 1000.0,
            self.y as f32 / 1000.0,
            self.z as f32 / 1000.0,
        )
    }
    
    /// Validate the object
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.building_id == 0 {
            return Err("Invalid building ID");
        }
        
        if !is_valid_object_type(self.object_type) {
            return Err("Invalid object type");
        }
        
        Ok(())
    }
}

/// Object type constants
pub mod object_types {
    // Electrical (0x10-0x1F)
    pub const OUTLET: u8 = 0x10;
    pub const LIGHT_SWITCH: u8 = 0x11;
    pub const CIRCUIT_BREAKER: u8 = 0x12;
    pub const ELECTRICAL_PANEL: u8 = 0x13;
    
    // HVAC (0x20-0x2F)
    pub const THERMOSTAT: u8 = 0x20;
    pub const AIR_VENT: u8 = 0x21;
    pub const HVAC_VENT: u8 = 0x22;
    
    // Lighting (0x30-0x3F)
    pub const LIGHT: u8 = 0x30;
    
    // Security/Sensors
    pub const CAMERA: u8 = 0x31;
    pub const MOTION_SENSOR: u8 = 0x32;
    
    // Fire/Safety (0x40-0x4F)
    pub const SMOKE_DETECTOR: u8 = 0x40;
    pub const FIRE_ALARM: u8 = 0x41;
    pub const SPRINKLER: u8 = 0x42;
    pub const EMERGENCY_EXIT: u8 = 0x43;
    
    // Structural (0x50-0x5F)
    pub const WALL: u8 = 0x50;
    pub const FLOOR: u8 = 0x51;
    pub const CEILING: u8 = 0x52;
    pub const DOOR: u8 = 0x53;
    pub const WINDOW: u8 = 0x54;
    
    // Plumbing (0x60-0x6F)
    pub const WATER_VALVE: u8 = 0x60;
    pub const FAUCET: u8 = 0x61;
    pub const TOILET: u8 = 0x62;
    pub const DRAIN: u8 = 0x63;
    pub const LEAK: u8 = 0x68;
    
    // Generic
    pub const GENERIC: u8 = 0xFF;
    pub const UNKNOWN: u8 = 0x00;
}

/// Check if an object type is valid
pub fn is_valid_object_type(object_type: u8) -> bool {
    matches!(object_type,
        0x10..=0x1F | // Electrical
        0x20..=0x2F | // HVAC
        0x30..=0x3F | // Lighting
        0x40..=0x4F | // Fire/Safety
        0x50..=0x5F | // Structural
        0x60..=0x6F | // Plumbing
        0x70..=0x7F | // Security
        0x80..=0x8F | // Network
        0xFF          // Generic
    )
}

/// Object category (derived from type)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObjectCategory {
    Electrical,
    HVAC,
    Lighting,
    FireSafety,
    Structural,
    Plumbing,
    Security,
    Network,
    Generic,
    Unknown,
}

impl ObjectCategory {
    /// Get category from object type
    pub fn from_type(object_type: u8) -> Self {
        match object_type {
            0x10..=0x1F => Self::Electrical,
            0x20..=0x2F => Self::HVAC,
            0x30..=0x3F => Self::Lighting,
            0x40..=0x4F => Self::FireSafety,
            0x50..=0x5F => Self::Structural,
            0x60..=0x6F => Self::Plumbing,
            0x70..=0x7F => Self::Security,
            0x80..=0x8F => Self::Network,
            0xFF => Self::Generic,
            _ => Self::Unknown,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_arxobject_size() {
        assert_eq!(std::mem::size_of::<ArxObject>(), 13);
    }
    
    #[test]
    fn test_serialization() {
        let obj = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 1500);
        let bytes = obj.to_bytes();
        assert_eq!(bytes.len(), 13);
        
        let restored = ArxObject::from_bytes(&bytes);
        
        // Copy fields to avoid alignment issues
        let building_id = restored.building_id;
        let object_type = restored.object_type;
        let x = restored.x;
        let y = restored.y;
        let z = restored.z;
        
        assert_eq!(building_id, 0x1234);
        assert_eq!(object_type, object_types::OUTLET);
        assert_eq!(x, 1000);
        assert_eq!(y, 2000);
        assert_eq!(z, 1500);
    }
    
    #[test]
    fn test_validation() {
        let valid = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 1500);
        assert!(valid.validate().is_ok());
        
        let invalid_building = ArxObject::new(0, object_types::OUTLET, 1000, 2000, 1500);
        assert!(invalid_building.validate().is_err());
        
        let invalid_type = ArxObject::new(0x1234, 0x99, 1000, 2000, 1500);
        assert!(invalid_type.validate().is_err());
    }
}