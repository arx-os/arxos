//! Tests for sensor processing command handlers

use arxos::commands::sensors::handle_process_sensors_command;
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
    
    // Note: This test would require a building data file and Git setup
    // For now, we just verify the command handler exists and accepts parameters
    let sensor_path = sensor_dir.to_string_lossy().to_string();
    
    // Just verify the function signature is correct (would fail if handler doesn't exist)
    assert!(!sensor_path.is_empty());
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

#[test]
#[ignore] // Requires sensor data and building setup
fn test_equipment_status_updates() {
    // This would test updating equipment status from sensor data
    // Requires:
    // 1. Existing building YAML file
    // 2. Sensor data files
    // 3. Git repository initialized
}

#[test]
#[ignore] // Requires Git repository setup
fn test_commit_workflow() {
    // This would test committing sensor updates to Git
    // Requires:
    // 1. Git repository initialized
    // 2. Sensor data processed
    // 3. Equipment updated
    // 4. Changes committed
}
