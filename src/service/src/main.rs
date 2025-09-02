//! ArxOS Service
//!
//! Software-as-a-Service running on Meshtastic hardware
//! Provides building intelligence through standard Meshtastic mesh networks

use anyhow::Result;
use clap::Parser;
use log::info;
use std::path::PathBuf;

mod config;
mod meshtastic_client;
mod protocol_translator;
mod service;
mod terminal_interface;

use config::ServiceConfig;
use service::ArxOSService;

/// ArxOS Service - Building Intelligence on Meshtastic Hardware
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Configuration file path
    #[arg(short, long, default_value = "config.toml")]
    config: PathBuf,

    /// Meshtastic device port
    #[arg(short, long)]
    meshtastic_port: Option<String>,

    /// Log level
    #[arg(short, long, default_value = "info")]
    log_level: String,

    /// Run in daemon mode
    #[arg(short, long)]
    daemon: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // Initialize logging
    env_logger::Builder::from_default_env()
        .filter_level(args.log_level.parse().unwrap_or(log::LevelFilter::Info))
        .init();

    info!("Starting ArxOS Service...");

    // Load configuration
    let mut config = ServiceConfig::load(&args.config)?;
    
    // Override config with command line arguments
    if let Some(port) = args.meshtastic_port {
        config.meshtastic.port = port;
    }

    // Create and start service
    let mut service = ArxOSService::new(config).await?;
    
    if args.daemon {
        info!("Running in daemon mode");
        service.run_daemon().await?;
    } else {
        info!("Running in interactive mode");
        service.run_interactive().await?;
    }

    info!("ArxOS Service stopped");
    Ok(())
}
