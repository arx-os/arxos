//! # Room Command Handlers
//!
//! This module handles room-related CLI commands with full integration
//! to the ArxOS core functionality.

use crate::error::CliError;
use crate::utils::display::{display_success, display_error, display_info};
use crate::cli::RoomCommands;
use arxos_core::{ArxOSCore, parse_room_type, parse_dimensions, parse_position};

/// Handle room commands with full core integration
pub fn handle_room_command(command: RoomCommands) -> Result<(), CliError> {
    let mut core = ArxOSCore::new()
        .map_err(|e| CliError::CoreOperation {
            operation: "initialize core".to_string(),
            source: e,
        })?;

    match command {
        RoomCommands::Create { building, floor, wing, name, room_type } => {
            display_info(&format!("Creating room: {} in building: {}", name, building));
            display_info(&format!("Floor: {}, Wing: {}, Type: {}", floor, wing, room_type));
            
            // Parse room type
            let parsed_type = parse_room_type(&room_type)
                .map_err(|e| CliError::InvalidInput {
                    field: "room_type".to_string(),
                    value: room_type,
                    reason: e.to_string(),
                })?;
            
            // Create room using core
            let room = core.create_room(&building, floor, &wing, &name, parsed_type)
                .map_err(|e| CliError::CoreOperation {
                    operation: "create room".to_string(),
                    source: e,
                })?;
            
            display_success(&format!("Room created successfully with ID: {}", room.id));
            display_info(&format!("Room type: {:?}", room.room_type));
        }
        
        RoomCommands::List { building, floor, wing } => {
            let building_name = building.unwrap_or_else(|| "Default Building".to_string());
            let floor_level = floor.unwrap_or(1);
            
            display_info(&format!("Listing rooms for building: {}", building_name));
            display_info(&format!("Floor: {}", floor_level));
            if let Some(wing_name) = wing {
                display_info(&format!("Wing: {}", wing_name));
            }
            
            // List rooms using core
            let rooms = core.list_rooms(&building_name, floor_level, wing.as_deref())
                .map_err(|e| CliError::CoreOperation {
                    operation: "list rooms".to_string(),
                    source: e,
                })?;
            
            if rooms.is_empty() {
                display_info("No rooms found");
            } else {
                display_success(&format!("Found {} rooms:", rooms.len()));
                for room in &rooms {
                    display_info(&format!("  🏠 {} (ID: {})", room.name, room.id));
                    display_info(&format!("    Type: {:?}", room.room_type));
                }
            }
        }
        
        RoomCommands::Show { room_id } => {
            display_info(&format!("Showing room: {}", room_id));
            
            // Look up room by ID in core
            let room = core.get_room("Default Building", 1, "Default Wing", &room_id)
                .map_err(|e| CliError::CoreOperation {
                    operation: "get room".to_string(),
                    source: e,
                })?;
            
            display_success("Room details:");
            display_info(&format!("  ID: {}", room.id));
            display_info(&format!("  Name: {}", room.name));
            display_info(&format!("  Type: {:?}", room.room_type));
            display_info(&format!("  Created: {}", room.created_at));
        }
        
        RoomCommands::Update { room_id, new_name, room_type, dimensions, position } => {
            display_info(&format!("Updating room: {}", room_id));
            
            // Parse optional parameters
            let parsed_type = if let Some(rt) = room_type {
                Some(parse_room_type(&rt)
                    .map_err(|e| CliError::InvalidInput {
                        field: "room_type".to_string(),
                        value: rt,
                        reason: e.to_string(),
                    })?)
            } else {
                None
            };
            
            let parsed_dimensions = if let Some(dims) = dimensions {
                Some(parse_dimensions(&dims)
                    .map_err(|e| CliError::InvalidInput {
                        field: "dimensions".to_string(),
                        value: dims,
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
            
            // Update room using core
            let updated_room = core.update_room("Default Building", 1, "Default Wing", &room_id, new_name.as_deref(), parsed_type, parsed_dimensions, parsed_position)
                .map_err(|e| CliError::CoreOperation {
                    operation: "update room".to_string(),
                    source: e,
                })?;
            
            display_success(&format!("Room updated successfully: {}", updated_room.name));
        }
        
        RoomCommands::Delete { room_id, confirm } => {
            if !confirm {
                display_error("Room deletion requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            display_info(&format!("Deleting room: {}", room_id));
            
            // Delete room using core
            core.delete_room("Default Building", 1, "Default Wing", &room_id)
                .map_err(|e| CliError::CoreOperation {
                    operation: "delete room".to_string(),
                    source: e,
                })?;
            
            display_success(&format!("Room {} deleted successfully", room_id));
        }
    }
    
    Ok(())
}
