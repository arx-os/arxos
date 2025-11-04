//! Command Definitions
//!
//! Provides all available commands for the command palette.

use super::types::{CommandEntry, CommandCategory};

/// Load all available commands
pub fn load_commands() -> Vec<CommandEntry> {
    vec![
        // Building Management
        CommandEntry {
            name: "init".to_string(),
            full_command: "arxos init".to_string(),
            description: "Initialize a new building project".to_string(),
            category: CommandCategory::Building,
            shortcut: None,
        },
        CommandEntry {
            name: "import".to_string(),
            full_command: "arxos import <ifc_file>".to_string(),
            description: "Import IFC file into building".to_string(),
            category: CommandCategory::ImportExport,
            shortcut: None,
        },
        CommandEntry {
            name: "export".to_string(),
            full_command: "arxos export --format <format>".to_string(),
            description: "Export building data to various formats".to_string(),
            category: CommandCategory::ImportExport,
            shortcut: None,
        },
        
        // Equipment
        CommandEntry {
            name: "equipment list".to_string(),
            full_command: "arxos equipment list".to_string(),
            description: "List all equipment".to_string(),
            category: CommandCategory::Equipment,
            shortcut: None,
        },
        CommandEntry {
            name: "equipment browser".to_string(),
            full_command: "arxos equipment browser".to_string(),
            description: "Interactive equipment browser".to_string(),
            category: CommandCategory::Equipment,
            shortcut: None,
        },
        CommandEntry {
            name: "equipment add".to_string(),
            full_command: "arxos equipment add".to_string(),
            description: "Add new equipment".to_string(),
            category: CommandCategory::Equipment,
            shortcut: None,
        },
        
        // Rooms
        CommandEntry {
            name: "room list".to_string(),
            full_command: "arxos room list".to_string(),
            description: "List all rooms".to_string(),
            category: CommandCategory::Room,
            shortcut: None,
        },
        CommandEntry {
            name: "room explorer".to_string(),
            full_command: "arxos room explorer".to_string(),
            description: "Interactive room explorer".to_string(),
            category: CommandCategory::Room,
            shortcut: None,
        },
        
        // Git Operations
        CommandEntry {
            name: "status".to_string(),
            full_command: "arxos status".to_string(),
            description: "Show Git status".to_string(),
            category: CommandCategory::Git,
            shortcut: None,
        },
        CommandEntry {
            name: "commit".to_string(),
            full_command: "arxos commit --message <msg>".to_string(),
            description: "Commit changes to Git".to_string(),
            category: CommandCategory::Git,
            shortcut: None,
        },
        CommandEntry {
            name: "diff".to_string(),
            full_command: "arxos diff".to_string(),
            description: "Show Git diff".to_string(),
            category: CommandCategory::Git,
            shortcut: None,
        },
        
        // Search
        CommandEntry {
            name: "search".to_string(),
            full_command: "arxos search <query>".to_string(),
            description: "Search building data".to_string(),
            category: CommandCategory::Search,
            shortcut: None,
        },
        CommandEntry {
            name: "filter".to_string(),
            full_command: "arxos filter".to_string(),
            description: "Filter equipment by criteria".to_string(),
            category: CommandCategory::Search,
            shortcut: None,
        },
        
        // Render
        CommandEntry {
            name: "render".to_string(),
            full_command: "arxos render".to_string(),
            description: "Render building visualization".to_string(),
            category: CommandCategory::Render,
            shortcut: None,
        },
        CommandEntry {
            name: "interactive".to_string(),
            full_command: "arxos interactive".to_string(),
            description: "Interactive 3D renderer".to_string(),
            category: CommandCategory::Render,
            shortcut: None,
        },
        
        // AR
        CommandEntry {
            name: "ar integrate".to_string(),
            full_command: "arxos ar integrate".to_string(),
            description: "Integrate AR scan data".to_string(),
            category: CommandCategory::AR,
            shortcut: None,
        },
        CommandEntry {
            name: "ar pending".to_string(),
            full_command: "arxos ar pending".to_string(),
            description: "Manage pending AR equipment".to_string(),
            category: CommandCategory::AR,
            shortcut: None,
        },
        
        // Config
        CommandEntry {
            name: "config".to_string(),
            full_command: "arxos config".to_string(),
            description: "Manage configuration".to_string(),
            category: CommandCategory::Config,
            shortcut: None,
        },
        CommandEntry {
            name: "config wizard".to_string(),
            full_command: "arxos config --interactive".to_string(),
            description: "Interactive configuration wizard".to_string(),
            category: CommandCategory::Config,
            shortcut: None,
        },
        
        // Sensors
        CommandEntry {
            name: "sensors process".to_string(),
            full_command: "arxos sensors process".to_string(),
            description: "Process sensor data".to_string(),
            category: CommandCategory::Sensors,
            shortcut: None,
        },
        CommandEntry {
            name: "watch".to_string(),
            full_command: "arxos watch".to_string(),
            description: "Watch building data in real-time".to_string(),
            category: CommandCategory::Sensors,
            shortcut: None,
        },
        
        // Health
        CommandEntry {
            name: "health".to_string(),
            full_command: "arxos health".to_string(),
            description: "Check system health".to_string(),
            category: CommandCategory::Health,
            shortcut: None,
        },
        CommandEntry {
            name: "validate".to_string(),
            full_command: "arxos validate".to_string(),
            description: "Validate building data".to_string(),
            category: CommandCategory::Health,
            shortcut: None,
        },
        
        // Documentation
        CommandEntry {
            name: "doc".to_string(),
            full_command: "arxos doc".to_string(),
            description: "Generate documentation".to_string(),
            category: CommandCategory::Documentation,
            shortcut: None,
        },
    ]
}

