//! Spatial data types and utilities

use nalgebra::Point3;
use serde::{Deserialize, Serialize};

/// 3D Point type alias
pub type Point3D = Point3<f64>;

/// Spatial entity trait
pub trait SpatialEntity: Send + Sync {
    fn position(&self) -> Point3D;
    fn set_position(&mut self, position: Point3D);
    fn id(&self) -> &str;
    fn name(&self) -> &str;
    fn entity_type(&self) -> &str;
    fn bounding_box(&self) -> &crate::core::spatial::BoundingBox3D;
}

/// Coordinate system information
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CoordinateSystem {
    pub name: String,
    pub origin: Point3D,
    pub x_axis: Point3D,
    pub y_axis: Point3D,
    pub z_axis: Point3D,
}

impl CoordinateSystem {
    pub fn new(name: String, origin: Point3D) -> Self {
        Self {
            name,
            origin,
            x_axis: Point3D::new(1.0, 0.0, 0.0),
            y_axis: Point3D::new(0.0, 1.0, 0.0),
            z_axis: Point3D::new(0.0, 0.0, 1.0),
        }
    }

    pub fn world() -> Self {
        Self::new("World".to_string(), Point3D::origin())
    }
}

/// Bounding box in 3D space
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BoundingBox {
    pub min: Point3D,
    pub max: Point3D,
}

impl BoundingBox {
    pub fn new(min: Point3D, max: Point3D) -> Self {
        Self { min, max }
    }

    pub fn contains(&self, point: &Point3D) -> bool {
        point.x >= self.min.x
            && point.x <= self.max.x
            && point.y >= self.min.y
            && point.y <= self.max.y
            && point.z >= self.min.z
            && point.z <= self.max.z
    }

    pub fn center(&self) -> Point3D {
        Point3D::new(
            (self.min.x + self.max.x) / 2.0,
            (self.min.y + self.max.y) / 2.0,
            (self.min.z + self.max.z) / 2.0,
        )
    }

    pub fn dimensions(&self) -> Point3D {
        Point3D::new(
            self.max.x - self.min.x,
            self.max.y - self.min.y,
            self.max.z - self.min.z,
        )
    }
}

/// 3D dimensions
pub type Dimensions = Point3D;

/// 3D position
pub type Position = Point3D;

/// Spatial properties for entities
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpatialProperties {
    pub position: Position,
    pub dimensions: Dimensions,
    pub bounding_box: BoundingBox,
    pub coordinate_system: String,
}

impl SpatialProperties {
    pub fn new(position: Position, dimensions: Dimensions) -> Self {
        let half = dimensions / 2.0;
        let min = Point3D::new(position.x - half.x, position.y - half.y, position.z - half.z);
        let max = Point3D::new(position.x + half.x, position.y + half.y, position.z + half.z);
        let bounding_box = BoundingBox::new(min, max);

        Self {
            position,
            dimensions,
            bounding_box,
            coordinate_system: "building_local".to_string(),
        }
    }
}

/// Result of a spatial query
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpatialQueryResult {
    pub entity_id: String,
    pub distance: f64,
    pub position: Position,
}

impl SpatialQueryResult {
    pub fn new(entity_id: String, distance: f64, position: Position) -> Self {
        Self {
            entity_id,
            distance,
            position,
        }
    }
}