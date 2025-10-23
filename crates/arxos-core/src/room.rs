//! Room management for ArxOS Core

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

        Err(ArxError::Unknown(format!("Room not found: {}", identifier)))
    }

    /// Update room properties
    pub fn update_room(&mut self, identifier: &str, properties: Vec<String>) -> Result<Room> {
        let room = self.rooms.get_mut(identifier)
            .ok_or_else(|| ArxError::Unknown(format!("Room not found: {}", identifier)))?;

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
            Err(ArxError::Unknown(format!("Room not found: {}", identifier)))
        }
    }
}

/// Parse dimensions from string format "width x depth x height"
fn parse_dimensions(dimensions: &str) -> Result<Dimensions> {
    let parts: Vec<&str> = dimensions.split('x').collect();
    if parts.len() != 3 {
        return Err(ArxError::Validation("Invalid dimensions format. Use 'width x depth x height'".to_string()));
    }

    let width = parts[0].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid width value".to_string()))?;
    let depth = parts[1].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid depth value".to_string()))?;
    let height = parts[2].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid height value".to_string()))?;

    Ok(Dimensions { width, height, depth })
}

/// Parse position from string format "x,y,z"
fn parse_position(position: &str) -> Result<Position> {
    let parts: Vec<&str> = position.split(',').collect();
    if parts.len() != 3 {
        return Err(ArxError::Validation("Invalid position format. Use 'x,y,z'".to_string()));
    }

    let x = parts[0].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid x coordinate".to_string()))?;
    let y = parts[1].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid y coordinate".to_string()))?;
    let z = parts[2].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid z coordinate".to_string()))?;

    Ok(Position {
        x,
        y,
        z,
        coordinate_system: "building_local".to_string(),
    })
}

/// Parse room type from string
pub fn parse_room_type(room_type: &str) -> RoomType {
    match room_type.to_lowercase().as_str() {
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
        _ => RoomType::Other(room_type.to_string()),
    }
}
