//! Transport abstraction layer for Arxos remote access
//! 
//! This module provides a unified interface for different communication methods:
//! - LoRa dongles (USB serial)
//! - Bluetooth mesh (BLE)
//! - SMS gateway
//! - Mock transport for testing

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};

pub mod mock;
pub mod lora;
pub mod lora_impl;
pub mod meshtastic;  // New Meshtastic transport
// pub mod bluetooth;  // TODO: Implement via Meshtastic BLE
// pub mod sms;        // TODO: Implement

/// Error types for transport operations
#[derive(Debug, thiserror::Error)]
pub enum TransportError {
    #[error("Not connected")]
    NotConnected,
    
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),
    
    #[error("Send failed: {0}")]
    SendFailed(String),
    
    #[error("Receive failed: {0}")]
    ReceiveFailed(String),
    
    #[error("Timeout")]
    Timeout,
    
    #[error("Invalid data: {0}")]
    InvalidData(String),
    
    #[error("Invalid configuration: {0}")]
    InvalidConfig(String),
    
    #[error("Would block")]
    WouldBlock,
    
    #[error("Transport not available")]
    NotAvailable,
}

/// Metrics for transport performance monitoring
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransportMetrics {
    pub connected: bool,
    #[serde(skip)]
    pub connected_since: Option<Instant>,
    pub connection_quality: f32,  // 0.0 to 1.0
    pub bytes_sent: usize,
    pub bytes_received: usize,
    pub packets_sent: usize,
    pub packets_received: usize,
    pub errors: usize,
    pub latency_ms: Option<u32>,
    pub signal_strength: Option<i8>,
}

impl Default for TransportMetrics {
    fn default() -> Self {
        Self {
            connected: false,
            connected_since: None,
            connection_quality: 0.0,
            bytes_sent: 0,
            bytes_received: 0,
            packets_sent: 0,
            packets_received: 0,
            errors: 0,
            latency_ms: None,
            signal_strength: None,
        }
    }
}

/// Transport trait that all communication methods must implement
#[async_trait]
pub trait Transport: Send + Sync {
    /// Connect to a building's mesh network
    async fn connect(&mut self, building_id: &str) -> Result<(), TransportError>;
    
    /// Disconnect from the network
    async fn disconnect(&mut self) -> Result<(), TransportError>;
    
    /// Send raw data
    async fn send(&mut self, data: &[u8]) -> Result<(), TransportError>;
    
    /// Receive raw data (with optional timeout)
    async fn receive(&mut self, timeout: Option<Duration>) -> Result<Vec<u8>, TransportError>;
    
    /// Check if connected
    fn is_connected(&self) -> bool;
    
    /// Get transport metrics
    fn get_metrics(&self) -> TransportMetrics;
    
    /// Get transport name for logging
    fn name(&self) -> &str;
    
    /// Check if this transport is available on the system
    async fn is_available(&self) -> bool;
}

/// Transport manager that handles multiple transport types
pub struct TransportManager {
    transports: Vec<Box<dyn Transport>>,
    active_transport: Option<usize>,
}

impl TransportManager {
    /// Create a new transport manager
    pub fn new() -> Self {
        Self {
            transports: Vec::new(),
            active_transport: None,
        }
    }
    
    /// Add a transport to the manager
    pub fn add_transport(&mut self, transport: Box<dyn Transport>) {
        self.transports.push(transport);
    }
    
    /// Auto-select the best available transport
    pub async fn auto_connect(&mut self, building_id: &str) -> Result<(), TransportError> {
        // Try transports in order of preference
        for (index, transport) in self.transports.iter_mut().enumerate() {
            if !transport.is_available().await {
                continue;
            }
            
            match transport.connect(building_id).await {
                Ok(()) => {
                    self.active_transport = Some(index);
                    log::info!("Connected via {}", transport.name());
                    return Ok(());
                }
                Err(e) => {
                    log::warn!("Failed to connect via {}: {}", transport.name(), e);
                }
            }
        }
        
        Err(TransportError::NotAvailable)
    }
    
    /// Get the active transport
    pub fn active_transport(&mut self) -> Option<&mut Box<dyn Transport>> {
        self.active_transport
            .and_then(|idx| self.transports.get_mut(idx))
    }
    
    /// Send data via active transport
    pub async fn send(&mut self, data: &[u8]) -> Result<(), TransportError> {
        match self.active_transport {
            Some(idx) => self.transports[idx].send(data).await,
            None => Err(TransportError::NotConnected),
        }
    }
    
    /// Receive data via active transport
    pub async fn receive(&mut self, timeout: Option<Duration>) -> Result<Vec<u8>, TransportError> {
        match self.active_transport {
            Some(idx) => self.transports[idx].receive(timeout).await,
            None => Err(TransportError::NotConnected),
        }
    }
    
    /// Get metrics for all transports
    pub fn get_all_metrics(&self) -> Vec<(String, TransportMetrics)> {
        self.transports
            .iter()
            .map(|t| (t.name().to_string(), t.get_metrics()))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::mock::MockTransport;
    
    #[tokio::test]
    async fn test_transport_manager() {
        let mut manager = TransportManager::new();
        
        // Add mock transport
        let mock = MockTransport::new();
        manager.add_transport(Box::new(mock));
        
        // Should connect successfully
        assert!(manager.auto_connect("test_building").await.is_ok());
        
        // Should be able to send data
        assert!(manager.send(b"test data").await.is_ok());
    }
}