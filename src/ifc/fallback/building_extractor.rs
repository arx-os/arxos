//! Building data extraction from IFC entities
//!
//! Extracts building information and hierarchy from IFC entities.

use super::types::IFCEntity;
use crate::core::Building;
use crate::ifc::identifiers::derive_building_identifiers;

/// Extracts building data from IFC entities
pub struct BuildingExtractor;

impl BuildingExtractor {
    pub fn new() -> Self {
        Self
    }

    /// Extract building information from entities
    pub fn extract_building(&self, entities: &[IFCEntity]) -> Building {
        let building_entity = entities.iter().find(|entity| entity.entity_type == "IFCBUILDING");

        let fallback_id = building_entity
            .map(|entity| entity.id.as_str())
            .unwrap_or("building");

        let identifiers = derive_building_identifiers(
            building_entity.map(|entity| entity.name.as_str()),
            fallback_id,
        );

        Building::new(
            identifiers.display_name.clone(),
            identifiers.canonical_path(),
        )
    }
}

impl Default for BuildingExtractor {
    fn default() -> Self {
        Self::new()
    }
}
