//! Game world state management
//! 
//! Manages the building as an explorable game world using ArxObjects

use std::collections::HashMap;
use crate::arxobject::{ArxObject, object_types};
use crate::progressive_renderer::ProgressiveRenderer;
use crate::detail_store::DetailStore;
use crate::error::{Result, ArxError};

/// Cardinal directions for movement
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Direction {
    North,
    South,
    East,
    West,
    Up,
    Down,
}

impl Direction {
    /// Get opposite direction
    pub fn opposite(&self) -> Direction {
        match self {
            Direction::North => Direction::South,
            Direction::South => Direction::North,
            Direction::East => Direction::West,
            Direction::West => Direction::East,
            Direction::Up => Direction::Down,
            Direction::Down => Direction::Up,
        }
    }
    
    /// Get movement delta in millimeters
    pub fn delta(&self) -> (i32, i32, i32) {
        match self {
            Direction::North => (0, 5000, 0),  // 5 meters north
            Direction::South => (0, -5000, 0),
            Direction::East => (5000, 0, 0),
            Direction::West => (-5000, 0, 0),
            Direction::Up => (0, 0, 3000),     // One floor up
            Direction::Down => (0, 0, -3000),
        }
    }
}

/// A room in the building
#[derive(Debug, Clone)]
pub struct Room {
    pub id: u16,
    pub name: String,
    pub position: (u16, u16, u16),
    pub size: (u16, u16, u16),
    pub exits: HashMap<Direction, u16>, // Direction -> Room ID
    pub objects: Vec<ArxObject>,
    pub description: String,
}

impl Room {
    /// Check if a position is inside this room
    pub fn contains(&self, x: u16, y: u16, z: u16) -> bool {
        x >= self.position.0 && x < self.position.0 + self.size.0 &&
        y >= self.position.1 && y < self.position.1 + self.size.1 &&
        z >= self.position.2 && z < self.position.2 + self.size.2
    }
    
    /// Get objects visible from a position
    pub fn visible_objects(&self, from: (u16, u16, u16), range: u16) -> Vec<&ArxObject> {
        self.objects.iter().filter(|obj| {
            let dx = (obj.x as i32 - from.0 as i32).abs();
            let dy = (obj.y as i32 - from.1 as i32).abs();
            let dz = (obj.z as i32 - from.2 as i32).abs();
            let distance = ((dx * dx + dy * dy + dz * dz) as f64).sqrt() as u16;
            distance <= range
        }).collect()
    }
}

/// The game world representing a building
#[derive(Debug, Clone)]
pub struct World {
    /// All ArxObjects in the world
    objects: HashMap<u64, ArxObject>,
    
    /// Rooms in the building
    rooms: HashMap<u16, Room>,
    
    /// Current player position
    player_position: (u16, u16, u16),
    
    /// Current room ID
    current_room: u16,
    
    /// Detail renderer
    renderer: ProgressiveRenderer,
    
    /// Detail store for progressive loading
    detail_store: DetailStore,
    
    /// Other players in the world (multiplayer)
    other_players: HashMap<u32, (u16, u16, u16)>,
    
    /// Building ID
    building_id: u16,
}

impl World {
    /// Create a new empty world
    pub fn new(building_id: u16) -> Self {
        Self {
            objects: HashMap::new(),
            rooms: HashMap::new(),
            player_position: (0, 0, 0),
            current_room: 0,
            renderer: ProgressiveRenderer::new(),
            detail_store: DetailStore::new(),
            other_players: HashMap::new(),
            building_id,
        }
    }
    
    /// Get player position
    pub fn player_position(&self) -> (u16, u16, u16) {
        self.player_position
    }
    
    /// Get mutable player position
    pub fn player_position_mut(&mut self) -> &mut (u16, u16, u16) {
        &mut self.player_position
    }
    
    /// Load world from ArxObjects
    pub fn from_arxobjects(objects: Vec<ArxObject>) -> Self {
        let mut world = Self::new(objects.first().map(|o| o.building_id).unwrap_or(0));
        
        // Group objects by rooms
        let mut room_objects: HashMap<u16, Vec<ArxObject>> = HashMap::new();
        let mut room_id = 0u16;
        
        for obj in objects {
            // Identify rooms
            if obj.object_type == object_types::ROOM {
                room_id += 1;
                let room = Room {
                    id: room_id,
                    name: format!("Room {}", room_id),
                    position: (obj.x, obj.y, obj.z),
                    size: (5000, 5000, 3000), // Default 5x5x3 meters
                    exits: HashMap::new(),
                    objects: Vec::new(),
                    description: {
                        let x = obj.x;
                        let y = obj.y;
                        let z = obj.z;
                        format!("A room at ({}, {}, {})", x, y, z)
                    },
                };
                world.rooms.insert(room_id, room);
            }
            
            // Store object
            let obj_id = Self::object_id(&obj);
            world.objects.insert(obj_id, obj);
            
            // Add to nearest room
            if let Some(room_id) = world.find_room_for_position(obj.x, obj.y, obj.z) {
                room_objects.entry(room_id).or_insert_with(Vec::new).push(obj);
            }
        }
        
        // Populate room objects
        for (room_id, objects) in room_objects {
            if let Some(room) = world.rooms.get_mut(&room_id) {
                room.objects = objects;
                
                // Detect doors and create exits
                for obj in &room.objects {
                    if obj.object_type == object_types::DOOR {
                        // Simple heuristic: doors on edges create exits
                        if obj.x < room.position.0 + 500 {
                            room.exits.insert(Direction::West, room_id + 1);
                        } else if obj.x > room.position.0 + room.size.0 - 500 {
                            room.exits.insert(Direction::East, room_id + 1);
                        }
                        if obj.y < room.position.1 + 500 {
                            room.exits.insert(Direction::South, room_id + 1);
                        } else if obj.y > room.position.1 + room.size.1 - 500 {
                            room.exits.insert(Direction::North, room_id + 1);
                        }
                    }
                }
            }
        }
        
        // Set initial room
        if let Some(first_room) = world.rooms.keys().next() {
            world.current_room = *first_room;
            if let Some(room) = world.rooms.get(first_room) {
                world.player_position = room.position;
            }
        }
        
        world
    }
    
    /// Move player in a direction
    pub fn move_player(&mut self, direction: Direction) -> Result<String> {
        // Check if there's an exit in that direction
        let current_room = self.rooms.get(&self.current_room)
            .ok_or_else(|| ArxError::GameError("Invalid room".into()))?;
        
        if let Some(&next_room_id) = current_room.exits.get(&direction) {
            // Move to next room
            self.current_room = next_room_id;
            
            if let Some(next_room) = self.rooms.get(&next_room_id) {
                self.player_position = next_room.position;
                return Ok(format!("You move {} to {}", 
                    format!("{:?}", direction).to_lowercase(), 
                    next_room.name));
            }
        }
        
        // Try to move within current room
        let delta = direction.delta();
        let new_x = (self.player_position.0 as i32 + delta.0).max(0) as u16;
        let new_y = (self.player_position.1 as i32 + delta.1).max(0) as u16;
        let new_z = (self.player_position.2 as i32 + delta.2).max(0) as u16;
        
        if current_room.contains(new_x, new_y, new_z) {
            self.player_position = (new_x, new_y, new_z);
            Ok(format!("You move {}", format!("{:?}", direction).to_lowercase()))
        } else {
            Err(ArxError::InvalidMove(format!("You can't go {} from here", 
                format!("{:?}", direction).to_lowercase())))
        }
    }
    
    /// Examine an object by name
    pub fn examine(&self, target: &str) -> Result<String> {
        let current_room = self.rooms.get(&self.current_room)
            .ok_or_else(|| ArxError::GameError("Invalid room".into()))?;
        
        // Find object matching target
        for obj in &current_room.objects {
            let obj_name = self.object_type_name(obj.object_type);
            if obj_name.to_lowercase().contains(&target.to_lowercase()) {
                return Ok(self.describe_object(obj));
            }
        }
        
        Err(ArxError::ObjectNotFound(format!("You don't see a {} here", target)))
    }
    
    /// Get current view as ASCII art
    pub fn render_view(&self) -> String {
        let current_room = match self.rooms.get(&self.current_room) {
            Some(room) => room,
            None => return "You are in the void...".to_string(),
        };
        
        let mut output = String::new();
        
        // Room header
        output.push_str(&format!("=== {} ===\n", current_room.name));
        output.push_str(&format!("{}\n\n", current_room.description));
        
        // ASCII room layout
        output.push_str(&self.render_room_ascii(current_room));
        output.push('\n');
        
        // List visible objects
        let visible = current_room.visible_objects(self.player_position, 5000);
        if !visible.is_empty() {
            output.push_str("You see:\n");
            for obj in visible {
                output.push_str(&format!("  - {} at ({:.1}m, {:.1}m, {:.1}m)\n",
                    self.object_type_name(obj.object_type),
                    obj.x as f32 / 1000.0,
                    obj.y as f32 / 1000.0,
                    obj.z as f32 / 1000.0));
            }
        }
        
        // List exits
        if !current_room.exits.is_empty() {
            output.push_str("\nExits: ");
            let exits: Vec<String> = current_room.exits.keys()
                .map(|d| format!("{:?}", d).to_lowercase())
                .collect();
            output.push_str(&exits.join(", "));
        }
        
        // Show other players
        if !self.other_players.is_empty() {
            output.push_str("\n\nOther explorers here:");
            for (player_id, pos) in &self.other_players {
                if self.same_room(*pos) {
                    output.push_str(&format!("\n  - Player {} at ({:.1}m, {:.1}m)",
                        player_id,
                        pos.0 as f32 / 1000.0,
                        pos.1 as f32 / 1000.0));
                }
            }
        }
        
        output
    }
    
    /// Render room as ASCII art
    fn render_room_ascii(&self, room: &Room) -> String {
        let mut grid = vec![vec![' '; 40]; 20];
        
        // Draw room boundaries
        for x in 0..40 {
            grid[0][x] = '═';
            grid[19][x] = '═';
        }
        for y in 0..20 {
            grid[y][0] = '║';
            grid[y][39] = '║';
        }
        grid[0][0] = '╔';
        grid[0][39] = '╗';
        grid[19][0] = '╚';
        grid[19][39] = '╝';
        
        // Place objects
        for obj in &room.objects {
            let rel_x = ((obj.x - room.position.0) * 38 / room.size.0).min(38).max(1) as usize;
            let rel_y = ((obj.y - room.position.1) * 18 / room.size.1).min(18).max(1) as usize;
            
            grid[rel_y][rel_x] = match obj.object_type {
                t if t == object_types::OUTLET => 'O',
                t if t == object_types::LIGHT => 'L',
                t if t == object_types::DOOR => 'D',
                t if t == object_types::WINDOW => 'W',
                t if t == object_types::THERMOSTAT => 'T',
                t if t == object_types::SMOKE_DETECTOR => 'S',
                t if t == object_types::LEAK => '💧',
                _ => '?',
            };
        }
        
        // Place player
        let player_x = ((self.player_position.0 - room.position.0) * 38 / room.size.0)
            .min(38).max(1) as usize;
        let player_y = ((self.player_position.1 - room.position.1) * 18 / room.size.1)
            .min(18).max(1) as usize;
        grid[player_y][player_x] = '@';
        
        // Convert grid to string
        grid.into_iter()
            .map(|row| row.into_iter().collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    }
    
    // Helper methods
    
    fn object_id(obj: &ArxObject) -> u64 {
        ((obj.building_id as u64) << 48) |
        ((obj.object_type as u64) << 40) |
        ((obj.x as u64) << 24) |
        ((obj.y as u64) << 8) |
        (obj.z as u64)
    }
    
    fn find_room_for_position(&self, x: u16, y: u16, z: u16) -> Option<u16> {
        for (id, room) in &self.rooms {
            if room.contains(x, y, z) {
                return Some(*id);
            }
        }
        None
    }
    
    fn same_room(&self, pos: (u16, u16, u16)) -> bool {
        self.find_room_for_position(pos.0, pos.1, pos.2) == Some(self.current_room)
    }
    
    fn object_type_name(&self, obj_type: u8) -> &str {
        match obj_type {
            t if t == object_types::OUTLET => "Electrical outlet",
            t if t == object_types::LIGHT => "Light fixture",
            t if t == object_types::DOOR => "Door",
            t if t == object_types::WINDOW => "Window",
            t if t == object_types::THERMOSTAT => "Thermostat",
            t if t == object_types::SMOKE_DETECTOR => "Smoke detector",
            t if t == object_types::LEAK => "LEAK DETECTED",
            _ => "Unknown object",
        }
    }
    
    fn describe_object(&self, obj: &ArxObject) -> String {
        // Copy fields from packed struct to avoid alignment issues
        let obj_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        let building_id = obj.building_id;
        let properties = obj.properties;
        
        format!("{}\nLocation: ({:.1}m, {:.1}m, {:.1}m)\nID: {:04x}\nProperties: {:?}",
            self.object_type_name(obj_type),
            x as f32 / 1000.0,
            y as f32 / 1000.0,
            z as f32 / 1000.0,
            building_id,
            properties)
    }
    
    /// Update world with new ArxObject from mesh
    pub fn update_object(&mut self, obj: ArxObject) {
        let obj_id = Self::object_id(&obj);
        self.objects.insert(obj_id, obj);
        
        // Update room if needed
        if let Some(room_id) = self.find_room_for_position(obj.x, obj.y, obj.z) {
            if let Some(room) = self.rooms.get_mut(&room_id) {
                // Check if object already exists
                if !room.objects.iter().any(|o| Self::object_id(o) == obj_id) {
                    room.objects.push(obj);
                }
            }
        }
    }
    
    /// Update other player position
    pub fn update_player(&mut self, player_id: u32, x: u16, y: u16, z: u16) {
        self.other_players.insert(player_id, (x, y, z));
    }
}