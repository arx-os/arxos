#!/usr/bin/env rust
//! ArxOS Art - High-quality ASCII art renderer
//! 
//! Creates atmospheric, detailed ASCII scenes like Dwarf Fortress, Cogmind, etc.

use arxos_core::arxobject::{ArxObject, object_types};
use std::fs::File;
use std::io::{BufReader, BufRead};
use std::env;
use std::collections::HashMap;

// Rich ASCII palette organized by visual weight
const BLOCKS: &str = "█▓▒░";
const SHADES: &str = "▓▒░·. ";  
const LINES: &str = "═║╔╗╚╝├┤┬┴┼─│";
const DOTS: &str = "●◉◎○◌◯⬤⬡⬢";
const ANGLES: &str = "╱╲╳✕✖✗⨯⨰";

struct ArtRenderer {
    width: usize,
    height: usize,
}

impl ArtRenderer {
    fn new(width: usize, height: usize) -> Self {
        Self { width, height }
    }
    
    fn render(&self, objects: &[ArxObject]) -> String {
        // Create density map
        let mut density_map = vec![vec![0.0f32; self.width]; self.height];
        let mut type_map = vec![vec![0u8; self.width]; self.height];
        
        // Find bounds
        let (mut min_x, mut max_x) = (i16::MAX, i16::MIN);
        let (mut min_y, mut max_y) = (i16::MAX, i16::MIN);
        let (mut min_z, mut max_z) = (i16::MAX, i16::MIN);
        
        for obj in objects {
            min_x = min_x.min(obj.x);
            max_x = max_x.max(obj.x);
            min_y = min_y.min(obj.y);
            max_y = max_y.max(obj.y);
            min_z = min_z.min(obj.z);
            max_z = max_z.max(obj.z);
        }
        
        // Map objects to screen with multi-layer rendering
        for obj in objects {
            // Project to 2D with depth
            let x_norm = if max_x > min_x {
                ((obj.x - min_x) as f32 / (max_x - min_x) as f32 * (self.width - 1) as f32) as usize
            } else { self.width / 2 };
            
            let y_norm = if max_y > min_y {
                ((obj.y - min_y) as f32 / (max_y - min_y) as f32 * (self.height - 1) as f32) as usize
            } else { self.height / 2 };
            
            // Calculate depth influence
            let depth = if max_z > min_z {
                (obj.z - min_z) as f32 / (max_z - min_z) as f32
            } else { 0.5 };
            
            // Weight by object type and depth
            let weight = match obj.object_type {
                t if t == object_types::WALL => 10.0 * (1.0 - depth * 0.5),
                t if t == object_types::FLOOR => 2.0,
                t if t == object_types::CEILING => 3.0,
                t if t == object_types::COLUMN => 8.0 * (1.0 - depth * 0.3),
                _ => 5.0,
            };
            
            // Apply to neighboring pixels for thickness
            for dy in 0..=1 {
                for dx in 0..=1 {
                    let px = (x_norm + dx).min(self.width - 1);
                    let py = (y_norm + dy).min(self.height - 1);
                    density_map[py][px] += weight;
                    if density_map[py][px] > 5.0 {
                        type_map[py][px] = obj.object_type;
                    }
                }
            }
        }
        
        // Normalize density
        let max_density = density_map.iter()
            .flat_map(|row| row.iter())
            .fold(0.0f32, |max, &val| max.max(val));
        
        // Convert to ASCII with pattern recognition
        let mut output = vec![vec![' '; self.width]; self.height];
        
        for y in 0..self.height {
            for x in 0..self.width {
                let density = density_map[y][x] / max_density.max(1.0);
                let obj_type = type_map[y][x];
                
                // Check neighbors for edge detection
                let is_edge = self.is_edge(&density_map, x, y, max_density);
                let (is_horiz, is_vert, is_corner) = self.check_orientation(&density_map, x, y);
                
                output[y][x] = self.select_char(density, obj_type, is_edge, is_horiz, is_vert, is_corner);
            }
        }
        
        // Apply artistic filters
        self.apply_texture_patterns(&mut output, &type_map);
        self.apply_shadows(&mut output, &density_map);
        
        // Convert to string with frame
        let mut result = String::new();
        
        // Top border
        result.push('╔');
        result.push_str(&"═".repeat(self.width));
        result.push('╗');
        result.push('\n');
        
        // Content
        for row in output {
            result.push('║');
            result.extend(row.iter());
            result.push('║');
            result.push('\n');
        }
        
        // Bottom border
        result.push('╚');
        result.push_str(&"═".repeat(self.width));
        result.push('╝');
        
        result
    }
    
    fn is_edge(&self, density_map: &[Vec<f32>], x: usize, y: usize, max_density: f32) -> bool {
        let threshold = 0.3;
        let current = density_map[y][x] / max_density;
        
        if current < 0.1 {
            return false;
        }
        
        // Check all neighbors
        for dy in -1i32..=1 {
            for dx in -1i32..=1 {
                if dx == 0 && dy == 0 { continue; }
                
                let nx = (x as i32 + dx) as usize;
                let ny = (y as i32 + dy) as usize;
                
                if nx < self.width && ny < self.height {
                    let neighbor = density_map[ny][nx] / max_density;
                    if (current - neighbor).abs() > threshold {
                        return true;
                    }
                }
            }
        }
        false
    }
    
    fn check_orientation(&self, density_map: &[Vec<f32>], x: usize, y: usize) -> (bool, bool, bool) {
        let mut horiz = false;
        let mut vert = false;
        
        // Check horizontal
        if x > 0 && x < self.width - 1 {
            horiz = density_map[y][x-1] > 0.0 && density_map[y][x+1] > 0.0;
        }
        
        // Check vertical
        if y > 0 && y < self.height - 1 {
            vert = density_map[y-1][x] > 0.0 && density_map[y+1][x] > 0.0;
        }
        
        (horiz, vert, horiz && vert)
    }
    
    fn select_char(&self, density: f32, obj_type: u8, is_edge: bool, 
                   is_horiz: bool, is_vert: bool, is_corner: bool) -> char {
        // Special handling for edges and corners
        if is_edge {
            if is_corner {
                return '┼';
            } else if is_horiz && !is_vert {
                return '─';
            } else if is_vert && !is_horiz {
                return '│';
            }
        }
        
        // Object-specific rendering
        match obj_type {
            t if t == object_types::WALL => {
                if density > 0.9 { '█' }
                else if density > 0.7 { '▓' }
                else if density > 0.5 { '▒' }
                else if density > 0.3 { '░' }
                else if density > 0.1 { '·' }
                else { ' ' }
            },
            t if t == object_types::FLOOR => {
                if density > 0.7 { '=' }
                else if density > 0.4 { '─' }
                else if density > 0.2 { '-' }
                else if density > 0.1 { '.' }
                else { ' ' }
            },
            t if t == object_types::CEILING => {
                if density > 0.7 { '▀' }
                else if density > 0.4 { '¯' }
                else if density > 0.2 { '˜' }
                else { ' ' }
            },
            t if t == object_types::COLUMN => {
                if density > 0.8 { '█' }
                else if density > 0.6 { '▓' }
                else if density > 0.4 { '║' }
                else if density > 0.2 { '│' }
                else { '·' }
            },
            _ => {
                // Generic objects
                if density > 0.8 { '▪' }
                else if density > 0.6 { '◾' }
                else if density > 0.4 { '▫' }
                else if density > 0.2 { '◦' }
                else if density > 0.1 { '·' }
                else { ' ' }
            }
        }
    }
    
    fn apply_texture_patterns(&self, output: &mut Vec<Vec<char>>, type_map: &[Vec<u8>]) {
        // Add texture details based on object types
        for y in 1..self.height-1 {
            for x in 1..self.width-1 {
                if output[y][x] == '░' || output[y][x] == '▒' {
                    // Add texture variations
                    let pattern = (x * 7 + y * 13) % 17;
                    if pattern < 3 && type_map[y][x] == object_types::WALL {
                        output[y][x] = ['▒', '░', '·'][pattern];
                    }
                }
            }
        }
    }
    
    fn apply_shadows(&self, output: &mut Vec<Vec<char>>, density_map: &[Vec<f32>]) {
        // Simple shadow casting from upper-left
        for y in 1..self.height {
            for x in 1..self.width {
                if density_map[y-1][x-1] > 10.0 && density_map[y][x] < 1.0 {
                    if output[y][x] == ' ' {
                        output[y][x] = '·';
                    } else if output[y][x] == '·' {
                        output[y][x] = ':';
                    }
                }
            }
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <ply_file>", args[0]);
        std::process::exit(1);
    }
    
    // Load PLY
    let file = File::open(&args[1]).expect("Failed to open PLY");
    let reader = BufReader::new(file);
    let mut points = Vec::new();
    let mut in_header = true;
    
    for line in reader.lines() {
        let line = line.unwrap();
        if in_header {
            if line == "end_header" {
                in_header = false;
            }
            continue;
        }
        
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 3 {
            points.push((
                parts[0].parse::<f32>().unwrap_or(0.0),
                parts[1].parse::<f32>().unwrap_or(0.0),
                parts[2].parse::<f32>().unwrap_or(0.0),
            ));
        }
    }
    
    // Convert to ArxObjects
    let mut voxels: HashMap<(i32, i32, i32), usize> = HashMap::new();
    for (x, y, z) in &points {
        let vx = (x / 0.15) as i32;  // 15cm voxels
        let vy = (y / 0.15) as i32;
        let vz = (z / 0.15) as i32;
        *voxels.entry((vx, vy, vz)).or_insert(0) += 1;
    }
    
    let mut objects = Vec::new();
    for ((vx, vy, vz), density) in voxels {
        let height = vz as f32 * 0.15;
        
        let obj_type = if height < 0.1 {
            object_types::FLOOR
        } else if height > 2.4 {
            object_types::CEILING
        } else if density > 40 {
            object_types::WALL
        } else if density > 20 {
            object_types::COLUMN
        } else if density > 5 {
            object_types::GENERIC
        } else {
            continue;
        };
        
        objects.push(ArxObject::new(
            0x0001,
            obj_type,
            (vx as f32 * 150.0) as i16,
            (vy as f32 * 150.0) as i16,
            (vz as f32 * 150.0) as i16,
        ));
    }
    
    println!("╔═══════════════════════════════════════════════════════════════════════════════════════╗");
    println!("║ ArxOS ASCII Art Renderer                                                              ║");
    println!("║ {} points → {} ArxObjects                                                    ║", 
             points.len(), objects.len());
    println!("╚═══════════════════════════════════════════════════════════════════════════════════════╝");
    println!();
    
    let renderer = ArtRenderer::new(88, 30);
    let art = renderer.render(&objects);
    println!("{}", art);
    
    println!("\n Legend: █▓▒░ = Walls | ─═ = Floor | ▀¯ = Ceiling | ┼│─ = Edges");
    println!(" ArxObjects ready for RF mesh: {} bytes", objects.len() * 13);
}