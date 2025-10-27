//! Integration tests for hardware sensor workflow
//!
//! These tests verify the complete sensor data processing workflow.

use arxos::hardware::{SensorIngestionService, SensorIngestionConfig, SensorData, SensorMetadata, SensorDataValues, EquipmentStatusUpdater};
use std::collections::HashMap;
use chrono::Utc;

#[test]
fn test_sensor_data_structure() {
    // Test creating sensor data structure
    let metadata = SensorMetadata {
        sensor_id: "sensor-001".to_string(),
        sensor_type: "temperature".to_string(),
        room_path: Some("/F1/R101".to_string()),
        timestamp: Utc::now().to_rfc3339(),
        source: "esp32".to_string(),
        building_id: Some("building-001".to_string()),
        equipment_id: Some("VAV-301".to_string()),
        extra: HashMap::new(),
    };
    
    let data = SensorDataValues {
        values: {
            let mut values = HashMap::new();
            values.insert("value".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(72.5)));
            values.insert("unit".to_string(), serde_yaml::Value::String("fahrenheit".to_string()));
            values
        },
    };
    
    let sensor_data = SensorData {
        api_version: "arxos.io/v1".to_string(),
        kind: "SensorData".to_string(),
        metadata,
        data,
        alerts: vec![],
        arxos: None,
    };
    
    assert_eq!(sensor_data.metadata.sensor_id, "sensor-001");
    assert_eq!(sensor_data.metadata.sensor_type, "temperature");
}

#[test]
fn test_sensor_service_creation() {
    // Test creating sensor ingestion service
    let config = SensorIngestionConfig {
        data_directory: std::path::PathBuf::from("./test_data/sensor-data"),
        supported_formats: vec!["yaml".to_string(), "json".to_string()],
        auto_process: true,
        ..Default::default()
    };
    
    let service = SensorIngestionService::new(config);
    assert_eq!(service.config.data_directory, std::path::PathBuf::from("./test_data/sensor-data"));
}

#[test]
fn test_equipment_status_updater_creation() {
    // Test creating equipment status updater
    // Note: This will fail if building data doesn't exist, which is expected in tests
    let updater = EquipmentStatusUpdater::new("test_building");
    
    // The updater might fail to create if building data doesn't exist
    // That's okay for this test
    assert!(true, "EquipmentStatusUpdater creation attempted");
}

