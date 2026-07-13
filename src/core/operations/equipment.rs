//! Equipment CRUD operations
//!
//! Mutates `core::Building` then persists via `ingest::persist_building_at`
//! using the same base path as the load.

use crate::core::Equipment;
use crate::ingest::persist_building_at;
use crate::persistence::{load_building_data_from_dir, PersistenceManager};
use std::collections::HashMap;

/// Add equipment to a room or floor
pub fn add_equipment(
    building_name: &str,
    room_name: Option<&str>,
    equipment: Equipment,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let persistence = PersistenceManager::new(building_name)?;
    let base = persistence.base_path().to_path_buf();
    let mut building = persistence.load_building_data()?;
    let eq_name = equipment.name.clone();

    if let Some(room_name) = room_name {
        let mut added = false;
        for floor in &mut building.floors {
            for wing in &mut floor.wings {
                if let Some(room) = wing
                    .rooms
                    .iter_mut()
                    .find(|r| r.name == room_name || r.id == room_name)
                {
                    room.equipment.push(equipment.clone());
                    added = true;
                    break;
                }
            }
            if added {
                break;
            }
        }
        if !added {
            return Err(format!("Room '{}' not found", room_name).into());
        }
    } else if let Some(floor) = building.floors.first_mut() {
        floor.equipment.push(equipment.clone());
    } else {
        return Err("Building has no floors to attach equipment".into());
    }

    persist_building_at(
        base,
        building,
        commit,
        Some(&format!("Add equipment: {}", eq_name)),
    )?;
    Ok(())
}

/// List all equipment in the building
pub fn list_equipment(
    building_name: Option<&str>,
) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
    let building = if let Some(b) = building_name {
        PersistenceManager::new(b)?.load_building_data()?
    } else {
        load_building_data_from_dir()?
    };

    Ok(building.get_all_equipment().into_iter().cloned().collect())
}

/// Update equipment in a building
pub fn update_equipment_impl(
    building_name: &str,
    equipment_id: &str,
    updates: HashMap<String, String>,
    commit: bool,
) -> Result<Equipment, Box<dyn std::error::Error>> {
    let persistence = PersistenceManager::new(building_name)?;
    let base = persistence.base_path().to_path_buf();
    let mut building = persistence.load_building_data()?;

    let equipment = building
        .find_equipment_mut(equipment_id)
        .ok_or_else(|| format!("Equipment '{}' not found", equipment_id))?;
    for (key, value) in updates.iter() {
        equipment.properties.insert(key.clone(), value.clone());
    }
    let updated = equipment.clone();

    let building = persist_building_at(
        base,
        building,
        commit,
        Some(&format!("Update equipment: {}", equipment_id)),
    )?;

    building
        .find_equipment(equipment_id)
        .cloned()
        .or(Some(updated))
        .ok_or_else(|| format!("Equipment '{}' not found after save", equipment_id).into())
}

/// Remove equipment from a building
pub fn remove_equipment_impl(
    building_name: &str,
    equipment_id: &str,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let persistence = PersistenceManager::new(building_name)?;
    let base = persistence.base_path().to_path_buf();
    let mut building = persistence.load_building_data()?;

    let mut found = false;
    for floor in &mut building.floors {
        let before = floor.equipment.len();
        floor
            .equipment
            .retain(|e| e.id != equipment_id && e.name != equipment_id);
        if floor.equipment.len() < before {
            found = true;
        }
        for wing in &mut floor.wings {
            let before = wing.equipment.len();
            wing.equipment
                .retain(|e| e.id != equipment_id && e.name != equipment_id);
            if wing.equipment.len() < before {
                found = true;
            }
            for room in &mut wing.rooms {
                let before = room.equipment.len();
                room.equipment
                    .retain(|e| e.id != equipment_id && e.name != equipment_id);
                if room.equipment.len() < before {
                    found = true;
                }
            }
        }
    }

    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }

    persist_building_at(
        base,
        building,
        commit,
        Some(&format!("Remove equipment: {}", equipment_id)),
    )?;
    Ok(())
}

/// Update equipment (loads Building from cwd)
pub fn update_equipment(
    equipment_id: &str,
    property: Vec<String>,
) -> Result<Equipment, Box<dyn std::error::Error>> {
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }

    let building = load_building_data_from_dir()?;
    let building_name = building.name.clone();
    update_equipment_impl(&building_name, equipment_id, updates, false)
}

/// Remove equipment (loads Building from cwd)
pub fn remove_equipment(equipment_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    let building = load_building_data_from_dir()?;
    let building_name = building.name.clone();
    remove_equipment_impl(&building_name, equipment_id, false)
}
