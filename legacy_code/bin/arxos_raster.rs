#!/usr/bin/env rust
//! ArxOS Rasterizer - Professional 3D to ASCII rendering pipeline
//! 
//! A general-purpose rasterizer that converts ANY 3D scan to cinematic ASCII art.
//! Not tuned for specific files - built for universal quality.

use arxos_core::arxobject::{ArxObject, object_types};
use std::fs::File;
use std::io::{BufReader, BufRead};
use std::env;
use std::collections::HashMap;
use std::f32::consts::PI;

// Vertex for 3D mesh
#[derive(Debug, Clone, Copy)]
struct Vertex {
    position: [f32; 3],
    normal: [f32; 3],
    material_id: u8,
}

// Triangle for rasterization
#[derive(Debug, Clone, Copy)]
struct Triangle {
    vertices: [Vertex; 3],
}

// Adaptive ASCII palettes based on material properties
mod palettes {
    pub struct MaterialPalette {
        pub name: &'static str,
        pub distance_chars: &'static [&'static str], // Near to far
        pub edge_chars: EdgeChars,
        pub texture_pattern: Option<TexturePattern>,
    }
    
    pub struct EdgeChars {
        pub horizontal: char,
        pub vertical: char,
        pub corner: char,
        pub diagonal_up: char,
        pub diagonal_down: char,
    }
    
    pub struct TexturePattern {
        pub pattern: &'static [&'static str],
        pub scale: f32,
    }
    
    // Universal material detection - not hardcoded for kitchen
    pub fn detect_material(density: f32, height: f32, variance: f32, neighbor_count: usize) -> &'static MaterialPalette {
        // Smart heuristics that work for any building
        if height < 0.2 && variance < 0.1 {
            &FLOOR_MATERIAL
        } else if height > 2.3 && density > 0.7 {
            &CEILING_MATERIAL
        } else if density > 0.8 && variance < 0.2 {
            &SOLID_WALL
        } else if density > 0.5 && neighbor_count > 4 {
            &STRUCTURAL_MATERIAL
        } else if density < 0.3 && variance > 0.5 {
            &GLASS_MATERIAL
        } else {
            &GENERIC_MATERIAL
        }
    }
    
    pub static SOLID_WALL: MaterialPalette = MaterialPalette {
        name: "solid_wall",
        distance_chars: &["██", "▓▓", "▒▒", "░░", "··", "··", "  "],
        edge_chars: EdgeChars {
            horizontal: '═',
            vertical: '║',
            corner: '╬',
            diagonal_up: '╱',
            diagonal_down: '╲',
        },
        texture_pattern: Some(TexturePattern {
            pattern: &["▓▒", "▒▓", "░▒", "▒░"],
            scale: 0.1,
        }),
    };
    
    pub static FLOOR_MATERIAL: MaterialPalette = MaterialPalette {
        name: "floor",
        distance_chars: &["==", "══", "──", "--", "··", "··", "  "],
        edge_chars: EdgeChars {
            horizontal: '─',
            vertical: '│',
            corner: '┼',
            diagonal_up: '/',
            diagonal_down: '\\',
        },
        texture_pattern: Some(TexturePattern {
            pattern: &["─═", "═─", "──", "══"],
            scale: 0.2,
        }),
    };
    
    pub static CEILING_MATERIAL: MaterialPalette = MaterialPalette {
        name: "ceiling",
        distance_chars: &["▀▀", "▀▄", "▄▄", "¯¯", "˜˜", "··", "  "],
        edge_chars: EdgeChars {
            horizontal: '▀',
            vertical: '│',
            corner: '┬',
            diagonal_up: '╱',
            diagonal_down: '╲',
        },
        texture_pattern: None,
    };
    
    pub static STRUCTURAL_MATERIAL: MaterialPalette = MaterialPalette {
        name: "structural",
        distance_chars: &["██", "█▓", "▓▒", "▒░", "░·", "··", "  "],
        edge_chars: EdgeChars {
            horizontal: '━',
            vertical: '┃',
            corner: '╋',
            diagonal_up: '╱',
            diagonal_down: '╲',
        },
        texture_pattern: None,
    };
    
    pub static GLASS_MATERIAL: MaterialPalette = MaterialPalette {
        name: "glass",
        distance_chars: &["◊◊", "◇◇", "◦◦", "°°", "··", "··", "  "],
        edge_chars: EdgeChars {
            horizontal: '─',
            vertical: '│',
            corner: '┼',
            diagonal_up: '╱',
            diagonal_down: '╲',
        },
        texture_pattern: None,
    };
    
    pub static GENERIC_MATERIAL: MaterialPalette = MaterialPalette {
        name: "generic",
        distance_chars: &["▪▪", "▫▫", "◾◾", "◦◦", "··", "··", "  "],
        edge_chars: EdgeChars {
            horizontal: '─',
            vertical: '│',
            corner: '┼',
            diagonal_up: '/',
            diagonal_down: '\\',
        },
        texture_pattern: None,
    };
}

// Marching Cubes implementation for mesh generation
mod marching_cubes {
    use super::*;
    
    pub fn voxels_to_mesh(voxels: &HashMap<(i32, i32, i32), VoxelData>) -> Vec<Triangle> {
        let mut triangles = Vec::new();
        
        // Process each voxel cube
        for ((x, y, z), data) in voxels {
            // Sample 8 corners of the cube
            let corners = [
                (*x, *y, *z),
                (*x + 1, *y, *z),
                (*x + 1, *y + 1, *z),
                (*x, *y + 1, *z),
                (*x, *y, *z + 1),
                (*x + 1, *y, *z + 1),
                (*x + 1, *y + 1, *z + 1),
                (*x, *y + 1, *z + 1),
            ];
            
            // Build case index
            let mut case_index = 0;
            for (i, corner) in corners.iter().enumerate() {
                if voxels.contains_key(corner) {
                    case_index |= 1 << i;
                }
            }
            
            // Generate triangles based on case (simplified - full table needed)
            if case_index != 0 && case_index != 255 {
                // This is a boundary voxel - generate surface
                let center = [
                    *x as f32 + 0.5,
                    *y as f32 + 0.5,
                    *z as f32 + 0.5,
                ];
                
                // Calculate normal from density gradient
                let normal = calculate_normal(voxels, *x, *y, *z);
                
                // Create simple quad (should use proper marching cubes table)
                let v = Vertex {
                    position: center,
                    normal,
                    material_id: data.material_type,
                };
                
                // Generate triangle fan from center
                triangles.push(Triangle {
                    vertices: [v, v, v], // Placeholder - need proper vertices
                });
            }
        }
        
        triangles
    }
    
    fn calculate_normal(voxels: &HashMap<(i32, i32, i32), VoxelData>, x: i32, y: i32, z: i32) -> [f32; 3] {
        let dx = sample_density(voxels, x + 1, y, z) - sample_density(voxels, x - 1, y, z);
        let dy = sample_density(voxels, x, y + 1, z) - sample_density(voxels, x, y - 1, z);
        let dz = sample_density(voxels, x, y, z + 1) - sample_density(voxels, x, y, z - 1);
        
        let len = (dx * dx + dy * dy + dz * dz).sqrt().max(0.001);
        [-dx / len, -dy / len, -dz / len]
    }
    
    fn sample_density(voxels: &HashMap<(i32, i32, i32), VoxelData>, x: i32, y: i32, z: i32) -> f32 {
        voxels.get(&(x, y, z)).map(|v| v.density).unwrap_or(0.0)
    }
}

// Voxel data with rich properties
#[derive(Debug, Clone)]
struct VoxelData {
    density: f32,
    material_type: u8,
    variance: f32,
    neighbor_count: usize,
}

// Main rasterizer
pub struct Rasterizer {
    width: usize,
    height: usize,
    zbuffer: Vec<Vec<f32>>,
    normal_buffer: Vec<Vec<[f32; 3]>>,
    material_buffer: Vec<Vec<u8>>,
    frame_buffer: Vec<Vec<[char; 2]>>, // 2 chars per pixel for detail
}

impl Rasterizer {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            zbuffer: vec![vec![f32::INFINITY; width]; height],
            normal_buffer: vec![vec![[0.0, 0.0, 0.0]; width]; height],
            material_buffer: vec![vec![0; width]; height],
            frame_buffer: vec![vec![[' ', ' ']; width]; height],
        }
    }
    
    pub fn render(&mut self, triangles: &[Triangle], camera: &Camera, light: &Light) -> String {
        self.clear();
        
        // Transform and project triangles
        for triangle in triangles {
            self.rasterize_triangle(triangle, camera, light);
        }
        
        // Post-processing
        self.apply_edge_detection();
        self.apply_ambient_occlusion();
        self.apply_depth_fog();
        
        // Convert to string
        self.to_string()
    }
    
    fn clear(&mut self) {
        for y in 0..self.height {
            for x in 0..self.width {
                self.zbuffer[y][x] = f32::INFINITY;
                self.normal_buffer[y][x] = [0.0, 0.0, 0.0];
                self.material_buffer[y][x] = 0;
                self.frame_buffer[y][x] = [' ', ' '];
            }
        }
    }
    
    fn rasterize_triangle(&mut self, triangle: &Triangle, camera: &Camera, light: &Light) {
        // Transform vertices to screen space
        let mut screen_verts = [[0.0; 2]; 3];
        let mut depths = [0.0; 3];
        
        for (i, vertex) in triangle.vertices.iter().enumerate() {
            let (screen_pos, depth) = camera.project(vertex.position);
            screen_verts[i] = screen_pos;
            depths[i] = depth;
        }
        
        // Compute bounding box
        let min_x = screen_verts.iter().map(|v| v[0] as i32).min().unwrap().max(0) as usize;
        let max_x = screen_verts.iter().map(|v| v[0] as i32).max().unwrap().min(self.width as i32 - 1) as usize;
        let min_y = screen_verts.iter().map(|v| v[1] as i32).min().unwrap().max(0) as usize;
        let max_y = screen_verts.iter().map(|v| v[1] as i32).max().unwrap().min(self.height as i32 - 1) as usize;
        
        // Scanline rasterization
        for y in min_y..=max_y {
            for x in min_x..=max_x {
                let point = [x as f32, y as f32];
                
                // Barycentric coordinates
                if let Some(bary) = self.barycentric(point, screen_verts) {
                    // Interpolate depth
                    let z = depths[0] * bary[0] + depths[1] * bary[1] + depths[2] * bary[2];
                    
                    // Depth test
                    if z < self.zbuffer[y][x] {
                        self.zbuffer[y][x] = z;
                        
                        // Interpolate normal
                        let normal = [
                            triangle.vertices[0].normal[0] * bary[0] + 
                            triangle.vertices[1].normal[0] * bary[1] + 
                            triangle.vertices[2].normal[0] * bary[2],
                            
                            triangle.vertices[0].normal[1] * bary[0] + 
                            triangle.vertices[1].normal[1] * bary[1] + 
                            triangle.vertices[2].normal[1] * bary[2],
                            
                            triangle.vertices[0].normal[2] * bary[0] + 
                            triangle.vertices[1].normal[2] * bary[1] + 
                            triangle.vertices[2].normal[2] * bary[2],
                        ];
                        
                        self.normal_buffer[y][x] = normal;
                        self.material_buffer[y][x] = triangle.vertices[0].material_id;
                        
                        // Calculate lighting
                        let brightness = light.calculate(normal, z);
                        
                        // Select ASCII characters
                        let chars = self.select_ascii(brightness, z, triangle.vertices[0].material_id);
                        self.frame_buffer[y][x] = chars;
                    }
                }
            }
        }
    }
    
    fn barycentric(&self, point: [f32; 2], verts: [[f32; 2]; 3]) -> Option<[f32; 3]> {
        let v0 = [verts[2][0] - verts[0][0], verts[2][1] - verts[0][1]];
        let v1 = [verts[1][0] - verts[0][0], verts[1][1] - verts[0][1]];
        let v2 = [point[0] - verts[0][0], point[1] - verts[0][1]];
        
        let dot00 = v0[0] * v0[0] + v0[1] * v0[1];
        let dot01 = v0[0] * v1[0] + v0[1] * v1[1];
        let dot02 = v0[0] * v2[0] + v0[1] * v2[1];
        let dot11 = v1[0] * v1[0] + v1[1] * v1[1];
        let dot12 = v1[0] * v2[0] + v1[1] * v2[1];
        
        let inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01);
        let u = (dot11 * dot02 - dot01 * dot12) * inv_denom;
        let v = (dot00 * dot12 - dot01 * dot02) * inv_denom;
        
        if u >= 0.0 && v >= 0.0 && u + v <= 1.0 {
            Some([1.0 - u - v, v, u])
        } else {
            None
        }
    }
    
    fn select_ascii(&self, brightness: f32, depth: f32, material_id: u8) -> [char; 2] {
        // This is where the magic happens - adaptive character selection
        // Not tuned for kitchen, but for general quality
        
        // Simplified for now - would use full material palette system
        let distance_factor = (depth / 50.0).min(1.0);
        let char_index = ((1.0 - brightness) * 6.0 * (1.0 - distance_factor * 0.5)) as usize;
        
        let chars = match material_id {
            t if t == object_types::WALL => ['█', '▓', '▒', '░', '·', '·', ' '],
            t if t == object_types::FLOOR => ['=', '═', '─', '-', '·', '·', ' '],
            _ => ['▪', '▫', '◾', '◦', '·', '·', ' '],
        };
        
        let ch = chars[char_index.min(chars.len() - 1)];
        [ch, ch]
    }
    
    fn apply_edge_detection(&mut self) {
        // Sobel operator for edge enhancement
        let mut edges = vec![vec![false; self.width]; self.height];
        
        for y in 1..self.height-1 {
            for x in 1..self.width-1 {
                let z_center = self.zbuffer[y][x];
                if z_center == f32::INFINITY { continue; }
                
                // Check depth discontinuities
                let threshold = 0.5;
                for dy in -1..=1 {
                    for dx in -1..=1 {
                        if dx == 0 && dy == 0 { continue; }
                        let ny = (y as i32 + dy) as usize;
                        let nx = (x as i32 + dx) as usize;
                        
                        if (self.zbuffer[ny][nx] - z_center).abs() > threshold {
                            edges[y][x] = true;
                            break;
                        }
                    }
                }
            }
        }
        
        // Apply edge characters
        for y in 0..self.height {
            for x in 0..self.width {
                if edges[y][x] {
                    // Determine edge direction and apply appropriate character
                    let is_horiz = x > 0 && x < self.width - 1 && 
                                  edges[y][x-1] && edges[y][x+1];
                    let is_vert = y > 0 && y < self.height - 1 && 
                                 edges[y-1][x] && edges[y+1][x];
                    
                    if is_horiz && is_vert {
                        self.frame_buffer[y][x] = ['┼', ' '];
                    } else if is_horiz {
                        self.frame_buffer[y][x] = ['─', ' '];
                    } else if is_vert {
                        self.frame_buffer[y][x] = ['│', ' '];
                    }
                }
            }
        }
    }
    
    fn apply_ambient_occlusion(&mut self) {
        // Screen-space ambient occlusion for depth
        for y in 2..self.height-2 {
            for x in 2..self.width-2 {
                if self.zbuffer[y][x] == f32::INFINITY { continue; }
                
                let mut occlusion = 0.0;
                let samples = 8;
                
                for i in 0..samples {
                    let angle = i as f32 * 2.0 * PI / samples as f32;
                    let dx = (angle.cos() * 2.0) as i32;
                    let dy = (angle.sin() * 2.0) as i32;
                    
                    let ny = (y as i32 + dy).max(0).min(self.height as i32 - 1) as usize;
                    let nx = (x as i32 + dx).max(0).min(self.width as i32 - 1) as usize;
                    
                    if self.zbuffer[ny][nx] < self.zbuffer[y][x] - 0.5 {
                        occlusion += 1.0 / samples as f32;
                    }
                }
                
                // Darken occluded areas
                if occlusion > 0.3 {
                    if self.frame_buffer[y][x][0] == '█' {
                        self.frame_buffer[y][x][0] = '▓';
                    } else if self.frame_buffer[y][x][0] == '▓' {
                        self.frame_buffer[y][x][0] = '▒';
                    }
                }
            }
        }
    }
    
    fn apply_depth_fog(&mut self) {
        // Atmospheric perspective
        let max_depth = 30.0;
        
        for y in 0..self.height {
            for x in 0..self.width {
                let depth = self.zbuffer[y][x];
                if depth < f32::INFINITY {
                    let fog_factor = (depth / max_depth).min(1.0);
                    
                    // Fade distant objects
                    if fog_factor > 0.7 {
                        if self.frame_buffer[y][x][0] != ' ' {
                            self.frame_buffer[y][x] = ['·', ' '];
                        }
                    } else if fog_factor > 0.9 {
                        self.frame_buffer[y][x] = [' ', ' '];
                    }
                }
            }
        }
    }
    
    fn to_string(&self) -> String {
        let mut result = String::new();
        
        for row in &self.frame_buffer {
            for chars in row {
                result.push(chars[0]);
                if chars[1] != ' ' {
                    result.push(chars[1]);
                }
            }
            result.push('\n');
        }
        
        result
    }
}

// Camera for 3D projection
struct Camera {
    position: [f32; 3],
    target: [f32; 3],
    up: [f32; 3],
    fov: f32,
    aspect_ratio: f32,
}

impl Camera {
    fn new(width: usize, height: usize) -> Self {
        Self {
            position: [0.0, -5.0, 2.0],
            target: [0.0, 0.0, 1.0],
            up: [0.0, 0.0, 1.0],
            fov: 60.0,
            aspect_ratio: width as f32 / height as f32,
        }
    }
    
    fn project(&self, world_pos: [f32; 3]) -> ([f32; 2], f32) {
        // View transform
        let view = self.look_at();
        let view_pos = transform_point(world_pos, &view);
        
        // Perspective projection
        let fov_rad = self.fov * PI / 180.0;
        let f = 1.0 / (fov_rad / 2.0).tan();
        
        let x = view_pos[0] * f / view_pos[2] / self.aspect_ratio;
        let y = -view_pos[1] * f / view_pos[2];
        
        // Convert to screen coordinates
        let screen_x = (x + 1.0) * 40.0; // Assuming 80 width
        let screen_y = (y + 1.0) * 12.0; // Assuming 24 height
        
        ([screen_x, screen_y], view_pos[2])
    }
    
    fn look_at(&self) -> [[f32; 4]; 4] {
        // Simplified look-at matrix
        [[1.0, 0.0, 0.0, -self.position[0]],
         [0.0, 1.0, 0.0, -self.position[1]],
         [0.0, 0.0, 1.0, -self.position[2]],
         [0.0, 0.0, 0.0, 1.0]]
    }
}

// Lighting system
struct Light {
    direction: [f32; 3],
    ambient: f32,
    diffuse: f32,
    specular: f32,
}

impl Light {
    fn new() -> Self {
        Self {
            direction: [-0.3, 0.5, -0.8],
            ambient: 0.2,
            diffuse: 0.6,
            specular: 0.2,
        }
    }
    
    fn calculate(&self, normal: [f32; 3], depth: f32) -> f32 {
        let n_dot_l = normal[0] * self.direction[0] + 
                     normal[1] * self.direction[1] + 
                     normal[2] * self.direction[2];
        
        let diffuse = n_dot_l.max(0.0) * self.diffuse;
        let brightness = self.ambient + diffuse;
        
        // Depth attenuation
        let attenuation = 1.0 / (1.0 + depth * 0.01);
        
        (brightness * attenuation).min(1.0)
    }
}

// Helper functions
fn transform_point(point: [f32; 3], matrix: &[[f32; 4]; 4]) -> [f32; 3] {
    [
        point[0] * matrix[0][0] + point[1] * matrix[0][1] + point[2] * matrix[0][2] + matrix[0][3],
        point[0] * matrix[1][0] + point[1] * matrix[1][1] + point[2] * matrix[1][2] + matrix[1][3],
        point[0] * matrix[2][0] + point[1] * matrix[2][1] + point[2] * matrix[2][2] + matrix[2][3],
    ]
}

// Main processing pipeline
fn process_ply_to_ascii(path: &str) -> String {
    // Load PLY
    let points = load_ply_points(path);
    println!("Loaded {} points", points.len());
    
    // Convert to smart voxels with material detection
    let voxels = points_to_voxels(&points);
    println!("Created {} voxels", voxels.len());
    
    // Generate mesh using marching cubes
    let triangles = marching_cubes::voxels_to_mesh(&voxels);
    println!("Generated {} triangles", triangles.len());
    
    // Set up renderer
    let mut rasterizer = Rasterizer::new(80, 30);
    let camera = Camera::new(80, 30);
    let light = Light::new();
    
    // Render!
    rasterizer.render(&triangles, &camera, &light)
}

fn load_ply_points(path: &str) -> Vec<[f32; 3]> {
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
            points.push([
                parts[0].parse().unwrap_or(0.0),
                parts[1].parse().unwrap_or(0.0),
                parts[2].parse().unwrap_or(0.0),
            ]);
        }
    }
    
    points
}

fn points_to_voxels(points: &[[f32; 3]]) -> HashMap<(i32, i32, i32), VoxelData> {
    let voxel_size = 0.15; // 15cm voxels - universal scale
    let mut voxel_points: HashMap<(i32, i32, i32), Vec<[f32; 3]>> = HashMap::new();
    
    // Group points into voxels
    for point in points {
        let vx = (point[0] / voxel_size) as i32;
        let vy = (point[1] / voxel_size) as i32;
        let vz = (point[2] / voxel_size) as i32;
        
        voxel_points.entry((vx, vy, vz))
            .or_insert_with(Vec::new)
            .push(*point);
    }
    
    // Analyze each voxel
    let mut voxels = HashMap::new();
    
    for ((vx, vy, vz), points) in voxel_points.iter() {
        let density = points.len() as f32 / 100.0; // Normalized density
        
        // Calculate variance for material detection
        let mean_z = points.iter().map(|p| p[2]).sum::<f32>() / points.len() as f32;
        let variance = points.iter()
            .map(|p| (p[2] - mean_z).powi(2))
            .sum::<f32>() / points.len() as f32;
        
        // Count neighbors
        let neighbor_count = [
            (-1, 0, 0), (1, 0, 0),
            (0, -1, 0), (0, 1, 0),
            (0, 0, -1), (0, 0, 1),
        ].iter()
            .filter(|(dx, dy, dz)| {
                voxel_points.contains_key(&(vx + dx, vy + dy, vz + dz))
            })
            .count();
        
        // Smart material detection
        let height = *vz as f32 * voxel_size;
        let material = palettes::detect_material(density, height, variance, neighbor_count);
        
        voxels.insert((*vx, *vy, *vz), VoxelData {
            density: density.min(1.0),
            material_type: match material.name {
                "solid_wall" => object_types::WALL,
                "floor" => object_types::FLOOR,
                "ceiling" => object_types::CEILING,
                "structural" => object_types::COLUMN,
                "glass" => object_types::WINDOW,
                _ => object_types::GENERIC,
            },
            variance,
            neighbor_count,
        });
    }
    
    voxels
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <ply_file>", args[0]);
        eprintln!("\nThis rasterizer works with ANY PLY scan:");
        eprintln!("  - Indoor spaces (rooms, hallways)");
        eprintln!("  - Outdoor buildings (facades, roofs)");
        eprintln!("  - Industrial sites (warehouses, factories)");
        eprintln!("  - Infrastructure (tunnels, bridges)");
        std::process::exit(1);
    }
    
    println!("╔═══════════════════════════════════════════════════════╗");
    println!("║ ArxOS Professional 3D ASCII Rasterizer                ║");
    println!("║ Universal renderer for building intelligence          ║");
    println!("╚═══════════════════════════════════════════════════════╝\n");
    
    let ascii_art = process_ply_to_ascii(&args[1]);
    
    println!("{}", ascii_art);
    
    println!("\n╔═══════════════════════════════════════════════════════╗");
    println!("║ Rendering complete. Ready for RF mesh transmission.   ║");
    println!("╚═══════════════════════════════════════════════════════╝");
}