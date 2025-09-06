#!/usr/bin/env rust
//! ArxOS Cinema - Cinematic ASCII renderer with proper shading and depth
//! 
//! Inspired by games like Stone Story RPG, Caves of Qud, and Cogmind
//! This achieves photorealistic ASCII through density mapping and dithering

use arxos_core::arxobject::{ArxObject, object_types};
use std::fs::File;
use std::io::{BufReader, BufRead};
use std::env;
use std::collections::HashMap;
use std::f32::consts::PI;

// Advanced ASCII palette with multiple shading levels
// From darkest to lightest, for different materials
mod palettes {
    pub const SOLID: &[char] = &['█', '▓', '▒', '░', '▪', '·', '•', '°', '∙', '.', ' '];
    pub const METAL: &[char] = &['█', '▓', '▒', '▄', '▀', '═', '─', '-', '·', '.', ' '];
    pub const STONE: &[char] = &['█', '▓', '▒', '░', '▫', '□', '▢', '⬚', '◦', '·', ' '];
    pub const WOOD: &[char] = &['█', '▓', '▒', '░', '≡', '≈', '~', '-', '·', '.', ' '];
    pub const GLASS: &[char] = &['▓', '▒', '░', '◊', '◈', '◇', '◆', '·', '°', '.', ' '];
    
    // Dithering patterns for smooth gradients
    pub const DITHER_BAYER_4X4: [[f32; 4]; 4] = [
        [0.0,   8.0,  2.0, 10.0],
        [12.0,  4.0, 14.0,  6.0],
        [3.0,  11.0,  1.0,  9.0],
        [15.0,  7.0, 13.0,  5.0],
    ];
}

// Material properties for different ArxObject types
#[derive(Clone, Copy)]
struct Material {
    palette: &'static [char],
    reflectivity: f32,
    roughness: f32,
    ambient_occlusion: f32,
}

impl Material {
    fn for_object_type(obj_type: u8) -> Self {
        match obj_type {
            t if t == object_types::WALL => Material {
                palette: palettes::STONE,
                reflectivity: 0.1,
                roughness: 0.8,
                ambient_occlusion: 0.7,
            },
            t if t == object_types::FLOOR => Material {
                palette: palettes::WOOD,
                reflectivity: 0.3,
                roughness: 0.6,
                ambient_occlusion: 0.5,
            },
            t if t == object_types::CEILING => Material {
                palette: palettes::SOLID,
                reflectivity: 0.2,
                roughness: 0.9,
                ambient_occlusion: 0.8,
            },
            t if t == object_types::WINDOW => Material {
                palette: palettes::GLASS,
                reflectivity: 0.9,
                roughness: 0.1,
                ambient_occlusion: 0.1,
            },
            t if t == object_types::ELECTRICAL_PANEL => Material {
                palette: palettes::METAL,
                reflectivity: 0.7,
                roughness: 0.3,
                ambient_occlusion: 0.4,
            },
            _ => Material {
                palette: palettes::SOLID,
                reflectivity: 0.5,
                roughness: 0.5,
                ambient_occlusion: 0.5,
            }
        }
    }
}

// Ray for casting through the scene
struct Ray {
    origin: [f32; 3],
    direction: [f32; 3],
}

impl Ray {
    fn new(origin: [f32; 3], direction: [f32; 3]) -> Self {
        // Normalize direction
        let len = (direction[0].powi(2) + direction[1].powi(2) + direction[2].powi(2)).sqrt();
        Self {
            origin,
            direction: [
                direction[0] / len,
                direction[1] / len,
                direction[2] / len,
            ],
        }
    }
}

// Advanced cinematic renderer with ray marching
pub struct CinematicRenderer {
    width: usize,
    height: usize,
    frame_buffer: Vec<Vec<char>>,
    depth_buffer: Vec<Vec<f32>>,
    normal_buffer: Vec<Vec<[f32; 3]>>,
    material_buffer: Vec<Vec<Material>>,
    camera_pos: [f32; 3],
    camera_target: [f32; 3],
    fov: f32,
    sun_direction: [f32; 3],
}

impl CinematicRenderer {
    pub fn new(width: usize, height: usize) -> Self {
        let default_material = Material::for_object_type(0xFF);
        Self {
            width,
            height,
            frame_buffer: vec![vec![' '; width]; height],
            depth_buffer: vec![vec![f32::INFINITY; width]; height],
            normal_buffer: vec![vec![[0.0, 0.0, 0.0]; width]; height],
            material_buffer: vec![vec![default_material; width]; height],
            camera_pos: [0.0, -5.0, 2.0],
            camera_target: [0.0, 0.0, 1.0],
            fov: 70.0,
            sun_direction: [-0.3, 0.7, -0.5], // Angled sunlight for dramatic shadows
        }
    }
    
    fn clear(&mut self) {
        for y in 0..self.height {
            for x in 0..self.width {
                self.frame_buffer[y][x] = ' ';
                self.depth_buffer[y][x] = f32::INFINITY;
                self.normal_buffer[y][x] = [0.0, 0.0, 0.0];
            }
        }
    }
    
    // Cast ray and find intersection with voxel grid
    fn cast_ray(&self, ray: &Ray, voxels: &HashMap<(i32, i32, i32), Vec<&ArxObject>>) 
        -> Option<(f32, [f32; 3], Material, [f32; 3])> {
        
        let max_distance = 50.0;
        let step_size = 0.05; // 5cm steps for accuracy
        let mut t = 0.0;
        
        while t < max_distance {
            let pos = [
                ray.origin[0] + ray.direction[0] * t,
                ray.origin[1] + ray.direction[1] * t,
                ray.origin[2] + ray.direction[2] * t,
            ];
            
            // Convert to voxel coordinates
            let vx = (pos[0] / 0.2) as i32;
            let vy = (pos[1] / 0.2) as i32;
            let vz = (pos[2] / 0.2) as i32;
            
            if let Some(objects) = voxels.get(&(vx, vy, vz)) {
                if let Some(first) = objects.first() {
                    // Calculate surface normal (simplified - in reality would use gradient)
                    let normal = self.calculate_normal(pos, voxels);
                    let material = Material::for_object_type(first.object_type);
                    return Some((t, pos, material, normal));
                }
            }
            
            t += step_size;
        }
        
        None
    }
    
    // Calculate surface normal using neighboring voxels
    fn calculate_normal(&self, pos: [f32; 3], voxels: &HashMap<(i32, i32, i32), Vec<&ArxObject>>) -> [f32; 3] {
        let delta = 0.1;
        
        // Sample density around the point
        let dx = self.sample_density([pos[0] + delta, pos[1], pos[2]], voxels) 
               - self.sample_density([pos[0] - delta, pos[1], pos[2]], voxels);
        let dy = self.sample_density([pos[0], pos[1] + delta, pos[2]], voxels)
               - self.sample_density([pos[0], pos[1] - delta, pos[2]], voxels);
        let dz = self.sample_density([pos[0], pos[1], pos[2] + delta], voxels)
               - self.sample_density([pos[0], pos[1], pos[2] - delta], voxels);
        
        // Normalize
        let len = (dx.powi(2) + dy.powi(2) + dz.powi(2)).sqrt().max(0.001);
        [-dx / len, -dy / len, -dz / len]
    }
    
    fn sample_density(&self, pos: [f32; 3], voxels: &HashMap<(i32, i32, i32), Vec<&ArxObject>>) -> f32 {
        let vx = (pos[0] / 0.2) as i32;
        let vy = (pos[1] / 0.2) as i32;
        let vz = (pos[2] / 0.2) as i32;
        
        if voxels.contains_key(&(vx, vy, vz)) {
            1.0
        } else {
            0.0
        }
    }
    
    // Calculate lighting using Phong shading model
    fn calculate_lighting(&self, pos: [f32; 3], normal: [f32; 3], material: Material) -> f32 {
        // Normalize sun direction
        let sun_len = (self.sun_direction[0].powi(2) + 
                      self.sun_direction[1].powi(2) + 
                      self.sun_direction[2].powi(2)).sqrt();
        let sun_dir = [
            self.sun_direction[0] / sun_len,
            self.sun_direction[1] / sun_len,
            self.sun_direction[2] / sun_len,
        ];
        
        // Diffuse lighting (Lambert)
        let n_dot_l = (normal[0] * sun_dir[0] + 
                      normal[1] * sun_dir[1] + 
                      normal[2] * sun_dir[2]).max(0.0);
        
        // View direction
        let view_dir = [
            self.camera_pos[0] - pos[0],
            self.camera_pos[1] - pos[1],
            self.camera_pos[2] - pos[2],
        ];
        let view_len = (view_dir[0].powi(2) + view_dir[1].powi(2) + view_dir[2].powi(2)).sqrt();
        let view_dir = [view_dir[0] / view_len, view_dir[1] / view_len, view_dir[2] / view_len];
        
        // Reflection vector
        let reflect = [
            2.0 * n_dot_l * normal[0] - sun_dir[0],
            2.0 * n_dot_l * normal[1] - sun_dir[1],
            2.0 * n_dot_l * normal[2] - sun_dir[2],
        ];
        
        // Specular lighting (Phong)
        let r_dot_v = (reflect[0] * view_dir[0] + 
                      reflect[1] * view_dir[1] + 
                      reflect[2] * view_dir[2]).max(0.0);
        let specular = r_dot_v.powf(32.0) * material.reflectivity;
        
        // Combine lighting components
        let ambient = 0.2 * material.ambient_occlusion;
        let diffuse = n_dot_l * (1.0 - material.roughness);
        
        (ambient + diffuse + specular).min(1.0)
    }
    
    // Apply dithering for smooth gradients
    fn apply_dithering(&self, x: usize, y: usize, value: f32) -> f32 {
        let dither_threshold = palettes::DITHER_BAYER_4X4[y % 4][x % 4] / 16.0;
        if value > dither_threshold {
            (value * 10.0).ceil() / 10.0
        } else {
            (value * 10.0).floor() / 10.0
        }
    }
    
    pub fn render(&mut self, objects: &[ArxObject]) -> String {
        self.clear();
        
        // Build spatial index
        let mut voxels: HashMap<(i32, i32, i32), Vec<&ArxObject>> = HashMap::new();
        for obj in objects {
            let vx = (obj.x as f32 / 200.0) as i32;
            let vy = (obj.y as f32 / 200.0) as i32;
            let vz = (obj.z as f32 / 200.0) as i32;
            voxels.entry((vx, vy, vz)).or_insert_with(Vec::new).push(obj);
        }
        
        // Ray march for each pixel
        let aspect_ratio = self.width as f32 / self.height as f32;
        let fov_rad = self.fov.to_radians();
        
        for y in 0..self.height {
            for x in 0..self.width {
                // Calculate ray direction
                let screen_x = (2.0 * x as f32 / self.width as f32 - 1.0) * aspect_ratio;
                let screen_y = 1.0 - 2.0 * y as f32 / self.height as f32;
                
                let ray_dir = [
                    screen_x * fov_rad.tan(),
                    1.0,
                    screen_y * fov_rad.tan(),
                ];
                
                let ray = Ray::new(self.camera_pos, ray_dir);
                
                // Cast ray and get intersection
                if let Some((distance, hit_pos, material, normal)) = self.cast_ray(&ray, &voxels) {
                    // Calculate lighting
                    let mut brightness = self.calculate_lighting(hit_pos, normal, material);
                    
                    // Apply fog for atmospheric perspective
                    let fog_factor = (1.0 - (distance / 30.0).min(1.0)).powi(2);
                    brightness *= fog_factor;
                    
                    // Apply dithering
                    brightness = self.apply_dithering(x, y, brightness);
                    
                    // Map brightness to ASCII character
                    let palette_index = ((1.0 - brightness) * (material.palette.len() - 1) as f32) as usize;
                    self.frame_buffer[y][x] = material.palette[palette_index.min(material.palette.len() - 1)];
                    self.depth_buffer[y][x] = distance;
                    self.normal_buffer[y][x] = normal;
                    self.material_buffer[y][x] = material;
                }
            }
        }
        
        // Apply edge detection for extra detail
        self.apply_edge_detection();
        
        // Convert to string
        let mut output = String::new();
        for row in &self.frame_buffer {
            for &ch in row {
                output.push(ch);
            }
            output.push('\n');
        }
        
        output
    }
    
    // Sobel edge detection for enhanced detail
    fn apply_edge_detection(&mut self) {
        let sobel_x = [[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]];
        let sobel_y = [[-1.0, -2.0, -1.0], [0.0, 0.0, 0.0], [1.0, 2.0, 1.0]];
        
        let mut edges = vec![vec![false; self.width]; self.height];
        
        for y in 1..self.height-1 {
            for x in 1..self.width-1 {
                let mut gx = 0.0;
                let mut gy = 0.0;
                
                // Apply Sobel operators
                for dy in 0..3 {
                    for dx in 0..3 {
                        let depth = self.depth_buffer[y + dy - 1][x + dx - 1];
                        if depth < f32::INFINITY {
                            gx += depth * sobel_x[dy][dx];
                            gy += depth * sobel_y[dy][dx];
                        }
                    }
                }
                
                let edge_strength = (gx.powi(2) + gy.powi(2)).sqrt();
                if edge_strength > 0.5 {
                    edges[y][x] = true;
                }
            }
        }
        
        // Apply edges with appropriate characters
        for y in 0..self.height {
            for x in 0..self.width {
                if edges[y][x] && self.frame_buffer[y][x] != ' ' {
                    // Determine edge orientation
                    let is_horizontal = y > 0 && y < self.height - 1 && 
                        edges[y-1][x] && edges[y+1][x];
                    let is_vertical = x > 0 && x < self.width - 1 && 
                        edges[y][x-1] && edges[y][x+1];
                    
                    if is_horizontal && is_vertical {
                        self.frame_buffer[y][x] = '┼';
                    } else if is_horizontal {
                        self.frame_buffer[y][x] = '│';
                    } else if is_vertical {
                        self.frame_buffer[y][x] = '─';
                    } else {
                        self.frame_buffer[y][x] = '·';
                    }
                }
            }
        }
    }
}

fn load_ply(path: &str) -> Vec<ArxObject> {
    let file = File::open(path).expect("Failed to open PLY");
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
    
    // Advanced voxelization with density analysis
    let voxel_size = 0.2;
    let mut voxels: HashMap<(i32, i32, i32), Vec<(f32, f32, f32)>> = HashMap::new();
    
    for (x, y, z) in &points {
        let vx = (x / voxel_size) as i32;
        let vy = (y / voxel_size) as i32;
        let vz = (z / voxel_size) as i32;
        voxels.entry((vx, vy, vz)).or_insert_with(Vec::new).push((*x, *y, *z));
    }
    
    let mut arxobjects = Vec::new();
    for ((vx, vy, vz), points_in_voxel) in voxels {
        let density = points_in_voxel.len();
        
        // Smart object classification based on position and density
        let height = vz as f32 * voxel_size;
        let object_type = if height < 0.1 {
            object_types::FLOOR
        } else if height > 2.5 {
            object_types::CEILING
        } else if density > 50 {
            object_types::WALL
        } else if density > 30 {
            object_types::COLUMN
        } else if density > 10 {
            // Could be furniture, equipment, etc
            if height < 1.0 {
                object_types::GENERIC // Lower objects
            } else if height > 1.5 {
                object_types::ELECTRICAL_PANEL // Wall-mounted
            } else {
                object_types::WINDOW // Mid-height openings
            }
        } else {
            continue; // Skip sparse voxels
        };
        
        arxobjects.push(ArxObject::new(
            0x0001,
            object_type,
            (vx as f32 * voxel_size * 1000.0) as i16,
            (vy as f32 * voxel_size * 1000.0) as i16,
            (vz as f32 * voxel_size * 1000.0) as i16,
        ));
    }
    
    arxobjects
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <ply_file>", args[0]);
        std::process::exit(1);
    }
    
    println!("Loading and processing {}...", args[1]);
    let objects = load_ply(&args[1]);
    println!("Converted to {} ArxObjects", objects.len());
    
    let mut renderer = CinematicRenderer::new(120, 40);
    
    // Cinematic camera positions
    let camera_positions = vec![
        ([0.0, -5.0, 1.5], [0.0, 0.0, 1.0]),  // Eye level
        ([3.0, -3.0, 2.5], [0.0, 0.0, 1.0]),  // Corner view
        ([0.0, -2.0, 3.5], [0.0, 0.0, 0.0]),  // Top-down angle
    ];
    
    for (i, (pos, target)) in camera_positions.iter().enumerate() {
        renderer.camera_pos = *pos;
        renderer.camera_target = *target;
        
        println!("\n╔═══════════════════════════════════════════════════════════════════════════════════════╗");
        println!("║ ArxOS Cinematic Renderer - View {} of {}                                              ║", i + 1, camera_positions.len());
        println!("╚═══════════════════════════════════════════════════════════════════════════════════════╝");
        
        let frame = renderer.render(&objects);
        print!("{}", frame);
        
        println!("Camera: ({:.1}, {:.1}, {:.1}) → ({:.1}, {:.1}, {:.1})",
                 pos[0], pos[1], pos[2], target[0], target[1], target[2]);
        println!("Objects: {} | Voxel size: 20cm | Lighting: Directional", objects.len());
        
        if i < camera_positions.len() - 1 {
            println!("\nPress Enter for next view...");
            let mut input = String::new();
            std::io::stdin().read_line(&mut input).ok();
        }
    }
    
    println!("\n✨ Cinematic rendering complete!");
}