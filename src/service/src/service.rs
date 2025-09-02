//! ArxOS Service
//!
//! Main service implementation

use anyhow::Result;
use log::{debug, error, info, warn};
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::time::{interval, Duration};

use crate::config::ServiceConfig;
use crate::meshtastic_client::{MeshtasticClient, NodeInfo};
use crate::terminal_interface::TerminalInterface;
use arxos_core::{ArxObject, Database};

/// Main ArxOS Service
pub struct ArxOSService {
    config: ServiceConfig,
    meshtastic_client: MeshtasticClient,
    terminal_interface: TerminalInterface,
    database: Database,
    is_running: Arc<std::sync::atomic::AtomicBool>,
}

impl ArxOSService {
    /// Create new ArxOS service
    pub async fn new(config: ServiceConfig) -> Result<Self> {
        info!("Initializing ArxOS Service");

        // Validate configuration
        config.validate()?;

        // Initialize Meshtastic client
        let meshtastic_client = MeshtasticClient::new(config.meshtastic.clone());

        // Initialize terminal interface
        let terminal_interface = TerminalInterface::new(config.terminal.clone());

        // Initialize database
        let database = Database::new(&config.database.path)?;

        // Initialize service
        let service = Self {
            config,
            meshtastic_client,
            terminal_interface,
            database,
            is_running: Arc::new(std::sync::atomic::AtomicBool::new(false)),
        };

        info!("ArxOS Service initialized successfully");
        Ok(service)
    }

    /// Run service in interactive mode
    pub async fn run_interactive(&mut self) -> Result<()> {
        info!("Starting ArxOS Service in interactive mode");

        // Connect to Meshtastic
        self.meshtastic_client.connect().await?;

        // Start message processing
        self.meshtastic_client.start_message_processing().await?;

        // Start terminal interface
        self.terminal_interface.start().await?;

        // Set running flag
        self.is_running.store(true, std::sync::atomic::Ordering::SeqCst);

        // Start background tasks
        let heartbeat_handle = self.start_heartbeat_task();
        let cleanup_handle = self.start_cleanup_task();

        // Main service loop
        self.run_main_loop().await?;

        // Stop background tasks
        self.is_running.store(false, std::sync::atomic::Ordering::SeqCst);
        let _ = heartbeat_handle.await;
        let _ = cleanup_handle.await;

        // Disconnect from Meshtastic
        self.meshtastic_client.disconnect().await?;

        info!("ArxOS Service stopped");
        Ok(())
    }

    /// Run service in daemon mode
    pub async fn run_daemon(&mut self) -> Result<()> {
        info!("Starting ArxOS Service in daemon mode");

        // Connect to Meshtastic
        self.meshtastic_client.connect().await?;

        // Start message processing
        self.meshtastic_client.start_message_processing().await?;

        // Set running flag
        self.is_running.store(true, std::sync::atomic::Ordering::SeqCst);

        // Start background tasks
        let heartbeat_handle = self.start_heartbeat_task();
        let cleanup_handle = self.start_cleanup_task();

        // Main service loop (no terminal interface)
        self.run_daemon_loop().await?;

        // Stop background tasks
        self.is_running.store(false, std::sync::atomic::Ordering::SeqCst);
        let _ = heartbeat_handle.await;
        let _ = cleanup_handle.await;

        // Disconnect from Meshtastic
        self.meshtastic_client.disconnect().await?;

        info!("ArxOS Service daemon stopped");
        Ok(())
    }

    /// Main service loop for interactive mode
    async fn run_main_loop(&mut self) -> Result<()> {
        info!("Starting main service loop");

        while self.is_running.load(std::sync::atomic::Ordering::SeqCst) {
            tokio::select! {
                // Handle Meshtastic messages
                mesh_msg = self.meshtastic_client.receive_arxobject() => {
                    if let Ok(Some(arxobject)) = mesh_msg {
                        self.handle_mesh_message(arxobject).await?;
                    }
                }
                // Handle terminal commands
                terminal_cmd = self.terminal_interface.get_command() => {
                    if let Ok(Some(command)) = terminal_cmd {
                        self.execute_command(command).await?;
                    }
                }
                // Handle shutdown signal
                _ = tokio::signal::ctrl_c() => {
                    info!("Received shutdown signal");
                    break;
                }
            }
        }

        Ok(())
    }

    /// Main service loop for daemon mode
    async fn run_daemon_loop(&mut self) -> Result<()> {
        info!("Starting daemon service loop");

        while self.is_running.load(std::sync::atomic::Ordering::SeqCst) {
            tokio::select! {
                // Handle Meshtastic messages
                mesh_msg = self.meshtastic_client.receive_arxobject() => {
                    if let Ok(Some(arxobject)) = mesh_msg {
                        self.handle_mesh_message(arxobject).await?;
                    }
                }
                // Handle shutdown signal
                _ = tokio::signal::ctrl_c() => {
                    info!("Received shutdown signal");
                    break;
                }
            }
        }

        Ok(())
    }

    /// Handle incoming mesh message
    async fn handle_mesh_message(&mut self, arxobject: ArxObject) -> Result<()> {
        debug!("Handling mesh message: {:?}", arxobject);

        // Store in database
        self.database.store_arxobject(&arxobject)?;

        // Process building intelligence
        self.process_building_intelligence(&arxobject).await?;

        // Forward to terminal interface if in interactive mode
        if self.terminal_interface.is_active() {
            self.terminal_interface.display_arxobject(&arxobject).await?;
        }

        Ok(())
    }

    /// Execute terminal command
    async fn execute_command(&mut self, command: String) -> Result<()> {
        debug!("Executing command: {}", command);

        let parts: Vec<&str> = command.trim().split_whitespace().collect();
        if parts.is_empty() {
            return Ok(());
        }

        match parts[0] {
            "status" => {
                let node_info = self.meshtastic_client.get_node_info().await?;
                self.terminal_interface.display_status(&node_info).await?;
            }
            "send" => {
                if parts.len() > 1 {
                    let arxobject = ArxObject::from_string(&parts[1..].join(" "))?;
                    self.meshtastic_client.send_arxobject(arxobject).await?;
                    self.terminal_interface.display_message("ArxObject sent successfully").await?;
                } else {
                    self.terminal_interface.display_error("Usage: send <arxobject>").await?;
                }
            }
            "query" => {
                if parts.len() > 1 {
                    let query = parts[1..].join(" ");
                    let results = self.database.query(&query)?;
                    self.terminal_interface.display_query_results(&results).await?;
                } else {
                    self.terminal_interface.display_error("Usage: query <expression>").await?;
                }
            }
            "help" => {
                self.terminal_interface.display_help().await?;
            }
            "exit" | "quit" => {
                self.is_running.store(false, std::sync::atomic::Ordering::SeqCst);
            }
            _ => {
                self.terminal_interface.display_error(&format!("Unknown command: {}", parts[0])).await?;
            }
        }

        Ok(())
    }

    /// Process building intelligence
    async fn process_building_intelligence(&mut self, arxobject: &ArxObject) -> Result<()> {
        debug!("Processing building intelligence for: {:?}", arxobject);

        // Add building intelligence processing logic here
        // This could include:
        // - Pattern recognition
        // - Anomaly detection
        // - Predictive analytics
        // - Holographic processing

        Ok(())
    }

    /// Start heartbeat task
    fn start_heartbeat_task(&self) -> tokio::task::JoinHandle<()> {
        let meshtastic_client = self.meshtastic_client.clone();
        let is_running = Arc::clone(&self.is_running);
        let interval_duration = Duration::from_secs(self.config.service.heartbeat_interval);

        tokio::spawn(async move {
            let mut interval = interval(interval_duration);

            while is_running.load(std::sync::atomic::Ordering::SeqCst) {
                interval.tick().await;

                if let Err(e) = meshtastic_client.send_heartbeat().await {
                    error!("Failed to send heartbeat: {}", e);
                }
            }
        })
    }

    /// Start cleanup task
    fn start_cleanup_task(&self) -> tokio::task::JoinHandle<()> {
        let database = self.database.clone();
        let is_running = Arc::clone(&self.is_running);
        let interval_duration = Duration::from_secs(self.config.service.cleanup_interval);

        tokio::spawn(async move {
            let mut interval = interval(interval_duration);

            while is_running.load(std::sync::atomic::Ordering::SeqCst) {
                interval.tick().await;

                if let Err(e) = database.cleanup_old_data() {
                    error!("Failed to cleanup old data: {}", e);
                }
            }
        })
    }
}

impl Drop for ArxOSService {
    fn drop(&mut self) {
        self.is_running.store(false, std::sync::atomic::Ordering::SeqCst);
    }
}
