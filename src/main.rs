// Module declarations - aligned with lib.rs for consistency

// Core modules (foundational)
pub mod core;
pub mod cli;
pub mod config;
pub mod error;

// Domain modules (business logic)
pub mod spatial;
pub mod git;
pub mod ifc;
pub mod progress;
pub mod render;
pub mod render3d;

// Integration modules (external systems)
pub mod ar_integration;
pub mod mobile_ffi;
pub mod hardware;

// Data modules (serialization/persistence)
pub mod yaml;
pub mod path;
pub mod persistence;
pub mod export;

// Application modules (commands, utilities, features)
pub mod commands;
pub mod search;
pub mod utils;
pub mod docs;
pub mod game;

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
