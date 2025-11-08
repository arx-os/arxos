//! Command handler implementations for trait-based routing

use super::traits::CommandHandler;
use crate::cli::Commands;
use crate::commands::*;

/// Handler for Init command
pub struct InitHandler;

impl CommandHandler for InitHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Init {
                name,
                description,
                location,
                git_init,
                commit,
                coordinate_system,
                units,
            } => {
                use init::InitConfig;
                init::handle_init(InitConfig {
                    name,
                    description,
                    location,
                    git_init,
                    commit,
                    coordinate_system,
                    units,
                })
            }
            _ => Err("InitHandler can only process Init commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Init"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Init { .. })
    }
}

/// Handler for Import command
pub struct ImportHandler;

impl CommandHandler for ImportHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Import {
                ifc_file,
                repo,
                dry_run,
            } => import::handle_import(ifc_file, repo, dry_run),
            _ => Err("ImportHandler can only process Import commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Import"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Import { .. })
    }
}

/// Handler for Export command
pub struct ExportHandler;

impl CommandHandler for ExportHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Export {
                format,
                output,
                repo,
                delta,
            } => export::handle_export_with_format(format, output, repo, delta),
            _ => Err("ExportHandler can only process Export commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Export"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Export { .. })
    }
}

/// Handler for Sync command
pub struct SyncHandler;

impl CommandHandler for SyncHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Sync { ifc, watch, delta } => sync::handle_sync(ifc, watch, delta),
            _ => Err("SyncHandler can only process Sync commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Sync"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Sync { .. })
    }
}

/// Handler for Validate command
pub struct ValidateHandler;

impl CommandHandler for ValidateHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Validate { path } => validate::handle_validate(path),
            _ => Err("ValidateHandler can only process Validate commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Validate"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Validate { .. })
    }
}

/// Handler for Query command
pub struct QueryHandler;

impl CommandHandler for QueryHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Query {
                pattern,
                format,
                verbose,
            } => query::handle_query_command(pattern, format, verbose),
            _ => Err("QueryHandler can only process Query commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Query"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Query { .. })
    }
}

/// Handler for Migrate command
pub struct MigrateHandler;

impl CommandHandler for MigrateHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Migrate { dry_run } => migrate::handle_migrate_address(dry_run),
            _ => Err("MigrateHandler can only process Migrate commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Migrate"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Migrate { .. })
    }
}

/// Handler for Doc command
pub struct DocHandler;

impl CommandHandler for DocHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Doc { building, output } => doc::handle_doc(building, output),
            _ => Err("DocHandler can only process Doc commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Doc"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Doc { .. })
    }
}

/// Handler for Verify command
pub struct VerifyHandler;

impl CommandHandler for VerifyHandler {
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        match command {
            Commands::Verify {
                commit,
                all,
                verbose,
            } => verify::handle_verify(commit, all, verbose),
            _ => Err("VerifyHandler can only process Verify commands".into()),
        }
    }

    fn command_name(&self) -> &'static str {
        "Verify"
    }

    fn can_handle(&self, command: &Commands) -> bool {
        matches!(command, Commands::Verify { .. })
    }
}
