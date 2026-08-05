//! Arx CLI — objects, capture, networking, spatial, interop, scoring.

mod args;
mod commands;
mod util;

use anyhow::Result;
use clap::Parser;

use args::{Cli, Commands};

fn main() -> Result<()> {
    let cli = Cli::parse();

    // Async net commands need a runtime.
    if matches!(cli.command, Commands::Net { .. }) {
        let rt = tokio::runtime::Runtime::new()?;
        return rt.block_on(commands::run_async(cli));
    }

    commands::run_sync(cli)
}
