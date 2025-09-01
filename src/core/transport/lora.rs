//! LoRa USB dongle transport implementation

use super::{Transport, TransportError, TransportMetrics};
use async_trait::async_trait;
use std::time::{Duration, Instant};

/// LoRa dongle transport configuration
#[derive(Debug, Clone)]
pub struct LoRaConfig {
    pub frequency: u32,        // Hz (e.g., 915000000 for 915MHz)
    pub spreading_factor: u8,  // 7-12
    pub bandwidth: u32,        // Hz (125000, 250000, 500000)
    pub coding_rate: u8,       // 5-8
    pub tx_power: i8,          // dBm (-9 to +22)
}

impl Default for LoRaConfig {
    fn default() -> Self {
        Self {
            frequency: 915_000_000,  // 915 MHz (US)
            spreading_factor: 7,      // SF7 for high data rate
            bandwidth: 125_000,       // 125 kHz
            coding_rate: 5,          // 4/5
            tx_power: 20,            // 20 dBm
        }
    }
}

/// LoRa packet structure
#[repr(C, packed)]
pub struct LoRaPacket {
    pub header: u8,           // Packet type and flags
    pub seq: u16,            // Sequence number
    pub payload_len: u8,     // Payload length (max 251)
    pub payload: [u8; 251],  // Actual data
}

impl LoRaPacket {
    pub const SIZE: usize = 255;
    pub const MAX_PAYLOAD: usize = 251;
    
    /// Create a new LoRa packet
    pub fn new(seq: u16, data: &[u8]) -> Result<Self, TransportError> {
        if data.len() > Self::MAX_PAYLOAD {
            return Err(TransportError::InvalidData(
                format!("Payload too large: {} > {}", data.len(), Self::MAX_PAYLOAD)
            ));
        }
        
        let mut packet = Self {
            header: 0x01,  // Data packet
            seq,
            payload_len: data.len() as u8,
            payload: [0; 251],
        };
        
        packet.payload[..data.len()].copy_from_slice(data);
        Ok(packet)
    }
    
    /// Convert to bytes for transmission
    pub fn to_bytes(&self) -> Vec<u8> {
        unsafe {
            std::slice::from_raw_parts(
                self as *const Self as *const u8,
                Self::SIZE
            ).to_vec()
        }
    }
    
    /// Parse from received bytes
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, TransportError> {
        if bytes.len() != Self::SIZE {
            return Err(TransportError::InvalidData(
                format!("Invalid packet size: {} != {}", bytes.len(), Self::SIZE)
            ));
        }
        
        unsafe {
            Ok(std::ptr::read(bytes.as_ptr() as *const Self))
        }
    }
}

/// LoRa USB dongle transport
pub struct LoRaTransport {
    config: LoRaConfig,
    connected: bool,
    building_id: Option<String>,
    port_name: Option<String>,
    // serial_port: Option<Box<dyn serialport::SerialPort>>,  // TODO: Add serialport dependency
    metrics: TransportMetrics,
    sequence: u16,
}

impl LoRaTransport {
    /// Create a new LoRa transport
    pub fn new(config: LoRaConfig) -> Self {
        Self {
            config,
            connected: false,
            building_id: None,
            port_name: None,
            metrics: TransportMetrics::default(),
            sequence: 0,
        }
    }
    
    /// Detect if a LoRa dongle is connected
    pub async fn detect() -> Option<Self> {
        // TODO: Implement USB device detection
        // For now, return None (not detected)
        None
    }
    
    /// Get next sequence number
    fn next_sequence(&mut self) -> u16 {
        let seq = self.sequence;
        self.sequence = self.sequence.wrapping_add(1);
        seq
    }
}

#[async_trait]
impl Transport for LoRaTransport {
    async fn connect(&mut self, building_id: &str) -> Result<(), TransportError> {
        if self.connected {
            return Err(TransportError::ConnectionFailed("Already connected".to_string()));
        }
        
        // TODO: Implement actual serial port connection
        // 1. Find USB serial port
        // 2. Open serial connection
        // 3. Configure LoRa parameters
        // 4. Perform handshake
        
        // For now, simulate connection
        log::info!("Connecting to {} via LoRa dongle", building_id);
        
        self.connected = true;
        self.building_id = Some(building_id.to_string());
        self.metrics.connected_since = Some(Instant::now());
        
        Ok(())
    }
    
    async fn disconnect(&mut self) -> Result<(), TransportError> {
        if !self.connected {
            return Err(TransportError::NotConnected);
        }
        
        // TODO: Close serial port
        
        self.connected = false;
        self.building_id = None;
        self.metrics.connected_since = None;
        
        Ok(())
    }
    
    async fn send(&mut self, data: &[u8]) -> Result<(), TransportError> {
        if !self.connected {
            return Err(TransportError::NotConnected);
        }
        
        // Fragment data into packets if necessary
        let chunks = data.chunks(LoRaPacket::MAX_PAYLOAD);
        
        for chunk in chunks {
            let packet = LoRaPacket::new(self.next_sequence(), chunk)?;
            let packet_bytes = packet.to_bytes();
            
            // TODO: Send via serial port
            // Copy values from packed struct to avoid alignment issues
            let seq = packet.seq;
            let len = packet.payload_len;
            log::debug!("Sending LoRa packet: seq={}, len={}", seq, len);
            
            // Update metrics
            self.metrics.bytes_sent += packet_bytes.len();
            self.metrics.packets_sent += 1;
        }
        
        Ok(())
    }
    
    async fn receive(&mut self, timeout: Option<Duration>) -> Result<Vec<u8>, TransportError> {
        if !self.connected {
            return Err(TransportError::NotConnected);
        }
        
        // TODO: Implement actual serial port reading
        // For now, return timeout
        
        let timeout = timeout.unwrap_or(Duration::from_secs(5));
        tokio::time::sleep(timeout).await;
        
        Err(TransportError::Timeout)
    }
    
    fn is_connected(&self) -> bool {
        self.connected
    }
    
    fn get_metrics(&self) -> TransportMetrics {
        self.metrics.clone()
    }
    
    fn name(&self) -> &str {
        "LoRa USB Dongle"
    }
    
    async fn is_available(&self) -> bool {
        // TODO: Check if USB dongle is present
        // For now, return false
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_lora_packet_creation() {
        let data = b"Hello, LoRa!";
        let packet = LoRaPacket::new(42, data).unwrap();
        
        // Copy values from packed struct to avoid alignment issues
        let header = packet.header;
        let seq = packet.seq;
        let payload_len = packet.payload_len;
        
        assert_eq!(header, 0x01);
        assert_eq!(seq, 42);
        assert_eq!(payload_len, data.len() as u8);
        assert_eq!(&packet.payload[..data.len()], data);
    }
    
    #[test]
    fn test_lora_packet_serialization() {
        let data = b"Test data";
        let packet = LoRaPacket::new(123, data).unwrap();
        
        let bytes = packet.to_bytes();
        assert_eq!(bytes.len(), LoRaPacket::SIZE);
        
        let restored = LoRaPacket::from_bytes(&bytes).unwrap();
        // Copy values from packed struct to avoid alignment issues
        let seq = restored.seq;
        let payload_len = restored.payload_len;
        
        assert_eq!(seq, 123);
        assert_eq!(payload_len, data.len() as u8);
        assert_eq!(&restored.payload[..data.len()], data);
    }
    
    #[test]
    fn test_lora_packet_max_payload() {
        let data = vec![0xAA; LoRaPacket::MAX_PAYLOAD];
        let packet = LoRaPacket::new(1, &data).unwrap();
        assert_eq!(packet.payload_len as usize, LoRaPacket::MAX_PAYLOAD);
        
        // Too large should fail
        let large_data = vec![0xBB; LoRaPacket::MAX_PAYLOAD + 1];
        assert!(LoRaPacket::new(2, &large_data).is_err());
    }
}