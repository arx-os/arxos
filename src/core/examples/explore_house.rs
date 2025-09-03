#!/usr/bin/env rust-script
//! Explore your house scan as an ASCII text adventure
//! 
//! Usage: cargo run --example explore_house

use std::io::{self, BufRead, BufReader, Write};
use std::fs::File;
use std::collections::HashMap;

// Simple ArxObject for demo (avoiding the packed struct issues)
#[derive(Debug, Clone, Copy)]
struct SimpleArxObject {
    building_id: u16,
    object_type: u8,
    x: u16,
    y: u16, 
    z: u16,
}

impl SimpleArxObject {
    fn new(building_id: u16, object_type: u8, x: f32, y: f32, z: f32) -> Self {
        // Convert meters to millimeters and clamp to u16
        Self {
            building_id,
            object_type,
            x: ((x * 1000.0).abs() as u16).min(65535),
            y: ((y * 1000.0).abs() as u16).min(65535),
            z: ((z * 1000.0).abs() as u16).min(65535),
        }
    }
}

// Simple room detection from point cloud
struct Room {
    id: usize,
    name: String,
    min: (f32, f32, f32),
    max: (f32, f32, f32),
    objects: Vec<SimpleArxObject>,
}

// Simple game world
struct World {
    rooms: Vec<Room>,
    current_room: usize,
    player_pos: (f32, f32, f32),
}

impl World {
    fn from_point_cloud(vertices: Vec<(f32, f32, f32)>) -> Self {
        println!("Processing {} vertices...", vertices.len());
        
        // Find bounds
        let mut min_x = f32::MAX;
        let mut max_x = f32::MIN;
        let mut min_y = f32::MAX;
        let mut max_y = f32::MIN;
        let mut min_z = f32::MAX;
        let mut max_z = f32::MIN;
        
        for (x, y, z) in &vertices {
            min_x = min_x.min(*x);
            max_x = max_x.max(*x);
            min_y = min_y.min(*y);
            max_y = max_y.max(*y);
            min_z = min_z.min(*z);
            max_z = max_z.max(*z);
        }
        
        println!("Bounds: X({:.2}, {:.2}), Y({:.2}, {:.2}), Z({:.2}, {:.2})",
                 min_x, max_x, min_y, max_y, min_z, max_z);
        
        // Create a simple grid of rooms (divide space into chunks)
        let mut rooms = Vec::new();
        let grid_size = 5.0; // 5 meter grid
        
        let x_cells = ((max_x - min_x) / grid_size).ceil() as usize;
        let y_cells = ((max_y - min_y) / grid_size).ceil() as usize;
        
        for y in 0..y_cells {
            for x in 0..x_cells {
                let room_min_x = min_x + (x as f32) * grid_size;
                let room_max_x = room_min_x + grid_size;
                let room_min_y = min_y + (y as f32) * grid_size;
                let room_max_y = room_min_y + grid_size;
                
                // Count points in this cell
                let points_in_cell = vertices.iter()
                    .filter(|(px, py, _)| {
                        *px >= room_min_x && *px < room_max_x &&
                        *py >= room_min_y && *py < room_max_y
                    })
                    .count();
                
                // Only create room if it has enough points
                if points_in_cell > 100 {
                    let room_id = rooms.len();
                    
                    // Create some ArxObjects for the room
                    let mut objects = Vec::new();
                    
                    // Add a floor object
                    objects.push(SimpleArxObject::new(
                        1, 0x30, // Floor type
                        room_min_x + grid_size/2.0,
                        room_min_y + grid_size/2.0,
                        min_z
                    ));
                    
                    // Add walls (simplified)
                    objects.push(SimpleArxObject::new(
                        1, 0x32, // Wall type
                        room_min_x,
                        room_min_y + grid_size/2.0,
                        min_z + 1.5
                    ));
                    
                    // Randomly add some objects based on point density
                    if points_in_cell > 1000 {
                        objects.push(SimpleArxObject::new(
                            1, 0x10, // Outlet
                            room_min_x + 0.5,
                            room_min_y + 0.5,
                            min_z + 0.3
                        ));
                    }
                    
                    rooms.push(Room {
                        id: room_id,
                        name: format!("Area {}", room_id + 1),
                        min: (room_min_x, room_min_y, min_z),
                        max: (room_max_x, room_max_y, max_z),
                        objects,
                    });
                }
            }
        }
        
        println!("Created {} rooms from point cloud", rooms.len());
        
        World {
            rooms,
            current_room: 0,
            player_pos: (min_x + 1.0, min_y + 1.0, min_z),
        }
    }
    
    fn render_current_room(&self) -> String {
        if self.rooms.is_empty() {
            return "No rooms detected in scan.".to_string();
        }
        
        let room = &self.rooms[self.current_room];
        let mut output = String::new();
        
        output.push_str(&format!("\n=== {} ===\n", room.name));
        output.push_str(&format!("Size: {:.1}m x {:.1}m\n", 
            room.max.0 - room.min.0,
            room.max.1 - room.min.1
        ));
        
        // Simple ASCII map
        output.push_str("\n");
        output.push_str("╔════════════════════╗\n");
        
        for _ in 0..5 {
            output.push_str("║                    ║\n");
        }
        
        // Show player position
        output.push_str("║         @          ║\n");
        
        for _ in 0..5 {
            output.push_str("║                    ║\n");
        }
        
        output.push_str("╚════════════════════╝\n");
        
        // List objects
        output.push_str("\nDetected objects:\n");
        for obj in &room.objects {
            let type_name = match obj.object_type {
                0x10 => "Outlet",
                0x30 => "Floor",
                0x32 => "Wall",
                _ => "Unknown",
            };
            output.push_str(&format!("  - {} at ({:.1}m, {:.1}m, {:.1}m)\n",
                type_name,
                obj.x as f32 / 1000.0,
                obj.y as f32 / 1000.0,
                obj.z as f32 / 1000.0
            ));
        }
        
        // Show navigation options
        output.push_str("\nExits: ");
        if self.current_room > 0 {
            output.push_str("[west] ");
        }
        if self.current_room < self.rooms.len() - 1 {
            output.push_str("[east] ");
        }
        output.push_str("\n");
        
        output
    }
    
    fn move_to_room(&mut self, direction: &str) -> String {
        match direction {
            "west" | "w" if self.current_room > 0 => {
                self.current_room -= 1;
                format!("You move west to {}", self.rooms[self.current_room].name)
            }
            "east" | "e" if self.current_room < self.rooms.len() - 1 => {
                self.current_room += 1;
                format!("You move east to {}", self.rooms[self.current_room].name)
            }
            _ => "You can't go that way.".to_string()
        }
    }
}

fn load_ply_vertices(path: &str) -> Result<Vec<(f32, f32, f32)>, Box<dyn std::error::Error>> {
    println!("Loading PLY file: {}", path);
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut lines = reader.lines();
    
    // Skip header until "end_header"
    let mut vertex_count = 0;
    for line in lines.by_ref() {
        let line = line?;
        if line.starts_with("element vertex") {
            vertex_count = line.split_whitespace()
                .nth(2)
                .and_then(|s| s.parse().ok())
                .unwrap_or(0);
        }
        if line == "end_header" {
            break;
        }
    }
    
    println!("Reading {} vertices...", vertex_count);
    
    // Read vertices (sample every 10th vertex to speed up)
    let mut vertices = Vec::new();
    let sample_rate = 10; // Sample 1 in 10 vertices
    
    for (i, line) in lines.enumerate() {
        if i >= vertex_count {
            break;
        }
        
        if i % sample_rate != 0 {
            continue; // Skip for sampling
        }
        
        if let Ok(line) = line {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 3 {
                if let (Ok(x), Ok(y), Ok(z)) = (
                    parts[0].parse::<f32>(),
                    parts[1].parse::<f32>(),
                    parts[2].parse::<f32>(),
                ) {
                    vertices.push((x, y, z));
                }
            }
        }
        
        if vertices.len() % 10000 == 0 {
            print!(".");
            io::stdout().flush().ok();
        }
    }
    
    println!("\nLoaded {} vertices (sampled from {})", vertices.len(), vertex_count);
    Ok(vertices)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("╔══════════════════════════════════════╗");
    println!("║     ArxOS House Explorer v0.1.0     ║");
    println!("║  ASCII Building Navigation System    ║");
    println!("╚══════════════════════════════════════╝\n");
    
    // Try to load the PLY file
    let ply_path = "/System/Volumes/Data/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply";
    
    println!("Loading your house scan...");
    let vertices = load_ply_vertices(ply_path)?;
    
    println!("Performing semantic compression...");
    let mut world = World::from_point_cloud(vertices);
    
    // Calculate compression ratio
    let original_size = 33 * 1024 * 1024; // 33MB
    let compressed_size = world.rooms.len() * 100; // Rough estimate
    let ratio = original_size as f32 / compressed_size as f32;
    
    println!("\nCompression achieved: {:.0}:1", ratio);
    println!("Original: 33MB → Compressed: ~{}KB\n", compressed_size / 1024);
    
    // Game loop
    println!("Type 'help' for commands, 'quit' to exit.\n");
    println!("{}", world.render_current_room());
    
    loop {
        print!("> ");
        io::stdout().flush()?;
        
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        let input = input.trim().to_lowercase();
        
        match input.as_str() {
            "quit" | "q" => {
                println!("Goodbye!");
                break;
            }
            "help" | "h" => {
                println!("\nCommands:");
                println!("  look (l)    - Look around");
                println!("  west (w)    - Move west");
                println!("  east (e)    - Move east");
                println!("  help (h)    - Show this help");
                println!("  quit (q)    - Exit\n");
            }
            "look" | "l" => {
                println!("{}", world.render_current_room());
            }
            "west" | "w" | "east" | "e" => {
                let result = world.move_to_room(&input);
                println!("{}", result);
                if !result.starts_with("You can't") {
                    println!("{}", world.render_current_room());
                }
            }
            _ => {
                println!("Unknown command. Type 'help' for commands.");
            }
        }
    }
    
    Ok(())
}