use serde::Serialize;

/// High-level category for a command.
#[derive(Debug, Clone, Copy, Serialize)]
pub enum CommandCategory {
    Building,
    Equipment,
    Room,
    Git,
    ImportExport,
    AR,
    Render,
    Search,
    Config,
    Sensors,
    Health,
    Documentation,
    Other,
}

impl CommandCategory {
    /// Human-friendly label.
    pub const fn name(self) -> &'static str {
        match self {
            CommandCategory::Building => "Building",
            CommandCategory::Equipment => "Equipment",
            CommandCategory::Room => "Room",
            CommandCategory::Git => "Git",
            CommandCategory::ImportExport => "Import/Export",
            CommandCategory::AR => "AR",
            CommandCategory::Render => "Render",
            CommandCategory::Search => "Search",
            CommandCategory::Config => "Config",
            CommandCategory::Sensors => "Sensors",
            CommandCategory::Health => "Health",
            CommandCategory::Documentation => "Documentation",
            CommandCategory::Other => "Other",
        }
    }
}

/// Availability of a command across the different surfaces.
#[derive(Debug, Clone, Copy, Serialize)]
pub struct CommandAvailability {
    pub cli: bool,
    pub pwa: bool,
    pub agent: bool,
}

impl CommandAvailability {
    pub const fn new(cli: bool, pwa: bool, agent: bool) -> Self {
        Self { cli, pwa, agent }
    }
}

/// Descriptor for a command palette entry.
#[derive(Debug, Clone, Serialize)]
pub struct CommandDescriptor {
    pub name: &'static str,
    pub full_command: &'static str,
    pub description: &'static str,
    pub category: CommandCategory,
    pub shortcut: Option<&'static str>,
    pub tags: &'static [&'static str],
    pub availability: CommandAvailability,
}

static COMMANDS: &[CommandDescriptor] = &[
    // Building
    CommandDescriptor {
        name: "init",
        full_command: "arxos init",
        description: "Initialize a new building project",
        category: CommandCategory::Building,
        shortcut: None,
        tags: &["setup", "project"],
        availability: CommandAvailability::new(true, false, false),
    },
    CommandDescriptor {
        name: "import",
        full_command: "arxos import <ifc_file>",
        description: "Import IFC file into building",
        category: CommandCategory::ImportExport,
        shortcut: None,
        tags: &["ifc", "ingest", "data"],
        availability: CommandAvailability::new(true, true, true),
    },
    CommandDescriptor {
        name: "export",
        full_command: "arxos export --format <format>",
        description: "Export building data to various formats",
        category: CommandCategory::ImportExport,
        shortcut: None,
        tags: &["ifc", "yaml", "data"],
        availability: CommandAvailability::new(true, true, true),
    },
    // Equipment
    CommandDescriptor {
        name: "equipment list",
        full_command: "arxos equipment list",
        description: "List all equipment",
        category: CommandCategory::Equipment,
        shortcut: None,
        tags: &["equipment", "report"],
        availability: CommandAvailability::new(true, true, false),
    },
    CommandDescriptor {
        name: "equipment browser",
        full_command: "arxos equipment browser",
        description: "Interactive equipment browser",
        category: CommandCategory::Equipment,
        shortcut: None,
        tags: &["equipment", "ui"],
        availability: CommandAvailability::new(true, true, false),
    },
    CommandDescriptor {
        name: "equipment add",
        full_command: "arxos equipment add",
        description: "Add new equipment",
        category: CommandCategory::Equipment,
        shortcut: None,
        tags: &["equipment", "edit"],
        availability: CommandAvailability::new(true, false, false),
    },
    // Rooms
    CommandDescriptor {
        name: "room list",
        full_command: "arxos room list",
        description: "List all rooms",
        category: CommandCategory::Room,
        shortcut: None,
        tags: &["rooms", "report"],
        availability: CommandAvailability::new(true, false, false),
    },
    CommandDescriptor {
        name: "room explorer",
        full_command: "arxos room explorer",
        description: "Interactive room explorer",
        category: CommandCategory::Room,
        shortcut: None,
        tags: &["rooms", "ui"],
        availability: CommandAvailability::new(true, true, false),
    },
    // Git
    CommandDescriptor {
        name: "status",
        full_command: "arxos status",
        description: "Show Git status",
        category: CommandCategory::Git,
        shortcut: None,
        tags: &["git", "report"],
        availability: CommandAvailability::new(true, true, true),
    },
    CommandDescriptor {
        name: "commit",
        full_command: "arxos commit --message <msg>",
        description: "Commit changes to Git",
        category: CommandCategory::Git,
        shortcut: None,
        tags: &["git", "changes"],
        availability: CommandAvailability::new(true, true, true),
    },
    CommandDescriptor {
        name: "diff",
        full_command: "arxos diff",
        description: "Show Git diff",
        category: CommandCategory::Git,
        shortcut: None,
        tags: &["git", "changes"],
        availability: CommandAvailability::new(true, true, true),
    },
    // Search
    CommandDescriptor {
        name: "search",
        full_command: "arxos search <query>",
        description: "Search building data",
        category: CommandCategory::Search,
        shortcut: None,
        tags: &["search", "data"],
        availability: CommandAvailability::new(true, true, false),
    },
    CommandDescriptor {
        name: "filter",
        full_command: "arxos filter",
        description: "Filter equipment by criteria",
        category: CommandCategory::Search,
        shortcut: None,
        tags: &["search", "filter"],
        availability: CommandAvailability::new(true, true, false),
    },
    // Render
    CommandDescriptor {
        name: "render",
        full_command: "arxos render",
        description: "Render building visualization",
        category: CommandCategory::Render,
        shortcut: None,
        tags: &["render", "visualization"],
        availability: CommandAvailability::new(true, true, false),
    },
    CommandDescriptor {
        name: "interactive",
        full_command: "arxos interactive",
        description: "Interactive 3D renderer",
        category: CommandCategory::Render,
        shortcut: None,
        tags: &["render", "3d"],
        availability: CommandAvailability::new(true, true, false),
    },
    // AR
    CommandDescriptor {
        name: "ar integrate",
        full_command: "arxos ar integrate",
        description: "Integrate AR scan data",
        category: CommandCategory::AR,
        shortcut: None,
        tags: &["ar", "scan"],
        availability: CommandAvailability::new(true, true, true),
    },
    CommandDescriptor {
        name: "ar pending",
        full_command: "arxos ar pending",
        description: "Manage pending AR equipment",
        category: CommandCategory::AR,
        shortcut: None,
        tags: &["ar", "review"],
        availability: CommandAvailability::new(true, true, true),
    },
    // Config
    CommandDescriptor {
        name: "config",
        full_command: "arxos config",
        description: "Manage configuration",
        category: CommandCategory::Config,
        shortcut: None,
        tags: &["config", "settings"],
        availability: CommandAvailability::new(true, false, false),
    },
    CommandDescriptor {
        name: "config wizard",
        full_command: "arxos config --interactive",
        description: "Interactive configuration wizard",
        category: CommandCategory::Config,
        shortcut: None,
        tags: &["config", "wizard"],
        availability: CommandAvailability::new(true, false, false),
    },
    // Sensors
    CommandDescriptor {
        name: "sensors process",
        full_command: "arxos sensors process",
        description: "Process sensor data",
        category: CommandCategory::Sensors,
        shortcut: None,
        tags: &["sensors", "ingest"],
        availability: CommandAvailability::new(true, false, true),
    },
    CommandDescriptor {
        name: "watch",
        full_command: "arxos watch",
        description: "Watch building data in real-time",
        category: CommandCategory::Sensors,
        shortcut: None,
        tags: &["monitoring", "sensors"],
        availability: CommandAvailability::new(true, true, true),
    },
    // Health
    CommandDescriptor {
        name: "health",
        full_command: "arxos health",
        description: "Check system health",
        category: CommandCategory::Health,
        shortcut: None,
        tags: &["health", "status"],
        availability: CommandAvailability::new(true, true, true),
    },
    CommandDescriptor {
        name: "validate",
        full_command: "arxos validate",
        description: "Validate building data",
        category: CommandCategory::Health,
        shortcut: None,
        tags: &["validate", "quality"],
        availability: CommandAvailability::new(true, false, true),
    },
    // Documentation
    CommandDescriptor {
        name: "doc",
        full_command: "arxos doc",
        description: "Generate documentation",
        category: CommandCategory::Documentation,
        shortcut: None,
        tags: &["docs", "export"],
        availability: CommandAvailability::new(true, false, false),
    },
];

/// Retrieve all command descriptors.
pub fn all_commands() -> &'static [CommandDescriptor] {
    COMMANDS
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn commands_have_metadata() {
        assert!(!COMMANDS.is_empty());
        for command in COMMANDS {
            assert!(!command.name.is_empty());
            assert!(!command.description.is_empty());
            assert!(
                !command.full_command.is_empty(),
                "full command missing for {}",
                command.name
            );
            assert!(
                command.tags.iter().all(|tag| !tag.is_empty()),
                "tags must not be empty for {}",
                command.name
            );
            let availability = command.availability;
            assert!(
                availability.cli || availability.pwa || availability.agent,
                "command {} must be available somewhere",
                command.name
            );
        }
    }
}
