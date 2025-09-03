//! Process real house scan through ArxOS pipeline

use arxos_core::ply_parser_simple::SimplePlyParser;
use arxos_core::persistence_simple::ArxObjectDatabase;
use arxos_core::arxobject_simple::{ObjectCategory, object_types};
use std::collections::HashMap;
use std::time::Instant;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let ply_file = "/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply";
    
    println!("╔══════════════════════════════════════════════════════╗");
    println!("║     ArxOS House Scan Processing Pipeline             ║");
    println!("╚══════════════════════════════════════════════════════╝");
    println!();
    
    // Step 1: Analyze PLY file
    println!("📊 ANALYZING PLY FILE");
    println!("━━━━━━━━━━━━━━━━━━━━");
    
    let file_size = std::fs::metadata(ply_file)?.len();
    println!("  File: {}", ply_file);
    println!("  Size: {:.2} MB", file_size as f64 / 1_048_576.0);
    
    let parser = SimplePlyParser::new();
    
    // Get statistics
    let start = Instant::now();
    let stats = parser.get_file_stats(ply_file)?;
    let parse_time = start.elapsed();
    
    println!("  Points: {:,}", stats.point_count);
    let ((min_x, min_y, min_z), (max_x, max_y, max_z)) = stats.bounds;
    println!("  Bounds:");
    println!("    X: {:.2}m to {:.2}m (width: {:.2}m)", min_x, max_x, max_x - min_x);
    println!("    Y: {:.2}m to {:.2}m (depth: {:.2}m)", min_y, max_y, max_y - min_y);
    println!("    Z: {:.2}m to {:.2}m (height: {:.2}m)", min_z, max_z, max_z - min_z);
    println!("  Parse time: {:?}", parse_time);
    println!();
    
    // Step 2: Convert to ArxObjects
    println!("🔄 CONVERTING TO ARXOBJECTS");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    let start = Instant::now();
    let building_id = 0x0001; // Your house
    let objects = parser.parse_to_arxobjects(ply_file, building_id)?;
    let conversion_time = start.elapsed();
    
    println!("  Generated: {:,} ArxObjects", objects.len());
    println!("  Conversion time: {:?}", conversion_time);
    
    // Analyze object types
    let mut type_counts: HashMap<u8, usize> = HashMap::new();
    let mut height_distribution: HashMap<String, usize> = HashMap::new();
    
    for obj in &objects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
        
        let (_x, _y, z) = obj.position_meters();
        let floor = if z < 0.5 {
            "Ground (0-0.5m)"
        } else if z < 1.0 {
            "Low (0.5-1m)"
        } else if z < 1.5 {
            "Mid (1-1.5m)"
        } else if z < 2.0 {
            "High (1.5-2m)"
        } else if z < 2.5 {
            "Ceiling (2-2.5m)"
        } else {
            "Above (>2.5m)"
        };
        *height_distribution.entry(floor.to_string()).or_insert(0) += 1;
    }
    
    println!("\n  Object Types Detected:");
    for (type_code, count) in type_counts.iter() {
        let category = ObjectCategory::from_type(*type_code);
        let name = match *type_code {
            object_types::FLOOR => "Floor",
            object_types::WALL => "Wall",
            object_types::CEILING => "Ceiling",
            object_types::OUTLET => "Outlet",
            object_types::LIGHT_SWITCH => "Light Switch",
            object_types::LIGHT => "Light",
            object_types::DOOR => "Door",
            object_types::WINDOW => "Window",
            object_types::GENERIC => "Generic",
            _ => "Other",
        };
        println!("    {} ({:?}): {:,}", name, category, count);
    }
    
    println!("\n  Height Distribution:");
    let heights = ["Ground (0-0.5m)", "Low (0.5-1m)", "Mid (1-1.5m)", 
                   "High (1.5-2m)", "Ceiling (2-2.5m)", "Above (>2.5m)"];
    for height in &heights {
        if let Some(count) = height_distribution.get(*height) {
            let bar_len = (*count * 30 / objects.len()).min(30);
            let bar = "█".repeat(bar_len);
            println!("    {:<20} {:>6} {}", height, count, bar);
        }
    }
    println!();
    
    // Step 3: Compression Analysis
    println!("📉 COMPRESSION ANALYSIS");
    println!("━━━━━━━━━━━━━━━━━━━━━━");
    
    let original_size = stats.point_count * std::mem::size_of::<(f32, f32, f32)>();
    let compressed_size = objects.len() * 13; // 13 bytes per ArxObject
    let ratio = original_size as f32 / compressed_size as f32;
    
    println!("  Original point cloud:");
    println!("    Points: {:,}", stats.point_count);
    println!("    Size: {:.2} MB (@ 12 bytes/point)", original_size as f64 / 1_048_576.0);
    
    println!("\n  Compressed ArxObjects:");
    println!("    Objects: {:,}", objects.len());
    println!("    Size: {:.2} KB (@ 13 bytes/object)", compressed_size as f64 / 1024.0);
    
    println!("\n  Compression Results:");
    println!("    Ratio: {:.1}:1", ratio);
    println!("    Space saved: {:.1}%", (1.0 - 1.0/ratio) * 100.0);
    println!("    Points per object: {:.1}", stats.point_count as f32 / objects.len() as f32);
    println!();
    
    // Step 4: Store in database
    println!("💾 STORING IN DATABASE");
    println!("━━━━━━━━━━━━━━━━━━━━");
    
    let mut db = ArxObjectDatabase::open("house_scan.db")?;
    
    // Clear previous data
    db.clear()?;
    
    let start = Instant::now();
    let inserted = db.insert_batch(&objects)?;
    let db_time = start.elapsed();
    
    println!("  Inserted: {:,} objects", inserted);
    println!("  Database: house_scan.db");
    println!("  Insert time: {:?}", db_time);
    println!();
    
    // Step 5: Test spatial queries
    println!("🔍 TESTING SPATIAL QUERIES");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━");
    
    // Find objects at typical outlet height (0.3m)
    let outlets = db.find_on_floor(building_id, 0.3, 0.1)?;
    println!("  Objects at outlet height (0.3m ± 0.1m): {:,}", outlets.len());
    
    // Find objects at switch height (1.2m)
    let switches = db.find_on_floor(building_id, 1.2, 0.1)?;
    println!("  Objects at switch height (1.2m ± 0.1m): {:,}", switches.len());
    
    // Find objects at ceiling height
    let ceiling = db.find_on_floor(building_id, 2.5, 0.3)?;
    println!("  Objects at ceiling height (2.5m ± 0.3m): {:,}", ceiling.len());
    
    // Test a spatial query in the center of the room
    let center_x = (min_x + max_x) / 2.0;
    let center_y = (min_y + max_y) / 2.0;
    let center_z = 1.0;
    
    let start = Instant::now();
    let nearby = db.find_within_radius(center_x, center_y, center_z, 2.0)?;
    let query_time = start.elapsed();
    
    println!("\n  Spatial query at room center:");
    println!("    Center: ({:.2}, {:.2}, {:.2})", center_x, center_y, center_z);
    println!("    Radius: 2.0m");
    println!("    Results: {:,} objects", nearby.len());
    println!("    Query time: {:?}", query_time);
    println!();
    
    // Step 6: Summary
    println!("✅ PROCESSING COMPLETE");
    println!("━━━━━━━━━━━━━━━━━━━━━");
    
    let total_time = parse_time + conversion_time + db_time;
    println!("  Total processing time: {:?}", total_time);
    println!("  Processing rate: {:.0} points/second", 
            stats.point_count as f64 / total_time.as_secs_f64());
    
    println!("\n📊 HOUSE INTELLIGENCE SUMMARY:");
    println!("  • Your house scan has been compressed {:.0}x", ratio);
    println!("  • {:,} intelligent objects identified", objects.len());
    println!("  • Spatial queries return in {:?}", query_time);
    println!("  • Ready for mesh network distribution");
    
    // Save some sample objects for inspection
    println!("\n🔬 SAMPLE ARXOBJECTS (First 5):");
    for (i, obj) in objects.iter().take(5).enumerate() {
        let (x, y, z) = obj.position_meters();
        println!("  {}. Type: 0x{:02X} at ({:.2}m, {:.2}m, {:.2}m)",
                i + 1, obj.object_type, x, y, z);
    }
    
    Ok(())
}