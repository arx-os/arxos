//! Example: PLY File to ASCII Art to ArxObject Pipeline
//! 
//! This demonstrates the core ArxOS innovation:
//! 1. Load PLY point cloud (5MB+)
//! 2. Render as ASCII art (visual understanding)
//! 3. Compress to ArxObjects (13 bytes each)

use arxos_core::{
    point_cloud_parser::{PointCloudParser, PointCloud},
    progressive_renderer::{ProgressiveRenderer, render_progress_bar},
    arxobject::{ArxObject, DetailLevel},
};
use std::env;
use std::time::Instant;

fn main() {
    env_logger::init();
    
    // Get PLY file from command line
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <file.ply>", args[0]);
        eprintln!("\nExample: {} /path/to/room_scan.ply", args[0]);
        std::process::exit(1);
    }
    
    let ply_path = &args[1];
    println!("╔══════════════════════════════════════════╗");
    println!("║     ArxOS PLY → ASCII → ArxObject       ║");
    println!("╚══════════════════════════════════════════╝");
    println!();
    
    // Step 1: Load PLY file
    println!("📁 Loading PLY file: {}", ply_path);
    let start = Instant::now();
    
    let parser = PointCloudParser::new();
    let cloud = match parser.parse_ply(ply_path) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("❌ Failed to parse PLY: {}", e);
            std::process::exit(1);
        }
    };
    
    let load_time = start.elapsed();
    println!("✅ Loaded {} points in {:.2}s", cloud.points.len(), load_time.as_secs_f32());
    
    // Calculate original size
    let original_size = cloud.points.len() * 12; // 3 floats per point
    println!("📊 Original size: {:.2} MB", original_size as f32 / 1_000_000.0);
    
    // Step 2: Analyze point cloud
    println!("\n🔍 Analyzing point cloud...");
    let planes = parser.detect_planes(&cloud);
    println!("✅ Detected {} planes", planes.len());
    
    for plane in &planes {
        println!("  - {:?} with {} points", plane.plane_type, plane.points.len());
    }
    
    // Step 3: Convert to building plan
    println!("\n🏢 Converting to building structure...");
    let building_plan = parser.to_building_plan(&cloud, "Scanned Building");
    
    println!("✅ Created building with {} floors", building_plan.floors.len());
    for floor in &building_plan.floors {
        println!("  Floor {}: {} rooms, {} equipment", 
            floor.floor_number, 
            floor.rooms.len(),
            floor.equipment.len()
        );
    }
    
    // Step 4: Render ASCII preview
    println!("\n🎨 Rendering ASCII art preview...");
    render_ascii_preview(&cloud);
    
    // Step 5: Compress to ArxObjects
    println!("\n🗜️ Compressing to ArxObjects...");
    let start = Instant::now();
    let arxobjects = parser.to_arxobjects(&cloud, 0x0001);
    let compress_time = start.elapsed();
    
    println!("✅ Created {} ArxObjects in {:.2}s", arxobjects.len(), compress_time.as_secs_f32());
    
    // Calculate compressed size
    let compressed_size = arxobjects.len() * 13; // 13 bytes per ArxObject
    println!("📊 Compressed size: {:.2} KB", compressed_size as f32 / 1000.0);
    
    // Calculate compression ratio
    let ratio = original_size as f32 / compressed_size as f32;
    println!("🎯 Compression ratio: {:.0}:1", ratio);
    
    // Step 6: Show sample ArxObjects with ASCII art
    println!("\n📦 Sample ArxObjects with progressive rendering:");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    let renderer = ProgressiveRenderer::new();
    
    // Show first few objects at different detail levels
    for (i, obj) in arxobjects.iter().take(5).enumerate() {
        println!("\n🔷 Object #{}", i + 1);
        
        // Show at different detail levels
        let detail_levels = [0.1, 0.5, 1.0];
        for &completeness in &detail_levels {
            let mut detail = DetailLevel::default();
            detail.material = completeness;
            detail.systems = completeness * 0.8;
            
            println!("\n  Detail: {}", render_progress_bar(completeness, 20));
            let ascii = renderer.render_object(obj, &detail);
            
            // Print each line with indent
            for line in ascii.as_str().lines() {
                println!("  {}", line);
            }
        }
    }
    
    // Step 7: Show floor plan
    println!("\n🗺️ ASCII Floor Plan:");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    let objects_with_detail: Vec<(ArxObject, DetailLevel)> = arxobjects
        .into_iter()
        .map(|obj| (obj, DetailLevel::default()))
        .collect();
    
    let floor_plan = renderer.render_floor_plan(&objects_with_detail, 60, 20);
    println!("{}", floor_plan);
    
    // Summary
    println!("\n╔══════════════════════════════════════════╗");
    println!("║              SUMMARY                     ║");
    println!("╠══════════════════════════════════════════╣");
    println!("║ Input:  {:<32.2} MB ║", original_size as f32 / 1_000_000.0);
    println!("║ Output: {:<32.2} KB ║", compressed_size as f32 / 1000.0);
    println!("║ Ratio:  {:<32.0}:1 ║", ratio);
    println!("║ Time:   {:<32.2}s ║", (load_time + compress_time).as_secs_f32());
    println!("╚══════════════════════════════════════════╝");
}

/// Render a simple ASCII preview of the point cloud
fn render_ascii_preview(cloud: &PointCloud) {
    // Create a simple 2D projection (top-down view)
    let mut grid = vec![vec![' '; 80]; 24];
    
    // Find bounds
    let min_x = cloud.bounds.min.x;
    let max_x = cloud.bounds.max.x;
    let min_y = cloud.bounds.min.y;
    let max_y = cloud.bounds.max.y;
    
    // Sample points for display
    let step = (cloud.points.len() / 1000).max(1); // Show up to 1000 points
    
    for (i, point) in cloud.points.iter().enumerate() {
        if i % step != 0 { continue; }
        
        // Map to grid coordinates
        let x = ((point.x - min_x) / (max_x - min_x) * 79.0) as usize;
        let y = ((point.y - min_y) / (max_y - min_y) * 23.0) as usize;
        
        if x < 80 && y < 24 {
            // Use different characters based on height
            let height_ratio = (point.z - cloud.bounds.min.z) / 
                             (cloud.bounds.max.z - cloud.bounds.min.z);
            
            grid[y][x] = match height_ratio {
                h if h < 0.1 => '.',  // Floor level
                h if h < 0.5 => '░',  // Low
                h if h < 0.8 => '▒',  // Mid
                _ => '▓',             // High/Ceiling
            };
        }
    }
    
    // Print grid with border
    println!("┌────────────────────────────────────────────────────────────────────────────────┐");
    for row in grid {
        print!("│");
        for ch in row {
            print!("{}", ch);
        }
        println!("│");
    }
    println!("└────────────────────────────────────────────────────────────────────────────────┘");
    
    // Legend
    println!("  Legend: [.] Floor  [░] Low  [▒] Mid  [▓] High/Ceiling");
}