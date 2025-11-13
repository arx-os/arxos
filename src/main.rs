//! ArxOS - Git for Buildings
//! 
//! A unified command-line tool for building data management, 3D visualization,
//! and collaborative workflows using Git as the foundation.

// Core modules (always available)
mod core;
mod domain;
mod error;
mod ifc;
mod git;
mod persistence;
mod sensor;
mod spatial;
mod utils;
mod validation;
mod yaml;
mod cli;

// Feature-gated modules
#[cfg(feature = "tui")]
mod tui;

#[cfg(feature = "render3d")]
mod render3d;

#[cfg(feature = "agent")]
mod agent;

use cli::Cli;
use clap::Parser;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    
    match cli.execute() {
        Ok(()) => {
            println!("✅ Command completed successfully");
            Ok(())
        }
        Err(e) => {
            eprintln!("❌ Error: {}", e);
            eprintln!("\n💡 For help, run: arx --help");
            std::process::exit(1);
        }
    }
}