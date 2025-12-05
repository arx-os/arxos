//! Core type definitions for spatial and building entities

use serde::{Deserialize, Serialize};

/// Position in 3D space with coordinate system
///
/// When serializing to YAML, this serializes as Point3D (omitting coordinate_system)
/// for backward compatibility. When deserializing, coordinate_system defaults to "building_local".
#[derive(Debug, Clone)]
pub struct Position {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub coordinate_system: String,
}

// Custom serialization to Point3D format (omits coordinate_system)
impl serde::Serialize for Position {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use crate::core::serde_helpers::serialize_position_as_point3d;
        serialize_position_as_point3d(self, serializer)
    }
}

// Custom deserialization from Point3D format (adds default coordinate_system)
impl<'de> serde::Deserialize<'de> for Position {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        use crate::core::serde_helpers::deserialize_point3d_as_position;
        deserialize_point3d_as_position(deserializer)
    }
}

/// Dimensions of a 3D object
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Dimensions {
    pub width: f64,
    pub height: f64,
    pub depth: f64,
}

/// Bounding box for spatial entities
///
/// When serializing to YAML, this serializes as BoundingBox3D (omitting coordinate systems)
/// for backward compatibility. When deserializing, coordinate systems default to "building_local".
#[derive(Debug, Clone)]
pub struct BoundingBox {
    pub min: Position,
    pub max: Position,
}

// Custom serialization to BoundingBox3D format (omits coordinate systems)
impl serde::Serialize for BoundingBox {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use crate::core::serde_helpers::serialize_bounding_box_as_bbox3d;
        serialize_bounding_box_as_bbox3d(self, serializer)
    }
}

// Custom deserialization from BoundingBox3D format (adds default coordinate systems)
impl<'de> serde::Deserialize<'de> for BoundingBox {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        use crate::core::serde_helpers::deserialize_bbox3d_as_bounding_box;
        deserialize_bbox3d_as_bounding_box(deserializer)
    }
}

impl BoundingBox {
    /// Create a new bounding box with validation
    ///
    /// # Arguments
    ///
    /// * `min` - Minimum position (should be less than max in all dimensions)
    /// * `max` - Maximum position (should be greater than min in all dimensions)
    ///
    /// # Panics
    ///
    /// Panics if `min` is not less than `max` in any dimension (debug builds only).
    /// In release builds, invalid bounding boxes are allowed but may cause issues.
    pub fn new(min: Position, max: Position) -> Self {
        debug_assert!(
            min.x <= max.x && min.y <= max.y && min.z <= max.z,
            "BoundingBox min must be <= max in all dimensions"
        );
        Self { min, max }
    }

    /// Validate that the bounding box is well-formed
    ///
    /// Returns `true` if `min <= max` in all dimensions, `false` otherwise.
    pub fn is_valid(&self) -> bool {
        self.min.x <= self.max.x && self.min.y <= self.max.y && self.min.z <= self.max.z
    }
}

/// Spatial properties of an entity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialProperties {
    pub position: Position,
    pub dimensions: Dimensions,
    pub bounding_box: BoundingBox,
    pub mesh: Option<crate::core::spatial::mesh::Mesh>,
    pub coordinate_system: String,
}

impl SpatialProperties {
    pub fn new(position: Position, dimensions: Dimensions, coordinate_system: String) -> Self {
        let bounding_box = BoundingBox {
            min: Position {
                x: position.x - dimensions.width / 2.0,
                y: position.y - dimensions.depth / 2.0,
                z: position.z,
                coordinate_system: coordinate_system.clone(),
            },
            max: Position {
                x: position.x + dimensions.width / 2.0,
                y: position.y + dimensions.depth / 2.0,
                z: position.z + dimensions.height,
                coordinate_system: coordinate_system.clone(),
            },
        };

        Self {
            position,
            dimensions,
            bounding_box,
            mesh: None,
            coordinate_system,
        }
    }
}

impl Default for SpatialProperties {
    fn default() -> Self {
        let position = Position {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        };

        let dimensions = Dimensions {
            width: 10.0,
            height: 3.0,
            depth: 10.0,
        };

        Self::new(position, dimensions, "building_local".to_string())
    }
}

/// Result of a spatial query
#[derive(Debug, Clone)]
pub struct SpatialQueryResult {
    pub entity_name: String,
    pub entity_type: String,
    pub position: Position,
    pub distance: f64,
}
