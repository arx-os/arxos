//! Building data extraction from IFC entities
//!
//! Extracts building information and hierarchy from IFC entities.

use super::types::IFCEntity;
use crate::core::Building;

/// Extracts building data from IFC entities
pub struct BuildingExtractor;

impl BuildingExtractor {
    pub fn new() -> Self {
        Self
    }

    /// Extract building information from entities
    pub fn extract_building(&self, entities: &[IFCEntity]) -> Building {
        let mut building_name = "Unknown Building".to_string();
        let mut building_id = "unknown".to_string();

        // Find IFCBUILDING entity
        for entity in entities {
            if entity.entity_type == "IFCBUILDING" {
                building_name = entity.name.clone();
                building_id = entity.id.clone();
                break;
            }
        }

        Building::new(building_id, building_name)
    }
}

impl Default for BuildingExtractor {
    fn default() -> Self {
        Self::new()
    }
}
