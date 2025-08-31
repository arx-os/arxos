//! Test binary for iPhone scan processing

use arxos_core::point_cloud_parser::{PointCloudParser, PointCloudError};
use arxos_core::ArxObject;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("╔════════════════════════════════════════╗");
    println!("║   ARXOS iPhone Scan Test              ║");
    println!("╚════════════════════════════════════════╝\n");

    // Check if PLY file exists
    let ply_path = std::env::args().nth(1)
        .unwrap_or_else(|| "/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply".to_string());
    
    if !Path::new(&ply_path).exists() {
        eprintln!("Error: PLY file not found at {}", ply_path);
        eprintln!("Usage: test_scan [path_to_ply_file]");
        return Ok(());
    }

    println!("📱 Processing: {}", ply_path);
    
    // Create parser
    let parser = PointCloudParser::new();
    
    // Parse PLY file
    println!("📂 Loading PLY file...");
    let point_cloud = parser.parse_ply(&ply_path)?;
    
    println!("✅ Loaded {} points", point_cloud.points.len());
    
    // Find bounds
    let (min, max) = point_cloud.calculate_bounds();
    println!("\n📏 Room Dimensions:");
    println!("   Width:  {:.2}m", max.x - min.x);
    println!("   Depth:  {:.2}m", max.y - min.y);  
    println!("   Height: {:.2}m", max.z - min.z);
    
    // Detect planes
    println!("\n🔍 Detecting planes...");
    let planes = parser.detect_planes(&point_cloud);
    println!("   Found {} planes (floors, walls, ceilings)", planes.len());
    
    // Voxelize
    println!("\n🔲 Voxelizing point cloud...");
    let voxels = parser.voxelize(&point_cloud, 0.05); // 5cm voxels
    println!("   Created {} voxels from {} points", voxels.len(), point_cloud.points.len());
    println!("   Reduction: {:.1}:1", point_cloud.points.len() as f32 / voxels.len() as f32);
    
    // Convert to ArxObjects
    println!("\n📦 Converting to ArxObjects...");
    let arxobjects = parser.to_arxobjects(&point_cloud, 0x0001);
    println!("   Generated {} ArxObjects", arxobjects.len());
    
    // Calculate compression
    let original_size = point_cloud.points.len() * 12; // 3 floats * 4 bytes
    let compressed_size = arxobjects.len() * 13; // 13 bytes per ArxObject
    let ratio = original_size as f32 / compressed_size as f32;
    
    println!("\n🗜️  Compression Results:");
    println!("   Original: {} bytes ({:.2} MB)", original_size, original_size as f32 / 1_000_000.0);
    println!("   Compressed: {} bytes ({:.2} KB)", compressed_size, compressed_size as f32 / 1000.0);
    println!("   Ratio: {:.0}:1", ratio);
    println!("   Space saved: {:.1}%", (1.0 - 1.0/ratio) * 100.0);
    
    // Save sample output
    if let Some(parent) = Path::new(&ply_path).parent() {
        let output_path = parent.join("arxos_output.bin");
        println!("\n💾 Saving ArxObjects to {:?}", output_path);
        
        use std::fs::File;
        use std::io::Write;
        let mut file = File::create(&output_path)?;
        
        for obj in arxobjects.iter().take(1000) { // Save first 1000 objects
            let bytes = obj.to_bytes();
            file.write_all(&bytes)?;
        }
        
        println!("   Saved {} ArxObjects (sample)", arxobjects.len().min(1000));
    }
    
    println!("\n✅ iPhone scan successfully processed!");
    
    Ok(())
}