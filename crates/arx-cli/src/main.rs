mod cli;
#[cfg(feature = "render3d")]
mod render_3d;
mod tui;
mod utils;

use crate::cli::Cli;
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
            Err(e.into())
        }
    }
}
