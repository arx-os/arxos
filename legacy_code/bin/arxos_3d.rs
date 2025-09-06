#!/usr/bin/env rust
//! ArxOS 3D - Terminal-based 3D building explorer
//! 
//! Inspired by ASCIIcker - renders ArxObjects in 3D ASCII perspective

use arxos_core::arxobject::{ArxObject, object_types};
use std::fs::File;
use std::io::{BufReader, BufRead, stdin, stdout, Write};
use std::env;
use std::collections::HashMap;
use crossterm::{
    terminal::{Clear, ClearType},
    cursor::{Hide, Show, MoveTo},
    event::{read, Event, KeyCode},
    execute,
    style::{Color, Print, SetForegroundColor, ResetColor},
};

// Camera for 3D navigation
struct Camera {
    x: f32,
    y: f32, 
    z: f32,
    yaw: f32,   // Horizontal rotation
    pitch: f32, // Vertical rotation
    fov: f32,
}

impl Camera {
    fn new() -> Self {
        Self {
            x: 0.0,
            y: 0.0,
            z: 1.5, // Eye level
            yaw: 0.0,
            pitch: 0.0,
            fov: 90.0,
        }
    }
    
    fn move_forward(&mut self, amount: f32) {
        self.x += amount * self.yaw.cos();
        self.y += amount * self.yaw.sin();
    }
    
    fn move_right(&mut self, amount: f32) {
        self.x += amount * (self.yaw - std::f32::consts::PI / 2.0).cos();
        self.y += amount * (self.yaw - std::f32::consts::PI / 2.0).sin();
    }
    
    fn turn(&mut self, yaw_delta: f32) {
        self.yaw += yaw_delta;
    }
    
    fn look_up_down(&mut self, pitch_delta: f32) {
        self.pitch = (self.pitch + pitch_delta).clamp(-1.5, 1.5);
    }
}

// 3D renderer using ASCII depth cues
struct Ascii3DRenderer {
    width: usize,
    height: usize,
    depth_buffer: Vec<Vec<f32>>,
    frame_buffer: Vec<Vec<char>>,
    camera: Camera,
}

impl Ascii3DRenderer {
    fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            depth_buffer: vec![vec![f32::MAX; width]; height],
            frame_buffer: vec![vec![' '; width]; height],
            camera: Camera::new(),
        }
    }
    
    fn clear(&mut self) {
        self.depth_buffer = vec![vec![f32::MAX; self.width]; self.height];
        self.frame_buffer = vec![vec![' '; self.width]; self.height];
    }
    
    fn project_point(&self, world_x: f32, world_y: f32, world_z: f32) -> Option<(usize, usize, f32)> {
        // Transform to camera space
        let dx = world_x - self.camera.x;
        let dy = world_y - self.camera.y;
        let dz = world_z - self.camera.z;
        
        // Rotate by camera yaw
        let cos_yaw = self.camera.yaw.cos();
        let sin_yaw = self.camera.yaw.sin();
        let view_x = dx * cos_yaw + dy * sin_yaw;
        let view_y = -dx * sin_yaw + dy * cos_yaw;
        let view_z = dz;
        
        // Don't render behind camera
        if view_y < 0.1 {
            return None;
        }
        
        // Apply pitch rotation
        let cos_pitch = self.camera.pitch.cos();
        let sin_pitch = self.camera.pitch.sin();
        let final_z = view_z * cos_pitch - view_y * sin_pitch;
        let final_y = view_z * sin_pitch + view_y * cos_pitch;
        
        // Perspective projection
        let aspect = self.width as f32 / self.height as f32;
        let fov_rad = self.camera.fov.to_radians();
        let proj_scale = 1.0 / (fov_rad / 2.0).tan();
        
        let screen_x = (view_x * proj_scale / final_y / aspect + 1.0) * self.width as f32 / 2.0;
        let screen_y = (-final_z * proj_scale / final_y + 1.0) * self.height as f32 / 2.0;
        
        if screen_x >= 0.0 && screen_x < self.width as f32 && 
           screen_y >= 0.0 && screen_y < self.height as f32 {
            Some((screen_x as usize, screen_y as usize, final_y))
        } else {
            None
        }
    }
    
    fn render_arxobject(&mut self, obj: &ArxObject) {
        let world_x = obj.x as f32 / 1000.0;
        let world_y = obj.y as f32 / 1000.0;
        let world_z = obj.z as f32 / 1000.0;
        
        if let Some((x, y, depth)) = self.project_point(world_x, world_y, world_z) {
            if depth < self.depth_buffer[y][x] {
                self.depth_buffer[y][x] = depth;
                
                // Choose character based on object type and distance
                let char = match obj.object_type {
                    t if t == object_types::WALL => {
                        if depth < 2.0 { '█' }
                        else if depth < 5.0 { '▓' }
                        else if depth < 10.0 { '▒' }
                        else { '░' }
                    },
                    t if t == object_types::FLOOR => {
                        if depth < 3.0 { '=' }
                        else if depth < 8.0 { '-' }
                        else { '.' }
                    },
                    t if t == object_types::CEILING => {
                        if depth < 5.0 { '▀' }
                        else { '¯' }
                    },
                    t if t == object_types::DOOR => '┃',
                    t if t == object_types::COLUMN => {
                        if depth < 5.0 { '█' }
                        else { '│' }
                    },
                    t if t == object_types::OUTLET => 'o',
                    _ => {
                        if depth < 5.0 { '▪' }
                        else { '·' }
                    }
                };
                
                self.frame_buffer[y][x] = char;
            }
        }
    }
    
    fn render_frame(&mut self, objects: &[ArxObject]) -> String {
        self.clear();
        
        // Sort objects by distance for proper rendering order
        let mut sorted_objects: Vec<_> = objects.iter().collect();
        sorted_objects.sort_by(|a, b| {
            let dist_a = ((a.x as f32 - self.camera.x * 1000.0).powi(2) + 
                         (a.y as f32 - self.camera.y * 1000.0).powi(2) + 
                         (a.z as f32 - self.camera.z * 1000.0).powi(2)).sqrt();
            let dist_b = ((b.x as f32 - self.camera.x * 1000.0).powi(2) + 
                         (b.y as f32 - self.camera.y * 1000.0).powi(2) + 
                         (b.z as f32 - self.camera.z * 1000.0).powi(2)).sqrt();
            dist_b.partial_cmp(&dist_a).unwrap()
        });
        
        // Render each object
        for obj in sorted_objects {
            self.render_arxobject(obj);
        }
        
        // Add crosshair
        let center_x = self.width / 2;
        let center_y = self.height / 2;
        if center_y > 0 && center_y < self.height && center_x > 0 && center_x < self.width {
            self.frame_buffer[center_y][center_x] = '+';
        }
        
        // Convert to string with border
        let mut output = String::new();
        output.push_str(&"═".repeat(self.width + 2));
        output.push('\n');
        
        for row in &self.frame_buffer {
            output.push('║');
            output.extend(row.iter());
            output.push('║');
            output.push('\n');
        }
        
        output.push_str(&"═".repeat(self.width + 2));
        output
    }
}

fn load_ply_to_arxobjects(path: &str) -> Vec<ArxObject> {
    let file = File::open(path).expect("Failed to open PLY file");
    let reader = BufReader::new(file);
    let mut points = Vec::new();
    let mut in_header = true;
    
    for line in reader.lines() {
        let line = line.expect("Failed to read line");
        
        if in_header {
            if line == "end_header" {
                in_header = false;
            }
            continue;
        }
        
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 3 {
            let x = parts[0].parse::<f32>().unwrap_or(0.0);
            let y = parts[1].parse::<f32>().unwrap_or(0.0);
            let z = parts[2].parse::<f32>().unwrap_or(0.0);
            points.push((x, y, z));
        }
    }
    
    // Voxelize to ArxObjects
    let voxel_size = 0.2; // 20cm voxels for better detail
    let mut voxels: HashMap<(i32, i32, i32), Vec<(f32, f32, f32)>> = HashMap::new();
    
    for (x, y, z) in &points {
        let vx = (x / voxel_size) as i32;
        let vy = (y / voxel_size) as i32;
        let vz = (z / voxel_size) as i32;
        voxels.entry((vx, vy, vz)).or_insert_with(Vec::new).push((*x, *y, *z));
    }
    
    let mut arxobjects = Vec::new();
    for ((vx, vy, vz), points_in_voxel) in voxels.iter() {
        let density = points_in_voxel.len();
        
        // Better object classification
        let object_type = if *vz < 2 {
            object_types::FLOOR
        } else if *vz > 12 {
            object_types::CEILING
        } else if density > 30 {
            object_types::WALL
        } else if density > 15 {
            object_types::COLUMN
        } else if density > 5 {
            object_types::GENERIC
        } else {
            continue; // Skip very sparse voxels
        };
        
        let x_mm = (*vx as f32 * voxel_size * 1000.0) as i16;
        let y_mm = (*vy as f32 * voxel_size * 1000.0) as i16;
        let z_mm = (*vz as f32 * voxel_size * 1000.0) as i16;
        
        arxobjects.push(ArxObject::new(0x0001, object_type, x_mm, y_mm, z_mm));
    }
    
    arxobjects
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <path_to.ply>", args[0]);
        std::process::exit(1);
    }
    
    println!("Loading {}...", args[1]);
    let objects = load_ply_to_arxobjects(&args[1]);
    println!("Loaded {} ArxObjects. Starting 3D explorer...", objects.len());
    std::thread::sleep(std::time::Duration::from_secs(1));
    
    // Initialize terminal
    execute!(stdout(), Clear(ClearType::All), Hide).unwrap();
    
    let mut renderer = Ascii3DRenderer::new(80, 24);
    
    // Find starting position (center of objects)
    if !objects.is_empty() {
        let sum_x: f32 = objects.iter().map(|o| o.x as f32).sum();
        let sum_y: f32 = objects.iter().map(|o| o.y as f32).sum();
        renderer.camera.x = sum_x / objects.len() as f32 / 1000.0;
        renderer.camera.y = sum_y / objects.len() as f32 / 1000.0;
    }
    
    // Main game loop
    loop {
        // Render frame
        execute!(stdout(), MoveTo(0, 0)).unwrap();
        let frame = renderer.render_frame(&objects);
        print!("{}", frame);
        
        // HUD
        println!("\n╔════════════════════════════════════════╗");
        println!("║ ArxOS 3D Building Explorer             ║");
        println!("║ WASD: Move  Q/E: Turn  R/F: Look       ║");
        println!("║ ESC: Exit   Pos: ({:.1},{:.1},{:.1})m        ║",
                 renderer.camera.x, renderer.camera.y, renderer.camera.z);
        println!("╚════════════════════════════════════════╝");
        stdout().flush().unwrap();
        
        // Handle input
        if let Ok(event) = read() {
            if let Event::Key(key_event) = event {
                match key_event.code {
                    KeyCode::Char('w') => renderer.camera.move_forward(0.2),
                    KeyCode::Char('s') => renderer.camera.move_forward(-0.2),
                    KeyCode::Char('a') => renderer.camera.move_right(-0.2),
                    KeyCode::Char('d') => renderer.camera.move_right(0.2),
                    KeyCode::Char('q') => renderer.camera.turn(-0.1),
                    KeyCode::Char('e') => renderer.camera.turn(0.1),
                    KeyCode::Char('r') => renderer.camera.look_up_down(0.1),
                    KeyCode::Char('f') => renderer.camera.look_up_down(-0.1),
                    KeyCode::Char(' ') => renderer.camera.z += 0.2,
                    KeyCode::Char('c') => renderer.camera.z -= 0.2,
                    KeyCode::Esc => break,
                    _ => {}
                }
            }
        }
    }
    
    // Cleanup
    execute!(stdout(), Show, Clear(ClearType::All)).unwrap();
    println!("Thanks for exploring with ArxOS!");
}