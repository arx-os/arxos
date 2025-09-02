//! ArxOS Terminal Commands
//! 
//! Clean, simple commands for building intelligence

use crate::meshtastic_client::MeshtasticClient;
use std::error::Error;

/// ArxOS command types
#[derive(Debug, Clone)]
pub enum ArxOSCommand {
    Query { query: String },
    Scan { room: Option<String> },
    Connect { device: Option<String> },
    Disconnect,
    Status,
    Help,
    Exit,
}

impl ArxOSCommand {
    /// Parse command from string
    pub fn parse(input: &str) -> Result<Self, String> {
        let parts: Vec<&str> = input.trim().split_whitespace().collect();
        
        if parts.is_empty() {
            return Err("Empty command".to_string());
        }
        
        match parts[0] {
            "query" => {
                if parts.len() < 2 {
                    return Err("Usage: query <expression>".to_string());
                }
                let query = parts[1..].join(" ");
                Ok(ArxOSCommand::Query { query })
            }
            "scan" => {
                let room = if parts.len() > 1 {
                    Some(parts[1..].join(" "))
                } else {
                    None
                };
                Ok(ArxOSCommand::Scan { room })
            }
            "connect" => {
                let device = if parts.len() > 1 {
                    Some(parts[1].to_string())
                } else {
                    None
                };
                Ok(ArxOSCommand::Connect { device })
            }
            "disconnect" => Ok(ArxOSCommand::Disconnect),
            "status" => Ok(ArxOSCommand::Status),
            "help" => Ok(ArxOSCommand::Help),
            "exit" | "quit" => Ok(ArxOSCommand::Exit),
            _ => Err(format!("Unknown command: {}", parts[0])),
        }
    }
    
    /// Execute command
    pub async fn execute(&self, client: &mut MeshtasticClient) -> Result<String, Box<dyn Error>> {
        match self {
            ArxOSCommand::Query { query } => {
                let response = client.send_query(query).await?;
                Ok(format!("Query: {}\nResponse: {}", query, response))
            }
            ArxOSCommand::Scan { room } => {
                let room_str = room.as_deref().unwrap_or("current");
                Ok(format!("Scanning room: {}\nUse mobile app for LiDAR scanning", room_str))
            }
            ArxOSCommand::Connect { device } => {
                client.connect(device.as_deref()).await?;
                Ok("Connected to mesh network".to_string())
            }
            ArxOSCommand::Disconnect => {
                client.disconnect().await?;
                Ok("Disconnected from mesh network".to_string())
            }
            ArxOSCommand::Status => {
                let status = client.get_status().await?;
                Ok(format!("Mesh Status: {}\nNode ID: {}\nConnected: {}", 
                    status.network_status, status.node_id, status.connected))
            }
            ArxOSCommand::Help => {
                Ok(Self::help_text())
            }
            ArxOSCommand::Exit => {
                Ok("Goodbye!".to_string())
            }
        }
    }
    
    /// Get help text
    fn help_text() -> String {
        r#"ArxOS Building Intelligence Terminal
====================================

Commands:
  query <expression>    - Query building data
  scan [room]          - Scan room (use mobile app for LiDAR)
  connect [device]     - Connect to mesh network
  disconnect           - Disconnect from mesh network
  status               - Show connection status
  help                 - Show this help
  exit                 - Exit ArxOS

Examples:
  query "room:205 type:outlet"
  query "emergency exits"
  query "hvac floor:2"
  scan room:205
  connect /dev/ttyUSB0
  connect bluetooth://meshtastic-001

Connection Methods:
  - USB: connect /dev/ttyUSB0
  - Bluetooth: connect bluetooth://device-name
  - LoRa Dongle: connect (auto-detect)

ArxOS routes building intelligence, it doesn't process it."#.to_string()
    }
}

/// Command processor for terminal
pub struct CommandProcessor {
    history: Vec<String>,
    history_index: usize,
}

impl CommandProcessor {
    pub fn new() -> Self {
        Self {
            history: Vec::new(),
            history_index: 0,
        }
    }
    
    /// Process command input
    pub async fn process_command(
        &mut self, 
        input: &str, 
        client: &mut MeshtasticClient
    ) -> Result<String, Box<dyn Error>> {
        // Add to history
        self.history.push(input.to_string());
        self.history_index = self.history.len();
        
        // Parse and execute command
        let command = ArxOSCommand::parse(input)?;
        let result = command.execute(client).await?;
        
        Ok(result)
    }
    
    /// Get command history
    pub fn get_history(&self) -> &Vec<String> {
        &self.history
    }
    
    /// Navigate history
    pub fn history_up(&mut self) -> Option<&String> {
        if self.history_index > 0 {
            self.history_index -= 1;
            self.history.get(self.history_index)
        } else {
            None
        }
    }
    
    /// Navigate history down
    pub fn history_down(&mut self) -> Option<&String> {
        if self.history_index < self.history.len() {
            self.history_index += 1;
            self.history.get(self.history_index)
        } else {
            None
        }
    }
}
