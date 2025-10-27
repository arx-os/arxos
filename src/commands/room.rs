// Room management command handlers

use crate::cli::RoomCommands;
use crate::core::RoomType;
use crate::persistence::PersistenceManager;
use crate::yaml::{RoomData, FloorData};
use crate::spatial::Point3D;
use std::collections::HashMap;

/// Handle room management commands
pub fn handle_room_command(command: RoomCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        RoomCommands::Create { building, floor, wing, name, room_type, dimensions, position, commit } => {
            handle_create_room(building, floor, wing, name, room_type, dimensions, position, commit)
        }
        RoomCommands::List { building, floor, wing, verbose } => {
            handle_list_rooms(building, floor, wing, verbose)
        }
        RoomCommands::Show { room, equipment } => {
            handle_show_room(room, equipment)
        }
        RoomCommands::Update { room, property, commit } => {
            handle_update_room(room, property, commit)
        }
        RoomCommands::Delete { room, confirm, commit } => {
            handle_delete_room(room, confirm, commit)
        }
    }
}

/// Create a new room
fn handle_create_room(
    building: String,
    floor: i32,
    wing: String,
    name: String,
    room_type: String,
    dimensions: Option<String>,
    position: Option<String>,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🏗️ Creating room: {} in {} Floor {} Wing {}", name, building, floor, wing);
    println!("   Type: {}", room_type);
    
    if let Some(ref dims) = dimensions {
        println!("   Dimensions: {}", dims);
    }
    
    if let Some(ref pos) = position {
        println!("   Position: {}", pos);
    }
    
    // Parse room type directly
    let parsed_room_type = match room_type.to_lowercase().as_str() {
        "classroom" => RoomType::Classroom,
        "laboratory" => RoomType::Laboratory,
        "office" => RoomType::Office,
        "gymnasium" => RoomType::Gymnasium,
        "cafeteria" => RoomType::Cafeteria,
        "library" => RoomType::Library,
        "auditorium" => RoomType::Auditorium,
        "hallway" => RoomType::Hallway,
        "restroom" => RoomType::Restroom,
        "storage" => RoomType::Storage,
        "mechanical" => RoomType::Mechanical,
        "electrical" => RoomType::Electrical,
        _ => RoomType::Other(room_type),
    };
    
    // Use the local core types directly
    let room = crate::core::Room::new(name.clone(), parsed_room_type);
    
    // Parse dimensions if provided
    let (width, height, depth) = if let Some(dims) = dimensions {
        parse_dimensions(&dims)?
    } else {
        (10.0, 3.0, 10.0) // Default dimensions
    };
    
    // Parse position if provided
    let (x, y, z) = if let Some(pos) = position {
        parse_position(&pos)?
    } else {
        (0.0, 0.0, 0.0) // Default position
    };
    
    // Add room using PersistenceManager
    let persistence = PersistenceManager::new(&building)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find or create the floor
    let floor_data = building_data.floors.iter_mut()
        .find(|f| f.level == floor);
    
    let floor_data = if let Some(floor) = floor_data {
        floor
    } else {
        // Floor doesn't exist, create it
        building_data.floors.push(FloorData {
            id: format!("floor-{}", floor),
            name: format!("Floor {}", floor),
            level: floor,
            elevation: floor as f64 * 3.0,
            rooms: vec![],
            equipment: vec![],
            bounding_box: None,
        });
        building_data.floors.last_mut().unwrap()
    };
    
    // Create room data
    let position_3d = Point3D { x, y, z };
    let room_data = RoomData {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type: room.room_type.to_string(),
        area: Some(width * depth),
        volume: Some(width * depth * height),
        position: position_3d,
        bounding_box: crate::spatial::BoundingBox3D {
            min: Point3D { x, y, z },
            max: Point3D { x: x + width, y: y + depth, z: z + height },
        },
        equipment: vec![],
        properties: HashMap::new(),
    };
    
    // Add room to floor
    floor_data.rooms.push(room_data);
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Add room: {}", room.name)))?;
        println!("✅ Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    println!("✅ Room created successfully: {}", room.name);
    Ok(())
}

/// Parse dimensions string (width x depth x height)
pub fn parse_dimensions(dims: &str) -> Result<(f64, f64, f64), Box<dyn std::error::Error>> {
    let parts: Vec<&str> = dims.split('x').map(|s| s.trim()).collect();
    if parts.len() != 3 {
        return Err(format!("Invalid dimensions format '{}'. Use: width x depth x height", dims).into());
    }
    Ok((
        parts[0].parse()?,
        parts[1].parse()?,
        parts[2].parse()?,
    ))
}

/// Parse position string (x,y,z)
pub fn parse_position(pos: &str) -> Result<(f64, f64, f64), Box<dyn std::error::Error>> {
    let parts: Vec<&str> = pos.split(',').map(|s| s.trim()).collect();
    if parts.len() != 3 {
        return Err(format!("Invalid position format '{}'. Use: x,y,z", pos).into());
    }
    Ok((
        parts[0].parse()?,
        parts[1].parse()?,
        parts[2].parse()?,
    ))
}

/// List rooms
fn handle_list_rooms(building: Option<String>, floor: Option<i32>, wing: Option<String>, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Listing rooms");
    
    if let Some(b) = building {
        println!("   Building: {}", b);
    }
    
    if let Some(f) = floor {
        println!("   Floor: {}", f);
    }
    
    if let Some(w) = wing {
        println!("   Wing: {}", w);
    }
    
    if verbose {
        println!("   Verbose mode enabled");
    }
    
    let rooms = crate::core::list_rooms()?;
    
    if rooms.is_empty() {
        println!("No rooms found");
    } else {
        for room in rooms {
            println!("   {} (ID: {}) - Type: {:?}", room.name, room.id, room.room_type);
            if verbose {
                println!("     Position: ({:.2}, {:.2}, {:.2})", 
                    room.spatial_properties.position.x,
                    room.spatial_properties.position.y,
                    room.spatial_properties.position.z);
                println!("     Dimensions: {:.2} x {:.2} x {:.2}", 
                    room.spatial_properties.dimensions.width,
                    room.spatial_properties.dimensions.depth,
                    room.spatial_properties.dimensions.height);
            }
        }
    }
    
    println!("✅ Room listing completed");
    Ok(())
}

/// Show room details
fn handle_show_room(room: String, equipment: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Showing room details: {}", room);
    
    if equipment {
        println!("   Including equipment");
    }
    
    let room_data = crate::core::get_room(&room)?;
    
    println!("   Name: {}", room_data.name);
    println!("   ID: {}", room_data.id);
    println!("   Type: {:?}", room_data.room_type);
    println!("   Position: ({:.2}, {:.2}, {:.2})", 
        room_data.spatial_properties.position.x,
        room_data.spatial_properties.position.y,
        room_data.spatial_properties.position.z);
    println!("   Dimensions: {:.2} x {:.2} x {:.2}", 
        room_data.spatial_properties.dimensions.width,
        room_data.spatial_properties.dimensions.depth,
        room_data.spatial_properties.dimensions.height);
    
    if equipment {
        println!("   Equipment: {} items", room_data.equipment.len());
        for eq in &room_data.equipment {
            println!("     - {} ({:?})", eq.name, eq.equipment_type);
        }
    }
    
    println!("✅ Room details displayed");
    Ok(())
}

/// Update room properties
fn handle_update_room(room: String, property: Vec<String>, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("✏️ Updating room: {}", room);
    
    for prop in &property {
        println!("   Property: {}", prop);
    }
    
    let updated_room = crate::core::update_room(&room, property)?;
    
    if commit {
        println!("💡 Changes saved but not committed (commit not yet implemented for update)");
    }
    
    println!("✅ Room updated successfully: {} (ID: {})", updated_room.name, updated_room.id);
    Ok(())
}

/// Delete a room
fn handle_delete_room(room: String, confirm: bool, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    if !confirm {
        println!("❌ Room deletion requires confirmation. Use --confirm flag.");
        return Ok(());
    }
    
    println!("🗑️ Deleting room: {}", room);
    
    crate::core::delete_room(&room)?;
    
    if commit {
        println!("💡 Changes saved but not committed (commit not yet implemented for delete)");
    }
    
    println!("✅ Room deleted successfully");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_dimensions_valid_format() {
        // Test valid 3-part dimensions (width x depth x height)
        let result = parse_dimensions("10 x 20 x 8");
        assert!(result.is_ok());
        let (width, depth, height) = result.unwrap();
        assert_eq!(width, 10.0);
        assert_eq!(depth, 20.0);
        assert_eq!(height, 8.0);
    }

    #[test]
    fn test_parse_dimensions_with_spaces() {
        // Test dimensions with extra spaces
        let result = parse_dimensions("15.5 x 25.3 x 9.2");
        assert!(result.is_ok());
        let (width, depth, height) = result.unwrap();
        assert_eq!(width, 15.5);
        assert_eq!(depth, 25.3);
        assert_eq!(height, 9.2);
    }

    #[test]
    fn test_parse_dimensions_invalid_format() {
        // Test invalid format (wrong number of parts)
        let result = parse_dimensions("10x20"); // Missing height
        assert!(result.is_err());
        
        let error_msg = result.unwrap_err().to_string();
        assert!(error_msg.contains("Invalid dimensions format"));
    }

    #[test]
    fn test_parse_dimensions_non_numeric() {
        // Test with non-numeric values
        let result = parse_dimensions("invalid x 20 x 8");
        assert!(result.is_err());
    }

    #[test]
    fn test_parse_position_valid_format() {
        // Test valid 3-part position (x,y,z)
        let result = parse_position("10, 20, 5");
        assert!(result.is_ok());
        let (x, y, z) = result.unwrap();
        assert_eq!(x, 10.0);
        assert_eq!(y, 20.0);
        assert_eq!(z, 5.0);
    }

    #[test]
    fn test_parse_position_with_floats() {
        // Test position with floating point values
        let result = parse_position("15.5, 25.3, 9.2");
        assert!(result.is_ok());
        let (x, y, z) = result.unwrap();
        assert_eq!(x, 15.5);
        assert_eq!(y, 25.3);
        assert_eq!(z, 9.2);
    }

    #[test]
    fn test_parse_position_invalid_format() {
        // Test invalid format (wrong number of coordinates)
        let result = parse_position("10,20"); // Missing z
        assert!(result.is_err());
        
        let error_msg = result.unwrap_err().to_string();
        assert!(error_msg.contains("Invalid position format"));
    }

    #[test]
    fn test_parse_position_non_numeric() {
        // Test with non-numeric values
        let result = parse_position("invalid, 20, 5");
        assert!(result.is_err());
    }
}
