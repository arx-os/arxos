//! Mock transport implementation for testing

use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use arxos_core::arxobject::ArxObject;

/// Mock transport for testing without hardware
pub struct MockTransport {
    pub connected: bool,
    pub tx_buffer: Arc<Mutex<VecDeque<Vec<u8>>>>,
    pub rx_buffer: Arc<Mutex<VecDeque<Vec<u8>>>>,
    pub error_on_next_send: bool,
    pub latency_ms: u32,
    pub packet_loss_rate: f32,
}

impl MockTransport {
    pub fn new() -> Self {
        Self {
            connected: false,
            tx_buffer: Arc::new(Mutex::new(VecDeque::new())),
            rx_buffer: Arc::new(Mutex::new(VecDeque::new())),
            error_on_next_send: false,
            latency_ms: 10,
            packet_loss_rate: 0.0,
        }
    }
    
    /// Create a pair of connected mock transports
    pub fn create_pair() -> (Self, Self) {
        let transport1 = Self::new();
        let transport2 = Self::new();
        
        // Cross-connect the buffers
        let t1_tx = transport1.tx_buffer.clone();
        let t2_rx = transport2.rx_buffer.clone();
        let t2_tx = transport2.tx_buffer.clone();
        let t1_rx = transport1.rx_buffer.clone();
        
        (
            Self {
                connected: false,
                tx_buffer: t1_tx.clone(),
                rx_buffer: t1_rx,
                error_on_next_send: false,
                latency_ms: 10,
                packet_loss_rate: 0.0,
            },
            Self {
                connected: false,
                tx_buffer: t2_tx.clone(),
                rx_buffer: t2_rx,
                error_on_next_send: false,
                latency_ms: 10,
                packet_loss_rate: 0.0,
            },
        )
    }
    
    pub fn connect(&mut self, _building_id: &str) -> Result<(), String> {
        if self.connected {
            return Err("Already connected".to_string());
        }
        self.connected = true;
        Ok(())
    }
    
    pub fn disconnect(&mut self) -> Result<(), String> {
        if !self.connected {
            return Err("Not connected".to_string());
        }
        self.connected = false;
        Ok(())
    }
    
    pub fn send(&mut self, data: &[u8]) -> Result<(), String> {
        if !self.connected {
            return Err("Not connected".to_string());
        }
        
        if self.error_on_next_send {
            self.error_on_next_send = false;
            return Err("Simulated send error".to_string());
        }
        
        // Simulate packet loss
        if self.packet_loss_rate > 0.0 {
            use rand::Rng;
            let mut rng = rand::thread_rng();
            if rng.gen::<f32>() < self.packet_loss_rate {
                // Silently drop packet
                return Ok(());
            }
        }
        
        // Add to TX buffer (will be received by paired transport)
        let mut buffer = self.tx_buffer.lock().unwrap();
        buffer.push_back(data.to_vec());
        
        Ok(())
    }
    
    pub fn receive(&mut self) -> Result<Vec<u8>, String> {
        if !self.connected {
            return Err("Not connected".to_string());
        }
        
        // Simulate latency
        if self.latency_ms > 0 {
            std::thread::sleep(std::time::Duration::from_millis(self.latency_ms as u64));
        }
        
        let mut buffer = self.rx_buffer.lock().unwrap();
        buffer.pop_front().ok_or_else(|| "No data available".to_string())
    }
    
    pub fn is_connected(&self) -> bool {
        self.connected
    }
    
    /// Inject data to be received
    pub fn inject_rx_data(&mut self, data: Vec<u8>) {
        let mut buffer = self.rx_buffer.lock().unwrap();
        buffer.push_back(data);
    }
    
    /// Get transmitted data for verification
    pub fn get_tx_data(&mut self) -> Option<Vec<u8>> {
        let mut buffer = self.tx_buffer.lock().unwrap();
        buffer.pop_front()
    }
    
    /// Simulate receiving ArxObjects
    pub fn inject_arxobjects(&mut self, objects: &[ArxObject]) {
        for obj in objects {
            self.inject_rx_data(obj.to_bytes().to_vec());
        }
    }
    
    /// Set network conditions for testing
    pub fn set_network_conditions(&mut self, latency_ms: u32, packet_loss_rate: f32) {
        self.latency_ms = latency_ms;
        self.packet_loss_rate = packet_loss_rate.clamp(0.0, 1.0);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_mock_transport_basic() {
        let mut transport = MockTransport::new();
        
        // Should not be connected initially
        assert!(!transport.is_connected());
        
        // Connect should succeed
        assert!(transport.connect("test_building").is_ok());
        assert!(transport.is_connected());
        
        // Send should work when connected
        assert!(transport.send(b"test data").is_ok());
        
        // Disconnect should work
        assert!(transport.disconnect().is_ok());
        assert!(!transport.is_connected());
        
        // Send should fail when disconnected
        assert!(transport.send(b"test data").is_err());
    }
    
    #[test]
    fn test_mock_transport_pair() {
        let (mut transport1, mut transport2) = MockTransport::create_pair();
        
        // Connect both transports
        transport1.connect("building1").unwrap();
        transport2.connect("building2").unwrap();
        
        // Data sent from transport1 should be received by transport2
        transport1.send(b"Hello from 1").unwrap();
        
        // Note: In real implementation, this would need async or threading
        // For testing, we manually move data between buffers
        let data = transport1.get_tx_data().unwrap();
        transport2.inject_rx_data(data);
        
        let received = transport2.receive().unwrap();
        assert_eq!(received, b"Hello from 1");
    }
}