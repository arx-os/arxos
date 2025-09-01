//! Enhanced Point Cloud Parser with better voxelization
//! 
//! Improves on the basic parser with tunable parameters and better semantic detection

use crate::arxobject::{ArxObject, object_types};
use crate::document_parser::{Point3D, BoundingBox};
use crate::point_cloud_parser::{PointCloud, Plane, PlaneType, PointCloudError};
use std::collections::HashMap;

/// Enhanced parser with tunable parameters
pub struct EnhancedPointCloudParser {
    /// Voxel size for spatial hashing (meters)
    pub voxel_size: f32,
    
    /// Minimum points to consider a voxel occupied
    pub min_points_per_voxel: usize,
    
    /// Distance threshold for plane fitting
    pub plane_threshold: f32,
    
    /// Height thresholds for semantic classification
    pub outlet_height_range: (f32, f32),
    pub switch_height_range: (f32, f32),
    pub thermostat_height_range: (f32, f32),
    pub light_height_range: (f32, f32),
}

impl Default for EnhancedPointCloudParser {
    fn default() -> Self {
        Self {
            voxel_size: 0.1,  // 10cm voxels (was 5cm)
            min_points_per_voxel: 3,  // Lower threshold (was 5)
            plane_threshold: 0.02,  // 2cm tolerance
            outlet_height_range: (0.2, 0.5),  // 20-50cm above floor
            switch_height_range: (1.0, 1.4),  // 1.0-1.4m (standard switch height)
            thermostat_height_range: (1.3, 1.7),  // 1.3-1.7m
            light_height_range: (2.4, 3.0),  // Near ceiling
        }
    }
}

impl EnhancedPointCloudParser {
    /// Create parser with custom parameters
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Create parser optimized for dense scans (iPhone LiDAR)
    pub fn for_dense_scan() -> Self {
        Self {
            voxel_size: 0.05,  // Smaller voxels for dense data
            min_points_per_voxel: 10,  // Higher threshold
            ..Self::default()
        }
    }
    
    /// Create parser optimized for sparse scans
    pub fn for_sparse_scan() -> Self {
        Self {
            voxel_size: 0.15,  // Larger voxels
            min_points_per_voxel: 2,  // Lower threshold
            ..Self::default()
        }
    }
    
    /// Compress point cloud to ArxObjects with semantic understanding
    pub fn to_arxobjects(&self, cloud: &PointCloud, building_id: u16) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        
        // Step 1: Detect planes for context
        let planes = self.detect_planes(cloud);
        let floor_z = self.get_floor_height(&planes);
        let ceiling_z = self.get_ceiling_height(&planes);
        
        println!("  Detected floor at z={:.2}m, ceiling at z={:.2}m", floor_z, ceiling_z);
        
        // Step 2: Voxelize the point cloud
        let voxels = self.voxelize(cloud);
        println!("  Created {} voxels", voxels.len());
        
        // Step 3: Classify voxels semantically
        let mut classified_voxels = HashMap::new();
        
        for ((vx, vy, vz), indices) in voxels {
            if indices.len() < self.min_points_per_voxel {
                continue;
            }
            
            // Calculate voxel center
            let center = self.calculate_center(cloud, &indices);
            
            // Height above floor
            let height_above_floor = center.z - floor_z;
            
            // Classify based on height and density
            let object_type = self.classify_voxel(
                height_above_floor,
                indices.len(),
                &center,
                ceiling_z - floor_z
            );
            
            classified_voxels.entry(object_type)
                .or_insert_with(Vec::new)
                .push((center, indices.len()));
        }
        
        // Step 4: Merge nearby voxels of same type
        for (object_type, voxel_centers) in classified_voxels {
            let merged = self.merge_nearby_voxels(&voxel_centers);
            
            for (center, point_count) in merged {
                // Convert to millimeters and create ArxObject
                let x_mm = (center.x * 1000.0).max(0.0).min(65535.0) as u16;
                let y_mm = (center.y * 1000.0).max(0.0).min(65535.0) as u16;
                let z_mm = (center.z * 1000.0).max(0.0).min(65535.0) as u16;
                
                let mut obj = ArxObject::new(building_id, object_type, x_mm, y_mm, z_mm);
                
                // Add properties based on type
                match object_type {
                    object_types::OUTLET => {
                        obj.properties[0] = 1;  // Circuit number
                        obj.properties[1] = 120;  // Voltage (120V)
                    }
                    object_types::LIGHT_SWITCH => {
                        obj.properties[0] = 1;  // Switch position (on/off)
                    }
                    object_types::THERMOSTAT => {
                        obj.properties[0] = 72;  // Temperature setting
                        obj.properties[1] = 1;  // Zone number
                    }
                    _ => {}
                }
                
                objects.push(obj);
                
                println!("    Created ArxObject: type=0x{:02X} at ({:.2}, {:.2}, {:.2})m with {} points",
                    object_type, center.x, center.y, center.z, point_count);
            }
        }
        
        objects
    }
    
    /// Detect planes using simplified RANSAC
    fn detect_planes(&self, cloud: &PointCloud) -> Vec<Plane> {
        let mut planes = Vec::new();
        
        // Find floor (lowest horizontal concentration)
        let mut z_values: Vec<f32> = cloud.points.iter().map(|p| p.z).collect();
        z_values.sort_by(|a, b| a.partial_cmp(b).unwrap());
        
        if !z_values.is_empty() {
            let floor_z = z_values[z_values.len() / 10];  // 10th percentile
            planes.push(Plane {
                normal: Point3D { x: 0.0, y: 0.0, z: 1.0 },
                distance: floor_z,
                points: vec![],
                plane_type: PlaneType::Floor,
            });
            
            let ceiling_z = z_values[z_values.len() * 9 / 10];  // 90th percentile
            planes.push(Plane {
                normal: Point3D { x: 0.0, y: 0.0, z: 1.0 },
                distance: ceiling_z,
                points: vec![],
                plane_type: PlaneType::Ceiling,
            });
        }
        
        planes
    }
    
    /// Get floor height from detected planes
    fn get_floor_height(&self, planes: &[Plane]) -> f32 {
        planes.iter()
            .find(|p| p.plane_type == PlaneType::Floor)
            .map(|p| p.distance)
            .unwrap_or(0.0)
    }
    
    /// Get ceiling height from detected planes
    fn get_ceiling_height(&self, planes: &[Plane]) -> f32 {
        planes.iter()
            .find(|p| p.plane_type == PlaneType::Ceiling)
            .map(|p| p.distance)
            .unwrap_or(3.0)
    }
    
    /// Voxelize point cloud
    fn voxelize(&self, cloud: &PointCloud) -> HashMap<(i32, i32, i32), Vec<usize>> {
        let mut voxels = HashMap::new();
        
        for (i, point) in cloud.points.iter().enumerate() {
            let voxel_x = (point.x / self.voxel_size).floor() as i32;
            let voxel_y = (point.y / self.voxel_size).floor() as i32;
            let voxel_z = (point.z / self.voxel_size).floor() as i32;
            
            voxels.entry((voxel_x, voxel_y, voxel_z))
                .or_insert_with(Vec::new)
                .push(i);
        }
        
        voxels
    }
    
    /// Calculate center of points
    fn calculate_center(&self, cloud: &PointCloud, indices: &[usize]) -> Point3D {
        let mut sum = Point3D { x: 0.0, y: 0.0, z: 0.0 };
        
        for &idx in indices {
            let p = &cloud.points[idx];
            sum.x += p.x;
            sum.y += p.y;
            sum.z += p.z;
        }
        
        let count = indices.len() as f32;
        Point3D {
            x: sum.x / count,
            y: sum.y / count,
            z: sum.z / count,
        }
    }
    
    /// Classify voxel based on semantic rules
    fn classify_voxel(&self, height_above_floor: f32, point_count: usize, center: &Point3D, room_height: f32) -> u8 {
        // Floor/ceiling detection
        if height_above_floor < 0.1 {
            return object_types::FLOOR;
        }
        if height_above_floor > room_height - 0.3 {
            return object_types::CEILING;
        }
        
        // Electrical outlets (low on wall)
        if height_above_floor >= self.outlet_height_range.0 && 
           height_above_floor <= self.outlet_height_range.1 &&
           point_count > 5 {
            return object_types::OUTLET;
        }
        
        // Light switches (mid-height on wall)
        if height_above_floor >= self.switch_height_range.0 &&
           height_above_floor <= self.switch_height_range.1 &&
           point_count > 5 {
            return object_types::LIGHT_SWITCH;
        }
        
        // Thermostats (mid-height, usually isolated)
        if height_above_floor >= self.thermostat_height_range.0 &&
           height_above_floor <= self.thermostat_height_range.1 &&
           point_count > 8 {
            return object_types::THERMOSTAT;
        }
        
        // Lights (near ceiling)
        if height_above_floor >= self.light_height_range.0 &&
           height_above_floor <= self.light_height_range.1 &&
           point_count > 10 {
            return object_types::LIGHT;
        }
        
        // Walls (vertical surfaces with many points)
        if point_count > 50 {
            return object_types::WALL;
        }
        
        // Default to generic object
        object_types::GENERIC
    }
    
    /// Merge nearby voxels of the same type
    fn merge_nearby_voxels(&self, voxels: &[(Point3D, usize)]) -> Vec<(Point3D, usize)> {
        if voxels.is_empty() {
            return vec![];
        }
        
        let mut merged = Vec::new();
        let mut used = vec![false; voxels.len()];
        let merge_distance = self.voxel_size * 2.0;  // Merge voxels within 2x voxel size
        
        for i in 0..voxels.len() {
            if used[i] {
                continue;
            }
            
            let mut cluster_center = voxels[i].0.clone();
            let mut cluster_points = voxels[i].1;
            let mut cluster_count = 1;
            used[i] = true;
            
            // Find nearby voxels to merge
            for j in (i + 1)..voxels.len() {
                if used[j] {
                    continue;
                }
                
                let dist = ((voxels[j].0.x - voxels[i].0.x).powi(2) +
                           (voxels[j].0.y - voxels[i].0.y).powi(2) +
                           (voxels[j].0.z - voxels[i].0.z).powi(2)).sqrt();
                
                if dist < merge_distance {
                    // Merge this voxel
                    cluster_center.x += voxels[j].0.x;
                    cluster_center.y += voxels[j].0.y;
                    cluster_center.z += voxels[j].0.z;
                    cluster_points += voxels[j].1;
                    cluster_count += 1;
                    used[j] = true;
                }
            }
            
            // Average the cluster center
            cluster_center.x /= cluster_count as f32;
            cluster_center.y /= cluster_count as f32;
            cluster_center.z /= cluster_count as f32;
            
            merged.push((cluster_center, cluster_points));
        }
        
        merged
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_enhanced_voxelization() {
        let parser = EnhancedPointCloudParser::new();
        
        // Create test point cloud
        let mut points = Vec::new();
        for i in 0..100 {
            points.push(Point3D {
                x: (i / 10) as f32 * 0.1,
                y: (i % 10) as f32 * 0.1,
                z: 0.0,
            });
        }
        
        let cloud = PointCloud {
            points,
            colors: vec![(255, 255, 255); 100],
            normals: vec![Point3D { x: 0.0, y: 0.0, z: 1.0 }; 100],
            bounds: BoundingBox {
                min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                max: Point3D { x: 1.0, y: 1.0, z: 0.0 },
            },
        };
        
        let objects = parser.to_arxobjects(&cloud, 0x0001);
        assert!(!objects.is_empty());
    }
}