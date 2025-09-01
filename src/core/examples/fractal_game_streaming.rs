//! Fractal Game Streaming: Elden Ring over Packet Radio
//! 
//! Demonstrates progressive reconstruction from 13-byte packets

use arxos_core::{
    arxobject::ArxObject,
    progressive_renderer::ProgressiveRenderer,
    detail_store::DetailLevel,
};
use std::collections::VecDeque;

// Game-specific object types
mod game_types {
    pub const PLAYER: u8 = 0x80;
    pub const BONFIRE: u8 = 0x81;
    pub const TREE: u8 = 0x82;
    pub const ENEMY_GRUNT: u8 = 0x83;
    pub const ENEMY_KNIGHT: u8 = 0x84;
    pub const ENEMY_BOSS: u8 = 0x85;
    pub const CHEST: u8 = 0x86;
    pub const CASTLE: u8 = 0x87;
    pub const BRIDGE: u8 = 0x88;
    pub const ITEM_SOUL: u8 = 0x89;
    pub const GRASS: u8 = 0x8A;
    pub const ROCK: u8 = 0x8B;
}

fn main() {
    println!("╔══════════════════════════════════════════════════════════╗");
    println!("║   ArxOS Fractal Streaming: Elden Ring over Packet Radio  ║");
    println!("╚══════════════════════════════════════════════════════════╝\n");
    
    // Simulate a game scene
    let scene = create_game_scene();
    
    println!("Scene contains {} ArxObjects ({} bytes)\n", 
        scene.len(), scene.len() * 13);
    
    // Simulate packet radio transmission at 1200 baud
    simulate_progressive_transmission(&scene, 1200);
}

fn create_game_scene() -> Vec<ArxObject> {
    let mut objects = Vec::new();
    
    // Player at spawn
    objects.push(create_game_object(game_types::PLAYER, 5000, 5000, 1000, 
        [100, 0, 0, 0])); // 100 HP
    
    // Bonfire (save point)
    objects.push(create_game_object(game_types::BONFIRE, 4800, 5000, 1000,
        [1, 0, 0, 0])); // Lit
    
    // Castle in distance
    objects.push(create_game_object(game_types::CASTLE, 8000, 8000, 2000,
        [0, 0, 0, 0]));
    
    // Trees scattered around
    for i in 0..5 {
        objects.push(create_game_object(game_types::TREE, 
            4000 + i * 500, 4500, 1000,
            [i as u8, 0, 0, 0])); // Different tree types
    }
    
    // Enemies
    objects.push(create_game_object(game_types::ENEMY_GRUNT, 5500, 5200, 1000,
        [100, 0, 0, 0])); // 100 HP, idle
    
    objects.push(create_game_object(game_types::ENEMY_KNIGHT, 6000, 5500, 1000,
        [100, 2, 0, 0])); // 100 HP, patrolling
    
    // Boss in castle
    objects.push(create_game_object(game_types::ENEMY_BOSS, 8000, 8000, 2100,
        [100, 0, 0, 0])); // Full health
    
    // Loot chest
    objects.push(create_game_object(game_types::CHEST, 5200, 4800, 1000,
        [0, 0, 0, 0])); // Unopened
    
    // Environmental details
    for i in 0..10 {
        objects.push(create_game_object(game_types::GRASS,
            4000 + (i * 317) % 2000, 4000 + (i * 271) % 2000, 950,
            [0, 0, 0, 0]));
    }
    
    objects
}

fn create_game_object(obj_type: u8, x: u16, y: u16, z: u16, properties: [u8; 4]) -> ArxObject {
    let mut obj = ArxObject::new(0x0001, obj_type, x, y, z);
    obj.properties = properties;
    obj
}

fn simulate_progressive_transmission(scene: &[ArxObject], baud_rate: u32) {
    let bytes_per_second = baud_rate / 8;
    let objects_per_second = bytes_per_second / 13;
    
    println!("Transmission at {} baud ({} objects/second)", 
        baud_rate, objects_per_second);
    println!("═══════════════════════════════════════════════\n");
    
    let mut transmission_queue: VecDeque<ArxObject> = scene.iter().copied().collect();
    let mut received_objects = Vec::new();
    let mut time_ms = 0;
    
    // Priority: Player first, then nearby threats, then environment
    transmission_queue.make_contiguous().sort_by_key(|obj| {
        match obj.object_type {
            game_types::PLAYER => 0,
            game_types::ENEMY_GRUNT | game_types::ENEMY_KNIGHT => 1,
            game_types::BONFIRE | game_types::CHEST => 2,
            game_types::ENEMY_BOSS => 3,
            game_types::CASTLE => 4,
            game_types::TREE => 5,
            _ => 6,
        }
    });
    
    // Simulate progressive reception
    while !transmission_queue.is_empty() {
        // Receive objects based on baud rate
        let objects_this_frame = (objects_per_second as f32 * 0.1).max(1.0) as usize;
        
        for _ in 0..objects_this_frame {
            if let Some(obj) = transmission_queue.pop_front() {
                received_objects.push(obj);
            }
        }
        
        // Render current state
        render_game_state(&received_objects, time_ms);
        
        time_ms += 100; // 100ms per frame
        
        // Show first few frames then skip to end
        if time_ms == 500 || time_ms == 1000 || transmission_queue.is_empty() {
            std::thread::sleep(std::time::Duration::from_millis(500));
        } else if time_ms > 1000 && !transmission_queue.is_empty() {
            continue; // Skip intermediate frames for demo
        }
    }
    
    println!("\n═══════════════════════════════════════════════");
    println!("Transmission complete in {:.1} seconds", time_ms as f32 / 1000.0);
    println!("Final scene: {} objects rendered", received_objects.len());
}

fn render_game_state(objects: &[ArxObject], time_ms: u32) {
    println!("T+{:04}ms: {} objects received", time_ms, objects.len());
    
    // Determine render quality based on time
    let detail_level = (time_ms as f32 / 5000.0).min(1.0);
    
    if detail_level < 0.2 {
        render_ascii_view(objects);
    } else if detail_level < 0.5 {
        render_2d_map(objects);
    } else {
        render_3d_description(objects, detail_level);
    }
    
    println!();
}

fn render_ascii_view(objects: &[ArxObject]) {
    println!("  [ASCII View - Immediate]");
    print!("  ");
    
    for obj in objects.iter().take(10) {
        let symbol = match obj.object_type {
            game_types::PLAYER => "@",
            game_types::BONFIRE => "🔥",
            game_types::TREE => "🌳",
            game_types::ENEMY_GRUNT => "☠",
            game_types::ENEMY_KNIGHT => "⚔",
            game_types::ENEMY_BOSS => "👹",
            game_types::CHEST => "📦",
            game_types::CASTLE => "🏰",
            game_types::GRASS => ".",
            _ => "?",
        };
        print!("{} ", symbol);
    }
    
    if objects.len() > 10 {
        print!("...");
    }
    println!();
}

fn render_2d_map(objects: &[ArxObject]) {
    println!("  [2D Map View]");
    println!("  ┌────────────────────┐");
    
    // Create simple 2D grid
    let mut grid = vec![vec![' '; 20]; 5];
    
    for obj in objects {
        let x = ((obj.x as usize - 4000) / 400).min(19);
        let y = ((obj.y as usize - 4000) / 400).min(4);
        
        let symbol = match obj.object_type {
            game_types::PLAYER => '@',
            game_types::BONFIRE => '▲',
            game_types::TREE => '♠',
            game_types::ENEMY_GRUNT => 'g',
            game_types::ENEMY_KNIGHT => 'K',
            game_types::ENEMY_BOSS => 'B',
            game_types::CHEST => '□',
            game_types::CASTLE => '▓',
            game_types::GRASS => '.',
            game_types::ROCK => 'o',
            _ => '?',
        };
        
        if grid[y][x] == ' ' || obj.object_type == game_types::PLAYER {
            grid[y][x] = symbol;
        }
    }
    
    for row in grid {
        print!("  │");
        for cell in row {
            print!("{}", cell);
        }
        println!("│");
    }
    
    println!("  └────────────────────┘");
}

fn render_3d_description(objects: &[ArxObject], detail_level: f32) {
    println!("  [3D Scene - {:.0}% Detail]", detail_level * 100.0);
    
    // Count object types
    let mut player = None;
    let mut enemies = Vec::new();
    let mut environment = Vec::new();
    let mut items = Vec::new();
    
    for obj in objects {
        match obj.object_type {
            game_types::PLAYER => player = Some(obj),
            game_types::ENEMY_GRUNT | game_types::ENEMY_KNIGHT | game_types::ENEMY_BOSS => {
                enemies.push(obj);
            }
            game_types::CHEST | game_types::ITEM_SOUL => items.push(obj),
            _ => environment.push(obj),
        }
    }
    
    if let Some(p) = player {
        let hp = p.properties[0];
        let x = p.x;
        let y = p.y;
        let z = p.z;
        println!("  Player: HP {}/100 at ({}, {}, {})", 
            hp, x, y, z);
    }
    
    if !enemies.is_empty() {
        print!("  Enemies: ");
        for (i, enemy) in enemies.iter().enumerate() {
            if i > 0 { print!(", "); }
            let enemy_type = match enemy.object_type {
                game_types::ENEMY_GRUNT => "Grunt",
                game_types::ENEMY_KNIGHT => "Knight",
                game_types::ENEMY_BOSS => "BOSS",
                _ => "Unknown",
            };
            print!("{} (HP:{})", enemy_type, enemy.properties[0]);
        }
        println!();
    }
    
    if !items.is_empty() {
        println!("  Items: {} available", items.len());
    }
    
    if detail_level > 0.7 {
        println!("  Environment: {} objects with textures", environment.len());
        println!("  Rendering: Shadows, particles, volumetric fog");
    } else {
        println!("  Environment: {} objects loading...", environment.len());
    }
}