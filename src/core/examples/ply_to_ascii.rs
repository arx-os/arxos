#!/usr/bin/env rust-script
//! Convert PLY point cloud to ASCII building visualization
//! 
//! Usage: cargo run --example ply_to_ascii <ply_file>

use arxos_core::point_cloud_parser::PointCloudParser;
use arxos_core::progressive_renderer::ProgressiveRenderer;
use arxos_core::detail_store::DetailLevel;
use arxos_core::arxobject::ArxObject;
use std::env;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Get PLY file from command line
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <ply_file>", args[0]);
        std::process::exit(1);
    }
    
    let ply_path = &args[1];
    println!("Processing PLY file: {}", ply_path);
    
    // Initialize parser
    let parser = PointCloudParser::new();
    
    // Parse PLY file
    println!("Parsing point cloud...");
    let point_cloud = parser.parse_ply(ply_path)?;
    println!("  Points: {}", point_cloud.points.len());
    
    // Convert to ArxObjects
    println!("\nConverting to ArxObjects...");
    let arxobjects = parser.to_arxobjects(&point_cloud, 0x0001);
    println!("  ArxObjects created: {}", arxobjects.len());
    
    // Calculate compression ratio
    let original_size = std::fs::metadata(ply_path)?.len();
    let compressed_size = arxobjects.len() * 13; // 13 bytes per ArxObject
    let ratio = original_size as f64 / compressed_size as f64;
    println!("  Compression: {:.1}:1 ({} KB → {} KB)", 
        ratio, 
        original_size / 1024, 
        compressed_size / 1024
    );
    
    // Initialize renderer
    let renderer = ProgressiveRenderer::new();
    
    // Render at different detail levels
    println!("\n=== BASIC RENDERING (Radio View) ===");
    let detail_level = DetailLevel::default();
    for obj in arxobjects.iter().take(10) {  // Show first 10 objects
        let output = renderer.render_object(obj, &detail_level);
        println!("{}", output);
    }
    
    // ASCII floor plan
    println!("\n=== FLOOR PLAN VIEW ===");
    render_floor_plan(&arxobjects);
    
    // Show statistics
    println!("\n=== STATISTICS ===");
    print_statistics(&arxobjects);
    
    Ok(())
}

fn render_floor_plan(objects: &[ArxObject]) {
    // Find bounds
    let (min_x, max_x, min_y, max_y) = find_bounds(objects);
    
    // Create ASCII grid (80x24 characters)
    const WIDTH: usize = 80;
    const HEIGHT: usize = 24;
    let mut grid = vec![vec![' '; WIDTH]; HEIGHT];
    
    // Scale factors
    let x_scale = WIDTH as f32 / (max_x - min_x) as f32;
    let y_scale = HEIGHT as f32 / (max_y - min_y) as f32;
    
    // Place objects on grid
    for obj in objects {
        let x = ((obj.x - min_x) as f32 * x_scale) as usize;
        let y = ((obj.y - min_y) as f32 * y_scale) as usize;
        
        if x < WIDTH && y < HEIGHT {
            grid[y][x] = match obj.object_type {
                0x10 => 'O', // Outlet
                0x11 => 'L', // Light
                0x12 => 'S', // Switch
                0x20 => 'V', // Vent
                0x21 => 'T', // Thermostat
                0x30 => '.', // Floor
                0x31 => '-', // Ceiling
                0x32 => '#', // Wall
                0x40 => 'D', // Door
                0x41 => 'W', // Window
                _ => '*',    // Other
            };
        }
    }
    
    // Add border and print
    println!("┌{}┐", "─".repeat(WIDTH));
    for row in grid {
        print!("│");
        for ch in row {
            print!("{}", ch);
        }
        println!("│");
    }
    println!("└{}┘", "─".repeat(WIDTH));
    
    // Legend
    println!("\nLegend:");
    println!("  O=Outlet  L=Light  S=Switch  V=Vent  T=Thermostat");
    println!("  #=Wall    .=Floor  -=Ceiling D=Door  W=Window");
}

fn find_bounds(objects: &[ArxObject]) -> (u16, u16, u16, u16) {
    let mut min_x = u16::MAX;
    let mut max_x = u16::MIN;
    let mut min_y = u16::MAX;
    let mut max_y = u16::MIN;
    
    for obj in objects {
        min_x = min_x.min(obj.x);
        max_x = max_x.max(obj.x);
        min_y = min_y.min(obj.y);
        max_y = max_y.max(obj.y);
    }
    
    (min_x, max_x, min_y, max_y)
}

fn print_statistics(objects: &[ArxObject]) {
    use std::collections::HashMap;
    
    let mut type_counts = HashMap::new();
    let mut total_z = 0u32;
    
    for obj in objects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
        total_z += obj.z as u32;
    }
    
    println!("Object Types:");
    for (obj_type, count) in type_counts {
        let name = match obj_type {
            0x10 => "Electrical Outlet",
            0x11 => "Light Fixture",
            0x12 => "Light Switch",
            0x20 => "HVAC Vent",
            0x21 => "Thermostat",
            0x30 => "Floor",
            0x31 => "Ceiling",
            0x32 => "Wall",
            0x33 => "Furniture",
            0x40 => "Door",
            0x41 => "Window",
            _ => "Unknown",
        };
        println!("  {:20} : {}", name, count);
    }
    
    let avg_height = total_z / objects.len() as u32;
    println!("\nAverage Height: {} mm ({:.1} m)", avg_height, avg_height as f32 / 1000.0);
}