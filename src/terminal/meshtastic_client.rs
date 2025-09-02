//! Meshtastic Client for connecting to Arxos mesh nodes
//!
//! Provides air-gapped terminal access to mesh nodes via meshtastic protocol

use async_trait::async_trait;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use thiserror::Error;
use anyhow::Result;
use log::{debug, error, info, warn};
use std::time::Duration;

/// Meshtastic client errors
#[derive(Error, Debug)]
pub enum MeshtasticClientError {
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),
    
    #[error("Radio error: {0}")]
    RadioError(String),
    
    #[error("Protocol error: {0}")]
    ProtocolError(String),
    
    #[error("Timeout")]
    Timeout,
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

/// Meshtastic connection configuration
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct MeshtasticConfig {
    pub node_id: u32,
    pub frequency_mhz: f32,
    pub region: String,
    pub timeout_seconds: u64,
    pub retry_attempts: u32,
}

impl Default for MeshtasticConfig {
    fn default() -> Self {
        Self {
            node_id: 0x0001,
            frequency_mhz: 915.0,  // US ISM band
            region: "US".to_string(),
            timeout_seconds: 30,
            retry_attempts: 3,
        }
    }
}

/// Meshtastic client for mesh node connection
pub struct MeshtasticClient {
    config: MeshtasticConfig,
    output_rx: mpsc::UnboundedReceiver<Vec<u8>>,
    output_tx: mpsc::UnboundedSender<Vec<u8>>,
    connected: bool,
    radio: Option<Box<dyn MeshtasticRadio + Send + Sync>>,
}

/// Trait for meshtastic radio implementations
#[async_trait]
pub trait MeshtasticRadio {
    async fn connect(&mut self, config: &MeshtasticConfig) -> Result<(), MeshtasticClientError>;
    async fn disconnect(&mut self) -> Result<(), MeshtasticClientError>;
    async fn send_packet(&mut self, packet: &MeshtasticPacket) -> Result<(), MeshtasticClientError>;
    async fn receive_packet(&mut self) -> Result<Option<MeshtasticPacket>, MeshtasticClientError>;
    fn is_connected(&self) -> bool;
}

/// Meshtastic packet structure
#[derive(Debug, Clone)]
pub struct MeshtasticPacket {
    pub source_id: u32,
    pub dest_id: u32,
    pub packet_type: u8,
    pub payload: Vec<u8>,
    pub sequence: u16,
}

impl MeshtasticPacket {
    pub fn new_query(source_id: u32, dest_id: u32, query: &str) -> Self {
        Self {
            source_id,
            dest_id,
            packet_type: 0x10, // Query packet
            payload: query.as_bytes().to_vec(),
            sequence: 0,
        }
    }
    
    pub fn new_response(source_id: u32, dest_id: u32, response: &str) -> Self {
        Self {
            source_id,
            dest_id,
            packet_type: 0x11, // Response packet
            payload: response.as_bytes().to_vec(),
            sequence: 0,
        }
    }
}

/// Mock meshtastic radio for testing
pub struct MockMeshtasticRadio {
    connected: bool,
    rx_buffer: std::collections::VecDeque<MeshtasticPacket>,
}

impl MockMeshtasticRadio {
    pub fn new() -> Self {
        Self {
            connected: false,
            rx_buffer: std::collections::VecDeque::new(),
        }
    }
    
    pub fn add_mock_response(&mut self, packet: MeshtasticPacket) {
        self.rx_buffer.push_back(packet);
    }
}

#[async_trait]
impl MeshtasticRadio for MockMeshtasticRadio {
    async fn connect(&mut self, _config: &MeshtasticConfig) -> Result<(), MeshtasticClientError> {
        self.connected = true;
        Ok(())
    }
    
    async fn disconnect(&mut self) -> Result<(), MeshtasticClientError> {
        self.connected = false;
        Ok(())
    }
    
    async fn send_packet(&mut self, packet: &MeshtasticPacket) -> Result<(), MeshtasticClientError> {
        if !self.connected {
            return Err(MeshtasticClientError::ConnectionFailed("Not connected".to_string()));
        }
        
        // Simulate packet transmission
        info!("Mock radio: Sending packet from {} to {}", packet.source_id, packet.dest_id);
        Ok(())
    }
    
    async fn receive_packet(&mut self) -> Result<Option<MeshtasticPacket>, MeshtasticClientError> {
        if !self.connected {
            return Err(MeshtasticClientError::ConnectionFailed("Not connected".to_string()));
        }
        
        Ok(self.rx_buffer.pop_front())
    }
    
    fn is_connected(&self) -> bool {
        self.connected
    }
}

impl MeshtasticClient {
    /// Create new meshtastic client
    pub fn new(config: MeshtasticConfig) -> Self {
        let (output_tx, output_rx) = mpsc::unbounded_channel();
        
        Self {
            config,
            output_rx,
            output_tx,
            connected: false,
            radio: None,
        }
    }
    
    /// Connect to mesh network
    pub async fn connect(&mut self) -> Result<(), MeshtasticClientError> {
        // For now, use mock radio
        let mut radio = Box::new(MockMeshtasticRadio::new());
        radio.connect(&self.config).await?;
        
        self.radio = Some(radio);
        self.connected = true;
        
        info!("Connected to meshtastic network on {} MHz", self.config.frequency_mhz);
        Ok(())
    }
    
    /// Disconnect from mesh network
    pub async fn disconnect(&mut self) {
        if let Some(ref mut radio) = self.radio {
            let _ = radio.disconnect().await;
        }
        self.connected = false;
    }
    
    /// Send command to mesh node
    pub async fn send_command(&mut self, command: &str) -> Result<String, MeshtasticClientError> {
        if !self.connected {
            return Err(MeshtasticClientError::ConnectionFailed("Not connected".to_string()));
        }
        
        let packet = MeshtasticPacket::new_query(
            self.config.node_id,
            0xFFFF, // Broadcast to all nodes
            command,
        );
        
        if let Some(ref mut radio) = self.radio {
            radio.send_packet(&packet).await?;
        }
        
        // For now, return a mock response
        let response = format!("Mock response for: {}\n", command);
        let _ = self.output_tx.send(response.clone().into_bytes());
        
        Ok(response)
    }
    
    /// Read output from mesh network
    pub async fn read_output(&mut self) -> Option<Vec<u8>> {
        self.output_rx.recv().await
    }
    
    /// Check if connected
    pub fn is_connected(&self) -> bool {
        self.connected
    }
    
    /// Get configuration
    pub fn config(&self) -> &MeshtasticConfig {
        &self.config
    }
    
    /// Get connection status
    pub async fn get_status(&self) -> Result<String> {
        if self.connected {
            Ok(format!("Connected to meshtastic network ({} MHz)", self.config.frequency_mhz))
        } else {
            Ok("Disconnected".to_string())
        }
    }
}

/// Load meshtastic configuration from file
pub async fn load_config(config_path: Option<&str>) -> Result<MeshtasticConfig> {
    // For now, just return default config
    // TODO: Implement file-based configuration
    Ok(MeshtasticConfig::default())
}

/// Prompt for meshtastic node ID
pub fn prompt_node_id(prompt: &str) -> Result<u32> {
    use std::io::{self, Write};
    
    print!("{}", prompt);
    io::stdout().flush()?;
    
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    
    let node_id = input.trim().parse::<u32>()
        .map_err(|_| anyhow::anyhow!("Invalid node ID"))?;
    
    Ok(node_id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_meshtastic_client_connection() {
        let config = MeshtasticConfig::default();
        let mut client = MeshtasticClient::new(config);
        
        assert!(!client.is_connected());
        
        let result = client.connect().await;
        assert!(result.is_ok());
        assert!(client.is_connected());
        
        client.disconnect().await;
        assert!(!client.is_connected());
    }

    #[tokio::test]
    async fn test_meshtastic_packet_creation() {
        let query_packet = MeshtasticPacket::new_query(0x0001, 0x0002, "test query");
        assert_eq!(query_packet.source_id, 0x0001);
        assert_eq!(query_packet.dest_id, 0x0002);
        assert_eq!(query_packet.packet_type, 0x10);
        assert_eq!(query_packet.payload, b"test query");
        
        let response_packet = MeshtasticPacket::new_response(0x0002, 0x0001, "test response");
        assert_eq!(response_packet.packet_type, 0x11);
        assert_eq!(response_packet.payload, b"test response");
    }
}
