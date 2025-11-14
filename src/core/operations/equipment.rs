//! Equipment CRUD operations
//!
//! This module provides functions for creating, reading, updating, and deleting
//! equipment in buildings.

use crate::core::Equipment;
use std::collections::HashMap;

/// Add equipment to a room or floor
///
/// # Arguments
///
/// * `building_name` - Name of the building
/// * `room_name` - Optional room name. If provided, equipment will be added to that room.
///   If not provided, equipment will be added to floor-level equipment.
/// * `equipment` - Equipment to add
/// * `commit` - Whether to commit changes to Git
pub fn add_equipment(
    building_name: &str,
    room_name: Option<&str>,
    equipment: Equipment,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find room if specified
    if let Some(room_name) = room_name {
        for floor in &mut building_data.building.floors {
            // Search in wings first (primary location)
            for wing in &mut floor.wings {
                if let Some(room) = wing.rooms.iter_mut().find(|r| r.name == room_name) {
                    // Add equipment to room
                    room.equipment.push(equipment.clone());
                    // Also add to floor's equipment list
                    floor.equipment.push(equipment.clone());
                    break;
                }
            }
            // Note: Legacy rooms list removed - rooms are only in wings now
        }
    } else {
        // Add to floor-level equipment if no room specified
        if let Some(floor) = building_data.building.floors.first_mut() {
            floor.equipment.push(equipment.clone());
        }
    }

    // Save
    if commit {
        persistence.save_and_commit(
            &building_data,
            Some(&format!("Add equipment: {}", equipment.name)),
        )?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(())
}

/// List all equipment in the building
///
/// # Arguments
/// * `building_name` - Optional building name to filter by. If None, loads from current directory.
pub fn list_equipment(
    building_name: Option<&str>,
) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
    use crate::persistence::{load_building_data_from_dir, PersistenceManager};

    let building_data = if let Some(building) = building_name {
        let persistence = PersistenceManager::new(building)?;
        persistence.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    let mut equipment = Vec::new();

    for floor in &building_data.building.floors {
        equipment.extend(floor.equipment.iter().cloned());
    }

    Ok(equipment)
}

/// Update equipment in a building
pub fn update_equipment_impl(
    building_name: &str,
    equipment_id: &str,
    updates: HashMap<String, String>,
    commit: bool,
) -> Result<Equipment, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and update equipment
    let mut found = false;
    for floor in &mut building_data.building.floors {
        if let Some(equipment) = floor
            .equipment
            .iter_mut()
            .find(|e| e.id == equipment_id || e.name == equipment_id)
        {
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

    // Get the updated equipment before saving
    let updated_equipment = {
        let mut found_equipment = None;
        for floor in &building_data.building.floors {
            if let Some(equipment) = floor
                .equipment
                .iter()
                .find(|e| e.id == equipment_id || e.name == equipment_id)
            {
                found_equipment = Some(equipment.clone());
                break;
            }
        }
        found_equipment.ok_or_else(|| format!("Equipment '{}' not found", equipment_id))?
    };

    // Save
    if commit {
        persistence.save_and_commit(
            &building_data,
            Some(&format!("Update equipment: {}", equipment_id)),
        )?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(updated_equipment)
}

/// Remove equipment from a building
pub fn remove_equipment_impl(
    building_name: &str,
    equipment_id: &str,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;

    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and remove equipment
    let mut found = false;
    for floor in &mut building_data.building.floors {
        let before = floor.equipment.len();
        floor
            .equipment
            .retain(|e| e.id != equipment_id && e.name != equipment_id);
        if floor.equipment.len() < before {
            found = true;
        }
    }

    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }

    // Save
    if commit {
        persistence.save_and_commit(
            &building_data,
            Some(&format!("Remove equipment: {}", equipment_id)),
        )?;
    } else {
        persistence.save_building_data(&building_data)?;
    }

    Ok(())
}

/// Update equipment (compatibility wrapper)
///
/// This function attempts to determine the building name from YAML files in the
/// current directory. For better reliability, use `update_equipment_impl` with an explicit
/// building name.
pub fn update_equipment(
    equipment_id: &str,
    property: Vec<String>,
) -> Result<Equipment, Box<dyn std::error::Error>> {
    

    // Parse properties into HashMap
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }

    // Determine building name from YAML file in current directory
    let building_data = crate::yaml::BuildingData {
        building: crate::core::Building::default(),
        equipment: Vec::new()
    };

    let building_name = &building_data.building.name;
    update_equipment_impl(building_name, equipment_id, updates, false)
}

/// Remove equipment (compatibility wrapper)
///
/// This function attempts to determine the building name from YAML files in the
/// current directory. For better reliability, use `remove_equipment_impl` with an explicit
/// building name.
pub fn remove_equipment(equipment_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Determine building name from YAML file in current directory
    let building_data = crate::yaml::BuildingData {
        building: crate::core::Building::default(),
        equipment: Vec::new()
    };

    let building_name = &building_data.building.name;
    remove_equipment_impl(building_name, equipment_id, false)
}
