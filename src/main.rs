pub mod core;
pub mod cli;
pub mod config;
pub mod error;
pub mod spatial;
pub mod git;
pub mod ifc;
pub mod progress;
pub mod render;
pub mod render3d;
pub mod ar_integration;
pub mod yaml;
pub mod path;
pub mod search;
pub mod persistence;
pub mod hardware;
pub mod commands;
pub mod utils;

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
            eprintln!("\n💡 For help, run: arxos --help");
            eprintln!("📚 For documentation, see: docs/USER_GUIDE.md");
            Err(e)
        }
    }
}
