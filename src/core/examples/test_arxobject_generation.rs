//! Test ArxObject generation from point clouds
//! 
//! This example helps debug and tune the voxelization parameters

use arxos_core::{
    point_cloud_parser::{PointCloudParser, PointCloud, PlaneType},
    arxobject::{ArxObject, object_types},
    document_parser::Point3D,
};
use std::collections::HashMap;

fn main() {
    // env_logger not available in core examples
    
    println!("Testing ArxObject Generation Pipeline");
    println!("=====================================\n");
    
    // Test 1: Simple synthetic point cloud
    test_synthetic_room();
    
    // Test 2: Dense outlet cluster
    test_outlet_detection();
    
    // Test 3: Wall detection
    test_wall_detection();
}

fn test_synthetic_room() {
    println!("Test 1: Synthetic Room");
    println!("----------------------");
    
    let parser = PointCloudParser::new();
    
    // Create a simple room with floor, walls, and some objects
    let mut points = Vec::new();
    
    // Floor points (z=0, dense grid)
    for x in 0..60 {
        for y in 0..40 {
            points.push(Point3D {
                x: x as f32 * 0.1,  // 6m x 4m room
                y: y as f32 * 0.1,
                z: 0.0,
            });
        }
    }
    println!("  Added {} floor points", 60 * 40);
    
    // Wall points (x=0 plane)
    for y in 0..40 {
        for z in 0..30 {
            points.push(Point3D {
                x: 0.0,
                y: y as f32 * 0.1,
                z: z as f32 * 0.1,
            });
        }
    }
    println!("  Added {} wall points", 40 * 30);
    
    // Outlet cluster at standard height (z=0.3m)
    for dx in -2..=2 {
        for dy in -2..=2 {
            points.push(Point3D {
                x: 1.0 + dx as f32 * 0.01,
                y: 2.0 + dy as f32 * 0.01,
                z: 0.3,
            });
        }
    }
    println!("  Added {} outlet points", 5 * 5);
    
    // Light fixture at ceiling (z=2.7m)
    for dx in -3..=3 {
        for dy in -3..=3 {
            points.push(Point3D {
                x: 3.0 + dx as f32 * 0.01,
                y: 2.0 + dy as f32 * 0.01,
                z: 2.7,
            });
        }
    }
    println!("  Added {} light points", 7 * 7);
    
    let cloud = PointCloud {
        points: points.clone(),
        colors: vec![(255, 255, 255); points.len()],
        normals: vec![Point3D { x: 0.0, y: 0.0, z: 1.0 }; points.len()],
        bounds: calculate_bounds(&points),
    };
    
    println!("\n  Total points: {}", cloud.points.len());
    println!("  Bounds: ({:.1}, {:.1}, {:.1}) to ({:.1}, {:.1}, {:.1})",
        cloud.bounds.min.x, cloud.bounds.min.y, cloud.bounds.min.z,
        cloud.bounds.max.x, cloud.bounds.max.y, cloud.bounds.max.z);
    
    // Test voxelization with different parameters
    test_voxelization(&parser, &cloud, 0.05, 5);   // Default
    test_voxelization(&parser, &cloud, 0.10, 5);   // Larger voxels
    test_voxelization(&parser, &cloud, 0.05, 2);   // Lower threshold
    test_voxelization(&parser, &cloud, 0.02, 2);   // Smaller voxels
}

fn test_outlet_detection() {
    println!("\nTest 2: Outlet Detection");
    println!("------------------------");
    
    let parser = PointCloudParser::new();
    
    // Create dense cluster at outlet height
    let mut points = Vec::new();
    
    // Simulate outlet scan pattern (dense cluster)
    for x in 0..10 {
        for y in 0..6 {
            for z in 0..3 {
                points.push(Point3D {
                    x: 1.0 + x as f32 * 0.005,  // 5cm wide
                    y: 0.1 + y as f32 * 0.005,  // 3cm tall
                    z: 0.3 + z as f32 * 0.005,  // 1.5cm deep
                });
            }
        }
    }
    
    let cloud = PointCloud {
        points: points.clone(),
        colors: vec![(255, 255, 255); points.len()],
        normals: vec![Point3D { x: 0.0, y: 0.0, z: 1.0 }; points.len()],
        bounds: calculate_bounds(&points),
    };
    
    println!("  Points in outlet cluster: {}", points.len());
    
    // Generate ArxObjects
    let objects = parser.to_arxobjects(&cloud, 0x0001);
    println!("  ArxObjects generated: {}", objects.len());
    
    for obj in &objects {
        let obj_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        println!("    Type: 0x{:02X}, Position: ({}, {}, {})",
            obj_type, x, y, z);
    }
}

fn test_wall_detection() {
    println!("\nTest 3: Wall Detection");
    println!("----------------------");
    
    let parser = PointCloudParser::new();
    
    // Create vertical plane (wall)
    let mut points = Vec::new();
    
    // Dense wall surface
    for y in 0..100 {
        for z in 0..60 {
            points.push(Point3D {
                x: 2.0,  // Wall at x=2m
                y: y as f32 * 0.03,  // 3m wide
                z: z as f32 * 0.05,  // 3m tall
            });
        }
    }
    
    let cloud = PointCloud {
        points: points.clone(),
        colors: vec![(200, 200, 200); points.len()],
        normals: vec![Point3D { x: 1.0, y: 0.0, z: 0.0 }; points.len()],
        bounds: calculate_bounds(&points),
    };
    
    println!("  Points in wall: {}", points.len());
    
    // Detect planes
    let planes = parser.detect_planes(&cloud);
    println!("  Planes detected: {}", planes.len());
    
    for plane in &planes {
        println!("    Type: {:?}, Points: {}, Normal: ({:.2}, {:.2}, {:.2})",
            plane.plane_type, plane.points.len(),
            plane.normal.x, plane.normal.y, plane.normal.z);
    }
    
    // Generate ArxObjects
    let objects = parser.to_arxobjects(&cloud, 0x0001);
    println!("  ArxObjects generated: {}", objects.len());
}

fn test_voxelization(parser: &PointCloudParser, cloud: &PointCloud, voxel_size: f32, min_points: usize) {
    println!("\n  Testing voxel_size={:.3}m, min_points={}:", voxel_size, min_points);
    
    // Create custom parser with test parameters
    let mut test_parser = PointCloudParser::new();
    // We can't modify the fields directly, so we'll count voxels manually
    
    let mut voxels = HashMap::new();
    for (i, point) in cloud.points.iter().enumerate() {
        let voxel_x = (point.x / voxel_size) as i32;
        let voxel_y = (point.y / voxel_size) as i32;
        let voxel_z = (point.z / voxel_size) as i32;
        
        voxels.entry((voxel_x, voxel_y, voxel_z))
            .or_insert_with(Vec::new)
            .push(i);
    }
    
    let dense_voxels: Vec<_> = voxels.iter()
        .filter(|(_, indices)| indices.len() >= min_points)
        .collect();
    
    println!("    Total voxels: {}", voxels.len());
    println!("    Dense voxels (>={} points): {}", min_points, dense_voxels.len());
    
    // Show distribution
    let mut height_distribution = HashMap::new();
    for ((_, _, z), indices) in &voxels {
        let height = (*z as f32 * voxel_size * 10.0) as i32 / 10;  // Round to 0.1m
        *height_distribution.entry(height).or_insert(0) += indices.len();
    }
    
    println!("    Height distribution:");
    let mut heights: Vec<_> = height_distribution.keys().collect();
    heights.sort();
    for height in heights {
        let count = height_distribution[height];
        let height_m = *height as f32 / 10.0;
        println!("      {:.1}m: {} points", height_m, count);
    }
}

fn calculate_bounds(points: &[Point3D]) -> arxos_core::document_parser::BoundingBox {
    let mut min = Point3D { x: f32::MAX, y: f32::MAX, z: f32::MAX };
    let mut max = Point3D { x: f32::MIN, y: f32::MIN, z: f32::MIN };
    
    for point in points {
        min.x = min.x.min(point.x);
        min.y = min.y.min(point.y);
        min.z = min.z.min(point.z);
        max.x = max.x.max(point.x);
        max.y = max.y.max(point.y);
        max.z = max.z.max(point.z);
    }
    
    arxos_core::document_parser::BoundingBox { min, max }
}