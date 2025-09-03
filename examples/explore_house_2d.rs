//! Interactive 2D exploration of house scan
//! 
//! Walk through your LiDAR-scanned house in ASCII

use arxos_core::ply_parser_simple::SimplePlyParser;
use arxos_core::ascii_renderer_2d::FloorRenderer;
use arxos_core::persistence_simple::ArxObjectDatabase;
use std::io::{self, Write};
use termion::raw::IntoRawMode;
use termion::input::TermRead;
use termion::event::Key;
use termion::clear;
use termion::cursor;

struct GameState {
    renderer: FloorRenderer,
    player_x: usize,
    player_y: usize,
    floor_level: f32,
    semantic_tags: std::collections::HashMap<(usize, usize), String>,
    mode: GameMode,
}

#[derive(PartialEq)]
enum GameMode {
    Explore,
    Inspect,
    Tag,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Parse house scan
    println!("Loading house scan...");
    let ply_file = "/Users/joelpate/Downloads/Untitled_Scan_18_44_21.ply";
    
    let parser = SimplePlyParser::new();
    let objects = parser.parse_to_arxobjects(ply_file, 0x0001)?;
    
    println!("Loaded {} objects. Press any key to start exploring...", objects.len());
    let _ = io::stdin().read_line(&mut String::new());
    
    // Initialize game
    let mut game = GameState {
        renderer: FloorRenderer::new(objects.clone(), 0.0, 1.5), // Ground floor
        player_x: 10,
        player_y: 10,
        floor_level: 0.0,
        semantic_tags: std::collections::HashMap::new(),
        mode: GameMode::Explore,
    };
    
    // Enter raw mode for keyboard input
    let stdout = io::stdout().into_raw_mode()?;
    let mut stdout = io::stdout();
    let stdin = io::stdin();
    
    // Game loop
    for key in stdin.keys() {
        // Clear screen
        write!(stdout, "{}{}", clear::All, cursor::Goto(1, 1))?;
        
        // Handle input
        match key? {
            Key::Char('q') | Key::Esc => break,
            
            // Movement (Explore mode only)
            Key::Up | Key::Char('w') if game.mode == GameMode::Explore => {
                if game.player_y > 0 { game.player_y -= 1; }
            }
            Key::Down | Key::Char('s') if game.mode == GameMode::Explore => {
                if game.player_y < 39 { game.player_y += 1; }
            }
            Key::Left | Key::Char('a') if game.mode == GameMode::Explore => {
                if game.player_x > 0 { game.player_x -= 1; }
            }
            Key::Right | Key::Char('d') if game.mode == GameMode::Explore => {
                if game.player_x < 119 { game.player_x += 1; }
            }
            
            // Mode switching
            Key::Char('i') => {
                game.mode = if game.mode == GameMode::Inspect {
                    GameMode::Explore
                } else {
                    GameMode::Inspect
                };
            }
            Key::Char('t') => {
                game.mode = if game.mode == GameMode::Tag {
                    GameMode::Explore
                } else {
                    GameMode::Tag
                };
            }
            
            // Floor switching
            Key::PageUp | Key::Char('[') => {
                game.floor_level += 3.0;
                game.renderer = FloorRenderer::new(objects.clone(), game.floor_level, 1.5);
            }
            Key::PageDown | Key::Char(']') => {
                game.floor_level -= 3.0;
                game.renderer = FloorRenderer::new(objects.clone(), game.floor_level, 1.5);
            }
            
            _ => {}
        }
        
        // Render
        render_game(&mut stdout, &mut game)?;
        
        stdout.flush()?;
    }
    
    // Store semantic tags if any were added
    if !game.semantic_tags.is_empty() {
        println!("\nSaving {} semantic tags...", game.semantic_tags.len());
        // In production, save to database
    }
    
    Ok(())
}

fn render_game(stdout: &mut impl Write, game: &mut GameState) -> io::Result<()> {
    // Header
    writeln!(stdout, "╔══════════════════════════════════════════════════════════════╗")?;
    writeln!(stdout, "║  ArxOS Building Explorer - Floor {:.0}m                        ║", game.floor_level)?;
    writeln!(stdout, "╚══════════════════════════════════════════════════════════════╝")?;
    
    // Render floor with player
    let floor_view = game.renderer.render();
    let lines: Vec<&str> = floor_view.lines().collect();
    
    for (y, line) in lines.iter().enumerate().take(30) {
        write!(stdout, "║")?;
        for (x, ch) in line.chars().enumerate().take(60) {
            if x == game.player_x && y == game.player_y {
                write!(stdout, "@")?;
            } else if let Some(tag) = game.semantic_tags.get(&(x, y)) {
                write!(stdout, "!")?; // Tagged location
            } else {
                write!(stdout, "{}", ch)?;
            }
        }
        writeln!(stdout, "║")?;
    }
    
    writeln!(stdout, "╠══════════════════════════════════════════════════════════════╣")?;
    
    // Status area
    match game.mode {
        GameMode::Explore => {
            writeln!(stdout, "║ Mode: EXPLORE                                               ║")?;
            writeln!(stdout, "║ Position: ({}, {})                                          ║", 
                     game.player_x, game.player_y)?;
            writeln!(stdout, "║                                                              ║")?;
            writeln!(stdout, "║ Controls:                                                    ║")?;
            writeln!(stdout, "║  WASD/Arrows: Move   [i]: Inspect   [t]: Tag                ║")?;
            writeln!(stdout, "║  [/]: Change floor   [q]: Quit                              ║")?;
        }
        
        GameMode::Inspect => {
            writeln!(stdout, "║ Mode: INSPECT                                               ║")?;
            
            if let Some(info) = game.renderer.inspect(game.player_x, game.player_y) {
                for line in info.lines() {
                    writeln!(stdout, "║ {}                                            ║", 
                             format!("{:<50}", line))?;
                }
            } else {
                writeln!(stdout, "║ Nothing here to inspect                                     ║")?;
            }
            
            writeln!(stdout, "║                                                              ║")?;
            writeln!(stdout, "║ Press [i] to return to exploration                          ║")?;
        }
        
        GameMode::Tag => {
            writeln!(stdout, "║ Mode: TAG                                                   ║")?;
            writeln!(stdout, "║ Enter semantic information for this location:               ║")?;
            
            if let Some(existing) = game.semantic_tags.get(&(game.player_x, game.player_y)) {
                writeln!(stdout, "║ Current: {}                                    ║", 
                         format!("{:<40}", existing))?;
            } else {
                writeln!(stdout, "║ (No tag yet)                                                ║")?;
            }
            
            writeln!(stdout, "║                                                              ║")?;
            writeln!(stdout, "║ Examples: \"Circuit 2\", \"Zone A HVAC\", \"Emergency Light\"     ║")?;
            writeln!(stdout, "║ Press [t] to cancel                                         ║")?;
        }
    }
    
    writeln!(stdout, "╚══════════════════════════════════════════════════════════════╝")?;
    
    // Legend
    writeln!(stdout, "\nLegend: @ You  █ Wall  o Outlet  / Switch  * Light  T Thermostat")?;
    
    Ok(())
}