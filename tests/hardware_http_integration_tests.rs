//! Integration tests for hardware sensor HTTP ingestion

use std::collections::HashMap;
use tempfile::TempDir;

/// Test helper to create valid sensor data
fn create_test_sensor_data() -> arxos::hardware::SensorData {
    arxos::hardware::SensorData {
        api_version: "arxos.io/v1".to_string(),
        kind: "SensorData".to_string(),
        metadata: arxos::hardware::SensorMetadata {
            sensor_id: "test_sensor_http_001".to_string(),
            sensor_type: "temperature".to_string(),
            room_path: Some("/test_building/3/301".to_string()),
            timestamp: "2024-01-15T10:30:00Z".to_string(),
            source: "test_http".to_string(),
            building_id: Some("test_building".to_string()),
            equipment_id: Some("HVAC-301".to_string()),
            extra: HashMap::new(),
        },
        data: arxos::hardware::SensorDataValues {
            values: {
                let mut map = HashMap::new();
                map.insert("temperature".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(72)));
                map
            },
        },
        alerts: vec![],
        arxos: None,
    }
}

#[tokio::test]
async fn test_sensor_data_structure_validation() {
    let sensor_data = create_test_sensor_data();
    
    // Verify all required fields
    assert_eq!(sensor_data.api_version, "arxos.io/v1");
    assert_eq!(sensor_data.metadata.sensor_id, "test_sensor_http_001");
    assert!(sensor_data.data.values.contains_key("temperature"));
}

#[cfg(feature = "async-sensors")]
#[tokio::test]
async fn test_sensor_http_response_serialization() {
    // Test HTTP response serialization
    use serde::{Serialize, Deserialize};
    
    #[derive(Debug, Serialize, Deserialize)]
    struct TestResponse {
        success: bool,
        message: String,
        sensor_id: Option<String>,
        timestamp: Option<String>,
    }
    
    let response = TestResponse {
        success: true,
        message: "Test message".to_string(),
        sensor_id: Some("test_001".to_string()),
        timestamp: Some("2024-01-15T10:30:00Z".to_string()),
    };
    
    // Verify JSON serialization works
    let json = serde_json::to_string(&response).unwrap();
    assert!(json.contains("test_001"));
    assert!(json.contains("Test message"));
}

#[tokio::test]
async fn test_equipment_sensor_mapping_structure() {
    use arxos::hardware::{EquipmentSensorMapping, SensorType, ThresholdCheck};
    
    let mapping = EquipmentSensorMapping {
        equipment_id: "HVAC-301".to_string(),
        sensor_id: "sensor_001".to_string(),
        sensor_type: SensorType::Temperature,
        threshold_min: Some(65.0),
        threshold_max: Some(75.0),
        alert_on_out_of_range: true,
    };
    
    // Test threshold checking
    assert_eq!(mapping.check_thresholds(70.0), ThresholdCheck::Normal);
    assert_eq!(mapping.check_thresholds(60.0), ThresholdCheck::OutOfRange);
    assert_eq!(mapping.check_thresholds(80.0), ThresholdCheck::OutOfRange);
}

#[tokio::test]
async fn test_sensor_ingestion_service_config() {
    let temp_dir = TempDir::new().unwrap();
    let config = arxos::hardware::SensorIngestionConfig {
        data_directory: temp_dir.path().to_path_buf(),
        ..Default::default()
    };
    
    let service = arxos::hardware::SensorIngestionService::new(config);
    
    // Verify default configuration
    assert_eq!(service.sensor_data_dir(), temp_dir.path());
}

