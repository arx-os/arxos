//! Room service for business logic operations
//!
//! Provides high-level operations for room management,
//! decoupled from persistence concerns.

use super::repository::RepositoryRef;
use crate::core::Room;
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

        // Add to wing (primary location)
        {
            let wing = building_data
                .get_or_create_wing_mut(floor_level, wing_name, &mut index)
                .map_err(|e| -> Box<dyn std::error::Error + Send + Sync> {
                    Box::new(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        format!("{}", e),
                    ))
                })?;
            wing.rooms.push(room.clone());
        }

        // Add to floor (backward compatibility)
        // Note: Rooms are now only in wings, so this section is redundant but kept for clarity
        // The room was already added to the wing above

        // Save
        if commit {
            let message_str = format!("Add room: {}", room_name);
            self.repository
                .save_and_commit(building_name, &building_data, Some(&message_str))?;
        } else {
            self.repository.save(building_name, &building_data)?;
        }

        Ok(())
    }

    /// List all rooms in a building
    pub fn list_rooms(
        &self,
        building_name: &str,
    ) -> Result<Vec<Room>, Box<dyn std::error::Error + Send + Sync>> {
        let building_data = self.repository.load(building_name)?;
        let mut rooms = Vec::new();

        for floor in &building_data.floors {
            // Collect rooms from wings (primary location)
            for wing in &floor.wings {
                rooms.extend(wing.rooms.iter().cloned());
            }
        }

        Ok(rooms)
    }

    /// Get a specific room by name
    pub fn get_room(
        &self,
        building_name: &str,
        room_name: &str,
    ) -> Result<Option<Room>, Box<dyn std::error::Error + Send + Sync>> {
        let building_data = self.repository.load(building_name)?;

        for floor in &building_data.floors {
            // Search in wings first (primary location)
            for wing in &floor.wings {
                if let Some(room) = wing.rooms.iter().find(|r| r.name == room_name) {
                    return Ok(Some(room.clone()));
                }
            }
        }

        Ok(None)
    }
}

impl Default for RoomService {
    fn default() -> Self {
        Self::with_file_repository()
    }
}
