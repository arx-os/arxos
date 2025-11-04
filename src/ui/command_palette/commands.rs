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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_load_commands() {
        let commands = load_commands();
        assert!(!commands.is_empty(), "Should load commands");
    }

    #[test]
    fn test_command_count() {
        let commands = load_commands();
        // Should have at least 20 commands based on the implementation
        assert!(commands.len() >= 20, "Should have multiple commands");
    }

    #[test]
    fn test_commands_by_category() {
        let commands = load_commands();
        let building: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Building)
            .collect();
        let equipment: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Equipment)
            .collect();
        let room: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Room)
            .collect();
        let git: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Git)
            .collect();
        let ar: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::AR)
            .collect();
        
        assert!(!building.is_empty(), "Should have Building commands");
        assert!(!equipment.is_empty(), "Should have Equipment commands");
        assert!(!room.is_empty(), "Should have Room commands");
        assert!(!git.is_empty(), "Should have Git commands");
        assert!(!ar.is_empty(), "Should have AR commands");
    }

    #[test]
    fn test_command_structure() {
        let commands = load_commands();
        for cmd in &commands {
            assert!(!cmd.name.is_empty(), "Command should have a name");
            assert!(!cmd.full_command.is_empty(), "Command should have full_command");
            assert!(!cmd.description.is_empty(), "Command should have description");
        }
    }

    #[test]
    fn test_no_duplicate_commands() {
        let commands = load_commands();
        let mut names: std::collections::HashSet<String> = std::collections::HashSet::new();
        for cmd in &commands {
            assert!(!names.contains(&cmd.name), 
                "Duplicate command name: {}", cmd.name);
            names.insert(cmd.name.clone());
        }
    }

    #[test]
    fn test_building_commands() {
        let commands = load_commands();
        let building_cmds: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Building)
            .collect();
        assert!(!building_cmds.is_empty(), "Should have Building category commands");
        assert!(building_cmds.iter().any(|c| c.name == "init"), 
            "Should have 'init' command");
    }

    #[test]
    fn test_equipment_commands() {
        let commands = load_commands();
        let equipment_cmds: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Equipment)
            .collect();
        assert!(!equipment_cmds.is_empty(), "Should have Equipment category commands");
        assert!(equipment_cmds.iter().any(|c| c.name.contains("equipment")), 
            "Should have equipment-related commands");
    }

    #[test]
    fn test_room_commands() {
        let commands = load_commands();
        let room_cmds: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Room)
            .collect();
        assert!(!room_cmds.is_empty(), "Should have Room category commands");
        assert!(room_cmds.iter().any(|c| c.name.contains("room")), 
            "Should have room-related commands");
    }

    #[test]
    fn test_git_commands() {
        let commands = load_commands();
        let git_cmds: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::Git)
            .collect();
        assert!(!git_cmds.is_empty(), "Should have Git category commands");
        assert!(git_cmds.iter().any(|c| c.name == "status" || c.name == "commit"), 
            "Should have git-related commands");
    }

    #[test]
    fn test_ar_commands() {
        let commands = load_commands();
        let ar_cmds: Vec<_> = commands.iter()
            .filter(|c| c.category == CommandCategory::AR)
            .collect();
        assert!(!ar_cmds.is_empty(), "Should have AR category commands");
        assert!(ar_cmds.iter().any(|c| c.name.contains("ar")), 
            "Should have AR-related commands");
    }

    #[test]
    fn test_all_categories_represented() {
        let commands = load_commands();
        let categories: std::collections::HashSet<_> = commands.iter()
            .map(|c| c.category)
            .collect();
        
        // Check that major categories are represented (Other may not have commands)
        assert!(categories.contains(&CommandCategory::Building));
        assert!(categories.contains(&CommandCategory::Equipment));
        assert!(categories.contains(&CommandCategory::Room));
        assert!(categories.contains(&CommandCategory::Git));
        assert!(categories.contains(&CommandCategory::ImportExport));
        assert!(categories.contains(&CommandCategory::AR));
        assert!(categories.contains(&CommandCategory::Render));
        assert!(categories.contains(&CommandCategory::Search));
        assert!(categories.contains(&CommandCategory::Config));
        assert!(categories.contains(&CommandCategory::Sensors));
        assert!(categories.contains(&CommandCategory::Health));
        assert!(categories.contains(&CommandCategory::Documentation));
        // Other category may not have commands, which is fine
    }
}

