//! Basic point cloud to ArxObject conversion
//! 
//! Simple voxel-based clustering for point cloud data

use crate::arxobject::{ArxObject, object_types};
use crate::document_parser::{Point3D, BoundingBox};
use std::collections::HashMap;

/// Point cloud data structure
#[derive(Debug, Clone)]
pub struct PointCloud {
    pub points: Vec<Point3D>,
    pub colors: Vec<(u8, u8, u8)>,
    pub normals: Vec<Point3D>,
    pub bounds: BoundingBox,
}

/// Point cloud parser for converting to ArxObjects
pub struct PointCloudParser {
    voxel_size: f32,  // Size of voxels in meters
    min_points: usize,  // Minimum points to form an object
}

impl PointCloudParser {
    /// Create new parser with default settings
    pub fn new() -> Self {
        Self {
            voxel_size: 0.05,  // 5cm voxels
            min_points: 5,      // At least 5 points per voxel
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
        
        // Convert voxels to ArxObjects
        for ((_vx, _vy, _vz), indices) in voxels {
            if indices.len() < self.min_points {
                continue;
            }
            
            // Calculate centroid
            let mut cx = 0.0;
            let mut cy = 0.0;
            let mut cz = 0.0;
            
            for &idx in &indices {
                cx += cloud.points[idx].x;
                cy += cloud.points[idx].y;
                cz += cloud.points[idx].z;
            }
            
            let n = indices.len() as f32;
            cx /= n;
            cy /= n;
            cz /= n;
            
            // Determine object type based on height
            let object_type = match cz {
                z if z < 0.1 => object_types::FLOOR,
                z if z > 2.5 => object_types::CEILING,
                z if (0.25..=0.35).contains(&z) => object_types::OUTLET,
                z if (1.1..=1.3).contains(&z) => object_types::LIGHT_SWITCH,
                z if (1.4..=1.6).contains(&z) => object_types::THERMOSTAT,
                z if z > 2.0 => object_types::LIGHT,
                _ => object_types::WALL,
            };
            
            // Convert to millimeters for ArxObject
            let x_mm = (cx * 1000.0) as u16;
            let y_mm = (cy * 1000.0) as u16;
            let z_mm = (cz * 1000.0) as u16;
            
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
}

impl Default for PointCloudParser {
    fn default() -> Self {
        Self::new()
    }
}