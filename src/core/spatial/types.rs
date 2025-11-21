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
    /// Create a new 3D point with the given coordinates
    ///
    /// # Arguments
    ///
    /// * `x` - X coordinate
    /// * `y` - Y coordinate
    /// * `z` - Z coordinate
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let point = Point3D::new(1.0, 2.0, 3.0);
    /// assert_eq!(point.x, 1.0);
    /// assert_eq!(point.y, 2.0);
    /// assert_eq!(point.z, 3.0);
    /// ```
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }

    /// Create a point at the origin (0, 0, 0)
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let origin = Point3D::origin();
    /// assert_eq!(origin.x, 0.0);
    /// assert_eq!(origin.y, 0.0);
    /// assert_eq!(origin.z, 0.0);
    /// ```
    pub fn origin() -> Self {
        Self {
            x: 0.0,
            y: 0.0,
            z: 0.0,
        }
    }

    /// Calculate Euclidean distance to another point
    ///
    /// Uses the standard 3D distance formula: √((x₂-x₁)² + (y₂-y₁)² + (z₂-z₁)²)
    ///
    /// # Arguments
    ///
    /// * `other` - The point to measure distance to
    ///
    /// # Returns
    ///
    /// The distance as a positive f64 value
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p1 = Point3D::new(0.0, 0.0, 0.0);
    /// let p2 = Point3D::new(3.0, 4.0, 0.0);
    /// assert_eq!(p1.distance_to(&p2), 5.0);
    /// ```
    pub fn distance_to(&self, other: &Point3D) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        let dz = self.z - other.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    /// Access coordinate by index for compatibility with array-based libraries
    ///
    /// Provides array-style indexing for interoperability with libraries like nalgebra.
    ///
    /// # Arguments
    ///
    /// * `index` - The coordinate index: 0 for x, 1 for y, 2 for z
    ///
    /// # Returns
    ///
    /// * `Some(f64)` - The coordinate value if index is 0, 1, or 2
    /// * `None` - If index is out of bounds
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p = Point3D::new(1.0, 2.0, 3.0);
    /// assert_eq!(p.get(0), Some(1.0));
    /// assert_eq!(p.get(1), Some(2.0));
    /// assert_eq!(p.get(2), Some(3.0));
    /// assert_eq!(p.get(3), None);
    /// ```
    pub fn get(&self, index: usize) -> Option<f64> {
        match index {
            0 => Some(self.x),
            1 => Some(self.y),
            2 => Some(self.z),
            _ => None,
        }
    }

    /// Add two points using vector addition
    ///
    /// Performs component-wise addition: (x₁ + x₂, y₁ + y₂, z₁ + z₂)
    ///
    /// # Arguments
    ///
    /// * `other` - The point to add to this point
    ///
    /// # Returns
    ///
    /// A new point representing the sum
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p1 = Point3D::new(1.0, 2.0, 3.0);
    /// let p2 = Point3D::new(4.0, 5.0, 6.0);
    /// let sum = p1.add(&p2);
    /// assert_eq!(sum, Point3D::new(5.0, 7.0, 9.0));
    /// ```
    pub fn add(&self, other: &Point3D) -> Point3D {
        Point3D::new(self.x + other.x, self.y + other.y, self.z + other.z)
    }

    /// Subtract two points using vector subtraction
    ///
    /// Performs component-wise subtraction: (x₁ - x₂, y₁ - y₂, z₁ - z₂)
    ///
    /// # Arguments
    ///
    /// * `other` - The point to subtract from this point
    ///
    /// # Returns
    ///
    /// A new point representing the difference
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p1 = Point3D::new(5.0, 7.0, 9.0);
    /// let p2 = Point3D::new(2.0, 3.0, 4.0);
    /// let diff = p1.sub(&p2);
    /// assert_eq!(diff, Point3D::new(3.0, 4.0, 5.0));
    /// ```
    pub fn sub(&self, other: &Point3D) -> Point3D {
        Point3D::new(self.x - other.x, self.y - other.y, self.z - other.z)
    }

    /// Scale the point by a scalar factor
    ///
    /// Multiplies each coordinate by the given factor: (x·f, y·f, z·f)
    ///
    /// # Arguments
    ///
    /// * `factor` - The scalar value to multiply by
    ///
    /// # Returns
    ///
    /// A new point with all coordinates scaled
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p = Point3D::new(1.0, 2.0, 3.0);
    /// let scaled = p.scale(2.0);
    /// assert_eq!(scaled, Point3D::new(2.0, 4.0, 6.0));
    /// ```
    pub fn scale(&self, factor: f64) -> Point3D {
        Point3D::new(self.x * factor, self.y * factor, self.z * factor)
    }

    /// Calculate the dot product with another point
    ///
    /// Computes the scalar dot product: x₁·x₂ + y₁·y₂ + z₁·z₂
    ///
    /// The dot product can be used to:
    /// - Measure the similarity of two vectors (positive = same direction)
    /// - Calculate projection of one vector onto another
    /// - Determine if vectors are perpendicular (dot product = 0)
    ///
    /// # Arguments
    ///
    /// * `other` - The point to compute dot product with
    ///
    /// # Returns
    ///
    /// The scalar dot product value
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p1 = Point3D::new(1.0, 2.0, 3.0);
    /// let p2 = Point3D::new(4.0, 5.0, 6.0);
    /// let dot = p1.dot(&p2);
    /// assert_eq!(dot, 32.0); // 1*4 + 2*5 + 3*6 = 32
    /// ```
    pub fn dot(&self, other: &Point3D) -> f64 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }

    /// Calculate the magnitude (length) of the vector from origin to this point
    ///
    /// Computes the Euclidean norm: √(x² + y² + z²)
    ///
    /// # Returns
    ///
    /// The length of the vector as a positive f64 value
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p = Point3D::new(3.0, 4.0, 0.0);
    /// assert_eq!(p.magnitude(), 5.0);
    /// ```
    pub fn magnitude(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    /// Normalize to a unit vector (magnitude = 1.0)
    ///
    /// Returns a new point in the same direction but with length 1.0.
    /// If the magnitude is zero, returns the original point unchanged.
    ///
    /// # Returns
    ///
    /// A new point with magnitude 1.0, or the original point if magnitude is 0
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::Point3D;
    /// let p = Point3D::new(3.0, 4.0, 0.0);
    /// let normalized = p.normalize();
    /// assert!((normalized.magnitude() - 1.0).abs() < 1e-10);
    /// assert!((normalized.x - 0.6).abs() < 1e-10);
    /// assert!((normalized.y - 0.8).abs() < 1e-10);
    /// assert!((normalized.z - 0.0).abs() < 1e-10);
    /// ```
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
    /// Create a new bounding box from min and max points
    ///
    /// # Arguments
    ///
    /// * `min` - The minimum corner point (smallest x, y, z)
    /// * `max` - The maximum corner point (largest x, y, z)
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{BoundingBox3D, Point3D};
    /// let bbox = BoundingBox3D::new(
    ///     Point3D::new(0.0, 0.0, 0.0),
    ///     Point3D::new(10.0, 10.0, 10.0),
    /// );
    /// assert_eq!(bbox.volume(), 1000.0);
    /// ```
    pub fn new(min: Point3D, max: Point3D) -> Self {
        Self { min, max }
    }

    /// Create a bounding box that tightly fits a set of points
    ///
    /// Calculates the minimum and maximum coordinates across all points
    /// to create the smallest axis-aligned bounding box that contains them all.
    ///
    /// # Arguments
    ///
    /// * `points` - Slice of points to bound
    ///
    /// # Returns
    ///
    /// * `Some(BoundingBox3D)` - The minimal bounding box containing all points
    /// * `None` - If the points slice is empty
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{BoundingBox3D, Point3D};
    /// let points = vec![
    ///     Point3D::new(0.0, 0.0, 0.0),
    ///     Point3D::new(1.0, 1.0, 1.0),
    ///     Point3D::new(-1.0, -1.0, -1.0),
    /// ];
    /// let bbox = BoundingBox3D::from_points(&points).unwrap();
    /// assert_eq!(bbox.min, Point3D::new(-1.0, -1.0, -1.0));
    /// assert_eq!(bbox.max, Point3D::new(1.0, 1.0, 1.0));
    /// ```
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

    /// Calculate the center point of the bounding box
    ///
    /// Returns the midpoint between the min and max corners.
    ///
    /// # Returns
    ///
    /// The center point with coordinates ((min+max)/2 for each axis)
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{BoundingBox3D, Point3D};
    /// let bbox = BoundingBox3D::new(
    ///     Point3D::new(0.0, 0.0, 0.0),
    ///     Point3D::new(10.0, 10.0, 10.0),
    /// );
    /// assert_eq!(bbox.center(), Point3D::new(5.0, 5.0, 5.0));
    /// ```
    pub fn center(&self) -> Point3D {
        Point3D::new(
            (self.min.x + self.max.x) / 2.0,
            (self.min.y + self.max.y) / 2.0,
            (self.min.z + self.max.z) / 2.0,
        )
    }

    /// Calculate the volume of the bounding box
    ///
    /// Computes the volume as (max.x - min.x) × (max.y - min.y) × (max.z - min.z)
    ///
    /// # Returns
    ///
    /// The volume in cubic units
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{BoundingBox3D, Point3D};
    /// let bbox = BoundingBox3D::new(
    ///     Point3D::new(0.0, 0.0, 0.0),
    ///     Point3D::new(2.0, 3.0, 4.0),
    /// );
    /// assert_eq!(bbox.volume(), 24.0);
    /// ```
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
    /// Create a new coordinate system with standard orthonormal axes
    ///
    /// Creates a right-handed coordinate system with the specified origin.
    /// The axes are initialized to standard unit vectors:
    /// - X-axis: (1, 0, 0)
    /// - Y-axis: (0, 1, 0)
    /// - Z-axis: (0, 0, 1)
    ///
    /// # Arguments
    ///
    /// * `name` - Descriptive name for this coordinate system
    /// * `origin` - The origin point of the coordinate system
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{CoordinateSystem, Point3D};
    /// let cs = CoordinateSystem::new(
    ///     "Building".to_string(),
    ///     Point3D::new(100.0, 200.0, 0.0),
    /// );
    /// assert_eq!(cs.name, "Building");
    /// assert_eq!(cs.origin, Point3D::new(100.0, 200.0, 0.0));
    /// ```
    pub fn new(name: String, origin: Point3D) -> Self {
        Self {
            name,
            origin,
            x_axis: Point3D::new(1.0, 0.0, 0.0),
            y_axis: Point3D::new(0.0, 1.0, 0.0),
            z_axis: Point3D::new(0.0, 0.0, 1.0),
        }
    }

    /// Create the world coordinate system at origin (0, 0, 0)
    ///
    /// This is the default global coordinate system with:
    /// - Name: "World"
    /// - Origin: (0, 0, 0)
    /// - Standard orthonormal axes
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{CoordinateSystem, Point3D};
    /// let world = CoordinateSystem::world();
    /// assert_eq!(world.name, "World");
    /// assert_eq!(world.origin, Point3D::origin());
    /// ```
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
    /// Create a new spatial entity with default bounding box
    ///
    /// Creates a spatial entity with a default 1×1×1 meter bounding box
    /// centered at the specified position.
    ///
    /// # Arguments
    ///
    /// * `id` - Unique identifier for this entity
    /// * `name` - Human-readable name
    /// * `entity_type` - Type classification (e.g., "Wall", "Door", "Equipment")
    /// * `position` - 3D position in space
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{SpatialEntity, Point3D};
    /// let entity = SpatialEntity::new(
    ///     "wall-001".to_string(),
    ///     "North Wall".to_string(),
    ///     "Wall".to_string(),
    ///     Point3D::new(10.0, 20.0, 0.0),
    /// );
    /// assert_eq!(entity.id, "wall-001");
    /// assert_eq!(entity.entity_type, "Wall");
    /// ```
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

    /// Set a custom bounding box for this entity (builder pattern)
    ///
    /// # Arguments
    ///
    /// * `bounding_box` - The bounding box to use
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{SpatialEntity, BoundingBox3D, Point3D};
    /// let entity = SpatialEntity::new(
    ///     "wall-001".to_string(),
    ///     "North Wall".to_string(),
    ///     "Wall".to_string(),
    ///     Point3D::new(10.0, 20.0, 0.0),
    /// ).with_bounding_box(BoundingBox3D::new(
    ///     Point3D::new(9.0, 19.0, -1.0),
    ///     Point3D::new(11.0, 21.0, 3.0),
    /// ));
    /// assert_eq!(entity.bounding_box.volume(), 16.0);  // 2.0 * 2.0 * 4.0
    /// ```
    pub fn with_bounding_box(mut self, bounding_box: BoundingBox3D) -> Self {
        self.bounding_box = bounding_box;
        self
    }

    /// Set a custom coordinate system for this entity (builder pattern)
    ///
    /// # Arguments
    ///
    /// * `coordinate_system` - The coordinate system to use
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::spatial::{SpatialEntity, CoordinateSystem, Point3D};
    /// let entity = SpatialEntity::new(
    ///     "wall-001".to_string(),
    ///     "North Wall".to_string(),
    ///     "Wall".to_string(),
    ///     Point3D::new(10.0, 20.0, 0.0),
    /// ).with_coordinate_system(CoordinateSystem::world());
    /// assert!(entity.coordinate_system.is_some());
    /// ```
    pub fn with_coordinate_system(mut self, coordinate_system: CoordinateSystem) -> Self {
        self.coordinate_system = Some(coordinate_system);
        self
    }

    // Accessor methods (for compatibility with code expecting trait-like interface)

    /// Get the entity's unique identifier
    pub fn id(&self) -> &str {
        &self.id
    }

    /// Get the entity's human-readable name
    pub fn name(&self) -> &str {
        &self.name
    }

    /// Get the entity's type classification
    pub fn entity_type(&self) -> &str {
        &self.entity_type
    }

    /// Get the entity's 3D position
    pub fn position(&self) -> Point3D {
        self.position
    }

    /// Get a reference to the entity's bounding box
    pub fn bounding_box(&self) -> &BoundingBox3D {
        &self.bounding_box
    }

    /// Update the entity's position
    ///
    /// # Arguments
    ///
    /// * `position` - The new 3D position
    ///
    /// # Note
    ///
    /// This does not automatically update the bounding box. If you need
    /// the bounding box to move with the position, you must update it separately.
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

        // Use epsilon comparison for floating-point values
        let expected = Point3D::new(0.6, 0.8, 0.0);
        assert!((normalized.x - expected.x).abs() < 1e-10);
        assert!((normalized.y - expected.y).abs() < 1e-10);
        assert!((normalized.z - expected.z).abs() < 1e-10);
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
