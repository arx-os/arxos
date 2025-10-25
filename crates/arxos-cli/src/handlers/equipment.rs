//! # Equipment Command Handlers
//!
//! This module handles equipment-related CLI commands with full integration
//! to the ArxOS core functionality.

use crate::error::CliError;
use crate::utils::display::{display_success, display_error, display_info};
use crate::cli::EquipmentCommands;
use arxos_core::{ArxOSCore, parse_equipment_type, parse_position};

/// Handle equipment commands with full core integration
pub fn handle_equipment_command(command: EquipmentCommands) -> Result<(), CliError> {
    let mut core = ArxOSCore::new()
        .map_err(|e| CliError::CoreOperation {
            operation: "initialize core".to_string(),
            source: e,
        })?;

    match command {
        EquipmentCommands::Add { building, floor, wing, room, name, equipment_type, position } => {
            display_info(&format!("Adding equipment: {} to room: {}", name, room));
            display_info(&format!("Building: {}, Floor: {}, Wing: {}", building, floor, wing));
            display_info(&format!("Type: {}", equipment_type));
            
            // Parse equipment type
            let parsed_type = parse_equipment_type(&equipment_type)
                .map_err(|e| CliError::InvalidInput {
                    field: "equipment_type".to_string(),
                    value: equipment_type,
                    reason: e.to_string(),
                })?;
            
            // Parse position if provided
            let parsed_position = if let Some(pos) = position {
                Some(parse_position(&pos)
                    .map_err(|e| CliError::InvalidInput {
                        field: "position".to_string(),
                        value: pos,
                        reason: e.to_string(),
                    })?)
            } else {
                None
            };
            
            // Add equipment using core
            let equipment = core.add_equipment(&building, floor, &wing, &room, &name, parsed_type, parsed_position)
                .map_err(|e| CliError::CoreOperation {
                    operation: "add equipment".to_string(),
                    source: e,
                })?;
            
            display_success(&format!("Equipment added successfully with ID: {}", equipment.id));
            display_info(&format!("Equipment type: {:?}", equipment.equipment_type));
            if let Some(pos) = &equipment.position {
                display_info(&format!("Position: ({}, {}, {})", pos.x, pos.y, pos.z));
            }
        }
        
        EquipmentCommands::List { building, floor, wing, room, equipment_type, verbose } => {
            let building_name = building.unwrap_or_else(|| "Default Building".to_string());
            let floor_level = floor.unwrap_or(1);
            let wing_name = wing.unwrap_or_else(|| "Default Wing".to_string());
            let room_name = room.unwrap_or_else(|| "Default Room".to_string());
            
            display_info(&format!("Listing equipment for building: {}", building_name));
            display_info(&format!("Floor: {}, Wing: {}, Room: {}", floor_level, wing_name, room_name));
            if let Some(et) = equipment_type {
                display_info(&format!("Type filter: {}", et));
            }
            
            // List equipment using core
            let equipment = core.list_equipment(&building_name, floor_level, &wing_name, &room_name)
                .map_err(|e| CliError::CoreOperation {
                    operation: "list equipment".to_string(),
                    source: e,
                })?;
            
            if equipment.is_empty() {
                display_info("No equipment found");
            } else {
                display_success(&format!("Found {} equipment items:", equipment.len()));
                for item in &equipment {
                    display_info(&format!("  🔧 {} (ID: {})", item.name, item.id));
                    display_info(&format!("    Type: {:?}", item.equipment_type));
                    if verbose {
                        display_info(&format!("    Status: {:?}", item.status));
                        if let Some(pos) = &item.position {
                            display_info(&format!("    Position: ({}, {}, {})", pos.x, pos.y, pos.z));
                        }
                    }
                }
            }
        }
        
        EquipmentCommands::Show { equipment_id, room } => {
            display_info(&format!("Showing equipment: {}", equipment_id));
            
            // Look up equipment by ID in core
            let equipment = core.get_equipment("Default Building", 1, "Default Wing", "Default Room", &equipment_id)
                .map_err(|e| CliError::CoreOperation {
                    operation: "get equipment".to_string(),
                    source: e,
                })?;
            
            display_success("Equipment details:");
            display_info(&format!("  ID: {}", equipment.id));
            display_info(&format!("  Name: {}", equipment.name));
            display_info(&format!("  Type: {:?}", equipment.equipment_type));
            display_info(&format!("  Status: {:?}", equipment.status));
            if room {
                display_info(&format!("  Room ID: {:?}", equipment.room_id));
            }
        }
        
        EquipmentCommands::Update { building, floor, wing, room, name, new_name, equipment_type, position } => {
            display_info(&format!("Updating equipment: {} in room: {}", name, room));
            
            // Parse optional parameters
            let parsed_type = if let Some(et) = equipment_type {
                Some(parse_equipment_type(&et)
                    .map_err(|e| CliError::InvalidInput {
                        field: "equipment_type".to_string(),
                        value: et,
                        reason: e.to_string(),
                    })?)
            } else {
                None
            };
            
            let parsed_position = if let Some(pos) = position {
                Some(parse_position(&pos)
                    .map_err(|e| CliError::InvalidInput {
                        field: "position".to_string(),
                        value: pos,
                        reason: e.to_string(),
                    })?)
            } else {
                None
            };
            
            // Update equipment using core
            let updated_equipment = core.update_equipment(&building, floor, &wing, &room, &name, new_name.as_deref(), parsed_type, parsed_position)
                .map_err(|e| CliError::CoreOperation {
                    operation: "update equipment".to_string(),
                    source: e,
                })?;
            
            display_success(&format!("Equipment updated successfully: {}", updated_equipment.name));
        }
        
        EquipmentCommands::Remove { building, floor, wing, room, name, confirm } => {
            if !confirm {
                display_error("Equipment removal requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            display_info(&format!("Removing equipment: {} from room: {}", name, room));
            
            // Remove equipment using core
            core.remove_equipment(&building, floor, &wing, &room, &name)
                .map_err(|e| CliError::CoreOperation {
                    operation: "remove equipment".to_string(),
                    source: e,
                })?;
            
            display_success(&format!("Equipment {} removed successfully", name));
        }
    }
    
    Ok(())
}
