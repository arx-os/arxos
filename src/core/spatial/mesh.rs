use serde::{Deserialize, Serialize};
use super::types::Point3D;

/// 3D Mesh geometry represented by vertices and triangle indices
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Mesh {
    /// List of unique vertices in the mesh
    pub vertices: Vec<Point3D>,
    /// Flattened list of triangle indices (0, 1, 2, 0, 2, 3...)
    /// Each triplet of indices forms a triangle referencing the vertices list.
    pub indices: Vec<u32>,
}

impl Mesh {
    /// Create a new mesh from vertices and indices
    pub fn new(vertices: Vec<Point3D>, indices: Vec<u32>) -> Self {
        Self { vertices, indices }
    }

    /// Create a simple tetrahedron mesh (4 vertices, 4 triangles)
    /// Useful for testing and default representations.
    pub fn tetrahedron(size: f64) -> Self {
        let h = size * (2.0f64.sqrt() / 3.0); // Height of regular tetrahedron
        let r = size * (6.0f64.sqrt() / 3.0); // Radius to vertex
        
        // Vertices for a regular tetrahedron
        let vertices = vec![
            Point3D::new(0.0, 0.0, h),              // Top
            Point3D::new(r, 0.0, 0.0),              // Base 1
            Point3D::new(-r/2.0, r*0.866, 0.0),     // Base 2
            Point3D::new(-r/2.0, -r*0.866, 0.0),    // Base 3
        ];

        // Indices (CCW winding)
        let indices = vec![
            0, 1, 2, // Side 1
            0, 2, 3, // Side 2
            0, 3, 1, // Side 3
            1, 3, 2, // Bottom
        ];

        Self::new(vertices, indices)
    }

    /// Validate the mesh topology
    pub fn validate(&self) -> bool {
        if self.indices.len() % 3 != 0 {
            return false;
        }
        let max_index = self.vertices.len() as u32;
        self.indices.iter().all(|&i| i < max_index)
    }
}
