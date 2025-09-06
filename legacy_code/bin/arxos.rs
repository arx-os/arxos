#!/usr/bin/env rust
//! ArxOS - The REAL binary that actually works
//! 
//! This processes actual PLY files into ArxObjects and renders them.
//! No demos. No fake data. Real processing.

use arxos_core::arxobject::{ArxObject, object_types};
use std::fs::File;
use std::io::{BufReader, BufRead};
use std::env;
use std::collections::HashMap;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <path_to.ply>", args[0]);
        std::process::exit(1);
    }
    
    let ply_path = &args[1];
    println!("🏗️ ArxOS - Building Intelligence System");
    println!("Processing: {}", ply_path);
    println!("═══════════════════════════════════════");
    
    // Step 1: Load PLY file
    let file = File::open(ply_path).expect("Failed to open PLY file");
    let reader = BufReader::new(file);
    let mut points = Vec::new();
    let mut in_header = true;
    let mut vertex_count = 0;
    
    for line in reader.lines() {
        let line = line.expect("Failed to read line");
        
        if in_header {
            if line.starts_with("element vertex") {
                vertex_count = line.split_whitespace()
                    .nth(2)
                    .and_then(|s| s.parse::<usize>().ok())
                    .unwrap_or(0);
            }
            if line == "end_header" {
                in_header = false;
                println!("📊 Found {} vertices", vertex_count);
            }
            continue;
        }
        
        // Parse vertex data (x y z [r g b] [nx ny nz])
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 3 {
            let x = parts[0].parse::<f32>().unwrap_or(0.0);
            let y = parts[1].parse::<f32>().unwrap_or(0.0);
            let z = parts[2].parse::<f32>().unwrap_or(0.0);
            points.push((x, y, z));
        }
    }
    
    println!("✅ Loaded {} points", points.len());
    
    // Step 2: Convert to ArxObjects using voxelization
    // Group points into 10cm voxels
    let voxel_size = 0.1; // 10cm = 100mm
    let mut voxels: HashMap<(i32, i32, i32), Vec<(f32, f32, f32)>> = HashMap::new();
    
    for (x, y, z) in &points {
        let vx = (x / voxel_size) as i32;
        let vy = (y / voxel_size) as i32;
        let vz = (z / voxel_size) as i32;
        voxels.entry((vx, vy, vz)).or_insert_with(Vec::new).push((*x, *y, *z));
    }
    
    // Convert voxels to ArxObjects
    let mut arxobjects = Vec::new();
    for ((vx, vy, vz), points_in_voxel) in voxels.iter() {
        // Determine object type based on height and density
        let object_type = if *vz < 5 {
            object_types::FLOOR
        } else if *vz > 25 {
            object_types::CEILING
        } else if points_in_voxel.len() > 50 {
            object_types::WALL
        } else if points_in_voxel.len() > 20 {
            object_types::COLUMN  // Using COLUMN for dense vertical objects
        } else {
            object_types::GENERIC
        };
        
        // Convert to millimeters for ArxObject
        let x_mm = (*vx as f32 * voxel_size * 1000.0) as i16;
        let y_mm = (*vy as f32 * voxel_size * 1000.0) as i16;
        let z_mm = (*vz as f32 * voxel_size * 1000.0) as i16;
        
        let obj = ArxObject::new(
            0x0001, // Building ID
            object_type,
            x_mm,
            y_mm,
            z_mm,
        );
        
        arxobjects.push(obj);
    }
    
    let original_size = points.len() * 12; // 3 floats per point
    let compressed_size = arxobjects.len() * 13; // 13 bytes per ArxObject
    let ratio = original_size as f32 / compressed_size as f32;
    
    println!("🗜️ Compression: {} points → {} ArxObjects", points.len(), arxobjects.len());
    println!("📉 Ratio: {:.1}:1", ratio);
    println!("💾 Size: {} bytes → {} bytes", original_size, compressed_size);
    
    // Step 3: Render as ASCII (simple 2D top-down view)
    println!("\n📺 ASCII Visualization (Top-Down View):");
    println!("═══════════════════════════════════════");
    
    // Find bounds
    let (mut min_x, mut max_x) = (i16::MAX, i16::MIN);
    let (mut min_y, mut max_y) = (i16::MAX, i16::MIN);
    
    for obj in &arxobjects {
        min_x = min_x.min(obj.x);
        max_x = max_x.max(obj.x);
        min_y = min_y.min(obj.y);
        max_y = max_y.max(obj.y);
    }
    
    // Create ASCII grid (80x24)
    let width = 80;
    let height = 24;
    let mut grid = vec![vec![' '; width]; height];
    
    // Map ArxObjects to grid
    for obj in &arxobjects {
        let x_norm = ((obj.x - min_x) as f32 / (max_x - min_x) as f32 * (width - 1) as f32) as usize;
        let y_norm = ((obj.y - min_y) as f32 / (max_y - min_y) as f32 * (height - 1) as f32) as usize;
        
        let symbol = match obj.object_type {
            t if t == object_types::WALL => '█',
            t if t == object_types::FLOOR => '.',
            t if t == object_types::COLUMN => '▓',
            t if t == object_types::DOOR => '┃',
            t if t == object_types::OUTLET => 'o',
            t if t == object_types::CEILING => '═',
            _ => '░',
        };
        
        if x_norm < width && y_norm < height {
            grid[y_norm][x_norm] = symbol;
        }
    }
    
    // Print grid
    for row in grid {
        println!("{}", row.iter().collect::<String>());
    }
    
    // Step 4: Show some actual objects
    println!("\n🔍 Sample ArxObjects (first 10):");
    println!("═══════════════════════════════════════");
    
    for (i, obj) in arxobjects.iter().take(10).enumerate() {
        let type_name = match obj.object_type {
            t if t == object_types::WALL => "WALL",
            t if t == object_types::FLOOR => "FLOOR",
            t if t == object_types::COLUMN => "COLUMN",
            t if t == object_types::CEILING => "CEILING",
            _ => "OBJECT",
        };
        
        println!("  [{}] {} @ ({:.1}, {:.1}, {:.1})m",
            i,
            type_name,
            obj.x as f32 / 1000.0,
            obj.y as f32 / 1000.0,
            obj.z as f32 / 1000.0
        );
    }
    
    // Step 5: Statistics
    println!("\n📊 Object Type Distribution:");
    println!("═══════════════════════════════════════");
    
    let mut type_counts: HashMap<u8, usize> = HashMap::new();
    for obj in &arxobjects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
    }
    
    for (obj_type, count) in type_counts {
        let type_name = match obj_type {
            t if t == object_types::WALL => "WALL",
            t if t == object_types::FLOOR => "FLOOR",
            t if t == object_types::COLUMN => "COLUMN",
            t if t == object_types::CEILING => "CEILING",
            t if t == object_types::OUTLET => "OUTLET",
            _ => "OTHER",
        };
        
        let bar_width = (count * 50 / arxobjects.len()).min(50);
        println!("  {} {}: {} {}",
            count,
            type_name,
            "█".repeat(bar_width),
            format!("({:.1}%)", count as f32 * 100.0 / arxobjects.len() as f32)
        );
    }
    
    // Step 6: Export capability
    println!("\n💾 Export:");
    println!("═══════════════════════════════════════");
    println!("  Total ArxObjects: {}", arxobjects.len());
    println!("  Binary size: {} bytes", arxobjects.len() * 13);
    println!("  Ready for RF mesh transmission");
    
    // Show actual bytes for first object
    if let Some(first) = arxobjects.first() {
        let bytes = first.to_bytes();
        println!("\n  First ArxObject as bytes:");
        println!("  {:02X?}", bytes);
    }
    
    println!("\n✅ Processing complete!");
    println!("🚀 ArxObjects ready for mesh network transmission");
}