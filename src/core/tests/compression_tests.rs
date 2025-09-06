//! Comprehensive tests for compression module

use crate::compression::{PointCloudProcessor, VoxelData, MaterialDetector};
use crate::arxobject::{ArxObject, object_types};

#[test]
fn test_compression_ratio() {
    let processor = PointCloudProcessor::new();
    
    // Simulate a dense point cloud
    let mut points = Vec::new();
    for x in 0..100 {
        for y in 0..100 {
            for z in 0..10 {
                points.push([
                    x as f32 * 0.01,
                    y as f32 * 0.01, 
                    z as f32 * 0.01,
                ]);
            }
        }
    }
    
    let original_size = points.len() * 12; // 3 floats * 4 bytes
    let objects = processor.points_to_arxobjects(&points);
    let compressed_size = objects.len() * 13; // ArxObject size
    
    let ratio = original_size as f32 / compressed_size as f32;
    
    // Should achieve significant compression
    assert!(ratio > 10.0, "Compression ratio {:.1} too low", ratio);
}

#[test]
fn test_material_detection_accuracy() {
    let detector = MaterialDetector::new();
    
    // Test floor detection
    let floor = VoxelData {
        point_count: 100,
        height: 0.05,
        variance: 0.1,
        density: 0.8,
        neighbor_count: 6,
        center: [0.5, 0.5, 0.05],
    };
    assert_eq!(detector.detect(&floor), object_types::FLOOR);
    
    // Test wall detection
    let wall = VoxelData {
        point_count: 150,
        height: 1.5,
        variance: 0.15,
        density: 0.9,
        neighbor_count: 4,
        center: [0.0, 0.5, 1.5],
    };
    assert_eq!(detector.detect(&wall), object_types::WALL);
    
    // Test ceiling detection
    let ceiling = VoxelData {
        point_count: 80,
        height: 2.5,
        variance: 0.12,
        density: 0.7,
        neighbor_count: 5,
        center: [0.5, 0.5, 2.5],
    };
    assert_eq!(detector.detect(&ceiling), object_types::CEILING);
    
    // Test door detection
    let door = VoxelData {
        point_count: 30,
        height: 1.0,
        variance: 0.4,
        density: 0.3,
        neighbor_count: 2,
        center: [1.0, 0.0, 1.0],
    };
    assert_eq!(detector.detect(&door), object_types::DOOR);
}

#[test]
fn test_voxel_size_impact() {
    let points = vec![
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.0],
        [1.0, 1.0, 0.0],
        [1.5, 1.5, 0.0],
    ];
    
    // Test with different voxel sizes
    let processor_small = PointCloudProcessor::new().with_voxel_size(0.1);
    let objects_small = processor_small.points_to_arxobjects(&points);
    
    let processor_large = PointCloudProcessor::new().with_voxel_size(1.0);
    let objects_large = processor_large.points_to_arxobjects(&points);
    
    // Smaller voxels should produce more objects
    assert!(objects_small.len() >= objects_large.len());
}

#[test]
fn test_arxobject_serialization() {
    let obj = ArxObject::new(0x0042, object_types::WALL, 1000, 2000, 1500);
    let bytes = obj.to_bytes();
    
    assert_eq!(bytes.len(), 13);
    
    let reconstructed = ArxObject::from_bytes(&bytes);
    assert_eq!(obj.building_id, reconstructed.building_id);
    assert_eq!(obj.object_type, reconstructed.object_type);
    assert_eq!(obj.x, reconstructed.x);
    assert_eq!(obj.y, reconstructed.y);
    assert_eq!(obj.z, reconstructed.z);
}

#[test]
fn test_empty_point_cloud() {
    let processor = PointCloudProcessor::new();
    let points: Vec<[f32; 3]> = vec![];
    let objects = processor.points_to_arxobjects(&points);
    
    assert_eq!(objects.len(), 0);
}

#[test]
fn test_single_point() {
    let processor = PointCloudProcessor::new();
    let points = vec![[0.5, 0.5, 0.1]];
    let objects = processor.points_to_arxobjects(&points);
    
    // Single point might not meet minimum density
    assert!(objects.len() <= 1);
}

#[test]
fn test_coordinate_bounds() {
    let processor = PointCloudProcessor::new();
    
    // Test extreme coordinates
    let points = vec![
        [-100.0, -100.0, -100.0],
        [100.0, 100.0, 100.0],
    ];
    
    let objects = processor.points_to_arxobjects(&points);
    
    for obj in objects {
        // Coordinates should be within i16 bounds
        assert!(obj.x >= i16::MIN && obj.x <= i16::MAX);
        assert!(obj.y >= i16::MIN && obj.y <= i16::MAX);
        assert!(obj.z >= i16::MIN && obj.z <= i16::MAX);
    }
}