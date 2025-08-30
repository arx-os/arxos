//! Node configuration and persistent settings

use esp_println::println;
use heapless::String;

/// RF region configuration
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Region {
    US915,  // 902-928 MHz
    EU868,  // 863-870 MHz  
    AS923,  // 920-923 MHz
}

/// Node configuration stored in flash
#[derive(Debug, Clone)]
pub struct NodeConfig {
    pub node_id: u16,
    pub region: Region,
    pub tx_power: i8,  // dBm
    pub spreading_factor: u8,
    pub bandwidth: u32,  // Hz
    pub building_id: u16,
    pub mesh_key: [u8; 32],
}

impl NodeConfig {
    /// Load configuration from flash or create default
    pub fn load_or_create(rng: &mut esp_hal::rng::Rng) -> Self {
        // TODO: Load from NVS flash storage
        // For now, create default config
        
        let mut node_id_bytes = [0u8; 2];
        rng.read(&mut node_id_bytes);
        let node_id = u16::from_le_bytes(node_id_bytes);
        
        println!("Generated node ID: 0x{:04X}", node_id);
        
        Self {
            node_id,
            region: Region::US915,  // Default to US
            tx_power: 20,  // 20 dBm
            spreading_factor: 9,
            bandwidth: 125_000,  // 125 kHz
            building_id: 0x0001,
            mesh_key: [0xAA; 32],  // TODO: Generate secure key
        }
    }
    
    /// Get frequency in MHz based on region
    pub fn frequency_mhz(&self) -> f32 {
        match self.region {
            Region::US915 => 915.0,
            Region::EU868 => 868.0,
            Region::AS923 => 923.0,
        }
    }
    
    /// Get region as string
    pub fn region_string(&self) -> &'static str {
        match self.region {
            Region::US915 => "US 915MHz",
            Region::EU868 => "EU 868MHz",
            Region::AS923 => "AS 923MHz",
        }
    }
    
    /// Validate configuration
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.tx_power > 30 || self.tx_power < -10 {
            return Err("Invalid TX power");
        }
        
        if self.spreading_factor < 7 || self.spreading_factor > 12 {
            return Err("Invalid spreading factor");
        }
        
        if self.bandwidth != 125_000 && self.bandwidth != 250_000 && self.bandwidth != 500_000 {
            return Err("Invalid bandwidth");
        }
        
        Ok(())
    }
}