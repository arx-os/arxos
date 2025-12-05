//! Simulated Hardware Interface for Testing/Demo
//!
//! Generates synthetic sensor data (sine waves, random noise) to demonstrate
//! system capabilities without physical hardware.

use super::{HardwareInterface, SensorReading, ReadingQuality};
use anyhow::Result;
use async_trait::async_trait;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

pub struct SimulatedInterface {
    connected: AtomicBool,
    sensors: HashMap<String, String>, // Address -> Type
}

impl SimulatedInterface {
    pub fn new() -> Self {
        let mut sensors = HashMap::new();
        sensors.insert("temp1".to_string(), "temperature".to_string());
        sensors.insert("temp2".to_string(), "temperature".to_string());
        sensors.insert("humidity".to_string(), "humidity".to_string());
        sensors.insert("power".to_string(), "power".to_string());
        
        Self {
            connected: AtomicBool::new(false),
            sensors,
        }
    }
}

#[async_trait]
impl HardwareInterface for SimulatedInterface {
    async fn connect(&mut self) -> Result<()> {
        self.connected.store(true, Ordering::SeqCst);
        Ok(())
    }

    async fn disconnect(&mut self) -> Result<()> {
        self.connected.store(false, Ordering::SeqCst);
        Ok(())
    }

    async fn is_connected(&self) -> bool {
        self.connected.load(Ordering::SeqCst)
    }

    async fn read_sensor(&self, location: &str, _sensor_type: &str) -> Result<SensorReading> {
        if !self.is_connected().await {
            anyhow::bail!("Simulated interface not connected");
        }

        // Generate synthetic data based on time
        let start = SystemTime::now();
        let since_the_epoch = start.duration_since(UNIX_EPOCH)?.as_secs_f64();
        
        let (value, unit) = match location {
            "temp1" => {
                // Sine wave: 22C +/- 2C, period 60s
                let v = 22.0 + 2.0 * (since_the_epoch / 10.0).sin();
                (v, "C".to_string())
            },
            "temp2" => {
                // Cosine wave: 24C +/- 1.5C, period 45s
                let v = 24.0 + 1.5 * (since_the_epoch / 7.5).cos();
                (v, "C".to_string())
            },
            "humidity" => {
                // 45% +/- 5%, noisy
                let noise = (since_the_epoch % 10.0) / 10.0; 
                (45.0 + 5.0 * noise, "%".to_string())
            },
            "power" => {
                // Ramp 0-100
                let v = (since_the_epoch % 100.0) as f64;
                (v, "W".to_string())
            },
            _ => anyhow::bail!("Unknown simulated sensor: {}", location),
        };

        Ok(SensorReading {
            value,
            unit,
            timestamp: chrono::Utc::now(),
            quality: ReadingQuality::Good,
        })
    }

    async fn write_control(&self, location: &str, _control_type: &str, value: f64) -> Result<()> {
        if !self.is_connected().await {
            anyhow::bail!("Simulated interface not connected");
        }
        tracing::info!("Simulated write to {}: {}", location, value);
        Ok(())
    }

    async fn list_sensors(&self) -> Result<Vec<String>> {
        Ok(self.sensors.keys().cloned().collect())
    }
}
