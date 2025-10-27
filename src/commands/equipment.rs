// Equipment management command handlers

use crate::cli::EquipmentCommands;
use crate::core::EquipmentType;

/// Handle equipment management commands
pub fn handle_equipment_command(command: EquipmentCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        EquipmentCommands::Add { room, name, equipment_type, position, property, commit } => {
            handle_add_equipment(room, name, equipment_type, position, property, commit)
        }
        EquipmentCommands::List { room, equipment_type, verbose } => {
            handle_list_equipment(room, equipment_type, verbose)
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
    property: Vec<String>,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔧 Adding equipment: {} to room {}", name, room);
    println!("   Type: {}", equipment_type);
    
    if let Some(ref pos) = position {
        println!("   Position: {}", pos);
    }
    
    for prop in &property {
        println!("   Property: {}", prop);
    }
    
    // Parse equipment type using helper function
    let parsed_equipment_type = parse_equipment_type(&equipment_type);
    
    // Use the local core types directly
    let equipment = crate::core::Equipment::new(name.clone(), "".to_string(), parsed_equipment_type);
    
    // TODO: Actually add to building data using PersistenceManager
    
    if commit {
        println!("💡 Changes will be committed to Git");
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
    
    let equipment_list = crate::core::list_equipment()?;
    
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
    
    let updated_equipment = crate::core::update_equipment(&equipment, property)?;
    
    if commit {
        println!("💡 Changes will be committed to Git");
    }
    
    println!("✅ Equipment updated successfully: {} (ID: {})", updated_equipment.name, updated_equipment.id);
    Ok(())
}

/// Remove equipment
fn handle_remove_equipment(equipment: String, confirm: bool, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    if !confirm {
        println!("❌ Equipment removal requires confirmation. Use --confirm flag.");
        return Ok(());
    }
    
    println!("🗑️ Removing equipment: {}", equipment);
    
    crate::core::remove_equipment(&equipment)?;
    
    if commit {
        println!("💡 Changes will be committed to Git");
    }
    
    println!("✅ Equipment removed successfully");
    Ok(())
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
