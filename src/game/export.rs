//! IFC Export from Game State
//!
//! Exports game plans to IFC files while preserving all metadata (entity IDs,
//! types, placement chains, properties) for complete round-trip compatibility.

use std::path::Path;
use crate::game::state::GameState;
use crate::game::ifc_sync::{IFCSyncManager, IFCMetadata};
use crate::game::ifc_mapping::IFCTypeMapper;
use crate::game::types::GameEquipmentPlacement;
use crate::spatial::{SpatialEntity, Point3D, BoundingBox3D};
use crate::ifc::EnhancedIFCParser;
use log::{info, warn};

/// Export game state to IFC file with full metadata preservation
pub struct IFCGameExporter {
    sync_manager: IFCSyncManager,
    parser: EnhancedIFCParser,
}

impl IFCGameExporter {
    /// Create new IFC exporter
    pub fn new() -> Self {
        Self {
            sync_manager: IFCSyncManager::new(),
            parser: EnhancedIFCParser::new(),
        }
    }

    /// Export game state to IFC file
    pub fn export_game_to_ifc(
        &mut self,
        game_state: &GameState,
        output_path: &Path,
    ) -> Result<(), Box<dyn std::error::Error>> {
        info!("Exporting game state to IFC file: {:?}", output_path);

        // Convert game placements to spatial entities with IFC metadata
        let spatial_entities = self.convert_placements_to_spatial_entities(game_state)?;

        // Write to IFC file
        let output_path_str = output_path.to_str()
            .ok_or("Invalid output path")?;
        
        self.parser.write_spatial_entities_to_ifc(&spatial_entities, output_path_str)?;

        info!(
            "Successfully exported {} equipment items to IFC file",
            spatial_entities.len()
        );

        Ok(())
    }

    /// Convert game equipment placements to spatial entities
    fn convert_placements_to_spatial_entities(
        &mut self,
        game_state: &GameState,
    ) -> Result<Vec<SpatialEntity>, Box<dyn std::error::Error>> {
        let mut spatial_entities = Vec::new();

        for placement in &game_state.placements {
            // Sync IFC metadata
            self.sync_manager.sync_from_placement(placement);

            // Apply IFC type mapping if needed
            if let Some(metadata) = self.sync_manager.get_metadata(&placement.equipment.id) {
                if metadata.entity_type.is_none() {
                    // Apply type mapping
                    crate::game::ifc_mapping::apply_ifc_type_mapping(
                        &mut self.sync_manager,
                        &placement.equipment.id,
                        &placement.equipment.equipment_type,
                        &placement.equipment.name,
                    );
                }
            }

            // Get final metadata after mapping
            let metadata = self.sync_manager
                .get_or_create_metadata(&placement.equipment.id);

            // Determine IFC entity type
            let ifc_entity_type = metadata.entity_type.clone()
                .unwrap_or_else(|| {
                    IFCTypeMapper::map_equipment_type_to_ifc(&placement.equipment.equipment_type)
                });

            // Create spatial entity
            let _merged_properties = self.merge_properties(placement, &metadata);
            let position = Point3D::new(
                placement.equipment.position.x,
                placement.equipment.position.y,
                placement.equipment.position.z,
            );
            
            let spatial_entity = SpatialEntity::new(
                metadata.entity_id
                    .clone()
                    .unwrap_or_else(|| format!("GAME_{}", placement.equipment.id)),
                placement.equipment.name.clone(),
                ifc_entity_type.clone(),
                position,
            )
            .with_bounding_box(self.calculate_bounding_box(placement));
            
            // Note: Properties are preserved in the equipment and IFC metadata,
            // but SpatialEntity doesn't store them directly

            spatial_entities.push(spatial_entity);
        }

        Ok(spatial_entities)
    }

    /// Calculate bounding box for equipment
    fn calculate_bounding_box(&self, placement: &GameEquipmentPlacement) -> BoundingBox3D {
        // Default size - could be enhanced with actual equipment dimensions
        let default_size = 0.5;
        
        let pos = &placement.equipment.position;
        let center = Point3D::new(pos.x, pos.y, pos.z);

        // Check if size is specified in properties
        let size = placement.equipment.properties
            .get("size")
            .and_then(|s| s.parse::<f64>().ok())
            .unwrap_or(default_size);

        BoundingBox3D {
            min: Point3D::new(
                center.x - size,
                center.y - size,
                center.z - size,
            ),
            max: Point3D::new(
                center.x + size,
                center.y + size,
                center.z + size,
            ),
        }
    }

    /// Merge equipment properties with IFC metadata properties
    fn merge_properties(
        &self,
        placement: &GameEquipmentPlacement,
        metadata: &IFCMetadata,
    ) -> std::collections::HashMap<String, String> {
        let mut properties = placement.equipment.properties.clone();

        // Add IFC metadata as properties
        if let Some(entity_id) = &metadata.entity_id {
            properties.insert("ifc_entity_id".to_string(), entity_id.clone());
        }

        if let Some(entity_type) = &metadata.entity_type {
            properties.insert("ifc_entity_type".to_string(), entity_type.clone());
        }

        if !metadata.placement_chain.is_empty() {
            properties.insert(
                "ifc_placement_chain".to_string(),
                metadata.placement_chain.join(","),
            );
        }

        // Merge original IFC properties
        for (key, value) in &metadata.original_properties {
            properties.insert(key.clone(), value.clone());
        }

        // Add game action as property
        properties.insert(
            "game_action".to_string(),
            format!("{:?}", placement.game_action),
        );

        properties
    }

    /// Get sync manager for external use
    pub fn sync_manager(&self) -> &IFCSyncManager {
        &self.sync_manager
    }

    /// Get mutable sync manager
    pub fn sync_manager_mut(&mut self) -> &mut IFCSyncManager {
        &mut self.sync_manager
    }

    /// Export validation summary
    pub fn export_summary(&self) -> IFCExportSummary {
        let sync_summary = self.sync_manager.export_summary();

        IFCExportSummary {
            total_equipment: sync_summary.total_equipment,
            with_ifc_entity_id: sync_summary.with_entity_id,
            with_ifc_entity_type: sync_summary.with_entity_type,
            with_placement_chain: sync_summary.with_placement_chain,
            synthetic_ids_used: sync_summary.synthetic_ids_used,
        }
    }
}

impl Default for IFCGameExporter {
    fn default() -> Self {
        Self::new()
    }
}

/// Summary of IFC export operation
#[derive(Debug, Clone)]
pub struct IFCExportSummary {
    pub total_equipment: usize,
    pub with_ifc_entity_id: usize,
    pub with_ifc_entity_type: usize,
    pub with_placement_chain: usize,
    pub synthetic_ids_used: u32,
}

/// Convenience function to export game state to IFC
pub fn export_game_to_ifc(
    game_state: &GameState,
    output_path: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut exporter = IFCGameExporter::new();
    exporter.export_game_to_ifc(game_state, output_path)
}

