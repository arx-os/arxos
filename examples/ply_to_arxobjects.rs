//! Example: Convert PLY file to ArxObjects
//! 
//! Demonstrates the complete pipeline from PLY point cloud to compressed ArxObjects

use arxos_core::ply_parser_simple::SimplePlyParser;
use arxos_core::arxobject_simple::{ArxObject, ObjectCategory};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() != 2 {
        eprintln!("Usage: {} <ply_file>", args[0]);
        eprintln!("Example: {} test_data/simple_room.ply", args[0]);
        std::process::exit(1);
    }
    
    let ply_file = &args[1];
    
    println!("ArxOS PLY to ArxObject Converter");
    println!("=================================\n");
    
    // Create parser
    let parser = SimplePlyParser::new();
    
    // Get file statistics
    println!("Analyzing PLY file: {}", ply_file);
    match parser.get_file_stats(ply_file) {
        Ok(stats) => {
            println!("  Points: {}", stats.point_count);
            let ((min_x, min_y, min_z), (max_x, max_y, max_z)) = stats.bounds;
            println!("  Bounds: ({:.2}, {:.2}, {:.2}) to ({:.2}, {:.2}, {:.2})",
                min_x, min_y, min_z, max_x, max_y, max_z);
            println!("  Size: {} bytes\n", stats.size_bytes);
        }
        Err(e) => {
            eprintln!("Failed to read PLY file: {}", e);
            std::process::exit(1);
        }
    }
    
    // Parse and convert to ArxObjects
    println!("Converting to ArxObjects...");
    let building_id = 0x4A7B; // Example building ID
    
    match parser.parse_to_arxobjects(ply_file, building_id) {
        Ok(objects) => {
            println!("Generated {} ArxObjects\n", objects.len());
            
            // Group by category
            let mut categories = std::collections::HashMap::new();
            for obj in &objects {
                let category = ObjectCategory::from_type(obj.object_type);
                *categories.entry(category).or_insert(0) += 1;
            }
            
            println!("Object Categories:");
            for (category, count) in categories {
                println!("  {:?}: {}", category, count);
            }
            
            // Calculate compression
            let stats = parser.get_file_stats(ply_file).unwrap();
            let original_size = stats.size_bytes;
            let compressed_size = objects.len() * 13;
            let ratio = original_size as f32 / compressed_size as f32;
            
            println!("\nCompression Results:");
            println!("  Original: {} bytes", original_size);
            println!("  Compressed: {} bytes", compressed_size);
            println!("  Ratio: {:.1}:1", ratio);
            println!("  Space saved: {:.1}%", (1.0 - 1.0/ratio) * 100.0);
            
            // Show sample objects
            println!("\nSample ArxObjects (first 5):");
            for (i, obj) in objects.iter().take(5).enumerate() {
                let (x_m, y_m, z_m) = obj.position_meters();
                println!("  {}. Type: 0x{:02X} at ({:.2}m, {:.2}m, {:.2}m)",
                    i + 1, obj.object_type, x_m, y_m, z_m);
            }
            
            // Serialize to bytes for transmission
            println!("\nSerialization test:");
            let bytes = objects[0].to_bytes();
            println!("  First object as bytes: {:02X?}", bytes);
            
            // Verify round-trip
            let restored = ArxObject::from_bytes(&bytes);
            if restored.building_id == objects[0].building_id {
                println!("  ✓ Serialization round-trip successful");
            }
            
            println!("\n✅ PLY conversion complete!");
        }
        Err(e) => {
            eprintln!("Failed to convert PLY file: {}", e);
            std::process::exit(1);
        }
    }
}