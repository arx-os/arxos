//! Minecraft-style Terminal Interface for ArxOS
//! 
//! Provides a 3D ASCII visualization of buildings where users can
//! walk around, place blocks (ArxObjects), mine (scan), and build
//! the digital twin in a familiar gaming interface.

use crate::arxobject::{ArxObject, ObjectCategory};
use crate::bilt_contribution_tracker::{ContributionType, PlayerProfile};
use crossterm::{
    event::{self, Event, KeyCode, KeyEvent},
    execute,
    terminal::{self, ClearType},
    cursor,
    style::{self, Color, Stylize},
};
use std::io::{self, Write};
use std::collections::HashMap;

/// Minecraft-style block types that map to ArxObjects
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum BlockType {
    Air,           // Empty space
    Wall,          // Solid wall
    Floor,         // Floor tile
    Ceiling,       // Ceiling tile
    Door,          // Doorway
    Window,        // Window
    Outlet,        // Electrical outlet
    Light,         // Light fixture
    HVAC,          // HVAC unit
    Equipment,     // Generic equipment
    Stairs,        // Stairway
    Unknown,       // Unscanned area
    Player,        // Player position
}

impl BlockType {
    /// Get the ASCII representation and color for this block
    pub fn render(&self) -> (&str, Color) {
        match self {
            BlockType::Air => ("  ", Color::Black),
            BlockType::Wall => ("██", Color::DarkGrey),
            BlockType::Floor => ("░░", Color::Grey),
            BlockType::Ceiling => ("▓▓", Color::Grey),
            BlockType::Door => ("[]", Color::DarkYellow),
            BlockType::Window => ("##", Color::Cyan),
            BlockType::Outlet => ("⚡", Color::Yellow),
            BlockType::Light => ("💡", Color::White),
            BlockType::HVAC => ("🌡", Color::Blue),
            BlockType::Equipment => ("⚙️", Color::Magenta),
            BlockType::Stairs => ("▲▼", Color::Green),
            BlockType::Unknown => ("??", Color::DarkRed),
            BlockType::Player => ("@@", Color::Green),
        }
    }
    
    /// Convert ArxObject to BlockType
    pub fn from_arxobject(obj: &ArxObject) -> Self {
        match obj.object_type {
            0x01 => BlockType::Wall,
            0x02 => BlockType::Floor,
            0x03 => BlockType::Ceiling,
            0x04 => BlockType::Door,
            0x05 => BlockType::Window,
            0x10 => BlockType::Outlet,
            0x11 => BlockType::Light,
            0x12 => BlockType::HVAC,
            0x20..=0x2F => BlockType::Equipment,
            0x30 => BlockType::Stairs,
            _ => BlockType::Unknown,
        }
    }
}

/// 3D world representation of a building
pub struct BuildingWorld {
    /// 3D grid of blocks [x][y][z]
    blocks: Vec<Vec<Vec<BlockType>>>,
    
    /// Player position
    player_x: usize,
    player_y: usize,
    player_z: usize,
    
    /// Player facing direction (0=N, 1=E, 2=S, 3=W)
    player_facing: u8,
    
    /// Dimensions
    width: usize,
    height: usize,
    depth: usize,
    
    /// Current floor being viewed
    current_floor: usize,
    
    /// Inventory of blocks player can place
    inventory: HashMap<BlockType, u32>,
    
    /// Currently selected block type
    selected_block: BlockType,
    
    /// Player profile
    player: PlayerProfile,
    
    /// Building completion percentage
    completion: f32,
    
    /// Active quests
    quests: Vec<Quest>,
}

/// Quest for gamification
#[derive(Debug, Clone)]
pub struct Quest {
    pub id: String,
    pub name: String,
    pub description: String,
    pub progress: u32,
    pub target: u32,
    pub bilt_reward: u32,
}

impl BuildingWorld {
    /// Create a new building world
    pub fn new(width: usize, height: usize, depth: usize, player: PlayerProfile) -> Self {
        // Initialize with mostly unknown blocks
        let mut blocks = vec![vec![vec![BlockType::Unknown; depth]; height]; width];
        
        // Add some basic structure (floors)
        for x in 0..width {
            for z in 0..depth {
                for floor in (0..height).step_by(3) {
                    blocks[x][floor][z] = BlockType::Floor;
                    if floor + 2 < height {
                        blocks[x][floor + 2][z] = BlockType::Ceiling;
                    }
                }
            }
        }
        
        // Initialize inventory
        let mut inventory = HashMap::new();
        inventory.insert(BlockType::Wall, 100);
        inventory.insert(BlockType::Door, 10);
        inventory.insert(BlockType::Window, 20);
        inventory.insert(BlockType::Outlet, 50);
        inventory.insert(BlockType::Light, 30);
        
        // Create starting quests
        let quests = vec![
            Quest {
                id: "scan_room".to_string(),
                name: "First Room".to_string(),
                description: "Scan your first complete room".to_string(),
                progress: 0,
                target: 1,
                bilt_reward: 100,
            },
            Quest {
                id: "place_10_objects".to_string(),
                name: "Object Placer".to_string(),
                description: "Place 10 objects in the building".to_string(),
                progress: 0,
                target: 10,
                bilt_reward: 50,
            },
        ];
        
        Self {
            blocks,
            player_x: width / 2,
            player_y: 0,
            player_z: depth / 2,
            player_facing: 0,
            width,
            height,
            depth,
            current_floor: 0,
            inventory,
            selected_block: BlockType::Wall,
            player,
            completion: 0.0,
            quests,
        }
    }
    
    /// Load ArxObjects into the world
    pub fn load_arxobjects(&mut self, objects: &[ArxObject]) {
        for obj in objects {
            // Convert coordinates from mm to grid units (1 unit = 1 meter)
            let x = (obj.x / 1000) as usize;
            let y = (obj.y / 1000) as usize;
            let z = (obj.z / 1000) as usize;
            
            if x < self.width && y < self.height && z < self.depth {
                self.blocks[x][y][z] = BlockType::from_arxobject(obj);
            }
        }
        
        self.update_completion();
    }
    
    /// Update building completion percentage
    fn update_completion(&mut self) {
        let total_blocks = self.width * self.height * self.depth;
        let unknown_blocks = self.blocks.iter()
            .flat_map(|x| x.iter())
            .flat_map(|y| y.iter())
            .filter(|&&b| b == BlockType::Unknown)
            .count();
        
        self.completion = 1.0 - (unknown_blocks as f32 / total_blocks as f32);
    }
    
    /// Move the player
    pub fn move_player(&mut self, dx: i32, dy: i32, dz: i32) -> bool {
        let new_x = (self.player_x as i32 + dx) as usize;
        let new_y = (self.player_y as i32 + dy) as usize;
        let new_z = (self.player_z as i32 + dz) as usize;
        
        // Check bounds
        if new_x >= self.width || new_y >= self.height || new_z >= self.depth {
            return false;
        }
        
        // Check collision
        if self.blocks[new_x][new_y][new_z] != BlockType::Air 
            && self.blocks[new_x][new_y][new_z] != BlockType::Unknown {
            return false;
        }
        
        self.player_x = new_x;
        self.player_y = new_y;
        self.player_z = new_z;
        true
    }
    
    /// Place a block at the target position
    pub fn place_block(&mut self, block_type: BlockType) -> Option<ArxObject> {
        let (tx, ty, tz) = self.get_target_position();
        
        // Check if we have the block in inventory
        if let Some(count) = self.inventory.get_mut(&block_type) {
            if *count > 0 {
                *count -= 1;
                self.blocks[tx][ty][tz] = block_type;
                
                // Update quest progress
                for quest in &mut self.quests {
                    if quest.id == "place_10_objects" {
                        quest.progress += 1;
                    }
                }
                
                // Create ArxObject for this placement
                return Some(ArxObject::new(
                    0x0001, // Building ID
                    block_type as u8,
                    (tx * 1000) as u16,
                    (ty * 1000) as u16,
                    (tz * 1000) as u16,
                ));
            }
        }
        None
    }
    
    /// Mine (scan) a block
    pub fn mine_block(&mut self) -> Option<BlockType> {
        let (tx, ty, tz) = self.get_target_position();
        let block = self.blocks[tx][ty][tz];
        
        if block != BlockType::Air && block != BlockType::Unknown {
            // "Mine" the block - convert unknown to known
            if block == BlockType::Unknown {
                // Simulate scanning - reveal the actual block
                self.blocks[tx][ty][tz] = BlockType::Air; // Or determine actual type
                
                // Update quest progress
                for quest in &mut self.quests {
                    if quest.id == "scan_room" {
                        quest.progress += 1;
                    }
                }
            }
            
            // Add to inventory
            *self.inventory.entry(block).or_insert(0) += 1;
            
            return Some(block);
        }
        None
    }
    
    /// Get the position the player is looking at
    fn get_target_position(&self) -> (usize, usize, usize) {
        let (dx, dz) = match self.player_facing {
            0 => (0, -1), // North
            1 => (1, 0),  // East
            2 => (0, 1),  // South
            3 => (-1, 0), // West
            _ => (0, 0),
        };
        
        let tx = (self.player_x as i32 + dx).max(0).min(self.width as i32 - 1) as usize;
        let tz = (self.player_z as i32 + dz).max(0).min(self.depth as i32 - 1) as usize;
        
        (tx, self.player_y, tz)
    }
    
    /// Render the world to terminal
    pub fn render(&self) -> String {
        let mut output = String::new();
        
        // Header
        output.push_str(&format!(
            "╔══════════════════════════════════════════════════════════════╗\n"
        ));
        output.push_str(&format!(
            "║  ArxOS BuildCraft  |  BILT: {}  |  Level: {}  |  {}% Complete  ║\n",
            self.player.total_bilt, self.player.level, (self.completion * 100.0) as u32
        ));
        output.push_str(&format!(
            "╠══════════════════════════════════════════════════════════════╣\n"
        ));
        
        // 3D view (top-down for current floor)
        let view_range = 10; // View distance
        let start_x = self.player_x.saturating_sub(view_range);
        let end_x = (self.player_x + view_range).min(self.width - 1);
        let start_z = self.player_z.saturating_sub(view_range);
        let end_z = (self.player_z + view_range).min(self.depth - 1);
        
        // Render map
        for z in start_z..=end_z {
            output.push_str("║ ");
            for x in start_x..=end_x {
                if x == self.player_x && z == self.player_z {
                    output.push_str("@@");
                } else {
                    let block = self.blocks[x][self.player_y][z];
                    let (symbol, _color) = block.render();
                    output.push_str(symbol);
                }
            }
            output.push_str(" ║\n");
        }
        
        output.push_str(&format!(
            "╠══════════════════════════════════════════════════════════════╣\n"
        ));
        
        // Inventory bar
        output.push_str("║ Inventory: ");
        for (block, count) in &self.inventory {
            if *count > 0 {
                let (symbol, _) = block.render();
                output.push_str(&format!("{}{} ", symbol, count));
            }
        }
        output.push_str(" ║\n");
        
        // Controls
        output.push_str(&format!(
            "╠══════════════════════════════════════════════════════════════╣\n"
        ));
        output.push_str(&format!(
            "║ [WASD] Move  [Q/E] Up/Down  [Space] Place  [F] Mine  [Tab] Inv ║\n"
        ));
        
        // Active quest
        if let Some(quest) = self.quests.first() {
            output.push_str(&format!(
                "║ Quest: {} ({}/{}) +{} BILT                    ║\n",
                quest.name, quest.progress, quest.target, quest.bilt_reward
            ));
        }
        
        output.push_str(&format!(
            "╚══════════════════════════════════════════════════════════════╝\n"
        ));
        
        output
    }
}

/// Terminal game loop
pub struct MinecraftTerminal {
    world: BuildingWorld,
    running: bool,
}

impl MinecraftTerminal {
    pub fn new(player: PlayerProfile) -> Self {
        Self {
            world: BuildingWorld::new(50, 10, 50, player),
            running: true,
        }
    }
    
    /// Run the game loop
    pub async fn run(&mut self) -> io::Result<()> {
        // Setup terminal
        terminal::enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, terminal::EnterAlternateScreen)?;
        
        while self.running {
            // Clear and render
            execute!(stdout, terminal::Clear(ClearType::All))?;
            execute!(stdout, cursor::MoveTo(0, 0))?;
            print!("{}", self.world.render());
            stdout.flush()?;
            
            // Handle input
            if event::poll(std::time::Duration::from_millis(100))? {
                if let Event::Key(key) = event::read()? {
                    self.handle_input(key);
                }
            }
        }
        
        // Restore terminal
        execute!(stdout, terminal::LeaveAlternateScreen)?;
        terminal::disable_raw_mode()?;
        
        Ok(())
    }
    
    fn handle_input(&mut self, key: KeyEvent) {
        match key.code {
            // Movement
            KeyCode::Char('w') => { self.world.move_player(0, 0, -1); }
            KeyCode::Char('s') => { self.world.move_player(0, 0, 1); }
            KeyCode::Char('a') => { self.world.move_player(-1, 0, 0); }
            KeyCode::Char('d') => { self.world.move_player(1, 0, 0); }
            KeyCode::Char('q') => { self.world.move_player(0, -1, 0); }
            KeyCode::Char('e') => { self.world.move_player(0, 1, 0); }
            
            // Actions
            KeyCode::Char(' ') => {
                if let Some(obj) = self.world.place_block(self.world.selected_block) {
                    // TODO: Send to blockchain
                    println!("Placed block: {:?}", obj);
                }
            }
            KeyCode::Char('f') => {
                if let Some(block) = self.world.mine_block() {
                    println!("Mined block: {:?}", block);
                }
            }
            
            // Rotation
            KeyCode::Left => { 
                self.world.player_facing = (self.world.player_facing + 3) % 4;
            }
            KeyCode::Right => {
                self.world.player_facing = (self.world.player_facing + 1) % 4;
            }
            
            // Quit
            KeyCode::Esc => { self.running = false; }
            
            _ => {}
        }
    }
}

/// Creative mode for remote contributors
pub struct CreativeMode {
    world: BuildingWorld,
    camera_x: f32,
    camera_y: f32,
    camera_z: f32,
    zoom: f32,
}

impl CreativeMode {
    pub fn new(player: PlayerProfile) -> Self {
        Self {
            world: BuildingWorld::new(100, 20, 100, player),
            camera_x: 50.0,
            camera_y: 10.0,
            camera_z: 50.0,
            zoom: 1.0,
        }
    }
    
    /// Render isometric view for better building visualization
    pub fn render_isometric(&self) -> String {
        let mut output = String::new();
        
        // Header with different stats for creative mode
        output.push_str(&format!(
            "╔══════════════════════════════════════════════════════════════╗\n"
        ));
        output.push_str(&format!(
            "║  ArxOS Creative Mode  |  Remote Contributor  |  BILT: {}  ║\n",
            self.world.player.total_bilt
        ));
        output.push_str(&format!(
            "╠══════════════════════════════════════════════════════════════╣\n"
        ));
        
        // Isometric grid view
        let view_size = 20;
        for y in 0..view_size {
            for x in 0..view_size {
                // Calculate isometric coordinates
                let iso_x = x - y;
                let iso_y = (x + y) / 2;
                
                // TODO: Render blocks in isometric perspective
            }
            output.push_str("║\n");
        }
        
        output.push_str(&format!(
            "╠══════════════════════════════════════════════════════════════╣\n"
        ));
        output.push_str(&format!(
            "║ Tools: [B]lock [W]ire [P]ipe [D]oor [L]ight [V]alidate       ║\n"
        ));
        output.push_str(&format!(
            "║ View: [+/-] Zoom  [Arrows] Pan  [PgUp/Dn] Floors  [G]rid     ║\n"
        ));
        output.push_str(&format!(
            "╚══════════════════════════════════════════════════════════════╝\n"
        ));
        
        output
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_world_creation() {
        let player = PlayerProfile {
            eth_address: [0; 20],
            username: "TestPlayer".to_string(),
            avatar_seed: 12345,
            total_bilt: 100,
            total_xp: 500,
            level: 5,
            daily_streak: 3,
            buildings_scanned: 1,
            objects_placed: 10,
            accuracy_rating: 0.95,
            achievements: vec![],
            titles: vec![],
            global_rank: 1000,
            district_rank: 10,
            weekly_rank: 50,
        };
        
        let world = BuildingWorld::new(10, 3, 10, player);
        assert_eq!(world.width, 10);
        assert_eq!(world.height, 3);
        assert_eq!(world.depth, 10);
    }
    
    #[test]
    fn test_player_movement() {
        let player = PlayerProfile {
            eth_address: [0; 20],
            username: "TestPlayer".to_string(),
            avatar_seed: 12345,
            total_bilt: 100,
            total_xp: 500,
            level: 5,
            daily_streak: 3,
            buildings_scanned: 1,
            objects_placed: 10,
            accuracy_rating: 0.95,
            achievements: vec![],
            titles: vec![],
            global_rank: 1000,
            district_rank: 10,
            weekly_rank: 50,
        };
        
        let mut world = BuildingWorld::new(10, 3, 10, player);
        let initial_x = world.player_x;
        
        world.move_player(1, 0, 0);
        assert_eq!(world.player_x, initial_x + 1);
    }
}