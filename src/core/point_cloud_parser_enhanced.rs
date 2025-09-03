//! Enhanced point cloud parser with configurable settings
//! 
//! Provides more flexible voxel-based clustering for different scan densities

use crate::arxobject::{ArxObject, object_types};
use crate::point_cloud_parser::PointCloud;
use std::collections::HashMap;

/// Enhanced point cloud parser with configurable parameters
pub struct EnhancedPointCloudParser {
    voxel_size: f32,    // Size of voxels in meters
    min_points: usize,  // Minimum points to form an object
    merge_distance: f32, // Distance to merge nearby voxels
}

impl EnhancedPointCloudParser {
    /// Create new parser with default settings
    pub fn new() -> Self {
        Self {
            voxel_size: 0.10,      // 10cm voxels
            min_points: 3,         // At least 3 points per voxel
            merge_distance: 0.15,  // Merge within 15cm
        }
    }
    
    /// Create parser optimized for sparse scans
    pub fn for_sparse_scan() -> Self {
        Self {
            voxel_size: 0.15,      // 15cm voxels
            min_points: 2,         // Only 2 points needed
            merge_distance: 0.20,  // Merge within 20cm
        }
    }
    
    /// Create parser optimized for dense scans
    pub fn for_dense_scan() -> Self {
        Self {
            voxel_size: 0.05,      // 5cm voxels
            min_points: 10,        // Need 10 points
            merge_distance: 0.08,  // Merge within 8cm
        }
    }
    
    /// Convert point cloud to ArxObjects
    pub fn to_arxobjects(&self, cloud: &PointCloud, building_id: u16) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        let mut voxels: HashMap<(i32, i32, i32), Vec<usize>> = HashMap::new();
        
        // Group points into voxels
        for (idx, point) in cloud.points.iter().enumerate() {
            let vx = (point.x / self.voxel_size).floor() as i32;
            let vy = (point.y / self.voxel_size).floor() as i32;
            let vz = (point.z / self.voxel_size).floor() as i32;
            
            voxels.entry((vx, vy, vz))
                .or_insert_with(Vec::new)
                .push(idx);
        }
        
        // Merge nearby voxels
        let mut merged_voxels = self.merge_nearby_voxels(voxels);
        
        // Convert voxels to ArxObjects
        for indices in merged_voxels.values_mut() {
            if indices.len() < self.min_points {
                continue;
            }
            
            // Calculate centroid
            let mut cx = 0.0;
            let mut cy = 0.0;
            let mut cz = 0.0;
            
            for &idx in indices.iter() {
                cx += cloud.points[idx].x;
                cy += cloud.points[idx].y;
                cz += cloud.points[idx].z;
            }
            
            let n = indices.len() as f32;
            cx /= n;
            cy /= n;
            cz /= n;
            
            // Enhanced object type detection with more categories
            let object_type = self.detect_object_type(cx, cy, cz, &cloud.points, indices);
            
            // Convert to millimeters for ArxObject
            let x_mm = (cx * 1000.0).min(65535.0) as u16;
            let y_mm = (cy * 1000.0).min(65535.0) as u16;
            let z_mm = (cz * 1000.0).min(65535.0) as u16;
            
            objects.push(ArxObject::new(
                building_id,
                object_type,
                x_mm,
                y_mm,
                z_mm,
            ));
        }
        
        objects
    }
    
    /// Merge nearby voxels to form larger objects
    fn merge_nearby_voxels(&self, voxels: HashMap<(i32, i32, i32), Vec<usize>>) 
        -> HashMap<usize, Vec<usize>> {
        let mut merged = HashMap::new();
        let mut cluster_id = 0;
        let mut visited = std::collections::HashSet::new();
        
        for (voxel_key, indices) in &voxels {
            if visited.contains(voxel_key) {
                continue;
            }
            
            let mut cluster = indices.clone();
            let mut stack = vec![*voxel_key];
            visited.insert(*voxel_key);
            
            while let Some((vx, vy, vz)) = stack.pop() {
                // Check all 26 neighbors
                for dx in -1..=1 {
                    for dy in -1..=1 {
                        for dz in -1..=1 {
                            if dx == 0 && dy == 0 && dz == 0 {
                                continue;
                            }
                            
                            let neighbor = (vx + dx, vy + dy, vz + dz);
                            if !visited.contains(&neighbor) {
                                if let Some(neighbor_indices) = voxels.get(&neighbor) {
                                    visited.insert(neighbor);
                                    cluster.extend(neighbor_indices);
                                    stack.push(neighbor);
                                }
                            }
                        }
                    }
                }
            }
            
            merged.insert(cluster_id, cluster);
            cluster_id += 1;
        }
        
        merged
    }
    
    /// Detect object type based on position and point distribution
    fn detect_object_type(&self, x: f32, y: f32, z: f32, 
                         _points: &[crate::document_parser::Point3D], 
                         indices: &[usize]) -> u8 {
        let point_count = indices.len();
        
        // Floor detection (z near 0, many points)
        if z < 0.1 && point_count > 100 {
            return object_types::FLOOR;
        }
        
        // Ceiling detection (z > 2.4m, many points)
        if z > 2.4 && point_count > 100 {
            return object_types::CEILING;
        }
        
        // Outlet detection (standard outlet height)
        if (0.25..=0.35).contains(&z) && point_count < 50 {
            return object_types::OUTLET;
        }
        
        // Light switch detection (standard switch height)
        if (1.1..=1.3).contains(&z) && point_count < 50 {
            return object_types::LIGHT_SWITCH;
        }
        
        // Thermostat detection
        if (1.4..=1.6).contains(&z) && point_count < 60 {
            return object_types::THERMOSTAT;
        }
        
        // Light fixture detection (high up, moderate points)
        if z > 2.0 && point_count < 100 {
            return object_types::LIGHT;
        }
        
        // Air vent detection (ceiling or high wall)
        if z > 2.2 && point_count > 20 && point_count < 80 {
            return object_types::AIR_VENT;
        }
        
        // Door detection (tall vertical cluster)
        if z > 0.5 && z < 2.2 && point_count > 200 {
            return object_types::DOOR;
        }
        
        // Window detection (mid-height, moderate points)
        if z > 0.8 && z < 2.0 && point_count > 100 && point_count < 300 {
            return object_types::WINDOW;
        }
        
        // Default to wall for everything else
        object_types::WALL
    }
}

impl Default for EnhancedPointCloudParser {
    fn default() -> Self {
        Self::new()
    }
}