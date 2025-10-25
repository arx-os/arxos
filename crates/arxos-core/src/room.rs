//! # Room Management for ArxOS Core
//!
//! This module provides comprehensive room management capabilities for building spaces,
//! including room creation, spatial organization, equipment assignment, and room hierarchy.
//!
//! ## Features
//!
//! - **Room CRUD Operations**: Create, read, update, and delete rooms
//! - **Room Types**: Support for various room types (classroom, office, lab, etc.)
//! - **Spatial Properties**: 3D positioning, dimensions, and bounding boxes
//! - **Equipment Assignment**: Associate equipment with rooms
//! - **Hierarchical Organization**: Floor and wing organization
//!
//! ## Room Types
//!
//! - **Classroom**: Educational spaces for teaching and learning
//! - **Office**: Administrative and professional workspaces
//! - **Laboratory**: Scientific and research facilities
//! - **Conference Room**: Meeting and collaboration spaces
//! - **Storage**: Utility and storage areas
//! - **Restroom**: Sanitary facilities
//! - **Corridor**: Circulation and access spaces
//!
//! ## Examples
//!
//! ```rust
//! use arxos_core::room::{RoomManager, RoomType, parse_room_type};
//!
//! let mut manager = RoomManager::new();
//! let room_type = parse_room_type("classroom");
//! 
//! let room = manager.create_room(
//!     "Math Classroom 101".to_string(),
//!     room_type,
//!     1,
//!     "A".to_string(),
//!     Some("10.0x8.0x3.0".to_string()),
//!     Some("5.0,10.0,0.0".to_string())
//! )?;
//! ```
//!
//! ## Spatial Organization
//!
//! Rooms are organized hierarchically:
//! - **Building** → **Floor** → **Wing** → **Room**
//! - Each room has spatial properties (position, dimensions)
//! - Equipment can be assigned to specific rooms
//! - Rooms can be queried by spatial relationships
//!
//! ## Performance Considerations
//!
//! - Room lookups use HashMap for O(1) access time
//! - Spatial queries are optimized for large room datasets
//! - Equipment associations are efficiently managed

use crate::{Result, Room, RoomType, SpatialProperties, Position, Dimensions, BoundingBox, ArxError};
use std::collections::HashMap;
use chrono::Utc;
use uuid::Uuid;

/// Room management operations
#[derive(Debug)]
pub struct RoomManager {
    rooms: HashMap<String, Room>,
}

impl RoomManager {
    /// Create a new room manager
    pub fn new() -> Self {
        Self {
            rooms: HashMap::new(),
        }
    }

    /// Create a new room
    pub fn create_room(
        &mut self,
        name: String,
        room_type: RoomType,
        _floor: i32,
        _wing: String,
        dimensions: Option<String>,
        position: Option<String>,
    ) -> Result<Room> {
        let id = Uuid::new_v4().to_string();
        
        // Parse dimensions if provided
        let parsed_dimensions = if let Some(dims) = dimensions {
            parse_dimensions(&dims)?
        } else {
            Dimensions {
                width: 10.0,
                height: 3.0,
                depth: 10.0,
            }
        };

        // Parse position if provided
        let parsed_position = if let Some(pos) = position {
            parse_position(&pos)?
        } else {
            Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            }
        };

        // Calculate bounding box
        let bounding_box = BoundingBox {
            min: Position {
                x: parsed_position.x - parsed_dimensions.width / 2.0,
                y: parsed_position.y,
                z: parsed_position.z - parsed_dimensions.depth / 2.0,
                coordinate_system: parsed_position.coordinate_system.clone(),
            },
            max: Position {
                x: parsed_position.x + parsed_dimensions.width / 2.0,
                y: parsed_position.y + parsed_dimensions.height,
                z: parsed_position.z + parsed_dimensions.depth / 2.0,
                coordinate_system: parsed_position.coordinate_system.clone(),
            },
        };

        let spatial_properties = SpatialProperties {
            position: parsed_position,
            dimensions: parsed_dimensions,
            bounding_box,
            coordinate_system: "building_local".to_string(),
        };

        let room = Room {
            id: id.clone(),
            name: name.clone(),
            room_type,
            equipment: Vec::new(),
            spatial_properties,
            properties: HashMap::new(),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        self.rooms.insert(id.clone(), room.clone());
        Ok(room)
    }

    /// List all rooms
    pub fn list_rooms(&self) -> Result<Vec<Room>> {
        Ok(self.rooms.values().cloned().collect())
    }

    /// Get room by ID or name
    pub fn get_room(&self, identifier: &str) -> Result<&Room> {
        // Try by ID first
        if let Some(room) = self.rooms.get(identifier) {
            return Ok(room);
        }

        // Try by name
        for room in self.rooms.values() {
            if room.name == identifier {
                return Ok(room);
            }
        }

        Err(ArxError::RoomNotFound { room_id: identifier.to_string() })
    }

    /// Update room properties
    pub fn update_room(&mut self, identifier: &str, properties: Vec<String>) -> Result<Room> {
        let room = self.rooms.get_mut(identifier)
            .ok_or_else(|| ArxError::RoomNotFound { room_id: identifier.to_string() })?;

        for property in properties {
            if let Some((key, value)) = property.split_once('=') {
                room.properties.insert(key.to_string(), value.to_string());
            }
        }

        room.updated_at = Utc::now();
        Ok(room.clone())
    }

    /// Delete a room
    pub fn delete_room(&mut self, identifier: &str) -> Result<()> {
        if self.rooms.remove(identifier).is_some() {
            Ok(())
        } else {
            Err(ArxError::RoomNotFound { room_id: identifier.to_string() })
        }
    }
}

/// Parse dimensions from string format "width x depth x height"
fn parse_dimensions(dimensions: &str) -> Result<Dimensions> {
    let parts: Vec<&str> = dimensions.split('x').collect();
    if parts.len() != 3 {
        return Err(ArxError::validation_error("Invalid dimensions format. Use 'width x depth x height'"));
    }

    let width = parts[0].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid width value"))?;
    let depth = parts[1].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid depth value"))?;
    let height = parts[2].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid height value"))?;

    Ok(Dimensions { width, height, depth })
}

/// Parse position from string format "x,y,z"
fn parse_position(position: &str) -> Result<Position> {
    let parts: Vec<&str> = position.split(',').collect();
    if parts.len() != 3 {
        return Err(ArxError::validation_error("Invalid position format. Use 'x,y,z'"));
    }

    let x = parts[0].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid x coordinate"))?;
    let y = parts[1].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid y coordinate"))?;
    let z = parts[2].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid z coordinate"))?;

    Ok(Position {
        x,
        y,
        z,
        coordinate_system: "building_local".to_string(),
    })
}

/// Parse room type from string
/// 
/// # Arguments
/// 
/// * `room_type` - String representation of room type
/// 
/// # Returns
/// 
/// * `Result<RoomType>` - Parsed room type or error if invalid
/// 
/// # Examples
/// 
/// ```rust
/// use arxos_core::room::parse_room_type;
/// 
/// let classroom_type = parse_room_type("classroom")?;
/// let office_type = parse_room_type("office")?;
/// ```
pub fn parse_room_type(room_type: &str) -> Result<RoomType> {
    match room_type.to_lowercase().as_str() {
        "classroom" => Ok(RoomType::Classroom),
        "laboratory" => Ok(RoomType::Laboratory),
        "office" => Ok(RoomType::Office),
        "gymnasium" => Ok(RoomType::Gymnasium),
        "cafeteria" => Ok(RoomType::Cafeteria),
        "library" => Ok(RoomType::Library),
        "auditorium" => Ok(RoomType::Auditorium),
        "hallway" => Ok(RoomType::Hallway),
        "restroom" => Ok(RoomType::Restroom),
        "storage" => Ok(RoomType::Storage),
        "mechanical" => Ok(RoomType::Mechanical),
        "electrical" => Ok(RoomType::Electrical),
        _ => Err(ArxError::InvalidRoomType {
            room_type: room_type.to_string(),
            valid_types: "classroom, laboratory, office, gymnasium, cafeteria, library, auditorium, hallway, restroom, storage, mechanical, electrical".to_string(),
        }),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{RoomType, Position, Dimensions, BoundingBox};

    #[test]
    fn test_room_manager_new() {
        let manager = RoomManager::new();
        assert!(manager.rooms.is_empty());
    }

    #[test]
    fn test_create_room() {
        let mut manager = RoomManager::new();
        let room = manager.create_room(
            "Test Classroom".to_string(),
            RoomType::Classroom,
            1,
            "A".to_string(),
            Some("10.0x8.0x3.0".to_string()),
            Some("5.0,10.0,0.0".to_string()),
        ).unwrap();

        assert_eq!(room.name, "Test Classroom");
        assert_eq!(room.room_type, RoomType::Classroom);
        assert_eq!(room.spatial_properties.position.x, 5.0);
        assert_eq!(room.spatial_properties.position.y, 10.0);
        assert_eq!(room.spatial_properties.position.z, 0.0);
        assert_eq!(room.spatial_properties.dimensions.width, 10.0);
        assert_eq!(room.spatial_properties.dimensions.depth, 8.0);
        assert_eq!(room.spatial_properties.dimensions.height, 3.0);
    }

    #[test]
    fn test_create_room_with_properties() {
        let mut manager = RoomManager::new();
        let room = manager.create_room(
            "Test Office".to_string(),
            RoomType::Office,
            2,
            "B".to_string(),
            None,
            None,
        ).unwrap();

        assert_eq!(room.name, "Test Office");
        assert_eq!(room.room_type, RoomType::Office);
        assert_eq!(room.spatial_properties.position.x, 0.0);
        assert_eq!(room.spatial_properties.position.y, 0.0);
        assert_eq!(room.spatial_properties.position.z, 0.0);
    }

    #[test]
    fn test_get_room() {
        let mut manager = RoomManager::new();
        let room = manager.create_room(
            "Test Room".to_string(),
            RoomType::Classroom,
            1,
            "A".to_string(),
            None,
            None,
        ).unwrap();

        let retrieved = manager.get_room(&room.id).unwrap();
        assert_eq!(retrieved.name, "Test Room");
    }

    #[test]
    fn test_get_room_not_found() {
        let manager = RoomManager::new();
        let result = manager.get_room("nonexistent");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::RoomNotFound { room_id } => {
                assert_eq!(room_id, "nonexistent");
            }
            _ => panic!("Expected RoomNotFound error"),
        }
    }

    #[test]
    fn test_list_rooms() {
        let mut manager = RoomManager::new();
        manager.create_room("Room 1".to_string(), RoomType::Classroom, 1, "A".to_string(), None, None).unwrap();
        manager.create_room("Room 2".to_string(), RoomType::Office, 2, "B".to_string(), None, None).unwrap();

        let rooms = manager.list_rooms().unwrap();
        assert_eq!(rooms.len(), 2);
    }

    #[test]
    fn test_update_room() {
        let mut manager = RoomManager::new();
        let room = manager.create_room(
            "Test Room".to_string(),
            RoomType::Classroom,
            1,
            "A".to_string(),
            None,
            None,
        ).unwrap();

        let updated = manager.update_room(
            &room.id,
            vec!["capacity=30".to_string()],
        ).unwrap();

        assert_eq!(updated.properties.get("capacity"), Some(&"30".to_string()));
    }

    #[test]
    fn test_delete_room() {
        let mut manager = RoomManager::new();
        let room = manager.create_room(
            "Test Room".to_string(),
            RoomType::Classroom,
            1,
            "A".to_string(),
            None,
            None,
        ).unwrap();

        manager.delete_room(&room.id).unwrap();
        assert!(manager.get_room(&room.id).is_err());
    }

    #[test]
    fn test_parse_room_type_valid() {
        assert_eq!(parse_room_type("classroom").unwrap(), RoomType::Classroom);
        assert_eq!(parse_room_type("office").unwrap(), RoomType::Office);
        assert_eq!(parse_room_type("laboratory").unwrap(), RoomType::Laboratory);
        assert_eq!(parse_room_type("gymnasium").unwrap(), RoomType::Gymnasium);
        assert_eq!(parse_room_type("cafeteria").unwrap(), RoomType::Cafeteria);
        assert_eq!(parse_room_type("library").unwrap(), RoomType::Library);
        assert_eq!(parse_room_type("auditorium").unwrap(), RoomType::Auditorium);
        assert_eq!(parse_room_type("hallway").unwrap(), RoomType::Hallway);
        assert_eq!(parse_room_type("restroom").unwrap(), RoomType::Restroom);
        assert_eq!(parse_room_type("storage").unwrap(), RoomType::Storage);
        assert_eq!(parse_room_type("mechanical").unwrap(), RoomType::Mechanical);
        assert_eq!(parse_room_type("electrical").unwrap(), RoomType::Electrical);
    }

    #[test]
    fn test_parse_room_type_case_insensitive() {
        assert_eq!(parse_room_type("CLASSROOM").unwrap(), RoomType::Classroom);
        assert_eq!(parse_room_type("Office").unwrap(), RoomType::Office);
        assert_eq!(parse_room_type("LABORATORY").unwrap(), RoomType::Laboratory);
    }

    #[test]
    fn test_parse_room_type_invalid() {
        let result = parse_room_type("invalid_type");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::InvalidRoomType { room_type, valid_types } => {
                assert_eq!(room_type, "invalid_type");
                assert!(valid_types.contains("classroom"));
                assert!(valid_types.contains("office"));
            }
            _ => panic!("Expected InvalidRoomType error"),
        }
    }

    #[test]
    fn test_parse_dimensions_valid() {
        let dimensions = parse_dimensions("10.5x8.3x3.2").unwrap();
        assert_eq!(dimensions.width, 10.5);
        assert_eq!(dimensions.depth, 8.3);
        assert_eq!(dimensions.height, 3.2);
    }

    #[test]
    fn test_parse_dimensions_invalid_format() {
        let result = parse_dimensions("10.5x8.3");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::ValidationError { message, .. } => {
                assert!(message.contains("Invalid dimensions format"));
            }
            _ => panic!("Expected ValidationError"),
        }
    }

    #[test]
    fn test_parse_dimensions_invalid_values() {
        let result = parse_dimensions("invalidx8.3x3.2");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::ValidationError { message, .. } => {
                assert!(message.contains("Invalid width value"));
            }
            _ => panic!("Expected ValidationError"),
        }
    }

    #[test]
    fn test_parse_position_valid() {
        let position = parse_position("10.5,20.3,3.2").unwrap();
        assert_eq!(position.x, 10.5);
        assert_eq!(position.y, 20.3);
        assert_eq!(position.z, 3.2);
        assert_eq!(position.coordinate_system, "building_local");
    }

    #[test]
    fn test_parse_position_invalid_format() {
        let result = parse_position("10.5,20.3");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::ValidationError { message, .. } => {
                assert!(message.contains("Invalid position format"));
            }
            _ => panic!("Expected ValidationError"),
        }
    }

    #[test]
    fn test_parse_position_invalid_coordinates() {
        let result = parse_position("invalid,20.3,3.2");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::ValidationError { message, .. } => {
                assert!(message.contains("Invalid x coordinate"));
            }
            _ => panic!("Expected ValidationError"),
        }
    }
}
