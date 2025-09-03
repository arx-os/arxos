//! Simple point cloud to ArxObject conversion
//! 
//! Converts 3D point cloud data into compressed ArxObjects

use crate::arxobject_simple::{ArxObject, object_types};
use crate::document_parser::Point3D;
use crate::point_cloud_parser::PointCloud;
use std::collections::HashMap;

/// Configuration for point cloud processing
pub struct ProcessorConfig {
    /// Voxel size in meters
    pub voxel_size: f32,
    /// Minimum points to form an object
    pub min_points: usize,
}

impl Default for ProcessorConfig {
    fn default() -> Self {
        Self {
            voxel_size: 0.10,      // 10cm voxels
            min_points: 5,         // At least 5 points
        }
    }
}

/// Simple point cloud processor
pub struct SimplePointCloudProcessor {
    config: ProcessorConfig,
}

impl SimplePointCloudProcessor {
    /// Create a new processor
    pub fn new() -> Self {
        Self {
            config: ProcessorConfig::default(),
        }
    }
    
    /// Create with custom config
    pub fn with_config(config: ProcessorConfig) -> Self {
        Self { config }
    }
    
    /// Process point cloud into ArxObjects
    pub fn process(&self, cloud: &PointCloud, building_id: u16) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        let mut voxels: HashMap<(i32, i32, i32), Vec<&Point3D>> = HashMap::new();
        
        // Group points into voxels
        for point in &cloud.points {
            let vx = (point.x / self.config.voxel_size).floor() as i32;
            let vy = (point.y / self.config.voxel_size).floor() as i32;
            let vz = (point.z / self.config.voxel_size).floor() as i32;
            
            voxels.entry((vx, vy, vz))
                .or_insert_with(Vec::new)
                .push(point);
        }
        
        // Convert voxels to ArxObjects
        for ((_vx, _vy, _vz), points) in voxels {
            if points.len() < self.config.min_points {
                continue;
            }
            
            // Calculate centroid
            let mut cx = 0.0;
            let mut cy = 0.0;
            let mut cz = 0.0;
            
            for point in &points {
                cx += point.x;
                cy += point.y;
                cz += point.z;
            }
            
            let n = points.len() as f32;
            cx /= n;
            cy /= n;
            cz /= n;
            
            // Classify object type based on height and point count
            let object_type = classify_by_position(cx, cy, cz, points.len());
            
            // Convert to millimeters (clamped to u16 range)
            let x_mm = (cx * 1000.0).clamp(0.0, 65535.0) as u16;
            let y_mm = (cy * 1000.0).clamp(0.0, 65535.0) as u16;
            let z_mm = (cz * 1000.0).clamp(0.0, 65535.0) as u16;
            
            // Create properties
            let mut properties = [0u8; 4];
            properties[0] = (points.len().min(255)) as u8; // Point count
            properties[1] = 95; // Confidence (95%)
            
            objects.push(ArxObject::with_properties(
                building_id,
                object_type,
                x_mm,
                y_mm,
                z_mm,
                properties,
            ));
        }
        
        objects
    }
}

/// Classify object type based on position
fn classify_by_position(_x: f32, _y: f32, z: f32, point_count: usize) -> u8 {
    match z {
        // Floor level (z < 10cm with many points)
        z if z < 0.1 && point_count > 100 => object_types::FLOOR,
        
        // Ceiling level (z > 2.4m with many points)
        z if z > 2.4 && point_count > 100 => object_types::CEILING,
        
        // Outlet height (25-35cm, small cluster)
        z if (0.25..=0.35).contains(&z) && point_count < 50 => object_types::OUTLET,
        
        // Light switch height (1.1-1.3m, small cluster)
        z if (1.1..=1.3).contains(&z) && point_count < 50 => object_types::LIGHT_SWITCH,
        
        // Thermostat height (1.4-1.6m, small cluster)
        z if (1.4..=1.6).contains(&z) && point_count < 60 => object_types::THERMOSTAT,
        
        // Light fixture (high up, moderate points)
        z if z > 2.0 && point_count < 100 => object_types::LIGHT,
        
        // Door (tall vertical cluster)
        z if z > 0.5 && z < 2.2 && point_count > 200 => object_types::DOOR,
        
        // Window (mid-height, moderate points)
        z if z > 0.8 && z < 2.0 && point_count > 100 && point_count < 200 => object_types::WINDOW,
        
        // Wall (large vertical surface)
        _ if point_count > 500 => object_types::WALL,
        
        // Default to generic
        _ => object_types::GENERIC,
    }
}

impl Default for SimplePointCloudProcessor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    fn create_test_cloud() -> PointCloud {
        let mut points = Vec::new();
        
        // Add floor points
        for x in 0..20 {
            for y in 0..20 {
                points.push(Point3D {
                    x: x as f32 * 0.05,
                    y: y as f32 * 0.05,
                    z: 0.0,
                });
            }
        }
        
        // Add outlet cluster
        for dx in 0..5 {
            for dy in 0..5 {
                points.push(Point3D {
                    x: 2.0 + dx as f32 * 0.01,
                    y: 1.0 + dy as f32 * 0.01,
                    z: 0.3,
                });
            }
        }
        
        PointCloud {
            points,
            colors: vec![],
            normals: vec![],
            bounds: BoundingBox {
                min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                max: Point3D { x: 3.0, y: 2.0, z: 0.3 },
            },
        }
    }
    
    #[test]
    fn test_point_cloud_processing() {
        let processor = SimplePointCloudProcessor::new();
        let cloud = create_test_cloud();
        
        let objects = processor.process(&cloud, 100);
        
        // Should have at least 2 objects (floor and outlet)
        assert!(objects.len() >= 2);
        
        // Check for floor object
        let has_floor = objects.iter().any(|o| o.object_type == object_types::FLOOR);
        assert!(has_floor);
        
        // Check for outlet
        let has_outlet = objects.iter().any(|o| o.object_type == object_types::OUTLET);
        assert!(has_outlet);
    }
}