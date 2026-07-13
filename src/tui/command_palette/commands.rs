//! Command definitions for the TUI palette (Building compiler surface only).

use super::types::{CommandCategory, CommandEntry};

/// Load palette entries for supported compiler commands.
pub fn load_commands() -> Vec<CommandEntry> {
    vec![
        entry(
            "init",
            "arx init --name 'My Building'",
            "Initialize a new building repository",
            CommandCategory::Building,
        ),
        entry(
            "import",
            "arx import ifc building.ifc",
            "Import IFC or LiDAR into building.yaml",
            CommandCategory::ImportExport,
        ),
        entry(
            "edit",
            "arx edit script.txt",
            "Apply text/AR edit script to Building",
            CommandCategory::Building,
        ),
        entry(
            "export",
            "arx export --format ifc --output building.ifc",
            "Export Building to IFC/YAML/JSON",
            CommandCategory::ImportExport,
        ),
        entry(
            "validate",
            "arx validate",
            "Validate building.yaml invariants",
            CommandCategory::Health,
        ),
        entry(
            "status",
            "arx status",
            "Show Git status for building SSOT",
            CommandCategory::Git,
        ),
        entry(
            "stage",
            "arx stage",
            "Stage building.yaml changes",
            CommandCategory::Git,
        ),
        entry(
            "commit",
            "arx commit -m 'message'",
            "Commit staged changes",
            CommandCategory::Git,
        ),
        entry("diff", "arx diff", "Show differences", CommandCategory::Git),
        entry(
            "history",
            "arx history",
            "Show commit history",
            CommandCategory::Git,
        ),
        entry(
            "room",
            "arx room create --name Office",
            "Manage rooms on Building graph",
            CommandCategory::Room,
        ),
        entry(
            "equipment",
            "arx equipment add --name Boiler",
            "Manage equipment on Building graph",
            CommandCategory::Equipment,
        ),
        entry(
            "query",
            "arx query '/local/*/*/*/*/*/*'",
            "Query equipment by durable ArxAddress",
            CommandCategory::Search,
        ),
        entry(
            "search",
            "arx search boiler",
            "Search names in Building",
            CommandCategory::Search,
        ),
        entry(
            "migrate",
            "arx migrate",
            "Backfill missing equipment addresses",
            CommandCategory::Building,
        ),
        entry(
            "render",
            "arx render --building .",
            "Visualize building",
            CommandCategory::Render,
        ),
        entry(
            "spatial",
            "arx spatial",
            "Spatial operations",
            CommandCategory::Other,
        ),
    ]
}

fn entry(name: &str, full: &str, description: &str, category: CommandCategory) -> CommandEntry {
    CommandEntry {
        name: name.to_string(),
        full_command: full.to_string(),
        description: description.to_string(),
        category,
        shortcut: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_load_commands() {
        let commands = load_commands();
        assert!(!commands.is_empty());
        assert!(commands.iter().any(|c| c.name == "query"));
        assert!(commands.iter().any(|c| c.name == "migrate"));
        // Compiler surface is intentionally smaller than the old kitchen-sink palette
        assert!(commands.len() >= 10);
        assert!(commands.len() < 30);
    }
}
