#!/usr/bin/env rust-script
//! Advanced 3D PLY to ASCII converter with video game quality rendering
//! 
//! Usage: cargo run --example ply_to_ascii_3d_fixed <ply_file>

use arxos_core::point_cloud_parser::PointCloudParser;
use arxos_core::arxobject::ArxObject;
use std::env;
use std::collections::HashMap;
use std::f32::consts::PI;

// Extended ASCII gradient for better shading
const ASCII_GRADIENT: &[char] = &[' ', '.', ':', '-', '=', '+', '*', '#', '%', '@'];
const ASCII_GRADIENT_EXTENDED: &[char] = &[
    ' ', '`', '.', '·', ',', ':', ';', '!', '/', '|', '(', ')', 
    '[', ']', '{', '}', '?', '7', 'r', 'x', 'n', 'u', 'v', 'c', 
    'z', 'X', 'Y', 'U', 'J', 'C', 'L', 'Q', '0', 'O', 'Z', 'm', 'W', 'M', '█'
];

// ANSI color codes
const RESET: &str = "\x1b[0m";
const RED: &str = "\x1b[31m";
const GREEN: &str = "\x1b[32m";
const YELLOW: &str = "\x1b[33m";
const BLUE: &str = "\x1b[34m";
const MAGENTA: &str = "\x1b[35m";
const CYAN: &str = "\x1b[36m";
const WHITE: &str = "\x1b[37m";
const BRIGHT_WHITE: &str = "\x1b[97m";

struct Renderer3D {
    width: usize,
    height: usize,
    frame_buffer: Vec<Vec<char>>,
    z_buffer: Vec<Vec<f32>>,
    color_buffer: Vec<Vec<&'static str>>,
}

impl Renderer3D {
    fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            frame_buffer: vec![vec![' '; width]; height],
            z_buffer: vec![vec![f32::MAX; width]; height],
            color_buffer: vec![vec![RESET; width]; height],
        }
    }
    
    fn clear(&mut self) {
        for y in 0..self.height {
            for x in 0..self.width {
                self.frame_buffer[y][x] = ' ';
                self.z_buffer[y][x] = f32::MAX;
                self.color_buffer[y][x] = RESET;
            }
        }
    }
    
    fn render_top_down(&mut self, objects: &[ArxObject]) {
        self.clear();
        
        // Find bounds
        let (min_x, max_x, min_y, max_y, min_z, max_z) = find_bounds_3d(objects);
        
        // Create density map
        let mut density = vec![vec![0u32; self.width]; self.height];
        let mut height_map = vec![vec![0u16; self.width]; self.height];
        
        for obj in objects {
            let x = ((obj.x - min_x) as f32 / (max_x - min_x + 1) as f32 * (self.width - 1) as f32) as usize;
            let y = ((obj.y - min_y) as f32 / (max_y - min_y + 1) as f32 * (self.height - 1) as f32) as usize;
            
            if x < self.width && y < self.height {
                density[y][x] += 1;
                height_map[y][x] = height_map[y][x].max(obj.z);
            }
        }
        
        // Render with shading based on density and height
        for y in 0..self.height {
            for x in 0..self.width {
                if density[y][x] > 0 {
                    // Calculate gradient index based on density
                    let intensity = (density[y][x] as f32).ln().min(ASCII_GRADIENT_EXTENDED.len() as f32 - 1.0);
                    let char_idx = intensity as usize;
                    
                    self.frame_buffer[y][x] = ASCII_GRADIENT_EXTENDED[char_idx];
                    
                    // Color by height
                    let height_normalized = (height_map[y][x] - min_z) as f32 / (max_z - min_z + 1) as f32;
                    self.color_buffer[y][x] = match (height_normalized * 5.0) as i32 {
                        0 => BLUE,
                        1 => CYAN,
                        2 => GREEN,
                        3 => YELLOW,
                        4 => MAGENTA,
                        _ => RED,
                    };
                }
            }
        }
    }
    
    fn render_perspective(&mut self, objects: &[ArxObject]) {
        self.clear();
        
        // Find bounds for scene
        let (min_x, max_x, min_y, max_y, min_z, max_z) = find_bounds_3d(objects);
        let center_x = (min_x + max_x) / 2;
        let center_y = (min_y + max_y) / 2;
        let center_z = (min_z + max_z) / 2;
        
        // Camera parameters
        let cam_distance = ((max_x - min_x).max(max_y - min_y).max(max_z - min_z) * 2) as f32;
        let fov = 60.0 * PI / 180.0;
        
        for obj in objects {
            // Center the object
            let x = (obj.x as i32 - center_x as i32) as f32;
            let y = (obj.y as i32 - center_y as i32) as f32;
            let z = (obj.z as i32 - center_z as i32) as f32;
            
            // Rotate for better view (45 degrees around Y axis)
            let angle = PI / 4.0;
            let rx = x * angle.cos() - y * angle.sin();
            let ry = x * angle.sin() + y * angle.cos();
            let rz = z;
            
            // Move camera back
            let cam_y = ry + cam_distance;
            
            if cam_y > 0.0 {
                // Perspective projection
                let screen_x = (rx / cam_y * (self.width as f32 / (fov.tan() * 2.0)) + self.width as f32 / 2.0) as usize;
                let screen_y = (self.height as f32 / 2.0 - rz / cam_y * (self.height as f32 / (fov.tan() * 2.0))) as usize;
                
                if screen_x < self.width && screen_y < self.height {
                    let depth = cam_y;
                    
                    if depth < self.z_buffer[screen_y][screen_x] {
                        self.z_buffer[screen_y][screen_x] = depth;
                        
                        // Character based on object type and depth
                        let depth_norm = (1.0 - (depth / cam_distance).min(1.0)).max(0.0);
                        let char_idx = (depth_norm * (ASCII_GRADIENT_EXTENDED.len() - 1) as f32) as usize;
                        
                        self.frame_buffer[screen_y][screen_x] = match obj.object_type {
                            0x30 => '.',  // Floor
                            0x31 => '‾',  // Ceiling  
                            0x32 => '█',  // Wall
                            0x33 => '●',  // Furniture
                            _ => ASCII_GRADIENT_EXTENDED[char_idx],
                        };
                        
                        // Color by height
                        let height_norm = (obj.z - min_z) as f32 / (max_z - min_z + 1) as f32;
                        self.color_buffer[screen_y][screen_x] = match (height_norm * 5.0) as i32 {
                            0 => BLUE,
                            1 => CYAN,
                            2 => GREEN,
                            3 => YELLOW,
                            4 => MAGENTA,
                            _ => RED,
                        };
                    }
                }
            }
        }
    }
    
    fn render_isometric(&mut self, objects: &[ArxObject]) {
        self.clear();
        
        // Find bounds
        let (min_x, max_x, min_y, max_y, min_z, max_z) = find_bounds_3d(objects);
        
        // Isometric angles
        let angle = PI / 6.0; // 30 degrees
        
        for obj in objects {
            // Normalize coordinates to 0-1 range
            let x = (obj.x - min_x) as f32 / (max_x - min_x + 1) as f32;
            let y = (obj.y - min_y) as f32 / (max_y - min_y + 1) as f32;
            let z = (obj.z - min_z) as f32 / (max_z - min_z + 1) as f32;
            
            // Isometric projection
            let iso_x = (x - y) * angle.cos();
            let iso_y = (x + y) * angle.sin() - z * 0.5;
            
            // Map to screen
            let screen_x = ((iso_x + 1.0) * self.width as f32 / 2.0) as usize;
            let screen_y = ((iso_y + 0.5) * self.height as f32) as usize;
            
            if screen_x < self.width && screen_y < self.height {
                let depth = x + y + z;
                
                if depth < self.z_buffer[screen_y][screen_x] {
                    self.z_buffer[screen_y][screen_x] = depth;
                    
                    self.frame_buffer[screen_y][screen_x] = match obj.object_type {
                        0x30 => '.',  // Floor
                        0x31 => '=',  // Ceiling
                        0x32 => '#',  // Wall
                        0x33 => 'o',  // Furniture
                        _ => '*',
                    };
                    
                    self.color_buffer[screen_y][screen_x] = match obj.object_type {
                        0x30 => BLUE,
                        0x31 => CYAN,
                        0x32 => WHITE,
                        0x33 => YELLOW,
                        _ => RESET,
                    };
                }
            }
        }
    }
    
    fn display(&self, title: &str) {
        println!("\n{}", title);
        println!("┌{}┐", "─".repeat(self.width));
        
        for y in 0..self.height {
            print!("│");
            for x in 0..self.width {
                print!("{}{}{}", self.color_buffer[y][x], self.frame_buffer[y][x], RESET);
            }
            println!("│");
        }
        
        println!("└{}┘", "─".repeat(self.width));
    }
}

fn find_bounds_3d(objects: &[ArxObject]) -> (u16, u16, u16, u16, u16, u16) {
    let mut min_x = u16::MAX;
    let mut max_x = u16::MIN;
    let mut min_y = u16::MAX;
    let mut max_y = u16::MIN;
    let mut min_z = u16::MAX;
    let mut max_z = u16::MIN;
    
    for obj in objects {
        min_x = min_x.min(obj.x);
        max_x = max_x.max(obj.x);
        min_y = min_y.min(obj.y);
        max_y = max_y.max(obj.y);
        min_z = min_z.min(obj.z);
        max_z = max_z.max(obj.z);
    }
    
    (min_x, max_x, min_y, max_y, min_z, max_z)
}

fn render_cross_section(objects: &[ArxObject]) {
    const WIDTH: usize = 100;
    const HEIGHT: usize = 30;
    
    let (min_x, max_x, min_y, max_y, min_z, max_z) = find_bounds_3d(objects);
    let mid_y = (min_y + max_y) / 2;
    let slice_thickness = 500; // 0.5m
    
    let mut grid = vec![vec![' '; WIDTH]; HEIGHT];
    let mut density = vec![vec![0u32; WIDTH]; HEIGHT];
    
    // Accumulate points in the slice
    for obj in objects {
        if obj.y.abs_diff(mid_y) < slice_thickness {
            let x = ((obj.x - min_x) as f32 / (max_x - min_x + 1) as f32 * (WIDTH - 1) as f32) as usize;
            let z = ((max_z - obj.z) as f32 / (max_z - min_z + 1) as f32 * (HEIGHT - 1) as f32) as usize;
            
            if x < WIDTH && z < HEIGHT {
                density[z][x] += 1;
            }
        }
    }
    
    // Convert density to characters
    for z in 0..HEIGHT {
        for x in 0..WIDTH {
            grid[z][x] = match density[z][x] {
                0 => ' ',
                1 => '·',
                2 => '∘',
                3..=4 => '○',
                5..=7 => '●',
                8..=10 => '█',
                _ => '▓',
            };
        }
    }
    
    println!("\n═══ CROSS-SECTION VIEW ═══");
    println!("┌{}┐", "─".repeat(WIDTH));
    for row in grid {
        print!("│");
        for ch in row {
            print!("{}", ch);
        }
        println!("│");
    }
    println!("└{}┘", "─".repeat(WIDTH));
    println!("Cross-section at Y={:.1}m (slice: ±{:.1}m)", 
        mid_y as f32 / 1000.0, 
        slice_thickness as f32 / 1000.0);
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <ply_file>", args[0]);
        std::process::exit(1);
    }
    
    println!(r#"
    ╔════════════════════════════════════════════════════════════════════╗
    ║           ARXOS 3D ASCII RENDERER - Video Game Quality            ║
    ║                    PLY → Advanced ASCII Art                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    "#);
    
    // Parse PLY
    let parser = PointCloudParser::new();
    let point_cloud = parser.parse_ply(&args[1])?;
    let arxobjects = parser.to_arxobjects(&point_cloud, 0x0001);
    
    println!("🎮 Loaded {} points → {} objects", 
        point_cloud.points.len(), 
        arxobjects.len());
    
    // Get scene info
    let (min_x, max_x, min_y, max_y, min_z, max_z) = find_bounds_3d(&arxobjects);
    println!("📏 Scene bounds: {:.1}m × {:.1}m × {:.1}m", 
        (max_x - min_x) as f32 / 1000.0,
        (max_y - min_y) as f32 / 1000.0,
        (max_z - min_z) as f32 / 1000.0);
    
    // Create renderer
    let mut renderer = Renderer3D::new(100, 30);
    
    // 1. Top-down view with density shading
    renderer.render_top_down(&arxobjects);
    renderer.display("═══ TOP-DOWN VIEW (Density Shaded) ═══");
    
    // 2. Perspective view 
    renderer.render_perspective(&arxobjects);
    renderer.display("═══ PERSPECTIVE VIEW (3D) ═══");
    
    // 3. Isometric view
    renderer.render_isometric(&arxobjects);
    renderer.display("═══ ISOMETRIC VIEW (Game Style) ═══");
    
    // 4. Cross-section
    render_cross_section(&arxobjects);
    
    // Stats
    println!("\n📊 RENDERING STATS");
    println!("  Total Objects: {}", arxobjects.len());
    println!("  Compression:   {:.1}:1", 
        point_cloud.points.len() as f32 / arxobjects.len() as f32);
    
    let mut type_counts: HashMap<u8, usize> = HashMap::new();
    for obj in &arxobjects {
        *type_counts.entry(obj.object_type).or_insert(0) += 1;
    }
    
    println!("\n  Object Types:");
    for (obj_type, count) in type_counts {
        let name = match obj_type {
            0x30 => "Floor",
            0x31 => "Ceiling",
            0x32 => "Wall",
            0x33 => "Furniture",
            _ => "Other",
        };
        println!("    {:12} : {}", name, count);
    }
    
    Ok(())
}