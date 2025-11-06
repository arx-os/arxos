//! Room service for business logic operations
//!
//! Provides high-level operations for room management,
//! decoupled from persistence concerns.

use super::repository::{Repository, RepositoryRef};
use crate::core::Room;
use crate::yaml::{BuildingData, RoomData};
use std::sync::Arc;

/// Service for room operations
pub struct RoomService {
    repository: RepositoryRef,
}

impl RoomService {
    /// Create a new room service with the given repository
    pub fn new(repository: RepositoryRef) -> Self {
        Self { repository }
    }
    
    /// Create a room service with file-based repository (production)
    pub fn with_file_repository() -> Self {
        use super::repository::FileRepository;
        Self::new(Arc::new(FileRepository::new()))
    }
    
    /// Create a room service with in-memory repository (testing)
    pub fn with_memory_repository() -> Self {
        use super::repository::InMemoryRepository;
        Self::new(Arc::new(InMemoryRepository::new()))
    }
    
    /// Create a room in a building
    pub fn create_room(
        &self,
        building_name: &str,
        floor_level: i32,
        room: Room,
        wing_name: Option<&str>,
        commit: bool,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut building_data = self.repository.load(building_name)?;
        let mut index = building_data.build_index();
        
        let wing_name = wing_name.unwrap_or("Default");
        let room_name = room.name.clone();
        
        // Convert Room to RoomData
        let room_data = self.room_to_room_data(&room);
        
        // Add to wing
        {
            let wing_data = building_data.get_or_create_wing_mut(floor_level, wing_name, &mut index)
                .map_err(|e| -> Box<dyn std::error::Error + Send + Sync> {
                    Box::new(std::io::Error::new(std::io::ErrorKind::Other, format!("{}", e)))
                })?;
            wing_data.rooms.push(room_data.clone());
        }
        
        // Add to floor (backward compatibility)
        {
            let floor_data = building_data.get_or_create_floor_mut(floor_level, &mut index)
                .map_err(|e| -> Box<dyn std::error::Error + Send + Sync> {
                    Box::new(std::io::Error::new(std::io::ErrorKind::Other, format!("{}", e)))
                })?;
            floor_data.rooms.push(room_data);
        }
        
        // Save
        if commit {
            let message_str = format!("Add room: {}", room_name);
            self.repository.save_and_commit(building_name, &building_data, Some(&message_str))?;
        } else {
            self.repository.save(building_name, &building_data)?;
        }
        
        Ok(())
    }
    
    /// List all rooms in a building
    pub fn list_rooms(&self, building_name: &str) -> Result<Vec<Room>, Box<dyn std::error::Error + Send + Sync>> {
        let building_data = self.repository.load(building_name)?;
        let mut rooms = Vec::new();
        
        for floor in &building_data.floors {
            for wing in &floor.wings {
                for room_data in &wing.rooms {
                    rooms.push(self.room_data_to_room(room_data));
                }
            }
            // Also check legacy rooms list
            for room_data in &floor.rooms {
                rooms.push(self.room_data_to_room(room_data));
            }
        }
        
        Ok(rooms)
    }
    
    /// Get a specific room by name
    pub fn get_room(&self, building_name: &str, room_name: &str) -> Result<Option<Room>, Box<dyn std::error::Error + Send + Sync>> {
        let building_data = self.repository.load(building_name)?;
        
        for floor in &building_data.floors {
            for wing in &floor.wings {
                if let Some(room_data) = wing.rooms.iter().find(|r| r.name == room_name) {
                    return Ok(Some(self.room_data_to_room(room_data)));
                }
            }
            // Also check legacy rooms list
            if let Some(room_data) = floor.rooms.iter().find(|r| r.name == room_name) {
                return Ok(Some(self.room_data_to_room(room_data)));
            }
        }
        
        Ok(None)
    }
    
    /// Convert Room to RoomData
    fn room_to_room_data(&self, room: &Room) -> RoomData {
        RoomData {
            id: room.id.clone(),
            name: room.name.clone(),
            room_type: format!("{}", room.room_type),
            area: Some(
                room.spatial_properties.dimensions.width * room.spatial_properties.dimensions.depth
            ),
            volume: Some(
                room.spatial_properties.dimensions.width
                    * room.spatial_properties.dimensions.depth
                    * room.spatial_properties.dimensions.height
            ),
            position: crate::spatial::Point3D {
                x: room.spatial_properties.position.x,
                y: room.spatial_properties.position.y,
                z: room.spatial_properties.position.z,
            },
            bounding_box: crate::spatial::BoundingBox3D {
                min: crate::spatial::Point3D {
                    x: room.spatial_properties.bounding_box.min.x,
                    y: room.spatial_properties.bounding_box.min.y,
                    z: room.spatial_properties.bounding_box.min.z,
                },
                max: crate::spatial::Point3D {
                    x: room.spatial_properties.bounding_box.max.x,
                    y: room.spatial_properties.bounding_box.max.y,
                    z: room.spatial_properties.bounding_box.max.z,
                },
            },
            equipment: vec![],
            properties: room.properties.clone(),
        }
    }
    
    /// Convert RoomData to Room
    fn room_data_to_room(&self, room_data: &RoomData) -> Room {
        use crate::yaml::conversions::room_data_to_room;
        room_data_to_room(room_data)
    }
}

impl Default for RoomService {
    fn default() -> Self {
        Self::with_file_repository()
    }
}

