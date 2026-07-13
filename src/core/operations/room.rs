//! Room CRUD operations
//!
//! Mutates `core::Building` then persists via `ingest::persist_building_at`
//! using the same base path as the load (no silent cwd split).

use crate::core::Room;
use crate::ingest::persist_building_at;
use crate::persistence::{load_building_data_from_dir, PersistenceManager};
use std::collections::HashMap;

/// Create a room in a building
pub fn create_room(
    building_name: &str,
    floor_level: i32,
    room: Room,
    wing_name: Option<&str>,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let persistence = PersistenceManager::new(building_name)?;
    let base = persistence.base_path().to_path_buf();
    let mut building = persistence.load_building_data()?;
    let room_name = room.name.clone();

    let floor = if let Some(floor) = building.find_floor_mut(floor_level) {
        floor
    } else {
        let new_floor = crate::core::Floor::new(format!("Floor {}", floor_level), floor_level);
        building.add_floor(new_floor);
        building
            .find_floor_mut(floor_level)
            .ok_or_else(|| format!("Failed to find floor {} after creating it", floor_level))?
    };

    let wing_name = wing_name.unwrap_or("Default");
    if !floor.wings.iter().any(|w| w.name == wing_name) {
        floor
            .wings
            .push(crate::core::Wing::new(wing_name.to_string()));
    }
    let wing = floor
        .wings
        .iter_mut()
        .find(|w| w.name == wing_name)
        .ok_or_else(|| format!("Failed to find wing '{}'", wing_name))?;

    wing.rooms.push(room);

    persist_building_at(
        base,
        building,
        commit,
        Some(&format!("Add room: {}", room_name)),
    )?;
    Ok(())
}

/// List all rooms in a building
pub fn list_rooms(building_name: Option<&str>) -> Result<Vec<Room>, Box<dyn std::error::Error>> {
    let building = if let Some(b) = building_name {
        PersistenceManager::new(b)?.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    let mut rooms = Vec::new();
    for floor in &building.floors {
        for wing in &floor.wings {
            rooms.extend(wing.rooms.iter().cloned());
        }
    }
    Ok(rooms)
}

/// Get a specific room by name or id
pub fn get_room(
    building_name: Option<&str>,
    room_name: &str,
) -> Result<Room, Box<dyn std::error::Error>> {
    let building = if let Some(b) = building_name {
        PersistenceManager::new(b)?.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    for floor in &building.floors {
        for wing in &floor.wings {
            for room in &wing.rooms {
                if room.name.eq_ignore_ascii_case(room_name)
                    || room.id.eq_ignore_ascii_case(room_name)
                {
                    return Ok(room.clone());
                }
            }
        }
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
    let persistence = PersistenceManager::new(building_name)?;
    let base = persistence.base_path().to_path_buf();
    let mut building = persistence.load_building_data()?;

    let room = building
        .find_room_mut(room_id)
        .ok_or_else(|| format!("Room '{}' not found", room_id))?;
    for (key, value) in updates.iter() {
        room.properties.insert(key.clone(), value.clone());
    }
    let updated_room = room.clone();

    let building = persist_building_at(
        base,
        building,
        commit,
        Some(&format!("Update room: {}", updated_room.name)),
    )?;

    building
        .find_room(room_id)
        .cloned()
        .or(Some(updated_room))
        .ok_or_else(|| format!("Room '{}' not found after save", room_id).into())
}

/// Delete a room from a building
pub fn delete_room_impl(
    building_name: &str,
    room_id: &str,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let persistence = PersistenceManager::new(building_name)?;
    let base = persistence.base_path().to_path_buf();
    let mut building = persistence.load_building_data()?;

    for floor in &mut building.floors {
        for wing in &mut floor.wings {
            wing.rooms.retain(|r| r.id != room_id && r.name != room_id);
        }
    }

    persist_building_at(
        base,
        building,
        commit,
        Some(&format!("Delete room: {}", room_id)),
    )?;
    Ok(())
}

/// Update room (loads Building from cwd)
pub fn update_room(
    room_id: &str,
    property: Vec<String>,
) -> Result<Room, Box<dyn std::error::Error>> {
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }

    let building = load_building_data_from_dir()?;
    let building_name = building.name.clone();
    update_room_impl(&building_name, room_id, updates, false)
}

/// Delete room (loads Building from cwd)
pub fn delete_room(room_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    let building = load_building_data_from_dir()?;
    let building_name = building.name.clone();
    delete_room_impl(&building_name, room_id, false)
}
