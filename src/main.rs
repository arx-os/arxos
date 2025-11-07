// Module declarations - aligned with lib.rs for consistency

// Core modules (foundational)
pub mod cli;
pub mod config;
pub mod core;
pub mod error;

// Domain modules (business logic)
pub mod domain;
pub mod git;
pub mod ifc;
pub mod render;
pub mod render3d;
pub mod spatial;

// Integration modules (external systems)
pub mod ar_integration;
pub mod hardware;
pub mod mobile_ffi;

// Data modules (serialization/persistence)
pub mod export;
pub mod persistence;
pub mod yaml;

// Application modules (commands, utilities, features)
pub mod commands;
pub mod docs;
pub mod game;
pub mod identity;
pub mod query;
pub mod search;
pub mod utils;

// Service layer (business logic abstraction)
pub mod services;

// UI module (terminal user interface)
pub mod ui;

use clap::Parser;
use cli::Cli;
use log::info;

// All command handlers have been moved to src/commands/
// All utilities have been moved to src/utils/

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    env_logger::init();

    info!("Starting ArxOS v2.0");

    // Parse CLI arguments
    let cli = Cli::parse();

    // Execute command via command router
    match commands::execute_command(cli.command) {
        Ok(()) => {
            info!("Command completed successfully");
            Ok(())
        }
        Err(e) => {
            eprintln!("❌ Error: {}", e);
            eprintln!("\n💡 For help, run: arx --help");
            eprintln!("📚 For documentation, see: docs/USER_GUIDE.md");
            Err(e)
        }
    }
}
