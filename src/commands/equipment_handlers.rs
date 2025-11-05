// Equipment management command handlers

use crate::cli::EquipmentCommands;
use crate::core::EquipmentType;
use crate::persistence::PersistenceManager;
use crate::spatial::Point3D;

/// Handle equipment management commands
pub fn handle_equipment_command(command: EquipmentCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        EquipmentCommands::Add { room, name, equipment_type, position, at, property, commit } => {
            handle_add_equipment(room, name, equipment_type, position, at, property, commit)
        }
        EquipmentCommands::List { room, equipment_type, verbose, interactive } => {
            if interactive {
                crate::commands::equipment::browser::handle_equipment_browser(room, equipment_type)
            } else {
                handle_list_equipment(room, equipment_type, verbose)
            }
        }
        EquipmentCommands::Update { equipment, property, position, commit } => {
            handle_update_equipment(equipment, property, position, commit)
        }
        EquipmentCommands::Remove { equipment, confirm, commit } => {
            handle_remove_equipment(equipment, confirm, commit)
        }
    }
}

/// Add equipment to a room
fn handle_add_equipment(
    room: String,
    name: String,
    equipment_type: String,
    position: Option<String>,
    at: Option<String>,
    property: Vec<String>,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔧 Adding equipment: {} to room {}", name, room);
    println!("   Type: {}", equipment_type);
    
    // Parse equipment type using helper function
    let parsed_equipment_type = parse_equipment_type(&equipment_type);
    
    // Parse position if provided
    let pos_3d = if let Some(ref pos_str) = position {
        let coords: Vec<&str> = pos_str.split(',').map(|s| s.trim()).collect();
        if coords.len() == 3 {
            let x = coords[0].parse()
                .map_err(|e| format!("Invalid X coordinate '{}': {}. Expected a number.", coords[0], e))?;
            let y = coords[1].parse()
                .map_err(|e| format!("Invalid Y coordinate '{}': {}. Expected a number.", coords[1], e))?;
            let z = coords[2].parse()
                .map_err(|e| format!("Invalid Z coordinate '{}': {}. Expected a number.", coords[2], e))?;
            Point3D { x, y, z }
        } else {
            return Err(format!(
                "Invalid position format '{}'. Expected format: x,y,z (e.g., '10.0,20.0,5.0')",
                pos_str
            ).into());
        }
    } else {
        Point3D { x: 0.0, y: 0.0, z: 0.0 }
    };
    
    if let Some(ref pos) = position {
        println!("   Position: {}", pos);
    }
    
    for prop in &property {
        println!("   Property: {}", prop);
    }
    
    // Use PersistenceManager to add equipment
    // First, we need to find the building name - for now, try loading from current dir
    use crate::utils::path_safety::PathSafety;
    let current_dir = std::env::current_dir()?;
    let yaml_files: Vec<_> = PathSafety::read_dir_safely(std::path::Path::new("."), &current_dir)
        .map_err(|e| format!("Failed to read directory: {}", e))?
        .into_iter()
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("yaml"))
        .collect();
    
    let building_name = if let Some(yaml_file) = yaml_files.first() {
        yaml_file.file_stem().and_then(|s| s.to_str()).unwrap_or("Default Building").to_string()
    } else {
        "Default Building".to_string()
    };
    
    let persistence = PersistenceManager::new(&building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Handle address: parse from --at flag or auto-generate
    let address = if let Some(path_str) = at {
        let addr = crate::domain::ArxAddress::from_path(&path_str)?;
        addr.validate()?;
        Some(addr)
    } else {
        // Auto-generate address from context
        // Find the room and floor level
        let mut found_floor_level: Option<i32> = None;
        let mut found_room_name: Option<String> = None;
        for floor in &building_data.floors {
            for room_data in &floor.rooms {
                if room_data.name == room {
                    found_floor_level = Some(floor.level);
                    found_room_name = Some(room_data.name.clone());
                    break;
                }
            }
            if found_floor_level.is_some() {
                break;
            }
        }
        
        if let (Some(floor_level), Some(room_name)) = (found_floor_level, found_room_name) {
            // Generate address from grid if available, otherwise use room name
            // Grid inference would go here - simplified for now
            
            let room_system = room_name.to_lowercase().replace(" ", "-");
            let floor_str = format!("floor-{:02}", floor_level);
            let fixture_type = equipment_type.to_lowercase();
            let fixture_id = format!("{}-01", fixture_type);
            
            let addr = crate::domain::ArxAddress::new(
                "usa", "ny", "brooklyn", // Defaults - could come from config
                &building_name.to_lowercase().replace(" ", "-"),
                &floor_str,
                &room_system,
                &fixture_id,
            );
            Some(addr)
        } else {
            None
        }
    };
    
    // Create equipment with position and address
    let mut equipment = crate::core::Equipment::new(name.clone(), "".to_string(), parsed_equipment_type);
    equipment.position = crate::core::Position {
        x: pos_3d.x,
        y: pos_3d.y,
        z: pos_3d.z,
        coordinate_system: "building_local".to_string(),
    };
    equipment.address = address.clone();
    
    // Find the room and add equipment to it
    let mut equipment_added = false;
    for floor in &mut building_data.floors {
        for room_data in &mut floor.rooms {
            if room_data.name == room {
                // Add equipment ID to room's equipment list
                room_data.equipment.push(equipment.id.clone());
                
                // Generate universal path for backward compatibility (from address if available)
                let universal_path = address.as_ref()
                    .map(|addr| addr.path.clone())
                    .unwrap_or_else(|| {
                        format!("/buildings/{}/floors/{}/rooms/{}/equipment/{}", 
                            building_name, floor.level, room, equipment.id)
                    });
                
                // Add to floor equipment list
                let equipment_data = crate::yaml::EquipmentData {
                    id: equipment.id.clone(),
                    name: equipment.name.clone(),
                    equipment_type: equipment_type_to_string(&equipment.equipment_type),
                    system_type: equipment_type_to_string(&equipment.equipment_type),
                    position: pos_3d,
                    bounding_box: crate::spatial::BoundingBox3D {
                        min: Point3D { x: pos_3d.x - 0.5, y: pos_3d.y - 0.5, z: pos_3d.z - 0.5 },
                        max: Point3D { x: pos_3d.x + 0.5, y: pos_3d.y + 0.5, z: pos_3d.z + 0.5 },
                    },
                    status: crate::yaml::EquipmentStatus::Unknown,
                    properties: property.iter().enumerate().map(|(i, p)| {
                        (format!("property_{}", i), p.clone())
                    }).collect(),
                    universal_path,
                    address: address.clone(),
                    sensor_mappings: None,
                };
                floor.equipment.push(equipment_data);
                equipment_added = true;
                
                if let Some(ref addr) = address {
                    println!("   Address: {}", addr.path);
                }
                break;
            }
        }
        if equipment_added {
            break;
        }
    }
    
    if !equipment_added {
        println!("⚠️ Warning: Room '{}' not found, equipment will not be added to any room", room);
    }
    
    // Save changes
    if commit {
        let commit_msg = format!("Add equipment: {} to room {}", equipment.name, room);
        persistence.save_and_commit(&building_data, Some(&commit_msg))?;
        println!("💡 Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
        println!("💡 Changes saved (staged). Use --commit to commit to Git");
    }
    
    println!("✅ Equipment added successfully: {}", equipment.name);
    Ok(())
}

/// List equipment
fn handle_list_equipment(room: Option<String>, equipment_type: Option<String>, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Listing equipment");
    
    if let Some(r) = room {
        println!("   Room: {}", r);
    }
    
    if let Some(et) = equipment_type {
        println!("   Type: {}", et);
    }
    
    if verbose {
        println!("   Verbose mode enabled");
    }
    
    let equipment_list = crate::core::list_equipment(None)?;
    
    if equipment_list.is_empty() {
        println!("No equipment found");
    } else {
        for eq in equipment_list {
            println!("   {} (ID: {}) - Type: {:?}", eq.name, eq.id, eq.equipment_type);
            if verbose {
                println!("     Position: ({:.2}, {:.2}, {:.2})", 
                    eq.position.x, eq.position.y, eq.position.z);
                println!("     Status: {:?}", eq.status);
                if let Some(room_id) = &eq.room_id {
                    println!("     Room ID: {}", room_id);
                }
            }
        }
    }
    
    println!("✅ Equipment listing completed");
    Ok(())
}

/// Update equipment
fn handle_update_equipment(equipment: String, property: Vec<String>, position: Option<String>, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("✏️ Updating equipment: {}", equipment);
    
    for prop in &property {
        println!("   Property: {}", prop);
    }
    
    if let Some(ref pos) = position {
        println!("   New position: {}", pos);
    }
    
    // Load building data with path safety
    use crate::utils::path_safety::PathSafety;
    let current_dir = std::env::current_dir()?;
    let yaml_files: Vec<_> = PathSafety::read_dir_safely(std::path::Path::new("."), &current_dir)
        .map_err(|e| format!("Failed to read directory: {}", e))?
        .into_iter()
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("yaml"))
        .collect();
    
    let building_name = if let Some(yaml_file) = yaml_files.first() {
        yaml_file.file_stem().and_then(|s| s.to_str()).unwrap_or("Default Building").to_string()
    } else {
        "Default Building".to_string()
    };

    let persistence = PersistenceManager::new(&building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and update equipment
    let mut equipment_found = false;
    for floor in &mut building_data.floors {
        for equipment_data in &mut floor.equipment {
            if equipment_data.name == equipment || equipment_data.id == equipment {
                // Update properties
                if let Some(pos_str) = &position {
                    let coords: Vec<&str> = pos_str.split(',').map(|s| s.trim()).collect();
                    if coords.len() == 3 {
                        equipment_data.position = Point3D {
                            x: coords[0].parse().unwrap_or(equipment_data.position.x),
                            y: coords[1].parse().unwrap_or(equipment_data.position.y),
                            z: coords[2].parse().unwrap_or(equipment_data.position.z),
                        };
                    }
                }
                
                // Update custom properties
                for prop in &property {
                    let parts: Vec<&str> = prop.split('=').map(|s| s.trim()).collect();
                    if parts.len() == 2 {
                        equipment_data.properties.insert(parts[0].to_string(), parts[1].to_string());
                    }
                }
                
                equipment_found = true;
                break;
            }
        }
        if equipment_found {
            break;
        }
    }
    
    if !equipment_found {
        return Err(format!("Equipment '{}' not found", equipment).into());
    }
    
    // Save changes
    if commit {
        let commit_msg = format!("Update equipment: {}", equipment);
        persistence.save_and_commit(&building_data, Some(&commit_msg))?;
        println!("💡 Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
        println!("💡 Changes saved (staged). Use --commit to commit to Git");
    }
    
    println!("✅ Equipment updated successfully: {}", equipment);
    Ok(())
}

/// Remove equipment
fn handle_remove_equipment(equipment: String, confirm: bool, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    if !confirm {
        println!("❌ Equipment removal requires confirmation. Use --confirm flag.");
        return Ok(());
    }
    
    println!("🗑️ Removing equipment: {}", equipment);
    
    // Load building data with path safety
    use crate::utils::path_safety::PathSafety;
    let current_dir = std::env::current_dir()?;
    let yaml_files: Vec<_> = PathSafety::read_dir_safely(std::path::Path::new("."), &current_dir)
        .map_err(|e| format!("Failed to read directory: {}", e))?
        .into_iter()
        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("yaml"))
        .collect();
    
    let building_name = if let Some(yaml_file) = yaml_files.first() {
        yaml_file.file_stem().and_then(|s| s.to_str()).unwrap_or("Default Building").to_string()
    } else {
        "Default Building".to_string()
    };

    let persistence = PersistenceManager::new(&building_name)?;
    let mut building_data = persistence.load_building_data()?;

    // Find and remove equipment
    let mut equipment_removed = false;
    for floor in &mut building_data.floors {
        let equipment_len_before = floor.equipment.len();
        
        // Remove from floor equipment list
        floor.equipment.retain(|eq| eq.name != equipment && eq.id != equipment);
        
        if floor.equipment.len() < equipment_len_before {
            equipment_removed = true;
        }
        
        // Remove from room equipment lists
        for room_data in &mut floor.rooms {
            room_data.equipment.retain(|eq_id| {
                floor.equipment.iter().any(|eq| eq.id == *eq_id)
            });
        }
    }
    
    if !equipment_removed {
        return Err(format!("Equipment '{}' not found", equipment).into());
    }
    
    // Save changes
    if commit {
        let commit_msg = format!("Remove equipment: {}", equipment);
        persistence.save_and_commit(&building_data, Some(&commit_msg))?;
        println!("💡 Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
        println!("💡 Changes saved (staged). Use --commit to commit to Git");
    }
    
    println!("✅ Equipment removed successfully");
    Ok(())
}

/// Convert EquipmentType enum to string
fn equipment_type_to_string(eq_type: &EquipmentType) -> String {
    match eq_type {
        EquipmentType::HVAC => "HVAC".to_string(),
        EquipmentType::Electrical => "Electrical".to_string(),
        EquipmentType::AV => "AV".to_string(),
        EquipmentType::Furniture => "Furniture".to_string(),
        EquipmentType::Safety => "Safety".to_string(),
        EquipmentType::Plumbing => "Plumbing".to_string(),
        EquipmentType::Network => "Network".to_string(),
        EquipmentType::Other(s) => s.clone(),
    }
}

/// Parse equipment type string to EquipmentType enum
pub fn parse_equipment_type(equipment_type: &str) -> EquipmentType {
    match equipment_type.to_lowercase().as_str() {
        "hvac" => EquipmentType::HVAC,
        "electrical" => EquipmentType::Electrical,
        "av" => EquipmentType::AV,
        "furniture" => EquipmentType::Furniture,
        "safety" => EquipmentType::Safety,
        "plumbing" => EquipmentType::Plumbing,
        "network" => EquipmentType::Network,
        _ => EquipmentType::Other(equipment_type.to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_equipment_type_hvac() {
        let result = parse_equipment_type("hvac");
        assert!(matches!(result, EquipmentType::HVAC));
    }

    #[test]
    fn test_parse_equipment_type_electrical() {
        let result = parse_equipment_type("electrical");
        assert!(matches!(result, EquipmentType::Electrical));
    }

    #[test]
    fn test_parse_equipment_type_case_insensitive() {
        let result1 = parse_equipment_type("HVAC");
        let result2 = parse_equipment_type("Hvac");
        let result3 = parse_equipment_type("hvac");
        assert!(matches!(result1, EquipmentType::HVAC));
        assert!(matches!(result2, EquipmentType::HVAC));
        assert!(matches!(result3, EquipmentType::HVAC));
    }

    #[test]
    fn test_parse_equipment_type_furniture() {
        let result = parse_equipment_type("furniture");
        assert!(matches!(result, EquipmentType::Furniture));
    }

    #[test]
    fn test_parse_equipment_type_safety() {
        let result = parse_equipment_type("safety");
        assert!(matches!(result, EquipmentType::Safety));
    }

    #[test]
    fn test_parse_equipment_type_plumbing() {
        let result = parse_equipment_type("plumbing");
        assert!(matches!(result, EquipmentType::Plumbing));
    }

    #[test]
    fn test_parse_equipment_type_network() {
        let result = parse_equipment_type("network");
        assert!(matches!(result, EquipmentType::Network));
    }

    #[test]
    fn test_parse_equipment_type_av() {
        let result = parse_equipment_type("av");
        assert!(matches!(result, EquipmentType::AV));
    }

    #[test]
    fn test_parse_equipment_type_unknown() {
        let result = parse_equipment_type("unknown_type");
        assert!(matches!(result, EquipmentType::Other(_)));
        if let EquipmentType::Other(ref value) = result {
            assert_eq!(value, "unknown_type");
        }
    }

    #[test]
    fn test_parse_equipment_type_empty_string() {
        let result = parse_equipment_type("");
        assert!(matches!(result, EquipmentType::Other(_)));
    }
}
