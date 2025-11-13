//! IFC Sync Layer
//!
//! Preserves IFC metadata (entity IDs, types, placement chains, properties) when
//! equipment is used in game modes, ensuring round-trip compatibility with IFC files.

use crate::core::Equipment;
use crate::game::types::GameEquipmentPlacement;
use crate::spatial::Point3D;
use log::{info, warn};
use std::collections::HashMap;

/// IFC metadata for equipment placement
#[derive(Debug, Clone)]
pub struct IFCMetadata {
    /// Original IFC entity ID (e.g., "#123")
    pub entity_id: Option<String>,
    /// IFC entity type (e.g., "IFCLIGHTFIXTURE", "IFCAIRTERMINAL")
    pub entity_type: Option<String>,
    /// IFC placement chain references (parent placement entities)
    pub placement_chain: Vec<String>,
    /// Original IFC properties preserved from source file
    pub original_properties: HashMap<String, String>,
    /// IFC coordinate system information
    pub coordinate_system: Option<String>,
}

impl IFCMetadata {
    /// Create empty IFC metadata
    pub fn new() -> Self {
        Self {
            entity_id: None,
            entity_type: None,
            placement_chain: Vec::new(),
            original_properties: HashMap::new(),
            coordinate_system: None,
        }
    }

    /// Create IFC metadata from equipment placement
    pub fn from_placement(placement: &GameEquipmentPlacement) -> Self {
        Self {
            entity_id: placement.ifc_entity_id.clone(),
            entity_type: placement.ifc_entity_type.clone(),
            placement_chain: placement.ifc_placement_chain.clone().unwrap_or_default(),
            original_properties: placement.ifc_original_properties.clone(),
            coordinate_system: Some("IFC_COORDINATE_SYSTEM".to_string()),
        }
    }

    /// Check if metadata indicates this came from an IFC file
    pub fn is_from_ifc(&self) -> bool {
        self.entity_id.is_some() || self.entity_type.is_some()
    }

    /// Preserve metadata when updating equipment position
    pub fn with_position_update(&self, new_position: Point3D) -> Self {
        let mut updated = self.clone();
        // Update position-related properties if they exist
        updated.original_properties.insert(
            "ifc_last_position_x".to_string(),
            new_position.x.to_string(),
        );
        updated.original_properties.insert(
            "ifc_last_position_y".to_string(),
            new_position.y.to_string(),
        );
        updated.original_properties.insert(
            "ifc_last_position_z".to_string(),
            new_position.z.to_string(),
        );
        updated
    }
}

impl Default for IFCMetadata {
    fn default() -> Self {
        Self::new()
    }
}

/// IFC sync manager for preserving metadata across game operations
pub struct IFCSyncManager {
    /// Mapping from equipment ID to IFC metadata
    metadata_map: HashMap<String, IFCMetadata>,
    /// Track original IFC entity IDs for new game-created equipment
    next_synthetic_entity_id: u32,
}

impl IFCSyncManager {
    /// Create new IFC sync manager
    pub fn new() -> Self {
        Self {
            metadata_map: HashMap::new(),
            next_synthetic_entity_id: 10000, // Start synthetic IDs high to avoid conflicts
        }
    }

    /// Register equipment with IFC metadata
    pub fn register_equipment(&mut self, equipment_id: &str, metadata: IFCMetadata) {
        info!("Registering equipment '{}' with IFC metadata", equipment_id);
        self.metadata_map.insert(equipment_id.to_string(), metadata);
    }

    /// Get IFC metadata for equipment
    pub fn get_metadata(&self, equipment_id: &str) -> Option<&IFCMetadata> {
        self.metadata_map.get(equipment_id)
    }

    /// Get or create IFC metadata for equipment (creates synthetic ID if needed)
    pub fn get_or_create_metadata(&mut self, equipment_id: &str) -> IFCMetadata {
        if let Some(metadata) = self.metadata_map.get(equipment_id).cloned() {
            metadata
        } else {
            // Create synthetic IFC metadata for game-created equipment
            let synthetic_id = format!("#{}", self.next_synthetic_entity_id);
            self.next_synthetic_entity_id += 1;

            let metadata = IFCMetadata {
                entity_id: Some(synthetic_id),
                entity_type: None, // Will be set by type mapping
                placement_chain: Vec::new(),
                original_properties: HashMap::new(),
                coordinate_system: Some("BUILDING_LOCAL".to_string()),
            };

            self.register_equipment(equipment_id, metadata.clone());
            metadata
        }
    }

    /// Update metadata when equipment is moved
    pub fn update_position(&mut self, equipment_id: &str, new_position: Point3D) {
        if let Some(metadata) = self.metadata_map.get_mut(equipment_id) {
            metadata.original_properties.insert(
                "ifc_last_position_x".to_string(),
                new_position.x.to_string(),
            );
            metadata.original_properties.insert(
                "ifc_last_position_y".to_string(),
                new_position.y.to_string(),
            );
            metadata.original_properties.insert(
                "ifc_last_position_z".to_string(),
                new_position.z.to_string(),
            );
            info!(
                "Updated position in IFC metadata for equipment '{}'",
                equipment_id
            );
        }
    }

    /// Set IFC entity type for equipment
    pub fn set_entity_type(&mut self, equipment_id: &str, entity_type: String) {
        if let Some(metadata) = self.metadata_map.get_mut(equipment_id) {
            let entity_type_clone = entity_type.clone();
            metadata.entity_type = Some(entity_type);
            info!(
                "Set IFC entity type '{}' for equipment '{}'",
                entity_type_clone, equipment_id
            );
        } else {
            warn!(
                "Cannot set entity type for unregistered equipment: {}",
                equipment_id
            );
        }
    }

    /// Add to placement chain
    pub fn add_placement_chain(&mut self, equipment_id: &str, placement_ref: String) {
        if let Some(metadata) = self.metadata_map.get_mut(equipment_id) {
            metadata.placement_chain.push(placement_ref);
        }
    }

    /// Extract IFC metadata from equipment placement and register it
    pub fn sync_from_placement(&mut self, placement: &GameEquipmentPlacement) {
        let metadata = IFCMetadata::from_placement(placement);
        self.register_equipment(&placement.equipment.id, metadata);
    }

    /// Apply IFC metadata to equipment placement
    pub fn apply_to_placement(&self, placement: &mut GameEquipmentPlacement) {
        if let Some(metadata) = self.get_metadata(&placement.equipment.id) {
            placement.ifc_entity_id = metadata.entity_id.clone();
            placement.ifc_entity_type = metadata.entity_type.clone();
            placement.ifc_placement_chain = if metadata.placement_chain.is_empty() {
                None
            } else {
                Some(metadata.placement_chain.clone())
            };

            // Merge original properties
            for (key, value) in &metadata.original_properties {
                if !placement.equipment.properties.contains_key(key) {
                    placement
                        .equipment
                        .properties
                        .insert(key.clone(), value.clone());
                }
                placement
                    .ifc_original_properties
                    .insert(key.clone(), value.clone());
            }
        }
    }

    /// Get all registered equipment IDs
    pub fn registered_equipment(&self) -> Vec<String> {
        self.metadata_map.keys().cloned().collect()
    }

    /// Clear all metadata
    pub fn clear(&mut self) {
        self.metadata_map.clear();
        self.next_synthetic_entity_id = 10000;
    }

    /// Export metadata summary for debugging
    pub fn export_summary(&self) -> IFCSyncSummary {
        let total = self.metadata_map.len();
        let with_entity_id = self
            .metadata_map
            .values()
            .filter(|m| m.entity_id.is_some())
            .count();
        let with_entity_type = self
            .metadata_map
            .values()
            .filter(|m| m.entity_type.is_some())
            .count();
        let with_placement_chain = self
            .metadata_map
            .values()
            .filter(|m| !m.placement_chain.is_empty())
            .count();

        IFCSyncSummary {
            total_equipment: total,
            with_entity_id,
            with_entity_type,
            with_placement_chain,
            synthetic_ids_used: self.next_synthetic_entity_id - 10000,
        }
    }
}

impl Default for IFCSyncManager {
    fn default() -> Self {
        Self::new()
    }
}

/// Summary of IFC sync status
#[derive(Debug, Clone)]
pub struct IFCSyncSummary {
    pub total_equipment: usize,
    pub with_entity_id: usize,
    pub with_entity_type: usize,
    pub with_placement_chain: usize,
    pub synthetic_ids_used: u32,
}

/// Helper to extract IFC metadata from equipment properties
pub fn extract_ifc_metadata_from_properties(equipment: &Equipment) -> IFCMetadata {
    let mut metadata = IFCMetadata::new();

    // Extract IFC entity ID
    if let Some(entity_id) = equipment.properties.get("ifc_entity_id") {
        metadata.entity_id = Some(entity_id.clone());
    }

    // Extract IFC entity type
    if let Some(entity_type) = equipment.properties.get("ifc_entity_type") {
        metadata.entity_type = Some(entity_type.clone());
    }

    // Extract placement chain
    if let Some(placement_chain_str) = equipment.properties.get("ifc_placement_chain") {
        metadata.placement_chain = placement_chain_str
            .split(',')
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect();
    }

    // Copy all IFC-related properties
    for (key, value) in &equipment.properties {
        if key.starts_with("ifc_") {
            metadata
                .original_properties
                .insert(key.clone(), value.clone());
        }
    }

    metadata
}

/// Helper to inject IFC metadata into equipment properties
pub fn inject_ifc_metadata_to_properties(equipment: &mut Equipment, metadata: &IFCMetadata) {
    if let Some(entity_id) = &metadata.entity_id {
        equipment
            .properties
            .insert("ifc_entity_id".to_string(), entity_id.clone());
    }

    if let Some(entity_type) = &metadata.entity_type {
        equipment
            .properties
            .insert("ifc_entity_type".to_string(), entity_type.clone());
    }

    if !metadata.placement_chain.is_empty() {
        equipment.properties.insert(
            "ifc_placement_chain".to_string(),
            metadata.placement_chain.join(","),
        );
    }

    // Merge original properties
    for (key, value) in &metadata.original_properties {
        equipment.properties.insert(key.clone(), value.clone());
    }
}
