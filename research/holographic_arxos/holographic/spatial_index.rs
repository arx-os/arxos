//! Spatial Index for Efficient 3D Queries
//! 
//! Implements an Octree-based spatial index for O(log n) spatial queries
//! instead of O(n) linear searches.

use crate::holographic::fractal::FractalSpace;
use crate::holographic::quantum::ArxObjectId;
use crate::holographic::error::{Result, HolographicError};
use std::collections::HashMap;

/// 3D point for spatial indexing
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Point3D {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

impl Point3D {
    pub fn new(x: f32, y: f32, z: f32) -> Self {
        Self { x, y, z }
    }
    
    pub fn distance_squared(&self, other: &Self) -> f32 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        let dz = self.z - other.z;
        dx * dx + dy * dy + dz * dz
    }
}

/// Bounding box for octree nodes
#[derive(Clone, Debug)]
struct BoundingBox {
    min: Point3D,
    max: Point3D,
}

impl BoundingBox {
    fn new(min: Point3D, max: Point3D) -> Self {
        Self { min, max }
    }
    
    fn contains(&self, point: &Point3D) -> bool {
        point.x >= self.min.x && point.x <= self.max.x &&
        point.y >= self.min.y && point.y <= self.max.y &&
        point.z >= self.min.z && point.z <= self.max.z
    }
    
    fn intersects_sphere(&self, center: &Point3D, radius: f32) -> bool {
        // Find closest point on box to sphere center
        let closest_x = center.x.clamp(self.min.x, self.max.x);
        let closest_y = center.y.clamp(self.min.y, self.max.y);
        let closest_z = center.z.clamp(self.min.z, self.max.z);
        
        let closest = Point3D::new(closest_x, closest_y, closest_z);
        closest.distance_squared(center) <= radius * radius
    }
    
    fn center(&self) -> Point3D {
        Point3D::new(
            (self.min.x + self.max.x) / 2.0,
            (self.min.y + self.max.y) / 2.0,
            (self.min.z + self.max.z) / 2.0,
        )
    }
    
    fn subdivide(&self) -> [BoundingBox; 8] {
        let center = self.center();
        
        [
            // Bottom four
            BoundingBox::new(self.min, center),
            BoundingBox::new(
                Point3D::new(center.x, self.min.y, self.min.z),
                Point3D::new(self.max.x, center.y, center.z),
            ),
            BoundingBox::new(
                Point3D::new(self.min.x, center.y, self.min.z),
                Point3D::new(center.x, self.max.y, center.z),
            ),
            BoundingBox::new(
                Point3D::new(center.x, center.y, self.min.z),
                Point3D::new(self.max.x, self.max.y, center.z),
            ),
            // Top four
            BoundingBox::new(
                Point3D::new(self.min.x, self.min.y, center.z),
                Point3D::new(center.x, center.y, self.max.z),
            ),
            BoundingBox::new(
                Point3D::new(center.x, self.min.y, center.z),
                Point3D::new(self.max.x, center.y, self.max.z),
            ),
            BoundingBox::new(
                Point3D::new(self.min.x, center.y, center.z),
                Point3D::new(center.x, self.max.y, self.max.z),
            ),
            BoundingBox::new(center, self.max),
        ]
    }
}

/// Octree node for spatial indexing
enum OctreeNode {
    Leaf {
        objects: Vec<(ArxObjectId, Point3D)>,
    },
    Branch {
        children: Box<[OctreeNode; 8]>,
        bounds: [BoundingBox; 8],
    },
}

impl OctreeNode {
    fn new_leaf() -> Self {
        OctreeNode::Leaf {
            objects: Vec::new(),
        }
    }
    
    fn new_branch(bounds: BoundingBox) -> Self {
        let subdivided = bounds.subdivide();
        OctreeNode::Branch {
            children: Box::new([
                Self::new_leaf(),
                Self::new_leaf(),
                Self::new_leaf(),
                Self::new_leaf(),
                Self::new_leaf(),
                Self::new_leaf(),
                Self::new_leaf(),
                Self::new_leaf(),
            ]),
            bounds: subdivided,
        }
    }
}

/// Spatial index using octree for efficient 3D queries
pub struct SpatialIndex {
    root: OctreeNode,
    bounds: BoundingBox,
    max_depth: usize,
    max_objects_per_node: usize,
    pub object_positions: HashMap<ArxObjectId, Point3D>,
}

impl SpatialIndex {
    /// Create a new spatial index
    pub fn new(min: Point3D, max: Point3D) -> Self {
        Self {
            root: OctreeNode::new_leaf(),
            bounds: BoundingBox::new(min, max),
            max_depth: 8,
            max_objects_per_node: 16,
            object_positions: HashMap::new(),
        }
    }
    
    /// Insert an object at a position
    pub fn insert(&mut self, id: ArxObjectId, position: Point3D) -> Result<()> {
        if !self.bounds.contains(&position) {
            return Err(HolographicError::InvalidInput(
                "Position outside spatial index bounds".to_string()
            ));
        }
        
        // Remove old position if it exists
        if self.object_positions.contains_key(&id) {
            self.remove(id)?;
        }
        
        self.object_positions.insert(id, position);
        let bounds = self.bounds.clone();
        Self::insert_recursive(&mut self.root, id, position, &bounds, 0, self.max_objects_per_node, self.max_depth);
        Ok(())
    }
    
    fn insert_recursive(
        node: &mut OctreeNode,
        id: ArxObjectId,
        position: Point3D,
        bounds: &BoundingBox,
        depth: usize,
        max_objects_per_node: usize,
        max_depth: usize,
    ) {
        match node {
            OctreeNode::Leaf { objects } => {
                objects.push((id, position));
                
                // Split if too many objects and not at max depth
                if objects.len() > max_objects_per_node && depth < max_depth {
                    let new_branch = OctreeNode::new_branch(bounds.clone());
                    let old_objects = std::mem::replace(objects, Vec::new());
                    *node = new_branch;
                    
                    // Re-insert old objects
                    if let OctreeNode::Branch { .. } = node {
                        for (obj_id, obj_pos) in old_objects {
                            Self::insert_recursive(node, obj_id, obj_pos, bounds, depth, max_objects_per_node, max_depth);
                        }
                    }
                }
            }
            OctreeNode::Branch { children, bounds: child_bounds } => {
                // Find which child contains this position
                for i in 0..8 {
                    if child_bounds[i].contains(&position) {
                        Self::insert_recursive(&mut children[i], id, position, &child_bounds[i], depth + 1, max_objects_per_node, max_depth);
                        break;
                    }
                }
            }
        }
    }
    
    /// Remove an object from the index
    pub fn remove(&mut self, id: ArxObjectId) -> Result<()> {
        if let Some(position) = self.object_positions.remove(&id) {
            Self::remove_recursive(&mut self.root, id, &position);
            Ok(())
        } else {
            Err(HolographicError::InvalidInput(
                "Object not found in spatial index".to_string()
            ))
        }
    }
    
    fn remove_recursive(node: &mut OctreeNode, id: ArxObjectId, position: &Point3D) -> bool {
        match node {
            OctreeNode::Leaf { objects } => {
                objects.retain(|(obj_id, _)| *obj_id != id);
                objects.is_empty()
            }
            OctreeNode::Branch { children, bounds } => {
                for i in 0..8 {
                    if bounds[i].contains(position) {
                        Self::remove_recursive(&mut children[i], id, position);
                        break;
                    }
                }
                false
            }
        }
    }
    
    /// Find all objects within a radius of a point
    pub fn find_within_radius(&self, center: &Point3D, radius: f32) -> Vec<ArxObjectId> {
        let mut results = Vec::new();
        self.query_sphere_recursive(&self.root, center, radius, &self.bounds, &mut results);
        results
    }
    
    fn query_sphere_recursive(
        &self,
        node: &OctreeNode,
        center: &Point3D,
        radius: f32,
        bounds: &BoundingBox,
        results: &mut Vec<ArxObjectId>,
    ) {
        if !bounds.intersects_sphere(center, radius) {
            return;
        }
        
        match node {
            OctreeNode::Leaf { objects } => {
                let radius_squared = radius * radius;
                for (id, pos) in objects {
                    if pos.distance_squared(center) <= radius_squared {
                        results.push(*id);
                    }
                }
            }
            OctreeNode::Branch { children, bounds: child_bounds } => {
                for i in 0..8 {
                    self.query_sphere_recursive(&children[i], center, radius, &child_bounds[i], results);
                }
            }
        }
    }
    
    /// Find k nearest neighbors to a point
    pub fn find_k_nearest(&self, center: &Point3D, k: usize) -> Vec<(ArxObjectId, f32)> {
        let mut candidates = Vec::new();
        
        // Collect all objects with distances
        for (id, pos) in &self.object_positions {
            let distance = pos.distance_squared(center).sqrt();
            candidates.push((*id, distance));
        }
        
        // Sort by distance and take first k
        candidates.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        candidates.truncate(k);
        candidates
    }
    
    /// Update an object's position
    pub fn update_position(&mut self, id: ArxObjectId, new_position: Point3D) -> Result<()> {
        self.remove(id)?;
        self.insert(id, new_position)
    }
    
    /// Get all objects in a bounding box
    pub fn find_in_box(&self, min: Point3D, max: Point3D) -> Vec<ArxObjectId> {
        let query_box = BoundingBox::new(min, max);
        let mut results = Vec::new();
        self.query_box_recursive(&self.root, &query_box, &self.bounds, &mut results);
        results
    }
    
    fn query_box_recursive(
        &self,
        node: &OctreeNode,
        query_box: &BoundingBox,
        node_bounds: &BoundingBox,
        results: &mut Vec<ArxObjectId>,
    ) {
        // Check if node bounds intersect query box
        if node_bounds.max.x < query_box.min.x || node_bounds.min.x > query_box.max.x ||
           node_bounds.max.y < query_box.min.y || node_bounds.min.y > query_box.max.y ||
           node_bounds.max.z < query_box.min.z || node_bounds.min.z > query_box.max.z {
            return;
        }
        
        match node {
            OctreeNode::Leaf { objects } => {
                for (id, pos) in objects {
                    if query_box.contains(pos) {
                        results.push(*id);
                    }
                }
            }
            OctreeNode::Branch { children, bounds } => {
                for i in 0..8 {
                    self.query_box_recursive(&children[i], query_box, &bounds[i], results);
                }
            }
        }
    }
    
    /// Clear all objects from the index
    pub fn clear(&mut self) {
        self.root = OctreeNode::new_leaf();
        self.object_positions.clear();
    }
    
    /// Get the number of objects in the index
    pub fn len(&self) -> usize {
        self.object_positions.len()
    }
    
    /// Check if the index is empty
    pub fn is_empty(&self) -> bool {
        self.object_positions.is_empty()
    }
}

/// Helper to convert FractalSpace to Point3D
impl FractalSpace {
    pub fn to_point(&self) -> Point3D {
        Point3D::new(
            self.x.base as f32,
            self.y.base as f32,
            self.z.base as f32,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_spatial_index_insert_and_query() -> Result<()> {
        let mut index = SpatialIndex::new(
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(1000.0, 1000.0, 1000.0),
        );
        
        // Insert some objects
        index.insert(1, Point3D::new(100.0, 100.0, 100.0))?;
        index.insert(2, Point3D::new(200.0, 200.0, 200.0))?;
        index.insert(3, Point3D::new(500.0, 500.0, 500.0))?;
        
        // Query nearby objects
        let nearby = index.find_within_radius(&Point3D::new(150.0, 150.0, 150.0), 100.0);
        assert!(nearby.contains(&1));
        assert!(nearby.contains(&2));
        assert!(!nearby.contains(&3));
        
        Ok(())
    }
    
    #[test]
    fn test_k_nearest_neighbors() -> Result<()> {
        let mut index = SpatialIndex::new(
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(1000.0, 1000.0, 1000.0),
        );
        
        // Insert objects
        for i in 0..10 {
            let pos = Point3D::new(i as f32 * 100.0, 0.0, 0.0);
            index.insert(i, pos)?;
        }
        
        // Find 3 nearest to origin
        let nearest = index.find_k_nearest(&Point3D::new(0.0, 0.0, 0.0), 3);
        assert_eq!(nearest.len(), 3);
        assert_eq!(nearest[0].0, 0); // Closest
        assert_eq!(nearest[1].0, 1); // Second closest
        assert_eq!(nearest[2].0, 2); // Third closest
        
        Ok(())
    }
    
    #[test]
    fn test_bounding_box_query() -> Result<()> {
        let mut index = SpatialIndex::new(
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(1000.0, 1000.0, 1000.0),
        );
        
        // Insert objects in a grid
        let mut id = 0;
        for x in 0..10 {
            for y in 0..10 {
                index.insert(id, Point3D::new(x as f32 * 100.0, y as f32 * 100.0, 0.0))?;
                id += 1;
            }
        }
        
        // Query a box
        let in_box = index.find_in_box(
            Point3D::new(150.0, 150.0, -10.0),
            Point3D::new(350.0, 350.0, 10.0),
        );
        
        // Should find 4 objects (2x2 grid from 200,200 to 300,300)
        assert_eq!(in_box.len(), 4);
        
        Ok(())
    }
}