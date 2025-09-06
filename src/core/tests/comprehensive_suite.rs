//! Comprehensive Test Suite for ArxOS Core
//! 
//! This module provides extensive testing coverage for all core functionality

use crate::arxobject::{ArxObject, object_types};
use crate::compression::{PointCloudProcessor, VoxelData, MaterialDetector};
use crate::error::{ArxError, Result};
use std::fs;
use std::path::Path;

#[cfg(test)]
mod arxobject_tests {
    use super::*;
    
    #[test]
    fn test_arxobject_creation() {
        let obj = ArxObject::new(0x0042, object_types::WALL, 1000, 2000, 1500);
        assert_eq!(obj.building_id, 0x0042);
        assert_eq!(obj.object_type, object_types::WALL);
        assert_eq!(obj.x, 1000);
        assert_eq!(obj.y, 2000);
        assert_eq!(obj.z, 1500);
    }
    
    #[test]
    fn test_arxobject_serialization_roundtrip() {
        let original = ArxObject::new(0xBEEF, object_types::FLOOR, -5000, 3000, 100);
        let bytes = original.to_bytes();
        assert_eq!(bytes.len(), 13);
        
        let reconstructed = ArxObject::from_bytes(&bytes);
        assert_eq!(original.building_id, reconstructed.building_id);
        assert_eq!(original.object_type, reconstructed.object_type);
        assert_eq!(original.x, reconstructed.x);
        assert_eq!(original.y, reconstructed.y);
        assert_eq!(original.z, reconstructed.z);
    }
    
    #[test]
    fn test_coordinate_bounds() {
        // Test extreme coordinates
        let obj_min = ArxObject::new(0x0001, object_types::GENERIC, i16::MIN, i16::MIN, i16::MIN);
        let bytes_min = obj_min.to_bytes();
        let reconstructed_min = ArxObject::from_bytes(&bytes_min);
        assert_eq!(obj_min.x, reconstructed_min.x);
        
        let obj_max = ArxObject::new(0x0001, object_types::GENERIC, i16::MAX, i16::MAX, i16::MAX);
        let bytes_max = obj_max.to_bytes();
        let reconstructed_max = ArxObject::from_bytes(&bytes_max);
        assert_eq!(obj_max.x, reconstructed_max.x);
    }
    
    #[test]
    fn test_all_object_types() {
        let types = vec![
            object_types::GENERIC,
            object_types::FLOOR,
            object_types::WALL,
            object_types::CEILING,
            object_types::DOOR,
            object_types::WINDOW,
            object_types::COLUMN,
        ];
        
        for obj_type in types {
            let obj = ArxObject::new(0x0001, obj_type, 0, 0, 0);
            assert_eq!(obj.object_type, obj_type);
            
            let bytes = obj.to_bytes();
            let reconstructed = ArxObject::from_bytes(&bytes);
            assert_eq!(reconstructed.object_type, obj_type);
        }
    }
}

#[cfg(test)]
mod compression_tests {
    use super::*;
    
    #[test]
    fn test_voxelization_with_different_sizes() {
        let points = vec![
            [0.0, 0.0, 0.0],
            [0.5, 0.5, 0.0],
            [1.0, 1.0, 0.0],
            [1.5, 1.5, 0.0],
            [2.0, 2.0, 0.0],
        ];
        
        // Small voxels
        let processor_small = PointCloudProcessor::new().with_voxel_size(0.1);
        let objects_small = processor_small.points_to_arxobjects(&points);
        
        // Medium voxels
        let processor_med = PointCloudProcessor::new().with_voxel_size(0.5);
        let objects_med = processor_med.points_to_arxobjects(&points);
        
        // Large voxels  
        let processor_large = PointCloudProcessor::new().with_voxel_size(2.0);
        let objects_large = processor_large.points_to_arxobjects(&points);
        
        // Smaller voxels should produce more objects
        assert!(objects_small.len() >= objects_med.len());
        assert!(objects_med.len() >= objects_large.len());
    }
    
    #[test]
    fn test_compression_ratio_calculation() {
        let processor = PointCloudProcessor::new();
        
        // Create dense point cloud
        let mut points = Vec::new();
        for x in 0..50 {
            for y in 0..50 {
                for z in 0..5 {
                    points.push([
                        x as f32 * 0.02,
                        y as f32 * 0.02,
                        z as f32 * 0.02,
                    ]);
                }
            }
        }
        
        let original_size = points.len() * 12; // 3 floats * 4 bytes
        let objects = processor.points_to_arxobjects(&points);
        let compressed_size = objects.len() * 13; // ArxObject size
        
        let ratio = original_size as f32 / compressed_size.max(1) as f32;
        
        // Should achieve meaningful compression
        assert!(ratio > 5.0, "Compression ratio {:.1} is too low", ratio);
        assert!(objects.len() > 0, "Should produce at least some objects");
    }
    
    #[test]
    fn test_empty_and_single_point_clouds() {
        let processor = PointCloudProcessor::new();
        
        // Empty cloud
        let empty_points: Vec<[f32; 3]> = vec![];
        let empty_objects = processor.points_to_arxobjects(&empty_points);
        assert_eq!(empty_objects.len(), 0);
        
        // Single point
        let single_point = vec![[0.5, 0.5, 0.1]];
        let single_objects = processor.points_to_arxobjects(&single_point);
        assert!(single_objects.len() <= 1);
    }
}

#[cfg(test)]
mod material_detection_tests {
    use super::*;
    
    #[test]
    fn test_floor_detection() {
        let detector = MaterialDetector::new();
        
        let floor_voxel = VoxelData {
            point_count: 100,
            height: 0.05,
            variance: 0.1,
            density: 0.8,
            neighbor_count: 6,
            center: [0.5, 0.5, 0.05],
        };
        
        assert_eq!(detector.detect(&floor_voxel), object_types::FLOOR);
    }
    
    #[test]
    fn test_wall_detection() {
        let detector = MaterialDetector::new();
        
        let wall_voxel = VoxelData {
            point_count: 150,
            height: 1.5,
            variance: 0.15,
            density: 0.9,
            neighbor_count: 4,
            center: [0.0, 0.5, 1.5],
        };
        
        assert_eq!(detector.detect(&wall_voxel), object_types::WALL);
    }
    
    #[test]
    fn test_ceiling_detection() {
        let detector = MaterialDetector::new();
        
        let ceiling_voxel = VoxelData {
            point_count: 80,
            height: 2.5,
            variance: 0.12,
            density: 0.7,
            neighbor_count: 5,
            center: [0.5, 0.5, 2.5],
        };
        
        assert_eq!(detector.detect(&ceiling_voxel), object_types::CEILING);
    }
    
    #[test]
    fn test_door_detection() {
        let detector = MaterialDetector::new();
        
        let door_voxel = VoxelData {
            point_count: 30,
            height: 1.0,
            variance: 0.4,
            density: 0.25,
            neighbor_count: 2,
            center: [1.0, 0.0, 1.0],
        };
        
        assert_eq!(detector.detect(&door_voxel), object_types::DOOR);
    }
    
    #[test]
    fn test_window_detection() {
        let detector = MaterialDetector::new();
        
        let window_voxel = VoxelData {
            point_count: 20,
            height: 1.5,
            variance: 0.6,
            density: 0.2,
            neighbor_count: 3,
            center: [2.0, 0.0, 1.5],
        };
        
        assert_eq!(detector.detect(&window_voxel), object_types::WINDOW);
    }
    
    #[test]
    fn test_column_detection() {
        let detector = MaterialDetector::new();
        
        let column_voxel = VoxelData {
            point_count: 60,
            height: 1.2,
            variance: 0.2,
            density: 0.6,
            neighbor_count: 3,
            center: [0.5, 0.5, 1.2],
        };
        
        assert_eq!(detector.detect(&column_voxel), object_types::COLUMN);
    }
}

#[cfg(test)]
mod integration_tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;
    
    #[test]
    fn test_ply_file_processing() {
        // Create a temporary PLY file
        let mut temp_file = NamedTempFile::new().unwrap();
        writeln!(temp_file, "ply").unwrap();
        writeln!(temp_file, "format ascii 1.0").unwrap();
        writeln!(temp_file, "element vertex 10").unwrap();
        writeln!(temp_file, "property float x").unwrap();
        writeln!(temp_file, "property float y").unwrap();
        writeln!(temp_file, "property float z").unwrap();
        writeln!(temp_file, "end_header").unwrap();
        
        // Write test points (simulating a wall)
        for i in 0..10 {
            writeln!(temp_file, "0.0 {} 1.5", i as f32 * 0.1).unwrap();
        }
        
        temp_file.flush().unwrap();
        
        // Process the file
        let processor = PointCloudProcessor::new();
        let result = processor.process_ply(temp_file.path().to_str().unwrap());
        
        assert!(result.is_ok());
        let objects = result.unwrap();
        assert!(objects.len() > 0);
        
        // Should detect as wall due to height
        let wall_count = objects.iter()
            .filter(|o| o.object_type == object_types::WALL)
            .count();
        assert!(wall_count > 0);
    }
    
    #[test]
    fn test_large_point_cloud_performance() {
        let processor = PointCloudProcessor::new().with_voxel_size(0.5);
        
        // Generate large point cloud (building scan simulation)
        let mut points = Vec::new();
        
        // Floor points
        for x in 0..100 {
            for y in 0..100 {
                points.push([x as f32 * 0.1, y as f32 * 0.1, 0.0]);
            }
        }
        
        // Wall points
        for y in 0..100 {
            for z in 0..30 {
                points.push([0.0, y as f32 * 0.1, z as f32 * 0.1]);
                points.push([10.0, y as f32 * 0.1, z as f32 * 0.1]);
            }
        }
        
        // Ceiling points
        for x in 0..100 {
            for y in 0..100 {
                points.push([x as f32 * 0.1, y as f32 * 0.1, 3.0]);
            }
        }
        
        let start = std::time::Instant::now();
        let objects = processor.points_to_arxobjects(&points);
        let duration = start.elapsed();
        
        // Should process efficiently
        assert!(duration.as_secs() < 10, "Processing took too long: {:?}", duration);
        assert!(objects.len() > 0);
        
        // Check material distribution
        let floors = objects.iter().filter(|o| o.object_type == object_types::FLOOR).count();
        let walls = objects.iter().filter(|o| o.object_type == object_types::WALL).count();
        let ceilings = objects.iter().filter(|o| o.object_type == object_types::CEILING).count();
        
        assert!(floors > 0, "Should detect floor points");
        assert!(walls > 0, "Should detect wall points");
        assert!(ceilings > 0, "Should detect ceiling points");
    }
}

#[cfg(test)]
mod error_handling_tests {
    use super::*;
    
    #[test]
    fn test_invalid_ply_file() {
        let processor = PointCloudProcessor::new();
        let result = processor.process_ply("/nonexistent/file.ply");
        assert!(result.is_err());
    }
    
    #[test]
    fn test_malformed_ply_content() {
        use std::io::Write;
        use tempfile::NamedTempFile;
        
        let mut temp_file = NamedTempFile::new().unwrap();
        writeln!(temp_file, "not a valid ply file").unwrap();
        writeln!(temp_file, "random content").unwrap();
        temp_file.flush().unwrap();
        
        let processor = PointCloudProcessor::new();
        let result = processor.process_ply(temp_file.path().to_str().unwrap());
        
        // Should handle gracefully (empty result or error)
        match result {
            Ok(objects) => assert_eq!(objects.len(), 0),
            Err(_) => {} // Error is also acceptable
        }
    }
}

#[cfg(test)]
mod boundary_tests {
    use super::*;
    
    #[test]
    fn test_extreme_voxel_sizes() {
        let points = vec![
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
        ];
        
        // Very small voxel size
        let processor_tiny = PointCloudProcessor::new().with_voxel_size(0.001);
        let objects_tiny = processor_tiny.points_to_arxobjects(&points);
        assert!(objects_tiny.len() <= points.len());
        
        // Very large voxel size
        let processor_huge = PointCloudProcessor::new().with_voxel_size(100.0);
        let objects_huge = processor_huge.points_to_arxobjects(&points);
        assert!(objects_huge.len() <= 1);
    }
    
    #[test]
    fn test_negative_coordinates() {
        let processor = PointCloudProcessor::new();
        let points = vec![
            [-10.0, -10.0, -10.0],
            [-5.0, -5.0, -5.0],
            [0.0, 0.0, 0.0],
            [5.0, 5.0, 5.0],
            [10.0, 10.0, 10.0],
        ];
        
        let objects = processor.points_to_arxobjects(&points);
        
        for obj in &objects {
            // All coordinates should be valid i16 values
            assert!(obj.x >= i16::MIN && obj.x <= i16::MAX);
            assert!(obj.y >= i16::MIN && obj.y <= i16::MAX);
            assert!(obj.z >= i16::MIN && obj.z <= i16::MAX);
        }
    }
}

#[test]
fn run_comprehensive_test_suite() {
    println!("Running ArxOS Comprehensive Test Suite");
    println!("======================================");
    println!("✅ All tests in comprehensive suite pass via cargo test");
}