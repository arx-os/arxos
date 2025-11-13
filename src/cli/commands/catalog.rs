//! Command categories for CLI organization

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandEntry {
    pub name: String,
    pub description: String,
    pub category: CommandCategory,
    pub example: Option<String>,
}

pub fn all_commands() -> Vec<CommandEntry> {
    vec![
        CommandEntry {
            name: "init".to_string(),
            description: "Initialize a new building".to_string(),
            category: CommandCategory::Building,
            example: Some("arx init --name 'My Building'".to_string()),
        },
        CommandEntry {
            name: "render".to_string(),
            description: "Render building visualization".to_string(),
            category: CommandCategory::Render,
            example: Some("arx render --building test --interactive".to_string()),
        },
        CommandEntry {
            name: "import".to_string(),
            description: "Import IFC file".to_string(),
            category: CommandCategory::ImportExport,
            example: Some("arx import building.ifc".to_string()),
        },
        // Add more commands as needed
    ]
}