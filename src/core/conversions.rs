//! Conversion functions between core types and YAML types

use super::{Room, Equipment, RoomType, EquipmentType, EquipmentStatus};
use super::types::{Position, Dimensions, BoundingBox, SpatialProperties};

/// Helper function to load building data from current directory
pub(crate) fn load_building_data_from_dir() -> Result<crate::yaml::BuildingData, Box<dyn std::error::Error>> {
    // Find YAML files in current directory
    let yaml_files: Vec<String> = std::fs::read_dir(".")
        .map_err(|e| format!("Failed to read current directory: {}", e))?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()? == "yaml" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();
    
    let yaml_file = yaml_files.first()
        .ok_or("No YAML files found in current directory. Run 'arx import <ifc-file>' first.")?;
    let yaml_content = std::fs::read_to_string(yaml_file)?;
    let building_data: crate::yaml::BuildingData = serde_yaml::from_str(&yaml_content)?;
    
    Ok(building_data)
}

/// Convert RoomData to Room
pub(crate) fn room_data_to_room(room_data: &crate::yaml::RoomData) -> Room {
    let room_type = match room_data.room_type.as_str() {
        "Classroom" => RoomType::Classroom,
        "Laboratory" => RoomType::Laboratory,
        "Office" => RoomType::Office,
        "Gymnasium" => RoomType::Gymnasium,
        "Cafeteria" => RoomType::Cafeteria,
        "Library" => RoomType::Library,
        "Auditorium" => RoomType::Auditorium,
        "Hallway" => RoomType::Hallway,
        "Restroom" => RoomType::Restroom,
        "Storage" => RoomType::Storage,
        "Mechanical" => RoomType::Mechanical,
        "Electrical" => RoomType::Electrical,
        _ => RoomType::Other(room_data.room_type.clone()),
    };
    
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
                coordinate_system: "building_local".to_string(),
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
                    coordinate_system: "building_local".to_string(),
                },
                max: Position {
                    x: room_data.bounding_box.max.x,
                    y: room_data.bounding_box.max.y,
                    z: room_data.bounding_box.max.z,
                    coordinate_system: "building_local".to_string(),
                },
            },
            coordinate_system: "building_local".to_string(),
        },
        properties: room_data.properties.clone(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
    }
}

/// Convert Equipment to EquipmentData
pub(crate) fn equipment_to_equipment_data(equipment: &Equipment) -> crate::yaml::EquipmentData {
    use crate::yaml::EquipmentStatus as YamlEquipmentStatus;
    
    crate::yaml::EquipmentData {
        id: equipment.id.clone(),
        name: equipment.name.clone(),
        equipment_type: format!("{:?}", equipment.equipment_type),
        system_type: "HVAC".to_string(), // Default system type
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
        sensor_mappings: None,
    }
}

/// Convert EquipmentData to Equipment
pub(crate) fn equipment_data_to_equipment(equipment_data: &crate::yaml::EquipmentData) -> Equipment {
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
        equipment_type,
        position: Position {
            x: equipment_data.position.x,
            y: equipment_data.position.y,
            z: equipment_data.position.z,
            coordinate_system: "building_local".to_string(),
        },
        properties: equipment_data.properties.clone(),
        status: match equipment_data.status {
            crate::yaml::EquipmentStatus::Healthy => EquipmentStatus::Active,
            crate::yaml::EquipmentStatus::Warning => EquipmentStatus::Maintenance,
            crate::yaml::EquipmentStatus::Critical => EquipmentStatus::Inactive,
            crate::yaml::EquipmentStatus::Unknown => EquipmentStatus::Unknown,
        },
        room_id: None,
    }
}

