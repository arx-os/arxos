//! Command registry for statically dispatched command routing

use crate::cli::Commands;
use crate::commands::{
    doc, export, import, init, init::InitConfig, migrate, query, sync, validate, verify,
};

/// Registry that maps command enums to their execution functions
pub struct CommandRegistry;

impl CommandRegistry {
    /// Create a new command registry
    pub fn new() -> Self {
        Self
    }

    /// Determine whether the registry can execute the provided command.
    pub fn can_handle(&self, command: &Commands) -> bool {
        matches!(
            command,
            Commands::Init { .. }
                | Commands::Import { .. }
                | Commands::Export { .. }
                | Commands::Sync { .. }
                | Commands::Validate { .. }
                | Commands::Query { .. }
                | Commands::Migrate { .. }
                | Commands::Doc { .. }
                | Commands::Verify { .. }
        )
    }

    /// Execute a command using direct enum dispatch
    pub fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Init {
                name,
                description,
                location,
                git_init,
                commit,
                coordinate_system,
                units,
            } => init::handle_init(InitConfig {
                name,
                description,
                location,
                git_init,
                commit,
                coordinate_system,
                units,
            }),
            Commands::Import {
                ifc_file,
                repo,
                dry_run,
            } => import::handle_import(ifc_file, repo, dry_run),
            Commands::Export {
                format,
                output,
                repo,
                delta,
            } => export::handle_export_with_format(format, output, repo, delta),
            Commands::Sync { ifc, watch, delta } => sync::handle_sync(ifc, watch, delta),
            Commands::Validate { path } => validate::handle_validate(path),
            Commands::Query {
                pattern,
                format,
                verbose,
            } => query::handle_query_command(pattern, format, verbose),
            Commands::Migrate { dry_run } => migrate::handle_migrate_address(dry_run),
            Commands::Doc { building, output } => doc::handle_doc(building, output),
            Commands::Verify {
                commit,
                all,
                verbose,
            } => verify::handle_verify(commit, all, verbose),
            _ => Err("No handler found for command".into()),
        }
    }
}

impl Default for CommandRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cli::Commands;

    #[test]
    fn matches_simple_commands() {
        let registry = CommandRegistry::new();
        let init_cmd = Commands::Init {
            name: "Test Building".to_string(),
            description: Some("Description".to_string()),
            location: Some("123 Main".to_string()),
            git_init: false,
            commit: false,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
        };

        assert!(registry.can_handle(&init_cmd));
    }

    #[test]
    fn reports_unhandled_command() {
        let registry = CommandRegistry::new();
        let status_cmd = Commands::Status {
            verbose: false,
            interactive: false,
        };

        assert!(!registry.can_handle(&status_cmd));
        let result = registry.execute(status_cmd);
        assert!(result.is_err());
    }
}
