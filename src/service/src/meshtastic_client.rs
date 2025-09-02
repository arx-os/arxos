//! Meshtastic Client
//!
//! Client for communicating with Meshtastic hardware

use anyhow::Result;
use log::{debug, error, info, warn};
use serialport::{SerialPort, SerialPortBuilder};
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::sync::mpsc;
use tokio::time::{sleep, timeout};

use crate::config::MeshtasticConfig;
use crate::protocol_translator::ProtocolTranslator;
use arxos_core::ArxObject;

/// Meshtastic client for communicating with hardware
pub struct MeshtasticClient {
    config: MeshtasticConfig,
    connection: Option<Box<dyn SerialPort>>,
    protocol_translator: ProtocolTranslator,
    message_queue: Arc<Mutex<VecDeque<ArxObject>>>,
    is_connected: Arc<Mutex<bool>>,
}

impl MeshtasticClient {
    /// Create new Meshtastic client
    pub fn new(config: MeshtasticConfig) -> Self {
        Self {
            config,
            connection: None,
            protocol_translator: ProtocolTranslator::new(),
            message_queue: Arc::new(Mutex::new(VecDeque::new())),
            is_connected: Arc::new(Mutex::new(false)),
        }
    }

    /// Connect to Meshtastic device
    pub async fn connect(&mut self) -> Result<()> {
        info!("Connecting to Meshtastic device on {}", self.config.port);

        let builder: SerialPortBuilder = serialport::new(&self.config.port, self.config.baud_rate)
            .timeout(Duration::from_secs(self.config.timeout_seconds));

        match builder.open() {
            Ok(port) => {
                self.connection = Some(port);
                *self.is_connected.lock().unwrap() = true;
                info!("Connected to Meshtastic device");
                Ok(())
            }
            Err(e) => {
                error!("Failed to connect to Meshtastic device: {}", e);
                Err(e.into())
            }
        }
    }

    /// Disconnect from Meshtastic device
    pub async fn disconnect(&mut self) -> Result<()> {
        if let Some(_) = self.connection.take() {
            *self.is_connected.lock().unwrap() = false;
            info!("Disconnected from Meshtastic device");
        }
        Ok(())
    }

    /// Check if connected to Meshtastic device
    pub fn is_connected(&self) -> bool {
        *self.is_connected.lock().unwrap()
    }

    /// Send ArxObject to mesh network
    pub async fn send_arxobject(&mut self, arxobject: ArxObject) -> Result<()> {
        if !self.is_connected() {
            return Err(anyhow::anyhow!("Not connected to Meshtastic device"));
        }

        debug!("Sending ArxObject: {:?}", arxobject);

        // Convert ArxObject to Meshtastic message
        let meshtastic_data = self.protocol_translator.encode_arxobject(arxobject)?;

        // Send via serial connection
        if let Some(port) = &mut self.connection {
            port.write_all(&meshtastic_data)?;
            port.flush()?;
            debug!("ArxObject sent successfully");
        }

        Ok(())
    }

    /// Receive ArxObject from mesh network
    pub async fn receive_arxobject(&mut self) -> Result<Option<ArxObject>> {
        if !self.is_connected() {
            return Ok(None);
        }

        // Check message queue first
        if let Some(arxobject) = self.message_queue.lock().unwrap().pop_front() {
            return Ok(Some(arxobject));
        }

        // Try to read from serial connection
        if let Some(port) = &mut self.connection {
            let mut buffer = [0u8; 256];
            
            match timeout(Duration::from_millis(100), async {
                port.read(&mut buffer)
            }).await {
                Ok(Ok(bytes_read)) if bytes_read > 0 => {
                    debug!("Received {} bytes from Meshtastic", bytes_read);
                    
                    // Convert Meshtastic message to ArxObject
                    let arxobject = self.protocol_translator.decode_arxobject(&buffer[..bytes_read])?;
                    debug!("Decoded ArxObject: {:?}", arxobject);
                    
                    Ok(Some(arxobject))
                }
                Ok(Ok(_)) => Ok(None), // No data available
                Ok(Err(e)) => {
                    warn!("Error reading from Meshtastic: {}", e);
                    Ok(None)
                }
                Err(_) => Ok(None), // Timeout
            }
        } else {
            Ok(None)
        }
    }

    /// Start background message processing
    pub async fn start_message_processing(&self) -> Result<()> {
        let message_queue = Arc::clone(&self.message_queue);
        let is_connected = Arc::clone(&self.is_connected);
        let config = self.config.clone();

        tokio::spawn(async move {
            info!("Starting Meshtastic message processing");

            while *is_connected.lock().unwrap() {
                // Process incoming messages
                // This would typically involve reading from serial port
                // and adding messages to the queue
                
                sleep(Duration::from_millis(100)).await;
            }

            info!("Meshtastic message processing stopped");
        });

        Ok(())
    }

    /// Get node information
    pub async fn get_node_info(&self) -> Result<NodeInfo> {
        Ok(NodeInfo {
            node_id: self.config.node_id,
            is_connected: self.is_connected(),
            port: self.config.port.clone(),
            baud_rate: self.config.baud_rate,
        })
    }

    /// Send heartbeat to mesh network
    pub async fn send_heartbeat(&mut self) -> Result<()> {
        if !self.is_connected() {
            return Ok(());
        }

        let heartbeat = ArxObject::heartbeat(self.config.node_id);
        self.send_arxobject(heartbeat).await?;
        
        debug!("Heartbeat sent");
        Ok(())
    }
}

/// Node information
#[derive(Debug, Clone)]
pub struct NodeInfo {
    pub node_id: u16,
    pub is_connected: bool,
    pub port: String,
    pub baud_rate: u32,
}

impl Drop for MeshtasticClient {
    fn drop(&mut self) {
        if self.is_connected() {
            let _ = futures::executor::block_on(self.disconnect());
        }
    }
}
