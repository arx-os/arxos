mod models;
mod database;
mod terminal;
mod query;
mod api;
mod events;
mod webhooks;
mod bulk;
mod middleware;
mod docs;
mod health;
mod rating;
mod market;
mod visualization;

use clap::Parser;
use anyhow::Result;

/// Initialize simple tracing
fn init_tracing() {
    use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};
    
    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| "arxos=info,tower_http=debug".into());
    
    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer().compact())
        .init();
}

#[derive(Parser)]
#[command(name = "arxos")]
#[command(about = "Buildings as queryable databases", long_about = None)]
struct Cli {
    /// Database URL
    #[arg(short, long, env = "DATABASE_URL", default_value = "postgresql://localhost/arxos")]
    database: String,
    
    /// Building ID to connect to
    #[arg(short, long)]
    building: Option<String>,
    
    /// Execute command and exit
    #[arg(short, long)]
    command: Option<String>,
    
    /// Verbosity
    #[arg(short, long, action = clap::ArgAction::Count)]
    verbose: u8,
    
    /// Start API server
    #[arg(long)]
    api: bool,
    
    /// API server port
    #[arg(long, default_value = "3000")]
    port: u16,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    
    // Setup logging
    let log_level = match cli.verbose {
        0 => "warn",
        1 => "info",
        2 => "debug",
        _ => "trace",
    };
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or(log_level))
        .format_timestamp(None)
        .init();
    
    // Connect to database
    let db = database::Database::connect(&cli.database).await?;
    let db_arc = std::sync::Arc::new(db);
    
    // If API mode, start the web server
    if cli.api {
        // Initialize tracing
        init_tracing();
        
        println!("Starting ArxOS API server on port {}", cli.port);
        
        // Create event system
        let event_system = std::sync::Arc::new(
            events::EventSystem::new(cli.database.clone())
        );
        
        // Create webhook system
        let webhook_system = std::sync::Arc::new(
            webhooks::WebhookSystem::new(&cli.database).await?
        );
        
        // Create bulk operations system
        let bulk_system = std::sync::Arc::new(
            bulk::BulkSystem::new(sqlx::PgPool::connect(&cli.database).await?)
        );
        
        // Create rating service
        let rating_service = std::sync::Arc::new(
            rating::RatingService::new(db_arc.clone())
        );
        
        // Create rating event handler
        let rating_event_handler = std::sync::Arc::new(
            rating::RatingEventHandler::new(event_system.clone())
        );
        
        // Create rating trigger system
        let rating_trigger_system = std::sync::Arc::new(
            rating::RatingTriggerSystem::new(rating_service.clone(), rating_event_handler)
        );
        
        // Create market service
        let market_service = std::sync::Arc::new(
            market::MarketService::new(db_arc.clone())
        );
        
        // Create health service
        let health_service = std::sync::Arc::new(
            health::HealthService::new()
        );
        
        // Create database pool for health checks
        let db_pool = std::sync::Arc::new(sqlx::PgPool::connect(&cli.database).await?);
        
        // Start event listener in background
        let event_system_clone = event_system.clone();
        let _webhook_system_clone = webhook_system.clone();
        tokio::spawn(async move {
            if let Err(e) = event_system_clone.start_listening().await {
                log::error!("Event listener failed: {}", e);
            }
        });
        
        // Start webhook delivery worker
        webhook_system.clone().start_delivery_worker().await;
        
        // Connect event system to webhooks
        let mut event_receiver = event_system.subscribe();
        let webhook_system_for_events = webhook_system.clone();
        tokio::spawn(async move {
            loop {
                match event_receiver.recv().await {
                    Ok(event) => {
                        if let Err(e) = webhook_system_for_events.process_event(&event).await {
                            log::error!("Failed to process webhook for event: {}", e);
                        }
                    }
                    Err(e) => {
                        log::error!("Event receiver error: {}", e);
                        break;
                    }
                }
            }
        });
        
        // Connect event system to rating triggers
        let rating_event_receiver = event_system.subscribe();
        let rating_trigger_system_clone = rating_trigger_system.clone();
        rating_trigger_system_clone.start_trigger_listener(rating_event_receiver).await;
        
        // Start scheduled rating recalculation (every 24 hours)
        let rating_trigger_system_for_scheduler = rating_trigger_system.clone();
        rating_trigger_system_for_scheduler.start_scheduled_recalculation(24).await;
        
        let app = api::create_router(
            db_arc.clone(), 
            event_system, 
            webhook_system, 
            bulk_system,
            rating_service,
            market_service,
            health_service,
            db_pool
        );
        let addr = format!("0.0.0.0:{}", cli.port);
        let listener = tokio::net::TcpListener::bind(&addr).await?;
        
        println!("API server listening on http://{}", addr);
        println!("Health check: http://{}/api/health", addr);
        println!("Event stream: http://{}/api/events", addr);
        println!("API documentation will be available at http://{}/api/docs", addr);
        
        axum::serve(listener, app).await?;
        return Ok(());
    }
    
    // Terminal mode
    let db = std::sync::Arc::try_unwrap(db_arc)
        .unwrap_or_else(|arc| (*arc).clone());
    
    // Get or select building
    let building_id = if let Some(id) = cli.building {
        id
    } else {
        let buildings = db.list_buildings().await?;
        if buildings.is_empty() {
            eprintln!("No buildings found. Create one with: arxos-admin create-building");
            std::process::exit(1);
        }
        buildings[0].id.to_string()
    };
    
    // Load building
    let building = db.load_building(&building_id).await?;
    
    // Create terminal
    let mut term = terminal::Terminal::new(building);
    
    // Run command or interactive mode
    if let Some(cmd) = cli.command {
        term.execute(&cmd)?;
    } else {
        println!("╔════════════════════════════════════════════════════════╗");
        println!("║                  ArxOS Terminal v1.0                  ║");
        println!("║          Buildings as Queryable Databases             ║");
        println!("╚════════════════════════════════════════════════════════╝");
        println!();
        println!("Type 'HELP' for commands, 'EXIT' to quit");
        println!();
        
        term.run().await?;
    }
    
    Ok(())
}