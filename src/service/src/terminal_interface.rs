//! Terminal Interface
//!
//! Terminal interface for ArxOS Service

use anyhow::Result;
use log::debug;
use std::sync::Arc;
use tokio::sync::mpsc;

use crate::config::TerminalConfig;
use crate::meshtastic_client::NodeInfo;
use arxos_core::ArxObject;

/// Terminal interface for ArxOS Service
pub struct TerminalInterface {
    config: TerminalConfig,
    command_sender: Option<mpsc::UnboundedSender<String>>,
    is_active: Arc<std::sync::atomic::AtomicBool>,
}

impl TerminalInterface {
    /// Create new terminal interface
    pub fn new(config: TerminalConfig) -> Self {
        Self {
            config,
            command_sender: None,
            is_active: Arc::new(std::sync::atomic::AtomicBool::new(false)),
        }
    }

    /// Start terminal interface
    pub async fn start(&mut self) -> Result<()> {
        debug!("Starting terminal interface");

        let (tx, mut rx) = mpsc::unbounded_channel::<String>();
        self.command_sender = Some(tx);

        // Start terminal input handling
        let is_active = Arc::clone(&self.is_active);
        let prompt = self.config.prompt.clone();

        tokio::spawn(async move {
            is_active.store(true, std::sync::atomic::Ordering::SeqCst);

            loop {
                // Simple terminal input simulation
                // In a real implementation, this would use crossterm or similar
                print!("{}", prompt);
                std::io::Write::flush(&mut std::io::stdout()).unwrap();

                let mut input = String::new();
                if std::io::stdin().read_line(&mut input).is_ok() {
                    let command = input.trim().to_string();
                    if !command.is_empty() {
                        // Send command to service
                        if let Some(sender) = &self.command_sender {
                            let _ = sender.send(command);
                        }
                    }
                }
            }
        });

        debug!("Terminal interface started");
        Ok(())
    }

    /// Get command from terminal
    pub async fn get_command(&mut self) -> Result<Option<String>> {
        // This would typically read from the command channel
        // For now, return None to indicate no command available
        Ok(None)
    }

    /// Display ArxObject
    pub async fn display_arxobject(&self, arxobject: &ArxObject) -> Result<()> {
        println!("Received ArxObject: {:?}", arxobject);
        Ok(())
    }

    /// Display status information
    pub async fn display_status(&self, node_info: &NodeInfo) -> Result<()> {
        println!("ArxOS Service Status:");
        println!("  Node ID: 0x{:04X}", node_info.node_id);
        println!("  Connected: {}", node_info.is_connected);
        println!("  Port: {}", node_info.port);
        println!("  Baud Rate: {}", node_info.baud_rate);
        Ok(())
    }

    /// Display message
    pub async fn display_message(&self, message: &str) -> Result<()> {
        println!("{}", message);
        Ok(())
    }

    /// Display error message
    pub async fn display_error(&self, error: &str) -> Result<()> {
        eprintln!("Error: {}", error);
        Ok(())
    }

    /// Display query results
    pub async fn display_query_results(&self, results: &[ArxObject]) -> Result<()> {
        println!("Query Results ({} objects):", results.len());
        for (i, arxobject) in results.iter().enumerate() {
            println!("  {}: {:?}", i + 1, arxobject);
        }
        Ok(())
    }

    /// Display help information
    pub async fn display_help(&self) -> Result<()> {
        println!("ArxOS Service Commands:");
        println!("  status     - Show service status");
        println!("  send <obj> - Send ArxObject to mesh");
        println!("  query <expr> - Query building database");
        println!("  help       - Show this help");
        println!("  exit/quit  - Exit service");
        Ok(())
    }

    /// Check if terminal interface is active
    pub fn is_active(&self) -> bool {
        self.is_active.load(std::sync::atomic::Ordering::SeqCst)
    }

    /// Stop terminal interface
    pub async fn stop(&self) -> Result<()> {
        self.is_active.store(false, std::sync::atomic::Ordering::SeqCst);
        debug!("Terminal interface stopped");
        Ok(())
    }
}
