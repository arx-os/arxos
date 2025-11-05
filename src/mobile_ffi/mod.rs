//! Mobile FFI interface for ArxOS
//! 
//! This module provides foreign function interface bindings for mobile applications.
//! The functions are designed to be called from iOS (Swift) and Android (Kotlin).
//!
//! All functions are FFI-safe and compatible with C-compatible calling conventions.

pub mod ffi;
pub mod offline_queue;
// Note: JNI module is conditionally compiled for Android targets
// The module file will be added when Android JNI integration is implemented

use crate::core::{Room, Equipment};
use std::collections::HashMap;

/// Error type for FFI operations
///
/// All errors are serialized to JSON for cross-platform compatibility.
#[derive(Debug, Clone)]
pub enum MobileError {
    /// Resource not found error
    NotFound(String),
    /// Invalid data format or content
    InvalidData(String),
    /// I/O or file system error
    IoError(String),
}

/// AR scan data from mobile devices (iOS/Android)
///
/// This struct represents augmented reality scan data received from mobile apps,
/// including detected equipment, room boundaries, and scan metadata.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ARScanData {
    #[serde(rename = "detectedEquipment")]
    pub detected_equipment: Vec<DetectedEquipment>,
    #[serde(rename = "roomBoundaries")]
    #[serde(default)]
    pub room_boundaries: RoomBoundaries,
    #[serde(rename = "deviceType")]
    pub device_type: Option<String>,
    #[serde(rename = "appVersion")]
    pub app_version: Option<String>,
    #[serde(rename = "scanDurationMs")]
    pub scan_duration_ms: Option<u64>,
    #[serde(rename = "pointCount")]
    pub point_count: Option<u64>,
    #[serde(rename = "accuracyEstimate")]
    pub accuracy_estimate: Option<f64>,
    #[serde(rename = "lightingConditions")]
    pub lighting_conditions: Option<String>,
    #[serde(rename = "roomName")]
    pub room_name: String,
    #[serde(rename = "floorLevel")]
    pub floor_level: i32,
}

/// Equipment detected during an AR scan
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DetectedEquipment {
    pub name: String,
    #[serde(rename = "type")]
    pub equipment_type: String,
    pub position: Position3D,
    pub confidence: f64,
    #[serde(rename = "detectionMethod")]
    pub detection_method: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Position3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct RoomBoundaries {
    pub walls: Vec<Wall>,
    pub openings: Vec<Opening>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Wall {
    #[serde(rename = "startPoint")]
    pub start_point: Position3D,
    #[serde(rename = "endPoint")]
    pub end_point: Position3D,
    pub height: f64,
    pub thickness: f64,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Opening {
    pub position: Position3D,
    pub width: f64,
    pub height: f64,
    #[serde(rename = "type")]
    pub opening_type: String,
}

impl std::fmt::Display for MobileError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MobileError::NotFound(msg) => write!(f, "Not found: {}", msg),
            MobileError::InvalidData(msg) => write!(f, "Invalid data: {}", msg),
            MobileError::IoError(msg) => write!(f, "IO error: {}", msg),
        }
    }
}

impl std::error::Error for MobileError {}

/// Room information for mobile apps
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct RoomInfo {
    pub id: String,
    pub name: String,
    pub room_type: String,
    pub position: Position,
    pub properties: HashMap<String, String>,
}

/// Equipment information for mobile apps
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct EquipmentInfo {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub position: Position,
    pub properties: HashMap<String, String>,
}

/// Position data
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Position {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub coordinate_system: String,
}

/// List rooms for a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// 
/// # Returns
/// 
/// A vector of RoomInfo objects representing all rooms in the building
pub fn list_rooms(building_name: String) -> Result<Vec<RoomInfo>, MobileError> {
    match crate::core::list_rooms(Some(&building_name)) {
        Ok(rooms) => Ok(rooms.into_iter().map(room_to_room_info).collect()),
        Err(e) => Err(MobileError::IoError(e.to_string())),
    }
}

/// Get a specific room
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `room_id` - ID or name of the room
/// 
/// # Returns
/// 
/// RoomInfo for the requested room
pub fn get_room(building_name: String, room_id: String) -> Result<RoomInfo, MobileError> {
    match crate::core::get_room(Some(&building_name), &room_id) {
        Ok(room) => Ok(room_to_room_info(room)),
        Err(e) => Err(MobileError::NotFound(format!("Room '{}' not found: {}", room_id, e))),
    }
}

/// List equipment for a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// 
/// # Returns
/// 
/// A vector of EquipmentInfo objects representing all equipment in the building
pub fn list_equipment(building_name: String) -> Result<Vec<EquipmentInfo>, MobileError> {
    match crate::core::list_equipment(Some(&building_name)) {
        Ok(equipment) => Ok(equipment.into_iter().map(equipment_to_equipment_info).collect()),
        Err(e) => Err(MobileError::IoError(e.to_string())),
    }
}

/// Get a specific equipment item
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `equipment_id` - ID or name of the equipment
/// 
/// # Returns
/// 
/// EquipmentInfo for the requested equipment
pub fn get_equipment(building_name: String, equipment_id: String) -> Result<EquipmentInfo, MobileError> {
    match crate::core::list_equipment(Some(&building_name)) {
        Ok(equipment) => {
            equipment.into_iter()
                .find(|e| e.id == equipment_id || e.name == equipment_id)
                .map(equipment_to_equipment_info)
                .ok_or_else(|| MobileError::NotFound(format!("Equipment '{}' not found", equipment_id)))
        }
        Err(e) => Err(MobileError::IoError(e.to_string())),
    }
}

/// Create a room in a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `floor_level` - Floor level
/// * `room` - Room information
/// * `commit` - Whether to commit to Git
/// 
/// # Returns
/// 
/// Unit on success
pub fn create_room(building_name: String, floor_level: i32, room: RoomInfo, commit: bool) -> Result<(), MobileError> {
    use crate::core::{Room, RoomType, SpatialProperties, Position as CorePosition, Dimensions, BoundingBox};
    use chrono::Utc;
    
    let room_type = room.room_type.parse().unwrap_or(RoomType::Other(room.room_type.clone()));
    let spatial_props = SpatialProperties {
        position: CorePosition {
            x: room.position.x,
            y: room.position.y,
            z: room.position.z,
            coordinate_system: room.position.coordinate_system.clone(),
        },
        dimensions: Dimensions {
            width: 10.0, // Default dimensions
            depth: 10.0,
            height: 3.0,
        },
            bounding_box: BoundingBox {
                min: CorePosition {
                    x: room.position.x - 5.0,
                    y: room.position.y - 5.0,
                    z: room.position.z,
                    coordinate_system: room.position.coordinate_system.clone(),
                },
                max: CorePosition {
                    x: room.position.x + 5.0,
                    y: room.position.y + 5.0,
                    z: room.position.z + 3.0,
                    coordinate_system: room.position.coordinate_system.clone(),
                },
            },
            coordinate_system: room.position.coordinate_system,
    };
    
    let core_room = Room {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type,
        equipment: vec![],
        spatial_properties: spatial_props,
        properties: room.properties.clone(),
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };
    
    // Extract wing from room properties if available
    let wing_name = room.properties.get("wing")
        .map(|s| s.as_str());
    
    crate::core::create_room(&building_name, floor_level, core_room, wing_name, commit)
        .map_err(|e| MobileError::IoError(e.to_string()))
}

/// Update a room in a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `room_id` - ID or name of the room
/// * `properties` - Properties to update
/// * `commit` - Whether to commit to Git
/// 
/// # Returns
/// 
/// Updated RoomInfo
pub fn update_room(building_name: String, room_id: String, properties: HashMap<String, String>, commit: bool) -> Result<RoomInfo, MobileError> {
    match crate::core::update_room_impl(&building_name, &room_id, properties.clone(), commit) {
        Ok(room) => Ok(room_to_room_info(room)),
        Err(e) => Err(MobileError::IoError(e.to_string())),
    }
}

/// Delete a room from a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `room_id` - ID or name of the room
/// * `commit` - Whether to commit to Git
/// 
/// # Returns
/// 
/// Unit on success
pub fn delete_room(building_name: String, room_id: String, commit: bool) -> Result<(), MobileError> {
    crate::core::delete_room_impl(&building_name, &room_id, commit)
        .map_err(|e| MobileError::IoError(e.to_string()))
}

/// Parse AR scan data from JSON
/// 
/// # Arguments
/// 
/// * `json_data` - JSON string containing AR scan data
/// 
/// # Returns
/// 
/// Parsed AR scan data structure
pub fn parse_ar_scan(json_data: &str) -> Result<ARScanData, MobileError> {
    serde_json::from_str(json_data)
        .map_err(|e| MobileError::InvalidData(format!("Failed to parse AR scan JSON: {}", e)))
}

/// Process AR scan and extract detected equipment
/// 
/// # Arguments
/// 
/// * `scan_data` - AR scan data
/// 
/// # Returns
/// 
/// Vector of equipment information extracted from AR scan
pub fn extract_equipment_from_ar_scan(scan_data: &ARScanData) -> Vec<EquipmentInfo> {
    scan_data.detected_equipment.iter().map(|eq| {
        EquipmentInfo {
            id: eq.name.clone(),
            name: eq.name.clone(),
            equipment_type: eq.equipment_type.clone(),
            status: "Unknown".to_string(),
            position: Position {
                x: eq.position.x,
                y: eq.position.y,
                z: eq.position.z,
                coordinate_system: "world".to_string(),
            },
            properties: {
                let mut props = HashMap::new();
                props.insert("confidence".to_string(), eq.confidence.to_string());
                if let Some(ref method) = eq.detection_method {
                    props.insert("detection_method".to_string(), method.clone());
                }
                props
            },
        }
    }).collect()
}

/// Add equipment to a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `equipment` - Equipment information
/// * `room_id` - Optional room ID to attach to
/// * `commit` - Whether to commit to Git
/// 
/// # Returns
/// 
/// Unit on success
pub fn add_equipment(building_name: String, equipment: EquipmentInfo, room_id: Option<String>, commit: bool) -> Result<(), MobileError> {
    use crate::core::{Equipment, EquipmentType, EquipmentStatus, Position as CorePosition};
    
    let equipment_type = match equipment.equipment_type.as_str() {
        "HVAC" => EquipmentType::HVAC,
        "Electrical" => EquipmentType::Electrical,
        "AV" => EquipmentType::AV,
        "Furniture" => EquipmentType::Furniture,
        "Safety" => EquipmentType::Safety,
        "Plumbing" => EquipmentType::Plumbing,
        "Network" => EquipmentType::Network,
        _ => EquipmentType::Other(equipment.equipment_type.clone()),
    };
    
    let status = match equipment.status.as_str() {
        "Active" => EquipmentStatus::Active,
        "Maintenance" => EquipmentStatus::Maintenance,
        "Inactive" => EquipmentStatus::Inactive,
        "OutOfOrder" => EquipmentStatus::OutOfOrder,
        _ => EquipmentStatus::Unknown,
    };
    
    let equipment_room_id = room_id.clone();
    let core_equipment = Equipment {
        id: equipment.id.clone(),
        name: equipment.name.clone(),
        path: format!("/equipment/{}", equipment.id),
        address: None,
        equipment_type,
        position: CorePosition {
            x: equipment.position.x,
            y: equipment.position.y,
            z: equipment.position.z,
            coordinate_system: equipment.position.coordinate_system.clone(),
        },
        properties: equipment.properties.clone(),
        status,
        room_id: equipment_room_id.clone(),
    };
    
    crate::core::add_equipment(&building_name, room_id.as_deref(), core_equipment, commit)
        .map_err(|e| MobileError::IoError(e.to_string()))
}

/// Update equipment in a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `equipment_id` - ID or name of the equipment
/// * `properties` - Properties to update
/// * `commit` - Whether to commit to Git
/// 
/// # Returns
/// 
/// Updated EquipmentInfo
pub fn update_equipment(building_name: String, equipment_id: String, properties: HashMap<String, String>, commit: bool) -> Result<EquipmentInfo, MobileError> {
    match crate::core::update_equipment_impl(&building_name, &equipment_id, properties.clone(), commit) {
        Ok(equipment) => Ok(equipment_to_equipment_info(equipment)),
        Err(e) => Err(MobileError::IoError(e.to_string())),
    }
}

/// Remove equipment from a building
/// 
/// # Arguments
/// 
/// * `building_name` - Name of the building
/// * `equipment_id` - ID or name of the equipment
/// * `commit` - Whether to commit to Git
/// 
/// # Returns
/// 
/// Unit on success
pub fn remove_equipment(building_name: String, equipment_id: String, commit: bool) -> Result<(), MobileError> {
    crate::core::remove_equipment_impl(&building_name, &equipment_id, commit)
        .map_err(|e| MobileError::IoError(e.to_string()))
}

/// Convert Room to RoomInfo
pub fn room_to_room_info(room: Room) -> RoomInfo {
    RoomInfo {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type: format!("{}", room.room_type),
        position: Position {
            x: room.spatial_properties.position.x,
            y: room.spatial_properties.position.y,
            z: room.spatial_properties.position.z,
            coordinate_system: room.spatial_properties.position.coordinate_system.clone(),
        },
        properties: room.properties.clone(),
    }
}

/// Convert Equipment to EquipmentInfo
pub fn equipment_to_equipment_info(equipment: Equipment) -> EquipmentInfo {
    EquipmentInfo {
        id: equipment.id.clone(),
        name: equipment.name.clone(),
        equipment_type: format!("{:?}", equipment.equipment_type),
        status: format!("{:?}", equipment.status),
        position: Position {
            x: equipment.position.x,
            y: equipment.position.y,
            z: equipment.position.z,
            coordinate_system: equipment.position.coordinate_system.clone(),
        },
        properties: equipment.properties.clone(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_room_to_room_info() {
        use crate::core::{Room, RoomType, SpatialProperties, Position, Dimensions, BoundingBox};
        
        let room = Room {
            id: "test-1".to_string(),
            name: "Test Room".to_string(),
            room_type: RoomType::Office,
            equipment: vec![],
            spatial_properties: SpatialProperties {
                position: Position { x: 1.0, y: 2.0, z: 3.0, coordinate_system: "local".to_string() },
                dimensions: Dimensions { width: 10.0, depth: 20.0, height: 3.0 },
                bounding_box: BoundingBox {
                    min: Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() },
                    max: Position { x: 10.0, y: 20.0, z: 3.0, coordinate_system: "local".to_string() },
                },
                coordinate_system: "local".to_string(),
            },
            properties: HashMap::new(),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        
        let info = room_to_room_info(room);
        assert_eq!(info.id, "test-1");
        assert_eq!(info.name, "Test Room");
        assert_eq!(info.position.x, 1.0);
    }
}

