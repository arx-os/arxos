//! Fallback IFC parser using custom STEP parsing
//!
//! This module is split into focused components:
//! - reader: File reading and validation
//! - entity_extractor: Entity parsing from STEP format
//! - building_extractor: Building data extraction
//! - spatial_extractor: Spatial data extraction
//! - error_recovery: Error handling and recovery
//! - types: Type definitions

mod building_extractor;
mod entity_extractor;
mod error_recovery;
mod reader;
mod spatial_extractor;
mod types;

pub use building_extractor::BuildingExtractor;
pub use entity_extractor::EntityExtractor;
pub use error_recovery::ErrorRecovery;
pub use reader::IFCReader;
pub use spatial_extractor::SpatialExtractor;
pub use types::IFCEntity;

use crate::core::Building;
use crate::spatial::SpatialEntity;
use crate::utils::progress::ProgressContext;
use log::info;
use rayon::prelude::*;

/// Fallback IFC parser using custom STEP parsing
pub struct FallbackIFCParser {
    reader: IFCReader,
    entity_extractor: EntityExtractor,
    building_extractor: BuildingExtractor,
    spatial_extractor: SpatialExtractor,
    error_recovery: ErrorRecovery,
}

impl Default for FallbackIFCParser {
    fn default() -> Self {
        Self::new()
    }
}

impl FallbackIFCParser {
    pub fn new() -> Self {
        Self {
            reader: IFCReader::new(),
            entity_extractor: EntityExtractor::new(),
            building_extractor: BuildingExtractor::new(),
            spatial_extractor: SpatialExtractor::new(),
            error_recovery: ErrorRecovery::new(),
        }
    }

    pub fn parse_ifc_file(
        &self,
        file_path: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Using custom STEP parser for: {}", file_path);

        let content = self.reader.read_file(file_path)?;
        let (building, spatial_entities) = self.parse_step_content(&content)?;

        info!(
            "Parsed building: {} with {} spatial entities",
            building.name,
            spatial_entities.len()
        );
        Ok((building, spatial_entities))
    }

    pub fn parse_ifc_file_parallel(
        &self,
        file_path: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Using parallel custom STEP parser for: {}", file_path);

        let content = self.reader.read_file(file_path)?;
        let (building, spatial_entities) = self.parse_step_content_parallel(&content)?;

        info!(
            "Parsed building: {} with {} spatial entities (parallel)",
            building.name,
            spatial_entities.len()
        );
        Ok((building, spatial_entities))
    }

    pub fn parse_ifc_file_with_progress(
        &self,
        file_path: &str,
        progress: ProgressContext,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Using custom STEP parser with progress for: {}", file_path);

        progress.update(25, "Validating file path...");
        let content = self.reader.read_file(file_path)?;

        progress.update(50, "Parsing STEP entities...");
        let (building, spatial_entities) =
            self.parse_step_content_with_progress(&content, progress)?;

        info!(
            "Parsed building: {} with {} spatial entities (with progress)",
            building.name,
            spatial_entities.len()
        );
        Ok((building, spatial_entities))
    }

    pub fn extract_entities(
        &self,
        content: &str,
    ) -> Result<Vec<IFCEntity>, Box<dyn std::error::Error>> {
        self.entity_extractor.extract_entities(content)
    }

    fn parse_step_content(
        &self,
        content: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        let entities = self.entity_extractor.extract_entities(content)?;

        let building = self.building_extractor.extract_building(&entities);

        let spatial_entities: Vec<SpatialEntity> = entities
            .iter()
            .filter(|e| self.spatial_extractor.is_spatial_entity(&e.entity_type))
            .filter_map(|e| self.spatial_extractor.extract_spatial_data(e))
            .collect();

        Ok((building, spatial_entities))
    }

    fn parse_step_content_parallel(
        &self,
        content: &str,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        let entities = self.entity_extractor.extract_entities(content)?;

        let building = self.building_extractor.extract_building(&entities);

        let spatial_entities: Vec<SpatialEntity> = entities
            .par_iter()
            .filter(|e| self.spatial_extractor.is_spatial_entity(&e.entity_type))
            .filter_map(|e| self.spatial_extractor.extract_spatial_data(e))
            .collect();

        Ok((building, spatial_entities))
    }

    fn parse_step_content_with_progress(
        &self,
        content: &str,
        progress: ProgressContext,
    ) -> Result<(Building, Vec<SpatialEntity>), Box<dyn std::error::Error>> {
        let lines: Vec<&str> = content.lines().collect();
        let total_lines = lines.len();

        let mut entities = Vec::new();

        progress.update(60, "Processing STEP entities...");

        for (i, line) in lines.iter().enumerate() {
            if line.starts_with("#") && line.contains("=") {
                match self.entity_extractor.parse_entity_line(line) {
                    Some(entity) => entities.push(entity),
                    None => {
                        // Try error recovery
                        if let Some(recovered) =
                            self.error_recovery.recover_entity(line, "Parse error")
                        {
                            entities.push(recovered);
                        }
                    }
                }
            }

            if i % 100 == 0 {
                let progress_percent = 60 + ((i * 30) / total_lines);
                progress.update(
                    progress_percent as u32,
                    &format!("Processing line {}/{}", i, total_lines),
                );
            }
        }

        progress.update(85, "Extracting building data...");
        let building = self.building_extractor.extract_building(&entities);

        progress.update(90, "Extracting spatial data...");
        let spatial_entities: Vec<SpatialEntity> = entities
            .iter()
            .filter(|e| self.spatial_extractor.is_spatial_entity(&e.entity_type))
            .filter_map(|e| {
                self.spatial_extractor
                    .extract_spatial_data(e)
                    .or_else(|| self.error_recovery.recover_spatial(e))
            })
            .collect();

        progress.update(100, "Complete");
        Ok((building, spatial_entities))
    }
}
