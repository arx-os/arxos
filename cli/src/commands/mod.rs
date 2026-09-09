//! Command dispatch for the `arx` CLI.

use anyhow::Result;

use crate::args::{Cli, Commands};

mod building;
mod capture;
mod debug;
mod export;
mod inbox;
mod merge;
mod net;
mod spatial;

pub async fn run_async(mut cli: Cli) -> Result<()> {
    let command = std::mem::replace(&mut cli.command, Commands::Version);
    match command {
        Commands::Net { command } => net::run(&cli, command).await,
        _ => unreachable!("async_main only for Net"),
    }
}

pub fn run_sync(mut cli: Cli) -> Result<()> {
    let command = std::mem::replace(&mut cli.command, Commands::Version);
    match command {
        Commands::Version => debug::version(),
        Commands::Key { command } => debug::key(&cli, command),
        Commands::Building { command } => building::run(&cli, command),
        Commands::Entity { command } => building::entity(&cli, command),
        Commands::Inbox { command } => inbox::run(&cli, command),
        Commands::Capture { command } => capture::run(&cli, command),
        Commands::Object { command } => debug::object(&cli, command),
        Commands::Root { command } => debug::root(&cli, command),
        Commands::Net { .. } => unreachable!("net commands are async"),
        Commands::Spatial { command } => spatial::run(&cli, command),
        Commands::Merge { command } => merge::run(&cli, command),
        Commands::Export { command } => export::export(&cli, command),
        Commands::Score {
            building_id,
            root,
            json,
        } => debug::score(&cli, building_id, root, json),
        Commands::Verify { root, json } => debug::verify(&cli, root, json),
        Commands::Attest {
            root,
            device_id,
            sign,
        } => debug::attest(&cli, root, device_id, sign),
        Commands::Import { command } => export::import(&cli, command),
    }
}
