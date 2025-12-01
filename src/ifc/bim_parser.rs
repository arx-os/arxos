//! IFC parser using the `ifc_rs` crate
//!
//! This module integrates the production-ready `ifc_rs` crate for IFC parsing.
//! The ifc_rs library provides robust IFC2X3, IFC4, and IFC4X3 parsing using winnow.

use crate::core::{Building, spatial::SpatialEntity};
use crate::ifc::hierarchy::HierarchyBuilder;
use crate::ifc::ifc_rs_converter::IFCRsConverter;
use crate::utils::progress::ProgressContext;
use log::info;

/// IFC parser using the `ifc_rs` crate
pub struct BimParser;

impl BimParser {
    pub fn new() -> Self {
        Self
    }

    /// Parse an IFC file using the `ifc_rs` crate
    pub fn parse_ifc_file(
        &self,
        file_path: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Parsing IFC file with ifc_rs: {}", file_path);
        
        // Parse IFC file using ifc_rs
        let ifc = ifc_rs::IFC::from_file(file_path)?;
        
        // Convert ifc_rs entities to ArxOS IFCEntity format
        let entities = IFCRsConverter::convert(&ifc)?;
        
        info!("Extracted {} entities from IFC file", entities.len());
        
        // Build hierarchy using existing HierarchyBuilder
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;
        
        // Spatial entities not currently extracted from IFC (future enhancement)
        let spatial_entities = Vec::new();
        
        info!("Successfully parsed building: {}", building.name);
        Ok((building, spatial_entities))
    }

    /// Parse IFC data from a string (useful for WASM/Web)
    pub fn parse_from_string(
        &self,
        content: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Parsing IFC from string with ifc_rs");
        
        // Parse IFC string using ifc_rs FromStr trait
        let ifc = content.parse::<ifc_rs::IFC>()?;
        
        // Convert ifc_rs entities to ArxOS IFCEntity format
        let entities = IFCRsConverter::convert(&ifc)?;
        
        info!("Extracted {} entities from IFC string", entities.len());
        
        // Build hierarchy using existing HierarchyBuilder
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;
        
        // Spatial entities not currently extracted from IFC (future enhancement)
        let spatial_entities = Vec::new();
        
        info!("Successfully parsed building: {}", building.name);
        Ok((building, spatial_entities))
    }

    /// Parse an IFC file with progress reporting
    pub fn parse_ifc_file_with_progress(
        &self,
        file_path: &str,
        mut progress: ProgressContext,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        progress.update(10, "Reading IFC file");
        
        // Parse IFC file using ifc_rs
        let ifc = ifc_rs::IFC::from_file(file_path)?;
        
        progress.update(40, "Converting entities");
        
        // Convert ifc_rs entities to ArxOS IFCEntity format
        let entities = IFCRsConverter::convert(&ifc)?;
        
        progress.update(70, "Building hierarchy");
        
        // Build hierarchy using existing HierarchyBuilder
        let hierarchy_builder = HierarchyBuilder::new(entities);
        let building = hierarchy_builder.build_hierarchy()?;
        
        progress.update(90, "Finalizing");
        
        // Spatial entities not currently extracted from IFC (future enhancement)
        let spatial_entities = Vec::new();
        
        progress.update(100, "Complete");
        
        info!("Successfully parsed building: {}", building.name);
        Ok((building, spatial_entities))
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
        let _parser = BimParser::new();
        assert!(true); // Basic instantiation test
    }
}
