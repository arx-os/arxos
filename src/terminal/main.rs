//! ArxOS Terminal - Lightweight Building Intelligence Interface
//! 
//! Simple terminal for routing building intelligence through mesh networks.
//! No heavy processing - just routing and display.

mod app;
mod meshtastic_client;
mod commands;
mod arxos_commands;

use app::App;
use meshtastic_client::{MeshtasticConfig, load_config, prompt_node_id};
use clap::Parser;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    Terminal,
};
use std::{error::Error, io, time::Duration};
use log::{error, info};

/// Arxos Terminal command-line arguments
#[derive(Parser, Debug)]
#[command(author, version, about = "Terminal client for Arxos mesh network", long_about = None)]
struct Args {
    /// Meshtastic node ID
    #[arg(short = 'n', long, default_value = "1")]
    node_id: u32,
    
    /// Radio frequency in MHz
    #[arg(short = 'f', long, default_value = "915.0")]
    frequency: f32,
    
    /// Radio region
    #[arg(short = 'r', long, default_value = "US")]
    region: String,
    
    /// Configuration file path
    #[arg(short, long)]
    config: Option<String>,
    
    /// Auto-connect on startup
    #[arg(short = 'a', long)]
    auto_connect: bool,
    
    /// Verbose logging
    #[arg(short, long)]
    verbose: bool,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Parse arguments
    let args = Args::parse();
    
    // Initialize logging
    let log_level = if args.verbose { "debug" } else { "info" };
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or(log_level))
        .init();
    
    info!("Starting Arxos Terminal Client");
    
    // Load or create meshtastic configuration
    let meshtastic_config = if let Some(config_path) = args.config {
        load_config(Some(&config_path)).await?
    } else {
        // Build config from arguments
        MeshtasticConfig {
            node_id: args.node_id,
            frequency_mhz: args.frequency,
            region: args.region,
            timeout_seconds: 30,
            retry_attempts: 3,
        }
    };
    
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    
    // Create app
    let mut app = App::new(meshtastic_config);
    
    // Auto-connect if requested
    if args.auto_connect {
        info!("Auto-connecting to meshtastic network...");
        if let Err(e) = app.connect().await {
            error!("Auto-connect failed: {}", e);
            app.add_output(format!("Auto-connect failed: {}", e));
        }
    } else {
        app.add_output("Welcome to Arxos Terminal!".to_string());
        app.add_output("Type 'connect' to connect to the meshtastic network.".to_string());
        app.add_output("Type 'help' for available commands.".to_string());
    }
    
    // Run the app
    let res = run_app(&mut terminal, app).await;
    
    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;
    
    if let Err(err) = res {
        error!("Application error: {}", err);
        println!("Error: {}", err);
    }
    
    info!("Arxos Terminal Client stopped");
    Ok(())
}

/// Main application loop
async fn run_app<B: Backend>(
    terminal: &mut Terminal<B>,
    mut app: App,
) -> Result<(), Box<dyn Error>> {
    loop {
        // Draw UI
        terminal.draw(|f| app.render(f))?;
        
        // Check if we should quit
        if app.should_quit {
            break;
        }
        
        // Handle events with timeout for async operations
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    app.handle_key(key).await;
                }
            }
        }
        
        // Process any pending meshtastic data
        // This would be done in a separate task in production
        // For now, we poll in the main loop
    }
    
    Ok(())
}

/// Print usage information
fn print_usage() {
    println!("╔════════════════════════════════════════╗");
    println!("║     Arxos Terminal - Meshtastic Client  ║");
    println!("╚════════════════════════════════════════╝");
    println!();
    println!("Usage: arxos [OPTIONS]");
    println!();
    println!("Options:");
    println!("  -n, --node-id <ID>     Meshtastic node ID [default: 1]");
    println!("  -f, --frequency <MHz>  Radio frequency [default: 915.0]");
    println!("  -r, --region <REGION>  Radio region [default: US]");
    println!("  -c, --config <PATH>    Configuration file path");
    println!("  -a, --auto-connect     Auto-connect on startup");
    println!("  -v, --verbose          Enable verbose logging");
    println!("  -h, --help             Print help");
    println!();
    println!("Examples:");
    println!("  # Connect with default settings");
    println!("  arxos");
    println!();
    println!("  # Connect with custom node ID");
    println!("  arxos -n 42 -f 868.0 -r EU");
    println!();
    println!("  # Auto-connect with config file");
    println!("  arxos -c ~/.config/arxos/terminal.toml -a");
}