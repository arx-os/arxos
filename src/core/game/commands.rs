//! Game command parsing and execution
//! 
//! Handles text-adventure style commands for building exploration

use crate::error::{Result, ArxError};
use super::world::{World, Direction};

/// Game commands that can be executed
#[derive(Debug, Clone)]
pub enum Command {
    // Movement
    Move(Direction),
    Go(String),
    
    // Exploration
    Look,
    Examine(String),
    Search,
    
    // Interaction
    Use(String),
    Take(String),
    Drop(String),
    
    // Communication
    Say(String),
    Broadcast(String),
    
    // Reporting
    Report(String),
    Alert(String),
    
    // System
    Help,
    Map,
    Status,
    Quit,
}

/// Command parser for text input
pub struct CommandParser;

impl CommandParser {
    /// Parse user input into a command
    pub fn parse(input: &str) -> Result<Command> {
        let input = input.trim().to_lowercase();
        let parts: Vec<&str> = input.split_whitespace().collect();
        
        if parts.is_empty() {
            return Err(ArxError::ParseError("Empty command".into()));
        }
        
        match parts[0] {
            // Movement commands
            "n" | "north" => Ok(Command::Move(Direction::North)),
            "s" | "south" => Ok(Command::Move(Direction::South)),
            "e" | "east" => Ok(Command::Move(Direction::East)),
            "w" | "west" => Ok(Command::Move(Direction::West)),
            "u" | "up" => Ok(Command::Move(Direction::Up)),
            "d" | "down" => Ok(Command::Move(Direction::Down)),
            
            "go" | "move" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Go where?".into()));
                }
                match parts[1] {
                    "n" | "north" => Ok(Command::Move(Direction::North)),
                    "s" | "south" => Ok(Command::Move(Direction::South)),
                    "e" | "east" => Ok(Command::Move(Direction::East)),
                    "w" | "west" => Ok(Command::Move(Direction::West)),
                    "u" | "up" => Ok(Command::Move(Direction::Up)),
                    "d" | "down" => Ok(Command::Move(Direction::Down)),
                    place => Ok(Command::Go(place.to_string())),
                }
            }
            
            // Exploration commands
            "l" | "look" => Ok(Command::Look),
            "x" | "ex" | "examine" | "inspect" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Examine what?".into()));
                }
                Ok(Command::Examine(parts[1..].join(" ")))
            }
            "search" => Ok(Command::Search),
            
            // Interaction commands
            "use" | "activate" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Use what?".into()));
                }
                Ok(Command::Use(parts[1..].join(" ")))
            }
            "take" | "get" | "grab" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Take what?".into()));
                }
                Ok(Command::Take(parts[1..].join(" ")))
            }
            "drop" | "put" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Drop what?".into()));
                }
                Ok(Command::Drop(parts[1..].join(" ")))
            }
            
            // Communication
            "say" | "'" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Say what?".into()));
                }
                Ok(Command::Say(parts[1..].join(" ")))
            }
            "broadcast" | "!" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Broadcast what?".into()));
                }
                Ok(Command::Broadcast(parts[1..].join(" ")))
            }
            
            // Reporting
            "report" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Report what?".into()));
                }
                Ok(Command::Report(parts[1..].join(" ")))
            }
            "alert" => {
                if parts.len() < 2 {
                    return Err(ArxError::ParseError("Alert about what?".into()));
                }
                Ok(Command::Alert(parts[1..].join(" ")))
            }
            
            // System commands
            "h" | "help" | "?" => Ok(Command::Help),
            "m" | "map" => Ok(Command::Map),
            "status" | "stats" => Ok(Command::Status),
            "q" | "quit" | "exit" => Ok(Command::Quit),
            
            _ => Err(ArxError::ParseError(format!("Unknown command: {}", parts[0]))),
        }
    }
    
    /// Get help text for commands
    pub fn help_text() -> &'static str {
        r#"
=== ArxOS Building Explorer Commands ===

MOVEMENT:
  n/north, s/south, e/east, w/west - Move in direction
  u/up, d/down                     - Move between floors
  go <place>                       - Go to specific location

EXPLORATION:
  l/look                           - Look around current location
  x/examine <object>               - Examine something closely
  search                           - Search the area

INTERACTION:
  use <object>                     - Use or activate something
  take <object>                    - Pick up an object
  drop <object>                    - Drop an object

COMMUNICATION:
  say <message>                    - Say something locally
  broadcast <message>              - Broadcast to entire building

REPORTING:
  report <issue>                   - Report a maintenance issue
  alert <emergency>                - Send emergency alert

SYSTEM:
  h/help                           - Show this help
  m/map                            - Show building map
  status                           - Show your status
  q/quit                           - Exit the explorer

SHORTCUTS:
  Single letters work for most commands (n, s, e, w, l, x, h, m, q)
        "#
    }
}

impl Command {
    /// Execute command on the world
    pub fn execute(&self, world: &mut World) -> Result<String> {
        match self {
            Command::Move(dir) => world.move_player(*dir),
            
            Command::Go(place) => {
                Ok(format!("You can't go to '{}' from here", place))
            }
            
            Command::Look => Ok(world.render_view()),
            
            Command::Examine(target) => world.examine(target),
            
            Command::Search => {
                Ok("You search the area carefully but find nothing new.".to_string())
            }
            
            Command::Use(object) => {
                Ok(format!("You can't use the {} right now", object))
            }
            
            Command::Take(object) => {
                Ok(format!("You can't take the {}", object))
            }
            
            Command::Drop(object) => {
                Ok(format!("You don't have a {}", object))
            }
            
            Command::Say(message) => {
                Ok(format!("You say: \"{}\"", message))
            }
            
            Command::Broadcast(message) => {
                Ok(format!("📡 Broadcasting: {}", message))
            }
            
            Command::Report(issue) => {
                Ok(format!("✅ Reported: {} (Work order #{})", issue, rand::random::<u16>()))
            }
            
            Command::Alert(emergency) => {
                Ok(format!("🚨 ALERT SENT: {}", emergency.to_uppercase()))
            }
            
            Command::Help => Ok(CommandParser::help_text().to_string()),
            
            Command::Map => {
                Ok("Building map not yet implemented".to_string())
            }
            
            Command::Status => {
                Ok(format!("Position: ({:.1}m, {:.1}m, {:.1}m)",
                    world.player_position().0 as f32 / 1000.0,
                    world.player_position().1 as f32 / 1000.0,
                    world.player_position().2 as f32 / 1000.0))
            }
            
            Command::Quit => {
                Ok("Goodbye!".to_string())
            }
        }
    }
    
    /// Check if this command should quit the game
    pub fn is_quit(&self) -> bool {
        matches!(self, Command::Quit)
    }
}

// Import rand for work order numbers
