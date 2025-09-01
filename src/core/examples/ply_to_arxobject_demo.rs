//! Demonstrates PLY to ArxObject conversion with enhanced parser
//! 
//! Shows the improved voxelization and semantic detection

use arxos_core::{
    point_cloud_parser::{PointCloud, PointCloudParser},
    point_cloud_parser_enhanced::EnhancedPointCloudParser,
    document_parser::{Point3D, BoundingBox},
    arxobject::object_types,
    progressive_renderer::ProgressiveRenderer,
};
use std::collections::HashMap;

fn main() {
    println!("ArxOS PLY to ArxObject Pipeline Demo");
    println!("=====================================\n");
    
    // Create a synthetic room with known objects
    let cloud = create_test_room();
    
    println!("Created test point cloud:");
    println!("  Points: {}", cloud.points.len());
    println!("  Bounds: ({:.2}, {:.2}, {:.2}) to ({:.2}, {:.2}, {:.2})\n",
        cloud.bounds.min.x, cloud.bounds.min.y, cloud.bounds.min.z,
        cloud.bounds.max.x, cloud.bounds.max.y, cloud.bounds.max.z);
    
    // Test different parser configurations
    test_parser_configuration("Original Parser (5cm voxels, 5-point minimum)", 
                             &PointCloudParser::new(), &cloud);
    
    test_parser_configuration("Enhanced Default (10cm voxels, 3-point minimum)", 
                             &EnhancedPointCloudParser::new(), &cloud);
    
    test_parser_configuration("Enhanced Dense Mode (5cm voxels, 10-point minimum)", 
                             &EnhancedPointCloudParser::for_dense_scan(), &cloud);
    
    test_parser_configuration("Enhanced Sparse Mode (15cm voxels, 2-point minimum)", 
                             &EnhancedPointCloudParser::for_sparse_scan(), &cloud);
    
    // Show detailed results with best configuration
    println!("\nDetailed Results with Best Configuration");
    println!("=========================================\n");
    
    let best_parser = EnhancedPointCloudParser::new();
    let objects = best_parser.to_arxobjects(&cloud, 0x0001);
    
    if objects.is_empty() {
        println!("No objects generated. Try adjusting voxelization parameters.");
        return;
    }
    
    // Analyze object types
    let mut type_counts = HashMap::new();
    for obj in &objects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
    }
    
    println!("Object Type Distribution:");
    for (obj_type, count) in &type_counts {
        let type_name = get_type_name(*obj_type);
        println!("  {} (0x{:02X}): {}", type_name, obj_type, count);
    }
    
    // Show compression ratio
    let original_size = cloud.points.len() * std::mem::size_of::<Point3D>();
    let compressed_size = objects.len() * 13;
    let ratio = original_size as f64 / compressed_size as f64;
    println!("\nCompression Analysis:");
    println!("  Original: {} bytes", original_size);
    println!("  Compressed: {} bytes", compressed_size);
    println!("  Ratio: {:.1}:1", ratio);
    
    // Render a few objects as ASCII art
    println!("\nASCII Art Rendering Examples:");
    println!("-----------------------------\n");
    
    let renderer = ProgressiveRenderer::new();
    let mut shown = 0;
    
    for obj in &objects {
        if shown >= 3 {
            break;
        }
        
        // Skip floors and ceilings for display
        if obj.object_type == object_types::FLOOR || 
           obj.object_type == object_types::CEILING ||
           obj.object_type == object_types::WALL {
            continue;
        }
        
        let type_name = get_type_name(obj.object_type);
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        println!("Object: {} at ({}, {}, {})mm",
            type_name, x, y, z);
        
        // Render with basic detail level (DetailLevel is a struct, not enum)
        let level = arxos_core::detail_store::DetailLevel {
            basic: true,
            material: 0.5,
            systems: 0.3,
            historical: 0.0,
            simulation: 0.0,
            predictive: 0.0,
        };
        
        let ascii = renderer.render_object(obj, &level);
        for line in ascii.lines() {
            println!("  {}", line);
        }
        println!();
        
        shown += 1;
    }
}

fn test_parser_configuration<P>(name: &str, parser: &P, cloud: &PointCloud) 
where
    P: HasToArxObjects,
{
    println!("Testing: {}", name);
    let objects = parser.to_arxobjects(cloud, 0x0001);
    println!("  Generated {} ArxObjects", objects.len());
    
    if !objects.is_empty() {
        // Quick type summary
        let mut types = HashMap::new();
        for obj in &objects {
            *types.entry(obj.object_type).or_insert(0) += 1;
        }
        
        print!("  Types: ");
        for (i, (t, count)) in types.iter().enumerate() {
            if i > 0 { print!(", "); }
            print!("{} {}", count, get_type_name(*t));
        }
        println!();
    }
    println!();
}

// Trait to handle both parser types
trait HasToArxObjects {
    fn to_arxobjects(&self, cloud: &PointCloud, building_id: u16) -> Vec<arxos_core::arxobject::ArxObject>;
}

impl HasToArxObjects for PointCloudParser {
    fn to_arxobjects(&self, cloud: &PointCloud, building_id: u16) -> Vec<arxos_core::arxobject::ArxObject> {
        self.to_arxobjects(cloud, building_id)
    }
}

impl HasToArxObjects for EnhancedPointCloudParser {
    fn to_arxobjects(&self, cloud: &PointCloud, building_id: u16) -> Vec<arxos_core::arxobject::ArxObject> {
        self.to_arxobjects(cloud, building_id)
    }
}

fn create_test_room() -> PointCloud {
    let mut points = Vec::new();
    
    // Floor (dense grid at z=0)
    for x in 0..30 {
        for y in 0..20 {
            points.push(Point3D {
                x: x as f32 * 0.2,  // 6m x 4m room
                y: y as f32 * 0.2,
                z: 0.0,
            });
        }
    }
    
    // Ceiling (z=3m)
    for x in 0..30 {
        for y in 0..20 {
            points.push(Point3D {
                x: x as f32 * 0.2,
                y: y as f32 * 0.2,
                z: 3.0,
            });
        }
    }
    
    // Wall (x=0 plane)
    for y in 0..20 {
        for z in 0..15 {
            points.push(Point3D {
                x: 0.0,
                y: y as f32 * 0.2,
                z: z as f32 * 0.2,
            });
        }
    }
    
    // Outlet cluster (dense points at outlet height)
    for dx in -10..=10 {
        for dy in -10..=10 {
            for dz in -3..=3 {
                points.push(Point3D {
                    x: 1.5 + dx as f32 * 0.005,
                    y: 2.0 + dy as f32 * 0.005,
                    z: 0.3 + dz as f32 * 0.005,
                });
            }
        }
    }
    
    // Light switch cluster
    for dx in -8..=8 {
        for dy in -8..=8 {
            for dz in -2..=2 {
                points.push(Point3D {
                    x: 0.1 + dx as f32 * 0.005,
                    y: 1.0 + dy as f32 * 0.005,
                    z: 1.2 + dz as f32 * 0.005,
                });
            }
        }
    }
    
    // Thermostat cluster
    for dx in -10..=10 {
        for dy in -10..=10 {
            for dz in -2..=2 {
                points.push(Point3D {
                    x: 3.0 + dx as f32 * 0.005,
                    y: 0.1 + dy as f32 * 0.005,
                    z: 1.5 + dz as f32 * 0.005,
                });
            }
        }
    }
    
    // Ceiling light
    for dx in -15..=15 {
        for dy in -15..=15 {
            points.push(Point3D {
                x: 3.0 + dx as f32 * 0.005,
                y: 2.0 + dy as f32 * 0.005,
                z: 2.8,
            });
        }
    }
    
    println!("Point distribution:");
    println!("  Floor/Ceiling: {} points", 30 * 20 * 2);
    println!("  Wall: {} points", 20 * 15);
    println!("  Outlet: {} points", 21 * 21 * 7);
    println!("  Switch: {} points", 17 * 17 * 5);
    println!("  Thermostat: {} points", 21 * 21 * 5);
    println!("  Light: {} points", 31 * 31);
    println!();
    
    PointCloud {
        points: points.clone(),
        colors: vec![(255, 255, 255); points.len()],
        normals: vec![Point3D { x: 0.0, y: 0.0, z: 1.0 }; points.len()],
        bounds: calculate_bounds(&points),
    }
}

fn calculate_bounds(points: &[Point3D]) -> BoundingBox {
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
    
    BoundingBox { min, max }
}

fn get_type_name(obj_type: u8) -> &'static str {
    match obj_type {
        object_types::OUTLET => "Outlet",
        object_types::LIGHT_SWITCH => "Switch",
        object_types::THERMOSTAT => "Thermostat",
        object_types::LIGHT => "Light",
        object_types::WALL => "Wall",
        object_types::FLOOR => "Floor",
        object_types::CEILING => "Ceiling",
        object_types::GENERIC => "Generic",
        _ => "Unknown",
    }
}