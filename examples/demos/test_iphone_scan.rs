//! Test enhanced parser on real iPhone LiDAR scan

use arxos_core::{
    point_cloud_parser::PointCloudParser,
    point_cloud_parser_enhanced::EnhancedPointCloudParser,
    arxobject::object_types,
    progressive_renderer::ProgressiveRenderer,
};
use std::collections::HashMap;

fn main() {
    println!("Testing iPhone LiDAR Scan with Enhanced Parser");
    println!("==============================================\n");
    
    let ply_path = "/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply";
    
    println!("Loading: {}", ply_path);
    
    let parser = PointCloudParser::new();
    let cloud = match parser.parse_ply(ply_path) {
        Ok(cloud) => {
            println!("✓ Loaded {} points", cloud.points.len());
            println!("✓ Bounds: ({:.2}, {:.2}, {:.2}) to ({:.2}, {:.2}, {:.2})",
                cloud.bounds.min.x, cloud.bounds.min.y, cloud.bounds.min.z,
                cloud.bounds.max.x, cloud.bounds.max.y, cloud.bounds.max.z);
            cloud
        }
        Err(e) => {
            eprintln!("Failed to parse PLY: {}", e);
            return;
        }
    };
    
    // Analyze point density
    let volume = (cloud.bounds.max.x - cloud.bounds.min.x) *
                 (cloud.bounds.max.y - cloud.bounds.min.y) *
                 (cloud.bounds.max.z - cloud.bounds.min.z);
    let density = cloud.points.len() as f32 / volume;
    println!("✓ Point density: {:.0} points/m³\n", density);
    
    // Test different configurations
    println!("Testing Parser Configurations:");
    println!("------------------------------\n");
    
    // Original parser
    println!("1. Original Parser (5cm voxels, 5-point minimum):");
    let original = PointCloudParser::new();
    let orig_objects = original.to_arxobjects(&cloud, 0x0001);
    println!("   Generated {} ArxObjects", orig_objects.len());
    show_type_summary(&orig_objects);
    
    // Enhanced default
    println!("\n2. Enhanced Default (10cm voxels, 3-point minimum):");
    let enhanced = EnhancedPointCloudParser::new();
    let enh_objects = enhanced.to_arxobjects(&cloud, 0x0001);
    println!("   Generated {} ArxObjects", enh_objects.len());
    show_type_summary(&enh_objects);
    
    // Enhanced dense (for iPhone LiDAR)
    println!("\n3. Enhanced Dense (5cm voxels, 10-point minimum):");
    let dense = EnhancedPointCloudParser::for_dense_scan();
    let dense_objects = dense.to_arxobjects(&cloud, 0x0001);
    println!("   Generated {} ArxObjects", dense_objects.len());
    show_type_summary(&dense_objects);
    
    // Custom tuned for iPhone
    println!("\n4. Custom iPhone Tuning (7cm voxels, 5-point minimum):");
    let mut custom = EnhancedPointCloudParser::new();
    custom.voxel_size = 0.07;  // 7cm voxels
    custom.min_points_per_voxel = 5;
    let custom_objects = custom.to_arxobjects(&cloud, 0x0001);
    println!("   Generated {} ArxObjects", custom_objects.len());
    show_type_summary(&custom_objects);
    
    // Choose best result
    let best_objects = if !dense_objects.is_empty() {
        println!("\nUsing Enhanced Dense configuration");
        dense_objects
    } else if !enh_objects.is_empty() {
        println!("\nUsing Enhanced Default configuration");
        enh_objects
    } else if !custom_objects.is_empty() {
        println!("\nUsing Custom iPhone configuration");
        custom_objects
    } else {
        println!("\nUsing Original configuration");
        orig_objects
    };
    
    // Compression analysis
    println!("\nCompression Analysis:");
    println!("--------------------");
    let original_size = cloud.points.len() * 12; // 3 floats * 4 bytes
    let compressed_size = best_objects.len() * 13;
    let ratio = original_size as f64 / compressed_size as f64;
    
    println!("  Original: {} bytes ({} points)", original_size, cloud.points.len());
    println!("  Compressed: {} bytes ({} objects)", compressed_size, best_objects.len());
    println!("  Compression ratio: {:.1}:1", ratio);
    
    // Show some interesting objects
    println!("\nInteresting Objects Found:");
    println!("-------------------------");
    
    let renderer = ProgressiveRenderer::new();
    let mut shown_types = HashMap::new();
    
    for obj in &best_objects {
        // Skip if we've already shown this type
        if shown_types.contains_key(&obj.object_type) {
            continue;
        }
        
        // Skip floors, ceilings, and walls for display
        if obj.object_type == object_types::FLOOR || 
           obj.object_type == object_types::CEILING ||
           obj.object_type == object_types::WALL ||
           obj.object_type == object_types::GENERIC {
            continue;
        }
        
        let type_name = get_type_name(obj.object_type);
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        
        println!("\n{} at ({}, {}, {})mm:", type_name, x, y, z);
        
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
        
        shown_types.insert(obj.object_type, true);
        
        if shown_types.len() >= 3 {
            break;
        }
    }
}

fn show_type_summary(objects: &[arxos_core::arxobject::ArxObject]) {
    if objects.is_empty() {
        return;
    }
    
    let mut type_counts = HashMap::new();
    for obj in objects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
    }
    
    print!("   Types: ");
    for (i, (obj_type, count)) in type_counts.iter().enumerate() {
        if i > 0 { print!(", "); }
        print!("{} {}", count, get_type_name(*obj_type));
    }
    println!();
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