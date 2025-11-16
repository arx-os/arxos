// Spatial data types for ArxOS
use serde::{Deserialize, Serialize};
use std::fmt;

/// 3D Point in space
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Point3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Point3D {
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }

    pub fn origin() -> Self {
        Self {
            x: 0.0,
            y: 0.0,
            z: 0.0,
        }
    }

    /// Calculate distance to another point
    pub fn distance_to(&self, other: &Point3D) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        let dz = self.z - other.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    /// Access by index (0=x, 1=y, 2=z) for nalgebra compatibility
    pub fn get(&self, index: usize) -> Option<f64> {
        match index {
            0 => Some(self.x),
            1 => Some(self.y),
            2 => Some(self.z),
            _ => None,
        }
    }

    /// Add two points (vector addition)
    pub fn add(&self, other: &Point3D) -> Point3D {
        Point3D::new(self.x + other.x, self.y + other.y, self.z + other.z)
    }

    /// Subtract two points (vector subtraction)
    pub fn sub(&self, other: &Point3D) -> Point3D {
        Point3D::new(self.x - other.x, self.y - other.y, self.z - other.z)
    }

    /// Scale by a factor
    pub fn scale(&self, factor: f64) -> Point3D {
        Point3D::new(self.x * factor, self.y * factor, self.z * factor)
    }

    /// Dot product with another point
    pub fn dot(&self, other: &Point3D) -> f64 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }

    /// Calculate the magnitude (length) of the vector from origin to this point
    pub fn magnitude(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    /// Normalize to unit vector
    pub fn normalize(&self) -> Point3D {
        let mag = self.magnitude();
        if mag > 0.0 {
            self.scale(1.0 / mag)
        } else {
            *self
        }
    }
}

impl fmt::Display for Point3D {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({:.2}, {:.2}, {:.2})", self.x, self.y, self.z)
    }
}

// Conversion from nalgebra Point3 to custom Point3D
impl From<nalgebra::Point3<f64>> for Point3D {
    fn from(p: nalgebra::Point3<f64>) -> Self {
        Self::new(p.x, p.y, p.z)
    }
}

// Conversion from custom Point3D to nalgebra Point3
impl From<Point3D> for nalgebra::Point3<f64> {
    fn from(p: Point3D) -> Self {
        nalgebra::Point3::new(p.x, p.y, p.z)
    }
}

/// 3D Bounding Box
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BoundingBox3D {
    pub min: Point3D,
    pub max: Point3D,
}

impl BoundingBox3D {
    pub fn new(min: Point3D, max: Point3D) -> Self {
        Self { min, max }
    }

    pub fn from_points(points: &[Point3D]) -> Option<Self> {
        if points.is_empty() {
            return None;
        }

        let mut min_x = points[0].x;
        let mut min_y = points[0].y;
        let mut min_z = points[0].z;
        let mut max_x = points[0].x;
        let mut max_y = points[0].y;
        let mut max_z = points[0].z;

        for point in points.iter().skip(1) {
            min_x = min_x.min(point.x);
            min_y = min_y.min(point.y);
            min_z = min_z.min(point.z);
            max_x = max_x.max(point.x);
            max_y = max_y.max(point.y);
            max_z = max_z.max(point.z);
        }

        Some(Self {
            min: Point3D::new(min_x, min_y, min_z),
            max: Point3D::new(max_x, max_y, max_z),
        })
    }

    pub fn center(&self) -> Point3D {
        Point3D::new(
            (self.min.x + self.max.x) / 2.0,
            (self.min.y + self.max.y) / 2.0,
            (self.min.z + self.max.z) / 2.0,
        )
    }

    pub fn volume(&self) -> f64 {
        (self.max.x - self.min.x) * (self.max.y - self.min.y) * (self.max.z - self.min.z)
    }
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

/// Spatial entity with position and bounds
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpatialEntity {
    pub id: String,
    pub name: String,
    pub entity_type: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub coordinate_system: Option<CoordinateSystem>,
}

impl SpatialEntity {
    pub fn new(id: String, name: String, entity_type: String, position: Point3D) -> Self {
        // Create a default bounding box around the position
        let bounding_box = BoundingBox3D::new(
            Point3D::new(position.x - 0.5, position.y - 0.5, position.z - 0.5),
            Point3D::new(position.x + 0.5, position.y + 0.5, position.z + 0.5),
        );

        Self {
            id,
            name,
            entity_type,
            position,
            bounding_box,
            coordinate_system: None,
        }
    }

    pub fn with_bounding_box(mut self, bounding_box: BoundingBox3D) -> Self {
        self.bounding_box = bounding_box;
        self
    }

    pub fn with_coordinate_system(mut self, coordinate_system: CoordinateSystem) -> Self {
        self.coordinate_system = Some(coordinate_system);
        self
    }

    // Accessor methods (for compatibility with code expecting trait-like interface)
    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn entity_type(&self) -> &str {
        &self.entity_type
    }

    pub fn position(&self) -> Point3D {
        self.position
    }

    pub fn bounding_box(&self) -> &BoundingBox3D {
        &self.bounding_box
    }

    pub fn set_position(&mut self, position: Point3D) {
        self.position = position;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_point3d_creation() {
        let point = Point3D::new(1.0, 2.0, 3.0);
        assert_eq!(point.x, 1.0);
        assert_eq!(point.y, 2.0);
        assert_eq!(point.z, 3.0);
    }

    #[test]
    fn test_point3d_distance() {
        let p1 = Point3D::new(0.0, 0.0, 0.0);
        let p2 = Point3D::new(3.0, 4.0, 0.0);
        assert_eq!(p1.distance_to(&p2), 5.0);
    }

    #[test]
    fn test_bounding_box_from_points() {
        let points = vec![
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(1.0, 1.0, 1.0),
            Point3D::new(-1.0, -1.0, -1.0),
        ];

        let bbox = BoundingBox3D::from_points(&points).unwrap();
        assert_eq!(bbox.min, Point3D::new(-1.0, -1.0, -1.0));
        assert_eq!(bbox.max, Point3D::new(1.0, 1.0, 1.0));
    }

    #[test]
    fn test_spatial_entity_creation() {
        let entity = SpatialEntity::new(
            "test-1".to_string(),
            "Test Equipment".to_string(),
            "HVAC".to_string(),
            Point3D::new(10.0, 20.0, 30.0),
        );

        assert_eq!(entity.id, "test-1");
        assert_eq!(entity.position, Point3D::new(10.0, 20.0, 30.0));
    }

    #[test]
    fn test_point3d_math_operations() {
        let p1 = Point3D::new(1.0, 2.0, 3.0);
        let p2 = Point3D::new(4.0, 5.0, 6.0);

        // Addition
        let sum = p1.add(&p2);
        assert_eq!(sum, Point3D::new(5.0, 7.0, 9.0));

        // Subtraction
        let diff = p2.sub(&p1);
        assert_eq!(diff, Point3D::new(3.0, 3.0, 3.0));

        // Scaling
        let scaled = p1.scale(2.0);
        assert_eq!(scaled, Point3D::new(2.0, 4.0, 6.0));

        // Dot product
        let dot = p1.dot(&p2);
        assert_eq!(dot, 32.0); // 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
    }

    #[test]
    fn test_point3d_magnitude_normalize() {
        let p = Point3D::new(3.0, 4.0, 0.0);
        assert_eq!(p.magnitude(), 5.0);

        let normalized = p.normalize();
        assert!((normalized.magnitude() - 1.0).abs() < 1e-10);
        assert_eq!(normalized, Point3D::new(0.6, 0.8, 0.0));
    }

    #[test]
    fn test_point3d_get_index() {
        let p = Point3D::new(1.0, 2.0, 3.0);
        assert_eq!(p.get(0), Some(1.0));
        assert_eq!(p.get(1), Some(2.0));
        assert_eq!(p.get(2), Some(3.0));
        assert_eq!(p.get(3), None);
    }

    #[test]
    fn test_from_nalgebra_point3() {
        let na_point = nalgebra::Point3::new(1.0, 2.0, 3.0);
        let custom_point: Point3D = na_point.into();
        assert_eq!(custom_point.x, 1.0);
        assert_eq!(custom_point.y, 2.0);
        assert_eq!(custom_point.z, 3.0);
    }

    #[test]
    fn test_to_nalgebra_point3() {
        let custom_point = Point3D::new(1.0, 2.0, 3.0);
        let na_point: nalgebra::Point3<f64> = custom_point.into();
        assert_eq!(na_point.x, 1.0);
        assert_eq!(na_point.y, 2.0);
        assert_eq!(na_point.z, 3.0);
    }

    #[test]
    fn test_roundtrip_conversion() {
        let original = Point3D::new(1.5, 2.5, 3.5);
        let na_point: nalgebra::Point3<f64> = original.into();
        let back: Point3D = na_point.into();
        assert_eq!(original, back);
    }
}
