//! Spatial anchor management for AR export
//! 
//! This module handles spatial anchors for ARKit/ARCore localization.

use crate::spatial::Point3D;
use std::collections::HashMap;
use std::path::Path;
use serde::{Serialize, Deserialize};

/// Spatial anchor for AR localization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialAnchor {
    /// Unique identifier for the anchor
    pub id: String,
    /// Position in 3D space
    pub position: Point3D,
    /// Rotation as quaternion (x, y, z, w)
    pub rotation: [f64; 4],
    /// Additional metadata
    pub metadata: HashMap<String, String>,
}

impl SpatialAnchor {
    /// Create a new spatial anchor
    pub fn new(id: String, position: Point3D) -> Self {
        Self {
            id,
            position,
            rotation: [0.0, 0.0, 0.0, 1.0], // Identity quaternion
            metadata: HashMap::new(),
        }
    }
    
    /// Create a spatial anchor with rotation
    pub fn with_rotation(mut self, rotation: [f64; 4]) -> Self {
        self.rotation = rotation;
        self
    }
    
    /// Add metadata to the anchor
    pub fn with_metadata(mut self, key: String, value: String) -> Self {
        self.metadata.insert(key, value);
        self
    }
}

/// Export spatial anchors to JSON
pub fn export_anchors_to_json(anchors: &[SpatialAnchor], output: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let json = serde_json::to_string_pretty(anchors)?;
    std::fs::write(output, json)?;
    Ok(())
}

/// Import spatial anchors from JSON
pub fn import_anchors_from_json(input: &Path) -> Result<Vec<SpatialAnchor>, Box<dyn std::error::Error>> {
    let json = std::fs::read_to_string(input)?;
    let anchors: Vec<SpatialAnchor> = serde_json::from_str(&json)?;
    Ok(anchors)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_spatial_anchor_creation() {
        let anchor = SpatialAnchor::new(
            "anchor1".to_string(),
            Point3D { x: 1.0, y: 2.0, z: 3.0 },
        );
        assert_eq!(anchor.id, "anchor1");
        assert_eq!(anchor.position.x, 1.0);
    }
    
    #[test]
    fn test_spatial_anchor_serialization() {
        let anchor = SpatialAnchor::new(
            "test".to_string(),
            Point3D { x: 0.0, y: 0.0, z: 0.0 },
        );
        let json = serde_json::to_string(&anchor).unwrap();
        assert!(json.contains("\"id\":\"test\""));
    }
}

