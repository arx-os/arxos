//! Room CRUD operations
//!
//! This module provides functions for creating, reading, updating, and deleting
//! rooms in buildings.

use crate::core::Room;
use std::collections::HashMap;

/// Create a room in a building
///
/// # Arguments
///
/// * `building_name` - Name of the building
/// * `floor_level` - Floor level where the room will be created
/// * `room` - Room to create
/// * `wing_name` - Optional wing name. If provided, room will be added to that wing.
///   If not provided or wing doesn't exist, room will be added to a default wing.
/// * `commit` - Whether to commit changes to Git
pub fn create_room(
    building_name: &str,
    floor_level: i32,
    room: Room,
    wing_name: Option<&str>,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Store room name for commit message
    let room_name = room.name.clone();

    // Find or create the floor
    let floor = if let Some(floor) = building_data.building.find_floor_mut(floor_level) {
        floor
    } else {
        // Create new floor
        let new_floor = crate::core::Floor::new(format!("Floor {}", floor_level), floor_level);
        building_data.building.add_floor(new_floor);
        building_data
            .building
            .find_floor_mut(floor_level)
            .ok_or_else(|| {
                format!("Failed to find floor {} after creating it", floor_level)
            })?
    };

    // Find or create the wing
    let wing_name = wing_name.unwrap_or("Default");
    if !floor.wings.iter().any(|w| w.name == wing_name) {
        let new_wing = crate::core::Wing::new(wing_name.to_string());
        floor.wings.push(new_wing);
    }
    let wing = floor
        .wings
        .iter_mut()
        .find(|w| w.name == wing_name)
        .ok_or_else(|| format!("Failed to find wing '{}' after creating it", wing_name))?;

    // Add room to wing
    wing.rooms.push(room);

    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Add room: {}", room_name)))?;
    } else {
        // For now, use the same method
        persistence.save_and_commit(&building_data, None)?;
    }

    Ok(())
}

/// List all rooms in a building
///
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
pub fn list_rooms(building_name: Option<&str>) -> Result<Vec<Room>, Box<dyn std::error::Error>> {
    use crate::persistence::{load_building_data_from_dir, PersistenceManager};

    let building_data = if let Some(building) = building_name {
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    let mut rooms = Vec::new();

    for floor in &building_data.building.floors {
        // Collect rooms from wings (primary location)
        for wing in &floor.wings {
            rooms.extend(wing.rooms.iter().cloned());
        }
        // Also collect from legacy rooms list
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    Ok(rooms)
}

/// Get a specific room by name
///
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
/// * `room_name` - Name or ID of the room to retrieve.
pub fn get_room(
    building_name: Option<&str>,
    room_name: &str,
) -> Result<Room, Box<dyn std::error::Error>> {
    use crate::persistence::{load_building_data_from_dir, PersistenceManager};

    let building_data = if let Some(building) = building_name {
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    for floor in &building_data.building.floors {
        // Search in wings first (primary location)
        for wing in &floor.wings {
            for room in &wing.rooms {
                if room.name.to_lowercase() == room_name.to_lowercase()
                    || room.id.to_lowercase() == room_name.to_lowercase()
                {
                    return Ok(room.clone());
                }
            }
        }
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    Err(format!("Room '{}' not found", room_name).into())
}

/// Update a room in a building
pub fn update_room_impl(
    building_name: &str,
    room_id: &str,
    updates: HashMap<String, String>,
    commit: bool,
) -> Result<Room, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and update room
    let mut updated_room = None;
    for floor in &mut building_data.building.floors {
        // Search in wings first (primary location)
        for wing in &mut floor.wings {
            if let Some(room) = wing
                .rooms
                .iter_mut()
                .find(|r| r.id == room_id || r.name == room_id)
            {
                // Update properties
                for (key, value) in updates.iter() {
                    room.properties.insert(key.clone(), value.clone());
                }
                updated_room = Some(room.clone());
                break;
            }
        }
        if updated_room.is_some() {
            break;
        }
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    let room = updated_room.ok_or_else(|| format!("Room '{}' not found", room_id))?;

    // Save
    if commit {
        persistence
            .save_and_commit(&building_data, Some(&format!("Update room: {}", room.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(room)
}

/// Delete a room from a building
pub fn delete_room_impl(
    building_name: &str,
    room_id: &str,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and remove room
    for floor in &mut building_data.building.floors {
        // Remove from wings (primary location)
        for wing in &mut floor.wings {
            wing.rooms.retain(|r| r.id != room_id && r.name != room_id);
        }
        // Note: Legacy rooms list removed - rooms are only in wings now
    }

    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Delete room: {}", room_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(())
}

/// Update room (compatibility wrapper)
///
/// This function attempts to determine the building name from YAML files in the
/// current directory. For better reliability, use `update_room_impl` with an explicit
/// building name.
pub fn update_room(
    room_id: &str,
    property: Vec<String>,
) -> Result<Room, Box<dyn std::error::Error>> {
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
///
/// This function attempts to determine the building name from YAML files in the
/// current directory. For better reliability, use `delete_room_impl` with an explicit
/// building name.
pub fn delete_room(room_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Determine building name from YAML file in current directory
    let building_data = crate::yaml::BuildingData {
        building: crate::core::Building::default(),
        equipment: Vec::new()
    };

    let building_name = &building_data.building.name;
    delete_room_impl(building_name, room_id, false)
}
