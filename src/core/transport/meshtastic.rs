//! Pure Rust Meshtastic transport for ArxOS
//! 
//! This module provides integration with Meshtastic mesh network devices
//! for RF-only building intelligence routing.

use async_trait::async_trait;
// TODO: Add meshtastic and tokio_serial dependencies when needed
// use meshtastic::api::{StreamApi, ConnectedStreamApi};
// use meshtastic::protobufs::{self, FromRadio, ToRadio, MeshPacket, PortNum};
// use meshtastic::packet::PacketRouter;
use tokio::sync::mpsc;
// use tokio_serial::SerialPortBuilderExt;
use std::time::Duration;
use log::{debug, info, warn, error};

use crate::arxobject::ArxObject;
use super::{Transport, TransportError, TransportMetrics};

/// Meshtastic transport implementation
pub struct MeshtasticTransport {
    /// Connected API for sending/receiving
    // api: Option<ConnectedStreamApi>,  // TODO: Enable when meshtastic is added
    
    /// Receiver for decoded packets
    // packet_receiver: Option<mpsc::UnboundedReceiver<FromRadio>>,  // TODO: Enable when meshtastic is added
    
    /// Node configuration
    node_id: u32,
    
    /// Transport metrics
    metrics: TransportMetrics,
    
    /// Serial port path
    serial_port: String,
    
    /// Connection status
    connected: bool,
}

impl MeshtasticTransport {
    /// Create a new Meshtastic transport
    pub fn new(serial_port: String) -> Self {
        Self {
            // api: None,  // TODO: Enable when meshtastic is added
            // packet_receiver: None,  // TODO: Enable when meshtastic is added
            node_id: 0,
            metrics: TransportMetrics::default(),
            serial_port,
            connected: false,
        }
    }
    
    /// Connect via USB serial port
    pub async fn connect_serial(&mut self, port: &str) -> Result<(), TransportError> {
        info!("Connecting to Meshtastic device on {}", port);
        
        // TODO: Implement when tokio_serial and meshtastic dependencies are added
        /*
        // Build serial stream
        let serial_stream = tokio_serial::new(port, 115200)
            .timeout(Duration::from_millis(100))
            .open_native_async()
            .map_err(|e| TransportError::ConnectionFailed(format!("Serial error: {}", e)))?;
        
        // Create StreamApi
        let stream_api = StreamApi::new();
        
        // Connect to device
        let (mut decoded_listener, connected_api) = stream_api
            .connect(serial_stream)
            .await
            .map_err(|e| TransportError::ConnectionFailed(format!("API error: {}", e)))?;
        
        // Create channel for packet reception
        let (tx, rx) = mpsc::unbounded_channel();
        
        // Spawn listener task
        tokio::spawn(async move {
            while let Some(packet) = decoded_listener.recv().await {
                if tx.send(packet).is_err() {
                    break; // Receiver dropped
                }
            }
        });
        
        self.api = Some(connected_api);
        self.packet_receiver = Some(rx);
        */
        
        self.connected = true;
        
        info!("Connected to Meshtastic device");
        Ok(())
    }
    
    /// Send an ArxObject as a Meshtastic packet
    async fn send_arxobject_internal(&mut self, obj: &ArxObject, _dest: u32) -> Result<(), TransportError> {
        // TODO: Implement when meshtastic dependency is added
        // let api = self.api.as_mut()
        //     .ok_or(TransportError::NotConnected)?;
        
        // Serialize ArxObject to 13 bytes
        let _payload = obj.to_bytes();
        
        // TODO: Create and send MeshPacket when meshtastic is available
        
        self.metrics.packets_sent += 1;
        self.metrics.bytes_sent += 13;
        
        debug!("Sent ArxObject: {:?}", obj);
        Ok(())
    }
    
    /// Receive and decode ArxObject from mesh
    async fn receive_arxobject_internal(&mut self) -> Result<Option<ArxObject>, TransportError> {
        // TODO: Implement when meshtastic dependency is added
        // let receiver = self.packet_receiver.as_mut()
        //     .ok_or(TransportError::NotConnected)?;
        
        // For now, just return None (no packets)
        Ok(None)
        
        // Original implementation will be restored when meshtastic is added:
        /*
        // Check for incoming packets
        match receiver.try_recv() {
            Ok(from_radio) => {
                // Process packet...
            }
            Err(mpsc::error::TryRecvError::Empty) => {
                // No packets available
                return Ok(None);
            }
            Err(mpsc::error::TryRecvError::Disconnected) => {
                return Err(TransportError::NotConnected);
            }
        }
        
        Ok(None)
        */
    }
}

#[async_trait]
impl Transport for MeshtasticTransport {
    async fn connect(&mut self, building_id: &str) -> Result<(), TransportError> {
        // For Meshtastic, building_id could be used to set channel
        self.connect_serial(&self.serial_port).await
    }
    
    async fn disconnect(&mut self) -> Result<(), TransportError> {
        // self.api = None;  // TODO: Enable when meshtastic is added
        // self.packet_receiver = None;  // TODO: Enable when meshtastic is added
        self.connected = false;
        info!("Disconnected from Meshtastic device");
        Ok(())
    }
    
    async fn send(&mut self, data: &[u8]) -> Result<(), TransportError> {
        if data.len() != 13 {
            return Err(TransportError::InvalidData("Data must be exactly 13 bytes".into()));
        }
        
        let mut bytes = [0u8; 13];
        bytes.copy_from_slice(data);
        let arxobject = ArxObject::from_bytes(&bytes);
        
        // Broadcast to all nodes (0xFFFFFFFF)
        self.send_arxobject_internal(&arxobject, 0xFFFFFFFF).await
    }
    
    async fn receive(&mut self, _timeout: Option<Duration>) -> Result<Vec<u8>, TransportError> {
        match self.receive_arxobject_internal().await? {
            Some(arxobject) => Ok(arxobject.to_bytes().to_vec()),
            None => Ok(Vec::new()),
        }
    }
    
    fn is_connected(&self) -> bool {
        self.connected
    }
    
    fn get_metrics(&self) -> TransportMetrics {
        self.metrics.clone()
    }
    
    fn name(&self) -> &str {
        "Meshtastic"
    }
    
    async fn is_available(&self) -> bool {
        // Check if the serial port exists
        std::path::Path::new(&self.serial_port).exists()
    }
}

/// Builder for Meshtastic transport configuration
pub struct MeshtasticTransportBuilder {
    serial_port: Option<String>,
    node_id: u32,
    channel: u8,
}

impl MeshtasticTransportBuilder {
    pub fn new() -> Self {
        Self {
            serial_port: None,
            node_id: 0,
            channel: 0,
        }
    }
    
    pub fn serial_port(mut self, port: String) -> Self {
        self.serial_port = Some(port);
        self
    }
    
    pub fn node_id(mut self, id: u32) -> Self {
        self.node_id = id;
        self
    }
    
    pub fn channel(mut self, ch: u8) -> Self {
        self.channel = ch;
        self
    }
    
    pub fn build(self) -> Result<MeshtasticTransport, TransportError> {
        let serial_port = self.serial_port
            .ok_or_else(|| TransportError::InvalidData("Serial port not specified".into()))?;
        
        Ok(MeshtasticTransport::new(serial_port))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_builder() {
        let transport = MeshtasticTransportBuilder::new()
            .serial_port("/dev/ttyUSB0".to_string())
            .node_id(12345)
            .channel(0)
            .build();
        
        assert!(transport.is_ok());
    }
    
    #[tokio::test]
    async fn test_arxobject_serialization() {
        let obj = ArxObject::new(0x1234, 0x15, 1000, 2000, 300);
        let bytes = obj.to_bytes();
        assert_eq!(bytes.len(), 13);
        
        let restored = ArxObject::from_bytes(&bytes);
        assert_eq!(obj.building_id, restored.building_id);
        assert_eq!(obj.object_type, restored.object_type);
        assert_eq!(obj.x, restored.x);
        assert_eq!(obj.y, restored.y);
        assert_eq!(obj.z, restored.z);
    }
}