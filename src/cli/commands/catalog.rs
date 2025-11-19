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
        // Building commands
        CommandEntry {
            name: "init".to_string(),
            description: "Initialize a new building from scratch".to_string(),
            category: CommandCategory::Building,
            example: Some("arx init --name 'My Building'".to_string()),
        },
        CommandEntry {
            name: "validate".to_string(),
            description: "Validate building data structure".to_string(),
            category: CommandCategory::Building,
            example: Some("arx validate".to_string()),
        },
        CommandEntry {
            name: "status".to_string(),
            description: "Show building status and summary".to_string(),
            category: CommandCategory::Building,
            example: Some("arx status".to_string()),
        },
        // Import/Export commands
        CommandEntry {
            name: "import".to_string(),
            description: "Import IFC file to Git repository".to_string(),
            category: CommandCategory::ImportExport,
            example: Some("arx import building.ifc".to_string()),
        },
        CommandEntry {
            name: "export".to_string(),
            description: "Export building data to various formats".to_string(),
            category: CommandCategory::ImportExport,
            example: Some("arx export --format ifc --output building.ifc".to_string()),
        },
        CommandEntry {
            name: "sync".to_string(),
            description: "Sync building data to IFC file".to_string(),
            category: CommandCategory::ImportExport,
            example: Some("arx sync --ifc building.ifc".to_string()),
        },
        // Render commands
        CommandEntry {
            name: "render".to_string(),
            description: "Render building visualization".to_string(),
            category: CommandCategory::Render,
            example: Some("arx render --building test --interactive".to_string()),
        },
        CommandEntry {
            name: "interactive".to_string(),
            description: "Interactive 3D building visualization".to_string(),
            category: CommandCategory::Render,
            example: Some("arx interactive --building test".to_string()),
        },
        // Git commands
        CommandEntry {
            name: "stage".to_string(),
            description: "Stage changes for commit".to_string(),
            category: CommandCategory::Git,
            example: Some("arx stage".to_string()),
        },
        CommandEntry {
            name: "commit".to_string(),
            description: "Commit staged changes".to_string(),
            category: CommandCategory::Git,
            example: Some("arx commit -m 'Update equipment'".to_string()),
        },
        CommandEntry {
            name: "unstage".to_string(),
            description: "Unstage changes".to_string(),
            category: CommandCategory::Git,
            example: Some("arx unstage".to_string()),
        },
        CommandEntry {
            name: "diff".to_string(),
            description: "Show differences between versions".to_string(),
            category: CommandCategory::Git,
            example: Some("arx diff".to_string()),
        },
        CommandEntry {
            name: "history".to_string(),
            description: "Show commit history".to_string(),
            category: CommandCategory::Git,
            example: Some("arx history".to_string()),
        },
        // Room commands
        CommandEntry {
            name: "room".to_string(),
            description: "Manage rooms in the building".to_string(),
            category: CommandCategory::Room,
            example: Some("arx room create --name 'Server Room'".to_string()),
        },
        // Equipment commands
        CommandEntry {
            name: "equipment".to_string(),
            description: "Manage building equipment".to_string(),
            category: CommandCategory::Equipment,
            example: Some("arx equipment add --type HVAC --room 'Mechanical'".to_string()),
        },
        // Search commands
        CommandEntry {
            name: "search".to_string(),
            description: "Search for equipment, rooms, or other entities".to_string(),
            category: CommandCategory::Search,
            example: Some("arx search --query 'HVAC'".to_string()),
        },
        CommandEntry {
            name: "query".to_string(),
            description: "Query building data with filters".to_string(),
            category: CommandCategory::Search,
            example: Some("arx query --type equipment --status active".to_string()),
        },
        CommandEntry {
            name: "spatial".to_string(),
            description: "Spatial queries and analysis".to_string(),
            category: CommandCategory::Search,
            example: Some("arx spatial --near 'Room 101'".to_string()),
        },
        // AR commands
        CommandEntry {
            name: "ar".to_string(),
            description: "AR integration and point cloud processing".to_string(),
            category: CommandCategory::AR,
            example: Some("arx ar --scan point-cloud.ply".to_string()),
        },
        CommandEntry {
            name: "ar-integrate".to_string(),
            description: "Integrate AR scan data into building model".to_string(),
            category: CommandCategory::AR,
            example: Some("arx ar-integrate --scan data.ply".to_string()),
        },
        // Sensor commands
        CommandEntry {
            name: "process-sensors".to_string(),
            description: "Process sensor data".to_string(),
            category: CommandCategory::Sensors,
            example: Some("arx process-sensors".to_string()),
        },
        CommandEntry {
            name: "sensors-http".to_string(),
            description: "Start HTTP server for sensor data ingestion".to_string(),
            category: CommandCategory::Sensors,
            example: Some("arx sensors-http --port 8080".to_string()),
        },
        CommandEntry {
            name: "sensors-mqtt".to_string(),
            description: "Subscribe to MQTT sensor feeds".to_string(),
            category: CommandCategory::Sensors,
            example: Some("arx sensors-mqtt --broker mqtt://localhost".to_string()),
        },
        // Health & Documentation
        CommandEntry {
            name: "health".to_string(),
            description: "Check system health and diagnostics".to_string(),
            category: CommandCategory::Health,
            example: Some("arx health".to_string()),
        },
        CommandEntry {
            name: "doc".to_string(),
            description: "Generate or view documentation".to_string(),
            category: CommandCategory::Documentation,
            example: Some("arx doc".to_string()),
        },
        // Config
        CommandEntry {
            name: "config".to_string(),
            description: "Manage ArxOS configuration".to_string(),
            category: CommandCategory::Config,
            example: Some("arx config --set key=value".to_string()),
        },
    ]
}