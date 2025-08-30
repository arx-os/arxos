//! Arxos Terminal Client with SSH Connectivity
//! 
//! Production terminal that connects to real mesh nodes via SSH

mod app;
mod ssh_client;
mod commands;

use app::{App, AppMode};
use ssh_client::{SshConfig, load_config, prompt_password};
use clap::Parser;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
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
    /// Host to connect to
    #[arg(short = 'H', long, default_value = "mesh-node.local")]
    host: String,
    
    /// Port to connect to
    #[arg(short, long, default_value_t = 2222)]
    port: u16,
    
    /// Username for SSH
    #[arg(short, long, default_value = "arxos")]
    username: String,
    
    /// Private key path for authentication
    #[arg(short = 'k', long)]
    key: Option<String>,
    
    /// Use password authentication (will prompt)
    #[arg(short = 'P', long)]
    password: bool,
    
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
    
    // Load or create SSH configuration
    let mut ssh_config = if let Some(config_path) = args.config {
        load_config(Some(&config_path)).await?
    } else {
        // Build config from arguments
        let mut config = SshConfig::default();
        config.host = args.host;
        config.port = args.port;
        config.username = args.username;
        config.private_key_path = args.key;
        
        // Handle password authentication
        if args.password {
            config.password = Some(prompt_password("Password: ")?);
        }
        
        config
    };
    
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    
    // Create app
    let mut app = App::new(ssh_config);
    
    // Auto-connect if requested
    if args.auto_connect {
        info!("Auto-connecting to mesh node...");
        if let Err(e) = app.connect().await {
            error!("Auto-connect failed: {}", e);
            app.add_output(format!("Auto-connect failed: {}", e));
        }
    } else {
        app.add_output("Welcome to Arxos Terminal!".to_string());
        app.add_output("Type 'connect' to connect to a mesh node.".to_string());
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
        
        // Process any pending SSH data
        // This would be done in a separate task in production
        // For now, we poll in the main loop
    }
    
    Ok(())
}

/// Print usage information
fn print_usage() {
    println!("╔════════════════════════════════════════╗");
    println!("║     Arxos Terminal - RF Mesh Client     ║");
    println!("╚════════════════════════════════════════╝");
    println!();
    println!("Usage: arxos [OPTIONS]");
    println!();
    println!("Options:");
    println!("  -H, --host <HOST>      Host to connect to [default: mesh-node.local]");
    println!("  -p, --port <PORT>      Port to connect to [default: 2222]");
    println!("  -u, --username <USER>  SSH username [default: arxos]");
    println!("  -k, --key <PATH>       Private key path for authentication");
    println!("  -P, --password         Use password authentication (will prompt)");
    println!("  -c, --config <PATH>    Configuration file path");
    println!("  -a, --auto-connect     Auto-connect on startup");
    println!("  -v, --verbose          Enable verbose logging");
    println!("  -h, --help             Print help");
    println!();
    println!("Examples:");
    println!("  # Connect with key authentication");
    println!("  arxos -H 192.168.1.100 -k ~/.ssh/arxos_key");
    println!();
    println!("  # Connect with password");
    println!("  arxos -H mesh-gateway.local -P");
    println!();
    println!("  # Auto-connect with config file");
    println!("  arxos -c ~/.config/arxos/terminal.toml -a");
}