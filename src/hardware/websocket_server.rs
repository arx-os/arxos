//! WebSocket server for real-time sensor data streaming
//!
//! This module provides WebSocket capabilities for real-time bidirectional communication
//! with clients for live sensor data updates.

#[cfg(feature = "async-sensors")]
use super::{SensorData, HardwareError};
#[cfg(feature = "async-sensors")]
use tokio::net::{TcpListener, TcpStream};
#[cfg(feature = "async-sensors")]
use tokio_tungstenite::{accept_async, tungstenite::Message};
#[cfg(feature = "async-sensors")]
use log::{info, warn, error};
#[cfg(feature = "async-sensors")]
use tokio::sync::broadcast;
#[cfg(feature = "async-sensors")]
use futures_util::{SinkExt, StreamExt};

/// WebSocket server for sensor data streaming
#[cfg(feature = "async-sensors")]
pub struct WebSocketSensorServer {
    host: String,
    port: u16,
    broadcaster: broadcast::Sender<SensorData>,
}

#[cfg(feature = "async-sensors")]
impl WebSocketSensorServer {
    /// Create a new WebSocket server
    pub fn new(host: String, port: u16) -> Self {
        let (tx, _rx) = broadcast::channel::<SensorData>(100);
        
        Self {
            host,
            port,
            broadcaster: tx,
        }
    }
    
    /// Get broadcaster for sending sensor data
    pub fn get_broadcaster(&self) -> broadcast::Sender<SensorData> {
        self.broadcaster.clone()
    }
    
    /// Start the WebSocket server
    pub async fn start(&self) -> Result<(), HardwareError> {
        let addr = format!("{}:{}", self.host, self.port);
        let listener = TcpListener::bind(&addr)
            .await
            .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Failed to bind to {}: {}", addr, e))))?;
        
        info!("WebSocket sensor server listening on ws://{}", addr);
        
        // Spawn a task to accept connections
        let broadcaster = self.broadcaster.clone();
        tokio::spawn(async move {
            while let Ok((stream, addr)) = listener.accept().await {
                info!("New WebSocket connection from: {}", addr);
                let tx = broadcaster.clone();
                
                tokio::spawn(async move {
                    Self::handle_connection(stream, addr, tx).await;
                });
            }
        });
        
        Ok(())
    }
    
    /// Handle a WebSocket connection
    #[cfg(feature = "async-sensors")]
    async fn handle_connection(
        stream: TcpStream,
        addr: std::net::SocketAddr,
        broadcaster: broadcast::Sender<SensorData>,
    ) {
        let ws_stream = match accept_async(stream).await {
            Ok(ws) => ws,
            Err(e) => {
                error!("Failed to accept WebSocket connection from {}: {}", addr, e);
                return;
            }
        };
        
        info!("WebSocket connection established with: {}", addr);
        
        let (mut tx, mut rx) = ws_stream.split();
        let mut broadcast_rx = broadcaster.subscribe();
        
        // Forward broadcast messages to WebSocket client
        tokio::spawn(async move {
            loop {
                tokio::select! {
                    result = broadcast_rx.recv() => {
                        match result {
                            Ok(sensor_data) => {
                                match serde_json::to_string(&sensor_data) {
                                    Ok(json) => {
                                        if let Err(e) = tx.send(Message::Text(json)).await {
                                            warn!("Failed to send to WebSocket client {}: {}", addr, e);
                                            break;
                                        }
                                    }
                                    Err(e) => {
                                        warn!("Failed to serialize sensor data: {}", e);
                                    }
                                }
                            }
                            Err(broadcast::error::RecvError::Closed) => {
                                info!("Broadcaster closed, closing connection to {}", addr);
                                break;
                            }
                            Err(_) => {
                                // Lag behind, skip this message
                            }
                        }
                    }
                }
            }
        });
        
        // Handle incoming messages from client
        while let Some(message_result) = rx.next().await {
            match message_result {
                Ok(message) => {
                    match message {
                        Message::Text(text) => {
                            info!("Received from client {}: {}", addr, text);
                            // Could implement query/control commands here
                        }
                        Message::Close(_) => {
                            info!("Client {} closed connection", addr);
                            break;
                        }
                        _ => {}
                    }
                }
                Err(e) => {
                    warn!("WebSocket error for client {}: {}", addr, e);
                    break;
                }
            }
        }
        
        info!("WebSocket connection closed with: {}", addr);
    }
}

/// Start WebSocket server for real-time sensor updates
#[cfg(feature = "async-sensors")]
pub async fn start_websocket_server(
    host: &str,
    port: u16,
) -> Result<broadcast::Sender<SensorData>, HardwareError> {
    let (tx, _rx) = broadcast::channel::<SensorData>(100);
    let broadcaster = tx.clone();
    
    let addr = format!("{}:{}", host, port);
    let listener = TcpListener::bind(&addr)
        .await
        .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Failed to bind to {}: {}", addr, e))))?;
    
    info!("WebSocket sensor server listening on ws://{}", addr);
    
    // Spawn a task to accept connections
    tokio::spawn(async move {
        while let Ok((stream, addr)) = listener.accept().await {
            info!("New WebSocket connection from: {}", addr);
            let tx_clone = broadcaster.clone();
            
            tokio::spawn(async move {
                WebSocketSensorServer::handle_connection(stream, addr, tx_clone).await;
            });
        }
    });
    
    Ok(tx)
}

#[cfg(not(feature = "async-sensors"))]
pub struct WebSocketSensorServer;

#[cfg(not(feature = "async-sensors"))]
impl WebSocketSensorServer {
    pub fn new(_host: String, _port: u16) -> Self {
        Self
    }
    
    pub async fn start(&self) -> Result<(), HardwareError> {
        Err(HardwareError::IoError(std::io::Error::other("WebSocket support requires async-sensors feature")))
    }
}

#[cfg(test)]
#[cfg(feature = "async-sensors")]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_websocket_server_creation() {
        let server = WebSocketSensorServer::new("127.0.0.1".to_string(), 8080);
        let _broadcaster = server.get_broadcaster();
        
        // Test that we can get the broadcaster successfully
        // (receiver_count is always >= 0, so the comparison was redundant)
    }
}

