//! Point Cloud Processing for ArxOS
//! 
//! Converts 3D point clouds from LiDAR scans into compressed ArxObjects
//! using spatial clustering and intelligent object detection.

use crate::arxobject::{ArxObject, object_types};
use crate::ply_parser::Point3D;
use crate::error::{ArxError, Result};
use std::collections::HashMap;

/// Voxel-based spatial index for efficient point grouping
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct VoxelKey {
    x: i32,
    y: i32, 
    z: i32,
}

impl VoxelKey {
    fn from_point(point: &Point3D, voxel_size: f32) -> Self {
        Self {
            x: (point.x / voxel_size).floor() as i32,
            y: (point.y / voxel_size).floor() as i32,
            z: (point.z / voxel_size).floor() as i32,
        }
    }
    
    fn to_world_position(&self, voxel_size: f32) -> (f32, f32, f32) {
        (
            (self.x as f32 + 0.5) * voxel_size,
            (self.y as f32 + 0.5) * voxel_size,
            (self.z as f32 + 0.5) * voxel_size,
        )
    }
}

/// Configuration for point cloud processing
#[derive(Debug, Clone)]
pub struct ProcessingConfig {
    /// Size of voxels in millimeters
    pub voxel_size_mm: f32,
    /// Minimum points required to create an ArxObject
    pub min_points_per_voxel: usize,
    /// Maximum distance for clustering (mm)
    pub cluster_distance_mm: f32,
    /// Enable intelligent object detection
    pub detect_objects: bool,
    /// Merge nearby similar objects
    pub merge_similar: bool,
    /// Z-height for floor detection (mm)
    pub floor_height_mm: f32,
    /// Z-height for ceiling detection (mm) 
    pub ceiling_height_mm: f32,
}

impl Default for ProcessingConfig {
    fn default() -> Self {
        Self {
            voxel_size_mm: 100.0,        // 10cm voxels
            min_points_per_voxel: 5,     // At least 5 points
            cluster_distance_mm: 200.0,   // 20cm clustering
            detect_objects: true,
            merge_similar: true,
            floor_height_mm: 100.0,       // Floor within 10cm of ground
            ceiling_height_mm: 2400.0,    // Ceiling around 2.4m
        }
    }
}

/// Point cloud processor
pub struct PointCloudProcessor {
    config: ProcessingConfig,
    voxel_map: HashMap<VoxelKey, Vec<Point3D>>,
    clusters: Vec<PointCluster>,
}

/// Cluster of related points
#[derive(Debug)]
struct PointCluster {
    points: Vec<Point3D>,
    centroid: Point3D,
    bounds_min: Point3D,
    bounds_max: Point3D,
    detected_type: Option<u8>,
}

impl PointCluster {
    fn from_points(points: Vec<Point3D>) -> Self {
        let mut min = Point3D::new(f32::MAX, f32::MAX, f32::MAX);
        let mut max = Point3D::new(f32::MIN, f32::MIN, f32::MIN);
        let mut sum = Point3D::new(0.0, 0.0, 0.0);
        
        for point in &points {
            min.x = min.x.min(point.x);
            min.y = min.y.min(point.y);
            min.z = min.z.min(point.z);
            max.x = max.x.max(point.x);
            max.y = max.y.max(point.y);
            max.z = max.z.max(point.z);
            sum.x += point.x;
            sum.y += point.y;
            sum.z += point.z;
        }
        
        let count = points.len() as f32;
        let centroid = Point3D::new(sum.x / count, sum.y / count, sum.z / count);
        
        Self {
            points,
            centroid,
            bounds_min: min,
            bounds_max: max,
            detected_type: None,
        }
    }
    
    fn width(&self) -> f32 {
        self.bounds_max.x - self.bounds_min.x
    }
    
    fn depth(&self) -> f32 {
        self.bounds_max.y - self.bounds_min.y
    }
    
    fn height(&self) -> f32 {
        self.bounds_max.z - self.bounds_min.z
    }
    
    fn volume(&self) -> f32 {
        self.width() * self.depth() * self.height()
    }
    
    fn density(&self) -> f32 {
        self.points.len() as f32 / self.volume().max(1.0)
    }
}

impl PointCloudProcessor {
    /// Create new processor with config
    pub fn new(config: ProcessingConfig) -> Self {
        Self {
            config,
            voxel_map: HashMap::new(),
            clusters: Vec::new(),
        }
    }
    
    /// Process point cloud into ArxObjects
    pub fn process(&mut self, points: &[Point3D], building_id: u16) -> Result<Vec<ArxObject>> {
        // Step 1: Voxelize points
        self.voxelize_points(points);
        
        // Step 2: Create clusters from voxels
        self.create_clusters();
        
        // Step 3: Detect object types if enabled
        if self.config.detect_objects {
            self.detect_object_types();
        }
        
        // Step 4: Convert clusters to ArxObjects
        let mut arxobjects = self.clusters_to_arxobjects(building_id);
        
        // Step 5: Merge similar objects if enabled
        if self.config.merge_similar {
            arxobjects = self.merge_similar_objects(arxobjects);
        }
        
        Ok(arxobjects)
    }
    
    /// Group points into voxels
    fn voxelize_points(&mut self, points: &[Point3D]) {
        self.voxel_map.clear();
        
        for point in points {
            let key = VoxelKey::from_point(point, self.config.voxel_size_mm);
            self.voxel_map.entry(key).or_insert_with(Vec::new).push(*point);
        }
        
        // Remove voxels with too few points
        self.voxel_map.retain(|_, points| points.len() >= self.config.min_points_per_voxel);
    }
    
    /// Create clusters from voxels using connected components
    fn create_clusters(&mut self) {
        self.clusters.clear();
        
        let mut visited = HashMap::new();
        for &key in self.voxel_map.keys() {
            visited.insert(key, false);
        }
        
        for &start_key in self.voxel_map.keys() {
            if visited[&start_key] {
                continue;
            }
            
            // Flood fill to find connected voxels
            let mut cluster_voxels = Vec::new();
            let mut stack = vec![start_key];
            
            while let Some(current) = stack.pop() {
                if visited[&current] {
                    continue;
                }
                
                visited.insert(current, true);
                cluster_voxels.push(current);
                
                // Check 26 neighbors (3x3x3 cube minus center)
                for dx in -1..=1 {
                    for dy in -1..=1 {
                        for dz in -1..=1 {
                            if dx == 0 && dy == 0 && dz == 0 {
                                continue;
                            }
                            
                            let neighbor = VoxelKey {
                                x: current.x + dx,
                                y: current.y + dy,
                                z: current.z + dz,
                            };
                            
                            if self.voxel_map.contains_key(&neighbor) && !visited[&neighbor] {
                                stack.push(neighbor);
                            }
                        }
                    }
                }
            }
            
            // Collect all points from cluster voxels
            let mut cluster_points = Vec::new();
            for voxel_key in cluster_voxels {
                if let Some(points) = self.voxel_map.get(&voxel_key) {
                    cluster_points.extend_from_slice(points);
                }
            }
            
            if !cluster_points.is_empty() {
                self.clusters.push(PointCluster::from_points(cluster_points));
            }
        }
    }
    
    /// Detect object types based on cluster characteristics
    fn detect_object_types(&mut self) {
        // First collect the classifications
        let classifications: Vec<u8> = self.clusters.iter()
            .map(|cluster| self.classify_cluster(cluster))
            .collect();
        
        // Then apply them
        for (cluster, class) in self.clusters.iter_mut().zip(classifications) {
            cluster.detected_type = Some(class);
        }
    }
    
    /// Classify a cluster into an object type
    fn classify_cluster(&self, cluster: &PointCluster) -> u8 {
        let z = cluster.centroid.z;
        let width = cluster.width();
        let depth = cluster.depth();
        let height = cluster.height();
        let density = cluster.density();
        let point_count = cluster.points.len();
        
        // Floor detection
        if z < self.config.floor_height_mm && width > 1000.0 && depth > 1000.0 && height < 100.0 {
            return object_types::FLOOR;
        }
        
        // Ceiling detection
        if z > self.config.ceiling_height_mm && width > 1000.0 && depth > 1000.0 && height < 100.0 {
            return object_types::CEILING;
        }
        
        // Wall detection (tall, thin, vertical)
        let aspect_ratio = height / width.min(depth).max(1.0);
        if aspect_ratio > 5.0 && height > 1500.0 {
            return object_types::WALL;
        }
        
        // Door detection (wall-like but specific height)
        if aspect_ratio > 3.0 && height > 1800.0 && height < 2200.0 && width < 1200.0 {
            return object_types::DOOR;
        }
        
        // Column detection (vertical cylinder-like)
        if aspect_ratio > 4.0 && width < 500.0 && depth < 500.0 {
            return object_types::COLUMN;
        }
        
        // Equipment detection (medium size, high density)
        if width > 300.0 && width < 2000.0 && density > 0.001 && point_count > 100 {
            // HVAC equipment tends to be boxy and elevated
            if z > 500.0 && z < 2000.0 {
                return object_types::HVAC_VENT;
            }
            
            // Electrical panels on walls
            if width < 800.0 && height > 400.0 && height < 1500.0 {
                return object_types::ELECTRICAL_PANEL;
            }
        }
        
        // Small objects near walls might be outlets/switches
        if width < 200.0 && height < 200.0 && z > 800.0 && z < 1500.0 {
            return object_types::OUTLET;
        }
        
        // Lights are usually on ceiling
        if z > self.config.ceiling_height_mm - 500.0 && width < 1000.0 {
            return object_types::LIGHT;
        }
        
        // Default to generic object
        object_types::GENERIC
    }
    
    /// Convert clusters to ArxObjects
    fn clusters_to_arxobjects(&self, building_id: u16) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        
        for cluster in &self.clusters {
            // Convert to millimeters and clamp to u16 range
            let x = cluster.centroid.x.clamp(0.0, 65535.0) as u16;
            let y = cluster.centroid.y.clamp(0.0, 65535.0) as u16;
            let z = cluster.centroid.z.clamp(0.0, 65535.0) as u16;
            
            let object_type = cluster.detected_type.unwrap_or(object_types::GENERIC);
            
            // Encode cluster properties
            let mut properties = [0u8; 4];
            properties[0] = (cluster.points.len().min(255)) as u8; // Point count (capped)
            properties[1] = (cluster.density() * 100.0).min(255.0) as u8; // Density
            properties[2] = (cluster.width() / 10.0).min(255.0) as u8; // Width in cm
            properties[3] = (cluster.height() / 10.0).min(255.0) as u8; // Height in cm
            
            objects.push(ArxObject {
                building_id,
                object_type,
                x,
                y,
                z,
                properties,
            });
        }
        
        objects
    }
    
    /// Merge similar nearby objects
    fn merge_similar_objects(&self, objects: Vec<ArxObject>) -> Vec<ArxObject> {
        let mut merged = Vec::new();
        let mut processed = vec![false; objects.len()];
        
        for i in 0..objects.len() {
            if processed[i] {
                continue;
            }
            
            let mut group = vec![objects[i]];
            processed[i] = true;
            
            // Find similar nearby objects
            for j in i + 1..objects.len() {
                if processed[j] {
                    continue;
                }
                
                let dist = self.object_distance(&objects[i], &objects[j]);
                
                // Merge if same type and close enough
                if objects[i].object_type == objects[j].object_type 
                    && dist < self.config.cluster_distance_mm {
                    group.push(objects[j]);
                    processed[j] = true;
                }
            }
            
            // Create merged object at centroid
            if group.len() == 1 {
                merged.push(group[0]);
            } else {
                merged.push(self.merge_group(&group));
            }
        }
        
        merged
    }
    
    /// Calculate distance between two ArxObjects
    fn object_distance(&self, a: &ArxObject, b: &ArxObject) -> f32 {
        let dx = a.x as f32 - b.x as f32;
        let dy = a.y as f32 - b.y as f32;
        let dz = a.z as f32 - b.z as f32;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
    
    /// Merge a group of objects into one
    fn merge_group(&self, group: &[ArxObject]) -> ArxObject {
        let mut sum_x = 0u64;
        let mut sum_y = 0u64;
        let mut sum_z = 0u64;
        
        for obj in group {
            sum_x += obj.x as u64;
            sum_y += obj.y as u64;
            sum_z += obj.z as u64;
        }
        
        let count = group.len() as u64;
        
        ArxObject {
            building_id: group[0].building_id,
            object_type: group[0].object_type,
            x: (sum_x / count) as u16,
            y: (sum_y / count) as u16,
            z: (sum_z / count) as u16,
            properties: [
                group.len().min(255) as u8,  // Number of merged objects
                0,
                0,
                0,
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_voxel_key_conversion() {
        let point = Point3D::new(150.0, 250.0, 350.0);
        let key = VoxelKey::from_point(&point, 100.0);
        
        assert_eq!(key.x, 1);
        assert_eq!(key.y, 2);
        assert_eq!(key.z, 3);
        
        let (x, y, z) = key.to_world_position(100.0);
        assert_eq!(x, 150.0);
        assert_eq!(y, 250.0);
        assert_eq!(z, 350.0);
    }
    
    #[test]
    fn test_cluster_creation() {
        let points = vec![
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(100.0, 0.0, 0.0),
            Point3D::new(0.0, 100.0, 0.0),
            Point3D::new(0.0, 0.0, 100.0),
        ];
        
        let cluster = PointCluster::from_points(points);
        
        assert_eq!(cluster.centroid.x, 25.0);
        assert_eq!(cluster.centroid.y, 25.0);
        assert_eq!(cluster.centroid.z, 25.0);
        assert_eq!(cluster.width(), 100.0);
        assert_eq!(cluster.depth(), 100.0);
        assert_eq!(cluster.height(), 100.0);
    }
}