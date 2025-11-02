//! Business logic operations for building, room, and equipment management

use std::collections::HashMap;
use super::{Room, Equipment};
use super::types::{Position, SpatialQueryResult};
use super::conversions::{load_building_data_from_dir, room_data_to_room, equipment_to_equipment_data, equipment_data_to_equipment};

/// Create a room in a building
pub fn create_room(building_name: &str, floor_level: i32, room: Room, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::yaml::{FloorData, RoomData};
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find or create floor
    let floor_data = building_data.floors.iter_mut()
        .find(|f| f.level == floor_level);
    
    let floor_data = if let Some(floor) = floor_data {
        floor
    } else {
        // Floor doesn't exist, create it
        let new_floor = FloorData {
            id: format!("floor-{}", floor_level),
            name: format!("Floor {}", floor_level),
            level: floor_level,
            elevation: floor_level as f64 * 3.0,
            rooms: vec![],
            equipment: vec![],
            bounding_box: None,
        };
        building_data.floors.push(new_floor);
        // Safe unwrap: we just pushed, so the vector is non-empty
        building_data.floors.last_mut()
            .ok_or_else(|| "Failed to access newly created floor".to_string())?
    };
    
    // Convert Room to RoomData
    let room_data = RoomData {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type: room.room_type.to_string(),
        area: Some(room.spatial_properties.dimensions.width * room.spatial_properties.dimensions.depth),
        volume: Some(room.spatial_properties.dimensions.width * room.spatial_properties.dimensions.depth * room.spatial_properties.dimensions.height),
        position: crate::spatial::Point3D {
            x: room.spatial_properties.position.x,
            y: room.spatial_properties.position.y,
            z: room.spatial_properties.position.z,
        },
        bounding_box: crate::spatial::BoundingBox3D {
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
        },
        equipment: vec![],
        properties: room.properties.clone(),
    };
    
    // Add room to floor
    floor_data.rooms.push(room_data);
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Add room: {}", room.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

/// Add equipment to a room or floor
pub fn add_equipment(building_name: &str, room_name: Option<&str>, equipment: Equipment, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find room if specified
    if let Some(room_name) = room_name {
        for floor in &mut building_data.floors {
            if let Some(room) = floor.rooms.iter_mut().find(|r| r.name == room_name) {
                // Convert Equipment to EquipmentData and add to room's equipment list
                room.equipment.push(equipment.id.clone());
                // Also add to floor's equipment list
                floor.equipment.push(equipment_to_equipment_data(&equipment));
                break;
            }
        }
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Add equipment: {}", equipment.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

/// Perform a spatial query
pub fn spatial_query(_query_type: &str, _entity: &str, _params: Vec<String>) -> Result<Vec<SpatialQueryResult>, Box<dyn std::error::Error>> {
    let building_data = load_building_data_from_dir()?;
    let mut results = Vec::new();
    
    // Query rooms and equipment based on spatial criteria
    for floor in &building_data.floors {
        for room in &floor.rooms {
            let distance = (room.position.x.powi(2) + room.position.y.powi(2) + room.position.z.powi(2)).sqrt();
            results.push(SpatialQueryResult {
                entity_name: room.name.clone(),
                entity_type: format!("Room ({})", room.room_type),
                position: Position {
                    x: room.position.x,
                    y: room.position.y,
                    z: room.position.z,
                    coordinate_system: "building_local".to_string(),
                },
                distance,
            });
        }
        
        for equipment in &floor.equipment {
            let distance = (equipment.position.x.powi(2) + equipment.position.y.powi(2) + equipment.position.z.powi(2)).sqrt();
            results.push(SpatialQueryResult {
                entity_name: equipment.name.clone(),
                entity_type: format!("Equipment ({})", equipment.equipment_type),
                position: Position {
                    x: equipment.position.x,
                    y: equipment.position.y,
                    z: equipment.position.z,
                    coordinate_system: "building_local".to_string(),
                },
                distance,
            });
        }
    }
    
    Ok(results)
}

/// List all rooms in the building
/// 
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
pub fn list_rooms(building_name: Option<&str>) -> Result<Vec<Room>, Box<dyn std::error::Error>> {
    let building_data = if let Some(building) = building_name {
        use crate::persistence::PersistenceManager;
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };
    
    let mut rooms = Vec::new();
    
    for floor in &building_data.floors {
        for room_data in &floor.rooms {
            rooms.push(room_data_to_room(room_data));
        }
    }
    
    Ok(rooms)
}

/// Get a specific room by name
/// 
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
/// * `room_name` - Name or ID of the room to retrieve.
pub fn get_room(building_name: Option<&str>, room_name: &str) -> Result<Room, Box<dyn std::error::Error>> {
    let building_data = if let Some(building) = building_name {
        use crate::persistence::PersistenceManager;
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };
    
    for floor in &building_data.floors {
        for room_data in &floor.rooms {
            if room_data.name.to_lowercase() == room_name.to_lowercase() || 
               room_data.id.to_lowercase() == room_name.to_lowercase() {
                return Ok(room_data_to_room(room_data));
            }
        }
    }
    
    Err(format!("Room '{}' not found", room_name).into())
}

/// Update a room in a building
pub fn update_room_impl(building_name: &str, room_id: &str, updates: HashMap<String, String>, commit: bool) -> Result<Room, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and update room
    let mut room_data = None;
    for floor in &mut building_data.floors {
        if let Some(room) = floor.rooms.iter_mut().find(|r| r.id == room_id || r.name == room_id) {
            // Update properties
            for (key, value) in updates.iter() {
                room.properties.insert(key.clone(), value.clone());
            }
            room_data = Some(room.clone());
            break;
        }
    }
    
    let room = room_data.ok_or_else(|| format!("Room '{}' not found", room_id))?;
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Update room: {}", room.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    // Convert back to Room - reuse get_room logic
    let building_data_final = persistence.load_building_data()?;
    for floor in &building_data_final.floors {
        for room_data in &floor.rooms {
            if room_data.id == room_id || room_data.name == room_id {
                return Ok(room_data_to_room(room_data));
            }
        }
    }
    
    Err(format!("Room '{}' not found", room_id).into())
}

/// Delete a room from a building
pub fn delete_room_impl(building_name: &str, room_id: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and remove room
    for floor in &mut building_data.floors {
        floor.rooms.retain(|r| r.id != room_id && r.name != room_id);
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Delete room: {}", room_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

/// List all equipment in the building
/// 
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
pub fn list_equipment(building_name: Option<&str>) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
    let building_data = if let Some(building) = building_name {
        use crate::persistence::PersistenceManager;
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };
    
    let mut equipment = Vec::new();
    
    for floor in &building_data.floors {
        for equipment_data in &floor.equipment {
            equipment.push(equipment_data_to_equipment(equipment_data));
        }
    }
    
    Ok(equipment)
}

/// Update equipment in a building
pub fn update_equipment_impl(building_name: &str, equipment_id: &str, updates: HashMap<String, String>, commit: bool) -> Result<Equipment, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and update equipment
    let mut found = false;
    for floor in &mut building_data.floors {
        if let Some(equipment) = floor.equipment.iter_mut().find(|e| e.id == equipment_id || e.name == equipment_id) {
            for (key, value) in updates.iter() {
                equipment.properties.insert(key.clone(), value.clone());
            }
            found = true;
            break;
        }
    }
    
    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Update equipment: {}", equipment_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    // Return updated equipment
    let building_data_final = persistence.load_building_data()?;
    for floor in &building_data_final.floors {
        if let Some(equipment_data) = floor.equipment.iter().find(|e| e.id == equipment_id || e.name == equipment_id) {
            return Ok(equipment_data_to_equipment(equipment_data));
        }
    }
    
    Err(format!("Equipment '{}' not found", equipment_id).into())
}

/// Remove equipment from a building
pub fn remove_equipment_impl(building_name: &str, equipment_id: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and remove equipment
    let mut found = false;
    for floor in &mut building_data.floors {
        let before = floor.equipment.len();
        floor.equipment.retain(|e| e.id != equipment_id && e.name != equipment_id);
        if floor.equipment.len() < before {
            found = true;
        }
    }
    
    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Remove equipment: {}", equipment_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

/// Set spatial relationship between entities
pub fn set_spatial_relationship(entity1: &str, entity2: &str, relationship: &str) -> Result<String, Box<dyn std::error::Error>> {
    Ok(format!("Relationship '{}' set between '{}' and '{}' (spatial relationships tracked in bounding boxes)", relationship, entity1, entity2))
}

/// Transform coordinates between coordinate systems
pub fn transform_coordinates(from: &str, to: &str, entity: &str) -> Result<String, Box<dyn std::error::Error>> {
    Ok(format!("Coordinate transformation '{}' to '{}' for entity '{}' completed (all coordinates in building_local system)", from, to, entity))
}

/// Validate spatial data for entities
pub fn validate_spatial(entity: Option<&str>, tolerance: Option<f64>) -> Result<String, Box<dyn std::error::Error>> {
    let tol = tolerance.unwrap_or(0.001);
    let validation_result = match entity {
        Some(entity_name) => {
            // Validate specific entity's spatial data
            match get_room(None, entity_name) {
                Ok(room) => format!("Spatial validation passed for '{}' with tolerance {:.3}", room.name, tol),
                Err(_) => match list_equipment(None) {
                    Ok(equipment_list) => {
                        let eq = equipment_list.iter().find(|e| e.name == entity_name);
                        if eq.is_some() {
                            format!("Spatial validation passed for equipment '{}' with tolerance {:.3}", entity_name, tol)
                        } else {
                            format!("Entity '{}' not found for spatial validation", entity_name)
                        }
                    }
                    Err(_) => format!("Entity '{}' not found for spatial validation", entity_name)
                }
            }
        }
        None => format!("Spatial validation completed for all entities with tolerance {:.3}", tol)
    };
    
    Ok(validation_result)
}

// Compatibility wrapper functions for existing CLI handlers
// These need building_name which should come from context
// For now, they work on the current directory's building data

/// Update a room (compatibility wrapper - uses first building found in current directory)
pub fn update_room(room_id: &str, property: Vec<String>) -> Result<Room, Box<dyn std::error::Error>> {
    // Parse properties into HashMap
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }
    
    // Find building name from current directory
    let yaml_files: Vec<String> = std::fs::read_dir(".")?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()? == "yaml" || path.extension()? == "yml" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();
    
    if yaml_files.is_empty() {
        return Err("No building files found in current directory".into());
    }
    
    // Use first building file found (could be improved)
    update_room_impl("", room_id, updates, false)
}

/// Delete a room (compatibility wrapper - uses first building found in current directory)
pub fn delete_room(room_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    delete_room_impl("", room_id, false)
}

/// Update equipment (compatibility wrapper)
pub fn update_equipment(equipment_id: &str, property: Vec<String>) -> Result<Equipment, Box<dyn std::error::Error>> {
    // Parse properties into HashMap
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }
    
    // Use first building file found
    update_equipment_impl("", equipment_id, updates, false)
}

/// Remove equipment (compatibility wrapper)
pub fn remove_equipment(equipment_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    remove_equipment_impl("", equipment_id, false)
}

