#!/usr/bin/env rust-script
//! Quick test of house scan processing
//! ```cargo
//! [dependencies]
//! ```

use std::io::{BufRead, BufReader};
use std::fs::File;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let ply_file = "/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply";
    
    println!("Analyzing house scan: {}", ply_file);
    
    let file = File::open(ply_file)?;
    let mut reader = BufReader::new(file);
    let mut line = String::new();
    
    // Read header
    let mut vertex_count = 0;
    let mut in_header = true;
    let mut line_count = 0;
    
    while in_header && line_count < 100 {
        line.clear();
        reader.read_line(&mut line)?;
        line_count += 1;
        
        let trimmed = line.trim();
        
        if trimmed == "end_header" {
            in_header = false;
            break;
        }
        
        if trimmed.starts_with("element vertex") {
            let parts: Vec<&str> = trimmed.split_whitespace().collect();
            if parts.len() >= 3 {
                vertex_count = parts[2].parse().unwrap_or(0);
            }
        }
        
        println!("{}: {}", line_count, trimmed);
    }
    
    println!("\nPLY File Summary:");
    println!("  Vertices: {}", vertex_count);
    println!("  Header lines: {}", line_count);
    
    // Read first few vertices to get bounds
    let mut min_x = f32::MAX;
    let mut max_x = f32::MIN;
    let mut min_y = f32::MAX;
    let mut max_y = f32::MIN;
    let mut min_z = f32::MAX;
    let mut max_z = f32::MIN;
    
    for i in 0..vertex_count.min(1000) {
        line.clear();
        reader.read_line(&mut line)?;
        
        let parts: Vec<&str> = line.trim().split_whitespace().collect();
        if parts.len() >= 3 {
            if let (Ok(x), Ok(y), Ok(z)) = (
                parts[0].parse::<f32>(),
                parts[1].parse::<f32>(),
                parts[2].parse::<f32>()
            ) {
                min_x = min_x.min(x);
                max_x = max_x.max(x);
                min_y = min_y.min(y);
                max_y = max_y.max(y);
                min_z = min_z.min(z);
                max_z = max_z.max(z);
            }
        }
    }
    
    println!("\nBounds (from first 1000 points):");
    println!("  X: {:.2} to {:.2} (width: {:.2}m)", min_x, max_x, max_x - min_x);
    println!("  Y: {:.2} to {:.2} (depth: {:.2}m)", min_y, max_y, max_y - min_y);
    println!("  Z: {:.2} to {:.2} (height: {:.2}m)", min_z, max_z, max_z - min_z);
    
    Ok(())
}