//! Integration tests for hardware module
//!
//! These tests verify that sensor data ingestion and equipment status updates work correctly.

use arxos::hardware::{SensorIngestionService, SensorIngestionConfig, HardwareError};
use std::path::PathBuf;
use tempfile::TempDir;

fn setup_test_environment() -> TempDir {
    tempfile::tempdir().expect("Failed to create temp directory")
}

#[test]
fn test_sensor_ingestion_service_creation() {
    let config = SensorIngestionConfig {
        data_directory: PathBuf::from("./sensor-data"),
        supported_formats: vec!["yaml".to_string(), "json".to_string()],
        auto_process: true,
    };
    
    let service = SensorIngestionService::new(config);
    assert_eq!(service.config.data_directory, PathBuf::from("./sensor-data"));
}

#[test]
fn test_read_nonexistent_sensor_file() {
    let config = SensorIngestionConfig::default();
    let service = SensorIngestionService::new(config);
    
    let result = service.read_sensor_data_file("nonexistent.yaml");
    assert!(result.is_err());
    
    if let Err(HardwareError::FileNotFound { path }) = result {
        assert_eq!(path, "nonexistent.yaml");
    } else {
        panic!("Expected FileNotFound error");
    }
}

// Note: Additional tests would require sample sensor data files
// These would test:
// - Reading valid sensor files
// - Processing sensor data
// - Updating equipment status
// - Equipment-sensor mapping

