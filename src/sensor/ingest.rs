//! Sensor data ingestion logic

use crate::error::ArxResult;
use super::types::{SensorReading, SensorBatch};
use std::fs::OpenOptions;
use std::io::Write;

pub struct SensorIngestor {
    // Placeholder for ingestion logic
}

impl SensorIngestor {
    pub fn new() -> Self {
        Self {}
    }

    pub fn ingest_reading(&mut self, reading: SensorReading) -> ArxResult<()> {
        let file_path = "sensor_data.csv";
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(file_path)
            .map_err(|e| crate::error::ArxError::IoError(e))?;
            
        writeln!(file, "{},{},{},{},{:?}", 
            reading.sensor_id, 
            reading.timestamp, 
            reading.value, 
            reading.unit,
            reading.location
        ).map_err(|e| crate::error::ArxError::IoError(e))?;
        
        Ok(())
    }

    pub fn ingest_batch(&mut self, batch: SensorBatch) -> ArxResult<()> {
        for reading in batch.readings {
            self.ingest_reading(reading)?;
        }
        Ok(())
    }
}

impl Default for SensorIngestor {
    fn default() -> Self {
        Self::new()
    }
}