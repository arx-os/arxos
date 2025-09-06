#!/usr/bin/env rust-script
//! Enhanced PLY to ASCII converter with better visualization
//! 
//! Usage: cargo run --example ply_to_ascii_enhanced <ply_file>

use arxos_core::point_cloud_parser::PointCloudParser;
use arxos_core::progressive_renderer::ProgressiveRenderer;
use arxos_core::detail_store::DetailLevel;
use arxos_core::arxobject::{ArxObject, object_types};
use std::env;
use std::collections::HashMap;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <ply_file>", args[0]);
        std::process::exit(1);
    }
    
    let ply_path = &args[1];
    
    // ASCII Art Header
    println!(r#"
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                  ARXOS BUILDING INTELLIGENCE SYSTEM                ║
    ║                     iPhone LiDAR → ASCII Renderer                  ║
    ╚═══════════════════════════════════════════════════════════════════╝
    "#);
    
    println!("📱 Processing iPhone scan: {}", ply_path);
    
    // Parse PLY
    let parser = PointCloudParser::new();
    let point_cloud = parser.parse_ply(ply_path)?;
    println!("📊 Points loaded: {:>8}", format_number(point_cloud.points.len()));
    
    // Convert to ArxObjects
    println!("\n🔄 Converting to ArxObjects...");
    let arxobjects = parser.to_arxobjects(&point_cloud, 0x0001);
    
    // Calculate stats
    let original_size = std::fs::metadata(ply_path)?.len();
    let compressed_size = arxobjects.len() * 13;
    let ratio = original_size as f64 / compressed_size as f64;
    
    println!("✅ Compression achieved: {:.1}:1", ratio);
    println!("   Original:   {:>8} KB", original_size / 1024);
    println!("   Compressed: {:>8} KB", compressed_size / 1024);
    println!("   ArxObjects: {:>8}", format_number(arxobjects.len()));
    
    // 3D Height Map
    println!("\n📏 HEIGHT DISTRIBUTION");
    render_height_distribution(&arxobjects);
    
    // Floor-by-floor rendering
    println!("\n🏢 BUILDING STRUCTURE");
    render_by_floors(&arxobjects);
    
    // Detailed floor plan
    println!("\n📐 FLOOR PLAN (Top View)");
    render_enhanced_floor_plan(&arxobjects);
    
    // Object distribution
    println!("\n📦 OBJECT ANALYSIS");
    print_object_analysis(&arxobjects);
    
    // Sample ArxObject details
    println!("\n🔍 SAMPLE ARXOBJECTS (First 5)");
    let renderer = ProgressiveRenderer::new();
    let detail_level = DetailLevel::default();
    for (i, obj) in arxobjects.iter().take(5).enumerate() {
        println!("\n Object #{}", i + 1);
        println!("  Type: 0x{:02X} ({})", obj.object_type, get_type_name(obj.object_type));
        println!("  Position: ({:.1}m, {:.1}m, {:.1}m)", 
            obj.x as f32 / 1000.0, 
            obj.y as f32 / 1000.0, 
            obj.z as f32 / 1000.0
        );
        let output = renderer.render_object(obj, &detail_level);
        for line in output.lines() {
            println!("  {}", line);
        }
    }
    
    // BILT earnings estimate
    let bilt_earned = arxobjects.len() * 10; // 10 BILT per object
    println!("\n💰 BILT TOKENS EARNED: {}", format_number(bilt_earned));
    
    Ok(())
}

fn render_height_distribution(objects: &[ArxObject]) {
    let mut height_buckets = vec![0; 10]; // 0-10m in 1m buckets
    
    for obj in objects {
        let height_m = (obj.z as f32 / 1000.0).min(9.9);
        let bucket = (height_m as usize).min(9);
        height_buckets[bucket] += 1;
    }
    
    let max_count = *height_buckets.iter().max().unwrap_or(&1);
    
    for (i, count) in height_buckets.iter().enumerate() {
        let bar_width = (count * 40 / max_count).max(1);
        print!("  {}m-{}m: ", i, i + 1);
        print!("{}", "█".repeat(bar_width));
        println!(" {}", count);
    }
}

fn render_by_floors(objects: &[ArxObject]) {
    // Group by approximate floor (every 3 meters)
    let mut floors: HashMap<i32, Vec<&ArxObject>> = HashMap::new();
    
    for obj in objects {
        let floor = (obj.z as f32 / 3000.0) as i32; // 3m per floor
        floors.entry(floor).or_insert_with(Vec::new).push(obj);
    }
    
    let mut floor_nums: Vec<i32> = floors.keys().copied().collect();
    floor_nums.sort();
    
    for floor in floor_nums {
        let count = floors[&floor].len();
        println!("  Floor {}: {} objects", floor, format_number(count));
    }
}

fn render_enhanced_floor_plan(objects: &[ArxObject]) {
    let (min_x, max_x, min_y, max_y) = find_bounds(objects);
    
    const WIDTH: usize = 100;
    const HEIGHT: usize = 30;
    let mut grid = vec![vec![' '; WIDTH]; HEIGHT];
    let mut density = vec![vec![0u32; WIDTH]; HEIGHT];
    
    let x_scale = WIDTH as f32 / (max_x - min_x + 1) as f32;
    let y_scale = HEIGHT as f32 / (max_y - min_y + 1) as f32;
    
    // Calculate density
    for obj in objects {
        let x = ((obj.x - min_x) as f32 * x_scale) as usize;
        let y = ((obj.y - min_y) as f32 * y_scale) as usize;
        
        if x < WIDTH && y < HEIGHT {
            density[y][x] += 1;
        }
    }
    
    // Convert density to characters
    for y in 0..HEIGHT {
        for x in 0..WIDTH {
            grid[y][x] = match density[y][x] {
                0 => ' ',
                1 => '·',
                2..=3 => '∘',
                4..=6 => '○',
                7..=10 => '●',
                11..=20 => '█',
                _ => '▓',
            };
        }
    }
    
    // Draw frame
    println!("  ┌{}┐", "─".repeat(WIDTH));
    for row in grid {
        print!("  │");
        for ch in row {
            print!("{}", ch);
        }
        println!("│");
    }
    println!("  └{}┘", "─".repeat(WIDTH));
    
    // Scale indicator
    let scale_x = (max_x - min_x) as f32 / 1000.0;
    let scale_y = (max_y - min_y) as f32 / 1000.0;
    println!("  Scale: {:.1}m × {:.1}m", scale_x, scale_y);
    println!("  Density: · ∘ ○ ● █ ▓ (low to high)");
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

fn print_object_analysis(objects: &[ArxObject]) {
    let mut type_counts: HashMap<u8, usize> = HashMap::new();
    let mut height_stats = HeightStats::new();
    
    for obj in objects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
        height_stats.add(obj.z);
    }
    
    // Sort by count
    let mut counts: Vec<(u8, usize)> = type_counts.into_iter().collect();
    counts.sort_by_key(|&(_, count)| std::cmp::Reverse(count));
    
    println!("  Object Type Distribution:");
    for (obj_type, count) in counts.iter().take(10) {
        let name = get_type_name(*obj_type);
        let percentage = (*count as f32 / objects.len() as f32) * 100.0;
        println!("    {:20} : {:>6} ({:>5.1}%)", name, format_number(*count), percentage);
    }
    
    println!("\n  Height Statistics:");
    println!("    Min:     {:.2}m", height_stats.min as f32 / 1000.0);
    println!("    Max:     {:.2}m", height_stats.max as f32 / 1000.0);
    println!("    Average: {:.2}m", height_stats.average() / 1000.0);
    println!("    Median:  {:.2}m", height_stats.median() / 1000.0);
}

struct HeightStats {
    values: Vec<u16>,
    min: u16,
    max: u16,
    sum: u64,
}

impl HeightStats {
    fn new() -> Self {
        Self {
            values: Vec::new(),
            min: u16::MAX,
            max: 0,
            sum: 0,
        }
    }
    
    fn add(&mut self, height: u16) {
        self.values.push(height);
        self.min = self.min.min(height);
        self.max = self.max.max(height);
        self.sum += height as u64;
    }
    
    fn average(&self) -> f32 {
        if self.values.is_empty() {
            0.0
        } else {
            self.sum as f32 / self.values.len() as f32
        }
    }
    
    fn median(&mut self) -> f32 {
        if self.values.is_empty() {
            return 0.0;
        }
        self.values.sort_unstable();
        let mid = self.values.len() / 2;
        if self.values.len() % 2 == 0 {
            (self.values[mid - 1] + self.values[mid]) as f32 / 2.0
        } else {
            self.values[mid] as f32
        }
    }
}

fn get_type_name(obj_type: u8) -> &'static str {
    match obj_type {
        0x10 => "Electrical Outlet",
        0x11 => "Light Fixture",
        0x12 => "Light Switch",
        0x20 => "HVAC Vent",
        0x21 => "Thermostat",
        0x30 => "Floor",
        0x31 => "Ceiling",
        0x32 => "Wall",
        0x33 => "Furniture/Equipment",
        0x40 => "Door",
        0x41 => "Window",
        0x50 => "Fire Alarm",
        0x51 => "Smoke Detector",
        0x52 => "Sprinkler",
        0x60 => "Motion Sensor",
        0x61 => "Security Camera",
        _ => "Unknown",
    }
}

fn format_number(n: usize) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, c) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(',');
        }
        result.push(c);
    }
    result.chars().rev().collect()
}