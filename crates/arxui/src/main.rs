mod cli;
mod commands;
mod docs;
mod render;
#[cfg(feature = "render3d")]
mod render3d;
mod tui;

pub use arx::{config, core, depin, domain, error, git, ifc, persistence, spatial, utils, yaml};
pub use arxos::{ar_integration, export, game, hardware, mobile_ffi, query, search, services};
#[cfg(feature = "render3d")]
pub use render3d::*;
pub use {docs::generate_building_docs, render::BuildingRenderer, tui::*};

use crate::cli::Cli;
use clap::Parser;
use log::info;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    info!("Starting ArxUI");

    let cli = Cli::parse();

    match commands::execute_command(cli.command) {
        Ok(()) => {
            info!("Command completed successfully");
            Ok(())
        }
        Err(e) => {
            eprintln!("❌ Error: {}", e);
            eprintln!("\n💡 For help, run: arxui --help");
            Err(e)
        }
    }
}
