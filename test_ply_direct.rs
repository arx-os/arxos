#!/usr/bin/env rust
//! Direct test of PLY to ASCII art pipeline
//! Compile: rustc test_ply_direct.rs
//! Run: ./test_ply_direct

use std::fs::File;
use std::io::{BufRead, BufReader};
use std::collections::HashMap;

const DENSITY_PALETTE: [char; 16] = [
    ' ', '.', ':', '-', '=', '+', '*', 'o',
    'O', '#', '█', '▓', '▒', '░', '▀', '■'
];

fn main() {
    println!("\n╔════════════════════════════════════════════════════════════╗");
    println!("║  🎨 ArxOS Direct PLY → ASCII Art Test                      ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");
    
    let ply_path = "test_data/Untitled_Scan_18_44_21.ply";
    
    match process_ply_to_ascii(ply_path) {
        Ok(ascii_art) => {
            println!("{}", ascii_art);
            println!("\n✨ Successfully rendered your LiDAR scan as ASCII art!");
        }
        Err(e) => {
            println!("❌ Error: {}", e);
        }
    }
}

fn process_ply_to_ascii(file_path: &str) -> Result<String, String> {
    // Read PLY file
    println!("📁 Loading PLY: {}", file_path);
    let points = read_ply_points(file_path)?;
    println!("  ✓ Loaded {} points", points.len());
    
    if points.is_empty() {
        return Err("No points found in PLY file".to_string());
    }
    
    // Find bounds
    let (min, max) = find_bounds(&points);
    println!("  ✓ Bounds: ({:.1}, {:.1}, {:.1}) to ({:.1}, {:.1}, {:.1})",
        min.0, min.1, min.2, max.0, max.1, max.2);
    
    // Create pixel grid (top-down view)
    let width = 120;
    let height = 40;
    let mut grid = vec![vec![0.0f32; width]; height];
    
    // Map points to grid
    println!("🔄 Converting to pixel art...");
    for point in &points {
        // Normalize to 0-1 range
        let nx = (point.0 - min.0) / (max.0 - min.0);
        let ny = (point.1 - min.1) / (max.1 - min.1);
        
        // Map to grid coordinates
        let gx = (nx * (width - 1) as f32) as usize;
        let gy = (ny * (height - 1) as f32) as usize;
        
        if gx < width && gy < height {
            grid[gy][gx] += 1.0;
        }
    }
    
    // Normalize density
    let max_density = grid.iter()
        .flat_map(|row| row.iter())
        .fold(0.0f32, |a, &b| a.max(b));
    
    if max_density > 0.0 {
        for row in &mut grid {
            for cell in row {
                *cell /= max_density;
            }
        }
    }
    
    // Convert to ASCII
    let mut output = String::new();
    
    // Top border
    output.push_str("╔");
    for _ in 0..width {
        output.push('═');
    }
    output.push_str("╗\n");
    
    // Grid
    for row in &grid {
        output.push('║');
        for &density in row {
            let idx = (density * 15.0) as usize;
            output.push(DENSITY_PALETTE[idx.min(15)]);
        }
        output.push_str("║\n");
    }
    
    // Bottom border
    output.push_str("╚");
    for _ in 0..width {
        output.push('═');
    }
    output.push_str("╝\n");
    
    // Stats
    output.push_str(&format!("\n📊 Compression: {} points → {} chars ({:.0}:1)",
        points.len(), width * height, points.len() as f32 / (width * height) as f32));
    
    Ok(output)
}

fn read_ply_points(file_path: &str) -> Result<Vec<(f32, f32, f32)>, String> {
    let file = File::open(file_path)
        .map_err(|e| format!("Cannot open file: {}", e))?;
    
    let reader = BufReader::new(file);
    let mut points = Vec::new();
    let mut in_data = false;
    let mut vertex_count = 0;
    
    for line in reader.lines() {
        let line = line.map_err(|e| format!("Read error: {}", e))?;
        let line = line.trim();
        
        if !in_data {
            if line.starts_with("element vertex") {
                vertex_count = line.split_whitespace()
                    .nth(2)
                    .and_then(|s| s.parse::<usize>().ok())
                    .unwrap_or(0);
            } else if line == "end_header" {
                in_data = true;
                println!("  ✓ Header parsed, expecting {} vertices", vertex_count);
            }
        } else {
            // Parse vertex data
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 3 {
                if let (Ok(x), Ok(y), Ok(z)) = (
                    parts[0].parse::<f32>(),
                    parts[1].parse::<f32>(),
                    parts[2].parse::<f32>()
                ) {
                    points.push((x, y, z));
                    
                    // Progress indicator
                    if points.len() % 10000 == 0 {
                        print!("  Reading: {} points...\r", points.len());
                    }
                }
            }
            
            // Stop if we've read expected vertices
            if vertex_count > 0 && points.len() >= vertex_count {
                break;
            }
        }
    }
    
    Ok(points)
}

fn find_bounds(points: &[(f32, f32, f32)]) -> ((f32, f32, f32), (f32, f32, f32)) {
    let mut min = (f32::MAX, f32::MAX, f32::MAX);
    let mut max = (f32::MIN, f32::MIN, f32::MIN);
    
    for &(x, y, z) in points {
        min.0 = min.0.min(x);
        min.1 = min.1.min(y);
        min.2 = min.2.min(z);
        max.0 = max.0.max(x);
        max.1 = max.1.max(y);
        max.2 = max.2.max(z);
    }
    
    (min, max)
}