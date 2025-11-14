//! Command Definitions
//!
//! Provides all available commands for the command palette.

use super::types::{CommandCategory, CommandEntry};

/// Load all available commands
pub fn load_commands() -> Vec<CommandEntry> {
    crate::cli::commands::all_commands()
        .into_iter()
        .map(|descriptor| CommandEntry {
            name: descriptor.name.clone(),
            full_command: descriptor.example.unwrap_or_else(|| format!("arx {}", descriptor.name)),
            description: descriptor.description,
            category: CommandCategory::from(descriptor.category),
            shortcut: None,
        })
        .collect()
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
        let building: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Building)
            .collect();
        let equipment: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Equipment)
            .collect();
        let room: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Room)
            .collect();
        let git: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Git)
            .collect();
        let ar: Vec<_> = commands
            .iter()
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
            assert!(
                !cmd.full_command.is_empty(),
                "Command should have full_command"
            );
            assert!(
                !cmd.description.is_empty(),
                "Command should have description"
            );
        }
    }

    #[test]
    fn test_no_duplicate_commands() {
        let commands = load_commands();
        let mut names: std::collections::HashSet<String> = std::collections::HashSet::new();
        for cmd in &commands {
            assert!(
                !names.contains(&cmd.name),
                "Duplicate command name: {}",
                cmd.name
            );
            names.insert(cmd.name.clone());
        }
    }

    #[test]
    fn test_building_commands() {
        let commands = load_commands();
        let building_cmds: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Building)
            .collect();
        assert!(
            !building_cmds.is_empty(),
            "Should have Building category commands"
        );
        assert!(
            building_cmds.iter().any(|c| c.name == "init"),
            "Should have 'init' command"
        );
    }

    #[test]
    fn test_equipment_commands() {
        let commands = load_commands();
        let equipment_cmds: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Equipment)
            .collect();
        assert!(
            !equipment_cmds.is_empty(),
            "Should have Equipment category commands"
        );
        assert!(
            equipment_cmds.iter().any(|c| c.name.contains("equipment")),
            "Should have equipment-related commands"
        );
    }

    #[test]
    fn test_room_commands() {
        let commands = load_commands();
        let room_cmds: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Room)
            .collect();
        assert!(!room_cmds.is_empty(), "Should have Room category commands");
        assert!(
            room_cmds.iter().any(|c| c.name.contains("room")),
            "Should have room-related commands"
        );
    }

    #[test]
    fn test_git_commands() {
        let commands = load_commands();
        let git_cmds: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::Git)
            .collect();
        assert!(!git_cmds.is_empty(), "Should have Git category commands");
        assert!(
            git_cmds
                .iter()
                .any(|c| c.name == "status" || c.name == "commit"),
            "Should have git-related commands"
        );
    }

    #[test]
    fn test_ar_commands() {
        let commands = load_commands();
        let ar_cmds: Vec<_> = commands
            .iter()
            .filter(|c| c.category == CommandCategory::AR)
            .collect();
        assert!(!ar_cmds.is_empty(), "Should have AR category commands");
        assert!(
            ar_cmds.iter().any(|c| c.name.contains("ar")),
            "Should have AR-related commands"
        );
    }

    #[test]
    fn test_all_categories_represented() {
        let commands = load_commands();
        let categories: std::collections::HashSet<_> =
            commands.iter().map(|c| c.category).collect();

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
