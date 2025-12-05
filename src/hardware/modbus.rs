//! Modbus TCP Implementation

use super::{HardwareInterface, SensorReading, ReadingQuality};
use anyhow::{Result, Context as AnyhowContext};
use async_trait::async_trait;
use tokio::sync::Mutex;
use tokio_modbus::prelude::*;
use tokio_modbus::client::Context;
use std::time::Duration;
use std::sync::Arc;

pub struct ModbusInterface {
    host: String,
    port: u16,
    // Client context protected by Mutex for interior mutability (HardwareInterface read is &self)
    client: Arc<Mutex<Option<Context>>>,
}

impl ModbusInterface {
    pub fn new(host: String, port: u16) -> Self {
        Self {
            host,
            port,
            client: Arc::new(Mutex::new(None)),
        }
    }

    // Helper to parse location: "holding:100" or just "100"
    fn parse_address(location: &str) -> Result<(String, u16)> {
        if let Some((type_str, addr_str)) = location.split_once(':') {
             Ok((type_str.to_lowercase(), addr_str.parse()?))
        } else {
            // Default to holding register if no prefix
            Ok(("holding".to_string(), location.parse()?))
        }
    }
}

#[async_trait]
impl HardwareInterface for ModbusInterface {
    async fn connect(&mut self) -> Result<()> {
        tracing::info!("Connecting to Modbus TCP at {}:{}", self.host, self.port);
        let socket_addr = format!("{}:{}", self.host, self.port).parse()?;
        
        // Create a new client context
        // We use a timeout to prevent hanging
        let ctx = tokio::time::timeout(
            Duration::from_secs(5),
            tokio_modbus::client::tcp::connect(socket_addr)
        ).await.context("Connection timed out")??;
        
        let mut client_lock = self.client.lock().await;
        *client_lock = Some(ctx);
        
        tracing::info!("Modbus connected successfully");
        Ok(())
    }

    async fn disconnect(&mut self) -> Result<()> {
        let mut client_lock = self.client.lock().await;
        if client_lock.is_some() {
             tracing::info!("Disconnecting Modbus client");
             *client_lock = None;
        }
        Ok(())
    }

    async fn is_connected(&self) -> bool {
        let client_lock = self.client.lock().await;
        client_lock.is_some()
    }

    async fn read_sensor(&self, location: &str, _sensor_type: &str) -> Result<SensorReading> {
        let (reg_type, addr) = Self::parse_address(location)?;
        
        let mut client_lock = self.client.lock().await;
        let client = client_lock.as_mut().context("Not connected to Modbus")?;
        
        let value = match reg_type.as_str() {
            "holding" => {
                let params = client.read_holding_registers(addr, 1).await?;
                if params.is_empty() { anyhow::bail!("No data returned"); }
                params[0] as f64
            },
            "input" => {
                let params = client.read_input_registers(addr, 1).await?;
                if params.is_empty() { anyhow::bail!("No data returned"); }
                params[0] as f64
            },
            "coil" => {
                let params = client.read_coils(addr, 1).await?;
                if params.is_empty() { anyhow::bail!("No data returned"); }
                if params[0] { 1.0 } else { 0.0 }
            },
            "discrete" => {
                let params = client.read_discrete_inputs(addr, 1).await?;
                if params.is_empty() { anyhow::bail!("No data returned"); }
                if params[0] { 1.0 } else { 0.0 }
            },
            _ => anyhow::bail!("Unknown Modbus register type: {}", reg_type),
        };

        Ok(SensorReading {
            value,
            unit: "raw".to_string(), // In a real app, mapping would convert unit based on sensor_type
            timestamp: chrono::Utc::now(),
            quality: ReadingQuality::Good,
        })
    }
    
    async fn write_control(&self, location: &str, _control_type: &str, value: f64) -> Result<()> {
         let (reg_type, addr) = Self::parse_address(location)?;
         
         let mut client_lock = self.client.lock().await;
         let client = client_lock.as_mut().context("Not connected to Modbus")?;
         
         match reg_type.as_str() {
            "holding" => {
                client.write_single_register(addr, value as u16).await?;
            },
            "coil" => {
                client.write_single_coil(addr, value != 0.0).await?;
            },
            _ => anyhow::bail!("Write not supported for type: {}", reg_type),
         }
         
         Ok(())
    }
    
    async fn list_sensors(&self) -> Result<Vec<String>> {
        // Modbus doesn't support discovery, so we return a static list or empty
        // In a real app, this would be config-driven
        Ok(vec![]) 
    }
}
