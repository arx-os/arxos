#!/usr/bin/env rust-script
//! Test the aesthetic pipeline with real LiDAR scan
//! 
//! Run with: rustc --edition 2021 test_aesthetic_scan.rs && ./test_aesthetic_scan

use std::path::Path;

// Since we can't directly import from arxos_core in a standalone script,
// let's create a simple test that can be run as an example

fn main() {
    println!("\n╔════════════════════════════════════════════════════════════╗");
    println!("║  ArxOS Aesthetic Pipeline Test                              ║");
    println!("║  Processing: Untitled_Scan_18_44_21.ply                     ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");
    
    let ply_path = "/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply";
    
    // Check if file exists
    if !Path::new(ply_path).exists() {
        println!("❌ PLY file not found at: {}", ply_path);
        println!("\nPlease ensure the file is at the expected location.");
        return;
    }
    
    println!("✅ Found PLY file");
    println!("\nTo process this file through the aesthetic pipeline:");
    println!("\n1. Copy the PLY file to the arxos project:");
    println!("   cp {} ./test_data/scan.ply", ply_path);
    println!("\n2. Run the aesthetic example:");
    println!("   cargo run --example aesthetic_scan");
    println!("\nThis will produce beautiful ASCII art from your LiDAR scan!");
}