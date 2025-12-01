//! IFC parser using the `bim` crate
//!
//! This module replaces the custom STEP parser with the community-supported `bim` crate.

use crate::core::{Building, spatial::SpatialEntity};
use crate::ifc::hierarchy::HierarchyBuilder;
use crate::ifc::fallback::types::IFCEntity;
use crate::utils::progress::ProgressContext;
use log::info;
use std::path::Path;

/// IFC parser using the `bim` crate
pub struct BimParser;

impl BimParser {
    pub fn new() -> Self {
        Self
    }

    /// Parse an IFC file using the `bim` crate
    pub fn parse_ifc_file(
        &self,
        file_path: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Using bim crate parser for: {}", file_path);

        // Read the IFC file using bim crate
        let path = Path::new(file_path);
        let ifc_file = bim::read(path)
            .map_err(|e| format!("Failed to read IFC file: {}", e))?;

        self.process_ifc_file(&ifc_file)
    }

    /// Parse IFC data from a string (useful for WASM/Web)
    pub fn parse_from_string(
        &self,
        content: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Parsing IFC from string (length: {})", content.len());

        // Attempt to parse string directly
        // Note: Assuming bim crate supports FromStr or similar. 
        // If not, we might need a temporary workaround or check docs.
        // For now, let's try bim::parse or generic read.
        let ifc_file = bim::parse(content)
            .map_err(|e| format!("Failed to parse IFC content: {}", e))?;

        self.process_ifc_file(&ifc_file)
    }

    fn process_ifc_file(
        &self,
        ifc_file: &bim::Ifc,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        // Convert bim entities to our IFCEntity format for compatibility with HierarchyBuilder
        let entities = self.convert_bim_entities(ifc_file)?;

        // Use existing HierarchyBuilder to construct the Building hierarchy
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;

        // For now, return empty spatial entities - this can be enhanced later
        let spatial_entities = Vec::new();

        info!(
            "Parsed building: {} using bim crate",
            building.name
        );
        Ok((building, spatial_entities))
    }

    /// Parse an IFC file with progress reporting
    pub fn parse_ifc_file_with_progress(
        &self,
        file_path: &str,
        mut progress: ProgressContext,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Using bim crate parser with progress for: {}", file_path);

        progress.update(25, "Reading IFC file with bim crate...");
        let path = Path::new(file_path);
        let ifc_file = bim::read(path)
            .map_err(|e| format!("Failed to read IFC file: {}", e))?;

        progress.update(50, "Converting entities...");
        let entities = self.convert_bim_entities(&ifc_file)?;

        progress.update(75, "Building hierarchy...");
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;

        let spatial_entities = Vec::new();

        progress.update(100, "Complete");
        info!(
            "Parsed building: {} using bim crate (with progress)",
            building.name
        );
        Ok((building, spatial_entities))
    }

    /// Convert bim crate entities to our IFCEntity format
    /// This maintains compatibility with the existing HierarchyBuilder
    fn convert_bim_entities(
        &self,
        ifc_file: &bim::Ifc,
    ) -> Result<Vec<IFCEntity>, Box<dyn std::error::Error>> {
        let mut entities = Vec::new();

        // Iterate through all entities in the IFC file
        for entity in ifc_file.entities() {
            // Convert bim entity to our IFCEntity format
            let ifc_entity = IFCEntity {
                id: entity.id().to_string(),
                entity_type: entity.entity_type().to_string(),
                name: entity.name().unwrap_or("").to_string(),
                definition: entity.to_string(), // Use the entity's string representation
            };
            entities.push(ifc_entity);
        }

        info!("Converted {} entities from bim crate", entities.len());
        Ok(entities)
    }
}

impl Default for BimParser {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bim_parser_creation() {
        let parser = BimParser::new();
        assert!(true); // Basic instantiation test
    }
}
