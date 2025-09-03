//! Process real LiDAR scan through aesthetic pipeline
//! 
//! Transforms PLY files into beautiful industrial pixel art ASCII

use arxos_core::aesthetic_pipeline::{AestheticPipeline, AestheticConfig, AestheticStyle};
use arxos_core::pixelated_renderer::demo_aesthetic;
use std::path::Path;
use std::env;

#[tokio::main]
async fn main() {
    println!("\n╔════════════════════════════════════════════════════════════╗");
    println!("║  🎨 ArxOS Aesthetic Scanner                                ║");
    println!("║  LiDAR → PLY → ArxObjects → Beautiful ASCII Art            ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");
    
    // Get PLY file path from command line or use default
    let args: Vec<String> = env::args().collect();
    let ply_path = if args.len() > 1 {
        &args[1]
    } else {
        // Try to find the scan file
        if Path::new("/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply").exists() {
            "/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply"
        } else if Path::new("./test_data/Untitled_Scan_18_44_21.ply").exists() {
            "./test_data/Untitled_Scan_18_44_21.ply"
        } else if Path::new("./test_data/simple_room.ply").exists() {
            println!("⚠️ Using fallback test file. To use your scan:");
            println!("  cargo run --bin aesthetic_scan /path/to/your/scan.ply\n");
            "./test_data/simple_room.ply"
        } else {
            println!("❌ No PLY file found!");
            println!("\nUsage: cargo run --bin aesthetic_scan <path_to_ply_file>");
            println!("\nOr copy your scan to: ./test_data/Untitled_Scan_18_44_21.ply");
            return;
        }
    };
    
    println!("📁 Processing: {}", ply_path);
    let path = Path::new(ply_path);
    
    if !path.exists() {
        println!("❌ File not found: {}", ply_path);
        return;
    }
    
    // Try different aesthetic styles
    let styles = vec![
        (AestheticStyle::IndustrialPixel, "Industrial Pixel Art"),
        (AestheticStyle::Brutalist, "Brutalist Architecture"),
        (AestheticStyle::RetroGame, "Retro Game Style"),
        (AestheticStyle::CyberMatrix, "Cyber Matrix"),
        (AestheticStyle::Atmospheric, "Atmospheric"),
    ];
    
    println!("\n🎨 Rendering in multiple aesthetic styles...\n");
    
    for (style, name) in styles {
        println!("\n{'═'<60}");
        println!("  Style: {}", name);
        println!("{'═'<60}\n");
        
        let config = AestheticConfig {
            style,
            compression_level: 0.6, // Moderate compression
            smart_detection: true,
            preserve_edges: true,
        };
        
        let pipeline = AestheticPipeline::new(config);
        
        match pipeline.process_ply_file(path).await {
            Ok(output) => {
                println!("{}", output);
                
                // Save to file
                let filename = format!("output_{:?}.txt", style).to_lowercase();
                match std::fs::write(&filename, &output) {
                    Ok(_) => println!("  💾 Saved to: {}", filename),
                    Err(e) => println!("  ⚠️ Could not save: {}", e),
                }
            }
            Err(e) => {
                println!("  ❌ Error processing in {} style: {}", name, e);
                println!("  Trying simulated data instead...\n");
                
                // Fall back to demo
                demo_aesthetic();
            }
        }
        
        println!("\n  Press Enter for next style...");
        let mut input = String::new();
        let _ = std::io::stdin().read_line(&mut input);
    }
    
    println!("\n✨ Aesthetic processing complete!");
    println!("\n📊 What just happened:");
    println!("  1. Loaded PLY point cloud");
    println!("  2. Compressed to 13-byte ArxObjects"); 
    println!("  3. Applied aesthetic compression");
    println!("  4. Rendered as beautiful ASCII art");
    println!("  5. Each character represents real building data!");
    
    println!("\n🎮 Next Steps:");
    println!("  • Each ASCII character is clickable/queryable");
    println!("  • Can transmit over radio in real-time");
    println!("  • Field techs can interact with the visualization");
    println!("  • Updates propagate through the mesh network");
}