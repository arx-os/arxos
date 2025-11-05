//! Conversion functions between core types and YAML types
//!
//! This module provides conversion functions between core domain types (Room, Equipment)
//! and YAML serialization types (RoomData, EquipmentData). These conversions are
//! YAML-specific, so they belong in the yaml module rather than core.

use crate::core::{Room, Equipment, RoomType, EquipmentType, EquipmentStatus};
use crate::core::{Position, Dimensions, BoundingBox, SpatialProperties};
use super::{RoomData, EquipmentData, EquipmentStatus as YamlEquipmentStatus};

/// Coordinate system constant to avoid repeated string allocations
const COORD_SYSTEM_BUILDING_LOCAL: &str = "building_local";

/// Convert RoomData to Room
pub(crate) fn room_data_to_room(room_data: &RoomData) -> Room {
    // Use FromStr trait for parsing
    let room_type = room_data.room_type.parse().unwrap_or_else(|_| RoomType::Other(room_data.room_type.clone()));
    
    Room {
        id: room_data.id.clone(),
        name: room_data.name.clone(),
        room_type,
        equipment: Vec::new(), // Will be populated separately if needed
        spatial_properties: SpatialProperties {
            position: Position {
                x: room_data.position.x,
                y: room_data.position.y,
                z: room_data.position.z,
                coordinate_system: COORD_SYSTEM_BUILDING_LOCAL.to_string(),
            },
            dimensions: Dimensions {
                width: room_data.bounding_box.max.x - room_data.bounding_box.min.x,
                height: room_data.bounding_box.max.z - room_data.bounding_box.min.z,
                depth: room_data.bounding_box.max.y - room_data.bounding_box.min.y,
            },
            bounding_box: BoundingBox {
                min: Position {
                    x: room_data.bounding_box.min.x,
                    y: room_data.bounding_box.min.y,
                    z: room_data.bounding_box.min.z,
                    coordinate_system: COORD_SYSTEM_BUILDING_LOCAL.to_string(),
                },
                max: Position {
                    x: room_data.bounding_box.max.x,
                    y: room_data.bounding_box.max.y,
                    z: room_data.bounding_box.max.z,
                    coordinate_system: COORD_SYSTEM_BUILDING_LOCAL.to_string(),
                },
            },
            coordinate_system: COORD_SYSTEM_BUILDING_LOCAL.to_string(),
        },
        properties: room_data.properties.clone(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
    }
}

/// Convert Equipment to EquipmentData
pub(crate) fn equipment_to_equipment_data(equipment: &Equipment) -> EquipmentData {
    
    // Derive system_type from equipment_type (pre-allocated strings)
    let system_type = match &equipment.equipment_type {
        EquipmentType::HVAC => "HVAC",
        EquipmentType::Electrical => "ELECTRICAL",
        EquipmentType::Plumbing => "PLUMBING",
        EquipmentType::Safety => "SAFETY",
        EquipmentType::Network => "NETWORK",
        EquipmentType::AV => "AV",
        EquipmentType::Furniture => "FURNITURE",
        EquipmentType::Other(_) => "OTHER",
    }.to_string();
    
    EquipmentData {
        id: equipment.id.clone(),
        name: equipment.name.clone(),
        equipment_type: format!("{:?}", equipment.equipment_type),
        system_type,
        position: crate::spatial::Point3D {
            x: equipment.position.x,
            y: equipment.position.y,
            z: equipment.position.z,
        },
        bounding_box: crate::spatial::BoundingBox3D {
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
        },
        status: match equipment.status {
            EquipmentStatus::Active => YamlEquipmentStatus::Healthy,
            EquipmentStatus::Maintenance => YamlEquipmentStatus::Warning,
            EquipmentStatus::Inactive => YamlEquipmentStatus::Critical,
            EquipmentStatus::OutOfOrder => YamlEquipmentStatus::Critical,
            EquipmentStatus::Unknown => YamlEquipmentStatus::Unknown,
        },
        properties: equipment.properties.clone(),
        universal_path: equipment.path.clone(),
        address: equipment.address.clone(),
        sensor_mappings: None,
    }
}

/// Convert EquipmentData to Equipment
pub(crate) fn equipment_data_to_equipment(equipment_data: &EquipmentData) -> Equipment {
    let equipment_type = match equipment_data.equipment_type.as_str() {
        "HVAC" => EquipmentType::HVAC,
        "Electrical" => EquipmentType::Electrical,
        "AV" => EquipmentType::AV,
        "Furniture" => EquipmentType::Furniture,
        "Safety" => EquipmentType::Safety,
        "Plumbing" => EquipmentType::Plumbing,
        "Network" => EquipmentType::Network,
        _ => EquipmentType::Other(equipment_data.equipment_type.clone()),
    };
    
    Equipment {
        id: equipment_data.id.clone(),
        name: equipment_data.name.clone(),
        path: equipment_data.universal_path.clone(),
        address: equipment_data.address.clone(),
        equipment_type,
        position: Position {
            x: equipment_data.position.x,
            y: equipment_data.position.y,
            z: equipment_data.position.z,
            coordinate_system: COORD_SYSTEM_BUILDING_LOCAL.to_string(),
        },
        properties: equipment_data.properties.clone(),
        status: match equipment_data.status {
            YamlEquipmentStatus::Healthy => EquipmentStatus::Active,
            YamlEquipmentStatus::Warning => EquipmentStatus::Maintenance,
            YamlEquipmentStatus::Critical => EquipmentStatus::Inactive,
            YamlEquipmentStatus::Unknown => EquipmentStatus::Unknown,
        },
        room_id: None,
    }
}

