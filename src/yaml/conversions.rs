//! Conversion functions between core types and YAML types
//!
//! **DEPRECATED**: These conversion functions are maintained for backward compatibility.
//! Core types (Equipment, Room) now serialize directly to YAML format, so conversion
//! functions should be avoided in new code. Use core types directly with serde serialization.
//!
//! This module provides conversion functions between core domain types (Room, Equipment)
//! and YAML serialization types (RoomData, EquipmentData). These conversions are
//! YAML-specific, so they belong in the yaml module rather than core.

#[allow(deprecated)]
use crate::core::{Room, Equipment};
#[allow(deprecated)]
use super::{RoomData, EquipmentData};

// Note: EquipmentData and RoomData cannot be type aliases because they have different structures:
// - EquipmentData has `equipment_type: String`, `system_type: String`, `bounding_box: BoundingBox3D`
// - Equipment has `equipment_type: EquipmentType` (enum), no `system_type` field, `position: Position`
// - RoomData has `room_type: String`, `area: Option<f64>`, `volume: Option<f64>`, `position: Point3D`
// - Room has `room_type: RoomType` (enum), `spatial_properties: SpatialProperties`
//
// However, they serialize to the same format (thanks to custom serialization), so we use serde
// for efficient conversion, then add computed fields.

/// Convert RoomData to Room
///
/// **DEPRECATED**: Room now deserializes directly from YAML format.
/// Use `serde::Deserialize` on Room directly instead.
///
/// This function uses serde for efficient conversion since Room and RoomData
/// serialize to the same format (except for computed fields like area/volume).
#[deprecated(note = "Use Room::deserialize directly from YAML instead")]
#[allow(deprecated)]
pub(crate) fn room_data_to_room(room_data: &RoomData) -> Room {
    // Use serde for efficient conversion (Room and RoomData serialize to same format)
    // Serialize RoomData to JSON, then deserialize as Room
    let json = serde_json::to_string(room_data)
        .expect("Failed to serialize RoomData");
    let mut room: Room = serde_json::from_str(&json)
        .expect("Failed to deserialize Room");
    
    // Equipment is deserialized as empty Vec (RoomData has equipment as IDs)
    // This matches the behavior of the old conversion function
    room.equipment = Vec::new();
    
    room
}

/// Convert Room to RoomData
///
/// **DEPRECATED**: Room now serializes directly to YAML format.
/// Use `serde::Serialize` on Room directly instead.
///
/// This function uses serde for efficient conversion since Room and RoomData
/// serialize to the same format (except for computed fields like area/volume).
#[deprecated(note = "Use Room::serialize directly to YAML instead")]
#[allow(deprecated)]
pub(crate) fn room_to_room_data(room: &Room) -> RoomData {
    // Use serde for efficient conversion (Room and RoomData serialize to same format)
    // Serialize Room to JSON, then deserialize as RoomData
    let json = serde_json::to_string(room)
        .expect("Failed to serialize Room");
    let mut room_data: RoomData = serde_json::from_str(&json)
        .expect("Failed to deserialize RoomData");
    
    // Equipment is serialized as IDs in Room, so RoomData will have equipment as Vec<String>
    // This matches the expected behavior
    
    room_data
}

/// Convert Equipment to EquipmentData
///
/// **DEPRECATED**: Equipment now serializes directly to YAML format.
/// Use `serde::Serialize` on Equipment directly instead.
///
/// This function uses serde for efficient conversion, then adds computed fields
/// (system_type, bounding_box) that EquipmentData requires.
#[deprecated(note = "Use Equipment::serialize directly to YAML instead")]
#[allow(deprecated)]
pub(crate) fn equipment_to_equipment_data(equipment: &Equipment) -> EquipmentData {
    // Use serde for base conversion (Equipment and EquipmentData serialize to same format)
    // Serialize Equipment to JSON, then deserialize as EquipmentData
    let json = serde_json::to_string(equipment)
        .expect("Failed to serialize Equipment");
    let mut equipment_data: EquipmentData = serde_json::from_str(&json)
        .expect("Failed to deserialize EquipmentData");
    
    // Add computed fields that EquipmentData requires
    equipment_data.system_type = equipment.system_type();
    equipment_data.equipment_type = format!("{:?}", equipment.equipment_type);
    equipment_data.bounding_box = crate::spatial::BoundingBox3D {
        min: crate::spatial::Point3D { 
            x: equipment.position.x - 0.5, 
            y: equipment.position.y - 0.5, 
            z: equipment.position.z 
        },
        max: crate::spatial::Point3D { 
            x: equipment.position.x + 0.5, 
            y: equipment.position.y + 0.5, 
            z: equipment.position.z + 1.0 
        },
    };
    equipment_data.universal_path = equipment.path.clone();
    
    equipment_data
}

/// Convert EquipmentData to Equipment
///
/// **DEPRECATED**: Equipment now deserializes directly from YAML format.
/// Use `serde::Deserialize` on Equipment directly instead.
///
/// This function uses serde for efficient conversion since Equipment and EquipmentData
/// serialize to the same format (except for computed fields like system_type, bounding_box).
#[deprecated(note = "Use Equipment::deserialize directly from YAML instead")]
#[allow(deprecated)]
pub(crate) fn equipment_data_to_equipment(equipment_data: &EquipmentData) -> Equipment {
    // Use serde for efficient conversion (Equipment and EquipmentData serialize to same format)
    // Serialize EquipmentData to JSON, then deserialize as Equipment
    let json = serde_json::to_string(equipment_data)
        .expect("Failed to serialize EquipmentData");
    let mut equipment: Equipment = serde_json::from_str(&json)
        .expect("Failed to deserialize Equipment");
    
    // Set path from universal_path (EquipmentData uses universal_path, Equipment uses path)
    equipment.path = equipment_data.universal_path.clone();
    
    equipment
}

