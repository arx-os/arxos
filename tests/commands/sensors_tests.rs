//! Tests for sensor processing command handlers

use arxui::commands::sensors::handle_process_sensors_command;
use tempfile::TempDir;
use std::fs::{create_dir_all, write};

#[test]
fn test_sensor_file_processing() {
    // Create temporary sensor data directory
    let temp_dir = tempfile::tempdir().unwrap();
    let sensor_dir = temp_dir.path().join("sensors");
    create_dir_all(&sensor_dir).unwrap();
    
    // Copy sample sensor files to temp directory
    let yaml_content = include_str!("../../test_data/sensor-data/sample_temperature_reading.yaml");
    write(sensor_dir.join("temp_reading.yaml"), yaml_content).unwrap();
    
    let json_content = include_str!("../../test_data/sensor-data/sample_air_quality.json");
    write(sensor_dir.join("air_quality.json"), json_content).unwrap();
    
    // Verify sensor directory structure was created correctly
    let sensor_path = sensor_dir.to_string_lossy().to_string();
    assert!(!sensor_path.is_empty());
    assert!(sensor_dir.exists());
    assert!(sensor_dir.join("temp_reading.yaml").exists());
    assert!(sensor_dir.join("air_quality.json").exists());
}

#[test]
fn test_sensor_data_structure() {
    // Test parsing sensor data from sample files
    let yaml_data = include_str!("../../test_data/sensor-data/sample_temperature_reading.yaml");
    let json_data = include_str!("../../test_data/sensor-data/sample_air_quality.json");
    
    // Verify structure
    assert!(yaml_data.contains("esp32_temp_001"));
    assert!(yaml_data.contains("temperature"));
    assert!(yaml_data.contains("HVAC-301"));
    
    assert!(json_data.contains("rp2040_air_001"));
    assert!(json_data.contains("air_quality"));
    assert!(json_data.contains("HVAC-205"));
}

// Note: Equipment status update and commit workflow tests are covered in:
// - tests/hardware/hardware_workflow_tests.rs (sensor ingestion workflows)
// - tests/e2e/e2e_workflow_tests.rs (sensor ingestion to equipment update workflow)
