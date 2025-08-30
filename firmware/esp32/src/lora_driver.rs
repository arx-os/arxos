//! LoRa SX1262 driver for ESP32

use embassy_time::{Duration, Timer};
use embedded_hal::digital::{InputPin, OutputPin};
use embedded_hal_async::spi::SpiDevice;
use esp_println::println;
use heapless::Vec;
use lora_phy::{
    mod_params::*,
    mod_traits::RadioKind,
    sx126x::{self, Sx126x, Sx126xVariant},
    LoRa,
};

use crate::config::NodeConfig;

/// LoRa driver wrapper
pub struct LoRaDriver {
    radio: Sx126x<SPI, CS, RESET, DIO1, BUSY, DELAY>,
    config: NodeConfig,
    rx_buffer: Vec<u8, 256>,
}

impl LoRaDriver {
    /// Initialize LoRa driver with SX1262
    pub async fn new(
        spi: SPI,
        cs: CS,
        reset: RESET,
        dio1: DIO1,
        busy: BUSY,
        config: NodeConfig,
    ) -> Self {
        println!("Initializing LoRa SX1262...");
        
        // Create SX1262 instance
        let mut radio = Sx126x::new(
            spi,
            cs,
            reset,
            dio1,
            busy,
            Delay,
            Sx126xVariant::Sx1262,
        );
        
        // Reset radio
        radio.reset().await.expect("Failed to reset radio");
        Timer::after(Duration::from_millis(100)).await;
        
        // Configure radio parameters
        let mod_params = ModulationParams {
            spreading_factor: SpreadingFactor::from_value(config.spreading_factor),
            bandwidth: Bandwidth::from_hz(config.bandwidth),
            coding_rate: CodingRate::Cr45,
            low_data_rate_optimize: true,
        };
        
        let tx_params = TxParams {
            power: config.tx_power,
            ramp_time: RampTime::Ramp40Us,
        };
        
        // Set frequency
        let frequency = (config.frequency_mhz() * 1_000_000.0) as u32;
        radio.set_frequency(frequency).await.expect("Failed to set frequency");
        
        // Set modulation parameters
        radio.set_modulation_params(mod_params).await.expect("Failed to set modulation");
        
        // Set TX parameters
        radio.set_tx_params(tx_params).await.expect("Failed to set TX params");
        
        // Set packet parameters
        let packet_params = PacketParams {
            preamble_length: 8,
            header_type: HeaderType::Variable,
            payload_length: 255,
            crc: CrcMode::Enabled,
            invert_iq: false,
        };
        radio.set_packet_params(packet_params).await.expect("Failed to set packet params");
        
        // Configure DIO and IRQ
        radio.set_dio_irq_params(
            IrqMask::TxDone | IrqMask::RxDone | IrqMask::Timeout | IrqMask::CrcErr,
            IrqMask::None,
            IrqMask::None,
            IrqMask::None,
        ).await.expect("Failed to set IRQ params");
        
        println!("LoRa initialized on {} MHz", config.frequency_mhz());
        
        Self {
            radio,
            config,
            rx_buffer: Vec::new(),
        }
    }
    
    /// Transmit packet
    pub async fn transmit(&mut self, data: &[u8]) -> Result<(), LoRaError> {
        if data.len() > 255 {
            return Err(LoRaError::PayloadTooLarge);
        }
        
        // Set to standby mode
        self.radio.set_standby(StandbyMode::StandbyRc).await?;
        
        // Write buffer
        self.radio.write_buffer(0, data).await?;
        
        // Set TX mode with timeout
        self.radio.set_tx(3000).await?;  // 3 second timeout
        
        // Wait for TX done
        let start = embassy_time::Instant::now();
        loop {
            let irq = self.radio.get_irq_status().await?;
            if irq & IrqMask::TxDone != 0 {
                self.radio.clear_irq_status(IrqMask::TxDone).await?;
                break;
            }
            if start.elapsed() > Duration::from_secs(5) {
                return Err(LoRaError::Timeout);
            }
            Timer::after(Duration::from_millis(1)).await;
        }
        
        Ok(())
    }
    
    /// Receive packet
    pub async fn receive(&mut self, timeout_ms: u32) -> Result<Vec<u8, 256>, LoRaError> {
        // Set to standby
        self.radio.set_standby(StandbyMode::StandbyRc).await?;
        
        // Set RX mode with timeout
        self.radio.set_rx(timeout_ms).await?;
        
        // Wait for RX done or timeout
        let start = embassy_time::Instant::now();
        loop {
            let irq = self.radio.get_irq_status().await?;
            
            if irq & IrqMask::RxDone != 0 {
                // Get packet status
                let (rssi, snr) = self.radio.get_packet_status().await?;
                println!("Packet received: RSSI={} dBm, SNR={} dB", rssi, snr);
                
                // Get payload length
                let (len, _) = self.radio.get_rx_buffer_status().await?;
                
                // Read buffer
                let mut buffer = Vec::new();
                buffer.resize(len as usize, 0).map_err(|_| LoRaError::BufferTooSmall)?;
                self.radio.read_buffer(0, &mut buffer).await?;
                
                // Clear IRQ
                self.radio.clear_irq_status(IrqMask::RxDone).await?;
                
                return Ok(buffer);
            }
            
            if irq & IrqMask::Timeout != 0 {
                self.radio.clear_irq_status(IrqMask::Timeout).await?;
                return Err(LoRaError::Timeout);
            }
            
            if irq & IrqMask::CrcErr != 0 {
                self.radio.clear_irq_status(IrqMask::CrcErr).await?;
                return Err(LoRaError::CrcError);
            }
            
            if start.elapsed() > Duration::from_millis(timeout_ms as u64 + 1000) {
                return Err(LoRaError::Timeout);
            }
            
            Timer::after(Duration::from_millis(1)).await;
        }
    }
    
    /// Get RSSI (signal strength)
    pub async fn get_rssi(&mut self) -> Result<i16, LoRaError> {
        self.radio.get_rssi_inst().await.map_err(|_| LoRaError::RadioError)
    }
    
    /// Set to sleep mode for power saving
    pub async fn sleep(&mut self) -> Result<(), LoRaError> {
        self.radio.set_sleep(SleepConfig::default()).await.map_err(|_| LoRaError::RadioError)
    }
}

/// LoRa errors
#[derive(Debug)]
pub enum LoRaError {
    PayloadTooLarge,
    Timeout,
    CrcError,
    BufferTooSmall,
    RadioError,
}