//! Data management command implementations
//!
//! Command implementations for data-related operations including
//! room management, equipment management, and spatial operations.

use super::Command;
use crate::cli::subcommands::{EquipmentCommands, RoomCommands, SpatialCommands};
use crate::core::domain::ArxAddress;
use crate::core::{Dimensions, Position, SpatialProperties};
use crate::core::{
    Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType, Room, RoomType,
};
use std::collections::HashMap;
use std::error::Error;
use std::path::{Path, PathBuf};

fn load_building_from_dir() -> Result<(PathBuf, crate::core::Building), Box<dyn Error>> {
    use crate::persistence::PersistenceManager;
    let pm = PersistenceManager::from_cwd()?;
    let path = pm.building_yaml_path();
    let building = pm.load_building_data()?;
    Ok((path, building))
}

/// Persist a mutated Building through finalize + hard validation + YAML SSOT.
///
/// `path` is the `building.yaml` file path; parent directory is the project root.
fn save_building_to_path(
    path: &Path,
    building: crate::core::Building,
    commit: bool,
    message: &str,
) -> Result<(), Box<dyn Error>> {
    let base = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    crate::ingest::persist_building_at(base, building, commit, Some(message))?;
    Ok(())
}

fn parse_dimensions(input: &str) -> Result<Dimensions, Box<dyn Error>> {
    let cleaned = input.replace('X', "x");
    let parts: Vec<&str> = cleaned.split('x').collect();
    if parts.len() != 3 {
        return Err("Dimensions must be in format WIDTHxDEPTHxHEIGHT".into());
    }

    let width: f64 = parts[0].trim().parse()?;
    let depth: f64 = parts[1].trim().parse()?;
    let height: f64 = parts[2].trim().parse()?;

    Ok(Dimensions {
        width,
        height,
        depth,
    })
}

fn parse_position(input: &str, coordinate_system: &str) -> Result<Position, Box<dyn Error>> {
    let parts: Vec<&str> = input
        .split([',', ' '])
        .filter(|s| !s.trim().is_empty())
        .collect();

    if parts.len() != 3 {
        return Err("Position must be in format x,y,z".into());
    }

    let x: f64 = parts[0].trim().parse()?;
    let y: f64 = parts[1].trim().parse()?;
    let z: f64 = parts[2].trim().parse()?;

    Ok(Position {
        x,
        y,
        z,
        coordinate_system: coordinate_system.to_string(),
    })
}

fn parse_properties(props: &[String]) -> Result<HashMap<String, String>, Box<dyn Error>> {
    let mut map = HashMap::new();
    for prop in props {
        let (key, value) = prop
            .split_once('=')
            .ok_or_else(|| format!("Invalid property '{}'. Use key=value format", prop))?;
        map.insert(key.trim().to_string(), value.trim().to_string());
    }
    Ok(map)
}

fn parse_equipment_type(input: &str) -> Result<EquipmentType, Box<dyn Error>> {
    let normalized = input.trim().to_lowercase();
    let eq_type = match normalized.as_str() {
        "hvac" => EquipmentType::HVAC,
        "electrical" => EquipmentType::Electrical,
        "av" => EquipmentType::AV,
        "furniture" => EquipmentType::Furniture,
        "safety" => EquipmentType::Safety,
        "plumbing" => EquipmentType::Plumbing,
        "network" => EquipmentType::Network,
        _ => EquipmentType::Other(input.to_string()),
    };
    Ok(eq_type)
}

fn parse_equipment_status(input: &str) -> Result<EquipmentStatus, Box<dyn Error>> {
    let normalized = input.trim().to_lowercase();
    match normalized.as_str() {
        "active" => Ok(EquipmentStatus::Active),
        "inactive" => Ok(EquipmentStatus::Inactive),
        "maintenance" => Ok(EquipmentStatus::Maintenance),
        "outoforder" | "out_of_order" | "out-of-order" => Ok(EquipmentStatus::OutOfOrder),
        "unknown" => Ok(EquipmentStatus::Unknown),
        _ => Err(format!("Unknown equipment status: {}", input).into()),
    }
}

fn parse_health_status(input: &str) -> Result<EquipmentHealthStatus, Box<dyn Error>> {
    let normalized = input.trim().to_lowercase();
    match normalized.as_str() {
        "healthy" => Ok(EquipmentHealthStatus::Healthy),
        "warning" => Ok(EquipmentHealthStatus::Warning),
        "critical" => Ok(EquipmentHealthStatus::Critical),
        "unknown" => Ok(EquipmentHealthStatus::Unknown),
        _ => Err(format!("Unknown health status: {}", input).into()),
    }
}

fn apply_room_updates(room: &mut Room, props: &[String]) -> Result<(), Box<dyn Error>> {
    for prop in props {
        let (key, value) = prop
            .split_once('=')
            .ok_or_else(|| format!("Invalid property '{}'. Use key=value format", prop))?;

        match key.trim().to_lowercase().as_str() {
            "name" => room.name = value.trim().to_string(),
            "room_type" => room.room_type = value.trim().parse::<RoomType>()?,
            "dimensions" => {
                let dims = parse_dimensions(value.trim())?;
                room.spatial_properties = SpatialProperties::new(
                    room.spatial_properties.position.clone(),
                    dims,
                    room.spatial_properties.coordinate_system.clone(),
                );
            }
            "position" => {
                let pos = parse_position(value.trim(), &room.spatial_properties.coordinate_system)?;
                room.spatial_properties = SpatialProperties::new(
                    pos,
                    room.spatial_properties.dimensions.clone(),
                    room.spatial_properties.coordinate_system.clone(),
                );
            }
            "coordinate_system" => {
                room.spatial_properties.coordinate_system = value.trim().to_string();
            }
            other => {
                room.properties
                    .insert(other.to_string(), value.trim().to_string());
            }
        }
    }
    Ok(())
}

fn apply_equipment_updates(
    equipment: &mut Equipment,
    props: &[String],
    position_override: Option<&str>,
) -> Result<(), Box<dyn Error>> {
    for prop in props {
        let (key, value) = prop
            .split_once('=')
            .ok_or_else(|| format!("Invalid property '{}'. Use key=value format", prop))?;

        match key.trim().to_lowercase().as_str() {
            "name" => equipment.name = value.trim().to_string(),
            "equipment_type" => equipment.equipment_type = parse_equipment_type(value)?,
            "status" => equipment.status = parse_equipment_status(value)?,
            "health_status" => equipment.health_status = Some(parse_health_status(value)?),
            "room" | "room_id" => equipment.room_id = Some(value.trim().to_string()),
            "address" => {
                let parsed = ArxAddress::from_path(value.trim())?;
                parsed.validate()?;
                equipment.address = Some(parsed.clone());
                equipment.path = parsed.path.clone();
            }
            "path" => equipment.path = value.trim().to_string(),
            "coordinate_system" => equipment.position.coordinate_system = value.trim().to_string(),
            "position" => {
                let pos = parse_position(value.trim(), &equipment.position.coordinate_system)?;
                equipment.set_position(pos);
            }
            other => {
                equipment
                    .properties
                    .insert(other.to_string(), value.trim().to_string());
            }
        }
    }

    if let Some(pos_str) = position_override {
        let pos = parse_position(pos_str, &equipment.position.coordinate_system)?;
        equipment.set_position(pos);
    }

    Ok(())
}

/// Room management command dispatcher
pub struct RoomCommand {
    pub subcommand: RoomCommands,
}

impl Command for RoomCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        match &self.subcommand {
            RoomCommands::Create {
                building,
                floor,
                wing,
                name,
                room_type,
                dimensions,
                position,
                commit,
            } => {
                let (path, mut model) = load_building_from_dir()?;
                if model.name != *building {
                    return Err(format!(
                        "Building name mismatch: expected '{}', found '{}'",
                        building, model.name
                    )
                    .into());
                }

                let parsed_room_type: RoomType = room_type.parse()?;
                let mut room = Room::new(name.clone(), parsed_room_type);

                let coordinate_system = "building_local".to_string();
                let mut pos = Position {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                    coordinate_system: coordinate_system.clone(),
                };
                let mut dims = Dimensions {
                    width: 10.0,
                    height: 3.0,
                    depth: 10.0,
                };

                if let Some(pos_str) = position.as_deref() {
                    pos = parse_position(pos_str, &coordinate_system)?;
                }
                if let Some(dim_str) = dimensions.as_deref() {
                    dims = parse_dimensions(dim_str)?;
                }

                room.spatial_properties = SpatialProperties::new(pos, dims, coordinate_system);

                let floor_ref = if let Some(floor_ref) = model.find_floor_mut(*floor) {
                    floor_ref
                } else {
                    let new_floor = crate::core::Floor::new(format!("Floor {}", floor), *floor);
                    model.add_floor(new_floor);
                    model
                        .find_floor_mut(*floor)
                        .ok_or_else(|| format!("Failed to create floor {}", floor))?
                };

                if !floor_ref.wings.iter().any(|w| w.name == *wing) {
                    let new_wing = crate::core::Wing::new(wing.to_string());
                    floor_ref.wings.push(new_wing);
                }

                let wing_ref = floor_ref
                    .wings
                    .iter_mut()
                    .find(|w| w.name == *wing)
                    .ok_or_else(|| format!("Failed to find wing '{}'", wing))?;

                wing_ref.rooms.push(room.clone());

                save_building_to_path(&path, model, *commit, &format!("Add room: {}", room.name))?;

                println!("✅ Created room: {}", room.name);
                Ok(())
            }
            RoomCommands::List {
                building,
                floor,
                wing,
                verbose,
                interactive,
            } => {
                if *interactive {
                    return Err("Interactive room explorer requires --features tui".into());
                }

                let (_path, model) = load_building_from_dir()?;
                if let Some(ref b) = building {
                    if model.name != *b {
                        return Err(format!(
                            "Building name mismatch: expected '{}', found '{}'",
                            b, model.name
                        )
                        .into());
                    }
                }

                let mut rooms: Vec<&Room> = Vec::new();
                for floor_ref in &model.floors {
                    if let Some(level) = floor {
                        if floor_ref.level != *level {
                            continue;
                        }
                    }

                    for wing_ref in &floor_ref.wings {
                        if let Some(wing_name) = wing {
                            if wing_ref.name != *wing_name {
                                continue;
                            }
                        }
                        rooms.extend(wing_ref.rooms.iter());
                    }
                }

                if rooms.is_empty() {
                    println!("📋 No rooms found");
                    return Ok(());
                }

                println!("📋 Rooms ({} total)", rooms.len());
                for room in rooms {
                    if *verbose {
                        println!("- {} ({})", room.name, room.room_type);
                        println!("  id: {}", room.id);
                        println!("  equipment: {}", room.equipment.len());
                    } else {
                        println!("- {}", room.name);
                    }
                }

                Ok(())
            }
            RoomCommands::Show { room, equipment } => {
                let (_path, model) = load_building_from_dir()?;

                let mut found_room: Option<&Room> = None;
                for floor_ref in &model.floors {
                    for wing_ref in &floor_ref.wings {
                        if let Some(r) = wing_ref.rooms.iter().find(|r| {
                            r.name.eq_ignore_ascii_case(room) || r.id.eq_ignore_ascii_case(room)
                        }) {
                            found_room = Some(r);
                            break;
                        }
                    }
                    if found_room.is_some() {
                        break;
                    }
                }

                let room_ref = found_room.ok_or_else(|| format!("Room '{}' not found", room))?;
                println!("🔍 Room details: {}", room_ref.name);
                println!("   ID: {}", room_ref.id);
                println!("   Type: {}", room_ref.room_type);
                println!("   Equipment count: {}", room_ref.equipment.len());

                if *equipment {
                    for eq in &room_ref.equipment {
                        println!("   - {} ({})", eq.name, eq.equipment_type);
                    }
                }

                Ok(())
            }
            RoomCommands::Update {
                room,
                property,
                commit,
            } => {
                let (path, mut model) = load_building_from_dir()?;

                let mut updated_room = None;
                for floor_ref in &mut model.floors {
                    for wing_ref in &mut floor_ref.wings {
                        if let Some(room_ref) = wing_ref.rooms.iter_mut().find(|r| {
                            r.name.eq_ignore_ascii_case(room) || r.id.eq_ignore_ascii_case(room)
                        }) {
                            apply_room_updates(room_ref, property)?;
                            updated_room = Some(room_ref.clone());
                            break;
                        }
                    }
                    if updated_room.is_some() {
                        break;
                    }
                }

                let updated = updated_room.ok_or_else(|| format!("Room '{}' not found", room))?;

                save_building_to_path(
                    &path,
                    model,
                    *commit,
                    &format!("Update room: {}", updated.name),
                )?;

                println!("✅ Updated room: {}", updated.name);
                Ok(())
            }
            RoomCommands::Delete { confirm, .. } => {
                if !confirm {
                    return Err("Room deletion requires --confirm flag".into());
                }

                if let RoomCommands::Delete { room, commit, .. } = &self.subcommand {
                    let (path, mut model) = load_building_from_dir()?;

                    let mut removed = false;
                    for floor_ref in &mut model.floors {
                        for wing_ref in &mut floor_ref.wings {
                            let before = wing_ref.rooms.len();
                            wing_ref.rooms.retain(|r| {
                                !r.name.eq_ignore_ascii_case(room)
                                    && !r.id.eq_ignore_ascii_case(room)
                            });
                            if wing_ref.rooms.len() < before {
                                removed = true;
                            }
                        }
                    }

                    if !removed {
                        return Err(format!("Room '{}' not found", room).into());
                    }

                    save_building_to_path(
                        &path,
                        model,
                        *commit,
                        &format!("Delete room: {}", room),
                    )?;

                    println!("✅ Deleted room: {}", room);
                    Ok(())
                } else {
                    Err("Invalid room delete arguments".into())
                }
            }
        }
    }

    fn name(&self) -> &'static str {
        "room"
    }
}

/// Equipment management command dispatcher
pub struct EquipmentCommand {
    pub subcommand: EquipmentCommands,
}

impl Command for EquipmentCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        match &self.subcommand {
            EquipmentCommands::Add {
                room,
                name,
                equipment_type,
                position,
                at,
                property,
                commit,
            } => {
                let (path, mut model) = load_building_from_dir()?;

                let eq_type = parse_equipment_type(equipment_type)?;
                let mut equipment = Equipment::new(
                    name.clone(),
                    at.clone().unwrap_or_else(|| "/".to_string()),
                    eq_type,
                );

                if let Some(addr) = at {
                    let parsed = ArxAddress::from_path(addr)?;
                    parsed.validate()?;
                    equipment.address = Some(parsed.clone());
                    equipment.path = parsed.path.clone();
                }

                if let Some(pos_str) = position.as_deref() {
                    let pos = parse_position(pos_str, &equipment.position.coordinate_system)?;
                    equipment.set_position(pos);
                }

                equipment.properties = parse_properties(property)?;

                let mut added = false;
                for floor_ref in &mut model.floors {
                    for wing_ref in &mut floor_ref.wings {
                        if let Some(room_ref) = wing_ref
                            .rooms
                            .iter_mut()
                            .find(|r| r.name == *room || r.id == *room)
                        {
                            equipment.room_id = Some(room_ref.id.clone());
                            room_ref.add_equipment(equipment.clone());
                            added = true;
                            break;
                        }
                    }
                    if added {
                        break;
                    }
                }

                if !added {
                    return Err(format!("Room '{}' not found", room).into());
                }

                save_building_to_path(
                    &path,
                    model,
                    *commit,
                    &format!("Add equipment: {}", equipment.name),
                )?;

                println!("✅ Added equipment: {}", equipment.name);
                Ok(())
            }
            EquipmentCommands::List {
                room,
                equipment_type,
                verbose,
                interactive,
            } => {
                if *interactive {
                    return Err("Interactive equipment browser requires --features tui".into());
                }

                let (_path, model) = load_building_from_dir()?;
                let all = model.get_all_equipment();
                let items: Vec<&Equipment> = all
                    .into_iter()
                    .filter(|eq| {
                        if let Some(ref r) = room {
                            let mut in_room = false;
                            for floor in &model.floors {
                                for wing in &floor.wings {
                                    for rm in &wing.rooms {
                                        if (rm.name.eq_ignore_ascii_case(r)
                                            || rm.id.eq_ignore_ascii_case(r))
                                            && rm.equipment.iter().any(|e| e.id == eq.id)
                                        {
                                            in_room = true;
                                        }
                                    }
                                }
                            }
                            if !in_room
                                && !eq
                                    .room_id
                                    .as_deref()
                                    .map(|id| id.eq_ignore_ascii_case(r))
                                    .unwrap_or(false)
                            {
                                return false;
                            }
                        }
                        if let Some(ref t) = equipment_type {
                            if eq.equipment_type.to_string().to_lowercase() != t.to_lowercase() {
                                return false;
                            }
                        }
                        true
                    })
                    .collect();

                if items.is_empty() {
                    println!("📋 No equipment found");
                    return Ok(());
                }

                println!("📋 Equipment ({} total)", items.len());
                for eq in items {
                    if *verbose {
                        println!("- {} ({})", eq.name, eq.equipment_type);
                        println!("  id: {}", eq.id);
                        if let Some(addr) = &eq.address {
                            println!("  address: {}", addr.path);
                        }
                    } else {
                        println!("- {}", eq.name);
                    }
                }

                Ok(())
            }
            EquipmentCommands::Update {
                equipment,
                property,
                position,
                commit,
            } => {
                let (path, mut model) = load_building_from_dir()?;

                let updated = if let Some(eq) = model.find_equipment_mut(equipment) {
                    apply_equipment_updates(eq, property, position.as_deref())?;
                    Some(eq.clone())
                } else {
                    None
                };

                let updated_eq =
                    updated.ok_or_else(|| format!("Equipment '{}' not found", equipment))?;

                save_building_to_path(
                    &path,
                    model,
                    *commit,
                    &format!("Update equipment: {}", updated_eq.name),
                )?;

                println!("✅ Updated equipment: {}", updated_eq.name);
                Ok(())
            }
            EquipmentCommands::Remove { confirm, .. } => {
                if !confirm {
                    return Err("Equipment removal requires --confirm flag".into());
                }

                if let EquipmentCommands::Remove {
                    equipment, commit, ..
                } = &self.subcommand
                {
                    let (path, mut model) = load_building_from_dir()?;

                    let before = model.get_all_equipment().len();
                    for floor_ref in &mut model.floors {
                        floor_ref.equipment.retain(|e| {
                            !e.id.eq_ignore_ascii_case(equipment)
                                && !e.name.eq_ignore_ascii_case(equipment)
                        });
                        for wing_ref in &mut floor_ref.wings {
                            wing_ref.equipment.retain(|e| {
                                !e.id.eq_ignore_ascii_case(equipment)
                                    && !e.name.eq_ignore_ascii_case(equipment)
                            });
                            for room_ref in &mut wing_ref.rooms {
                                room_ref.equipment.retain(|e| {
                                    !e.id.eq_ignore_ascii_case(equipment)
                                        && !e.name.eq_ignore_ascii_case(equipment)
                                });
                            }
                        }
                    }
                    let removed = model.get_all_equipment().len() < before;

                    if !removed {
                        return Err(format!("Equipment '{}' not found", equipment).into());
                    }

                    save_building_to_path(
                        &path,
                        model,
                        *commit,
                        &format!("Remove equipment: {}", equipment),
                    )?;

                    println!("✅ Removed equipment: {}", equipment);
                    Ok(())
                } else {
                    Err("Invalid equipment remove arguments".into())
                }
            }
        }
    }

    fn name(&self) -> &'static str {
        "equipment"
    }
}

/// Spatial operations command dispatcher
pub struct SpatialCommand {
    pub subcommand: SpatialCommands,
}

impl Command for SpatialCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        use crate::core::operations::spatial::{
            spatial_query, transform_coordinates, validate_spatial,
        };
        use crate::persistence::load_building_at;
        use std::path::Path;

        match &self.subcommand {
            SpatialCommands::Query {
                query_type,
                entity,
                params,
            } => {
                let building = load_building_at(Path::new("."))
                    .map_err(|e| format!("load building.yaml: {}", e))?;
                let results = spatial_query(&building, query_type, entity, params.clone())?;
                if results.is_empty() {
                    println!("No spatial matches for query type '{}'", query_type);
                } else {
                    for r in &results {
                        println!(
                            "{} ({}) dist={:.3} @ ({:.2},{:.2},{:.2})",
                            r.entity_name,
                            r.entity_type,
                            r.distance,
                            r.position.x,
                            r.position.y,
                            r.position.z
                        );
                    }
                    println!("Total: {} result(s)", results.len());
                }
                Ok(())
            }
            SpatialCommands::Transform { from, to, entity } => {
                let building = load_building_at(Path::new("."))
                    .map_err(|e| format!("load building.yaml: {}", e))?;
                let msg = transform_coordinates(&building, from, to, entity)?;
                println!("{}", msg);
                Ok(())
            }
            SpatialCommands::Validate { entity, tolerance } => {
                let building = load_building_at(Path::new("."))
                    .map_err(|e| format!("load building.yaml: {}", e))?;
                let result =
                    validate_spatial(&building, entity.as_deref(), *tolerance)?;
                println!(
                    "Spatial validation: checked={} issues={} valid={}",
                    result.entities_checked, result.issues_found, result.is_valid
                );
                for issue in &result.issues {
                    println!(
                        "  [{}] {} ({}): {}",
                        issue.severity, issue.entity_name, issue.issue_type, issue.message
                    );
                }
                if result.is_valid {
                    Ok(())
                } else {
                    Err("Spatial validation found issues".into())
                }
            }
        }
    }

    fn name(&self) -> &'static str {
        "spatial"
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serial_test::serial;
    use tempfile::tempdir;

    #[test]
    #[serial]
    fn test_room_create_command() {
        let tmp = tempdir().expect("tempdir");
        let dir = tmp.path();

        let building =
            crate::core::Building::new("My Building".to_string(), "/building".to_string());
        crate::persistence::save_building_at(dir, &building).expect("write building.yaml");

        let original_dir = std::env::current_dir().unwrap_or_else(|_| {
            let manifest_dir =
                std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR env var");
            let path = PathBuf::from(manifest_dir);
            let _ = std::env::set_current_dir(&path);
            path
        });
        std::env::set_current_dir(dir).expect("set_current_dir");

        let cmd = RoomCommand {
            subcommand: RoomCommands::Create {
                building: "My Building".to_string(),
                floor: 1,
                wing: "north".to_string(),
                name: "conference-room".to_string(),
                room_type: "Office".to_string(),
                dimensions: Some("10x12x3".to_string()),
                position: Some("0,0,0".to_string()),
                commit: false,
            },
        };

        assert_eq!(cmd.name(), "room");
        assert!(cmd.execute().is_ok());

        let building =
            crate::persistence::load_building_data_from_dir().expect("load building data");
        assert_eq!(building.floors.len(), 1);
        assert_eq!(building.floors[0].wings.len(), 1);
        assert_eq!(building.floors[0].wings[0].rooms.len(), 1);

        std::env::set_current_dir(&original_dir).expect("restore current_dir");
    }

    #[test]
    #[serial]
    fn test_equipment_add_command() {
        let tmp = tempdir().expect("tempdir");
        let dir = tmp.path();

        let building =
            crate::core::Building::new("My Building".to_string(), "/building".to_string());
        crate::persistence::save_building_at(dir, &building).expect("write building.yaml");

        let original_dir = std::env::current_dir().unwrap_or_else(|_| {
            let manifest_dir =
                std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR env var");
            let path = PathBuf::from(manifest_dir);
            let _ = std::env::set_current_dir(&path);
            path
        });
        std::env::set_current_dir(dir).expect("set_current_dir");

        let room_cmd = RoomCommand {
            subcommand: RoomCommands::Create {
                building: "My Building".to_string(),
                floor: 1,
                wing: "north".to_string(),
                name: "conference-room".to_string(),
                room_type: "Office".to_string(),
                dimensions: Some("10x12x3".to_string()),
                position: Some("0,0,0".to_string()),
                commit: false,
            },
        };
        room_cmd.execute().expect("create room");

        let cmd = EquipmentCommand {
            subcommand: EquipmentCommands::Add {
                room: "conference-room".to_string(),
                name: "projector-01".to_string(),
                equipment_type: "AV".to_string(),
                position: Some("5,6,2.5".to_string()),
                at: Some("/usa/ny/brooklyn/ps-118/floor-02/conference/projector-01".to_string()),
                property: vec!["brand=Epson".to_string()],
                commit: false,
            },
        };

        assert_eq!(cmd.name(), "equipment");
        assert!(cmd.execute().is_ok());

        let building =
            crate::persistence::load_building_data_from_dir().expect("load building data");
        let eq_count = building.get_all_equipment().len();
        assert_eq!(eq_count, 1);

        std::env::set_current_dir(&original_dir).expect("restore current_dir");
    }

    #[test]
    fn test_spatial_command_name() {
        let cmd = SpatialCommand {
            subcommand: SpatialCommands::Validate {
                entity: None,
                tolerance: None,
            },
        };
        assert_eq!(cmd.name(), "spatial");
    }
}
