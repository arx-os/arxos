//! ArxOS - Git for Buildings
//!
//! A unified command-line tool for building data management, 3D visualization,
//! and collaborative workflows using Git as the foundation.

use arxos::cli::Cli;
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