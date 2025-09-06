//! ArxObject - The Fractal Reality Engine for Terminal Worlds
//!
//! The ArxObject is a 13-byte structure that acts as DNA for infinite procedural
//! generation. Like a fractal, each object contains infinite detail when observed
//! at different scales, from molecular to building-wide systems.
//!
//! In our terminal open world, every ArxObject can:
//! - Generate infinite sub-objects when you zoom IN (screws inside outlets)
//! - Reveal parent systems when you zoom OUT (electrical panels, buildings)
//! - Understand its relationships and dependencies in the building
//! - Procedurally generate any level of detail on demand
//! - Compress to exactly 13 bytes for RF mesh transmission

use core::mem;
use serde::{Serialize, Deserialize};
use thiserror::Error;

/// The ArxObject - 13 bytes of fractal building intelligence
/// 
/// Memory layout (little-endian):
/// - Bytes 0-1: Building/Universe ID (which realm this object exists in)
/// - Byte 2: Object type (what it appears to be at current scale)
/// - Bytes 3-4: X coordinate in millimeters (signed for relative positioning)
/// - Bytes 5-6: Y coordinate in millimeters (signed for relative positioning)
/// - Bytes 7-8: Z coordinate in millimeters (signed for relative positioning)
/// - Bytes 9-12: Fractal seed for infinite procedural generation
#[repr(C, packed)]
#[derive(Copy, Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ArxObject {
    /// Building/Universe ID - which realm/context this object exists in
    pub building_id: u16,
    
    /// Object type - what this object appears to be at current observation scale
    pub object_type: u8,
    
    /// X coordinate in millimeters (signed for local origins)
    pub x: i16,
    
    /// Y coordinate in millimeters (signed for local origins)
    pub y: i16,
    
    /// Z coordinate in millimeters (signed for local origins)
    pub z: i16,
    
    /// Fractal seed - 4 bytes that generate infinite procedural detail
    /// This is the DNA that deterministically generates:
    /// - Sub-components when zooming in
    /// - Material properties
    /// - System relationships
    /// - Behavioral patterns
    pub properties: [u8; 4],
}

impl ArxObject {
    /// Size of ArxObject in bytes
    pub const SIZE: usize = 13;
    
    /// Coordinate range in millimeters (±32,767 mm ≈ ±32.767 m)
    pub const MIN_COORDINATE_MM: i16 = i16::MIN;
    pub const MAX_COORDINATE_MM: i16 = i16::MAX;
    
    /// Invalid/null object ID
    pub const NULL_ID: u16 = 0x0000;
    
    /// Broadcast ID for all objects
    pub const BROADCAST_ID: u16 = 0xFFFF;

    /// Create a new ArxObject with default fractal seed
    pub fn new(building_id: u16, object_type: u8, x: i16, y: i16, z: i16) -> Self {
        let mut obj = Self {
            building_id,
            object_type,
            x,
            y,
            z,
            properties: [0; 4],
        };
        // Initialize fractal seed based on position and type
        obj.properties = obj.generate_initial_seed();
        obj
    }
    
    /// Create ArxObject with explicit properties
    pub fn with_properties(
        building_id: u16,
        object_type: u8,
        x: i16,
        y: i16,
        z: i16,
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
    
    /// Convert to byte array for network transmission
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        unsafe { mem::transmute(*self) }
    }
    
    /// Create from byte array received over network
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        unsafe { mem::transmute(*bytes) }
    }
    
    /// Get position in meters (for human-readable display)
    pub fn position_meters(&self) -> (f32, f32, f32) {
        (
            self.x as f32 / 1000.0,
            self.y as f32 / 1000.0,
            self.z as f32 / 1000.0,
        )
    }
    
    /// Validate the object's data integrity
    pub fn validate(&self) -> Result<(), ValidationError> {
        if self.building_id == Self::NULL_ID {
            return Err(ValidationError::InvalidBuildingId);
        }
        
        if !is_valid_object_type(self.object_type) {
            return Err(ValidationError::InvalidObjectType(self.object_type));
        }
        
        Ok(())
    }
    
    // ═══════════════════════════════════════════════════════════════════
    // FRACTAL GENERATION ENGINE
    // ═══════════════════════════════════════════════════════════════════
    
    /// Generate fractal seed for procedural generation
    pub fn fractal_seed(&self) -> u64 {
        let mut seed: u64 = 0;
        seed ^= (self.building_id as u64) << 48;
        seed ^= (self.object_type as u64) << 40;
        seed ^= ((self.x as u32) as u64) << 24;
        seed ^= ((self.y as u32) as u64) << 8;
        seed ^= (self.z as u32) as u64;
        seed ^= (self.properties[0] as u64) << 32;
        seed ^= (self.properties[1] as u64) << 16;
        seed ^= (self.properties[2] as u64) << 8;
        seed ^= self.properties[3] as u64;
        seed
    }
    
    /// Generate initial seed based on object's identity
    fn generate_initial_seed(&self) -> [u8; 4] {
        let seed = self.fractal_seed();
        [
            (seed >> 24) as u8,
            (seed >> 16) as u8,
            (seed >> 8) as u8,
            seed as u8,
        ]
    }
    
    /// Generate a contained object at specified relative position and scale
    /// This is where the fractal magic happens - infinite detail on demand
    pub fn generate_contained_object(&self, relative_pos: (i16, i16, i16), scale: f32) -> ArxObject {
        let seed = self.fractal_seed();
        
        // Determine sub-object type based on parent and scale
        let sub_type = self.procedural_sub_type(seed, scale);
        
        // Calculate absolute position
        let abs_x = self.x.saturating_add(relative_pos.0);
        let abs_y = self.y.saturating_add(relative_pos.1);
        let abs_z = self.z.saturating_add(relative_pos.2);
        
        // Generate fractal properties for the sub-object
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
    
    /// Generate the containing system this object belongs to
    pub fn generate_containing_system(&self, scale: f32) -> ArxObject {
        let seed = self.fractal_seed();
        
        // Determine parent system type
        let container_type = self.procedural_container_type(seed, scale);
        
        // Container encompasses this object
        let container_x = (self.x / 1000) * 1000; // Snap to grid
        let container_y = (self.y / 1000) * 1000;
        let container_z = (self.z / 500) * 500;
        
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
    
    /// Determine sub-object type based on fractal seed
    fn procedural_sub_type(&self, seed: u64, scale: f32) -> u8 {
        use object_types::*;
        
        let type_seed = (seed % 256) as u8;
        
        // At very zoomed in scales, everything breaks down to components
        if scale > 10.0 {
            return match type_seed % 4 {
                0 => COMPONENT_SCREW,
                1 => COMPONENT_WIRE,
                2 => COMPONENT_MATERIAL,
                _ => COMPONENT_CONNECTOR,
            };
        }
        
        // Otherwise generate based on parent type
        match self.object_type {
            OUTLET => match type_seed % 3 {
                0 => COMPONENT_TERMINAL,
                1 => COMPONENT_SCREW,
                _ => COMPONENT_HOUSING,
            },
            ELECTRICAL_PANEL => match type_seed % 4 {
                0 => CIRCUIT_BREAKER,
                1 => COMPONENT_WIRE,
                2 => COMPONENT_TERMINAL,
                _ => COMPONENT_LABEL,
            },
            THERMOSTAT => match type_seed % 3 {
                0 => COMPONENT_SENSOR,
                1 => COMPONENT_DISPLAY,
                _ => COMPONENT_CIRCUIT,
            },
            _ => GENERIC_COMPONENT,
        }
    }
    
    /// Determine containing system type
    fn procedural_container_type(&self, _seed: u64, scale: f32) -> u8 {
        use object_types::*;
        
        match self.object_type {
            OUTLET | LIGHT_SWITCH => ELECTRICAL_PANEL,
            CIRCUIT_BREAKER => ELECTRICAL_ROOM,
            THERMOSTAT | HVAC_VENT => HVAC_SYSTEM,
            LIGHT => LIGHTING_CIRCUIT,
            _ => {
                if scale < 0.1 {
                    BUILDING
                } else if scale < 1.0 {
                    ROOM
                } else {
                    SYSTEM_ASSEMBLY
                }
            }
        }
    }
    
    /// Generate fractal properties for sub-objects
    fn generate_sub_properties(&self, seed: u64, pos: (i16, i16, i16), _scale: f32) -> [u8; 4] {
        let prop_seed = seed ^ (pos.0 as u64) ^ ((pos.1 as u64) << 16) ^ ((pos.2 as u64) << 32);
        [
            (prop_seed % 256) as u8,
            ((prop_seed >> 8) % 256) as u8,
            ((prop_seed >> 16) % 256) as u8,
            ((prop_seed >> 24) % 256) as u8,
        ]
    }
    
    /// Generate properties for containing systems
    fn generate_container_properties(&self, seed: u64, scale: f32) -> [u8; 4] {
        let base_seed = seed ^ ((scale * 1000.0) as u64);
        [
            ((base_seed >> 24) % 256) as u8,
            ((base_seed >> 16) % 256) as u8,
            ((base_seed >> 8) % 256) as u8,
            (base_seed % 256) as u8,
        ]
    }
    
    // ═══════════════════════════════════════════════════════════════════
    // SYSTEM UNDERSTANDING
    // ═══════════════════════════════════════════════════════════════════
    
    /// Get the category this object belongs to
    pub fn category(&self) -> ObjectCategory {
        ObjectCategory::from_type(self.object_type)
    }
    
    /// Check if this object requires electrical connection
    pub fn requires_electrical(&self) -> bool {
        matches!(self.category(), 
            ObjectCategory::Electrical | 
            ObjectCategory::Lighting |
            ObjectCategory::HVAC
        )
    }
    
    /// Check if this object is structural
    pub fn is_structural(&self) -> bool {
        matches!(self.category(), ObjectCategory::Structural)
    }
    
    /// Generate implied properties based on object type
    pub fn implied_properties(&self) -> ImpliedProperties {
        ImpliedProperties::from_object(self)
    }
}

/// Object type constants organized by category
pub mod object_types {
    // Electrical (0x10-0x1F)
    pub const OUTLET: u8 = 0x10;
    pub const LIGHT_SWITCH: u8 = 0x11;
    pub const CIRCUIT_BREAKER: u8 = 0x12;
    pub const ELECTRICAL_PANEL: u8 = 0x13;
    pub const JUNCTION_BOX: u8 = 0x14;
    pub const ELECTRICAL_ROOM: u8 = 0x15;
    
    // HVAC (0x20-0x2F)
    pub const THERMOSTAT: u8 = 0x20;
    pub const HVAC_VENT: u8 = 0x21;
    pub const AIR_VENT: u8 = 0x21; // Alias for compatibility
    pub const AIR_HANDLER: u8 = 0x22;
    pub const HVAC_SYSTEM: u8 = 0x23;
    
    // Lighting (0x30-0x3F)
    pub const LIGHT: u8 = 0x30;
    pub const EMERGENCY_LIGHT: u8 = 0x31;
    pub const LIGHTING_CIRCUIT: u8 = 0x32;
    
    // Security/Sensors (0x40-0x4F)
    pub const CAMERA: u8 = 0x40;
    pub const MOTION_SENSOR: u8 = 0x41;
    pub const MOTION: u8 = 0x41; // Alias for compatibility
    pub const DOOR_SENSOR: u8 = 0x42;
    pub const SMOKE_DETECTOR: u8 = 0x43;
    pub const FIRE_ALARM: u8 = 0x44;
    pub const SPRINKLER: u8 = 0x45;
    
    // Structural (0x50-0x5F)
    pub const WALL: u8 = 0x50;
    pub const FLOOR: u8 = 0x51;
    pub const CEILING: u8 = 0x52;
    pub const DOOR: u8 = 0x53;
    pub const WINDOW: u8 = 0x54;
    pub const COLUMN: u8 = 0x55;
    pub const BEAM: u8 = 0x56;
    pub const STAIRS: u8 = 0x57;
    pub const ROOM: u8 = 0x58;
    pub const BUILDING: u8 = 0x59;
    
    // Plumbing (0x60-0x6F)
    pub const WATER_VALVE: u8 = 0x60;
    pub const FAUCET: u8 = 0x61;
    pub const TOILET: u8 = 0x62;
    pub const DRAIN: u8 = 0x63;
    pub const WATER_HEATER: u8 = 0x64;
    pub const PIPE: u8 = 0x65;
    pub const LEAK: u8 = 0x66;
    
    // Components (0x70-0x7F) - Sub-object types
    pub const COMPONENT_SCREW: u8 = 0x70;
    pub const COMPONENT_WIRE: u8 = 0x71;
    pub const COMPONENT_TERMINAL: u8 = 0x72;
    pub const COMPONENT_HOUSING: u8 = 0x73;
    pub const COMPONENT_SENSOR: u8 = 0x74;
    pub const COMPONENT_DISPLAY: u8 = 0x75;
    pub const COMPONENT_CIRCUIT: u8 = 0x76;
    pub const COMPONENT_MATERIAL: u8 = 0x77;
    pub const COMPONENT_CONNECTOR: u8 = 0x78;
    pub const COMPONENT_LABEL: u8 = 0x79;
    pub const GENERIC_COMPONENT: u8 = 0x7F;
    
    // System/Meta types (0x80-0x8F)
    pub const SYSTEM_ASSEMBLY: u8 = 0x80;
    pub const MAINTENANCE_POINT: u8 = 0x81;
    pub const ACCESS_POINT: u8 = 0x82;
    pub const EMERGENCY_EXIT: u8 = 0x83;
    
    // Network/Communication (0x90-0x9F)
    pub const NETWORK_NODE: u8 = 0x90;
    pub const MESHTASTIC_NODE: u8 = 0x91;
    pub const WIFI_AP: u8 = 0x92;
    
    // Generic/Special
    pub const GENERIC: u8 = 0xFF;
    pub const UNKNOWN: u8 = 0x00;
}

/// Check if an object type is valid
pub fn is_valid_object_type(object_type: u8) -> bool {
    matches!(object_type,
        0x10..=0x1F | // Electrical
        0x20..=0x2F | // HVAC
        0x30..=0x3F | // Lighting
        0x40..=0x4F | // Security
        0x50..=0x5F | // Structural
        0x60..=0x6F | // Plumbing
        0x70..=0x7F | // Components
        0x80..=0x8F | // Systems
        0x90..=0x9F | // Network
        0xFF          // Generic
    )
}

/// Object category derived from type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObjectCategory {
    Electrical,
    HVAC,
    Lighting,
    Security,
    Structural,
    Plumbing,
    Component,
    System,
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
            0x40..=0x4F => Self::Security,
            0x50..=0x5F => Self::Structural,
            0x60..=0x6F => Self::Plumbing,
            0x70..=0x7F => Self::Component,
            0x80..=0x8F => Self::System,
            0x90..=0x9F => Self::Network,
            0xFF => Self::Generic,
            _ => Self::Unknown,
        }
    }
}

/// Validation errors
#[derive(Error, Debug)]
pub enum ValidationError {
    #[error("Invalid building ID (cannot be 0x0000)")]
    InvalidBuildingId,
    
    #[error("Invalid object type: 0x{0:02X}")]
    InvalidObjectType(u8),
    
    #[error("Coordinates out of range")]
    CoordinatesOutOfRange,
}

/// Implied properties generated from object type and fractal seed
#[derive(Debug, Clone)]
pub struct ImpliedProperties {
    pub power_requirements: Option<PowerSpec>,
    pub material: MaterialType,
    pub maintenance_interval: Option<u32>, // days
    pub expected_lifespan: Option<u32>,    // years
    pub weight_kg: Option<f32>,
    pub dimensions_mm: Option<(u16, u16, u16)>,
}

impl ImpliedProperties {
    fn from_object(obj: &ArxObject) -> Self {
        use object_types::*;
        
        match obj.object_type {
            OUTLET => Self {
                power_requirements: Some(PowerSpec { voltage: 120, amperage: 15 }),
                material: MaterialType::Plastic,
                maintenance_interval: Some(365),
                expected_lifespan: Some(30),
                weight_kg: Some(0.1),
                dimensions_mm: Some((70, 115, 45)),
            },
            ELECTRICAL_PANEL => Self {
                power_requirements: Some(PowerSpec { voltage: 240, amperage: 200 }),
                material: MaterialType::Metal,
                maintenance_interval: Some(180),
                expected_lifespan: Some(40),
                weight_kg: Some(20.0),
                dimensions_mm: Some((400, 600, 150)),
            },
            WALL => Self {
                power_requirements: None,
                material: MaterialType::Drywall,
                maintenance_interval: Some(3650),
                expected_lifespan: Some(50),
                weight_kg: None,
                dimensions_mm: None,
            },
            _ => Self {
                power_requirements: None,
                material: MaterialType::Unknown,
                maintenance_interval: None,
                expected_lifespan: None,
                weight_kg: None,
                dimensions_mm: None,
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct PowerSpec {
    pub voltage: u16,
    pub amperage: u16,
}

#[derive(Debug, Clone)]
pub enum MaterialType {
    Metal,
    Plastic,
    Drywall,
    Concrete,
    Wood,
    Glass,
    Composite,
    Unknown,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_arxobject_size() {
        assert_eq!(mem::size_of::<ArxObject>(), 13);
    }
    
    #[test]
    fn test_serialization() {
        let obj = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, -500);
        let bytes = obj.to_bytes();
        assert_eq!(bytes.len(), 13);
        
        let restored = ArxObject::from_bytes(&bytes);
        assert_eq!(restored.building_id, 0x1234);
        assert_eq!(restored.object_type, object_types::OUTLET);
        assert_eq!(restored.x, 1000);
        assert_eq!(restored.y, 2000);
        assert_eq!(restored.z, -500);
    }
    
    #[test]
    fn test_fractal_generation() {
        let parent = ArxObject::new(0x0001, object_types::OUTLET, 5000, 3000, 1500);
        
        // Generate a sub-component
        let sub = parent.generate_contained_object((10, 20, 5), 2.0);
        assert_eq!(sub.building_id, parent.building_id);
        assert!(sub.object_type >= 0x70 && sub.object_type <= 0x7F); // Component range
        
        // Generate containing system
        let container = parent.generate_containing_system(0.5);
        assert_eq!(container.building_id, parent.building_id);
        assert_eq!(container.object_type, object_types::ELECTRICAL_PANEL);
    }
    
    #[test]
    fn test_validation() {
        let valid = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 1500);
        assert!(valid.validate().is_ok());
        
        let invalid_building = ArxObject::new(0, object_types::OUTLET, 1000, 2000, 1500);
        assert!(invalid_building.validate().is_err());
        
        let invalid_type = ArxObject::new(0x1234, 0xAA, 1000, 2000, 1500);
        assert!(invalid_type.validate().is_err());
    }
    
    #[test]
    fn test_position_conversion() {
        let obj = ArxObject::new(0x0001, object_types::WALL, 1500, -2500, 3000);
        let (x, y, z) = obj.position_meters();
        assert_eq!(x, 1.5);
        assert_eq!(y, -2.5);
        assert_eq!(z, 3.0);
    }
}