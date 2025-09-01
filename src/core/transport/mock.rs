//! Mock transport implementation for testing

use super::{Transport, TransportError, TransportMetrics};
use async_trait::async_trait;
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

/// Mock transport for testing without hardware
pub struct MockTransport {
    connected: bool,
    building_id: Option<String>,
    rx_buffer: Arc<Mutex<VecDeque<Vec<u8>>>>,
    tx_buffer: Arc<Mutex<VecDeque<Vec<u8>>>>,
    metrics: TransportMetrics,
    available: bool,
}

impl MockTransport {
    /// Create a new mock transport
    pub fn new() -> Self {
        Self {
            connected: false,
            building_id: None,
            rx_buffer: Arc::new(Mutex::new(VecDeque::new())),
            tx_buffer: Arc::new(Mutex::new(VecDeque::new())),
            metrics: TransportMetrics::default(),
            available: true,
        }
    }
    
    /// Set availability for testing
    pub fn set_available(&mut self, available: bool) {
        self.available = available;
    }
    
    /// Inject data to be received
    pub fn inject_rx_data(&self, data: Vec<u8>) {
        let mut buffer = self.rx_buffer.lock().unwrap();
        buffer.push_back(data);
    }
    
    /// Get transmitted data for verification
    pub fn get_tx_data(&self) -> Option<Vec<u8>> {
        let mut buffer = self.tx_buffer.lock().unwrap();
        buffer.pop_front()
    }
    
    /// Create a connected pair of mock transports
    pub fn create_pair() -> (Self, Self) {
        let transport1 = Self::new();
        let transport2 = Self::new();
        
        // Note: In a real implementation, we'd cross-connect the buffers
        // For now, they're independent
        
        (transport1, transport2)
    }
}

#[async_trait]
impl Transport for MockTransport {
    async fn connect(&mut self, building_id: &str) -> Result<(), TransportError> {
        if self.connected {
            return Err(TransportError::ConnectionFailed("Already connected".to_string()));
        }
        
        // Simulate connection delay
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        self.connected = true;
        self.building_id = Some(building_id.to_string());
        self.metrics.connected_since = Some(Instant::now());
        
        Ok(())
    }
    
    async fn disconnect(&mut self) -> Result<(), TransportError> {
        if !self.connected {
            return Err(TransportError::NotConnected);
        }
        
        self.connected = false;
        self.building_id = None;
        self.metrics.connected_since = None;
        
        Ok(())
    }
    
    async fn send(&mut self, data: &[u8]) -> Result<(), TransportError> {
        if !self.connected {
            return Err(TransportError::NotConnected);
        }
        
        // Store in tx buffer
        let mut buffer = self.tx_buffer.lock().unwrap();
        buffer.push_back(data.to_vec());
        
        // Update metrics
        self.metrics.bytes_sent += data.len();
        self.metrics.packets_sent += 1;
        
        Ok(())
    }
    
    async fn receive(&mut self, timeout: Option<Duration>) -> Result<Vec<u8>, TransportError> {
        if !self.connected {
            return Err(TransportError::NotConnected);
        }
        
        let start = Instant::now();
        let timeout = timeout.unwrap_or(Duration::from_secs(5));
        
        loop {
            // Check buffer
            {
                let mut buffer = self.rx_buffer.lock().unwrap();
                if let Some(data) = buffer.pop_front() {
                    // Update metrics
                    self.metrics.bytes_received += data.len();
                    self.metrics.packets_received += 1;
                    return Ok(data);
                }
            }
            
            // Check timeout
            if start.elapsed() > timeout {
                return Err(TransportError::Timeout);
            }
            
            // Small delay to avoid busy waiting
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    }
    
    fn is_connected(&self) -> bool {
        self.connected
    }
    
    fn get_metrics(&self) -> TransportMetrics {
        self.metrics.clone()
    }
    
    fn name(&self) -> &str {
        "MockTransport"
    }
    
    async fn is_available(&self) -> bool {
        self.available
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_mock_transport_connection() {
        let mut transport = MockTransport::new();
        
        // Initially not connected
        assert!(!transport.is_connected());
        
        // Connect should succeed
        assert!(transport.connect("test_building").await.is_ok());
        assert!(transport.is_connected());
        
        // Double connect should fail
        assert!(transport.connect("test_building").await.is_err());
        
        // Disconnect should succeed
        assert!(transport.disconnect().await.is_ok());
        assert!(!transport.is_connected());
    }
    
    #[tokio::test]
    async fn test_mock_transport_data_transfer() {
        let mut transport = MockTransport::new();
        
        // Connect first
        transport.connect("test_building").await.unwrap();
        
        // Send data
        let test_data = b"Hello, Arxos!";
        transport.send(test_data).await.unwrap();
        
        // Verify it's in tx buffer
        let tx_data = transport.get_tx_data().unwrap();
        assert_eq!(tx_data, test_data);
        
        // Inject some rx data
        transport.inject_rx_data(b"Response".to_vec());
        
        // Receive it
        let rx_data = transport.receive(None).await.unwrap();
        assert_eq!(rx_data, b"Response");
        
        // Check metrics
        let metrics = transport.get_metrics();
        assert_eq!(metrics.bytes_sent, test_data.len());
        assert_eq!(metrics.packets_sent, 1);
        assert_eq!(metrics.bytes_received, 8);
        assert_eq!(metrics.packets_received, 1);
    }
    
    #[tokio::test]
    async fn test_mock_transport_timeout() {
        let mut transport = MockTransport::new();
        transport.connect("test_building").await.unwrap();
        
        // Try to receive with short timeout
        let result = transport.receive(Some(Duration::from_millis(100))).await;
        assert!(matches!(result, Err(TransportError::Timeout)));
    }
}