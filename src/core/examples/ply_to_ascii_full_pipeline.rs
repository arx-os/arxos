//! Complete PLY to ASCII to ArxObject pipeline demonstration
//! 
//! This example shows the entire workflow from point cloud to compressed objects

use arxos_core::{
    document_parser::{DocumentParser, Point3D},
    point_cloud_parser::PointCloudParser,
    point_cloud_parser_enhanced::EnhancedPointCloudParser,
    progressive_renderer::ProgressiveRenderer,
    arxobject::{ArxObject, object_types},
    detail_store::{DetailStore, DetailLevel},
};
use std::path::Path;

fn main() {
    println!("ArxOS Complete Pipeline: PLY → ASCII → ArxObject");
    println!("================================================\n");
    
    // Step 1: Load PLY file
    let ply_path = "/Users/joelpate/repos/arxos/test_data/simple_room.ply";
    
    if !Path::new(ply_path).exists() {
        eprintln!("PLY file not found at: {}", ply_path);
        eprintln!("Creating synthetic test data instead...\n");
        run_synthetic_test();
        return;
    }
    
    println!("Step 1: Loading PLY file");
    println!("------------------------");
    
    let parser = DocumentParser::new();
    let cloud = match parser.parse_ply(ply_path) {
        Ok(cloud) => {
            println!("  ✓ Loaded {} points", cloud.points.len());
            println!("  ✓ Bounds: ({:.2}, {:.2}, {:.2}) to ({:.2}, {:.2}, {:.2})",
                cloud.bounds.min.x, cloud.bounds.min.y, cloud.bounds.min.z,
                cloud.bounds.max.x, cloud.bounds.max.y, cloud.bounds.max.z);
            cloud
        }
        Err(e) => {
            eprintln!("  ✗ Failed to parse PLY: {}", e);
            eprintln!("  Running synthetic test instead...\n");
            run_synthetic_test();
            return;
        }
    };
    
    // Step 2: Compare parsers
    println!("\nStep 2: Point Cloud to ArxObjects");
    println!("----------------------------------");
    
    // Original parser
    println!("\n  A. Original Parser (5cm voxels, 5-point minimum):");
    let original_parser = PointCloudParser::new();
    let original_objects = original_parser.to_arxobjects(&cloud, 0x0001);
    println!("     Generated {} ArxObjects", original_objects.len());
    
    // Enhanced parser with default settings
    println!("\n  B. Enhanced Parser (10cm voxels, 3-point minimum):");
    let enhanced_parser = EnhancedPointCloudParser::new();
    let enhanced_objects = enhanced_parser.to_arxobjects(&cloud, 0x0001);
    println!("     Generated {} ArxObjects", enhanced_objects.len());
    
    // Enhanced parser for sparse data
    println!("\n  C. Enhanced Parser for Sparse (15cm voxels, 2-point minimum):");
    let sparse_parser = EnhancedPointCloudParser::for_sparse_scan();
    let sparse_objects = sparse_parser.to_arxobjects(&cloud, 0x0001);
    println!("     Generated {} ArxObjects", sparse_objects.len());
    
    // Choose best result
    let objects = if !enhanced_objects.is_empty() {
        enhanced_objects
    } else if !sparse_objects.is_empty() {
        sparse_objects
    } else {
        original_objects
    };
    
    if objects.is_empty() {
        println!("\n  ⚠ No objects generated. Testing with synthetic data...\n");
        run_synthetic_test();
        return;
    }
    
    // Step 3: Analyze compression
    println!("\nStep 3: Compression Analysis");
    println!("----------------------------");
    
    let original_size = cloud.points.len() * std::mem::size_of::<Point3D>();
    let compressed_size = objects.len() * 13; // ArxObject is 13 bytes
    let ratio = original_size as f64 / compressed_size as f64;
    
    println!("  Original point cloud: {} bytes ({} points × {} bytes)",
        original_size, cloud.points.len(), std::mem::size_of::<Point3D>());
    println!("  Compressed ArxObjects: {} bytes ({} objects × 13 bytes)",
        compressed_size, objects.len());
    println!("  Compression ratio: {:.1}:1", ratio);
    
    // Step 4: Render as ASCII art
    println!("\nStep 4: Progressive ASCII Rendering");
    println!("-----------------------------------");
    
    let renderer = ProgressiveRenderer::new();
    let mut detail_store = DetailStore::new();
    
    // Add objects to detail store
    for obj in &objects {
        detail_store.add_object(*obj);
    }
    
    // Render at different detail levels
    for level in [DetailLevel::Basic, DetailLevel::Enhanced, DetailLevel::Full] {
        println!("\n  Level: {:?}", level);
        println!("  {}", "-".repeat(40));
        
        for obj in objects.iter().take(3) {  // Show first 3 objects
            let obj_type = obj.object_type;
            let x = obj.x;
            let y = obj.y;
            let z = obj.z;
            
            println!("\n  Object type 0x{:02X} at ({}, {}, {})mm:",
                obj_type, x, y, z);
            
            let ascii = renderer.render_object(obj, level);
            for line in ascii.lines() {
                println!("    {}", line);
            }
        }
        
        if objects.len() > 3 {
            println!("\n  ... and {} more objects", objects.len() - 3);
        }
    }
    
    // Step 5: Summary
    println!("\nStep 5: Pipeline Summary");
    println!("------------------------");
    println!("  ✓ Loaded {} points from PLY", cloud.points.len());
    println!("  ✓ Generated {} ArxObjects", objects.len());
    println!("  ✓ Achieved {:.1}:1 compression", ratio);
    println!("  ✓ Rendered ASCII art at 3 detail levels");
    
    // Object type distribution
    let mut type_counts = std::collections::HashMap::new();
    for obj in &objects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
    }
    
    println!("\n  Object Type Distribution:");
    for (obj_type, count) in type_counts {
        let type_name = match obj_type {
            object_types::OUTLET => "Outlet",
            object_types::LIGHT_SWITCH => "Light Switch",
            object_types::THERMOSTAT => "Thermostat",
            object_types::LIGHT => "Light",
            object_types::WALL => "Wall",
            object_types::FLOOR => "Floor",
            object_types::CEILING => "Ceiling",
            object_types::GENERIC => "Generic",
            _ => "Unknown",
        };
        println!("    {} (0x{:02X}): {}", type_name, obj_type, count);
    }
}

fn run_synthetic_test() {
    println!("Synthetic Test: Creating Room with Known Objects");
    println!("================================================\n");
    
    // Create synthetic point cloud with known objects
    let mut points = Vec::new();
    
    // Add floor (dense grid at z=0)
    for x in 0..50 {
        for y in 0..50 {
            points.push(Point3D {
                x: x as f32 * 0.1,
                y: y as f32 * 0.1,
                z: 0.0,
            });
        }
    }
    
    // Add outlet cluster (at standard height)
    for dx in -5..=5 {
        for dy in -5..=5 {
            for dz in -2..=2 {
                points.push(Point3D {
                    x: 1.0 + dx as f32 * 0.01,
                    y: 2.0 + dy as f32 * 0.01,
                    z: 0.3 + dz as f32 * 0.01,
                });
            }
        }
    }
    
    // Add light switch cluster
    for dx in -5..=5 {
        for dy in -5..=5 {
            for dz in -2..=2 {
                points.push(Point3D {
                    x: 2.0 + dx as f32 * 0.01,
                    y: 0.1 + dy as f32 * 0.01,
                    z: 1.2 + dz as f32 * 0.01,
                });
            }
        }
    }
    
    // Add thermostat cluster
    for dx in -6..=6 {
        for dy in -6..=6 {
            for dz in -1..=1 {
                points.push(Point3D {
                    x: 3.0 + dx as f32 * 0.01,
                    y: 2.0 + dy as f32 * 0.01,
                    z: 1.5 + dz as f32 * 0.01,
                });
            }
        }
    }
    
    // Add ceiling light
    for dx in -8..=8 {
        for dy in -8..=8 {
            points.push(Point3D {
                x: 2.5 + dx as f32 * 0.01,
                y: 2.5 + dy as f32 * 0.01,
                z: 2.7,
            });
        }
    }
    
    println!("Created synthetic point cloud with {} points", points.len());
    println!("  - Floor: 2500 points");
    println!("  - Outlet: 605 points");
    println!("  - Light switch: 605 points");
    println!("  - Thermostat: 507 points");
    println!("  - Ceiling light: 289 points");
    
    let cloud = arxos_core::point_cloud_parser::PointCloud {
        points: points.clone(),
        colors: vec![(255, 255, 255); points.len()],
        normals: vec![Point3D { x: 0.0, y: 0.0, z: 1.0 }; points.len()],
        bounds: calculate_bounds(&points),
    };
    
    // Test with enhanced parser
    println!("\nTesting Enhanced Parser:");
    let parser = EnhancedPointCloudParser::new();
    let objects = parser.to_arxobjects(&cloud, 0x0001);
    
    println!("\nGenerated {} ArxObjects", objects.len());
    
    // Render some objects
    let renderer = ProgressiveRenderer::new();
    for (i, obj) in objects.iter().enumerate().take(5) {
        let obj_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        
        println!("\n[{}] Type 0x{:02X} at ({}, {}, {})mm",
            i, obj_type, x, y, z);
        
        let ascii = renderer.render_object(obj, DetailLevel::Enhanced);
        for line in ascii.lines() {
            println!("  {}", line);
        }
    }
    
    // Compression stats
    let original_size = points.len() * std::mem::size_of::<Point3D>();
    let compressed_size = objects.len() * 13;
    let ratio = original_size as f64 / compressed_size as f64;
    
    println!("\nCompression Statistics:");
    println!("  Original: {} bytes", original_size);
    println!("  Compressed: {} bytes", compressed_size);
    println!("  Ratio: {:.1}:1", ratio);
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