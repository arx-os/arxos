//! Unified Compression Module
//! 
//! Consolidates all point cloud to ArxObject compression approaches

use crate::arxobject::{ArxObject, object_types};
use crate::error::ArxError;
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufReader, BufRead};

/// Unified point cloud processor
pub struct PointCloudProcessor {
    voxel_size: f32,
    min_density: usize,
    material_detector: MaterialDetector,
}

impl PointCloudProcessor {
    pub fn new() -> Self {
        Self {
            voxel_size: 0.2, // 20cm default
            min_density: 5,
            material_detector: MaterialDetector::new(),
        }
    }
    
    pub fn with_voxel_size(mut self, size: f32) -> Self {
        self.voxel_size = size;
        self
    }
    
    /// Process PLY file into ArxObjects
    pub fn process_ply(&self, path: &str) -> Result<Vec<ArxObject>, ArxError> {
        let points = self.load_ply(path)?;
        Ok(self.points_to_arxobjects(&points))
    }
    
    /// Load points from PLY file
    fn load_ply(&self, path: &str) -> Result<Vec<[f32; 3]>, ArxError> {
        let file = File::open(path)
            .map_err(|e| ArxError::Io(e))?;
        let reader = BufReader::new(file);
        let mut points = Vec::new();
        let mut in_header = true;
        
        for line in reader.lines() {
            let line = line.map_err(|e| ArxError::Io(e))?;
            
            if in_header {
                if line == "end_header" {
                    in_header = false;
                }
                continue;
            }
            
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 3 {
                points.push([
                    parts[0].parse().unwrap_or(0.0),
                    parts[1].parse().unwrap_or(0.0),
                    parts[2].parse().unwrap_or(0.0),
                ]);
            }
        }
        
        Ok(points)
    }
    
    /// Convert points to ArxObjects using intelligent voxelization
    pub fn points_to_arxobjects(&self, points: &[[f32; 3]]) -> Vec<ArxObject> {
        // Voxelize points
        let voxels = self.voxelize(points);
        
        // Convert to ArxObjects
        let mut objects = Vec::new();
        for (coords, voxel_data) in voxels {
            if voxel_data.point_count < self.min_density {
                continue;
            }
            
            let material = self.material_detector.detect(&voxel_data);
            
            objects.push(ArxObject::new(
                0x0001, // Default building ID
                material,
                (coords.0 as f32 * self.voxel_size * 1000.0) as i16,
                (coords.1 as f32 * self.voxel_size * 1000.0) as i16,
                (coords.2 as f32 * self.voxel_size * 1000.0) as i16,
            ));
        }
        
        objects
    }
    
    /// Voxelize point cloud
    fn voxelize(&self, points: &[[f32; 3]]) -> HashMap<(i32, i32, i32), VoxelData> {
        let mut voxels: HashMap<(i32, i32, i32), Vec<[f32; 3]>> = HashMap::new();
        
        // Group points into voxels
        for point in points {
            let vx = (point[0] / self.voxel_size) as i32;
            let vy = (point[1] / self.voxel_size) as i32;
            let vz = (point[2] / self.voxel_size) as i32;
            
            voxels.entry((vx, vy, vz))
                .or_insert_with(Vec::new)
                .push(*point);
        }
        
        // Analyze each voxel
        let mut analyzed = HashMap::new();
        for ((vx, vy, vz), points) in voxels.iter() {
            let data = VoxelData::from_points(points, *vz as f32 * self.voxel_size);
            
            // Count neighbors for better classification
            let mut neighbor_count = 0;
            for (dx, dy, dz) in &[
                (-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)
            ] {
                if voxels.contains_key(&(vx + dx, vy + dy, vz + dz)) {
                    neighbor_count += 1;
                }
            }
            
            let mut data = data;
            data.neighbor_count = neighbor_count;
            analyzed.insert((*vx, *vy, *vz), data);
        }
        
        analyzed
    }
}

/// Voxel analysis data
#[derive(Debug, Clone)]
pub struct VoxelData {
    pub point_count: usize,
    pub height: f32,
    pub variance: f32,
    pub density: f32,
    pub neighbor_count: usize,
    pub center: [f32; 3],
}

impl VoxelData {
    fn from_points(points: &[[f32; 3]], height: f32) -> Self {
        let count = points.len();
        
        // Calculate center
        let mut center = [0.0, 0.0, 0.0];
        for p in points {
            center[0] += p[0];
            center[1] += p[1];
            center[2] += p[2];
        }
        center[0] /= count as f32;
        center[1] /= count as f32;
        center[2] /= count as f32;
        
        // Calculate variance
        let mut variance = 0.0;
        for p in points {
            let dist_sq = (p[0] - center[0]).powi(2) + 
                         (p[1] - center[1]).powi(2) + 
                         (p[2] - center[2]).powi(2);
            variance += dist_sq;
        }
        variance /= count as f32;
        
        Self {
            point_count: count,
            height,
            variance: variance.sqrt(),
            density: count as f32 / 100.0, // Normalized
            neighbor_count: 0, // Set later
            center,
        }
    }
}

/// Material detection from voxel properties
pub struct MaterialDetector {
    floor_threshold: f32,
    ceiling_threshold: f32,
    wall_density_threshold: f32,
}

impl MaterialDetector {
    pub fn new() -> Self {
        Self {
            floor_threshold: 0.2,
            ceiling_threshold: 2.3,
            wall_density_threshold: 0.7,
        }
    }
    
    /// Detect material type from voxel data
    pub fn detect(&self, voxel: &VoxelData) -> u8 {
        // Height-based detection first
        if voxel.height < self.floor_threshold {
            return object_types::FLOOR;
        }
        if voxel.height > self.ceiling_threshold {
            return object_types::CEILING;
        }
        
        // Density and neighbor analysis
        if voxel.density > self.wall_density_threshold && voxel.neighbor_count >= 4 {
            return object_types::WALL;
        }
        
        // Variance-based detection for special features
        if voxel.variance > 0.5 && voxel.density < 0.3 {
            return object_types::WINDOW; // High variance, low density = opening
        }
        
        if voxel.density > 0.5 && voxel.neighbor_count >= 3 {
            return object_types::COLUMN; // Dense vertical structure
        }
        
        // Check for doors (vertical openings)
        if voxel.height > 0.5 && voxel.height < 2.0 && 
           voxel.variance > 0.3 && voxel.neighbor_count == 2 {
            return object_types::DOOR;
        }
        
        object_types::GENERIC
    }
}

impl Default for PointCloudProcessor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_voxelization() {
        let processor = PointCloudProcessor::new();
        let points = vec![
            [0.0, 0.0, 0.0],
            [0.1, 0.1, 0.0],
            [0.2, 0.2, 0.0],
        ];
        
        let objects = processor.points_to_arxobjects(&points);
        assert_eq!(objects.len(), 1); // Should create 1 voxel
        assert_eq!(objects[0].object_type, object_types::FLOOR);
    }
    
    #[test]
    fn test_material_detection() {
        let detector = MaterialDetector::new();
        
        let floor_voxel = VoxelData {
            point_count: 50,
            height: 0.1,
            variance: 0.1,
            density: 0.5,
            neighbor_count: 6,
            center: [0.0, 0.0, 0.1],
        };
        assert_eq!(detector.detect(&floor_voxel), object_types::FLOOR);
        
        let wall_voxel = VoxelData {
            point_count: 100,
            height: 1.5,
            variance: 0.2,
            density: 0.8,
            neighbor_count: 4,
            center: [0.0, 0.0, 1.5],
        };
        assert_eq!(detector.detect(&wall_voxel), object_types::WALL);
    }
}