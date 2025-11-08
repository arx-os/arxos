//! Error recovery for IFC parsing
//!
//! Handles parsing errors gracefully and provides fallback behavior.

use super::types::IFCEntity;
use crate::spatial::SpatialEntity;

/// Error recovery strategies for IFC parsing
pub struct ErrorRecovery;

impl ErrorRecovery {
    pub fn new() -> Self {
        Self
    }

    /// Recover from entity parsing errors
    ///
    /// Returns None if the entity cannot be recovered, otherwise returns the recovered entity
    pub fn recover_entity(&self, line: &str, _error: &str) -> Option<IFCEntity> {
        // Try to extract at least the ID and type even if full parsing fails
        if let Some(id_start) = line.find('#') {
            if let Some(id_end) = line[id_start + 1..].find('=') {
                let id = line[id_start + 1..id_start + 1 + id_end].to_string();

                // Try to extract entity type from the definition part
                let def_part = &line[id_start + 1 + id_end + 1..];
                let entity_type = if def_part.contains("IFC") {
                    // Extract IFC type name
                    if let Some(ifc_start) = def_part.find("IFC") {
                        if let Some(ifc_end) =
                            def_part[ifc_start..].find(|c: char| !c.is_uppercase() && c != '_')
                        {
                            def_part[ifc_start..ifc_start + ifc_end].to_string()
                        } else {
                            "UNKNOWN".to_string()
                        }
                    } else {
                        "UNKNOWN".to_string()
                    }
                } else {
                    "UNKNOWN".to_string()
                };

                return Some(IFCEntity {
                    id,
                    entity_type,
                    name: "Recovered".to_string(),
                    definition: line.to_string(),
                });
            }
        }

        None
    }

    /// Recover from spatial extraction errors
    ///
    /// Provides fallback spatial data when extraction fails
    pub fn recover_spatial(&self, entity: &IFCEntity) -> Option<SpatialEntity> {
        // Use default position and size for recovered entities
        use crate::spatial::{BoundingBox3D, Point3D};

        let position = Point3D::new(0.0, 0.0, 0.0);
        let bounding_box =
            BoundingBox3D::new(Point3D::new(-0.5, -0.5, -0.5), Point3D::new(0.5, 0.5, 0.5));

        Some(
            SpatialEntity::new(
                entity.id.clone(),
                entity.name.clone(),
                entity.entity_type.clone(),
                position,
            )
            .with_bounding_box(bounding_box),
        )
    }

    /// Check if an error is recoverable
    #[allow(dead_code)]
    pub fn is_recoverable(&self, error: &str) -> bool {
        // Most parsing errors are recoverable with fallback behavior
        !error.contains("FATAL") && !error.contains("CRITICAL")
    }
}

impl Default for ErrorRecovery {
    fn default() -> Self {
        Self::new()
    }
}
