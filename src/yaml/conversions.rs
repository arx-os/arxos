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
use super::RoomData;
#[allow(deprecated)]
use crate::core::{Equipment, Room};

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
#[allow(dead_code)]
pub(crate) fn room_data_to_room(room_data: &RoomData) -> Room {
    // Use serde for efficient conversion (Room and RoomData serialize to same format)
    // Serialize RoomData to JSON, then deserialize as Room
    let json = serde_json::to_string(room_data).expect("Failed to serialize RoomData");
    let mut room: Room = serde_json::from_str(&json).expect("Failed to deserialize Room");

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
pub fn room_to_room_data(room: &Room) -> crate::yaml::RoomData {
    // Convert spatial_properties to position and bounding_box
    let position = crate::spatial::Point3D {
        x: room.spatial_properties.position.x,
        y: room.spatial_properties.position.y,
        z: room.spatial_properties.position.z,
    };

    let bounding_box = crate::spatial::BoundingBox3D {
        min: crate::spatial::Point3D {
            x: room.spatial_properties.bounding_box.min.x,
            y: room.spatial_properties.bounding_box.min.y,
            z: room.spatial_properties.bounding_box.min.z,
        },
        max: crate::spatial::Point3D {
            x: room.spatial_properties.bounding_box.max.x,
            y: room.spatial_properties.bounding_box.max.y,
            z: room.spatial_properties.bounding_box.max.z,
        },
    };

    // Calculate area and volume from dimensions
    let area = room.spatial_properties.dimensions.width * room.spatial_properties.dimensions.depth;
    let volume = area * room.spatial_properties.dimensions.height;

    // Convert equipment to IDs
    let equipment_ids: Vec<String> = room.equipment.iter().map(|e| e.id.clone()).collect();

    crate::yaml::RoomData {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type: format!("{:?}", room.room_type),
        area: Some(area),
        volume: Some(volume),
        position,
        bounding_box,
        equipment: equipment_ids,
        properties: room.properties.clone(),
    }
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
pub fn equipment_to_equipment_data(equipment: &Equipment) -> crate::yaml::EquipmentData {
    // Map health_status to EquipmentData.status (or derive from operational status)
    let status = match equipment.health_status {
        Some(crate::core::EquipmentHealthStatus::Healthy) => crate::yaml::EquipmentStatus::Healthy,
        Some(crate::core::EquipmentHealthStatus::Warning) => crate::yaml::EquipmentStatus::Warning,
        Some(crate::core::EquipmentHealthStatus::Critical) => {
            crate::yaml::EquipmentStatus::Critical
        }
        Some(crate::core::EquipmentHealthStatus::Unknown) => crate::yaml::EquipmentStatus::Unknown,
        None => {
            // Fall back to deriving from operational status
            match equipment.status {
                crate::core::EquipmentStatus::Active => crate::yaml::EquipmentStatus::Healthy,
                crate::core::EquipmentStatus::Maintenance => crate::yaml::EquipmentStatus::Warning,
                crate::core::EquipmentStatus::Inactive
                | crate::core::EquipmentStatus::OutOfOrder => {
                    crate::yaml::EquipmentStatus::Critical
                }
                crate::core::EquipmentStatus::Unknown => crate::yaml::EquipmentStatus::Unknown,
            }
        }
    };

    // Convert sensor mappings
    let sensor_mappings = equipment.sensor_mappings.as_ref().map(|mappings| {
        mappings
            .iter()
            .map(|m| crate::yaml::SensorMapping {
                sensor_id: m.sensor_id.clone(),
                sensor_type: m.sensor_type.clone(),
                thresholds: m
                    .thresholds
                    .iter()
                    .map(|(k, v)| {
                        (
                            k.clone(),
                            crate::yaml::ThresholdConfig {
                                min: v.min,
                                max: v.max,
                                warning_min: v.warning_min,
                                warning_max: v.warning_max,
                                critical_min: v.critical_min,
                                critical_max: v.critical_max,
                            },
                        )
                    })
                    .collect(),
            })
            .collect()
    });

    crate::yaml::EquipmentData {
        id: equipment.id.clone(),
        name: equipment.name.clone(),
        equipment_type: format!("{:?}", equipment.equipment_type),
        system_type: equipment.system_type(),
        position: crate::spatial::Point3D {
            x: equipment.position.x,
            y: equipment.position.y,
            z: equipment.position.z,
        },
        bounding_box: crate::spatial::BoundingBox3D {
            min: crate::spatial::Point3D {
                x: equipment.position.x - 0.5,
                y: equipment.position.y - 0.5,
                z: equipment.position.z,
            },
            max: crate::spatial::Point3D {
                x: equipment.position.x + 0.5,
                y: equipment.position.y + 0.5,
                z: equipment.position.z + 1.0,
            },
        },
        status,
        properties: equipment.properties.clone(),
        universal_path: equipment.path.clone(),
        address: equipment.address.clone(),
        sensor_mappings,
    }
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
pub fn equipment_data_to_equipment(data: &crate::yaml::EquipmentData) -> Equipment {
    // Parse equipment_type from string
    let equipment_type = match data.equipment_type.as_str() {
        "HVAC" => crate::core::EquipmentType::HVAC,
        "Electrical" => crate::core::EquipmentType::Electrical,
        "AV" => crate::core::EquipmentType::AV,
        "Furniture" => crate::core::EquipmentType::Furniture,
        "Safety" => crate::core::EquipmentType::Safety,
        "Plumbing" => crate::core::EquipmentType::Plumbing,
        "Network" => crate::core::EquipmentType::Network,
        other => crate::core::EquipmentType::Other(other.to_string()),
    };

    // Convert health status to health_status
    let health_status = match data.status {
        crate::yaml::EquipmentStatus::Healthy => Some(crate::core::EquipmentHealthStatus::Healthy),
        crate::yaml::EquipmentStatus::Warning => Some(crate::core::EquipmentHealthStatus::Warning),
        crate::yaml::EquipmentStatus::Critical => {
            Some(crate::core::EquipmentHealthStatus::Critical)
        }
        crate::yaml::EquipmentStatus::Unknown => Some(crate::core::EquipmentHealthStatus::Unknown),
    };

    // Map operational status based on YAML status (health-based)
    let status = match data.status {
        crate::yaml::EquipmentStatus::Healthy => crate::core::EquipmentStatus::Active,
        crate::yaml::EquipmentStatus::Warning => crate::core::EquipmentStatus::Maintenance,
        crate::yaml::EquipmentStatus::Critical => crate::core::EquipmentStatus::Inactive,
        crate::yaml::EquipmentStatus::Unknown => crate::core::EquipmentStatus::Unknown,
    };

    // Convert sensor mappings
    let sensor_mappings = data.sensor_mappings.as_ref().map(|mappings| {
        mappings
            .iter()
            .map(|m| crate::core::SensorMapping {
                sensor_id: m.sensor_id.clone(),
                sensor_type: m.sensor_type.clone(),
                thresholds: m
                    .thresholds
                    .iter()
                    .map(|(k, v)| {
                        (
                            k.clone(),
                            crate::core::ThresholdConfig {
                                min: v.min,
                                max: v.max,
                                warning_min: v.warning_min,
                                warning_max: v.warning_max,
                                critical_min: v.critical_min,
                                critical_max: v.critical_max,
                            },
                        )
                    })
                    .collect(),
            })
            .collect()
    });

    Equipment {
        id: data.id.clone(),
        name: data.name.clone(),
        path: data.universal_path.clone(),
        address: data.address.clone(),
        equipment_type,
        position: crate::core::Position {
            x: data.position.x,
            y: data.position.y,
            z: data.position.z,
            coordinate_system: "LOCAL".to_string(),
        },
        properties: data.properties.clone(),
        status,
        health_status,
        room_id: None,
        sensor_mappings,
    }
}
