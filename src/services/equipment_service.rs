//! Equipment service for business logic operations
//!
//! Provides high-level operations for equipment management,
//! decoupled from persistence concerns.

use super::repository::{Repository, RepositoryRef};
use crate::core::Equipment;
use crate::yaml::{BuildingData, EquipmentData};
use std::sync::Arc;

/// Service for equipment operations
pub struct EquipmentService {
    repository: RepositoryRef,
}

impl EquipmentService {
    /// Create a new equipment service with the given repository
    pub fn new(repository: RepositoryRef) -> Self {
        Self { repository }
    }
    
    /// Create an equipment service with file-based repository (production)
    pub fn with_file_repository() -> Self {
        use super::repository::FileRepository;
        Self::new(Arc::new(FileRepository::new()))
    }
    
    /// Create an equipment service with in-memory repository (testing)
    pub fn with_memory_repository() -> Self {
        use super::repository::InMemoryRepository;
        Self::new(Arc::new(InMemoryRepository::new()))
    }
    
    /// Add equipment to a building
    pub fn add_equipment(
        &self,
        building_name: &str,
        room_name: Option<&str>,
        equipment: Equipment,
        commit: bool,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut building_data = self.repository.load(building_name)?;
        let equipment_data = self.equipment_to_equipment_data(&equipment);
        let equipment_name = equipment.name.clone();
        
        // Find room if specified
        if let Some(room_name) = room_name {
            for floor in &mut building_data.floors {
                for wing in &mut floor.wings {
                    if let Some(room) = wing.rooms.iter_mut().find(|r| r.name == room_name) {
                        room.equipment.push(equipment.id.clone());
                    }
                }
                // Also check legacy rooms list
                if let Some(room) = floor.rooms.iter_mut().find(|r| r.name == room_name) {
                    room.equipment.push(equipment.id.clone());
                }
                // Add to floor's equipment list
                floor.equipment.push(equipment_data.clone());
            }
        } else {
            // Add to first floor if no room specified
            if let Some(floor) = building_data.floors.first_mut() {
                floor.equipment.push(equipment_data);
            }
        }
        
        // Save
        if commit {
            let message_str = format!("Add equipment: {}", equipment_name);
            self.repository.save_and_commit(building_name, &building_data, Some(&message_str))?;
        } else {
            self.repository.save(building_name, &building_data)?;
        }
        
        Ok(())
    }
    
    /// List all equipment in a building
    pub fn list_equipment(&self, building_name: &str) -> Result<Vec<Equipment>, Box<dyn std::error::Error + Send + Sync>> {
        let building_data = self.repository.load(building_name)?;
        let mut equipment = Vec::new();
        
        for floor in &building_data.floors {
            for equipment_data in &floor.equipment {
                equipment.push(self.equipment_data_to_equipment(equipment_data));
            }
        }
        
        Ok(equipment)
    }
    
    /// Get equipment by ID
    pub fn get_equipment(&self, building_name: &str, equipment_id: &str) -> Result<Option<Equipment>, Box<dyn std::error::Error + Send + Sync>> {
        let building_data = self.repository.load(building_name)?;
        
        for floor in &building_data.floors {
            if let Some(equipment_data) = floor.equipment.iter().find(|e| e.id == equipment_id) {
                return Ok(Some(self.equipment_data_to_equipment(equipment_data)));
            }
        }
        
        Ok(None)
    }
    
    /// Convert Equipment to EquipmentData
    fn equipment_to_equipment_data(&self, equipment: &Equipment) -> EquipmentData {
        use crate::yaml::conversions::equipment_to_equipment_data;
        equipment_to_equipment_data(equipment)
    }
    
    /// Convert EquipmentData to Equipment
    fn equipment_data_to_equipment(&self, equipment_data: &EquipmentData) -> Equipment {
        use crate::yaml::conversions::equipment_data_to_equipment;
        equipment_data_to_equipment(equipment_data)
    }
}

impl Default for EquipmentService {
    fn default() -> Self {
        Self::with_file_repository()
    }
}

