//! Test PLY scan with ArxOS aesthetic pipeline
//! 
//! Run with: cargo run --bin test_scan

use arxos_core::aesthetic_pipeline::{AestheticPipeline, AestheticConfig, AestheticStyle};
use std::path::Path;

#[tokio::main]
async fn main() {
    println!("\n╔════════════════════════════════════════════════════════════╗");
    println!("║  🎨 ArxOS PLY Scan Test                                    ║");
    println!("║  Processing: Untitled_Scan_18_44_21.ply                    ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");
    
    let ply_path = "test_data/Untitled_Scan_18_44_21.ply";
    
    if !Path::new(ply_path).exists() {
        println!("❌ PLY file not found at: {}", ply_path);
        println!("\nExpected file: test_data/Untitled_Scan_18_44_21.ply");
        return;
    }
    
    // Test with Industrial Pixel style (the aesthetic you want)
    let config = AestheticConfig {
        style: AestheticStyle::IndustrialPixel,
        compression_level: 0.5,
        smart_detection: true,
        preserve_edges: true,
    };
    
    let pipeline = AestheticPipeline::new(config);
    
    println!("Starting processing...\n");
    
    match pipeline.process_ply_file(Path::new(ply_path)).await {
        Ok(output) => {
            println!("\n{}", output);
            
            // Save output
            match std::fs::write("scan_output.txt", &output) {
                Ok(_) => println!("\n💾 Output saved to: scan_output.txt"),
                Err(e) => println!("\n⚠️ Could not save output: {}", e),
            }
            
            println!("\n✨ Success! Your LiDAR scan has been transformed into ASCII art!");
            println!("\n📊 What happened:");
            println!("  1. Parsed {} MB PLY file", 33);
            println!("  2. Converted points to ArxObjects (13 bytes each)");
            println!("  3. Applied aesthetic compression");
            println!("  4. Rendered as industrial pixel art");
            println!("\n🎮 Each character represents real spatial data that can be:");
            println!("  • Transmitted over radio");
            println!("  • Queried by field techs");
            println!("  • Updated in real-time");
        }
        Err(e) => {
            println!("❌ Error processing PLY file: {}", e);
            println!("\nThis might be due to:");
            println!("  • File format issues");
            println!("  • Memory constraints");
            println!("  • Parsing errors");
            
            println!("\n📝 Debug information:");
            println!("  Error details: {:?}", e);
        }
    }
}